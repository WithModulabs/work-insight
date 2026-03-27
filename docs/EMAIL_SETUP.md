# Azure AD / Office 365 이메일 연결 가이드

WorkInsight에서 Azure AD 테넌트의 Office 365 이메일 서비스를 사용하여 자동으로 아침 브리핑 및 리스크 알림을 이메일로 전송할 수 있습니다.

## 📋 사전 준비

- Azure 구독 및 Azure AD 테넌트 접근 권한
- Office 365 라이선스 (이메일 서비스)
- Microsoft Entra ID (Azure AD) 앱 등록 권한

---

## 🔧 설정 단계

### Step 1: Azure AD 앱 등록

1. **Azure Portal** 접속
   - https://portal.azure.com 접속
   
2. **Entra ID 이동**
   - 좌측 탐색 메뉴 → "Azure Entra ID" 또는 "Azure Active Directory"

3. **앱 등록 (App registrations)**
   - 좌측 메뉴 → "App registrations" 클릭
   - "+ New registration" 클릭

4. **앱 등록 정보 입력**
   ```
   Name: WorkInsight Email Service
   Supported account types: Accounts in this organizational directory only
   Redirect URI: (선택사항) Web - http://localhost:3000/callback
   ```
   - "Register" 클릭

### Step 2: 클라이언트 자격증명 생성

1. **등록된 앱 선택**
   - "WorkInsight Email Service" 앱 클릭

2. **클라이언트 ID 복사**
   - "Application (client) ID" 값 복사 → `.env` 파일의 `AZURE_CLIENT_ID`

3. **테넌트 ID 확인**
   - "Directory (tenant) ID" 값 복사 → `.env` 파일의 `AZURE_TENANT_ID`

4. **클라이언트 시크릿 생성**
   - 좌측 메뉴 → "Certificates & secrets" 클릭
   - "+ New client secret" 클릭
   - Description: "WorkInsight Email" 입력
   - Expires: "12 months" 선택
   - "Add" 클릭
   - **"Value" 복사** → `.env` 파일의 `AZURE_CLIENT_SECRET`
   
   ⚠️ **중요**: 시크릿은 한 번만 표시됩니다. 반드시 복사하여 안전한 곳에 저장하세요.

### Step 3: API 권한 설정

1. **권한 추가**
   - 좌측 메뉴 → "API permissions" 클릭
   - "+ Add a permission" 클릭

2. **Microsoft Graph 선택**
   - "Microsoft APIs" 탭
   - "Microsoft Graph" 클릭

3. **권한 선택**
   - "Application permissions" 클릭
   - 검색: "Mail.Send"
   - ☑️ "Mail.Send" 체크
   - ☑️ "User.Read.All" 체크 (선택사항)
   - "Add permissions" 클릭

4. **관리자 승인**
   - "Grant admin consent for [Tenant Name]" 클릭
   - "Yes" 확인

### Step 4: 환경 변수 설정

`.env` 파일 또는 OS 환경 변수로 다음을 설정합니다:

```bash
# Azure AD 설정
AZURE_TENANT_ID=5a4fecd1-2599-42cc-9964-6fc44f346df0
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here
EMAIL_SENDER=JoniS@M365x12195465.OnMicrosoft.com

# 이메일 서비스 활성화
EMAIL_ENABLED=True
```

### Step 5: 애플리케이션 설정 (선택사항)

```python
# backend/config.py 확인
AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")
EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
```

---

## 🧪 테스트

### API를 통한 이메일 전송 테스트

#### 1. 아침 브리핑 이메일 전송

```bash
curl -X POST "http://localhost:8002/dashboard/morning-brief/send-email" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "user@example.com",
    "organization_name": "WorkInsight"
  }'
```

**응답 예시:**
```json
{
  "status": "success",
  "message": "✅ 아침 브리핑 이메일이 user@example.com로 전송되었습니다",
  "to": "user@example.com",
  "subject": "[WorkInsight] 2024년 3월 27일 아침 경영 브리핑",
  "sent_at": "2024-03-27T09:30:00"
}
```

#### 2. 리스크 알림 이메일 전송

```bash
curl -X POST "http://localhost:8002/dashboard/risk-alert/send-email" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "ceo@example.com",
    "organization_name": "WorkInsight"
  }'
```

**응답 예시:**
```json
{
  "status": "success",
  "message": "✅ 리스크 알림 이메일이 ceo@example.com로 전송되었습니다",
  "to": "ceo@example.com",
  "risk_count": 5,
  "sent_at": "2024-03-27T09:15:00"
}
```

---

## 📖 API 엔드포인트

### 아침 브리핑 이메일 전송

```
POST /dashboard/morning-brief/send-email
Query Parameters:
  - recipient_email (required): 수신자 이메일
  - organization_name (optional): 조직명 (기본값: "WorkInsight")
```

**응답:**
```json
{
  "status": "success|error",
  "message": "상태 메시지",
  "to": "수신자 이메일",
  "subject": "이메일 제목",
  "sent_at": "전송 시간"
}
```

### 리스크 알림 이메일 전송

```
POST /dashboard/risk-alert/send-email
Query Parameters:
  - recipient_email (required): 수신자 이메일
  - organization_name (optional): 조직명 (기본값: "WorkInsight")
```

**응답:**
```json
{
  "status": "success|error",
  "message": "상태 메시지",
  "to": "수신자 이메일",
  "risk_count": "감지된 리스크 개수",
  "sent_at": "전송 시간"
}
```

---

## 🐛 문제 해결

### 문제 1: "인증 실패" 오류

```
❌ Azure AD 인증 초기화 실패: Invalid credentials
```

**해결:**
1. `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` 확인
2. 클라이언트 시크릿 만료 여부 확인
3. 새 시크릿 재생성 필요

### 문제 2: "권한 부족" 오류

```
❌ 토큰 획득 실패: Insufficient privileges to complete the operation
```

**해결:**
1. Azure AD 앱에 "Mail.Send" 권한 추가 확인
2. 관리자 승인 (Grant admin consent) 완료 확인
3. 권한 변경 후 15분 대기

### 문제 3: "사용자를 찾을 수 없음" 오류

```
❌ 이메일 전송 실패 (404): User not found
```

**해결:**
1. `EMAIL_SENDER` 이메일 주소 확인
2. 테넌트 내 존재하는 계정인지 확인
3. 계정 주소를 정확하게 입력했는지 확인

---

## 🔐 보안 권장사항

1. **클라이언트 시크릿 관리**
   - `.env` 파일을 `.gitignore`에 추가
   - 프로덕션 환경에서는 Azure Key Vault 사용
   
2. **권한 최소화**
   - "Mail.Send" 권한만 부여
   - 필요한 최소 권한만 설정
   
3. **토큰 만료**
   - 클라이언트 시크릿 정기적 갱신 (6-12개월)
   - 사용하지 않는 앱 등록 삭제

4. **감시**
   - Azure AD 로그 모니터링
   - 이메일 전송 실패 로깅 및 알림 설정

---

## 📞 문의

워크인사이트 이메일 연동에 관한 문제가 있으면:
1. 로그 확인: `backend` 콘솔 출력 메시지
2. Azure Portal에서 앱 등록 상태 확인
3. Microsoft Graph API 문서 참고: https://docs.microsoft.com/en-us/graph/api/

---

## 참고 자료

- [Microsoft Graph API - Send Email](https://docs.microsoft.com/en-us/graph/api/user-sendmail)
- [Azure AD Authentication Library](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [Azure Identity SDK for Python](https://docs.microsoft.com/en-us/python/api/azure-identity/)
