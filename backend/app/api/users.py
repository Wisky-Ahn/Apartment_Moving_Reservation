"""
사용자 관리 API 라우터
사용자 등록, 인증, 정보 관리 엔드포인트
강화된 인증 및 권한 시스템 적용
표준 응답 형식 적용
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import or_
import time

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin
from app.crud.user import (
    create_user,
    create_admin_user,
    get_user,
    get_user_by_username,
    get_user_by_email,
    get_pending_admin_users,
    approve_admin_user,
    reject_admin_user,
    update_user,
    delete_user
)
from app.core.security import (
    verify_password, 
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
    get_current_super_admin_user,
    require_user_permission,
    require_resource_permission
)
from app.core.exceptions import (
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    DataException,
    BusinessLogicException,
    ErrorCode,
    raise_validation_error,
    raise_authentication_error,
    raise_authorization_error,
    raise_not_found,
    raise_conflict
)
from app.core.response import ResponseHelper

# APIRouter 인스턴스 생성
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "사용자를 찾을 수 없습니다"}}
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 사용자를 등록합니다.
    
    Args:
        user_data: 사용자 등록 데이터
        db: 데이터베이스 세션
        
    Returns:
        JSONResponse: 표준 생성 응답
        
    Raises:
        ValidationException: 사용자명 또는 이메일 중복 시
        BusinessLogicException: 등록 실패 시
    """
    try:
        # 사용자명 중복 확인
        if get_user_by_username(db, user_data.username):
            raise ValidationException(
                error_code=ErrorCode.DUPLICATE_VALUE,
                message=f"중복된 사용자명: {user_data.username}",
                user_message="이미 사용중인 사용자명입니다.",
                field="username"
            )
        
        # 이메일 중복 확인
        if get_user_by_email(db, user_data.email):
            raise ValidationException(
                error_code=ErrorCode.DUPLICATE_VALUE,
                message=f"중복된 이메일: {user_data.email}",
                user_message="이미 등록된 이메일 주소입니다.",
                field="email"
            )
        
        # 사용자 생성
        new_user = create_user(db, user_data)
        if not new_user:
            raise BusinessLogicException(
                error_code=ErrorCode.OPERATION_FAILED,
                message="사용자 생성 실패",
                user_message="사용자 등록에 실패했습니다. 다시 시도해주세요."
            )
        
        # 표준 생성 응답 반환
        return ResponseHelper.created(
            data=UserResponse.from_orm(new_user),
            message="사용자가 성공적으로 등록되었습니다.",
            resource_id=new_user.id
        )
        
    except (ValidationException, BusinessLogicException):
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"사용자 등록 중 예상치 못한 오류: {str(e)}",
            user_message="사용자 등록 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )

@router.post("/register-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_admin_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 관리자를 등록합니다 (승인 대기 상태).
    
    Args:
        user_data: 관리자 등록 데이터
        db: 데이터베이스 세션
        
    Returns:
        UserResponse: 생성된 관리자 정보
        
    Raises:
        ValidationException: 사용자명 또는 이메일 중복 시
        BusinessLogicException: 등록 실패 시
    """
    try:
        # 사용자명 중복 확인
        if get_user_by_username(db, user_data.username):
            raise ValidationException(
                error_code=ErrorCode.DUPLICATE_VALUE,
                message=f"중복된 사용자명: {user_data.username}",
                user_message="이미 사용중인 사용자명입니다.",
                field="username"
            )
        
        # 이메일 중복 확인
        if get_user_by_email(db, user_data.email):
            raise ValidationException(
                error_code=ErrorCode.DUPLICATE_VALUE,
                message=f"중복된 이메일: {user_data.email}",
                user_message="이미 등록된 이메일 주소입니다.",
                field="email"
            )
        
        # 관리자 계정 생성 (승인 대기 상태)
        new_admin = create_admin_user(db, user_data)
        if not new_admin:
            raise BusinessLogicException(
                error_code=ErrorCode.OPERATION_FAILED,
                message="관리자 생성 실패",
                user_message="관리자 등록에 실패했습니다. 다시 시도해주세요."
            )
        
        return new_admin
        
    except (ValidationException, BusinessLogicException):
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"관리자 등록 중 예상치 못한 오류: {str(e)}",
            user_message="관리자 등록 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )

@router.get("/admin/pending", response_model=List[UserResponse])
async def get_pending_admins(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    승인 대기 중인 관리자 목록을 조회합니다. (슈퍼관리자 전용)
    
    Args:
        db: 데이터베이스 세션
        current_user: 현재 슈퍼관리자 사용자
        
    Returns:
        List[UserResponse]: 승인 대기 중인 관리자 목록
    """
    try:
        pending_admins = get_pending_admin_users(db)
        return pending_admins
        
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"승인 대기 목록 조회 중 오류: {str(e)}",
            user_message="승인 대기 목록 조회 중 오류가 발생했습니다."
        )

@router.post("/admin/{user_id}/approve", response_model=UserResponse)
async def approve_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    관리자 계정을 승인합니다. (슈퍼관리자 전용)
    
    Args:
        user_id: 승인할 관리자 ID
        db: 데이터베이스 세션
        current_user: 현재 슈퍼관리자 사용자
        
    Returns:
        UserResponse: 승인된 관리자 정보
        
    Raises:
        DataException: 승인할 관리자를 찾을 수 없을 때
        BusinessLogicException: 승인 실패 시
    """
    try:
        approved_admin = approve_admin_user(db, user_id)
        if not approved_admin:
            raise DataException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"승인할 수 있는 관리자 계정을 찾을 수 없습니다: ID {user_id}",
                user_message="승인할 수 있는 관리자 계정을 찾을 수 없습니다."
            )
        
        return approved_admin
        
    except DataException:
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"관리자 승인 중 오류: {str(e)}",
            user_message="관리자 승인 중 오류가 발생했습니다."
        )

@router.delete("/admin/{user_id}/reject")
async def reject_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    관리자 계정을 거부합니다. (슈퍼관리자 전용)
    
    Args:
        user_id: 거부할 관리자 ID
        db: 데이터베이스 세션
        current_user: 현재 슈퍼관리자 사용자
        
    Returns:
        dict: 성공 메시지
        
    Raises:
        DataException: 거부할 관리자를 찾을 수 없을 때
        BusinessLogicException: 거부 실패 시
    """
    try:
        success = reject_admin_user(db, user_id)
        if not success:
            raise DataException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"거부할 수 있는 관리자 계정을 찾을 수 없습니다: ID {user_id}",
                user_message="거부할 수 있는 관리자 계정을 찾을 수 없습니다."
            )
        
        return {"message": f"관리자 계정 ID {user_id}가 성공적으로 거부되었습니다."}
        
    except DataException:
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"관리자 거부 중 오류: {str(e)}",
            user_message="관리자 거부 중 오류가 발생했습니다."
        )

@router.post("/test-login")
async def test_login_simple(user_credentials: UserLogin):
    """
    의존성 없는 간단한 로그인 테스트
    """
    print(f"🧪 테스트 로그인 시작: {user_credentials.username}")
    return {"message": "테스트 로그인 성공", "username": user_credentials.username}

@router.post("/login")
async def login_user(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    사용자 로그인을 처리합니다.
    
    Args:
        user_credentials: 로그인 자격 증명
        db: 데이터베이스 세션
        
    Returns:
        JSONResponse: 표준 성공 응답 (토큰과 사용자 정보)
        
    Raises:
        AuthenticationException: 인증 실패 시
    """
    start_time = time.time()
    print(f"🚀 로그인 시작: {user_credentials.username}")
    
    try:
        # 사용자 조회 (타임아웃 모니터링)
        print(f"📊 1단계: 사용자 조회 시작")
        user_query_start = time.time()
        user = get_user_by_username(db, user_credentials.username)
        query_time = time.time() - user_query_start
        print(f"📊 1단계 완료: 사용자 조회 {query_time:.3f}초")
        
        if query_time > 1.0:  # 1초 이상 걸리면 경고
            print(f"⚠️ 사용자 조회 느림: {query_time:.3f}초")
        
        if not user:
            print(f"❌ 사용자 없음: {user_credentials.username}")
            raise AuthenticationException(
                error_code=ErrorCode.INVALID_CREDENTIALS,
                message=f"존재하지 않는 사용자명: {user_credentials.username}",
                user_message="잘못된 사용자명 또는 비밀번호입니다."
            )
        
        print(f"✅ 사용자 발견: {user.username}, 해시: {user.hashed_password[:50]}...")
        
        # 비밀번호 확인 (타임아웃 모니터링)
        print(f"🔐 2단계: 비밀번호 검증 시작")
        verify_start = time.time()
        password_valid = verify_password(user_credentials.password, user.hashed_password)
        verify_time = time.time() - verify_start
        print(f"🔐 2단계 완료: 비밀번호 검증 {verify_time:.3f}초, 결과: {password_valid}")
        
        if verify_time > 1.0:  # 1초 이상 걸리면 경고
            print(f"⚠️ 비밀번호 검증 느림: {verify_time:.3f}초")
        
        if not password_valid:
            print(f"❌ 비밀번호 불일치: {user_credentials.username}")
            raise AuthenticationException(
                error_code=ErrorCode.INVALID_CREDENTIALS,
                message=f"잘못된 비밀번호: 사용자 {user_credentials.username}",
                user_message="잘못된 사용자명 또는 비밀번호입니다."
            )
        
        # 계정 활성화 확인
        print(f"🔍 3단계: 계정 활성화 확인")
        if not user.is_active:
            # 관리자 승인 대기 중인 경우 특별한 메시지
            if user.is_admin and user.admin_approved == False:
                print(f"⏳ 관리자 승인 대기: {user_credentials.username}")
                raise AuthenticationException(
                    error_code=ErrorCode.ADMIN_APPROVAL_REQUIRED,
                    message=f"관리자 승인 대기 중인 사용자: {user_credentials.username}",
                    user_message="관리자 승인 대기 중입니다. 슈퍼관리자에게 문의하세요."
                )
            else:
                print(f"❌ 비활성화된 계정: {user_credentials.username}")
                raise AuthenticationException(
                    error_code=ErrorCode.ACCOUNT_DISABLED,
                    message=f"비활성화된 계정: {user_credentials.username}",
                    user_message="비활성화된 계정입니다. 관리자에게 문의하세요."
                )
        
        print(f"✅ 3단계 완료: 계정 활성 상태")
        
        # JWT 토큰 생성
        print(f"🎫 4단계: JWT 토큰 생성 시작")
        token_start = time.time()
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        token_time = time.time() - token_start
        print(f"🎫 4단계 완료: JWT 토큰 생성 {token_time:.3f}초")
        
        total_time = time.time() - start_time
        print(f"✅ 로그인 완료: 총 {total_time:.3f}초 (쿼리: {query_time:.3f}s, 검증: {verify_time:.3f}s, 토큰: {token_time:.3f}s)")
        
        # 표준 성공 응답 반환
        return ResponseHelper.success(
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "name": user.name,
                    "is_admin": user.is_admin,
                    "is_super_admin": user.is_super_admin
                }
            },
            message="로그인이 성공적으로 완료되었습니다."
        )
        
    except AuthenticationException:
        total_time = time.time() - start_time
        print(f"🚫 로그인 인증 실패: {total_time:.3f}초")
        raise
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ 로그인 실패: {total_time:.3f}초, 에러: {str(e)}")
        raise AuthenticationException(
            error_code=ErrorCode.UNAUTHORIZED,
            message=f"로그인 중 예상치 못한 오류: {str(e)}",
            user_message="로그인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )

@router.get("/")
async def get_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db)
):
    """
    일반 사용자 목록 조회 (기본 정보만)
    
    Args:
        page: 페이지 번호 (1부터 시작)
        size: 페이지 크기
        db: 데이터베이스 세션
        
    Returns:
        JSONResponse: 페이지네이션된 사용자 목록 (기본 정보만)
    """
    try:
        # 활성 사용자만 조회
        query = db.query(User).filter(User.is_active == True)
        
        # 전체 개수 조회
        total = query.count()
        
        # 페이지네이션 적용
        skip = (page - 1) * size
        users = query.offset(skip).limit(size).all()
        
        # 기본 정보만 반환 (보안상 이유로 제한된 정보만)
        user_basic_info = [
            {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "is_admin": user.is_admin
            }
            for user in users
        ]
        
        return ResponseHelper.paginated(
            items=user_basic_info,
            page=page,
            size=size,
            total=total,
            message="사용자 목록을 성공적으로 조회했습니다."
        )
        
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"사용자 목록 조회 중 오류: {str(e)}",
            user_message="사용자 목록 조회 중 오류가 발생했습니다."
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    현재 로그인한 사용자의 프로필을 조회합니다.
    
    Args:
        current_user: 현재 인증된 사용자
        
    Returns:
        UserResponse: 현재 사용자 정보
    """
    try:
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"사용자 프로필 조회 중 오류: {str(e)}",
            user_message="사용자 프로필 조회 중 오류가 발생했습니다."
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    특정 사용자의 정보를 조회합니다.
    본인의 정보이거나 관리자 권한이 필요합니다.
    
    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        UserResponse: 사용자 정보
        
    Raises:
        AuthorizationException: 권한 부족 시
        DataException: 사용자를 찾을 수 없을 때
    """
    try:
        # 권한 확인: 본인의 정보이거나 관리자 권한 필요
        require_user_permission(user_id, current_user.id, current_user.is_admin)
        
        user = get_user(db, user_id)
        if not user:
            raise DataException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"사용자를 찾을 수 없습니다: ID {user_id}",
                user_message="요청하신 사용자를 찾을 수 없습니다."
            )
        
        return user
        
    except (AuthorizationException, DataException):
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"사용자 정보 조회 중 오류: {str(e)}",
            user_message="사용자 정보 조회 중 오류가 발생했습니다."
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    사용자 정보를 수정합니다.
    본인의 정보이거나 관리자 권한이 필요합니다.
    
    Args:
        user_id: 사용자 ID
        user_update: 수정할 사용자 데이터
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        UserResponse: 수정된 사용자 정보
        
    Raises:
        AuthorizationException: 권한 부족 시
        DataException: 사용자를 찾을 수 없을 때
        ValidationException: 이메일 중복 시
    """
    try:
        # 권한 확인: 본인의 정보이거나 관리자 권한 필요
        require_user_permission(user_id, current_user.id, current_user.is_admin)
        
        # 기존 사용자 존재 확인
        existing_user = get_user(db, user_id)
        if not existing_user:
            raise DataException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"수정할 사용자를 찾을 수 없습니다: ID {user_id}",
                user_message="수정할 사용자를 찾을 수 없습니다."
            )
        
        # 이메일 중복 확인 (변경하려는 경우)
        if user_update.email and user_update.email != existing_user.email:
            if get_user_by_email(db, user_update.email):
                raise ValidationException(
                    error_code=ErrorCode.DUPLICATE_VALUE,
                    message=f"중복된 이메일: {user_update.email}",
                    user_message="이미 사용중인 이메일 주소입니다.",
                    field="email"
                )
        
        # 사용자 정보 수정
        updated_user = update_user(db, user_id, user_update)
        if not updated_user:
            raise BusinessLogicException(
                error_code=ErrorCode.OPERATION_FAILED,
                message=f"사용자 정보 수정 실패: ID {user_id}",
                user_message="사용자 정보 수정에 실패했습니다."
            )
        
        return updated_user
        
    except (AuthorizationException, DataException, ValidationException, BusinessLogicException):
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"사용자 정보 수정 중 오류: {str(e)}",
            user_message="사용자 정보 수정 중 오류가 발생했습니다."
        )

@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    사용자를 삭제합니다.
    본인의 계정이거나 관리자 권한이 필요합니다.
    
    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        dict: 삭제 성공 메시지
        
    Raises:
        AuthorizationException: 권한 부족 시
        DataException: 사용자를 찾을 수 없을 때
        BusinessLogicException: 삭제 실패 시
    """
    try:
        # 권한 확인: 본인의 계정이거나 관리자 권한 필요
        require_user_permission(user_id, current_user.id, current_user.is_admin)
        
        # 사용자 존재 확인
        existing_user = get_user(db, user_id)
        if not existing_user:
            raise DataException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"삭제할 사용자를 찾을 수 없습니다: ID {user_id}",
                user_message="삭제할 사용자를 찾을 수 없습니다."
            )
        
        # 사용자 삭제
        success = delete_user(db, user_id)
        if not success:
            raise BusinessLogicException(
                error_code=ErrorCode.OPERATION_FAILED,
                message=f"사용자 삭제 실패: ID {user_id}",
                user_message="사용자 삭제에 실패했습니다."
            )
        
        return {"message": f"사용자 ID {user_id}가 성공적으로 삭제되었습니다."}
        
    except (AuthorizationException, DataException, BusinessLogicException):
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"사용자 삭제 중 오류: {str(e)}",
            user_message="사용자 삭제 중 오류가 발생했습니다."
        )

# ========== 관리자 전용 사용자 관리 엔드포인트 ==========

@router.get("/admin/users")
async def get_all_users_for_admin(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    search: str = Query(None, description="검색어 (이름, 이메일, 사용자명)"),
    apartment_number: str = Query(None, description="동/호수로 필터링"),
    is_admin: bool = Query(None, description="관리자 여부로 필터링"),
    is_active: bool = Query(None, description="활성화 상태로 필터링"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    관리자용 사용자 목록을 조회합니다.
    검색, 필터링, 페이지네이션 지원
    
    Args:
        page: 페이지 번호 (1부터 시작)
        size: 페이지 크기
        search: 검색어 (이름, 이메일, 사용자명)
        apartment_number: 동/호수로 필터링
        is_admin: 관리자 여부로 필터링
        is_active: 활성화 상태로 필터링
        db: 데이터베이스 세션
        current_user: 현재 관리자 사용자
        
    Returns:
        JSONResponse: 페이지네이션된 사용자 목록
    """
    try:
        query = db.query(User)
        
        # 검색 조건 적용
        if search:
            search_filter = or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # 아파트 호수 필터링
        if apartment_number:
            query = query.filter(User.apartment_number.ilike(f"%{apartment_number}%"))
        
        # 관리자 여부 필터링
        if is_admin is not None:
            query = query.filter(User.is_admin == is_admin)
        
        # 활성화 상태 필터링
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # 전체 개수 조회
        total = query.count()
        
        # 페이지네이션 적용
        skip = (page - 1) * size
        users = query.offset(skip).limit(size).all()
        
        # UserResponse로 변환
        user_responses = [UserResponse.from_orm(user) for user in users]
        
        # 페이지네이션 응답 반환
        return ResponseHelper.paginated(
            items=user_responses,
            page=page,
            size=size,
            total=total,
            message="사용자 목록을 성공적으로 조회했습니다."
        )
        
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"사용자 목록 조회 중 오류: {str(e)}",
            user_message="사용자 목록 조회 중 오류가 발생했습니다."
        )

@router.get("/admin/users/stats")
async def get_users_stats_for_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    관리자용 사용자 통계 조회
    
    Args:
        db: 데이터베이스 세션
        current_user: 현재 관리자 사용자
        
    Returns:
        JSONResponse: 표준 성공 응답 (사용자 통계 정보)
    """
    try:
        # 총 사용자 수
        total_users = db.query(User).count()
        
        # 활성 사용자 수
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # 관리자 수
        admin_users = db.query(User).filter(User.is_admin == True, User.admin_approved == True).count()
        
        # 승인 대기 관리자 수
        pending_admins = db.query(User).filter(
            User.is_admin == True, 
            User.admin_approved == False
        ).count()
        
        # 최근 30일 신규 가입자 수
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_users = db.query(User).filter(
            User.created_at >= thirty_days_ago
        ).count()
        
        stats_data = {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users,
            "pending_admins": pending_admins,
            "recent_users": recent_users,
            "stats_date": datetime.now().isoformat()
        }
        
        # 표준 성공 응답 반환
        return ResponseHelper.success(
            data=stats_data,
            message="사용자 통계를 성공적으로 조회했습니다."
        )
        
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"사용자 통계 조회 중 오류: {str(e)}",
            user_message="사용자 통계 조회 중 오류가 발생했습니다."
        )

@router.put("/admin/users/{user_id}/status")
async def toggle_user_status_for_admin(
    user_id: int,
    is_active: bool = Body(..., description="활성화 상태"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    관리자용 사용자 활성화 상태 변경
    
    Args:
        user_id: 사용자 ID
        is_active: 설정할 활성화 상태
        db: 데이터베이스 세션
        current_user: 현재 관리자 사용자
        
    Returns:
        dict: 변경 결과 메시지
        
    Raises:
        DataException: 사용자를 찾을 수 없을 때
        BusinessLogicException: 슈퍼관리자를 비활성화하려고 할 때
    """
    try:
        # 사용자 존재 확인
        user = get_user(db, user_id)
        if not user:
            raise DataException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"사용자를 찾을 수 없습니다: ID {user_id}",
                user_message="요청하신 사용자를 찾을 수 없습니다."
            )
        
        # 슈퍼관리자는 비활성화할 수 없음
        if user.is_super_admin and not is_active:
            raise BusinessLogicException(
                error_code=ErrorCode.FORBIDDEN,
                message="슈퍼관리자 계정은 비활성화할 수 없습니다.",
                user_message="슈퍼관리자 계정은 비활성화할 수 없습니다."
            )
        
        # 상태 변경
        user.is_active = is_active
        db.commit()
        db.refresh(user)
        
        status_text = "활성화" if is_active else "비활성화"
        return {
            "message": f"사용자 '{user.username}'이 성공적으로 {status_text}되었습니다.",
            "user_id": user_id,
            "is_active": is_active
        }
        
    except (DataException, BusinessLogicException):
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"사용자 상태 변경 중 오류: {str(e)}",
            user_message="사용자 상태 변경 중 오류가 발생했습니다."
        )

@router.delete("/admin/users/bulk")
async def bulk_delete_users_for_admin(
    user_ids: List[int] = Body(..., description="삭제할 사용자 ID 목록"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    관리자용 사용자 대량 삭제
    
    Args:
        user_ids: 삭제할 사용자 ID 목록
        db: 데이터베이스 세션
        current_user: 현재 관리자 사용자
        
    Returns:
        dict: 삭제 결과
        
    Raises:
        BusinessLogicException: 사용자 ID 목록이 비어있거나 삭제 실패 시
    """
    try:
        if not user_ids:
            raise BusinessLogicException(
                error_code=ErrorCode.BAD_REQUEST,
                message="삭제할 사용자를 선택해주세요.",
                user_message="삭제할 사용자를 선택해주세요."
            )
        
        # 슈퍼관리자 포함 여부 확인
        super_admin_ids = db.query(User.id).filter(
            User.id.in_(user_ids),
            User.is_super_admin == True
        ).all()
        
        if super_admin_ids:
            super_admin_id_list = [id[0] for id in super_admin_ids]
            raise BusinessLogicException(
                error_code=ErrorCode.FORBIDDEN,
                message=f"슈퍼관리자 계정은 삭제할 수 없습니다: {super_admin_id_list}",
                user_message="슈퍼관리자 계정은 삭제할 수 없습니다."
            )
        
        # 삭제할 사용자 조회
        users_to_delete = db.query(User).filter(User.id.in_(user_ids)).all()
        existing_ids = [user.id for user in users_to_delete]
        not_found_ids = [id for id in user_ids if id not in existing_ids]
        
        # 사용자 삭제 실행
        deleted_count = 0
        for user in users_to_delete:
            try:
                db.delete(user)
                deleted_count += 1
            except Exception as e:
                # 개별 삭제 실패는 로그로 기록하고 계속 진행
                print(f"사용자 {user.id} 삭제 실패: {e}")
        
        db.commit()
        
        result = {
            "message": f"{deleted_count}명의 사용자가 성공적으로 삭제되었습니다.",
            "deleted_count": deleted_count,
            "requested_count": len(user_ids),
            "success": True
        }
        
        if not_found_ids:
            result["warnings"] = f"다음 ID의 사용자를 찾을 수 없습니다: {not_found_ids}"
        
        return result
        
    except BusinessLogicException:
        raise
    except Exception as e:
        raise BusinessLogicException(
            error_code=ErrorCode.OPERATION_FAILED,
            message=f"대량 삭제 중 오류: {str(e)}",
            user_message="대량 삭제 중 오류가 발생했습니다."
        ) 