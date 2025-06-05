"""
보안 관련 유틸리티
JWT 토큰 생성/검증, 비밀번호 해싱, 인증/권한 시스템
강화된 보안 및 에러 처리 적용
argon2를 사용한 고성능 패스워드 해싱
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ErrorCode,
    raise_unauthorized,
    raise_forbidden
)
from app.db.database import get_db
from app.crud.user import get_user, get_user_by_username

# Argon2 패스워드 해셔 (고성능)
ph = PasswordHasher()

# JWT Bearer 토큰 스키마
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증 (Argon2 사용)
    평문 비밀번호와 해시된 비밀번호를 비교
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """
    비밀번호 해싱 (Argon2 사용)
    평문 비밀번호를 해시로 변환
    """
    try:
        return ph.hash(password)
    except HashingError as e:
        raise Exception(f"패스워드 해싱 실패: {str(e)}")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    사용자 정보를 포함한 토큰 생성
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """
    JWT 토큰 검증
    토큰의 유효성을 확인하고 페이로드 반환
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 토큰 만료 확인
        exp = payload.get("exp")
        if exp is None:
            return None
        
        if datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        # 토큰 타입 확인
        token_type = payload.get("type")
        if token_type != "access":
            return None
        
        return payload
    except JWTError:
        return None

async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    현재 사용자 토큰 검증 및 사용자 정보 반환
    
    Args:
        credentials: HTTP Authorization 헤더의 Bearer 토큰
        db: 데이터베이스 세션
    
    Returns:
        User: 인증된 사용자 객체
    
    Raises:
        AuthenticationException: 토큰이 유효하지 않거나 사용자를 찾을 수 없을 때
    """
    try:
        # 토큰 검증
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise AuthenticationException(
                error_code=ErrorCode.TOKEN_EXPIRED,
                message="토큰이 만료되었거나 유효하지 않습니다.",
                user_message="다시 로그인해주세요."
            )
        
        # 사용자명 추출
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None or user_id is None:
            raise AuthenticationException(
                error_code=ErrorCode.INVALID_CREDENTIALS,
                message="토큰에서 사용자 정보를 찾을 수 없습니다.",
                user_message="올바르지 않은 인증 정보입니다."
            )
        
    except JWTError:
        raise AuthenticationException(
            error_code=ErrorCode.TOKEN_EXPIRED,
            message="JWT 토큰 파싱 에러",
            user_message="토큰이 손상되었습니다. 다시 로그인해주세요."
        )
    except AuthenticationException:
        raise
    except Exception as e:
        raise AuthenticationException(
            error_code=ErrorCode.UNAUTHORIZED,
            message=f"토큰 검증 중 예상치 못한 오류: {str(e)}",
            user_message="인증 처리 중 오류가 발생했습니다."
        )
    
    # 사용자 정보 조회
    user = get_user_by_username(db, username=username)
    if user is None:
        raise AuthenticationException(
            error_code=ErrorCode.USER_NOT_FOUND,
            message=f"사용자를 찾을 수 없습니다: {username}",
            user_message="사용자 정보를 찾을 수 없습니다."
        )
    
    # 계정 활성화 확인
    if not user.is_active:
        if user.is_admin and not user.admin_approved:
            raise AuthenticationException(
                error_code=ErrorCode.ADMIN_APPROVAL_REQUIRED,
                message=f"관리자 승인 대기 중인 사용자: {username}",
                user_message="관리자 승인 대기 중입니다. 슈퍼관리자에게 문의하세요."
            )
        else:
            raise AuthenticationException(
                error_code=ErrorCode.ACCOUNT_DISABLED,
                message=f"비활성화된 사용자: {username}",
                user_message="비활성화된 계정입니다. 관리자에게 문의하세요."
            )
    
    return user

async def get_current_active_user(
    current_user = Depends(get_current_user_token)
):
    """
    현재 활성 사용자 반환 (간단한 래퍼)
    """
    return current_user

async def get_current_admin_user(
    current_user = Depends(get_current_active_user)
):
    """
    현재 사용자가 관리자인지 확인
    
    Args:
        current_user: 현재 인증된 사용자
    
    Returns:
        User: 관리자 사용자 객체
    
    Raises:
        AuthorizationException: 관리자 권한이 없을 때
    """
    if not current_user.is_admin:
        raise AuthorizationException(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=f"관리자 권한이 없는 사용자의 접근 시도: {current_user.username}",
            user_message="관리자 권한이 필요합니다."
        )
    
    # 관리자 승인 확인
    if not current_user.admin_approved:
        raise AuthorizationException(
            error_code=ErrorCode.ADMIN_APPROVAL_REQUIRED,
            message=f"승인되지 않은 관리자의 접근 시도: {current_user.username}",
            user_message="관리자 승인이 완료되지 않았습니다."
        )
    
    return current_user

async def get_current_super_admin_user(
    current_user = Depends(get_current_active_user)
):
    """
    현재 사용자가 슈퍼관리자인지 확인
    
    Args:
        current_user: 현재 인증된 사용자
    
    Returns:
        User: 슈퍼관리자 사용자 객체
    
    Raises:
        AuthorizationException: 슈퍼관리자 권한이 없을 때
    """
    if not current_user.is_super_admin:
        raise AuthorizationException(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=f"슈퍼관리자 권한이 없는 사용자의 접근 시도: {current_user.username}",
            user_message="슈퍼관리자 권한이 필요합니다."
        )
    
    return current_user

def require_user_permission(target_user_id: int, current_user_id: int, is_admin: bool = False):
    """
    사용자 권한 확인 헬퍼 함수
    자기 자신의 정보이거나 관리자 권한이 있어야 함
    
    Args:
        target_user_id: 접근하려는 대상 사용자 ID
        current_user_id: 현재 사용자 ID
        is_admin: 현재 사용자가 관리자인지 여부
    
    Raises:
        AuthorizationException: 권한이 없을 때
    """
    if target_user_id != current_user_id and not is_admin:
        raise AuthorizationException(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=f"사용자 {current_user_id}가 사용자 {target_user_id}의 정보에 무단 접근 시도",
            user_message="본인의 정보만 접근 가능합니다."
        )

def require_resource_permission(resource_owner_id: int, current_user_id: int, is_admin: bool = False):
    """
    리소스 권한 확인 헬퍼 함수
    리소스 소유자이거나 관리자 권한이 있어야 함
    
    Args:
        resource_owner_id: 리소스 소유자 ID
        current_user_id: 현재 사용자 ID
        is_admin: 현재 사용자가 관리자인지 여부
    
    Raises:
        AuthorizationException: 권한이 없을 때
    """
    if resource_owner_id != current_user_id and not is_admin:
        raise AuthorizationException(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=f"사용자 {current_user_id}가 사용자 {resource_owner_id}의 리소스에 무단 접근 시도",
            user_message="해당 리소스에 접근할 권한이 없습니다."
        ) 