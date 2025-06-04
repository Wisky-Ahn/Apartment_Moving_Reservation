"""
API 요청 데이터 검증 미들웨어
모든 HTTP 요청의 데이터를 자동으로 검증하고 정리
"""
import json
import re
from typing import Dict, Any, Optional, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status
from urllib.parse import parse_qs

from app.core.validators import validate_request_data, SecurityValidator
from app.core.exceptions import ValidationException, ErrorCode
from app.core.logging import api_logger, security_logger, LogCategory
from app.core.response import error_response


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    요청 데이터 검증 미들웨어
    
    모든 HTTP 요청의 데이터를 자동으로 검증하고,
    보안 위험이 있는 입력을 차단합니다.
    """
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        """
        미들웨어 초기화
        
        Args:
            app: FastAPI 애플리케이션 인스턴스
            config: 검증 설정
        """
        super().__init__(app)
        self.config = config or {}
        
        # 검증에서 제외할 경로
        self.exclude_paths = self.config.get('exclude_paths', [
            '/health',
            '/docs',
            '/redoc',
            '/openapi.json',
            '/favicon.ico',
            '/static/'
        ])
        
        # 검증 규칙이 다른 경로들
        self.validation_rules = self.config.get('validation_rules', {
            '/api/users/register': 'user',
            '/api/users/register-admin': 'user',
            '/api/users/login': 'user',
            '/api/users/': 'user',
            '/api/reservations/': 'reservation',
            '/api/notices/': 'general'
        })
        
        # 엄격한 검증이 필요한 경로 (관리자 API 등)
        self.strict_validation_paths = self.config.get('strict_validation_paths', [
            '/api/users/admin/',
            '/api/admin/',
            '/api/super-admin/'
        ])
    
    async def dispatch(self, request: Request, call_next):
        """
        요청 처리 및 검증
        
        Args:
            request: HTTP 요청 객체
            call_next: 다음 미들웨어 또는 엔드포인트 함수
            
        Returns:
            Response: HTTP 응답 객체
        """
        # 제외 경로 확인
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # 검증이 필요한 메서드만 처리 (GET은 제외)
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            request_id = getattr(request.state, 'request_id', None)
            logger = api_logger.set_request_id(request_id) if request_id else api_logger
            
            try:
                # 요청 데이터 추출 및 검증
                await self._validate_request(request, logger)
                
            except ValidationException as e:
                # 검증 실패 시 에러 응답 반환
                logger.log_validation_error(
                    field=e.details.get('field', 'unknown') if e.details else 'unknown',
                    value="request_data",
                    error_message=e.message,
                    path=request.url.path,
                    method=request.method
                )
                
                return JSONResponse(
                    status_code=e.status_code,
                    content=e.detail
                )
            
            except Exception as e:
                # 예상치 못한 에러
                logger.error(
                    f"Validation middleware error: {str(e)}",
                    category=LogCategory.VALIDATION,
                    exc_info=True,
                    path=request.url.path,
                    method=request.method
                )
                
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error_code": ErrorCode.INTERNAL_SERVER_ERROR,
                        "message": "검증 처리 중 오류가 발생했습니다.",
                        "user_message": "잠시 후 다시 시도해주세요.",
                        "success": False
                    }
                )
        
        # 쿼리 파라미터 검증 (모든 메서드)
        try:
            self._validate_query_params(request)
        except ValidationException as e:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail
            )
        
        # 다음 미들웨어/엔드포인트 호출
        return await call_next(request)
    
    def _should_exclude_path(self, path: str) -> bool:
        """경로가 검증에서 제외되어야 하는지 확인"""
        return any(path.startswith(exclude_path) for exclude_path in self.exclude_paths)
    
    async def _validate_request(self, request: Request, logger) -> None:
        """요청 데이터 검증"""
        path = request.url.path
        method = request.method
        
        # 요청 본문 데이터 추출
        request_data = await self._extract_request_data(request)
        
        if not request_data:
            return
        
        # 검증 타입 결정
        validation_type = self._get_validation_type(path, method)
        
        # 엄격한 검증 경로인지 확인
        is_strict = any(path.startswith(strict_path) for strict_path in self.strict_validation_paths)
        
        logger.info(
            f"Validating request data for {method} {path}",
            category=LogCategory.VALIDATION,
            validation_type=validation_type,
            is_strict=is_strict,
            data_keys=list(request_data.keys()) if isinstance(request_data, dict) else None
        )
        
        # 데이터 검증 수행
        if isinstance(request_data, dict):
            # 엄격한 검증이 필요한 경우 추가 보안 검사
            if is_strict:
                self._strict_security_validation(request_data, path)
            
            # 메인 검증 실행
            validated_data = validate_request_data(request_data, validation_type)
            
            # 검증된 데이터를 request에 저장 (엔드포인트에서 사용 가능)
            request.state.validated_data = validated_data
        
        logger.info(
            f"Request validation completed for {method} {path}",
            category=LogCategory.VALIDATION,
            validation_type=validation_type
        )
    
    async def _extract_request_data(self, request: Request) -> Optional[Dict[str, Any]]:
        """요청 본문에서 데이터 추출"""
        try:
            content_type = request.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                # JSON 데이터
                body = await request.body()
                if body:
                    data = json.loads(body.decode())
                    # 요청 본문을 다시 읽을 수 있도록 설정
                    request._body = body
                    return data
            
            elif 'application/x-www-form-urlencoded' in content_type:
                # 폼 데이터
                form = await request.form()
                return dict(form)
            
            elif 'multipart/form-data' in content_type:
                # 멀티파트 폼 데이터 (파일 업로드 등)
                form = await request.form()
                data = {}
                for key, value in form.items():
                    if hasattr(value, 'filename'):
                        # 파일 필드
                        data[key] = {
                            'filename': value.filename,
                            'content_type': getattr(value, 'content_type', 'unknown'),
                            'size': len(await value.read()) if hasattr(value, 'read') else 0
                        }
                    else:
                        # 일반 필드
                        data[key] = value
                return data
            
            return None
            
        except json.JSONDecodeError as e:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=f"잘못된 JSON 형식입니다: {str(e)}",
                user_message="올바른 JSON 형식으로 데이터를 전송해주세요."
            )
        except Exception as e:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=f"요청 데이터를 읽을 수 없습니다: {str(e)}",
                user_message="요청 형식을 확인해주세요."
            )
    
    def _validate_query_params(self, request: Request) -> None:
        """쿼리 파라미터 검증"""
        query_params = dict(request.query_params)
        
        if not query_params:
            return
        
        # 각 쿼리 파라미터에 대해 보안 검증
        for key, value in query_params.items():
            if isinstance(value, str):
                # SQL 인젝션 검사
                if SecurityValidator.check_sql_injection(value):
                    request_id = getattr(request.state, 'request_id', None)
                    security_logger.set_request_id(request_id).log_security_event(
                        event="SQL injection attempt in query parameter",
                        severity="high",
                        parameter=key,
                        value=value[:100],
                        path=request.url.path
                    )
                    
                    raise ValidationException(
                        error_code=ErrorCode.VALIDATION_ERROR,
                        message=f"쿼리 파라미터 '{key}'에 허용되지 않는 문자가 포함되어 있습니다.",
                        user_message="쿼리 파라미터에 특수 문자가 포함되어 있습니다.",
                        details={"field": key, "reason": "sql_injection_detected"}
                    )
                
                # XSS 방지를 위한 HTML 태그 체크
                if re.search(r'<[^>]+>', value):
                    raise ValidationException(
                        error_code=ErrorCode.VALIDATION_ERROR,
                        message=f"쿼리 파라미터 '{key}'에 HTML 태그가 포함되어 있습니다.",
                        user_message="HTML 태그는 사용할 수 없습니다.",
                        details={"field": key, "reason": "html_tags_detected"}
                    )
                
                # 길이 제한
                if len(value) > 1000:
                    raise ValidationException(
                        error_code=ErrorCode.VALIDATION_ERROR,
                        message=f"쿼리 파라미터 '{key}'가 너무 깁니다.",
                        user_message="쿼리 파라미터가 허용된 길이를 초과했습니다.",
                        details={"field": key, "max_length": 1000}
                    )
    
    def _get_validation_type(self, path: str, method: str) -> str:
        """경로와 메서드에 따른 검증 타입 결정"""
        # 직접 매칭
        for rule_path, validation_type in self.validation_rules.items():
            if path.startswith(rule_path):
                return validation_type
        
        # 패턴 매칭
        if '/api/users/' in path:
            return 'user'
        elif '/api/reservations/' in path:
            return 'reservation'
        elif '/api/notices/' in path:
            return 'general'
        
        return 'general'
    
    def _strict_security_validation(self, data: Dict[str, Any], path: str) -> None:
        """엄격한 보안 검증 (관리자 API 등)"""
        request_id = getattr(security_logger, 'request_id', None)
        logger = security_logger.set_request_id(request_id) if request_id else security_logger
        
        logger.log_security_event(
            event="Strict validation applied",
            severity="low",
            path=path,
            data_fields=list(data.keys()) if isinstance(data, dict) else None
        )
        
        # 관리자 API에 대한 추가 검증 로직
        for key, value in data.items():
            if isinstance(value, str):
                # 더 엄격한 패턴 검사
                suspicious_patterns = [
                    r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # 스크립트 태그
                    r'javascript:',  # 자바스크립트 프로토콜
                    r'data:.*base64',  # base64 인코딩된 데이터
                    r'vbscript:',  # VBScript
                    r'onload\s*=',  # 이벤트 핸들러
                    r'onerror\s*=',
                    r'onclick\s*=',
                ]
                
                for pattern in suspicious_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.log_security_event(
                            event="Suspicious pattern detected in admin API",
                            severity="critical",
                            pattern=pattern,
                            field=key,
                            path=path
                        )
                        
                        raise ValidationException(
                            error_code=ErrorCode.VALIDATION_ERROR,
                            message=f"필드 '{key}'에 허용되지 않는 패턴이 발견되었습니다.",
                            user_message="보안상 허용되지 않는 입력입니다.",
                            details={"field": key, "reason": "suspicious_pattern"}
                        )


def setup_validation_middleware(app, config: Optional[Dict[str, Any]] = None):
    """
    애플리케이션에 검증 미들웨어 추가
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
        config: 검증 설정
    """
    # 기본 설정
    default_config = {
        'exclude_paths': [
            '/health',
            '/docs',
            '/redoc', 
            '/openapi.json',
            '/favicon.ico',
            '/static/'
        ],
        'validation_rules': {
            '/api/users/register': 'user',
            '/api/users/register-admin': 'user', 
            '/api/users/login': 'user',
            '/api/users/': 'user',
            '/api/reservations/': 'reservation',
            '/api/notices/': 'general'
        },
        'strict_validation_paths': [
            '/api/users/admin/',
            '/api/admin/',
            '/api/super-admin/'
        ]
    }
    
    # 사용자 설정과 기본 설정 병합
    final_config = {**default_config, **(config or {})}
    
    # 미들웨어 추가
    app.add_middleware(ValidationMiddleware, config=final_config)
    
    api_logger.info(
        "Validation middleware added to application",
        category=LogCategory.VALIDATION,
        config=final_config
    ) 