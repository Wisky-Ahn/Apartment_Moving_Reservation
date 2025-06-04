"""
커스텀 예외 클래스 및 에러 처리 시스템
API 에러를 체계적으로 관리하고 사용자 친화적인 메시지를 제공합니다.
"""
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ErrorCode(str, Enum):
    """
    에러 코드 정의
    각 에러 유형별로 고유한 코드를 할당하여 프론트엔드에서 적절한 처리 가능
    """
    # 인증 관련 에러
    UNAUTHORIZED = "AUTH_001"
    INVALID_CREDENTIALS = "AUTH_002"
    TOKEN_EXPIRED = "AUTH_003"
    INSUFFICIENT_PERMISSIONS = "AUTH_004"
    ACCOUNT_DISABLED = "AUTH_005"
    ADMIN_APPROVAL_REQUIRED = "AUTH_006"
    
    # 사용자 관련 에러
    USER_NOT_FOUND = "USER_001"
    USER_ALREADY_EXISTS = "USER_002"
    INVALID_USER_DATA = "USER_003"
    USER_INACTIVE = "USER_004"
    APARTMENT_NUMBER_REQUIRED = "USER_005"
    
    # 예약 관련 에러
    RESERVATION_NOT_FOUND = "RESERVATION_001"
    RESERVATION_TIME_CONFLICT = "RESERVATION_002"
    INVALID_RESERVATION_TIME = "RESERVATION_003"
    RESERVATION_ALREADY_APPROVED = "RESERVATION_004"
    RESERVATION_CANCELLED = "RESERVATION_005"
    PAST_DATE_RESERVATION = "RESERVATION_006"
    MAX_RESERVATIONS_EXCEEDED = "RESERVATION_007"
    
    # 공지사항 관련 에러
    NOTICE_NOT_FOUND = "NOTICE_001"
    INVALID_NOTICE_TYPE = "NOTICE_002"
    NOTICE_ALREADY_PUBLISHED = "NOTICE_003"
    
    # 데이터 검증 에러
    VALIDATION_ERROR = "VALIDATION_001"
    MISSING_REQUIRED_FIELD = "VALIDATION_002"
    INVALID_DATA_FORMAT = "VALIDATION_003"
    INVALID_DATE_RANGE = "VALIDATION_004"
    
    # 데이터베이스 에러
    DATABASE_ERROR = "DB_001"
    CONSTRAINT_VIOLATION = "DB_002"
    FOREIGN_KEY_ERROR = "DB_003"
    
    # 일반 서버 에러
    INTERNAL_SERVER_ERROR = "SERVER_001"
    SERVICE_UNAVAILABLE = "SERVER_002"
    RATE_LIMIT_EXCEEDED = "SERVER_003"
    
    # 일반적인 상태 코드
    NOT_FOUND = "GENERAL_001"
    DUPLICATE_VALUE = "GENERAL_002"
    OPERATION_FAILED = "GENERAL_003"
    BAD_REQUEST = "GENERAL_004"
    FORBIDDEN = "GENERAL_005"


class AppException(HTTPException):
    """
    애플리케이션 커스텀 예외 기본 클래스
    일관된 에러 응답 형식과 로깅을 제공합니다.
    """
    
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        user_message: str = None,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_code = error_code
        self.user_message = user_message or message
        self.details = details or {}
        
        # 로깅
        logger.error(f"[{error_code}] {message} - Details: {details}")
        
        # HTTPException 초기화
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "user_message": self.user_message,
                "details": self.details,
                "success": False
            },
            headers=headers
        )


class AuthenticationException(AppException):
    """인증 관련 예외"""
    def __init__(self, error_code: ErrorCode, message: str, user_message: str = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            message=message,
            user_message=user_message or "인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationException(AppException):
    """권한 관련 예외"""
    def __init__(self, error_code: ErrorCode, message: str, user_message: str = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            message=message,
            user_message=user_message or "이 작업을 수행할 권한이 없습니다."
        )


class ValidationException(AppException):
    """데이터 검증 예외"""
    def __init__(self, error_code: ErrorCode, message: str, details: Dict[str, Any] = None, user_message: str = None, field: str = None):
        validation_details = details or {}
        if field:
            validation_details["field"] = field
        
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            message=message,
            user_message=user_message or "입력된 데이터가 올바르지 않습니다.",
            details=validation_details
        )


class NotFoundException(AppException):
    """리소스를 찾을 수 없는 예외"""
    def __init__(self, error_code: ErrorCode, message: str, user_message: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            message=message,
            user_message=user_message or "요청한 정보를 찾을 수 없습니다."
        )


class DataException(AppException):
    """데이터 관련 예외 (404, 충돌 등)"""
    def __init__(self, error_code: ErrorCode, message: str, user_message: str = None):
        # 에러 코드에 따라 상태 코드 결정
        if error_code == ErrorCode.NOT_FOUND or "NOT_FOUND" in error_code:
            status_code = status.HTTP_404_NOT_FOUND
            default_message = "요청한 정보를 찾을 수 없습니다."
        elif error_code == ErrorCode.DUPLICATE_VALUE:
            status_code = status.HTTP_409_CONFLICT
            default_message = "이미 존재하는 데이터입니다."
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            default_message = "데이터 처리 중 오류가 발생했습니다."
        
        super().__init__(
            status_code=status_code,
            error_code=error_code,
            message=message,
            user_message=user_message or default_message
        )


class BusinessLogicException(AppException):
    """비즈니스 로직 관련 예외"""
    def __init__(self, error_code: ErrorCode, message: str, user_message: str = None):
        # 에러 코드에 따라 상태 코드 결정
        if error_code == ErrorCode.FORBIDDEN:
            status_code = status.HTTP_403_FORBIDDEN
            default_message = "이 작업을 수행할 권한이 없습니다."
        elif error_code == ErrorCode.BAD_REQUEST:
            status_code = status.HTTP_400_BAD_REQUEST
            default_message = "잘못된 요청입니다."
        elif error_code == ErrorCode.OPERATION_FAILED:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            default_message = "작업 처리 중 오류가 발생했습니다."
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            default_message = "요청을 처리할 수 없습니다."
        
        super().__init__(
            status_code=status_code,
            error_code=error_code,
            message=message,
            user_message=user_message or default_message
        )


class ConflictException(AppException):
    """리소스 충돌 예외"""
    def __init__(self, error_code: ErrorCode, message: str, user_message: str = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            message=message,
            user_message=user_message or "요청이 현재 상태와 충돌합니다."
        )


class BadRequestException(AppException):
    """잘못된 요청 예외"""
    def __init__(self, error_code: ErrorCode, message: str, user_message: str = None, details: Dict[str, Any] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            message=message,
            user_message=user_message or "잘못된 요청입니다.",
            details=details
        )


class DatabaseException(AppException):
    """데이터베이스 관련 예외"""
    def __init__(self, error_code: ErrorCode, message: str, user_message: str = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            message=message,
            user_message=user_message or "데이터 처리 중 오류가 발생했습니다."
        )


class ServerException(AppException):
    """서버 내부 에러 예외"""
    def __init__(self, error_code: ErrorCode, message: str, user_message: str = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            message=message,
            user_message=user_message or "서버에서 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


# 자주 사용되는 예외들을 위한 헬퍼 함수들
def raise_unauthorized(message: str = "인증이 필요합니다."):
    """인증 필요 예외 발생"""
    raise AuthenticationException(
        error_code=ErrorCode.UNAUTHORIZED,
        message=message
    )


def raise_forbidden(message: str = "권한이 없습니다."):
    """권한 없음 예외 발생"""
    raise AuthorizationException(
        error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
        message=message
    )


def raise_not_found(resource: str, identifier: Union[str, int] = None):
    """리소스 없음 예외 발생"""
    message = f"{resource}을(를) 찾을 수 없습니다."
    if identifier:
        message += f" (ID: {identifier})"
    
    if "사용자" in resource:
        error_code = ErrorCode.USER_NOT_FOUND
    elif "예약" in resource:
        error_code = ErrorCode.RESERVATION_NOT_FOUND
    elif "공지사항" in resource:
        error_code = ErrorCode.NOTICE_NOT_FOUND
    else:
        error_code = ErrorCode.VALIDATION_ERROR
    
    raise NotFoundException(
        error_code=error_code,
        message=message
    )


def raise_validation_error(field: str, value: Any = None, message: str = None):
    """데이터 검증 에러 발생"""
    if not message:
        message = f"'{field}' 필드의 값이 올바르지 않습니다."
    
    details = {"field": field}
    if value is not None:
        details["value"] = str(value)
    
    raise ValidationException(
        error_code=ErrorCode.VALIDATION_ERROR,
        message=message,
        details=details
    )


def raise_conflict(resource: str, reason: str = None):
    """
    409 Conflict 에러 발생
    
    Args:
        resource: 충돌이 발생한 리소스
        reason: 충돌 이유 (옵션)
    """
    message = f"{resource} 충돌 발생"
    if reason:
        message += f": {reason}"
    
    raise ConflictException(
        error_code=ErrorCode.DUPLICATE_VALUE,
        message=message,
        user_message=f"{resource}이(가) 이미 존재합니다."
    )


def raise_authentication_error(message: str = "인증에 실패했습니다.", user_message: str = None):
    """
    401 인증 에러 발생
    
    Args:
        message: 내부 로그 메시지
        user_message: 사용자에게 표시할 메시지
    """
    raise AuthenticationException(
        error_code=ErrorCode.UNAUTHORIZED,
        message=message,
        user_message=user_message or "인증이 필요합니다."
    )


def raise_authorization_error(message: str = "권한이 없습니다.", user_message: str = None):
    """
    403 권한 에러 발생
    
    Args:
        message: 내부 로그 메시지
        user_message: 사용자에게 표시할 메시지
    """
    raise AuthorizationException(
        error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
        message=message,
        user_message=user_message or "이 작업을 수행할 권한이 없습니다."
    ) 