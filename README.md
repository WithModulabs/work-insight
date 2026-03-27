# WorkInsight - 경영 인사이트 Copilot MVP

퇴근보고, 1:1 상담, 프로젝트 진행 데이터를 기반으로 대표와 팀장이 조직 상태를 파악하고, 매일 실행 우선순위를 받고, 궁금한 것을 직접 질문할 수 있는 경영지원 에이전트입니다.

## 프로젝트 구조

```
agenthon/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── models/         # SQLAlchemy ORM 모델
│   │   ├── schemas/        # Pydantic 스키마
│   │   ├── api/            # API 라우터
│   │   ├── services/       # 비즈니스 로직
│   │   ├── analysis/       # AI/분석 엔진
│   │   ├── utils/          # 공통 유틸리티
│   │   └── main.py         # FastAPI 앱 진입점
│   ├── config.py           # 설정 파일
│   └── requirements.txt     # 패키지 의존성
├── frontend/               # 프론트엔드 웹 UI
├── docs/                   # 문서
└── README.md
```

## 주요 모듈

### 1. 퇴근보고 (Daily Report)
- 팀원이 매일 작성하는 퇴근보고 관리
- 자동 분류 및 분석 (프로젝트 태깅, 이슈 추출, 감정 분석)

### 2. 1:1 상담 (One-on-One)
- 팀장-팀원 상담 기록 관리
- 액션아이템 추적
- 민감정보 접근 제어

### 3. 대시보드 (Dashboard)
- 팀장용: 팀원별 업무 현황, 미완료 누적, 반복 이슈
- 대표용: 전사 프로젝트 진행, 지연 위험, 조직 피로도

### 4. RAG 기반 Copilot
- 자연어 질의 처리
- 관련 데이터 하이브리드 검색
- 근거 포함 답변 생성

### 5. 아침 브리핑
- 자동 생성 및 이메일 발송
- 대상별 맞춤 콘텐츠

### 6. 리스크 신호 탐지
- 이탈 리스크, 번아웃, 갈등 신호 감지
- 조기 경고 및 추천 액션

## 설치 및 실행

### 1. 환경 설정
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 데이터베이스 초기화
```bash
alembic upgrade head
```

### 3. 서버 실행
```bash
uvicorn app.main:app --reload
```

API 문서: http://localhost:8000/docs

### 4. 프론트엔드 실행
```bash
cd frontend
# 간단한 HTTP 서버로 실행 가능
```

## 핵심 API 엔드포인트

### 퇴근보고
- `POST /api/reports/` - 퇴근보고 작성
- `GET /api/reports/{report_id}` - 보고 조회
- `GET /api/reports/my/` - 내 보고 목록

### 1:1 상담
- `POST /api/oneone/` - 상담 기록
- `GET /api/oneone/{record_id}` - 상담 조회
- `POST /api/action-items/` - 액션 아이템 생성

### 대시보드
- `GET /api/dashboard/team/{team_id}` - 팀 대시보드
- `GET /api/dashboard/org/` - 전사 대시보드

### Copilot
- `POST /api/copilot/query` - 자연어 질의
- `GET /api/copilot/suggestions` - 추천 질문

## 개발 로드맵

### MVP Phase 1
- ✅ 기본 데이터 모델
- ✅ 퇴근보고 입력/조회
- ✅ 1:1 상담 관리
- ✅ 기본 대시보드
- ✅ RAG 기반 Copilot
- ✅ 리스크 신호 탐지
- 🚀 아침 브리핑 발송

### Phase 2
- 평가 및 피드백
- 고급 분석 및 트렌드
- 모바일 앱
- 멀티언어 지원

## 환경 변수 설정

`.env` 파일 생성:
```
OPENAI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./workinsight.db
SECRET_KEY=your_secret_key
```

## 라이선스

MIT
