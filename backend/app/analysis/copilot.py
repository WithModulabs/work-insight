"""RAG-based Copilot engine for natural language queries"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import math
import httpx

from config import settings


class CopilotEngine:
    """경영 Copilot 엔진 - RAG 기반 자연어 질의 처리"""
    
    # 질의 의도 분류를 위한 키워드
    INTENT_KEYWORDS = {
        "status": ["어디서", "어떤", "현황", "상태", "진행", "상황", "얼마나", "몇"],
        "analysis": ["왜", "이유", "원인", "이유가뭔가", "분석", "어떻게"],
        "people": ["누가", "누구", "팀", "사람", "조직", "인물"],
        "action": ["뭐해야", "어떻게해", "방법", "권고", "액션", "조치"],
        "comparison": ["비교", "차이", "다른", "어떤게", "누가더"],
    }
    
    def __init__(self, db_context=None):
        self.db_context = db_context
        self.query_history = []
        self.orchestration_endpoint = settings.ORCHESTRATION_USER_ENDPOINT
    
    def process_query(self, query: str, user_role: str, team_id: Optional[int] = None) -> Dict:
        """
        자연어 질의를 처리하고 답변 생성
        """
        # 질의 의도 분류
        intent = self._classify_intent(query)

        # 오케스트레이션 에이전트가 연결되어 있으면 우선 사용
        orchestrated_result = self._try_orchestration_agent(
            query=query,
            intent=intent,
            user_role=user_role,
            team_id=team_id,
        )
        if orchestrated_result:
            return orchestrated_result
        
        # 권한 기반 검색 범위 결정
        search_scope = self._determine_search_scope(user_role, team_id)
        
        # 관련 문서 검색
        relevant_docs = self._retrieve_documents(query, intent, search_scope)
        
        # 데이터 집계 및 분석
        evidence = self._analyze_evidence(relevant_docs, intent)
        
        # 답변 생성
        response = self._generate_response(query, intent, evidence, user_role)
        
        # 추천 후속 질문
        follow_ups = self._generate_follow_ups(query, intent)
        
        return {
            "query": query,
            "intent": intent,
            "response": response,
            "evidence": evidence,
            "confidence": self._calculate_confidence(len(relevant_docs), evidence),
            "follow_ups": follow_ups,
        }

    def _try_orchestration_agent(
        self,
        query: str,
        intent: str,
        user_role: str,
        team_id: Optional[int],
    ) -> Optional[Dict]:
        if not self.orchestration_endpoint:
            return None

        headers = {
            "Content-Type": "application/json",
        }
        if settings.ORCHESTRATION_API_KEY:
            headers["api-key"] = settings.ORCHESTRATION_API_KEY
        if settings.ORCHESTRATION_BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {settings.ORCHESTRATION_BEARER_TOKEN}"

        payload = {
            "query": query,
            "intent": intent,
            "user_role": user_role,
            "team_id": team_id,
        }

        endpoint = self.orchestration_endpoint.strip()
        candidate_urls: List[str] = [endpoint]
        if "/api/projects/" in endpoint and not endpoint.endswith("/"):
            candidate_urls.insert(0, endpoint + "/")

        body = None
        try:
            with httpx.Client(timeout=settings.ORCHESTRATION_TIMEOUT_SECONDS) as client:
                for url in dict.fromkeys(candidate_urls):
                    try:
                        response = client.post(url, headers=headers, json=payload)
                        response.raise_for_status()
                        body = response.json()
                        break
                    except Exception:
                        continue
        except Exception:
            return None

        if body is None:
            return None

        response_text = (
            body.get("response_text")
            or body.get("response")
            or body.get("answer")
            or "오케스트레이션 에이전트 응답을 받았지만 본문이 비어 있습니다."
        )
        if isinstance(response_text, dict):
            response_text = response_text.get("answer", json.dumps(response_text, ensure_ascii=False))

        evidence = body.get("evidence")
        if not isinstance(evidence, list):
            evidence = []

        follow_ups = body.get("suggested_follow_ups") or body.get("follow_ups") or []
        if not isinstance(follow_ups, list):
            follow_ups = []

        confidence = body.get("confidence_score")
        if not isinstance(confidence, (float, int)):
            confidence = body.get("confidence", 0.7)

        return {
            "query": query,
            "intent": intent,
            "response": str(response_text),
            "evidence": evidence,
            "confidence": float(confidence),
            "follow_ups": follow_ups,
        }
    
    def _classify_intent(self, query: str) -> str:
        """질의 의도 분류"""
        query_lower = query.lower()
        
        intent_scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            intent_scores[intent] = score
        
        # 가장 높은 점수의 의도 반환
        return max(intent_scores, key=intent_scores.get) if max(intent_scores.values()) > 0 else "status"
    
    def _determine_search_scope(self, user_role: str, team_id: Optional[int]) -> Dict:
        """권한에 따른 검색 범위 결정"""
        scope = {
            "can_access_org": user_role in ["director", "admin"],
            "can_access_team": user_role in ["team_lead", "director", "admin"],
            "can_access_sensitive": user_role in ["hr", "admin"],
            "team_id": team_id,
        }
        return scope
    
    def _retrieve_documents(self, query: str, intent: str, scope: Dict) -> List[Dict]:
        """
        관련 문서 검색 (하이브리드 검색)
        실제 구현에서는 벡터 DB + 키워드 검색 결합
        """
        documents = []
        
        # 키워드 기반 검색
        keyword_docs = self._keyword_search(query, scope)
        documents.extend(keyword_docs)
        
        # 의도별 특화 검색
        if intent == "status":
            # 프로젝트 상태, 현황 관련 문서
            status_docs = self._search_status_documents(query, scope)
            documents.extend(status_docs)
        
        elif intent == "analysis":
            # 분석, 근거 관련 문서
            analysis_docs = self._search_analysis_documents(query, scope)
            documents.extend(analysis_docs)
        
        elif intent == "people":
            # 사람, 팀 관련 문서
            people_docs = self._search_people_documents(query, scope)
            documents.extend(people_docs)
        
        elif intent == "action":
            # 액션, 추천 관련 문서
            action_docs = self._search_action_documents(query, scope)
            documents.extend(action_docs)
        
        return list({d['id']: d for d in documents}.values())  # 중복 제거
    
    def _keyword_search(self, query: str, scope: Dict) -> List[Dict]:
        """키워드 기반 검색"""
        # 실제 구현에서는 DB 쿼리 실행
        # 여기서는 예시만 제공
        return [
            {
                "id": "doc_1",
                "source": "daily_report",
                "content": "프로젝트 A가 진행 중입니다",
                "date": datetime.now(),
                "author": "팀원1",
                "relevance": 0.9
            }
        ]
    
    def _search_status_documents(self, query: str, scope: Dict) -> List[Dict]:
        """상태 관련 문서 검색"""
        return []
    
    def _search_analysis_documents(self, query: str, scope: Dict) -> List[Dict]:
        """분석 관련 문서 검색"""
        return []
    
    def _search_people_documents(self, query: str, scope: Dict) -> List[Dict]:
        """사람/팀 관련 문서 검색"""
        return []
    
    def _search_action_documents(self, query: str, scope: Dict) -> List[Dict]:
        """액션 관련 문서 검색"""
        return []
    
    def _analyze_evidence(self, documents: List[Dict], intent: str) -> Dict:
        """
        검색된 문서에서 근거 추출 및 분석
        """
        if not documents:
            return {
                "type": "insufficient_data",
                "summary": "관련 데이터가 부족합니다",
                "sources": [],
            }
        
        # 의도에 따른 분석
        if intent == "status":
            return self._analyze_status_evidence(documents)
        elif intent == "analysis":
            return self._analyze_cause_evidence(documents)
        elif intent == "people":
            return self._analyze_people_evidence(documents)
        elif intent == "action":
            return self._analyze_action_evidence(documents)
        elif intent == "comparison":
            return self._analyze_comparison_evidence(documents)
        
        return {"type": "general", "sources": documents}
    
    def _analyze_status_evidence(self, documents: List[Dict]) -> Dict:
        """상태 분석"""
        summary = self._synthesize_documents(documents)
        return {
            "type": "status",
            "summary": summary,
            "sources": documents,
            "metrics": self._extract_metrics(documents),
        }
    
    def _analyze_cause_evidence(self, documents: List[Dict]) -> Dict:
        """원인 분석"""
        root_causes = self._identify_root_causes(documents)
        return {
            "type": "causal",
            "root_causes": root_causes,
            "supporting_evidence": documents,
        }
    
    def _analyze_people_evidence(self, documents: List[Dict]) -> Dict:
        """사람/조직 분석"""
        people_insights = self._extract_people_insights(documents)
        return {
            "type": "people",
            "insights": people_insights,
            "sources": documents,
        }
    
    def _analyze_action_evidence(self, documents: List[Dict]) -> Dict:
        """액션/권고 분석"""
        recommendations = self._generate_recommendations(documents)
        return {
            "type": "action",
            "recommendations": recommendations,
            "sources": documents,
        }
    
    def _analyze_comparison_evidence(self, documents: List[Dict]) -> Dict:
        """비교 분석"""
        comparisons = self._perform_comparison(documents)
        return {
            "type": "comparison",
            "comparisons": comparisons,
            "sources": documents,
        }
    
    def _synthesize_documents(self, documents: List[Dict]) -> str:
        """문서 합성 및 요약"""
        # 실제 구현에서는 LLM 사용
        return " ".join([doc.get("content", "")[:100] for doc in documents[:3]])
    
    def _extract_metrics(self, documents: List[Dict]) -> Dict:
        """지표 추출"""
        return {
            "document_count": len(documents),
            "date_range": f"{documents[0].get('date')} ~ {documents[-1].get('date')}",
        }
    
    def _identify_root_causes(self, documents: List[Dict]) -> List[str]:
        """근본 원인 식별"""
        causes = []
        
        # 문서에서 원인 패턴 추출
        for doc in documents:
            content = doc.get("content", "").lower()
            
            if "지연" in content and "원인" in content:
                causes.append("일정 지연")
            if "갈등" in content:
                causes.append("협업 갈등")
            if "리소스" in content:
                causes.append("리소스 부족")
        
        return list(set(causes))
    
    def _extract_people_insights(self, documents: List[Dict]) -> Dict:
        """사람 관련 인사이트 추출"""
        return {
            "affected_people": [],
            "sentiment_trend": "neutral",
            "key_issues": [],
        }
    
    def _generate_recommendations(self, documents: List[Dict]) -> List[str]:
        """권고사항 생성"""
        recommendations = []
        
        # 문서 기반 권고 생성
        for doc in documents:
            if doc.get("source") == "daily_report":
                if "지연" in doc.get("content", ""):
                    recommendations.append("프로젝트 리소스 추가 검토")
                if "갈등" in doc.get("content", ""):
                    recommendations.append("팀 미팅을 통한 협업 개선")
        
        return recommendations[:5]  # 상위 5개만 반환
    
    def _perform_comparison(self, documents: List[Dict]) -> List[Dict]:
        """비교 분석"""
        return [
            {
                "category": "시간",
                "comparison": "최근 주 대비 이전 주의 차이",
            }
        ]
    
    def _generate_response(self, query: str, intent: str, evidence: Dict, user_role: str) -> str:
        """
        최종 답변 생성
        실제 구현에서는 LLM 사용
        """
        # 시뮬레이션 답변 생성
        response_template = {
            "status": "프로젝트 A는 현재 온트랙 상태입니다.",
            "analysis": "지연의 주요 원인은 리소스 부족으로 파악됩니다.",
            "people": "팀원 B가 최근 업무 부하가 높은 것으로 보입니다.",
            "action": "프로젝트 리소스를 추가하고 우선순위를 재조정하는 것을 권고합니다.",
            "comparison": "이번 주가 지난 주 대비 더 많은 지연 신호를 보이고 있습니다.",
        }
        
        return response_template.get(intent, "해당 질문에 대해 답변할 수 없습니다.")
    
    def _generate_follow_ups(self, query: str, intent: str) -> List[str]:
        """추천 후속 질문 생성"""
        follow_ups = {
            "status": [
                "이 프로젝트의 병목은 무엇인가요?",
                "이 프로젝트의 일정이 지연될 위험은?",
            ],
            "analysis": [
                "이 문제를 해결하려면?",
                "비슷한 사례가 있었나요?",
            ],
            "people": [
                "이 팀원을 어떻게 지원할 수 있을까요?",
                "비슷한 신호를 보이는 다른 팀원이 있나요?",
            ],
            "action": [
                "이 조치의 우선순위는?",
                "할 일 순서는?",
            ],
        }
        
        return follow_ups.get(intent, ["더 구체적으로 물어봐주세요."])[:3]
    
    def _calculate_confidence(self, doc_count: int, evidence: Dict) -> float:
        """답변 신뢰도 계산"""
        if doc_count == 0:
            return 0.1
        elif doc_count < 3:
            return 0.5
        elif doc_count < 10:
            return 0.7
        else:
            return 0.9


class QuerySuggester:
    """추천 질문 생성"""
    
    @staticmethod
    def get_suggested_questions(user_role: str, recent_data: Dict) -> List[Dict]:
        """
        사용자 역할과 최근 데이터를 기반으로 추천 질문 생성
        """
        suggestions = []
        
        if user_role == "director":
            suggestions = [
                {"question": "이번 주 가장 위험한 프로젝트는?", "category": "status"},
                {"question": "조직에서 지금 가장 긴급한 이슈는?", "category": "status"},
                {"question": "최근 일주일 간 리스크 신호가 증가한 팀은?", "category": "analysis"},
                {"question": "우리 팀에서 케어가 필요한 사람은?", "category": "people"},
            ]
        
        elif user_role == "team_lead":
            suggestions = [
                {"question": "우리 팀의 미완료 업무가 가장 많은 사람은?", "category": "people"},
                {"question": "이번 주 팀의 병목 이슈는?", "category": "status"},
                {"question": "팀원 중에 번아웃 신호가 있는 사람?", "category": "analysis"},
                {"question": "우선적으로 지원해야 할 프로젝트는?", "category": "action"},
            ]
        
        elif user_role == "team_member":
            suggestions = [
                {"question": "오늘 내 우선순위는?", "category": "status"},
                {"question": "내 현재 프로젝트의 지연 위험은?", "category": "analysis"},
                {"question": "나에게 필요한 지원은?", "category": "action"},
            ]
        
        return suggestions
