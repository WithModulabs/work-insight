"""API Router - Copilot"""
from fastapi import APIRouter, Query, HTTPException
from typing import List
from datetime import datetime

from app.schemas.schemas import CopilotQueryRequest, CopilotQueryResponse, SuggestedQuestion
from app.analysis.copilot import CopilotEngine, QuerySuggester

router = APIRouter()

# Copilot 엔진 초기화
copilot_engine = CopilotEngine()

# 질의 히스토리 (프로토타입용)
query_history = []


@router.post("/query", response_model=CopilotQueryResponse)
async def process_copilot_query(
    request: CopilotQueryRequest,
    user_id: int = Query(1, description="사용자 ID"),
    user_role: str = Query("team_lead", description="사용자 역할"),
    team_id: int = Query(None, description="팀 ID"),
):
    """
    자연어 질의 처리
    
    예시:
    - "이번 주 가장 위험한 프로젝트는?"
    - "우리 팀에서 가장 과부하된 팀원은?"
    - "최근 가장 많이 반복된 이슈는?"
    """
    
    # Copilot 엔진으로 처리
    result = copilot_engine.process_query(request.query_text, user_role, team_id)

    response_text = result.get("response", "")
    if isinstance(response_text, dict):
        response_text = response_text.get("answer", str(response_text))

    evidence = result.get("evidence", [])
    if isinstance(evidence, dict):
        evidence = [evidence]
    elif not isinstance(evidence, list):
        evidence = []

    follow_ups = result.get("follow_ups", [])
    if not isinstance(follow_ups, list):
        follow_ups = []
    
    # 히스토리 저장
    query_history.append({
        "user_id": user_id,
        "query": request.query_text,
        "intent": result["intent"],
        "timestamp": datetime.now(),
        "confidence": result["confidence"],
    })
    
    return {
        "response_text": response_text,
        "evidence": evidence,
        "confidence_score": result["confidence"],
        "suggested_follow_ups": follow_ups,
    }


@router.get("/suggestions", response_model=List[SuggestedQuestion])
async def get_suggestions(
    user_id: int = Query(1),
    user_role: str = Query("team_lead"),
):
    """
    현재 사용자의 역할에 맞는 추천 질문 제공
    """
    suggestions = QuerySuggester.get_suggested_questions(user_role, {})
    
    return [
        SuggestedQuestion(
            question=s["question"],
            category=s["category"]
        )
        for s in suggestions
    ]


@router.get("/history", response_model=List[dict])
async def get_query_history(
    user_id: int = Query(1),
    limit: int = Query(10),
):
    """사용자의 질의 히스토리 조회"""
    user_queries = [q for q in query_history if q.get("user_id") == user_id]
    return sorted(user_queries, key=lambda x: x["timestamp"], reverse=True)[:limit]


@router.post("/feedback")
async def submit_feedback(
    query_id: int,
    is_helpful: bool,
    feedback_text: str = None,
):
    """Copilot 응답에 대한 피드백"""
    # 실제 구현에서는 피드백을 저장하고 모델 개선에 사용
    return {
        "status": "success",
        "message": "피드백이 저장되었습니다.",
    }


@router.get("/example-queries", response_model=dict)
async def get_example_queries():
    """다양한 질의 예시 제공"""
    
    return {
        "director": {
            "status": [
                "이번 주 가장 위험한 프로젝트는?",
                "전사 프로젝트 진행 상황을 요약해줘",
                "조직에서 지금 가장 긴급한 의사결정이 필요한 건?",
            ],
            "analysis": [
                "최근 지연이 많아진 이유는?",
                "우리 팀에서 제일 문제가 되는 팀은?",
                "지난주 대비 지금 주의 리스크가 증가했나?",
            ],
            "people": [
                "조직에서 케어가 필요한 팀원은?",
                "최근 만족도가 떨어진 팀은?",
                "이탈 위험이 있는 팀원 리스트는?",
            ],
        },
        "team_lead": {
            "status": [
                "우리 팀의 현황은?",
                "미결 프로젝트는 몇 개?",
                "팀의 주요 병목은?",
            ],
            "analysis": [
                "최근 우리 팀의 피로도는?",
                "반복되는 이슈는?",
                "팀의 협업 효율도는?",
            ],
            "people": [
                "팀원 중 과부하된 사람은?",
                "가장 만족도 낮은 팀원은?",
                "1:1이 필요한 팀원은?",
            ],
            "action": [
                "우리팀이 개선해야할 우선순위는?",
                "지원해야할 팀원은?",
                "일정 재조정이 필요한 프로젝트는?",
            ],
        },
        "team_member": {
            "status": [
                "오늘 내 우선순위는?",
                "내 현재 평가는?",
                "진행 중인 업무 현황?",
            ],
            "analysis": [
                "내가 이 프로젝트에서 병목인가?",
                "내 최근 성과는?",
                "개선할 부분은?",
            ],
            "action": [
                "다음에 집중해야 할 건?",
                "내가 도움을 청할 사람은?",
                "스킬 개발 플랜은?",
            ],
        },
    }
