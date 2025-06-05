"""
표준 API 응답 형식 정의
모든 API 엔드포인트에서 일관된 응답 구조 제공
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.core.exceptions import ErrorCode


class StandardResponse(BaseModel):
    """
    표준 API 응답 모델
    모든 API 응답에 사용되는 기본 구조
    """
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error_code: Optional[ErrorCode] = None
    errors: Optional[List[Dict[str, Any]]] = None
    meta: Optional[Dict[str, Any]] = None


class PaginationMeta(BaseModel):
    """
    페이지네이션 메타데이터
    """
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(StandardResponse):
    """
    페이지네이션이 적용된 응답 모델
    """
    data: List[Any]
    meta: PaginationMeta


def success_response(
    data: Any = None,
    message: str = "요청이 성공적으로 처리되었습니다.",
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    성공 응답 생성 헬퍼 함수
    
    Args:
        data: 응답 데이터
        message: 성공 메시지
        meta: 메타데이터 (페이지네이션 등)
        status_code: HTTP 상태 코드
        
    Returns:
        JSONResponse: 표준 성공 응답
    """
    response_data = StandardResponse(
        success=True,
        message=message,
        data=data,
        meta=meta
    )
    
    # Pydantic 모델과 datetime 객체를 올바르게 직렬화
    serialized_data = jsonable_encoder(response_data.dict(exclude_none=True))
    
    return JSONResponse(
        content=serialized_data,
        status_code=status_code
    )


def error_response(
    error_code: ErrorCode,
    message: str,
    user_message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    errors: Optional[List[Dict[str, Any]]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """
    에러 응답 생성 헬퍼 함수
    
    Args:
        error_code: 에러 코드
        message: 개발자용 에러 메시지
        user_message: 사용자용 에러 메시지
        details: 에러 상세 정보
        errors: 검증 에러 목록
        status_code: HTTP 상태 코드
        
    Returns:
        JSONResponse: 표준 에러 응답
    """
    response_data = {
        "success": False,
        "error_code": error_code.value,
        "message": message,
        "user_message": user_message or message
    }
    
    if details:
        response_data["details"] = details
        
    if errors:
        response_data["errors"] = errors
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )


def paginated_response(
    items: List[Any],
    page: int,
    size: int,
    total: int,
    message: str = "데이터를 성공적으로 조회했습니다.",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    페이지네이션 응답 생성 헬퍼 함수
    
    Args:
        items: 페이지네이션된 데이터 목록
        page: 현재 페이지 번호
        size: 페이지 크기
        total: 전체 항목 수
        message: 성공 메시지
        status_code: HTTP 상태 코드
        
    Returns:
        JSONResponse: 페이지네이션 응답
    """
    pages = (total + size - 1) // size  # 전체 페이지 수 계산
    
    meta = PaginationMeta(
        page=page,
        size=size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )
    
    response_data = PaginatedResponse(
        success=True,
        message=message,
        data=items,
        meta=meta
    )
    
    # Pydantic 모델과 datetime 객체를 올바르게 직렬화
    serialized_data = jsonable_encoder(response_data.dict(exclude_none=True))
    
    return JSONResponse(
        content=serialized_data,
        status_code=status_code
    )


def created_response(
    data: Any = None,
    message: str = "리소스가 성공적으로 생성되었습니다.",
    resource_id: Optional[Union[str, int]] = None
) -> JSONResponse:
    """
    생성 성공 응답 (201 Created)
    
    Args:
        data: 생성된 리소스 데이터
        message: 성공 메시지
        resource_id: 생성된 리소스 ID
        
    Returns:
        JSONResponse: 생성 성공 응답
    """
    meta = {"resource_id": resource_id} if resource_id else None
    
    return success_response(
        data=data,
        message=message,
        meta=meta,
        status_code=status.HTTP_201_CREATED
    )


def updated_response(
    data: Any = None,
    message: str = "리소스가 성공적으로 수정되었습니다.",
    resource_id: Optional[Union[str, int]] = None
) -> JSONResponse:
    """
    수정 성공 응답
    
    Args:
        data: 수정된 리소스 데이터
        message: 성공 메시지
        resource_id: 수정된 리소스 ID
        
    Returns:
        JSONResponse: 수정 성공 응답
    """
    meta = {"resource_id": resource_id} if resource_id else None
    
    return success_response(
        data=data,
        message=message,
        meta=meta,
        status_code=status.HTTP_200_OK
    )


def deleted_response(
    message: str = "리소스가 성공적으로 삭제되었습니다.",
    resource_id: Optional[Union[str, int]] = None
) -> JSONResponse:
    """
    삭제 성공 응답
    
    Args:
        message: 성공 메시지
        resource_id: 삭제된 리소스 ID
        
    Returns:
        JSONResponse: 삭제 성공 응답
    """
    meta = {"resource_id": resource_id} if resource_id else None
    
    return success_response(
        data=None,
        message=message,
        meta=meta,
        status_code=status.HTTP_200_OK
    )


def no_content_response(
    message: str = "요청이 성공적으로 처리되었습니다."
) -> JSONResponse:
    """
    내용 없음 응답 (204 No Content)
    
    Args:
        message: 성공 메시지
        
    Returns:
        JSONResponse: 내용 없음 응답
    """
    return JSONResponse(
        content={"success": True, "message": message},
        status_code=status.HTTP_204_NO_CONTENT
    )


def validation_error_response(
    errors: List[Dict[str, Any]],
    message: str = "입력 데이터 검증에 실패했습니다."
) -> JSONResponse:
    """
    검증 에러 응답 (422 Unprocessable Entity)
    
    Args:
        errors: 검증 에러 목록
        message: 에러 메시지
        
    Returns:
        JSONResponse: 검증 에러 응답
    """
    return error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message=message,
        user_message="입력하신 정보를 다시 확인해주세요.",
        errors=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


def unauthorized_response(
    message: str = "인증이 필요합니다."
) -> JSONResponse:
    """
    인증 실패 응답 (401 Unauthorized)
    
    Args:
        message: 에러 메시지
        
    Returns:
        JSONResponse: 인증 실패 응답
    """
    return error_response(
        error_code=ErrorCode.UNAUTHORIZED,
        message=message,
        user_message="로그인이 필요합니다.",
        status_code=status.HTTP_401_UNAUTHORIZED
    )


def forbidden_response(
    message: str = "접근 권한이 없습니다."
) -> JSONResponse:
    """
    권한 없음 응답 (403 Forbidden)
    
    Args:
        message: 에러 메시지
        
    Returns:
        JSONResponse: 권한 없음 응답
    """
    return error_response(
        error_code=ErrorCode.FORBIDDEN,
        message=message,
        user_message="이 작업을 수행할 권한이 없습니다.",
        status_code=status.HTTP_403_FORBIDDEN
    )


def not_found_response(
    resource: str = "리소스",
    message: Optional[str] = None
) -> JSONResponse:
    """
    리소스 없음 응답 (404 Not Found)
    
    Args:
        resource: 리소스 이름
        message: 커스텀 에러 메시지
        
    Returns:
        JSONResponse: 리소스 없음 응답
    """
    default_message = f"{resource}를 찾을 수 없습니다."
    
    return error_response(
        error_code=ErrorCode.NOT_FOUND,
        message=message or default_message,
        user_message=f"요청하신 {resource}를 찾을 수 없습니다.",
        status_code=status.HTTP_404_NOT_FOUND
    )


def conflict_response(
    message: str = "리소스 충돌이 발생했습니다.",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    리소스 충돌 응답 (409 Conflict)
    
    Args:
        message: 에러 메시지
        details: 충돌 상세 정보
        
    Returns:
        JSONResponse: 리소스 충돌 응답
    """
    return error_response(
        error_code=ErrorCode.DUPLICATE_VALUE,
        message=message,
        user_message="이미 존재하는 데이터입니다.",
        details=details,
        status_code=status.HTTP_409_CONFLICT
    )


def internal_server_error_response(
    message: str = "서버 내부 오류가 발생했습니다.",
    error_id: Optional[str] = None
) -> JSONResponse:
    """
    서버 내부 오류 응답 (500 Internal Server Error)
    
    Args:
        message: 에러 메시지
        error_id: 에러 추적 ID
        
    Returns:
        JSONResponse: 서버 내부 오류 응답
    """
    details = {"error_id": error_id} if error_id else None
    
    return error_response(
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        message=message,
        user_message="일시적인 서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        details=details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# 응답 헬퍼 함수들을 모아놓은 클래스
class ResponseHelper:
    """
    응답 생성 헬퍼 클래스
    모든 표준 응답 함수들을 하나의 클래스로 묶어서 사용 편의성 제공
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "요청이 성공적으로 처리되었습니다.", **kwargs):
        return success_response(data=data, message=message, **kwargs)
    
    @staticmethod
    def error(error_code: ErrorCode, message: str, **kwargs):
        return error_response(error_code=error_code, message=message, **kwargs)
    
    @staticmethod
    def paginated(items: List[Any], page: int, size: int, total: int, **kwargs):
        return paginated_response(items=items, page=page, size=size, total=total, **kwargs)
    
    @staticmethod
    def created(data: Any = None, **kwargs):
        return created_response(data=data, **kwargs)
    
    @staticmethod
    def updated(data: Any = None, **kwargs):
        return updated_response(data=data, **kwargs)
    
    @staticmethod
    def deleted(**kwargs):
        return deleted_response(**kwargs)
    
    @staticmethod
    def validation_error(errors: List[Dict[str, Any]], **kwargs):
        return validation_error_response(errors=errors, **kwargs)
    
    @staticmethod
    def unauthorized(**kwargs):
        return unauthorized_response(**kwargs)
    
    @staticmethod
    def forbidden(**kwargs):
        return forbidden_response(**kwargs)
    
    @staticmethod
    def not_found(resource: str = "리소스", **kwargs):
        return not_found_response(resource=resource, **kwargs)
    
    @staticmethod
    def conflict(**kwargs):
        return conflict_response(**kwargs)
    
    @staticmethod
    def internal_error(**kwargs):
        return internal_server_error_response(**kwargs) 