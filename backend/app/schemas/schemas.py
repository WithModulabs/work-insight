"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, EmailStr, Field


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str  # team_member, team_lead, director, hr

    
class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    team_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Team Schemas
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class TeamCreate(TeamBase):
    lead_id: Optional[int] = None


class Team(TeamBase):
    id: int
    lead_id: Optional[int] = None
    created_at: datetime
    members: List[User] = []
    
    class Config:
        from_attributes = True


# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "planning"  # planning, in_progress, at_risk, completed
    priority: str = "medium"


class ProjectCreate(ProjectBase):
    team_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class Project(ProjectBase):
    id: int
    team_id: int
    risk_score: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Daily Report Schemas
class DailyReportBase(BaseModel):
    accomplished: str
    in_progress: Optional[str] = None
    not_completed: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    issues: Optional[str] = None
    support_needed: Optional[str] = None
    collaboration_needed: Optional[str] = None
    summary: Optional[str] = None
    fatigue_level: Optional[float] = None


class DailyReportCreate(DailyReportBase):
    project_id: Optional[int] = None


class DailyReport(DailyReportBase):
    id: int
    author_id: int
    project_id: Optional[int] = None
    report_date: datetime
    sentiment_score: Optional[float] = None
    risk_level: Optional[str] = None
    fatigue_level: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# One-on-One Schemas
class ActionItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None


class ActionItemCreate(ActionItemBase):
    assigned_to_id: int
    oneone_record_id: Optional[int] = None


class ActionItem(ActionItemBase):
    id: int
    assigned_to_id: int
    assigned_by_id: int
    status: str
    completion_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class OneOnOneBase(BaseModel):
    discussion_topic: str
    work_satisfaction: Optional[float] = None  # 0-10
    concerns: Optional[str] = None
    feedback_given: Optional[str] = None
    employee_requests: Optional[str] = None
    observed_signals: Optional[str] = None
    public_note: Optional[str] = None


class OneOnOneCreate(OneOnOneBase):
    attendee_id: int
    manager_private_note: Optional[str] = None
    hr_sensitive_note: Optional[str] = None
    action_items: Optional[List[ActionItemCreate]] = []


class OneOnOne(OneOnOneBase):
    id: int
    conducted_by_id: int
    attendee_id: int
    session_date: datetime
    action_items: List[ActionItem] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


# Risk Signal Schemas
class RiskSignalBase(BaseModel):
    risk_type: str
    risk_level: str
    signal_keywords: str  # JSON string
    explanation: str


class RiskSignal(RiskSignalBase):
    id: int
    user_id: int
    detected_at: datetime
    is_addressed: bool
    
    class Config:
        from_attributes = True


# Dashboard Schemas
class TeamDashboardResponse(BaseModel):
    team_name: str
    total_members: int
    report_submission_rate: float  # 0-1
    critical_issues: List[dict]
    pending_action_items: int
    at_risk_projects: List[dict]
    risk_signals: List[RiskSignal]


class OrgDashboardResponse(BaseModel):
    total_teams: int
    total_members: int
    critical_projects: List[dict]
    high_risk_signals: List[RiskSignal]
    team_health_score: float


# Copilot Schemas
class CopilotQueryRequest(BaseModel):
    query_text: str
    context: Optional[str] = None  # 추가 컨텍스트


class CopilotQueryResponse(BaseModel):
    response_text: str
    evidence: List[dict]  # 근거 목록
    confidence_score: float  # 0-1
    suggested_follow_ups: List[str]  # 추천 후속 질문


class SuggestedQuestion(BaseModel):
    question: str
    category: str  # status, analysis, people, action


# Morning Brief Request/Response
class MorningBriefRequest(BaseModel):
    # 아침 브리핑 생성 요청
    recipient_role: str  # team_member, team_lead, director
    team_id: Optional[int] = None


class MorningBriefResponse(BaseModel):
    id: int
    recipient_id: int
    content: str
    brief_date: datetime
    
    class Config:
        from_attributes = True


class EmailAttachmentMetadata(BaseModel):
    file_name: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None


class ReceivedEmailSaveRequest(BaseModel):
    message_id: str = Field(..., min_length=3)
    internet_message_id: Optional[str] = None
    subject: str = Field(default="(no subject)", min_length=1)
    from_address: EmailStr
    to_addresses: List[EmailStr] = Field(default_factory=list)
    cc_addresses: List[EmailStr] = Field(default_factory=list)
    received_at: datetime
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    raw_mime_base64: Optional[str] = None
    attachments: List[EmailAttachmentMetadata] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SharePointListItem(BaseModel):
    item_id: str
    list_item_url: Optional[str] = None


class ReceivedEmailSaveResponse(BaseModel):
    stored_at: datetime
    message_id: str
    subject: str
    list_item_id: str
    list_item_url: Optional[str] = None
    field_count: int


class GraphSubscriptionCreateRequest(BaseModel):
    mailbox_user_id: Optional[str] = None
    notification_url: Optional[str] = None
    client_state: Optional[str] = None
    sharepoint_folder: Optional[str] = None
    resource: Optional[str] = None
    expiration_minutes: Optional[int] = Field(default=None, ge=15, le=4230)


class GraphSubscriptionResponse(BaseModel):
    id: str
    resource: str
    expiration_date_time: datetime
    client_state: Optional[str] = None
    notification_url: str


class GraphWebhookNotification(BaseModel):
    subscriptionId: str
    changeType: str
    resource: str
    clientState: Optional[str] = None
    tenantId: Optional[str] = None
    subscriptionExpirationDateTime: Optional[datetime] = None


class GraphWebhookPayload(BaseModel):
    value: List[GraphWebhookNotification] = Field(default_factory=list)


class GraphWebhookAcceptedResponse(BaseModel):
    accepted: bool
    notification_count: int
