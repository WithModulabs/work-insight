"""API Router - Dashboard"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta

from app.schemas.schemas import TeamDashboardResponse, OrgDashboardResponse

router = APIRouter()


@router.get("/team/{team_id}", response_model=TeamDashboardResponse)
async def get_team_dashboard(
    team_id: int,
    days: int = Query(7, description="최근 N일간의 데이터"),
):
    """팀 대시보드 조회"""
    # 실제 구현에서는 DB에서 데이터를 조회
    # 여기서는 시뮬레이션 데이터 반환
    
    return {
        "team_name": f"Team {team_id}",
        "total_members": 5,
        "report_submission_rate": 0.85,  # 85%
        "critical_issues": [
            {
                "title": "프로젝트 A 일정 지연",
                "severity": "high",
                "status": "in_progress",
            }
        ],
        "pending_action_items": 3,
        "at_risk_projects": [
            {
                "name": "프로젝트 B",
                "status": "at_risk",
                "risk_score": 0.75,
            }
        ],
        "risk_signals": [
            {
                "id": 1,
                "user_id": 2,
                "risk_type": "overload",
                "risk_level": "warning",
                "signal_keywords": '["미완료", "과부하"]',
                "explanation": "미완료 업무가 연속으로 적재되고 있습니다.",
                "detected_at": datetime.now(),
                "is_addressed": False,
            }
        ],
    }


@router.get("/org/", response_model=OrgDashboardResponse)
async def get_org_dashboard(
    days: int = Query(7, description="최근 N일간의 데이터"),
):
    """전사 대시보드 조회"""
    return {
        "total_teams": 8,
        "total_members": 45,
        "critical_projects": [
            {
                "name": "전사 시스템 고도화",
                "status": "at_risk",
                "risk_score": 0.82,
            },
            {
                "name": "신규 기능 개발",
                "status": "in_progress",
                "risk_score": 0.45,
            }
        ],
        "high_risk_signals": [
            {
                "id": 1,
                "user_id": 5,
                "risk_type": "churn_risk",
                "risk_level": "high",
                "signal_keywords": '["만족도_하락", "보고_미제출", "불만"]',
                "explanation": "조직 내 이탈 리스크가 높아지고 있습니다.",
                "detected_at": datetime.now() - timedelta(days=1),
                "is_addressed": False,
            }
        ],
        "team_health_score": 0.72,
    }


@router.get("/overview", response_model=dict)
async def get_overview(
    days: int = Query(7),
):
    """종합 개요"""
    return {
        "period": {
            "start": (datetime.now() - timedelta(days=days)).date(),
            "end": datetime.now().date(),
        },
        "metrics": {
            "total_reports": 125,
            "report_submission_rate": 0.87,
            "avg_sentiment": 0.12,
            "avg_fatigue": 0.35,
            "critical_issues": 3,
            "high_risk_signals": 5,
        },
        "projects": {
            "total": 12,
            "on_track": 8,
            "at_risk": 3,
            "completed": 1,
        },
        "teams": {
            "total": 8,
            "needing_support": 2,
        },
    }


@router.get("/projects/{project_id}", response_model=dict)
async def get_project_details(project_id: int):
    """프로젝트 상세 정보"""
    return {
        "id": project_id,
        "name": f"Project {project_id}",
        "status": "in_progress",
        "risk_score": 0.45,
        "team": {
            "id": 1,
            "name": "Team A",
        },
        "timeline": {
            "start": "2024-01-01",
            "end": "2024-03-31",
            "progress": 0.65,
        },
        "issues": [
            {
                "title": "UI 지연",
                "severity": "medium",
                "resolution": "예정",
            }
        ],
        "recent_updates": [
            {
                "date": datetime.now(),
                "update": "2024년 3월 27일: 진행 상황 업데이트",
            }
        ],
    }
