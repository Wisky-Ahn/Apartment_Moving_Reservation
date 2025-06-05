"""
예약 관리 API 라우터
아파트 이사예약의 생성, 조회, 수정, 삭제 및 승인/거부 기능을 제공합니다.
"""
from datetime import datetime, date, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.db.database import get_db
from app.models.reservation import Reservation
from app.schemas.reservation import (
    ReservationCreate, 
    ReservationUpdate, 
    ReservationResponse,
    ReservationListResponse,
    ReservationStatusUpdate
)
from app.crud.reservation import (
    create_reservation,
    get_reservation,
    get_reservations,
    update_reservation,
    delete_reservation,
    approve_reservation,
    reject_reservation,
    check_time_conflict,
    check_apartment_reservation_limit
)
from app.core.security import get_current_active_user
from app.models.user import User

# APIRouter 인스턴스 생성
router = APIRouter(
    prefix="/api/reservations",
    tags=["reservations"],
    responses={404: {"description": "예약을 찾을 수 없습니다"}}
)


@router.get("/check-apartment-limit")
async def check_apartment_reservation_limit_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    현재 사용자의 호수에서 기존 예약이 있는지 확인합니다.
    
    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        dict: 호수 예약 제한 상태
    """
    try:
        has_existing, existing_reservations = check_apartment_reservation_limit(db, current_user.id)
        
        return {
            "has_existing_reservation": has_existing,
            "existing_reservations": existing_reservations,
            "apartment_number": current_user.apartment_number,
            "message": f"호수 {current_user.apartment_number}에서 {len(existing_reservations)}개의 활성 예약이 있습니다." if has_existing else "새로운 예약을 생성할 수 있습니다."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"호수 예약 제한 검사 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/conflicts/check")
async def check_reservation_conflicts(
    reservation_date: date = Query(..., description="예약 날짜"),
    start_time: time = Query(..., description="시작 시간"),
    end_time: time = Query(..., description="종료 시간"),
    equipment_type: str = Query(..., description="장비 유형 (elevator/parking/other)"),
    exclude_reservation_id: Optional[int] = Query(None, description="제외할 예약 ID"),
    db: Session = Depends(get_db)
):
    """
    특정 시간대의 예약 충돌을 확인합니다.
    
    Args:
        reservation_date: 예약 날짜
        start_time: 시작 시간
        end_time: 종료 시간
        equipment_type: 장비 유형 (elevator/parking/other)
        exclude_reservation_id: 제외할 예약 ID (수정 시 사용)
        db: 데이터베이스 세션
        
    Returns:
        dict: 충돌 여부와 관련 정보
    """
    try:
        # datetime 객체 생성
        start_datetime = datetime.combine(reservation_date, start_time)
        end_datetime = datetime.combine(reservation_date, end_time)
        
        # 임시 예약 데이터 생성 (새 스키마 형식 사용)
        temp_reservation = ReservationCreate(
            reservation_type=equipment_type,  # equipment_type -> reservation_type
            start_time=start_datetime,        # datetime 형식
            end_time=end_datetime,           # datetime 형식
            description="Conflict check only"
        )
        
        # 충돌 확인
        has_conflict = check_time_conflict(db, temp_reservation, exclude_reservation_id)
        
        return {
            "has_conflict": has_conflict,
            "conflicting_reservations": [],  # 필요시 충돌하는 예약 목록 반환
            "message": "해당 시간대에 예약이 가능합니다." if not has_conflict else "해당 시간대에 이미 예약이 있습니다.",
            "checked_date": reservation_date,
            "checked_time_range": f"{start_time} - {end_time}",
            "equipment_type": equipment_type
        }
        
    except Exception as e:
        logger.error(f"예약 충돌 확인 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예약 충돌 확인 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/", response_model=ReservationListResponse)
async def get_all_reservations(
    skip: int = Query(0, ge=0, description="건너뛸 예약 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 최대 예약 수"),
    status_filter: Optional[str] = Query(None, description="상태별 필터링"),
    user_id: Optional[int] = Query(None, description="사용자별 필터링"),
    date_from: Optional[date] = Query(None, description="시작 날짜"),
    date_to: Optional[date] = Query(None, description="종료 날짜"),
    db: Session = Depends(get_db)
):
    """
    예약 목록을 조회합니다.
    
    Args:
        skip: 건너뛸 예약 수
        limit: 가져올 최대 예약 수  
        status_filter: 상태별 필터 (pending, approved, rejected, completed, cancelled)
        user_id: 특정 사용자의 예약만 조회
        date_from: 시작 날짜
        date_to: 종료 날짜
        db: 데이터베이스 세션
        
    Returns:
        ReservationListResponse: 예약 목록과 총 개수
    """
    try:
        reservations, total = get_reservations(
            db=db,
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to
        )
        
        # 페이지 정보 계산
        page = (skip // limit) + 1
        has_next = skip + limit < total
        has_prev = skip > 0
        
        return ReservationListResponse(
            reservations=reservations,
            total=total,
            page=page,
            size=limit,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예약 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/my", response_model=ReservationListResponse)
async def get_my_reservations(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    status_filter: Optional[str] = Query(None, description="상태별 필터링"),
    date_from: Optional[date] = Query(None, description="시작 날짜"),
    date_to: Optional[date] = Query(None, description="종료 날짜"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    현재 로그인한 사용자의 예약 목록을 조회합니다.
    
    Args:
        page: 페이지 번호 (1부터 시작)
        size: 페이지 크기
        status_filter: 상태별 필터 (pending, approved, rejected, completed, cancelled)
        date_from: 시작 날짜
        date_to: 종료 날짜
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        ReservationListResponse: 예약 목록과 총 개수
    """
    try:
        # skip 계산
        skip = (page - 1) * size
        
        # 현재 사용자의 예약만 조회
        reservations, total = get_reservations(
            db=db,
            skip=skip,
            limit=size,
            status_filter=status_filter,
            user_id=current_user.id,  # 현재 사용자 ID로 필터링
            date_from=date_from,
            date_to=date_to
        )
        
        # 페이지 정보 계산
        has_next = skip + size < total
        has_prev = page > 1
        
        return ReservationListResponse(
            reservations=reservations,
            total=total,
            page=page,
            size=size,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"내 예약 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_reservation(
    reservation_data: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    새로운 이사예약을 생성합니다.
    
    Args:
        reservation_data: 예약 생성 데이터
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        
    Returns:
        ReservationResponse: 생성된 예약 정보
        
    Raises:
        HTTPException: 예약 생성 실패 시
    """
    try:
        # 호수당 예약 제한 검사
        has_existing, existing_reservations = check_apartment_reservation_limit(db, current_user.id)
        if has_existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"호수당 하나의 예약만 가능합니다. 기존 예약을 완료하거나 취소한 후 새로운 예약을 생성해주세요. (기존 예약: {len(existing_reservations)}개)"
            )
        
        # 사용자 ID 자동 설정
        reservation_data.user_id = current_user.id
        
        # 시간 충돌 체크
        if check_time_conflict(db, reservation_data):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="선택하신 시간대에 이미 다른 예약이 있습니다. 다른 시간을 선택해주세요."
            )
        
        # 예약 생성
        new_reservation = create_reservation(db, reservation_data)
        return new_reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예약 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation_by_id(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 예약의 상세 정보를 조회합니다.
    
    Args:
        reservation_id: 예약 ID
        db: 데이터베이스 세션
        
    Returns:
        ReservationResponse: 예약 상세 정보
        
    Raises:
        HTTPException: 예약을 찾을 수 없을 때
    """
    try:
        reservation = get_reservation(db, reservation_id)
        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {reservation_id}에 해당하는 예약을 찾을 수 없습니다."
            )
        
        return reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예약 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation_by_id(
    reservation_id: int,
    reservation_update: ReservationUpdate,
    db: Session = Depends(get_db)
):
    """
    기존 예약 정보를 수정합니다.
    
    Args:
        reservation_id: 예약 ID
        reservation_update: 수정할 예약 데이터
        db: 데이터베이스 세션
        
    Returns:
        ReservationResponse: 수정된 예약 정보
        
    Raises:
        HTTPException: 예약을 찾을 수 없거나 수정 실패 시
    """
    try:
        # 기존 예약 존재 확인
        existing_reservation = get_reservation(db, reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {reservation_id}에 해당하는 예약을 찾을 수 없습니다."
            )
        
        # 시간 변경 시 충돌 체크
        if reservation_update.reservation_date or reservation_update.start_time or reservation_update.end_time:
            # 임시 데이터로 충돌 체크
            temp_data = ReservationCreate(
                user_id=existing_reservation.user_id,
                reservation_date=reservation_update.reservation_date or existing_reservation.reservation_date,
                start_time=reservation_update.start_time or existing_reservation.start_time,
                end_time=reservation_update.end_time or existing_reservation.end_time,
                equipment_type=reservation_update.equipment_type or existing_reservation.equipment_type,
                purpose=reservation_update.purpose or existing_reservation.purpose,
                contact_phone=reservation_update.contact_phone or existing_reservation.contact_phone,
                notes=reservation_update.notes or existing_reservation.notes
            )
            
            if check_time_conflict(db, temp_data, exclude_id=reservation_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="변경하려는 시간대에 이미 다른 예약이 있습니다."
                )
        
        # 예약 수정
        updated_reservation = update_reservation(db, reservation_id, reservation_update)
        return updated_reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예약 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{reservation_id}")
async def delete_reservation_by_id(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """
    예약을 삭제합니다.
    
    Args:
        reservation_id: 삭제할 예약 ID
        db: 데이터베이스 세션
        
    Returns:
        dict: 삭제 완료 메시지
        
    Raises:
        HTTPException: 예약을 찾을 수 없거나 삭제 실패 시
    """
    try:
        # 예약 존재 확인
        existing_reservation = get_reservation(db, reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {reservation_id}에 해당하는 예약을 찾을 수 없습니다."
            )
        
        # 예약 삭제
        success = delete_reservation(db, reservation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="예약 삭제에 실패했습니다."
            )
        
        return {
            "message": f"예약 ID {reservation_id}가 성공적으로 삭제되었습니다.",
            "deleted_id": reservation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예약 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/{reservation_id}/approve", response_model=ReservationResponse)
async def approve_reservation_by_id(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """
    예약을 승인합니다. (관리자 전용)
    
    Args:
        reservation_id: 승인할 예약 ID
        db: 데이터베이스 세션
        
    Returns:
        ReservationResponse: 승인된 예약 정보
        
    Raises:
        HTTPException: 예약을 찾을 수 없거나 승인 실패 시
    """
    try:
        # 예약 존재 확인
        existing_reservation = get_reservation(db, reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {reservation_id}에 해당하는 예약을 찾을 수 없습니다."
            )
        
        # 예약 승인
        approved_reservation = approve_reservation(db, reservation_id)
        if not approved_reservation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="예약 승인에 실패했습니다."
            )
        
        return approved_reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예약 승인 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/{reservation_id}/reject", response_model=ReservationResponse)
async def reject_reservation_by_id(
    reservation_id: int,
    status_update: ReservationStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    예약을 거부합니다. (관리자 전용)
    
    Args:
        reservation_id: 거부할 예약 ID
        status_update: 거부 사유 등 상태 업데이트 정보
        db: 데이터베이스 세션
        
    Returns:
        ReservationResponse: 거부된 예약 정보
        
    Raises:
        HTTPException: 예약을 찾을 수 없거나 거부 실패 시
    """
    try:
        # 예약 존재 확인
        existing_reservation = get_reservation(db, reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {reservation_id}에 해당하는 예약을 찾을 수 없습니다."
            )
        
        # 예약 거부
        rejected_reservation = reject_reservation(db, reservation_id, status_update.reason)
        if not rejected_reservation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="예약 거부에 실패했습니다."
            )
        
        return rejected_reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예약 거부 중 오류가 발생했습니다: {str(e)}"
        ) 