"""
사용자 관리 API 라우터
사용자 등록, 인증, 정보 관리 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin
from app.crud.user import (
    create_user,
    get_user,
    get_user_by_username,
    get_user_by_email,
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
                "is_admin": user.is_admin
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 삭제에 실패했습니다."
            )
        
        return {"message": f"사용자 {existing_user.username}이(가) 성공적으로 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 삭제 중 오류가 발생했습니다: {str(e)}"
        ) 