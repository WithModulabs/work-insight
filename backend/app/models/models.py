"""Database models for WorkInsight"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class User(Base):
    """사용자 및 직원 정보"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    role = Column(String)  # team_member, team_lead, director, hr, admin
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    reports = relationship("DailyReport", back_populates="author")
    conducted_oneones = relationship("OneOnOneRecord", foreign_keys="OneOnOneRecord.conducted_by_id", back_populates="conductor")
    received_oneones = relationship("OneOnOneRecord", foreign_keys="OneOnOneRecord.attendee_id", back_populates="attendee")


class Team(Base):
    """팀 정보"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    lead_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    members = relationship("User", back_populates="team")
    projects = relationship("Project", back_populates="team")


class Project(Base):
    """프로젝트 정보"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    description = Column(Text, nullable=True)
    status = Column(String)  # planning, in_progress, at_risk, completed, cancelled
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    priority = Column(String)  # critical, high, medium, low
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="projects")
    reports = relationship("DailyReport", back_populates="project")


class DailyReport(Base):
    """퇴근보고"""
    __tablename__ = "daily_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # 보고 내용
    report_date = Column(DateTime, index=True)
    accomplished = Column(Text)  # 오늘 한 일
    in_progress = Column(Text, nullable=True)  # 진행 중인 일
    not_completed = Column(Text, nullable=True)  # 미완료 업무
    tomorrow_plan = Column(Text, nullable=True)  # 내일 할 일
    issues = Column(Text, nullable=True)  # 이슈/장애요인
    support_needed = Column(Text, nullable=True)  # 지원 필요사항
    collaboration_needed = Column(Text, nullable=True)  # 협업 필요 대상
    summary = Column(Text, nullable=True)  # 한 줄 요약
    
    # 자동 분석 결과
    fatigue_level = Column(Float, nullable=True)  # 0-1 (0=fresh, 1=exhausted)
    sentiment_score = Column(Float, nullable=True)  # -1 ~ 1
    risk_keywords = Column(Text, nullable=True)  # JSON 형식: 감지된 리스크 키워드
    risk_level = Column(String, nullable=True)  # low, medium, high, critical
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="reports")
    project = relationship("Project", back_populates="reports")


class OneOnOneRecord(Base):
    """1:1 상담 기록"""
    __tablename__ = "oneone_records"
    
    id = Column(Integer, primary_key=True, index=True)
    conducted_by_id = Column(Integer, ForeignKey("users.id"))
    attendee_id = Column(Integer, ForeignKey("users.id"))
    
    # 상담 정보
    session_date = Column(DateTime, index=True)
    discussion_topic = Column(Text)  # 주요 논의 내용
    
    # 구조화된 기록
    work_satisfaction = Column(Float, nullable=True)  # 0-10
    concerns = Column(Text, nullable=True)  # 고민사항
    feedback_given = Column(Text, nullable=True)  # 제공된 피드백
    employee_requests = Column(Text, nullable=True)  # 요청사항
    observed_signals = Column(Text, nullable=True)  # 관찰된 신호 (번아웃, 갈등 등)
    
    # 공개/비공개 메모
    public_note = Column(Text, nullable=True)
    manager_private_note = Column(Text, nullable=True)  # 팀장만 볼 수 있음
    hr_sensitive_note = Column(Text, nullable=True)  # HR만 볼 수 있음
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conductor = relationship("User", foreign_keys=[conducted_by_id], back_populates="conducted_oneones")
    attendee = relationship("User", foreign_keys=[attendee_id], back_populates="received_oneones")
    action_items = relationship("ActionItem", back_populates="oneone_record")


class ActionItem(Base):
    """액션 아이템 (1:1 상담이나 보고에서 생성)"""
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    oneone_record_id = Column(Integer, ForeignKey("oneone_records.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    assigned_by_id = Column(Integer, ForeignKey("users.id"))
    
    # 액션 내용
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    priority = Column(String)  # low, medium, high, critical
    status = Column(String)  # todo, in_progress, completed, cancelled
    
    # 추적
    completion_date = Column(DateTime, nullable=True)
    completion_note = Column(Text, nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    oneone_record = relationship("OneOnOneRecord", back_populates="action_items")


class RiskSignal(Base):
    """리스크 신호 (이탈 위험, 번아웃 등)"""
    __tablename__ = "risk_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    risk_type = Column(String)  # churn_risk, burnout, conflict, overload
    risk_level = Column(String)  # attention, warning, high, critical
    signal_keywords = Column(Text)  # JSON: 탐지된 신호
    explanation = Column(Text)  # 왜 이 신호가 발생했는지 설명
    
    # 배경 데이터
    report_ids = Column(Text, nullable=True)  # 관련 보고 ID (JSON)
    oneone_ids = Column(Text, nullable=True)  # 관련 상담 ID (JSON)
    
    # 추적
    is_addressed = Column(Boolean, default=False)
    addressed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    addressed_date = Column(DateTime, nullable=True)
    follow_up_action = Column(Text, nullable=True)
    
    # 메타데이터
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MorningBrief(Base):
    """아침 브리핑 메일"""
    __tablename__ = "morning_briefs"
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), index=True)
    recipient_role = Column(String)  # team_member, team_lead, director
    
    # 컨텐츠
    brief_date = Column(DateTime, index=True)
    content = Column(Text)  # HTML 형식
    
    # 추적
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CopilotQuery(Base):
    """사용자 Copilot 질의 기록"""
    __tablename__ = "copilot_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # 질의
    query_text = Column(Text)
    query_intent = Column(String)  # status, analysis, people, action, comparison
    
    # 응답
    response_text = Column(Text, nullable=True)
    evidence_ids = Column(Text, nullable=True)  # 근거 객체 ID (JSON)
    
    # 평가
    is_helpful = Column(Boolean, nullable=True)
    user_feedback = Column(Text, nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    response_time_ms = Column(Integer, nullable=True)
