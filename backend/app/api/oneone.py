"""API Router - One-on-One Consultations"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.schemas.schemas import (
    OneOnOne, OneOnOneCreate, ActionItem, ActionItemCreate
)

router = APIRouter()

# 메모리 저장소 (프로토타입용)
oneones_db = {}
actions_db = {}
next_oneone_id = 1
next_action_id = 1


@router.post("/", response_model=OneOnOne)
async def create_oneone(oneone: OneOnOneCreate):
    """1:1 상담 기록 생성"""
    global next_oneone_id, next_action_id
    
    oneone_data = {
        "id": next_oneone_id,
        "conducted_by_id": 1,  # 실제는 인증된 사용자에서
        "attendee_id": oneone.attendee_id,
        "session_date": datetime.now(),
        "discussion_topic": oneone.discussion_topic,
        "work_satisfaction": oneone.work_satisfaction,
        "concerns": oneone.concerns,
        "feedback_given": oneone.feedback_given,
        "employee_requests": oneone.employee_requests,
        "observed_signals": oneone.observed_signals,
        "public_note": oneone.public_note,
        "manager_private_note": oneone.manager_private_note,
        "hr_sensitive_note": oneone.hr_sensitive_note,
        "action_items": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    # 액션아이템 생성
    for action in oneone.action_items or []:
        action_data = {
            "id": next_action_id,
            "oneone_record_id": next_oneone_id,
            "assigned_to_id": action.assigned_to_id,
            "assigned_by_id": 1,  # 실제는 인증된 사용자
            "title": action.title,
            "description": action.description,
            "priority": action.priority,
            "due_date": action.due_date,
            "status": "todo",
            "completion_date": None,
            "completion_note": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        actions_db[next_action_id] = action_data
        oneone_data["action_items"].append(action_data)
        next_action_id += 1
    
    oneones_db[next_oneone_id] = oneone_data
    next_oneone_id += 1
    
    return oneone_data


@router.get("/{oneone_id}", response_model=OneOnOne)
async def get_oneone(oneone_id: int):
    """1:1 상담 조회"""
    if oneone_id not in oneones_db:
        raise HTTPException(status_code=404, detail="상담을 찾을 수 없습니다")
    
    return oneones_db[oneone_id]


@router.get("/", response_model=List[OneOnOne])
async def list_oneones(
    attendee_id: Optional[int] = None,
    days: int = Query(30),
    limit: int = Query(50),
):
    """1:1 상담 목록 조회"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    filtered = [
        o for o in oneones_db.values()
        if o.get("session_date", datetime.now()) >= cutoff_date
    ]
    
    if attendee_id:
        filtered = [o for o in filtered if o.get("attendee_id") == attendee_id]
    
    return sorted(filtered, key=lambda x: x["session_date"], reverse=True)[:limit]


@router.post("/action-items/", response_model=ActionItem)
async def create_action_item(action: ActionItemCreate):
    """액션아이템 생성"""
    global next_action_id
    
    action_data = {
        "id": next_action_id,
        "oneone_record_id": action.oneone_record_id,
        "assigned_to_id": action.assigned_to_id,
        "assigned_by_id": 1,
        "title": action.title,
        "description": action.description,
        "priority": action.priority,
        "due_date": action.due_date,
        "status": "todo",
        "completion_date": None,
        "completion_note": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    actions_db[next_action_id] = action_data
    next_action_id += 1
    
    return action_data


@router.get("/action-items/{action_id}", response_model=ActionItem)
async def get_action_item(action_id: int):
    """액션아이템 조회"""
    if action_id not in actions_db:
        raise HTTPException(status_code=404, detail="액션아이템을 찾을 수 없습니다")
    
    return actions_db[action_id]


@router.post("/action-items/{action_id}/complete")
async def complete_action_item(action_id: int, completion_note: str = ""):
    """액션아이템 완료"""
    if action_id not in actions_db:
        raise HTTPException(status_code=404, detail="액션아이템을 찾을 수 없습니다")
    
    action = actions_db[action_id]
    action["status"] = "completed"
    action["completion_date"] = datetime.now()
    action["completion_note"] = completion_note
    action["updated_at"] = datetime.now()
    
    return action


@router.get("/stats/completion-rate", response_model=dict)
async def get_completion_stats(days: int = Query(30)):
    """액션아이템 완료율 통계"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    recent_actions = [
        a for a in actions_db.values()
        if a.get("created_at", datetime.now()) >= cutoff_date
    ]
    
    completed = sum(1 for a in recent_actions if a.get("status") == "completed")
    
    return {
        "total_actions": len(recent_actions),
        "completed": completed,
        "completion_rate": completed / len(recent_actions) if recent_actions else 0,
        "pending": len(recent_actions) - completed,
    }
