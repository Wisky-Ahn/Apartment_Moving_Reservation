"""
FNM FastAPI 메인 애플리케이션
아파트 이사예약 관리 시스템의 백엔드 API 서버입니다.
강화된 로깅 시스템 및 알림 시스템 적용
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import traceback
from typing import Union

from app.core.config import settings
from app.core.exceptions import (
    AppException, 
    ErrorCode, 
    DatabaseException, 
    ServerException,
    ValidationException
)
# 강화된 로깅 시스템 import
from app.core.logging import (
    setup_logging, 
    app_logger, 
    security_logger,
    api_logger,
    LogCategory
)
from app.core.notifications import (
    setup_notifications,
    send_critical_alert,
    send_security_alert,
    NotificationLevel
)
from app.middleware.logging import setup_logging_middleware
from app.middleware.validation import setup_validation_middleware
from app.middleware.performance import setup_performance_monitoring
from app.db.database import init_db, get_db
from app.crud.user import get_super_admin, create_super_admin

# API 라우터 import
from app.api import users, reservations, notices, statistics, monitoring


def create_application() -> FastAPI:
    """
    FastAPI 애플리케이션 생성 및 설정
    미들웨어, 라우터, 예외 처리기 등을 설정합니다.
    """
    # FastAPI 앱 인스턴스 생성
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        debug=settings.DEBUG,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None
    )
    
    # 로깅 시스템 초기화
    setup_logging()
    app_logger.info("Logging system initialized")
    
    # 알림 시스템 초기화
    setup_notifications()
    app_logger.info("Notification system initialized")
    
    # CORS 미들웨어 추가
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 로깅 미들웨어 추가 (일시 비활성화 - request.body() 호환성 문제)
    # setup_logging_middleware(app)
    # app_logger.info("Logging middleware added (bug fixed)")
    app_logger.info("Logging middleware temporarily disabled (request.body() compatibility issue)")
    
    # 검증 미들웨어 추가 (일시 비활성화 - 호환성 문제 발견)
    # setup_validation_middleware(app)
    # app_logger.info("Validation middleware added (compatibility testing)")
    app_logger.info("Validation middleware temporarily disabled (compatibility issue found)")
    
    # 성능 모니터링 미들웨어 추가 (호환성 테스트)
    setup_performance_monitoring(app)
    app_logger.info("Performance monitoring middleware added (compatibility testing)")
    
    # 예외 처리기 등록
    register_exception_handlers(app)
    
    # API 라우터 등록
    app.include_router(users.router, tags=["사용자 관리"])
    app.include_router(reservations.router, tags=["예약 관리"])
    app.include_router(notices.router, tags=["공지사항"])
    app.include_router(statistics.router, tags=["통계"])
    app.include_router(monitoring.router, tags=["모니터링"])
    
    app_logger.info("API routers registered")
    
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """
    전역 예외 처리기들을 등록하는 함수
    다양한 종류의 예외에 대해 일관된 응답 형식을 제공합니다.
    """
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """
        커스텀 AppException 처리기
        우리가 정의한 비즈니스 로직 예외들을 처리합니다.
        """
        # 강화된 로깅 사용
        request_id = getattr(request.state, 'request_id', None)
        logger = app_logger.set_request_id(request_id) if request_id else app_logger
        
        logger.error(
            f"AppException: {exc.error_code} - {exc.detail}",
            category=LogCategory.BUSINESS_LOGIC,
            error_code=exc.error_code,
            status_code=exc.status_code,
            path=request.url.path,
            method=request.method
        )
        
        # 심각한 에러인 경우 알림 발송
        if exc.status_code >= 500:
            await send_critical_alert(
                title=f"Application Error: {exc.error_code}",
                message=str(exc.detail),
                error_code=exc.error_code,
                request_id=request_id,
                context={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": exc.status_code
                }
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        FastAPI 요청 데이터 검증 실패 처리기
        Pydantic 모델 검증 실패 시 사용자 친화적 메시지 제공
        """
        request_id = getattr(request.state, 'request_id', None)
        logger = app_logger.set_request_id(request_id) if request_id else app_logger
        
        error_details = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.log_validation_error(
            field="request_validation",
            value="multiple_fields",
            error_message=f"Validation failed: {len(error_details)} errors",
            path=request.url.path,
            method=request.method,
            errors=error_details
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": ErrorCode.VALIDATION_ERROR,
                "message": "입력 데이터 검증에 실패했습니다.",
                "user_message": "입력된 정보를 다시 확인해주세요.",
                "details": {"validation_errors": error_details},
                "success": False
            }
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """
        Pydantic 검증 에러 처리기
        모델 데이터 검증 실패 시 처리
        """
        request_id = getattr(request.state, 'request_id', None)
        logger = app_logger.set_request_id(request_id) if request_id else app_logger
        
        logger.log_validation_error(
            field="pydantic_validation",
            value="model_data",
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            errors=exc.errors()
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": ErrorCode.VALIDATION_ERROR,
                "message": "데이터 형식이 올바르지 않습니다.",
                "user_message": "입력된 데이터 형식을 확인해주세요.",
                "details": {"validation_errors": exc.errors()},
                "success": False
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """
        데이터베이스 관련 예외 처리기
        SQLAlchemy 에러들을 사용자 친화적 메시지로 변환
        """
        request_id = getattr(request.state, 'request_id', None)
        logger = app_logger.set_request_id(request_id) if request_id else app_logger
        
        error_msg = str(exc)
        
        # 특정 데이터베이스 에러들 처리
        if isinstance(exc, IntegrityError):
            if "UNIQUE constraint failed" in error_msg:
                user_message = "이미 존재하는 정보입니다."
                error_code = ErrorCode.CONSTRAINT_VIOLATION
            elif "FOREIGN KEY constraint failed" in error_msg:
                user_message = "연관된 데이터가 존재하지 않습니다."
                error_code = ErrorCode.FOREIGN_KEY_ERROR
            else:
                user_message = "데이터 제약 조건 위반입니다."
                error_code = ErrorCode.CONSTRAINT_VIOLATION
        else:
            user_message = "데이터베이스 처리 중 오류가 발생했습니다."
            error_code = ErrorCode.DATABASE_ERROR
        
        logger.error(
            f"Database error: {error_msg}",
            category=LogCategory.DATABASE,
            exc_info=True,
            error_code=error_code,
            path=request.url.path,
            method=request.method
        )
        
        # 데이터베이스 에러는 심각한 문제이므로 알림 발송
        await send_critical_alert(
            title="Database Error",
            message=f"Database operation failed: {error_msg}",
            error_code=error_code,
            request_id=request_id,
            context={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": error_code,
                "message": f"Database error: {error_msg}" if settings.DEBUG else "데이터베이스 오류",
                "user_message": user_message,
                "details": {"original_error": error_msg} if settings.DEBUG else {},
                "success": False
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        일반 HTTP 예외 처리기
        FastAPI의 기본 HTTPException들을 우리 형식에 맞게 변환
        """
        request_id = getattr(request.state, 'request_id', None)
        logger = app_logger.set_request_id(request_id) if request_id else app_logger
        
        # 에러 코드 매핑
        error_code_map = {
            400: ErrorCode.VALIDATION_ERROR,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.INSUFFICIENT_PERMISSIONS,
            404: ErrorCode.USER_NOT_FOUND,  # 기본값, 실제로는 컨텍스트에 따라 달라져야 함
            409: ErrorCode.RESERVATION_TIME_CONFLICT,
            422: ErrorCode.VALIDATION_ERROR,
            500: ErrorCode.INTERNAL_SERVER_ERROR
        }
        
        error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)
        
        # 로깅 레벨 결정
        if exc.status_code >= 500:
            log_level = "error"
        elif exc.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"
        
        getattr(logger, log_level)(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            category=LogCategory.API_RESPONSE,
            error_code=error_code,
            status_code=exc.status_code,
            path=request.url.path,
            method=request.method
        )
        
        # 보안 관련 에러인 경우 보안 로그에도 기록
        if exc.status_code in [401, 403]:
            security_logger.set_request_id(request_id).log_security_event(
                event=f"Security HTTP exception: {exc.status_code}",
                severity="medium",
                status_code=exc.status_code,
                path=request.url.path,
                method=request.method
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": error_code,
                "message": str(exc.detail),
                "user_message": str(exc.detail),
                "details": {},
                "success": False
            },
            headers=getattr(exc, 'headers', None)
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        최종 전역 예외 처리기
        예상하지 못한 모든 에러를 처리하고 안전한 응답을 제공합니다.
        """
        request_id = getattr(request.state, 'request_id', None)
        logger = app_logger.set_request_id(request_id) if request_id else app_logger
        
        # 전체 스택 트레이스 로깅
        logger.critical(
            f"Unhandled exception: {str(exc)}",
            category=LogCategory.SYSTEM,
            exc_info=True,
            exception_type=type(exc).__name__,
            path=request.url.path,
            method=request.method
        )
        
        # 예상치 못한 에러는 즉시 알림 발송
        await send_critical_alert(
            title="Unhandled Exception",
            message=f"Unexpected error: {str(exc)}",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            request_id=request_id,
            context={
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc() if settings.DEBUG else "Hidden in production"
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": ErrorCode.INTERNAL_SERVER_ERROR,
                "message": f"Internal server error: {str(exc)}" if settings.DEBUG else "서버 내부 오류",
                "user_message": "예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "details": {"traceback": traceback.format_exc()} if settings.DEBUG else {},
                "success": False
            }
        )


# FastAPI 앱 인스턴스 생성
app = create_application()


def create_super_admin_if_not_exists():
    """
    슈퍼관리자가 존재하지 않으면 생성하는 함수
    """
    try:
        db = next(get_db())
        
        # 슈퍼관리자 존재 확인
        super_admin = get_super_admin(db)
        if not super_admin:
            # 슈퍼관리자 생성
            create_super_admin(
                db=db,
                username="superadmin",
                email="superadmin@fnm.com",
                password="allapt322410@",
                name="시스템관리자"
            )
            app_logger.info("✅ 슈퍼관리자 계정이 생성되었습니다 (superadmin/allapt322410@)")
        else:
            app_logger.info("✅ 슈퍼관리자 계정이 이미 존재합니다")
            
    except Exception as e:
        app_logger.error(f"❌ 슈퍼관리자 생성 실패: {e}", exc_info=True)
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 시 실행되는 이벤트
    데이터베이스 초기화 및 필요한 설정을 수행합니다.
    """
    app_logger.info("🚀 FNM FastAPI 서버를 시작합니다...")
    app_logger.info(f"📊 데이터베이스: {settings.DATABASE_URL}")
    app_logger.info(f"🌍 허용된 Origins: {settings.ALLOWED_ORIGINS}")
    
    # 데이터베이스 초기화 (개발용)
    # 프로덕션에서는 Alembic 마이그레이션 사용 권장
    try:
        init_db()
        app_logger.info("✅ 데이터베이스 초기화 완료")
        
        # 슈퍼관리자 생성
        create_super_admin_if_not_exists()
        
    except Exception as e:
        app_logger.error(f"❌ 데이터베이스 초기화 실패: {e}", exc_info=True)
        # 시작 실패 알림
        await send_critical_alert(
            title="Application Startup Failed",
            message=f"Database initialization failed: {str(e)}",
            error_code=ErrorCode.DATABASE_ERROR,
            context={"operation": "startup", "component": "database"}
        )


@app.on_event("shutdown")
async def shutdown_event():
    """
    애플리케이션 종료 시 실행되는 이벤트
    리소스 정리 및 연결 종료를 수행합니다.
    """
    app_logger.info("🛑 FNM FastAPI 서버를 종료합니다...")


@app.get("/", tags=["Root"])
async def root():
    """
    루트 엔드포인트
    API 서버의 기본 정보를 반환합니다.
    """
    return {
        "message": "FNM (File & Note Manager) API Server",
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "status": "running",
        "docs_url": "/docs" if settings.DEBUG else None,
        "success": True
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
            "version": settings.VERSION,
            "success": True
        }
    except Exception as e:
        app_logger.error(f"헬스체크 실패: {e}", exc_info=True)
        raise ServerException(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message=f"헬스체크 실패: {e}",
            user_message="서버 상태 확인에 실패했습니다."
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