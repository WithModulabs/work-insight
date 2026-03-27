# SharePoint Email Storage

## 개요

이 문서는 백엔드가 수신한 이메일 데이터를 SharePoint 문서 라이브러리에 저장하는 기능의 설정 방법을 설명한다.

현재 구현 범위는 다음과 같다.

- 백엔드가 이메일 payload를 받는다.
- 이메일 메타데이터를 JSON 파일로 SharePoint에 저장한다.
- `raw_mime_base64`가 있으면 원본 메일을 `.eml` 파일로 함께 저장한다.
- Microsoft Graph subscription 생성 API를 제공한다.
- Microsoft Graph webhook 알림을 받아서 메일을 조회한 뒤 SharePoint에 저장한다.

현재 구현하지 않은 범위는 다음과 같다.

- 첨부파일 개별 업로드
- 구독 갱신 스케줄러
- 저장 실패 재시도 큐

## 1. Microsoft Entra 앱 등록

1. Azure Portal에서 App Registration을 생성한다.
2. `Application (client) ID`와 `Directory (tenant) ID`를 기록한다.
3. `Certificates & secrets`에서 client secret을 발급한다.
4. `API permissions`에서 Microsoft Graph Application Permission을 추가한다.

필수 권한 예시:

- `Sites.ReadWrite.All`
- `Files.ReadWrite.All`
- `Mail.Read`
- `Subscription.ReadWrite.All`

권한 추가 후 관리자 동의를 완료해야 한다.

## 2. SharePoint Site ID와 Drive ID 확인

저장 대상은 SharePoint 문서 라이브러리다. 구현은 `site_id`와 `drive_id`를 직접 사용한다.

예시 Graph 호출:

```text
GET https://graph.microsoft.com/v1.0/sites/{hostname}:/sites/{site-path}
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drives
```

메일을 저장할 문서 라이브러리의 `drive.id`를 확인해서 환경변수에 넣으면 된다.

## 3. 환경변수 설정

`backend/.env.example`를 참고해서 실제 `.env`에 아래 값을 넣는다.

```env
MICROSOFT_TENANT_ID=your-tenant-id
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
SHAREPOINT_SITE_ID=your-site-id
SHAREPOINT_DRIVE_ID=your-drive-id
SHAREPOINT_EMAIL_FOLDER=inbound-emails
GRAPH_MAILBOX_USER_ID=shared-mailbox@example.com
GRAPH_NOTIFICATION_URL=https://your-public-domain/api/email-storage/graph/webhook
GRAPH_SUBSCRIPTION_CLIENT_STATE=change-this-random-secret
GRAPH_SUBSCRIPTION_RESOURCE=
GRAPH_SUBSCRIPTION_EXPIRATION_MINUTES=1440
```

## 4. 백엔드 실행

```bash
cd backend
pip install -r ..\requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 5. 상태 확인

다음 엔드포인트로 SharePoint 설정 반영 여부를 볼 수 있다.

```text
GET /api/email-storage/sharepoint/status
```

응답 예시:

```json
{
  "configured": true,
  "default_folder": "inbound-emails"
}
```

## 6. Graph 구독 생성

메일박스 신규 메일 생성 이벤트를 구독하려면 아래 엔드포인트를 호출한다.

```text
POST /api/email-storage/graph/subscriptions
```

요청 예시:

```json
{
  "mailbox_user_id": "shared-mailbox@example.com",
  "notification_url": "https://your-public-domain/api/email-storage/graph/webhook",
  "client_state": "change-this-random-secret",
  "sharepoint_folder": "inbound-emails/support",
  "expiration_minutes": 1440
}
```

참고:

- `resource`를 주지 않으면 기본값으로 `users/{mailbox}/mailFolders('Inbox')/messages`를 사용한다.
- `sharepoint_folder`는 webhook 처리 시 쿼리로 넘길 때 사용하면 되고, 현재 구독 응답 자체에는 저장되지 않는다.

## 7. Graph webhook 엔드포인트

Graph는 `notification_url`로 validation request와 실제 notification request를 보낸다.

엔드포인트:

```text
POST /api/email-storage/graph/webhook
```

동작:

- `validationToken` 쿼리가 있으면 plain text로 그대로 반환한다.
- 실제 notification이면 백그라운드 태스크로 메일을 조회하고 SharePoint에 저장한다.

메일 저장 폴더를 강제하려면 webhook URL에 쿼리를 붙일 수 있다.

예시:

```text
https://your-public-domain/api/email-storage/graph/webhook?sharepoint_folder=inbound-emails/support
```

## 8. 직접 이메일 저장 요청

다음 엔드포인트로 수신 이메일을 저장한다.

```text
POST /api/email-storage/sharepoint/store
```

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
  "raw_mime_base64": null,
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
  },
  "sharepoint_folder": "inbound-emails/support"
}
```

응답 예시:

```json
{
  "stored_at": "2026-03-27T09:15:03.112345Z",
  "message_id": "mail-20260327-001",
  "subject": "고객 문의 메일",
  "sharepoint_folder": "inbound-emails/support",
  "metadata_file": {
    "item_id": "01ABCDEF...",
    "name": "20260327T091500Z_...json",
    "path": "inbound-emails/support/20260327T091500Z_...json",
    "web_url": "https://..."
  },
  "mime_file": null
}
```

## 9. 처리 흐름

1. `POST /api/email-storage/graph/subscriptions`로 Graph 구독을 만든다.
2. Microsoft Graph가 webhook validation을 호출한다.
3. 신규 메일이 오면 Graph가 webhook notification을 보낸다.
4. 백엔드가 Graph API로 메일 본문, 수신자, MIME 원문, 첨부파일 메타데이터를 조회한다.
5. 조회한 결과를 기존 SharePoint 저장 서비스에 넘긴다.
6. SharePoint 문서 라이브러리에 JSON과 `.eml`이 저장된다.

## 10. 현재 구조에서의 권장 확장 순서

1. 메일 수신 워커 또는 Graph webhook을 붙여서 이 API를 호출한다.
2. 첨부파일 원본도 SharePoint에 개별 업로드한다.
3. 저장 성공 이력을 DB에 남긴다.
4. 중복 저장 방지를 위해 `message_id` 기준 idempotency를 추가한다.
5. subscription 만료 전에 자동 갱신 작업을 추가한다.