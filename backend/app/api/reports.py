"""API Router - Daily Reports"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.schemas.schemas import (
    DailyReport, DailyReportCreate, DailyReportBase
)
from app.analysis.analyzer import ReportAnalyzer, RiskSignalDetector

router = APIRouter()

# 메모리 저장소 (프로토타입용, 실제는 DB 사용)
reports_db = {}
next_id = 1


@router.post("/", response_model=DailyReport)
async def create_report(report: DailyReportCreate):
    """퇴근보고 작성"""
    global next_id
    
    # 분석 수행
    analyzer = ReportAnalyzer()
    analysis_result = analyzer.analyze_report(report.accomplished)
    
    # 보고 저장
    full_text = f"{report.accomplished} {report.issues or ''} {report.tomorrow_plan or ''}"
    
    report_data = {
        "id": next_id,
        "author_id": 1,  # 실제는 인증된 사용자에서 가져와야 함
        "project_id": report.project_id,
        "report_date": datetime.now(),
        "accomplished": report.accomplished,
        "in_progress": report.in_progress,
        "not_completed": report.not_completed,
        "tomorrow_plan": report.tomorrow_plan,
        "issues": report.issues,
        "support_needed": report.support_needed,
        "collaboration_needed": report.collaboration_needed,
        "summary": report.summary,
        "fatigue_level": analysis_result["fatigue_level"],
        "sentiment_score": analysis_result["sentiment_score"],
        "risk_keywords": analysis_result["risk_keywords"],
        "risk_level": analysis_result["risk_level"],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    reports_db[next_id] = report_data
    next_id += 1
    
    return report_data


@router.get("/{report_id}", response_model=DailyReport)
async def get_report(report_id: int):
    """퇴근보고 조회"""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="보고를 찾을 수 없습니다")
    
    return reports_db[report_id]


@router.get("/my/", response_model=List[DailyReport])
async def get_my_reports(
    days: int = Query(7, description="최근 N일 간의 보고"),
    limit: int = Query(10, description="최대 개수")
):
    """내 퇴근보고 목록 조회"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    filtered_reports = [
        r for r in reports_db.values()
        if r.get("report_date", datetime.now()) >= cutoff_date
    ]
    
    return sorted(filtered_reports, key=lambda x: x["report_date"], reverse=True)[:limit]


@router.get("/", response_model=List[DailyReport])
async def list_reports(
    project_id: Optional[int] = None,
    author_id: Optional[int] = None,
    risk_level: Optional[str] = None,
    limit: int = Query(50),
):
    """퇴근보고 목록 조회 (필터 지원)"""
    filtered = list(reports_db.values())
    
    if project_id:
        filtered = [r for r in filtered if r.get("project_id") == project_id]
    
    if author_id:
        filtered = [r for r in filtered if r.get("author_id") == author_id]
    
    if risk_level:
        filtered = [r for r in filtered if r.get("risk_level") == risk_level]
    
    return sorted(filtered, key=lambda x: x["created_at"], reverse=True)[:limit]


@router.get("/stats/risk", response_model=dict)
async def get_risk_stats(days: int = Query(7)):
    """리스크 통계"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    recent_reports = [
        r for r in reports_db.values()
        if r.get("report_date", datetime.now()) >= cutoff_date
    ]
    
    risk_distribution = {}
    for report in recent_reports:
        risk = report.get("risk_level", "low")
        risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
    
    return {
        "total_reports": len(recent_reports),
        "risk_distribution": risk_distribution,
        "avg_sentiment": sum(r.get("sentiment_score", 0) for r in recent_reports) / len(recent_reports) if recent_reports else 0,
        "avg_fatigue": sum(r.get("fatigue_level", 0) for r in recent_reports) / len(recent_reports) if recent_reports else 0,
    }
