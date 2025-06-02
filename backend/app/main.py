"""
FNM FastAPI 메인 애플리케이션
아파트 이사예약 관리 시스템의 백엔드 API 서버입니다.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.db.database import init_db
# API 라우터 import
from app.api import users, reservations, notices

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    FastAPI 애플리케이션 팩토리 함수
    앱 설정, 미들웨어, 라우터를 구성합니다.
    
    Returns:
        FastAPI: 구성된 FastAPI 애플리케이션 인스턴스
    """
    
    # FastAPI 앱 인스턴스 생성
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc",  # ReDoc
        openapi_url="/openapi.json"
    )
    
    # CORS 미들웨어 설정
    # Next.js 프론트엔드와의 통신을 위해 CORS를 허용합니다.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # API 라우터 등록
    app.include_router(users.router)
    app.include_router(reservations.router)
    app.include_router(notices.router)
    
    return app


# FastAPI 앱 인스턴스 생성
app = create_application()


@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 시 실행되는 이벤트
    데이터베이스 초기화 및 필요한 설정을 수행합니다.
    """
    logger.info("🚀 FNM FastAPI 서버를 시작합니다...")
    logger.info(f"📊 데이터베이스: {settings.DATABASE_URL}")
    logger.info(f"🌍 허용된 Origins: {settings.ALLOWED_ORIGINS}")
    
    # 데이터베이스 초기화 (개발용)
    # 프로덕션에서는 Alembic 마이그레이션 사용 권장
    try:
        init_db()
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    애플리케이션 종료 시 실행되는 이벤트
    리소스 정리 및 연결 종료를 수행합니다.
    """
    logger.info("🛑 FNM FastAPI 서버를 종료합니다...")


# 기본 엔드포인트들
@app.get("/", tags=["Root"])
async def root():
    """
    루트 엔드포인트
    API 서버의 기본 정보를 반환합니다.
    """
    return {
        "message": "🏠 FNM - 아파트 이사예약 관리 시스템",
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    헬스체크 엔드포인트
    서버 상태와 데이터베이스 연결 상태를 확인합니다.
    """
    try:
        # 데이터베이스 연결 테스트는 추후 구현
        return {
            "status": "healthy",
            "message": "✅ 서버가 정상적으로 작동 중입니다.",
            "timestamp": "2024-12-18",
            "database": "connected",  # 실제 DB 연결 확인 로직 추가 예정
            "version": settings.VERSION
        }
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 상태 확인에 실패했습니다.")


@app.get("/api/test", tags=["Test"])
async def api_test():
    """
    API 테스트 엔드포인트
    프론트엔드에서 백엔드 연결을 테스트하기 위한 엔드포인트입니다.
    """
    return {
        "message": "🎉 FastAPI 백엔드 연결 성공!",
        "frontend_message": "Next.js에서 이 메시지를 받았다면 API 통신이 정상입니다.",
        "cors_enabled": True,
        "timestamp": "2024-12-18T10:00:00Z"
    }


# 전역 예외 처리기
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    전역 예외 처리기
    예상하지 못한 에러를 적절히 처리하고 로깅합니다.
    """
    logger.error(f"전역 에러 발생: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "내부 서버 오류",
            "message": "문제가 지속되면 관리자에게 문의하세요.",
            "detail": str(exc) if settings.DEBUG else "서버 오류"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # 개발 서버 실행
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 코드 변경 시 자동 재시작
        log_level="info"
    ) 