"""
예약 관리 CRUD 함수들
데이터베이스와의 예약 관련 작업을 처리합니다.
"""
from datetime import datetime, date, time
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreate, ReservationUpdate


def create_reservation(db: Session, reservation_data: ReservationCreate) -> Reservation:
    """
    새로운 예약을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        reservation_data: 예약 생성 데이터
        
    Returns:
        Reservation: 생성된 예약 객체
    """
    db_reservation = Reservation(
        user_id=reservation_data.user_id,
        reservation_date=reservation_data.reservation_date,
        start_time=reservation_data.start_time,
        end_time=reservation_data.end_time,
        equipment_type=reservation_data.equipment_type,
        purpose=reservation_data.purpose,
        contact_phone=reservation_data.contact_phone,
        notes=reservation_data.notes,
        status="pending",  # 기본 상태는 대기중
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def get_reservation(db: Session, reservation_id: int) -> Optional[Reservation]:
    """
    특정 예약을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        reservation_id: 예약 ID
        
    Returns:
        Optional[Reservation]: 예약 객체 또는 None
    """
    return db.query(Reservation).filter(Reservation.id == reservation_id).first()


def get_reservations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    user_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Tuple[List[Reservation], int]:
    """
    예약 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        skip: 건너뛸 예약 수
        limit: 가져올 최대 예약 수
        status_filter: 상태별 필터
        user_id: 사용자별 필터
        date_from: 시작 날짜
        date_to: 종료 날짜
        
    Returns:
        Tuple[List[Reservation], int]: 예약 목록과 총 개수
    """
    query = db.query(Reservation)
    
    # 필터 적용
    if status_filter:
        query = query.filter(Reservation.status == status_filter)
    
    if user_id:
        query = query.filter(Reservation.user_id == user_id)
    
    if date_from:
        query = query.filter(Reservation.reservation_date >= date_from)
    
    if date_to:
        query = query.filter(Reservation.reservation_date <= date_to)
    
    # 총 개수 계산
    total = query.count()
    
    # 페이지네이션 적용
    reservations = query.order_by(Reservation.reservation_date.desc(), 
                                Reservation.start_time.desc()).offset(skip).limit(limit).all()
    
    return reservations, total


def update_reservation(
    db: Session, 
    reservation_id: int, 
    reservation_update: ReservationUpdate
) -> Optional[Reservation]:
    """
    예약 정보를 수정합니다.
    
    Args:
        db: 데이터베이스 세션
        reservation_id: 예약 ID
        reservation_update: 수정할 데이터
        
    Returns:
        Optional[Reservation]: 수정된 예약 객체 또는 None
    """
    db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    
    if not db_reservation:
        return None
    
    # 수정할 필드들 업데이트
    update_data = reservation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reservation, field, value)
    
    # 수정 시간 업데이트
    db_reservation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def delete_reservation(db: Session, reservation_id: int) -> bool:
    """
    예약을 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        reservation_id: 예약 ID
        
    Returns:
        bool: 삭제 성공 여부
    """
    db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    
    if not db_reservation:
        return False
    
    db.delete(db_reservation)
    db.commit()
    return True


def approve_reservation(db: Session, reservation_id: int) -> Optional[Reservation]:
    """
    예약을 승인합니다.
    
    Args:
        db: 데이터베이스 세션
        reservation_id: 예약 ID
        
    Returns:
        Optional[Reservation]: 승인된 예약 객체 또는 None
    """
    db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    
    if not db_reservation:
        return None
    
    db_reservation.status = "approved"
    db_reservation.approved_at = datetime.utcnow()
    db_reservation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def reject_reservation(db: Session, reservation_id: int, reason: str = None) -> Optional[Reservation]:
    """
    예약을 거부합니다.
    
    Args:
        db: 데이터베이스 세션
        reservation_id: 예약 ID
        reason: 거부 사유
        
    Returns:
        Optional[Reservation]: 거부된 예약 객체 또는 None
    """
    db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    
    if not db_reservation:
        return None
    
    db_reservation.status = "rejected"
    if reason:
        db_reservation.rejection_reason = reason
    db_reservation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def check_time_conflict(
    db: Session, 
    reservation_data: ReservationCreate, 
    exclude_id: Optional[int] = None
) -> bool:
    """
    예약 시간 충돌을 확인합니다.
    
    Args:
        db: 데이터베이스 세션
        reservation_data: 예약 데이터
        exclude_id: 제외할 예약 ID (수정 시 사용)
        
    Returns:
        bool: 충돌 여부 (True: 충돌 있음, False: 충돌 없음)
    """
    query = db.query(Reservation).filter(
        and_(
            Reservation.reservation_date == reservation_data.reservation_date,
            Reservation.equipment_type == reservation_data.equipment_type,
            Reservation.status.in_(["pending", "approved"]),  # 대기중이거나 승인된 예약만 체크
            or_(
                # 새 예약의 시작 시간이 기존 예약 시간 범위 내에 있는 경우
                and_(
                    Reservation.start_time <= reservation_data.start_time,
                    Reservation.end_time > reservation_data.start_time
                ),
                # 새 예약의 종료 시간이 기존 예약 시간 범위 내에 있는 경우
                and_(
                    Reservation.start_time < reservation_data.end_time,
                    Reservation.end_time >= reservation_data.end_time
                ),
                # 새 예약이 기존 예약을 완전히 포함하는 경우
                and_(
                    Reservation.start_time >= reservation_data.start_time,
                    Reservation.end_time <= reservation_data.end_time
                )
            )
        )
    )
    
    # 수정 시 자기 자신은 제외
    if exclude_id:
        query = query.filter(Reservation.id != exclude_id)
    
    conflicting_reservation = query.first()
    return conflicting_reservation is not None


def get_reservations_by_date_range(
    db: Session,
    start_date: date,
    end_date: date,
    equipment_type: Optional[str] = None
) -> List[Reservation]:
    """
    특정 날짜 범위의 예약을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        start_date: 시작 날짜
        end_date: 종료 날짜
        equipment_type: 장비 유형 필터
        
    Returns:
        List[Reservation]: 예약 목록
    """
    query = db.query(Reservation).filter(
        and_(
            Reservation.reservation_date >= start_date,
            Reservation.reservation_date <= end_date
        )
    )
    
    if equipment_type:
        query = query.filter(Reservation.equipment_type == equipment_type)
    
    return query.order_by(Reservation.reservation_date, Reservation.start_time).all()


def get_user_reservations(
    db: Session,
    user_id: int,
    status_filter: Optional[str] = None
) -> List[Reservation]:
    """
    특정 사용자의 예약을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        status_filter: 상태 필터
        
    Returns:
        List[Reservation]: 사용자의 예약 목록
    """
    query = db.query(Reservation).filter(Reservation.user_id == user_id)
    
    if status_filter:
        query = query.filter(Reservation.status == status_filter)
    
    return query.order_by(Reservation.reservation_date.desc()).all() 