"""API Router - Dashboard"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime, timedelta

from app.schemas.schemas import TeamDashboardResponse, OrgDashboardResponse
from app.services.email_service import email_service

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


@router.post("/morning-brief/send-email", response_model=dict)
async def send_morning_brief_email(
    recipient_email: str = Query(..., description="수신자 이메일"),
    organization_name: str = Query("WorkInsight", description="조직명"),
):
    """
    아침 브리핑 이메일 전송
    
    Example:
        GET /dashboard/morning-brief/send-email?recipient_email=user@example.com&organization_name=ABC Company
    """
    # 아침 브리핑 HTML 생성
    overview = await get_overview()
    
    brief_html = f"""
    <h3>📊 종합 현황</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #f0f0f0;">
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>총 일일보고</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{overview['metrics']['total_reports']}개</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>제출률</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{overview['metrics']['report_submission_rate']*100:.0f}%</td>
        </tr>
        <tr style="background: #f0f0f0;">
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>평균 감정도</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{overview['metrics']['avg_sentiment']:.2f}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>평균 피로도</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{overview['metrics']['avg_fatigue']:.2f}</td>
        </tr>
        <tr style="background: #f0f0f0;">
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>긴급 이슈</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #d32f2f;">🚨 {overview['metrics']['critical_issues']}건</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>고위험 신호</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #f57c00;">⚠️ {overview['metrics']['high_risk_signals']}건</td>
        </tr>
    </table>
    
    <h3>🎯 프로젝트 현황</h3>
    <ul>
        <li><strong>총</strong>: {overview['projects']['total']}개</li>
        <li><span style="color: #4caf50;">✅ 정상</span>: {overview['projects']['on_track']}개</li>
        <li><span style="color: #f57c00;">⚠️ 위험</span>: {overview['projects']['at_risk']}개</li>
        <li><span style="color: #2196f3;">✔️ 완료</span>: {overview['projects']['completed']}개</li>
    </ul>
    
    <h3>👥 팀 상태</h3>
    <p>
        • 총 {overview['teams']['total']}개 팀<br>
        • <span style="color: #d32f2f;">지원 필요 팀: {overview['teams']['needing_support']}개</span>
    </p>
    
    <hr>
    <p style="color: #666; font-size: 12px;">
        📅 기간: {overview['period']['start']} ~ {overview['period']['end']}<br>
        🔗 상세 정보는 <a href="http://127.0.0.1:3001">WorkInsight 대시보드</a>에서 확인하세요.
    </p>
    """
    
    try:
        success = await email_service.send_morning_brief_email(
            recipient_email=recipient_email,
            brief_html=brief_html,
            organization_name=organization_name
        )
        
        if success:
            return {
                "status": "success",
                "message": f"✅ 아침 브리핑 이메일이 {recipient_email}로 전송되었습니다",
                "to": recipient_email,
                "subject": f"[{organization_name}] {datetime.now().strftime('%Y년 %m월 %d일')} 아침 경영 브리핑",
                "sent_at": datetime.now()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="이메일 전송 실패. Azure AD 인증 정보를 확인하세요"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이메일 전송 중 오류 발생: {str(e)}"
        )


@router.post("/risk-alert/send-email", response_model=dict)
async def send_risk_alert_email(
    recipient_email: str = Query(..., description="수신자 이메일"),
    organization_name: str = Query("WorkInsight", description="조직명"),
):
    """
    리스크 신호 알림 이메일 전송
    
    Example:
        POST /dashboard/risk-alert/send-email?recipient_email=ceo@example.com&organization_name=ABC Company
    """
    dashboard = await get_org_dashboard()
    
    risk_signals = []
    for signal in dashboard.get("high_risk_signals", []):
        risk_signals.append({
            "title": f"Risk Type: {signal.get('risk_type', 'Unknown')}",
            "message": signal.get("explanation", ""),
            "level": signal.get("risk_level", "warning"),
            "timestamp": signal.get("detected_at", datetime.now()).strftime("%Y-%m-%d %H:%M")
        })
    
    try:
        success = await email_service.send_risk_alert_email(
            recipient_email=recipient_email,
            risk_signals=risk_signals,
            organization_name=organization_name
        )
        
        if success:
            return {
                "status": "success",
                "message": f"✅ 리스크 알림 이메일이 {recipient_email}로 전송되었습니다",
                "to": recipient_email,
                "risk_count": len(risk_signals),
                "sent_at": datetime.now()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="이메일 전송 실패. Azure AD 인증 정보를 확인하세요"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이메일 전송 중 오류 발생: {str(e)}"
        )
