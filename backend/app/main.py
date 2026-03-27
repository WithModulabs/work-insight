"""FastAPI main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from app.api import reports, oneone, dashboard, copilot


# Lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    # Startup
    print("🚀 WorkInsight 애플리케이션 시작")
    yield
    # Shutdown
    print("👋 WorkInsight 애플리케이션 종료")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="경영 인사이트 Copilot - 퇴근보고, 상담, 프로젝트를 기반으로 의사결정을 지원",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 포함
app.include_router(reports.router, prefix="/api/reports", tags=["퇴근보고"])
app.include_router(oneone.router, prefix="/api/oneone", tags=["1:1 상담"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["대시보드"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["Copilot"])


@app.get("/", tags=["Root"])
async def root():
    """API 진입점"""
    return {
        "message": "WorkInsight API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
    )
