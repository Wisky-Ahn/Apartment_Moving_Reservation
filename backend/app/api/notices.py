"""
공지사항 관리 API 라우터
공지사항의 생성, 조회, 수정, 삭제 및 필터링 기능을 제공합니다.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.notice import Notice
from app.models.user import User
from app.schemas.notice import (
    NoticeCreate,
    NoticeUpdate,
    NoticeResponse,
    NoticeListResponse,
    NoticeStats
)
from app.crud.notice import (
    create_notice,
    get_notice,
    get_notices,
    update_notice,
    delete_notice,
    increment_view_count,
    get_notice_stats
)
from app.core.security import get_current_admin_user

# APIRouter 인스턴스 생성
router = APIRouter(
    prefix="/api/notices",
    tags=["notices"],
    responses={404: {"description": "공지사항을 찾을 수 없습니다"}}
)


@router.post("/", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED)
async def create_new_notice(
    notice_data: NoticeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    새로운 공지사항을 작성합니다. (관리자 전용)
    
    Args:
        notice_data: 공지사항 생성 데이터
        db: 데이터베이스 세션
        current_user: 현재 인증된 관리자 사용자
        
    Returns:
        NoticeResponse: 생성된 공지사항 정보
        
    Raises:
        HTTPException: 공지사항 생성 실패 시
    """
    try:
        new_notice = create_notice(db, notice_data, current_user.id)
        return new_notice
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공지사항 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/", response_model=NoticeListResponse)
async def get_all_notices(
    skip: int = Query(0, ge=0, description="건너뛸 공지사항 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 최대 공지사항 수"),
    notice_type: Optional[str] = Query(None, description="공지사항 유형별 필터링"),
    is_important: Optional[bool] = Query(None, description="중요 공지만 조회"),
    is_pinned: Optional[bool] = Query(None, description="고정 공지만 조회"),
    is_active: Optional[bool] = Query(True, description="활성화된 공지만 조회"),
    search: Optional[str] = Query(None, description="제목/내용 검색"),
    db: Session = Depends(get_db)
):
    """
    공지사항 목록을 조회합니다.
    
    Args:
        skip: 건너뛸 공지사항 수
        limit: 가져올 최대 공지사항 수
        notice_type: 공지사항 유형 필터 (general, important, maintenance, event)
        is_important: 중요 공지만 조회
        is_pinned: 고정 공지만 조회
        is_active: 활성화된 공지만 조회
        search: 제목/내용 검색어
        db: 데이터베이스 세션
        
    Returns:
        NoticeListResponse: 공지사항 목록과 총 개수
    """
    try:
        notices, total = get_notices(
            db=db,
            skip=skip,
            limit=limit,
            notice_type=notice_type,
            is_important=is_important,
            is_pinned=is_pinned,
            is_active=is_active,
            search=search
        )
        
        return NoticeListResponse(
            notices=notices,
            total=total,
            page=skip // limit + 1,
            per_page=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공지사항 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/pinned", response_model=List[NoticeResponse])
async def get_pinned_notices(
    db: Session = Depends(get_db)
):
    """
    상단 고정 공지사항만 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        List[NoticeResponse]: 고정된 공지사항 목록
    """
    try:
        notices, _ = get_notices(
            db=db,
            skip=0,
            limit=10,  # 고정 공지는 최대 10개
            is_pinned=True,
            is_active=True
        )
        
        return notices
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"고정 공지사항 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/important", response_model=List[NoticeResponse])
async def get_important_notices(
    limit: int = Query(5, ge=1, le=20, description="가져올 중요 공지 수"),
    db: Session = Depends(get_db)
):
    """
    중요 공지사항만 조회합니다.
    
    Args:
        limit: 가져올 중요 공지 수
        db: 데이터베이스 세션
        
    Returns:
        List[NoticeResponse]: 중요 공지사항 목록
    """
    try:
        notices, _ = get_notices(
            db=db,
            skip=0,
            limit=limit,
            is_important=True,
            is_active=True
        )
        
        return notices
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"중요 공지사항 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/stats", response_model=NoticeStats)
async def get_notices_statistics(
    db: Session = Depends(get_db)
):
    """
    공지사항 통계를 조회합니다. (관리자 전용)
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        NoticeStats: 공지사항 통계 정보
    """
    try:
        stats = get_notice_stats(db)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공지사항 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{notice_id}", response_model=NoticeResponse)
async def get_notice_by_id(
    notice_id: int,
    increment_views: bool = Query(True, description="조회수 증가 여부"),
    db: Session = Depends(get_db)
):
    """
    특정 공지사항의 상세 정보를 조회합니다.
    
    Args:
        notice_id: 공지사항 ID
        increment_views: 조회수 증가 여부
        db: 데이터베이스 세션
        
    Returns:
        NoticeResponse: 공지사항 상세 정보
        
    Raises:
        HTTPException: 공지사항을 찾을 수 없을 때
    """
    try:
        notice = get_notice(db, notice_id)
        if not notice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {notice_id}에 해당하는 공지사항을 찾을 수 없습니다."
            )
        
        # 조회수 증가
        if increment_views:
            increment_view_count(db, notice_id)
            # 조회수가 증가된 공지사항을 다시 조회
            notice = get_notice(db, notice_id)
        
        return notice
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공지사항 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{notice_id}", response_model=NoticeResponse)
async def update_notice_by_id(
    notice_id: int,
    notice_update: NoticeUpdate,
    db: Session = Depends(get_db)
):
    """
    기존 공지사항을 수정합니다. (관리자 전용)
    
    Args:
        notice_id: 공지사항 ID
        notice_update: 수정할 공지사항 데이터
        db: 데이터베이스 세션
        
    Returns:
        NoticeResponse: 수정된 공지사항 정보
        
    Raises:
        HTTPException: 공지사항을 찾을 수 없거나 수정 실패 시
    """
    try:
        # 기존 공지사항 존재 확인
        existing_notice = get_notice(db, notice_id)
        if not existing_notice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {notice_id}에 해당하는 공지사항을 찾을 수 없습니다."
            )
        
        # 공지사항 수정
        updated_notice = update_notice(db, notice_id, notice_update)
        return updated_notice
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공지사항 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{notice_id}")
async def delete_notice_by_id(
    notice_id: int,
    db: Session = Depends(get_db)
):
    """
    공지사항을 삭제합니다. (관리자 전용)
    
    Args:
        notice_id: 삭제할 공지사항 ID
        db: 데이터베이스 세션
        
    Returns:
        dict: 삭제 완료 메시지
        
    Raises:
        HTTPException: 공지사항을 찾을 수 없거나 삭제 실패 시
    """
    try:
        # 공지사항 존재 확인
        existing_notice = get_notice(db, notice_id)
        if not existing_notice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {notice_id}에 해당하는 공지사항을 찾을 수 없습니다."
            )
        
        # 공지사항 삭제
        success = delete_notice(db, notice_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="공지사항 삭제에 실패했습니다."
            )
        
        return {
            "message": f"공지사항 ID {notice_id}가 성공적으로 삭제되었습니다.",
            "deleted_id": notice_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공지사항 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/{notice_id}/toggle-pin")
async def toggle_notice_pin(
    notice_id: int,
    db: Session = Depends(get_db)
):
    """
    공지사항의 고정 상태를 토글합니다. (관리자 전용)
    
    Args:
        notice_id: 공지사항 ID
        db: 데이터베이스 세션
        
    Returns:
        dict: 변경된 고정 상태 정보
    """
    try:
        notice = get_notice(db, notice_id)
        if not notice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {notice_id}에 해당하는 공지사항을 찾을 수 없습니다."
            )
        
        # 고정 상태 토글
        new_pin_status = not notice.is_pinned
        notice_update = NoticeUpdate(is_pinned=new_pin_status)
        updated_notice = update_notice(db, notice_id, notice_update)
        
        return {
            "message": f"공지사항 고정 상태가 {'설정' if new_pin_status else '해제'}되었습니다.",
            "notice_id": notice_id,
            "is_pinned": new_pin_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공지사항 고정 상태 변경 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/{notice_id}/toggle-active")
async def toggle_notice_active(
    notice_id: int,
    db: Session = Depends(get_db)
):
    """
    공지사항의 활성화 상태를 토글합니다. (관리자 전용)
    
    Args:
        notice_id: 공지사항 ID
        db: 데이터베이스 세션
        
    Returns:
        dict: 변경된 활성화 상태 정보
    """
    try:
        notice = get_notice(db, notice_id)
        if not notice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {notice_id}에 해당하는 공지사항을 찾을 수 없습니다."
            )
        
        # 활성화 상태 토글
        new_active_status = not notice.is_active
        notice_update = NoticeUpdate(is_active=new_active_status)
        updated_notice = update_notice(db, notice_id, notice_update)
        
        return {
            "message": f"공지사항이 {'활성화' if new_active_status else '비활성화'}되었습니다.",
            "notice_id": notice_id,
            "is_active": new_active_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공지사항 활성화 상태 변경 중 오류가 발생했습니다: {str(e)}"
        ) 