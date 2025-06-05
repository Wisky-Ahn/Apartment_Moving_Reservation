"""
API 요청/응답 로깅 미들웨어
모든 HTTP 요청과 응답을 구조화된 형태로 로깅
"""
import time
import json
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status

from app.core.logging import (
    api_logger, 
    security_logger, 
    generate_request_id,
    LogCategory
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    API 요청/응답 로깅 미들웨어
    모든 HTTP 요청을 인터셉트하여 로깅 처리
    """
    
    def __init__(self, app, exclude_paths: list = None):
        """
        미들웨어 초기화
        
        Args:
            app: FastAPI 애플리케이션 인스턴스
            exclude_paths: 로깅에서 제외할 경로 목록
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        요청 처리 및 로깅
        
        Args:
            request: HTTP 요청 객체
            call_next: 다음 미들웨어 또는 엔드포인트 함수
            
        Returns:
            Response: HTTP 응답 객체
        """
        # 제외 경로 확인
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # 요청 ID 생성 및 설정
        request_id = generate_request_id()
        
        # 요청 시작 시간 기록
        start_time = time.time()
        
        # 요청 정보 추출
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params) if request.query_params else None
        user_agent = request.headers.get("user-agent")
        client_ip = self._get_client_ip(request)
        
        # 요청 본문 읽기 (가능한 경우)
        request_body = await self._get_request_body(request)
        
        # 사용자 정보 추출 (Authorization 헤더에서)
        user_info = await self._extract_user_info(request)
        
        # 로거에 컨텍스트 설정
        logger = api_logger.set_request_id(request_id)
        if user_info:
            logger.set_user_info(**user_info)
        
        # 요청 로깅
        logger.log_api_request(
            method=method,
            path=path,
            user_id=user_info.get("user_id") if user_info else None,
            request_data={
                "query_params": query_params,
                "body": request_body,
                "user_agent": user_agent,
                "client_ip": client_ip
            }
        )
        
        # 보안 관련 요청 별도 로깅
        if self._is_security_relevant(method, path):
            security_logger.set_request_id(request_id).log_security_event(
                event=f"Security relevant request: {method} {path}",
                severity="low",
                method=method,
                path=path,
                client_ip=client_ip,
                user_agent=user_agent
            )
        
        # 요청 헤더에 request_id 추가 (다운스트림 처리를 위해)
        request.state.request_id = request_id
        
        try:
            # 다음 미들웨어 또는 엔드포인트 호출
            response = await call_next(request)
            
            # 응답 시간 계산
            response_time_ms = (time.time() - start_time) * 1000
            
            # 응답 로깅
            logger.log_api_response(
                method=method,
                path=path,
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
            
            # 응답 헤더에 request_id 추가
            response.headers["X-Request-ID"] = request_id
            
            # 성능 경고 (응답 시간이 너무 긴 경우)
            if response_time_ms > 5000:  # 5초 이상
                logger.warning(
                    f"Slow API response: {method} {path} took {response_time_ms:.2f}ms",
                    category=LogCategory.PERFORMANCE,
                    method=method,
                    path=path,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code
                )
            
            # 에러 상태 코드인 경우 추가 로깅
            if response.status_code >= 400:
                severity = "high" if response.status_code >= 500 else "medium"
                logger.error(
                    f"API Error: {method} {path} returned {response.status_code}",
                    category=LogCategory.API_RESPONSE,
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    severity=severity
                )
            
            return response
            
        except Exception as exc:
            # 예외 발생 시 에러 로깅
            response_time_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"API Exception: {method} {path} - {str(exc)}",
                category=LogCategory.API_RESPONSE,
                exc_info=True,
                method=method,
                path=path,
                response_time_ms=response_time_ms,
                exception_type=type(exc).__name__,
                exception_message=str(exc)
            )
            
            # 보안 관련 예외인 경우 보안 로그에도 기록
            if self._is_security_exception(exc):
                security_logger.set_request_id(request_id).log_security_event(
                    event=f"Security exception: {type(exc).__name__}",
                    severity="high",
                    method=method,
                    path=path,
                    client_ip=client_ip,
                    exception_type=type(exc).__name__,
                    exception_message=str(exc)
                )
            
            # 예외를 다시 발생시켜 FastAPI가 처리하도록 함
            raise exc
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        # X-Forwarded-For 헤더 확인 (프록시 환경)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # X-Real-IP 헤더 확인
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 직접 연결
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _get_request_body(self, request: Request) -> dict:
        """
        요청 본문 추출 (가능한 경우)
        민감한 정보는 자동으로 마스킹됨 (SecurityFilter에서 처리)
        """
        try:
            # Content-Type 확인
            content_type = request.headers.get("content-type", "")
            
            if "application/json" in content_type:
                # JSON 본문 읽기 (한 번만 읽을 수 있으므로 주의 필요)
                body = await request.body()
                if body:
                    # 요청 본문을 다시 읽을 수 있도록 설정 (중요!)
                    request._body = body
                    return json.loads(body.decode())
            
            elif "application/x-www-form-urlencoded" in content_type:
                # 폼 데이터는 민감할 수 있으므로 키만 로깅
                form = await request.form()
                return {"form_fields": list(form.keys())} if form else None
            
            elif "multipart/form-data" in content_type:
                # 파일 업로드는 파일명과 크기만 로깅
                form = await request.form()
                file_info = {}
                for key, value in form.items():
                    if hasattr(value, 'filename'):
                        file_info[key] = {
                            "filename": value.filename,
                            "content_type": getattr(value, 'content_type', 'unknown')
                        }
                    else:
                        file_info[key] = "form_field"
                return file_info if file_info else None
            
            return None
            
        except Exception:
            # 본문 읽기 실패 시 무시 (로깅이 주 목적이 아니므로)
            return None
    
    async def _extract_user_info(self, request: Request) -> dict:
        """Authorization 헤더에서 사용자 정보 추출"""
        try:
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # JWT 토큰에서 사용자 정보를 추출하려면 
            # JWT 디코딩이 필요하지만, 여기서는 보안상 토큰 자체는 로깅하지 않음
            # 대신 토큰의 존재 여부만 확인
            return {"has_token": True}
            
        except Exception:
            return None
    
    def _is_security_relevant(self, method: str, path: str) -> bool:
        """보안 관련 요청인지 확인"""
        security_paths = [
            "/api/users/login",
            "/api/users/register",
            "/api/users/register-admin",
            "/api/users/admin/",
            "/admin/"
        ]
        
        # 관리자 관련 경로
        if "/admin/" in path:
            return True
        
        # 인증 관련 경로
        if any(sec_path in path for sec_path in security_paths):
            return True
        
        # PUT, DELETE 메서드는 보안 관련으로 간주
        if method in ["PUT", "DELETE", "PATCH"]:
            return True
        
        return False
    
    def _is_security_exception(self, exc: Exception) -> bool:
        """보안 관련 예외인지 확인"""
        security_exceptions = [
            "AuthenticationException",
            "AuthorizationException", 
            "PermissionError",
            "Forbidden",
            "Unauthorized"
        ]
        
        exc_name = type(exc).__name__
        return any(sec_exc in exc_name for sec_exc in security_exceptions)


# 미들웨어 설정을 위한 헬퍼 함수
def setup_logging_middleware(app, exclude_paths: list = None):
    """
    애플리케이션에 로깅 미들웨어 추가
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
        exclude_paths: 로깅에서 제외할 경로 목록
    """
    app.add_middleware(LoggingMiddleware, exclude_paths=exclude_paths) 