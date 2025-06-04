"""
사용자 관리 API 라우터
사용자 등록, 인증, 정보 관리 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import or_

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
from app.core.security import verify_password, create_access_token

# APIRouter 인스턴스 생성
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "사용자를 찾을 수 없습니다"}}
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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
        UserResponse: 생성된 사용자 정보
        
    Raises:
        HTTPException: 사용자명 또는 이메일 중복 시
    """
    try:
        # 중복 확인
        if get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용중인 사용자명입니다."
            )
        
        if get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일 주소입니다."
            )
        
        # 사용자 생성
        new_user = create_user(db, user_data)
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 등록 중 오류가 발생했습니다: {str(e)}"
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
        HTTPException: 사용자명 또는 이메일 중복 시
    """
    try:
        # 중복 확인
        if get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용중인 사용자명입니다."
            )
        
        if get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일 주소입니다."
            )
        
        # 관리자 계정 생성 (승인 대기 상태)
        new_admin = create_admin_user(db, user_data)
        return new_admin
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"관리자 등록 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/admin/pending", response_model=List[UserResponse])
async def get_pending_admins(
    db: Session = Depends(get_db)
):
    """
    승인 대기 중인 관리자 목록을 조회합니다. (슈퍼관리자 전용)
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        List[UserResponse]: 승인 대기 중인 관리자 목록
    """
    try:
        pending_admins = get_pending_admin_users(db)
        return pending_admins
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"승인 대기 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/admin/{user_id}/approve", response_model=UserResponse)
async def approve_admin(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    관리자 계정을 승인합니다. (슈퍼관리자 전용)
    
    Args:
        user_id: 승인할 관리자 ID
        db: 데이터베이스 세션
        
    Returns:
        UserResponse: 승인된 관리자 정보
        
    Raises:
        HTTPException: 승인 실패 시
    """
    try:
        approved_admin = approve_admin_user(db, user_id)
        if not approved_admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="승인할 수 있는 관리자 계정을 찾을 수 없습니다."
            )
        
        return approved_admin
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"관리자 승인 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/admin/{user_id}/reject")
async def reject_admin(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    관리자 계정을 거부합니다. (슈퍼관리자 전용)
    
    Args:
        user_id: 거부할 관리자 ID
        db: 데이터베이스 세션
        
    Returns:
        dict: 성공 메시지
        
    Raises:
        HTTPException: 거부 실패 시
    """
    try:
        success = reject_admin_user(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="거부할 수 있는 관리자 계정을 찾을 수 없습니다."
            )
        
        return {"message": "관리자 계정이 거부되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"관리자 거부 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/login")
async def login_user(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    사용자 로그인 및 JWT 토큰 발급
    
    Args:
        user_credentials: 로그인 정보
        db: 데이터베이스 세션
        
    Returns:
        dict: 액세스 토큰과 사용자 정보
        
    Raises:
        HTTPException: 인증 실패 시
    """
    try:
        # 사용자 조회
        user = get_user_by_username(db, user_credentials.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 사용자명 또는 비밀번호입니다."
            )
        
        # 비밀번호 확인
        if not verify_password(user_credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 사용자명 또는 비밀번호입니다."
            )
        
        # 비활성화된 계정 확인
        if not user.is_active:
            # 관리자 승인 대기 중인 경우 특별한 메시지
            if user.is_admin and user.admin_approved == False:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="관리자 승인 대기 중입니다. 슈퍼관리자에게 문의하세요."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="비활성화된 계정입니다. 관리자에게 문의하세요."
                )
        
        # JWT 토큰 생성
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        return {
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
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 정보를 조회합니다.
    
    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션
        
    Returns:
        UserResponse: 사용자 정보
        
    Raises:
        HTTPException: 사용자를 찾을 수 없을 때
    """
    try:
        user = get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {user_id}에 해당하는 사용자를 찾을 수 없습니다."
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    사용자 정보를 수정합니다.
    
    Args:
        user_id: 사용자 ID
        user_update: 수정할 사용자 데이터
        db: 데이터베이스 세션
        
    Returns:
        UserResponse: 수정된 사용자 정보
        
    Raises:
        HTTPException: 사용자를 찾을 수 없거나 수정 실패 시
    """
    try:
        # 기존 사용자 존재 확인
        existing_user = get_user(db, user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {user_id}에 해당하는 사용자를 찾을 수 없습니다."
            )
        
        # 이메일 중복 확인 (변경하려는 경우)
        if user_update.email and user_update.email != existing_user.email:
            if get_user_by_email(db, user_update.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 사용중인 이메일 주소입니다."
                )
        
        # 사용자 정보 수정
        updated_user = update_user(db, user_id, user_update)
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    사용자를 삭제합니다.
    
    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션
        
    Returns:
        dict: 삭제 성공 메시지
        
    Raises:
        HTTPException: 사용자를 찾을 수 없거나 삭제 실패 시
    """
    try:
        # 사용자 존재 확인
        existing_user = get_user(db, user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {user_id}에 해당하는 사용자를 찾을 수 없습니다."
            )
        
        # 사용자 삭제
        success = delete_user(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 사용자를 찾을 수 없습니다."
            )
        
        return {"message": f"사용자 ID {user_id}가 성공적으로 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 삭제 중 오류가 발생했습니다: {str(e)}"
        )

# ========== 관리자 전용 사용자 관리 엔드포인트 ==========

@router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users_for_admin(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(50, ge=1, le=100, description="한 번에 가져올 레코드 수"),
    search: str = Query(None, description="검색어 (이름, 이메일, 사용자명)"),
    apartment_number: str = Query(None, description="동/호수로 필터링"),
    is_admin: bool = Query(None, description="관리자 여부로 필터링"),
    is_active: bool = Query(None, description="활성화 상태로 필터링"),
    db: Session = Depends(get_db)
):
    """
    관리자용 전체 사용자 목록 조회 (검색 및 필터링 지원)
    
    Args:
        skip: 건너뛸 레코드 수
        limit: 한 번에 가져올 레코드 수
        search: 검색어
        apartment_number: 동/호수 필터
        is_admin: 관리자 여부 필터
        is_active: 활성화 상태 필터
        db: 데이터베이스 세션
        
    Returns:
        List[UserResponse]: 사용자 목록
    """
    try:
        users_query = db.query(User)
        
        # 검색어 필터링
        if search:
            search_filter = f"%{search}%"
            users_query = users_query.filter(
                or_(
                    User.name.ilike(search_filter),
                    User.username.ilike(search_filter),
                    User.email.ilike(search_filter)
                )
            )
        
        # 동/호수 필터링
        if apartment_number:
            users_query = users_query.filter(User.apartment_number.ilike(f"%{apartment_number}%"))
        
        # 관리자 여부 필터링
        if is_admin is not None:
            users_query = users_query.filter(User.is_admin == is_admin)
        
        # 활성화 상태 필터링
        if is_active is not None:
            users_query = users_query.filter(User.is_active == is_active)
        
        # 결과 조회
        users = users_query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/admin/users/stats")
async def get_users_stats_for_admin(db: Session = Depends(get_db)):
    """
    관리자용 사용자 통계 조회
    
    Returns:
        dict: 사용자 통계 정보
    """
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        pending_admins = db.query(User).filter(
            User.is_admin == True, 
            User.admin_approved == False
        ).count()
        
        # 최근 30일 가입자 수
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_users = db.query(User).filter(User.created_at >= thirty_days_ago).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users,
            "pending_admins": pending_admins,
            "recent_users": recent_users
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/admin/users/{user_id}/status")
async def toggle_user_status_for_admin(
    user_id: int,
    is_active: bool = Body(..., description="활성화 상태"),
    db: Session = Depends(get_db)
):
    """
    관리자용 사용자 활성화/비활성화 토글
    
    Args:
        user_id: 사용자 ID
        is_active: 설정할 활성화 상태
        db: 데이터베이스 세션
        
    Returns:
        dict: 상태 변경 결과
    """
    try:
        user = get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 슈퍼관리자는 비활성화할 수 없음
        if user.is_super_admin and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="슈퍼관리자 계정은 비활성화할 수 없습니다."
            )
        
        # 상태 업데이트
        user.is_active = is_active
        db.commit()
        db.refresh(user)
        
        status_text = "활성화" if is_active else "비활성화"
        return {
            "message": f"사용자 '{user.name}'이 {status_text}되었습니다.",
            "user_id": user_id,
            "is_active": is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 상태 변경 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/admin/users/bulk")
async def bulk_delete_users_for_admin(
    user_ids: List[int] = Body(..., description="삭제할 사용자 ID 목록"),
    db: Session = Depends(get_db)
):
    """
    관리자용 사용자 대량 삭제
    
    Args:
        user_ids: 삭제할 사용자 ID 목록
        db: 데이터베이스 세션
        
    Returns:
        dict: 삭제 결과
    """
    try:
        if not user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="삭제할 사용자를 선택해주세요."
            )
        
        deleted_count = 0
        failed_users = []
        
        for user_id in user_ids:
            try:
                user = get_user(db, user_id)
                if not user:
                    failed_users.append(f"ID {user_id}: 사용자를 찾을 수 없음")
                    continue
                
                # 슈퍼관리자는 삭제할 수 없음
                if user.is_super_admin:
                    failed_users.append(f"ID {user_id}: 슈퍼관리자는 삭제할 수 없음")
                    continue
                
                # 사용자 삭제
                success = delete_user(db, user_id)
                if success:
                    deleted_count += 1
                else:
                    failed_users.append(f"ID {user_id}: 삭제 실패")
                    
            except Exception as e:
                failed_users.append(f"ID {user_id}: {str(e)}")
        
        result = {
            "message": f"{deleted_count}명의 사용자가 삭제되었습니다.",
            "deleted_count": deleted_count,
            "total_requested": len(user_ids)
        }
        
        if failed_users:
            result["failed_users"] = failed_users
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대량 삭제 중 오류가 발생했습니다: {str(e)}"
        ) 