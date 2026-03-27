"""
Azure AD / Office 365 이메일 서비스
Microsoft Graph API를 통해 이메일 전송
"""

import json
import aiohttp
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import settings
from azure.identity import ClientSecretCredential


class EmailService:
    """Microsoft Graph API를 사용한 이메일 서비스"""
    
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    
    def __init__(self):
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.sender_email = settings.EMAIL_SENDER
        self.credential = None
        self.access_token = None
        
        if settings.EMAIL_ENABLED:
            self._initialize_credential()
    
    def _initialize_credential(self):
        """Azure AD 인증 초기화"""
        try:
            self.credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            print("✅ Azure AD 인증 초기화 완료")
        except Exception as e:
            print(f"❌ Azure AD 인증 초기화 실패: {e}")
    
    async def _get_access_token(self) -> Optional[str]:
        """접근 토큰 획득"""
        if not self.credential:
            return None
        
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default")
            self.access_token = token.token
            return self.access_token
        except Exception as e:
            print(f"❌ 토큰 획득 실패: {e}")
            return None
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        이메일 전송
        
        Args:
            to: 수신자 이메일 리스트
            subject: 제목
            html_body: HTML 본문
            cc: 참조 리스트
            bcc: 숨은 참조 리스트
            attachments: 첨부 파일 리스트
        
        Returns:
            bool: 성공 여부
        """
        if not settings.EMAIL_ENABLED:
            print("⚠️ 이메일 서비스가 활성화되지 않았습니다")
            return False
        
        token = await self._get_access_token()
        if not token:
            print("❌ 접근 토큰을 획득할 수 없습니다")
            return False
        
        # 이메일 페이로드 구성
        email_payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_body
                },
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
                "isReminderOn": False,
            },
            "saveToSentItems": True
        }
        
        # CC 추가
        if cc:
            email_payload["message"]["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc
            ]
        
        # BCC 추가
        if bcc:
            email_payload["message"]["bccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in bcc
            ]
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                url = f"{self.GRAPH_API_BASE}/me/sendMail"
                
                async with session.post(
                    url,
                    json=email_payload,
                    headers=headers
                ) as response:
                    if response.status == 202:
                        print(f"✅ 이메일 전송 성공: {subject}")
                        return True
                    else:
                        error = await response.text()
                        print(f"❌ 이메일 전송 실패 ({response.status}): {error}")
                        return False
        
        except Exception as e:
            print(f"❌ 이메일 전송 중 오류: {e}")
            return False
    
    async def send_morning_brief_email(
        self,
        recipient_email: str,
        brief_html: str,
        organization_name: str = "WorkInsight"
    ) -> bool:
        """
        아침 브리핑 이메일 전송
        
        Args:
            recipient_email: 수신자 이메일
            brief_html: 브리핑 HTML 콘텐츠
            organization_name: 조직명
        
        Returns:
            bool: 성공 여부
        """
        today = datetime.now().strftime("%Y년 %m월 %d일")
        subject = f"[{organization_name}] {today} 아침 경영 브리핑"
        
        # 이메일 헤더 추가
        html_body = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f5f5f5; padding: 20px; border-radius: 0 0 8px 8px; }}
                    .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>🎯 {organization_name} 아침 경영 브리핑</h2>
                        <p>{today}</p>
                    </div>
                    <div class="content">
                        {brief_html}
                    </div>
                    <div class="footer">
                        <p>본 이메일은 WorkInsight 자동화 시스템에서 발송되었습니다.</p>
                        <p>문의사항은 경영팀(admin@workinsight.local)으로 연락해주세요.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(
            to=[recipient_email],
            subject=subject,
            html_body=html_body
        )
    
    async def send_risk_alert_email(
        self,
        recipient_email: str,
        risk_signals: List[Dict[str, Any]],
        organization_name: str = "WorkInsight"
    ) -> bool:
        """
        리스크 신호 알림 이메일 전송
        
        Args:
            recipient_email: 수신자 이메일
            risk_signals: 리스크 신호 리스트
            organization_name: 조직명
        
        Returns:
            bool: 성공 여부
        """
        subject = f"[{organization_name}] ⚠️ 리스크 신호 긴급 알림"
        
        # 리스크 신호를 HTML로 변환
        risk_html = ""
        for signal in risk_signals:
            level_icon = "🚨" if signal.get("level") == "critical" else "⚠️"
            risk_html += f"""
            <div style="padding: 12px; margin: 8px 0; background: #fff3cd; border-left: 4px solid #ff9800; border-radius: 4px;">
                <strong>{level_icon} {signal.get('title', 'Risk Alert')}</strong>
                <p>{signal.get('message', '')}</p>
                <small>{signal.get('timestamp', '')}</small>
            </div>
            """
        
        html_body = f"""
        <h3>긴급 리스크 신호가 감지되었습니다</h3>
        <p>다음과 같은 조직 내 위험 신호가 감지되었으니 빠른 조치를 부탁드립니다.</p>
        {risk_html}
        <hr>
        <p><strong>권장 조치:</strong></p>
        <ul>
            <li>대해당 팀원/팀리드와 즉시 면담</li>
            <li>1:1 상담 기록 검토</li>
            <li>대시보드에서 상세 정보 확인</li>
        </ul>
        """
        
        return await self.send_email(
            to=[recipient_email],
            subject=subject,
            html_body=html_body
        )


# 글로벌 인스턴스
email_service = EmailService()
