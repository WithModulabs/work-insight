# SharePoint Email Storage (RawWorkReports List)

## 개요

이 문서는 백엔드가 수신한 이메일 데이터를 SharePoint **RawWorkReports 목록**에 저장하는 기능의 설정 방법을 설명한다.

현재 구현 범위:

- 백엔드가 이메일 payload를 받거나 Graph webhook으로 신규 메일을 감지한다.
- 이메일 메타데이터를 SharePoint RawWorkReports 목록의 항목으로 저장한다.
- Microsoft Graph subscription 생성 API를 제공한다.
- Microsoft Graph webhook 알림을 받아서 메일을 조회한 뒤 리스트에 추가한다.

현재 구현하지 않은 범위:

- 첨부파일 개별 업로드
- 구독 갱신 스케줄러
- 저장 실패 재시도 큐
- 메시지 id 기반 중복 제거

## 1. Microsoft Entra 앱 등록

1. Azure Portal에서 App Registration을 생성한다.
2. `Application (client) ID`와 `Directory (tenant) ID`를 기록한다.
3. `Certificates & secrets`에서 client secret을 발급한다.
4. `API permissions`에서 Microsoft Graph Application Permission을 추가한다.

필수 권한:

- `Mail.Read`
- `Subscription.ReadWrite.All`
- `Sites.ReadWrite.All`

권한 추가 후 관리자 동의를 완료해야 한다.

## 2. SharePoint Site ID와 List ID 확인

Microsoft Graph Explorer에서 다음 호출로 정보를 조회한다.

**Site ID 조회:**

```
GET https://graph.microsoft.com/v1.0/sites/m365x12195465.sharepoint.com:/sites/Report
```

응답에서 `id` 필드를 복사한다. (형식: `hostname,siteId,webId`)

**List ID 조회:**

```
GET https://graph.microsoft.com/v1.0/sites/{siteId}/lists?$filter=displayName eq 'RawWorkReports'
```

응답에서 `id` 필드를 복사한다.

## 3. 환경변수 설정 예제

`backend/.env` 파일 (제공된 예제):

```env
# Microsoft Graph & SharePoint Configuration
MICROSOFT_TENANT_ID=M365x12195465.onmicrosoft.com
MICROSOFT_CLIENT_ID=<Azure App Registration에서 복사>
MICROSOFT_CLIENT_SECRET=<Azure App 시크릿 값>

# SharePoint Configuration - RawWorkReports List
SHAREPOINT_SITE_ID=m365x12195465.sharepoint.com,01d4673c-de92-4195-be66-ef76275ed32d,a37ced2a-d959-402d-916d-09f4918ad7bc
SHAREPOINT_LIST_ID=c7df069c-ed1c-422a-9034-d1c9cda6d64b

# Graph Configuration
GRAPH_MAILBOX_USER_ID=report@M365x12195465.onmicrosoft.com
GRAPH_NOTIFICATION_URL=http://localhost:8000/api/email-storage/graph/webhook
GRAPH_SUBSCRIPTION_CLIENT_STATE=work-insight-webhook-secret
GRAPH_SUBSCRIPTION_RESOURCE=me/mailFolders('Inbox')/messages
GRAPH_SUBSCRIPTION_EXPIRATION_MINUTES=4230
```

## 4. 백엔드 실행

```bash
cd backend
pip install -r ..\requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 5. 상태 확인

다음 엔드포인트로 SharePoint 및 Graph 설정 반영 여부를 확인한다:

```
GET /api/email-storage/sharepoint/status
```

응답 예시:

```json
{
  "configured": true,
  "graph": {
    "graph_configured": true,
    "mailbox_user_id": "report@M365x12195465.onmicrosoft.com",
    "notification_url": "http://localhost:8000/api/email-storage/graph/webhook",
    "has_client_state": true,
    "sharepoint_ready": true
  }
}
```

## 6. API 엔드포인트

### 6-1. 직접 이메일 저장 (POST /api/email-storage/sharepoint/store)

이메일을 RawWorkReports 목록에 항목으로 추가한다.

요청 예시:

```json
{
  "message_id": "mail-20260327-001",
  "internet_message_id": "<abc123@example.com>",
  "subject": "고객 문의 메일",
  "from_address": "sender@example.com",
  "to_addresses": ["team@example.com"],
  "cc_addresses": [],
  "received_at": "2026-03-27T09:15:00Z",
  "body_text": "안녕하세요. 문의드립니다.",
  "body_html": "<p>안녕하세요. 문의드립니다.</p>",
  "raw_mime_base64": "TUlNRS1WZXJzaW9uOiAxLjAK...",
  "attachments": [
    {
      "file_name": "quote.pdf",
      "content_type": "application/pdf",
      "size_bytes": 120443
    }
  ],
  "metadata": {
    "source": "mail-ingestion-worker",
    "mailbox": "support@example.com"
  }
}
```

응답 예시:

```json
{
  "stored_at": "2026-03-27T09:15:03.112345Z",
  "message_id": "mail-20260327-001",
  "subject": "고객 문의 메일",
  "list_item_id": "123",
  "list_item_url": "https://m365x12195465.sharepoint.com/sites/Report/Lists/RawWorkReports/123_.000",
  "field_count": 14
}
```

### 6-2. Graph 구독 생성 (POST /api/email-storage/graph/subscriptions)

메일박스 신규 메일 생성 이벤트를 구독한다.

요청 예시:

```json
{
  "mailbox_user_id": "report@M365x12195465.onmicrosoft.com",
  "notification_url": "http://localhost:8000/api/email-storage/graph/webhook",
  "client_state": "work-insight-webhook-secret",
  "expiration_minutes": 4230
}
```

응답 예시:

```json
{
  "id": "e4d4f32f-a166-4352-a9f6-5e1d19748e7c",
  "resource": "me/mailFolders('Inbox')/messages",
  "expiration_date_time": "2026-04-24T09:15:00+00:00",
  "client_state": "work-insight-webhook-secret",
  "notification_url": "http://localhost:8000/api/email-storage/graph/webhook"
}
```

### 6-3. Graph Webhook (POST /api/email-storage/graph/webhook)

Microsoft Graph가 메일 생성 이벤트를 이 엔드포인트로 전송한다.

동작:

- Graph validation 요청 (`validationToken` 쿼리): plain text로 토큰 반환
- 실제 notification 요청: 백그라운드 태스크로 메일 조회 → RawWorkReports 목록에 항목 추가

## 7. 데이터 흐름

1. `POST /api/email-storage/graph/subscriptions` 호출 → Graph에 구독 등록
2. 신규 이메일 수신 → Graph가 webhook notification 전송
3. 백엔드: Graph API에서 메일 조회 (본문, 첨부파일 메타데이터, MIME 원문)
4. 백엔드: ReceivedEmailSaveRequest 생성 → `save_email()` 호출
5. 백엔드: SharePoint RawWorkReports 리스트에 항목 추가
6. 응답 반환: list_item_id와 list_item_url

## 8. List 필드 매핑

RawWorkReports 목록의 필드:

| 필드명 | 타입 | 설명 |
|--------|------|------|
| Title | Text | `[timestamp] subject` |
| message_id | Text | 메시지 ID |
| internet_message_id | Text | SMTP Message-ID |
| subject | Text | 제목 |
| from_address | Text | 발신자 이메일 |
| to_addresses | JSON | 수신자 리스트 (JSON 배열) |
| cc_addresses | JSON | CC 리스트 (JSON 배열) |
| received_at | DateTime | 수신 시간 |
| body_text | Text | 텍스트 본문 |
| body_html | Text | HTML 본문 |
| raw_mime_base64 | Text | MIME 원본 (base64) |
| attachments | JSON | 첨부 메타데이터 (JSON) |
| metadata | JSON | 추가 메타데이터 (JSON) |
| stored_at | DateTime | 저장 시간 |

SharePoint 목록에 이 필드들이 사전 생성되어 있어야 한다.

## 9. 에러 처리

| 상황 | HTTP 코드 | 설명 |
|------|----------|----|
| 설정 부재 (TENANT_ID/CLIENT_ID/CLIENT_SECRET/SHAREPOINT_SITE_ID/SHAREPOINT_LIST_ID) | 400 | SharePointConfigurationError |
| Graph 토큰 획득 실패 | 502 | MicrosoftGraphRequestError → SharePointUploadError |
| 리스트 항목 추가 실패 | 502 | Graph API 오류 → SharePointUploadError |
| Webhook clientState 불일치 | 처리 안 함 | 백그라운드 태스크에서 예외 무시 |

## 10. 실행 예제

```bash
# 1. 백엔드 실행
cd backend
pip install -r ..\requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. 상태 확인
curl http://localhost:8000/api/email-storage/sharepoint/status

# 3. 구독 생성 (Graph 구독 ID 기록)
curl -X POST http://localhost:8000/api/email-storage/graph/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "mailbox_user_id": "report@M365x12195465.onmicrosoft.com",
    "notification_url": "http://your-public-url/api/email-storage/graph/webhook",
    "client_state": "work-insight-webhook-secret",
    "expiration_minutes": 4230
  }'

# 4. 직접 이메일 저장 (테스트용)
curl -X POST http://localhost:8000/api/email-storage/sharepoint/store \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "test-001",
    "subject": "테스트 이메일",
    "from_address": "test@example.com",
    "to_addresses": ["report@M365x12195465.onmicrosoft.com"],
    "received_at": "2026-03-27T09:15:00Z"
  }'
```

## 11. 주의사항

- **Webhook URL은 public URL이어야 함** (Graph가 외부에서 접근 가능)
- **HTTPS 권장** (프로덕션 환경)
- **구독 만료 시간**: 기본 4230분 (70.5시간, Graph 최대값)
- **구독 갱신** 필요: 현재 자동 갱신 미구현 (향후 추가 예정)
- **Raw MIME 저장**: `raw_mime_base64` 필드가 있으면 저장, 없으면 생략
- **첨부파일**: 메타데이터만 저장 (실제 파일은 미구현)
5. 조회한 결과를 기존 SharePoint 저장 서비스에 넘긴다.
6. SharePoint 문서 라이브러리에 JSON과 `.eml`이 저장된다.

## 10. 현재 구조에서의 권장 확장 순서

1. 메일 수신 워커 또는 Graph webhook을 붙여서 이 API를 호출한다.
2. 첨부파일 원본도 SharePoint에 개별 업로드한다.
3. 저장 성공 이력을 DB에 남긴다.
4. 중복 저장 방지를 위해 `message_id` 기준 idempotency를 추가한다.
5. subscription 만료 전에 자동 갱신 작업을 추가한다.