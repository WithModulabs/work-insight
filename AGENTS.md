# AGENTS.md

## 목적

이 문서는 현재 `work-insight` 저장소를 빠르게 파악하고, 다음 작업자가 구현 상태와 리스크를 오해하지 않도록 돕기 위한 코드베이스 리뷰다.

핵심 판단은 다음과 같다.

- 현재 저장소는 "동작하는 프로토타입"에 가깝다.
- 문서에 적힌 목표 아키텍처와 실제 구현 사이의 간극이 크다.
- 백엔드는 FastAPI 기반이지만 영속 저장소, 인증, 서비스 계층, 실제 RAG 연동은 아직 없다.
- 프론트엔드는 React가 아니라 정적 HTML + Vanilla JS이며, 상당수 데이터는 목업 응답으로 렌더링된다.

## 저장소 개요

### 루트

- `backend/`: FastAPI 애플리케이션
- `frontend/`: 정적 웹 UI
- `docs/`: 목표 아키텍처 및 빠른 시작 문서
- `requirements.txt`: Python 의존성

### 실제 진입점

- 백엔드 진입점: `backend/app/main.py`
- 프론트엔드 진입점: `frontend/index.html`

## 실제 구현 상태

### 백엔드

#### 애플리케이션 부트스트랩

`backend/app/main.py`

- FastAPI 앱 생성
- CORS 설정 적용
- 라우터 4개 등록
  - `/api/reports`
  - `/api/oneone`
  - `/api/dashboard`
  - `/api/copilot`
- 루트 `/` 및 `/health` 엔드포인트 제공

#### 설정

`backend/config.py`

- `BaseSettings` 기반 설정 객체 사용
- `.env` 파일을 읽도록 구성됨
- DB, OpenAI, SMTP, CORS, 분석 임계값 필드가 존재
- 다만 이 설정 값들 중 상당수는 실제 런타임 로직에서 적극적으로 사용되지 않음

#### 데이터 모델

`backend/app/models/models.py`

- SQLAlchemy ORM 모델이 정의되어 있음
- 주요 엔티티
  - `User`
  - `Team`
  - `Project`
  - `DailyReport`
  - `OneOnOneRecord`
  - `ActionItem`
  - `RiskSignal`
  - `MorningBrief`
  - `CopilotQuery`
- 그러나 현재 API 라우터는 이 ORM 모델을 사용하지 않음
- 실제 저장은 전부 라우터 내부 전역 딕셔너리로 처리됨

#### 스키마

`backend/app/schemas/schemas.py`

- 요청/응답용 Pydantic 스키마 존재
- 프로토타입 수준에서는 충분하지만, DB 모델과 완전한 일관성은 없음

#### API 구현

`backend/app/api/reports.py`

- 퇴근보고 생성/조회/리스트/리스크 통계 제공
- `ReportAnalyzer`를 호출해 감정/피로도/리스크를 계산
- 저장 방식은 `reports_db` 딕셔너리
- 인증 없음, `author_id`는 하드코딩

`backend/app/api/oneone.py`

- 1:1 기록 생성/조회
- 액션아이템 생성/완료 처리
- 저장 방식은 `oneones_db`, `actions_db` 딕셔너리
- 인증 없음, `conducted_by_id`, `assigned_by_id`는 하드코딩

`backend/app/api/dashboard.py`

- 팀/전사/개요/프로젝트 상세 엔드포인트 제공
- 전부 시뮬레이션 데이터 반환
- 실제 DB 조회나 집계 없음

`backend/app/api/copilot.py`

- 자연어 질의, 추천 질문, 히스토리, 피드백 엔드포인트 제공
- 내부적으로 `CopilotEngine` 호출
- 히스토리는 메모리 리스트에 적재
- 실제 LLM 호출은 없음

#### 분석 엔진

`backend/app/analysis/analyzer.py`

- `ReportAnalyzer`
  - 키워드 기반 리스크 분류
  - 감정 점수 계산
  - 피로도 추정
  - 갈등 신호 탐지
- `RiskSignalDetector`
  - 번아웃
  - 이탈 리스크
  - 과부하
  - 갈등
- `BriefingGenerator`
  - HTML 형태 브리핑 생성 로직 일부 포함

`backend/app/analysis/copilot.py`

- `CopilotEngine`
  - 질의 의도 분류
  - 권한 기반 검색 범위 결정
  - 목업 문서 검색
  - 근거 분석 및 후속 질문 생성
- 구현은 개념 검증용이며, 실제 RAG나 벡터 DB 연결은 없음

### 프론트엔드

`frontend/index.html`

- 단일 페이지 형태 UI
- 홈, 퇴근보고, 대시보드, Copilot, 프로필 섹션 포함
- 별도 빌드 도구 없이 브라우저에서 정적 파일로 열 수 있는 구조

`frontend/js/app.js`

- 네비게이션 및 섹션 전환
- 탭 전환
- 대시보드 뷰 전환
- 인사말, 실시간 통계, 리스크 신호 시뮬레이션
- 저장되지 않은 변경 경고

`frontend/js/api.js`

- 실제 HTTP 요청 함수 틀은 있으나 주석 처리되어 있음
- 현재는 `mockApiResponses`를 통해 프론트 내부에서 목업 데이터 사용
- 보고 제출, Copilot 질의, 추천 질문 로드 등이 백엔드 없이도 동작하는 형태

## 문서와 실제 구현의 차이

### README 및 architecture 문서가 더 앞서 있다

문서에는 아래 요소가 있는 것처럼 보이지만 현재 저장소 기준으로는 구현되지 않았거나 부분 구현 상태다.

- 서비스 계층 (`app/services/`) 없음
- 실제 DB 세션/리포지토리 계층 없음
- Alembic 설정 파일 없음
- 인증/인가 없음
- 민감정보 접근 통제 없음
- 실제 이메일 발송 없음
- 실제 RAG, Chroma, 벡터 검색 없음
- React 프론트엔드 없음
- 실시간 대시보드 없음

즉 문서는 "목표 설계"에 가깝고, 코드는 "MVP 데모" 단계다.

## 핵심 리스크 및 주의사항

### 1. 영속성 부재

모든 주요 데이터가 프로세스 메모리에 저장된다.

- 서버 재시작 시 데이터 유실
- 멀티프로세스 환경에서 일관성 없음
- 테스트 재현성 낮음

영향 파일:

- `backend/app/api/reports.py`
- `backend/app/api/oneone.py`
- `backend/app/api/copilot.py`

### 2. Copilot 응답 타입 불일치

`backend/app/analysis/copilot.py`의 `_generate_response()`는 딕셔너리를 반환한다. 하지만 `backend/app/api/copilot.py`는 그 값을 `response_text`에 그대로 넣고 있고, 스키마 `CopilotQueryResponse.response_text`는 문자열을 기대한다.

이 상태에서 실제 백엔드 엔드포인트를 정직하게 호출하면 응답 직렬화 또는 스키마 검증 문제가 발생할 가능성이 높다.

### 3. 문서화된 실행 경로와 실제 실행 경로의 불일치

README에는 Alembic 마이그레이션과 DB 기반 구조를 전제로 한 설명이 포함되어 있지만, 현재 저장소만으로는 그대로 재현되지 않는다.

온보딩 시 가장 먼저 혼란을 줄 수 있는 지점이다.

### 4. 프론트와 백엔드가 아직 실제로 연결되지 않음

`frontend/js/api.js`에 실제 `fetch()` 구현이 주석 처리되어 있다.

즉 현재 프론트는 백엔드 API 연동 상태를 검증하는 UI가 아니라, UI 목업과 사용자 흐름 데모에 가깝다.

추가로 `API_BASE_URL`은 `8002` 포트를 가리키지만, 백엔드 기본 포트는 `8000`이다. 실제 fetch 코드를 활성화하면 바로 수정이 필요하다.

### 5. 라우팅 충돌 가능성

`reports.py`와 `oneone.py`는 동적 경로가 일부 정적 경로보다 먼저 선언되어 있다.

예시:

- `GET /api/reports/{report_id}` 가 `GET /api/reports/my/`, `GET /api/reports/stats/risk` 보다 먼저 선언됨
- `GET /api/oneone/{oneone_id}` 가 `GET /api/oneone/stats/completion-rate` 보다 먼저 선언됨

프레임워크 라우팅 해석에 따라 정적 경로 요청이 동적 경로 검증으로 먼저 소모되어 `422` 또는 예상치 못한 매칭 문제가 날 수 있다. 정적 경로를 먼저 두는 편이 안전하다.

### 6. 인증 및 권한 검사가 전혀 없음

- 사용자 ID가 쿼리 파라미터 또는 하드코딩 값으로 처리됨
- 역할 기반 제어는 분석 엔진 내부 플래그 수준에 머무름
- 실제 민감정보 보호는 구현되지 않음

이 프로젝트의 도메인 특성상 가장 빨리 보강해야 하는 영역이다.

### 7. 환경 준비 상태가 불명확함

에디터 진단 기준으로 현재 Python 패키지가 설치되지 않아 import 해석 오류가 보인다.

- `pydantic_settings`
- `sqlalchemy`

이는 코드 자체 문제라기보다 현재 워크스페이스 인터프리터 또는 의존성 설치 상태 문제일 가능성이 높다.

## 유지보수 관점 평가

### 강점

- 파일 구조가 역할별로 비교적 명확하다
- 도메인 모델링 방향이 선명하다
- 스키마와 API가 빠르게 데모하기 좋은 형태다
- 분석 엔진이 순수 Python 로직이라 테스트하기 쉽다

### 약점

- 구현 계층 간 분리가 약하다
- 프로토타입용 전역 상태가 많다
- 문서와 실제 코드 간 차이가 커서 신뢰 비용이 높다
- 프론트와 백엔드 통합 검증이 어렵다

## 우선순위 높은 개선 제안

### P0

- 메모리 저장소를 실제 DB 세션으로 교체
- 인증 도입 및 하드코딩된 사용자 값 제거
- Copilot 응답 스키마 불일치 수정
- 프론트 `fetch()` 연동 복구 및 포트 정합성 맞추기

### P1

- 정적 경로와 동적 경로 선언 순서 정리
- 서비스 계층 분리
- 테스트 추가
  - 분석기 단위 테스트
  - API 스모크 테스트
  - Copilot 응답 스키마 테스트

### P2

- 실제 RAG 저장소 연결
- 브리핑 생성/발송 자동화
- 대시보드 집계 로직 고도화

## 다음 작업자가 이해해야 할 현실적인 운영 규칙

- 이 저장소를 엔터프라이즈 완성형으로 가정하면 안 된다.
- 문서보다 코드를 우선 신뢰해야 한다.
- 백엔드 API를 고친 뒤에는 프론트 목업 코드가 실제 연동을 가리고 있는지 항상 확인해야 한다.
- 분석 로직은 현재 키워드 기반이므로, 성능보다 규칙 가독성과 테스트 추가가 먼저다.

## 빠른 실행 메모

백엔드 실행:

```bash
cd backend
pip install -r ..\requirements.txt
uvicorn app.main:app --reload --port 8000
```

프론트 실행:

```bash
cd frontend
python -m http.server 3000
```

주의:

- 프론트는 현재 백엔드를 실제 호출하지 않아도 대부분 화면이 동작한다.
- 진짜 통합 테스트를 하려면 `frontend/js/api.js`의 실제 `fetch()` 경로를 되살려야 한다.

## 한 줄 결론

`work-insight`는 도메인 방향이 잘 잡힌 프로토타입이지만, 현재 시점에서는 "문서상 제품"이 아니라 "데모 중심 MVP 코드베이스"로 보는 것이 정확하다.