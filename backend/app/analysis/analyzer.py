"""Analysis engine for daily reports and signals"""
import json
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import math


class ReportAnalyzer:
    """퇴근보고 분석 엔진"""
    
    # 리스크 키워드
    RISK_KEYWORDS = {
        "high": ["지연", "막혔다", "장애", "문제", "실패", "위기", "긴급", "위험", "정체", "병목"],
        "medium": ["어렵다", "진행 중", "추진", "검토", "답답", "복잡"],
        "low": ["진행", "확인", "검토 예정"]
    }
    
    FATIGUE_KEYWORDS = ["피곤", "힘들다", "지쳐", "번아웃", "소진", "회의적", "무기력"]
    POSITIVE_KEYWORDS = ["성공", "완료", "달성", "좋다", "만족", "기쁘다", "자랑스럽다"]
    CONFLICT_KEYWORDS = ["갈등", "의견", "불화", "충돌", "싸움", "불만"]
    
    def __init__(self):
        pass
    
    def analyze_report(self, report_text: str) -> Dict:
        """
        퇴근보고 전문을 분석하고 구조화된 정보 추출
        """
        analysis = {
            "risk_level": self._classify_risk_level(report_text),
            "risk_keywords": self._extract_risk_keywords(report_text),
            "sentiment_score": self._calculate_sentiment(report_text),
            "fatigue_level": self._estimate_fatigue(report_text),
            "contains_conflict": self._detect_conflict(report_text),
        }
        return analysis
    
    def _classify_risk_level(self, text: str) -> str:
        """리스크 레벨 분류"""
        text_lower = text.lower()
        
        high_count = sum(1 for kw in self.RISK_KEYWORDS["high"] if kw in text_lower)
        medium_count = sum(1 for kw in self.RISK_KEYWORDS["medium"] if kw in text_lower)
        
        if high_count >= 2:
            return "critical"
        elif high_count >= 1:
            return "high"
        elif medium_count >= 2:
            return "medium"
        else:
            return "low"
    
    def _extract_risk_keywords(self, text: str) -> List[str]:
        """리스크 키워드 추출"""
        text_lower = text.lower()
        found_keywords = []
        
        for level_keywords in self.RISK_KEYWORDS.values():
            for kw in level_keywords:
                if kw in text_lower:
                    found_keywords.append(kw)
        
        return list(set(found_keywords))  # 중복 제거
    
    def _calculate_sentiment(self, text: str) -> float:
        """
        감정 점수 계산 (-1 ~ 1)
        간단한 키워드 기반 분석
        """
        text_lower = text.lower()
        
        # 긍정 점수
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        
        # 부정 점수  
        negative_count = sum(1 for kw in self.FATIGUE_KEYWORDS if kw in text_lower)
        negative_count += sum(1 for kw in self.RISK_KEYWORDS["high"] if kw in text_lower)
        
        # 정규화된 점수 계산
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / max(total, 1)
        return max(-1.0, min(1.0, sentiment))
    
    def _estimate_fatigue(self, text: str) -> float:
        """피로도 추정 (0 ~ 1, 0=fresh, 1=exhausted)"""
        text_lower = text.lower()
        
        # 피로 신호
        fatigue_count = sum(1 for kw in self.FATIGUE_KEYWORDS if kw in text_lower)
        
        # 미완료 업무가 많은 경우
        not_completed_markers = ["안 했다", "못 했다", "미루었", "못했다"]
        incomplete_count = sum(1 for kw in not_completed_markers if kw in text_lower)
        
        # 업무 시간이 길어 보이는 경우
        time_exhaustion = text_lower.count("늦게") + text_lower.count("야근") + text_lower.count("밤")
        
        total_signals = fatigue_count + incomplete_count + time_exhaustion
        fatigue_score = min(1.0, total_signals * 0.2)
        
        return fatigue_score
    
    def _detect_conflict(self, text: str) -> bool:
        """갈등 신호 탐지"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.CONFLICT_KEYWORDS)


class RiskSignalDetector:
    """리스크 신호 탐지 엔진 (이탈 위험, 번아웃 등)"""
    
    def __init__(self):
        self.analyzer = ReportAnalyzer()
    
    def detect_signals(self, user_id: int, recent_reports: List[Dict], oneones: List[Dict]) -> List[Dict]:
        """
        사용자의 리스크 신호를 종합적으로 탐지
        """
        signals = []
        
        # 1. 번아웃 신호
        burnout_signal = self._detect_burnout(user_id, recent_reports, oneones)
        if burnout_signal:
            signals.append(burnout_signal)
        
        # 2. 이탈 리스크
        churn_signal = self._detect_churn_risk(user_id, recent_reports, oneones)
        if churn_signal:
            signals.append(churn_signal)
        
        # 3. 과부하 신호
        overload_signal = self._detect_overload(user_id, recent_reports)
        if overload_signal:
            signals.append(overload_signal)
        
        # 4. 협업 갈등
        conflict_signal = self._detect_conflict(user_id, recent_reports, oneones)
        if conflict_signal:
            signals.append(conflict_signal)
        
        return signals
    
    def _detect_burnout(self, user_id: int, reports: List[Dict], oneones: List[Dict]) -> Optional[Dict]:
        """번아웃 신호 탐지"""
        if len(reports) < 3:
            return None
        
        # 최근 3개 보고에서 피로도 추이 확인
        recent_fatigue = [r.get("fatigue_level", 0) for r in reports[-3:]]
        avg_fatigue = sum(recent_fatigue) / len(recent_fatigue)
        
        # 부정적 감정 점수 추이
        recent_sentiment = [r.get("sentiment_score", 0) for r in reports[-3:]]
        avg_sentiment = sum(recent_sentiment) / len(recent_sentiment)
        
        # 번아웃 판단
        if avg_fatigue > 0.6 and avg_sentiment < -0.3:
            # 최근 1:1에서도 번아웃 신호 있는지 확인
            oneone_mentions = sum(1 for o in oneones[-2:] if "번아웃" in o.get("discussion_topic", "").lower())
            
            if oneone_mentions > 0 or len([r for r in reports[-5:] if r.get("fatigue_level", 0) > 0.6]) >= 3:
                return {
                    "type": "burnout",
                    "level": "high" if avg_fatigue > 0.75 else "warning",
                    "user_id": user_id,
                    "explanation": f"최근 피로도({avg_fatigue:.1%}), 부정 감정({avg_sentiment:.1f}) 지속",
                    "recommended_action": "관리자 1:1 상담 및 업무 재조정 권고",
                }
        
        return None
    
    def _detect_churn_risk(self, user_id: int, reports: List[Dict], oneones: List[Dict]) -> Optional[Dict]:
        """이탈 위험 신호 탐지"""
        if len(reports) < 5:
            return None
        
        # 보고 제출 패턴 분석
        report_gaps = self._analyze_report_gaps(reports)
        
        # 최근 부정적 신호 누적
        negative_reports = sum(
            1 for r in reports[-10:] 
            if r.get("sentiment_score", 0) < -0.5
        )
        
        # 최근 1:1에서의 불만 언급
        recent_oneones = oneones[-3:]
        satisfaction_scores = [o.get("work_satisfaction", 5) for o in recent_oneones]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 5
        
        # 이탈 위험 판단
        missing_reports = report_gaps > 2  # 2일 이상 미제출
        declining_satisfaction = avg_satisfaction < 4  # 만족도 낮음
        negative_sentiment_trend = negative_reports >= 3  # 최근 부정 신호 많음
        
        if (missing_reports and declining_satisfaction) or (negative_sentiment_trend and declining_satisfaction):
            return {
                "type": "churn_risk",
                "level": "critical" if missing_reports and declining_satisfaction else "high",
                "user_id": user_id,
                "explanation": f"보고 미제출 패턴({report_gaps}일), 만족도({avg_satisfaction:.1f}), 부정 신호({negative_reports}회)",
                "recommended_action": "긴급 1:1 상담, HR 개입 검토",
            }
        
        return None
    
    def _detect_overload(self, user_id: int, reports: List[Dict]) -> Optional[Dict]:
        """과부하 신호 탐지"""
        if len(reports) < 3:
            return None
        
        # 미완료 업무 누적
        recent_reports = reports[-5:]
        incomplete_mentions = sum(
            1 for r in recent_reports
            if r.get("not_completed") and len(r.get("not_completed", "")) > 20
        )
        
        # 리스크 레벨이 높은 보고 많음
        high_risk_reports = sum(
            1 for r in recent_reports
            if r.get("risk_level") in ["high", "critical"]
        )
        
        if incomplete_mentions >= 3 or high_risk_reports >= 3:
            return {
                "type": "overload",
                "level": "high",
                "user_id": user_id,
                "explanation": f"미완료 업무 누적({incomplete_mentions}회), 고위험 보고({high_risk_reports}회)",
                "recommended_action": "업무 재조정, 우선순위 정리 미팅",
            }
        
        return None
    
    def _detect_conflict(self, user_id: int, reports: List[Dict], oneones: List[Dict]) -> Optional[Dict]:
        """협업 갈등 신호"""
        recent_reports = reports[-5:]
        recent_oneones = oneones[-3:]
        
        # 보고에서 갈등 언급
        conflict_mentions_reports = sum(
            1 for r in recent_reports
            if "갈등" in r.get("issues", "") or "의견" in r.get("collaboration_needed", "")
        )
        
        # 1:1에서 갈등 언급
        conflict_mentions_oneones = sum(
            1 for o in recent_oneones
            if "갈등" in o.get("discussion_topic", "").lower() or 
               "불화" in o.get("observed_signals", "").lower()
        )
        
        if conflict_mentions_reports >= 2 or conflict_mentions_oneones >= 1:
            return {
                "type": "conflict",
                "level": "warning" if conflict_mentions_reports == 1 else "high",
                "user_id": user_id,
                "explanation": f"협업 관련 언급이 반복됨 (보고{conflict_mentions_reports}회, 상담{conflict_mentions_oneones}회)",
                "recommended_action": "팀장 중재 미팅, 관계 개선 지원",
            }
        
        return None
    
    def _analyze_report_gaps(self, reports: List[Dict]) -> int:
        """보고 제출 간격 분석 (최대 연속 미제출 일수)"""
        if not reports:
            return 0
        
        # 보고 날짜 추출
        dates = sorted([r.get("report_date") for r in reports if r.get("report_date")])
        
        if len(dates) < 2:
            return 0
        
        max_gap = 0
        for i in range(1, len(dates)):
            gap_days = (dates[i] - dates[i-1]).days - 1
            max_gap = max(max_gap, gap_days)
        
        return max_gap


class BriefingGenerator:
    """아침 브리핑 생성 엔진"""
    
    def __init__(self):
        self.analyzer = ReportAnalyzer()
    
    def generate_team_member_brief(self, user_id: int, yesterday_report: Optional[Dict]) -> str:
        """팀원용 아침 브리핑"""
        if not yesterday_report:
            return "<p>어제 보고를 찾을 수 없습니다.</p>"
        
        html_content = """
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>📋 오늘의 실행 계획</h2>
            
            <h3>🎯 오늘 가장 중요한 업무</h3>
            <ul>
                <li>{tomorrow_plan}</li>
            </ul>
            
            <h3>⚠️ 주의사항</h3>
            <ul>
                <li>어제 미완료: {not_completed}</li>
                <li>진행 중: {in_progress}</li>
            </ul>
            
            <h3>🤝 협업 필요</h3>
            <p>{collaboration}</p>
            
            <p style="color: #666; font-size: 12px;">
                생성 시간: {generated_at}
            </p>
        </div>
        """.format(
            tomorrow_plan=yesterday_report.get("tomorrow_plan", "내용 없음"),
            not_completed=yesterday_report.get("not_completed", "없음"),
            in_progress=yesterday_report.get("in_progress", "없음"),
            collaboration=yesterday_report.get("collaboration_needed", "없음"),
            generated_at=datetime.now().strftime("%H:%M")
        )
        return html_content
    
    def generate_team_lead_brief(self, team_id: int, team_members_reports: List[Dict], team_data: Dict) -> str:
        """팀장용 아침 브리핑"""
        # 팀원별 핵심 요약
        critical_items = []
        for report in team_members_reports:
            if report.get("risk_level") in ["high", "critical"]:
                critical_items.append({
                    "member": report.get("author_name"),
                    "issue": report.get("issues"),
                    "risk_level": report.get("risk_level")
                })
        
        # 미완료 업무가 많은 팀원
        overloaded_members = [
            (r.get("author_name"), r.get("not_completed"))
            for r in team_members_reports
            if r.get("not_completed") and len(r.get("not_completed", "")) > 30
        ]
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>👥 팀 브리핑 - {team_data.get('team_name', '기본 팀')}</h2>
            
            <h3>🚨 긴급 확인 필요</h3>
            <ul>
        """
        
        for item in critical_items:
            html_content += f"<li><strong>{item['member']}</strong>: {item['issue']} [{item['risk_level']}]</li>"
        
        html_content += """
            </ul>
            
            <h3>⚠️ 업무 과부하 대상</h3>
            <ul>
        """
        
        for member, issues in overloaded_members:
            html_content += f"<li><strong>{member}</strong>: {issues[:50]}...</li>"
        
        html_content += f"""
            </ul>
            
            <h3>✅ 오늘의 체크리스트</h3>
            <ul>
                <li>[ ] 긴급 이슈 1:1</li>
                <li>[ ] 과부하 팀원 지원 계획</li>
                <li>[ ] 프로젝트 진행률 확인</li>
            </ul>
            
            <p style="color: #666; font-size: 12px;">
                생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M")}
            </p>
        </div>
        """
        
        return html_content
    
    def generate_director_brief(self, org_data: Dict, critical_projects: List[Dict], risk_signals: List[Dict]) -> str:
        """대표님용 아침 브리핑"""
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>🏢 전사 경영 브리핑</h2>
            
            <h3>🚨 긴급 의사결정 필요</h3>
            <ul>
        """
        
        for project in critical_projects[:3]:
            html_content += f"<li><strong>{project.get('name')}</strong>: {project.get('status')} (위험도: {project.get('risk_score')})</li>"
        
        html_content += f"""
            </ul>
            
            <h3>⚠️ 조직 신호</h3>
            <ul>
        """
        
        for signal in risk_signals[:5]:
            html_content += f"<li>{signal.get('type')}: {signal.get('explanation')}</li>"
        
        html_content += f"""
            </ul>
            
            <h3>📊 주요 지표</h3>
            <ul>
                <li>보고 제출률: {org_data.get('report_submission_rate', 0):.1%}</li>
                <li>고위험 프로젝트: {len(critical_projects)}</li>
                <li>주의 필요 신호: {len(risk_signals)}</li>
            </ul>
            
            <p style="color: #666; font-size: 12px;">
                생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M")}
            </p>
        </div>
        """
        
        return html_content
