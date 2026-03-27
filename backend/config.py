import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    APP_NAME: str = "WorkInsight"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # 데이터베이스
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./workinsight.db"
    )
    
    # OpenAI / LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")
    
    # 보안
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "your-secret-key-change-in-production"
    )
    
    # API 포트
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    # SMTP
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Azure AD / Office 365 이메일 발송 설정
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "JoniS@M365x12195465.OnMicrosoft.com")
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "False").lower() == "true"

    # SharePoint 이메일 저장 설정 (Microsoft Graph)
    MICROSOFT_TENANT_ID: str = os.getenv("MICROSOFT_TENANT_ID", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    SHAREPOINT_SITE_ID: str = os.getenv("SHAREPOINT_SITE_ID", "")
    SHAREPOINT_LIST_ID: str = os.getenv("SHAREPOINT_LIST_ID", "")
    GRAPH_MAILBOX_USER_ID: str = os.getenv("GRAPH_MAILBOX_USER_ID", "")
    GRAPH_NOTIFICATION_URL: str = os.getenv("GRAPH_NOTIFICATION_URL", "")
    GRAPH_SUBSCRIPTION_CLIENT_STATE: str = os.getenv("GRAPH_SUBSCRIPTION_CLIENT_STATE", "")
    GRAPH_SUBSCRIPTION_RESOURCE: str = os.getenv("GRAPH_SUBSCRIPTION_RESOURCE", "")
    GRAPH_SUBSCRIPTION_EXPIRATION_MINUTES: int = int(
        os.getenv("GRAPH_SUBSCRIPTION_EXPIRATION_MINUTES", "1440")
    )

    # 오케스트레이션 에이전트 설정
    ORCHESTRATION_USER_ENDPOINT: str = os.getenv(
        "ORCHESTRATION_USER_ENDPOINT",
        "",
    )
    ORCHESTRATION_API_KEY: str = os.getenv("ORCHESTRATION_API_KEY", "")
    ORCHESTRATION_BEARER_TOKEN: str = os.getenv("ORCHESTRATION_BEARER_TOKEN", "")
    ORCHESTRATION_TIMEOUT_SECONDS: float = float(
        os.getenv("ORCHESTRATION_TIMEOUT_SECONDS", "20")
    )
    
    # RAG 설정
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "chroma")  # chroma, faiss, pinecone
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # 분석 설정
    RISK_THRESHOLD: float = float(os.getenv("RISK_THRESHOLD", "0.7"))
    SENTIMENT_THRESHOLD: float = float(os.getenv("SENTIMENT_THRESHOLD", "-0.3"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
