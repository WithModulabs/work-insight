# WorkInsight MVP 아키텍처

## 시스템 개요

WorkInsight는 퇴근보고, 1:1 상담, 프로젝트 정보를 종합하여 대표와 팀장이 조직 상태를 파악하고 의사결정을 지원하는 경영지원 에이전트입니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    프론트엔드 (React/Vanilla JS)             │
│  - 퇴근보고 입력                                            │
│  - 1:1 상담 기록                                            │
│  - 대시보드 (팀/전사)                                       │
│  - RAG Copilot 인터페이스                                  │
└──────────────┬──────────────────────────────────────────────┘
               │ HTTP/REST
┌──────────────▼──────────────────────────────────────────────┐
│              FastAPI 백엔드 (:8000)                         │
├─────────────────────────────────────────────────────────────┤
│  API Layer                                                  │
│  ├─ /api/reports        - 퇴근보고 CRUD                    │
│  ├─ /api/oneone         - 1:1 상담 CRUD                    │
│  ├─ /api/dashboard      - 대시보드 데이터                  │
│  └─ /api/copilot        - Copilot 질의                     │
├─────────────────────────────────────────────────────────────┤
│  Service Layer                                              │
│  ├─ ReportService       - 보고 비즈니스 로직               │
│  ├─ OneOneService       - 상담 비즈니스 로직               │
│  ├─ DashboardService    - 대시보드 데이터 생성             │
│  └─ CopilotService      - Copilot 로직                     │
├─────────────────────────────────────────────────────────────┤
│  Analysis Layer                                             │
│  ├─ ReportAnalyzer      - 퇴근보고 분석                    │
│  ├─ RiskSignalDetector  - 리스크 신호 탐지                 │
│  ├─ BriefingGenerator   - 아침 브리핑 생성                │
│  └─ CopilotEngine       - RAG 기반 질의 처리              │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├─ ORM: SQLAlchemy                                        │
│  ├─ DB: SQLite (프로토타입) / PostgreSQL (프로덕션)        │
│  └─ Vector DB: Chroma (RAG용)                              │
└─────────────────────────────────────────────────────────────┘
```

## 모듈 구조

### 1. API 라우터 (`app/api/`)

#### reports.py - 퇴근보고 API
- `POST /api/reports/` - 새 보고 작성
  - 자동 분석: 감정점수, 피로도, 리스크 키워드
- `GET /api/reports/{report_id}` - 보고 조회
- `GET /api/reports/my/` - 내 보고 목록
- `GET /api/reports/stats/risk` - 리스크 통계

#### oneone.py - 1:1 상담 API
- `POST /api/oneone/` - 상담 기록
  - 액션아이템 자동 생성
- `GET /api/oneone/{oneone_id}` - 상담 조회
- `POST /api/action-items/` - 액션아이템 생성
- `POST /api/action-items/{action_id}/complete` - 완료 처리

#### dashboard.py - 대시보드 API
- `GET /api/dashboard/team/{team_id}` - 팀 대시보드
- `GET /api/dashboard/org/` - 전사 대시보드
- `GET /api/dashboard/overview` - 종합 개요
- `GET /api/dashboard/projects/{project_id}` - 프로젝트 상세

#### copilot.py - Copilot API
- `POST /api/copilot/query` - 자연어 질의 처리
- `GET /api/copilot/suggestions` - 추천 질문
- `GET /api/copilot/history` - 질의 히스토리
- `POST /api/copilot/feedback` - 응답 피드백

### 2. 데이터 모델 (`app/models/`)

```
User
├─ 팀 정보 (Team)
├─ 퇴근보고 (DailyReport)
└─ 상담 기록 (OneOnOneRecord)
    └─ 액션아이템 (ActionItem)

Project
├─ 팀 (Team)
└─ 퇴근보고 (DailyReport)

RiskSignal
└─ 사용자 (User)

MorningBrief
└─ 수신자 (User)

CopilotQuery
└─ 사용자 (User)
```

### 3. 분석 엔진 (`app/analysis/`)

#### analyzer.py

**ReportAnalyzer**
- 퇴근보고 자동 분석
- 감정점수 계산 (-1 ~ 1)
- 피로도 추정 (0 ~ 1)
- 리스크 키워드 추출
- 갈등 신호 탐지

**RiskSignalDetector**
- 이탈 위험 (Churn Risk)
- 번아웃 신호 (Burnout)
- 과부하 신호 (Overload)
- 협업 갈등 (Conflict)

**BriefingGenerator**
- 팀원용 아침 브리핑 (개인 우선순위)
- 팀장용 아침 브리핑 (팀 현황)
- 대표용 아침 브리핑 (전사 요약)

#### copilot.py

**CopilotEngine**
- 질의 의도 분류 (status, analysis, people, action, comparison)
- 하이브리드 검색 (키워드 + 의미)
- 증거 기반 응답 생성
- 근거 포함 (근거 문서 링크)
- 후속 질문 추천
- 신뢰도 계산

**QuerySuggester**
- 역할별 추천 질문
- 컨텍스트 기반 제안

## 데이터 흐름

### 1. 퇴근보고 제출 프로세스
```
팀원 입력
    ↓
ReportAnalyzer 분석
    ├─ 감정 분석
    ├─ 피로도 계산
    ├─ 리스크 키워드 추출
    └─ 갈등 신호 탐지
    ↓
DB 저장 (DailyReport)
    ↓
RiskSignalDetector 실행
    ├─ 번아웃 체크
    ├─ 이탈 위험 체크
    ├─ 과부하 체크
    └─ 갈등 체크
    ↓
RiskSignal 생성 (필요시)
    ↓
다음날 아침 브리핑에 포함
```

### 2. Copilot 질의 처리 프로세스
```
사용자 질의
    ↓
의도 분류 (Intent Classification)
    ↓
권한 기반 검색 범위 결정
    ↓
하이브리드 검색 (Hybrid Search)
    ├─ 키워드 검색
    ├─ 의미 검색 (Vector DB)
    └─ 의도별 특화 검색
    ↓
근거 분석 (Evidence Analysis)
    ├─ 상태 분석
    ├─ 원인 분석
    ├─ 사람 분석
    └─ 액션 분석
    ↓
답변 생성 (Response Generation)
    ├─ 결론
    ├─ 근거
    ├─ 신뢰도
    └─ 후속 질문
    ↓
응답 반환
```

## 권한 정책

| 역할 | 퇴근보고 | 상담 | 대시보드 | 리스크신호 |
|------|--------|------|----------|-----------|
| 팀원 | 본인만 조회 | 본인만 조회 | - | - |
| 팀장 | 팀 조회 | 팀 관리 | 팀 대시보드 | 팀 신호 |
| 대표 | 전사 조회 | 전사 요약만 | 전사 대시보드 | 전사 신호 |
| HR | 제한적 조회 | 민감정보 접근 | 조직 리스크 | 케어신호 |
| 관리자 | 전체 | 전체 | 전체 | 전체 |

## 설정 및 환경변수

```env
# 기본 설정
APP_NAME=WorkInsight
APP_VERSION=0.1.0
DEBUG=True

# 데이터베이스
DATABASE_URL=sqlite:///./workinsight.db

# LLM/OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo-16k

# RAG
VECTOR_DB_TYPE=chroma
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# 분석 임계값
RISK_THRESHOLD=0.7
SENTIMENT_THRESHOLD=-0.3
```

## 개발 로드맵

### Phase 1: MVP (현재)
- ✅ 기본 데이터 모델
- ✅ 퇴근보고 입력/조회/분석
- ✅ 1:1 상담 관리
- ✅ 기본 대시보드
- ✅ RAG 기반 Copilot (프로토타입)
- ✅ 리스크 신호 탐지
- 🚀 아침 브리핑 생성/발송

### Phase 2: 고도화
- 실시간 대시보드 (WebSocket)
- 고급 분석 (트렌드, 상관관계)
- 프로젝트 중심 대시보드
- 외부 API 연동 (Slack, Teams, Notion)
- 알림/메일 자동화
- 모바일 앱

### Phase 3: 엔터프라이즈
- AI 모델 커스터마이징
- 멀티 조직 지원
- SLA/배포 자동화
- 고급 권한 관리
- 코딩 최소화 (No-code 데이터 맵핑)

## 배포

### 로컬 개발
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 프로더션 배포
```bash
# Docker 불드
docker build -t workinsight:latest .

# Azure Container Apps / App Service / Functions로 배포
```

## 성능 최적화

- 데이터베이스 인덱싱 (report_date, user_id, risk_level)
- 캐싱 (Redis) - 대시보드 데이터
- 비동기 처리 - 아침 브리핑 생성
- 배치 처리 - 리스크 신호 탐지
- CDN - 프론트엔드 정적 파일

## 모니터링

- Application Insights (Python SDK)
- 에러 추적 (Sentry)
- 성능 모니터링 (DataDog)
- 감사 로그 (User actions, Copilot queries)

## 보안

- JWT 인증
- RBAC (Role-Based Access Control)
- 민감정보 암호화 (HR 메모)
- API 레이트 제한
- CORS 설정
- SQL Injection 방지 (ORM 사용)
- XSS 방지 (Pydantic validation)
