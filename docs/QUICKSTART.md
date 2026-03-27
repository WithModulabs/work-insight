# WorkInsight 빠른 시작 가이드

## 설치

### 1. 저장소 클론 및 디렉토리 이동
```bash
cd /Users/user/Documents/agenthon
```

### 2. Python 가상환경 생성
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 설정
```bash
# .env 파일 생성 (backend 디렉토리에서)
cp backend/.env.example backend/.env

# 엔진 키 설정 (선택사항, 데모용으로는 불필요)
# .env 파일에서 OPENAI_API_KEY 설정
```

## 실행

### 백엔드 API 서버 실행
```bash
# backend 디렉토리로 이동
cd backend

# FastAPI 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

### 프론트엔드 실행
```bash
# 별도의 터미널에서:
cd frontend

# 간단한 HTTP 서버로 실행 (Python 내장)
python3 -m http.server 3000
```

웹 UI: http://localhost:3000

## 주요 기능

### 1. 퇴근보고 작성
- 오늘 한 일, 미완료 업무, 내일 계획 기입
- 자동 감정 분석 및 피로도 계산
- 리스크 키워드 자동 추출

### 2. 대시보드
- **팀 대시보드**: 팀원별 현황, 긴급 이슈, 위험 신호
- **전사 대시보드**: 프로젝트 진행, 조직 건강도
- 필터 및 드릴다운 지원

### 3. RAG Copilot
- 자연어 질의 처리
- 예시:
  - "이번 주 가장 위험한 프로젝트는?"
  - "우리 팀에서 케어가 필요한 사람은?"
  - "최근 반복되는 이슈는?"

### 4. 1:1 상담
- 상담 기록 및 액션아이템 관리
- 만족도, 고민, 피드백 기록
- 후속 액션 추적

## API 엔드포인트

### 퇴근보고
```
POST   /api/reports/              - 새 보고 작성
GET    /api/reports/{id}          - 보고 조회
GET    /api/reports/my/           - 내 보고 목록
GET    /api/reports/stats/risk    - 리스크 통계
```

### 1:1 상담
```
POST   /api/oneone/               - 상담 기록
GET    /api/oneone/{id}           - 상담 조회
POST   /api/action-items/         - 액션 생성
POST   /api/action-items/{id}/complete  - 액션 완료
```

### 대시보드
```
GET    /api/dashboard/team/{team_id}    - 팀 대시보드
GET    /api/dashboard/org/              - 전사 대시보드
GET    /api/dashboard/overview          - 종합 개요
```

### Copilot
```
POST   /api/copilot/query         - 질의 처리
GET    /api/copilot/suggestions   - 추천 질문
GET    /api/copilot/history       - 질의 히스토리
```

## 샘플 API 호출

### 퇴근보고 작성
```bash
curl -X POST "http://localhost:8000/api/reports/" \
  -H "Content-Type: application/json" \
  -d '{
    "accomplished": "프로젝트 A 진행회의, 스펙 검토",
    "not_completed": "데이터베이스 설계",
    "tomorrow_plan": "DB 스키마 완성",
    "issues": "API 스펙이 지연됨",
    "support_needed": "백엔드 팀의 빠른 검토 필요",
    "fatigue_level": 0.6
  }'
```

### Copilot 질의
```bash
curl -X POST "http://localhost:8000/api/copilot/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "이번 주 가장 위험한 프로젝트는?"
  }' \
  -G -d "user_role=director"
```

## 디버깅

### 로그 확인
```bash
# 터미널에서 바로 확인 가능 (--reload 옵션 사용시)
```

### 데이터베이스 초기화
```bash
# SQLite 데이터베이스 재초기화
rm backend/workinsight.db

# 다시 실행하면 자동 생성됨
```

### API 테스트
```bash
# Swagger UI에서 직접 테스트
http://localhost:8000/docs
```

## 프로토타입 데이터

현재 MVP는 메모리 기반 저장소를 사용합니다 (실제 DB 연결 전).

프로덕션 배포 시:
1. SQLite → PostgreSQL로 변경
2. Vector DB (Chroma → Pinecone) 연결
3. 실제 LLM (OpenAI, Claude, Gemini) 연결

## 다음 단계

### 단기 (1주)
- [ ] 실제 데이터베이스 연결 (PostgreSQL)
- [ ] 사용자 인증 (JWT)
- [ ] 아침 브리핑 이메일 발송
- [ ] 고급 Copilot (실제 LLM 연결)

### 중기 (1개월)
- [ ] 모바일 앱 (React Native / Flutter)
- [ ] Slack 연동
- [ ] 고급 분석 (트렌드, 상관관계)
- [ ] 외부 도구 연동 (Jira, Asana)

### 장기 (3개월)
- [ ] 글로벌 확장 (다국어)
- [ ] 엔터프라이즈 기능:
  - [ ] 감사 로그
  - [ ] 고급 권한 관리
  - [ ] 데이터 거버넌스
  - [ ] SLA 관리

## 트러블슈팅

### npm 모듈 오류
```bash
# node_modules 재설치
rm -rf node_modules package-lock.json
npm install
```

### 포트 충돌
```bash
# 다른 포트로 실행
uvicorn app.main:app --reload --port 8001
python3 -m http.server 3001
```

### CORS 오류
config.py에서 CORS_ORIGINS 확인:
```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## 지원

문제가 발생하면:
1. 로그 확인
2. 이슈 트래커 참고
3. 팀 채널에서 질문

성공적인 배포를 기원합니다! 🚀
