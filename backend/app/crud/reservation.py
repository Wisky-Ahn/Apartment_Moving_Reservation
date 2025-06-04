"""
예약 CRUD 연산
데이터베이스 예약 관련 생성, 조회, 수정, 삭제 작업
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, Tuple, List
from datetime import date, datetime
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.reservation import ReservationCreate, ReservationUpdate


def create_reservation(db: Session, reservation_data: ReservationCreate) -> Reservation:
    """
    새로운 예약 생성
    """
    db_reservation = Reservation(**reservation_data.dict())
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def get_reservation(db: Session, reservation_id: int) -> Optional[Reservation]:
    """
    ID로 예약 조회
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
    예약 목록 조회 (필터링 포함)
    """
    query = db.query(Reservation)
    
    # 필터 적용
    if status_filter:
        query = query.filter(Reservation.status == status_filter)
    if user_id:
        query = query.filter(Reservation.user_id == user_id)
    if date_from:
        query = query.filter(func.date(Reservation.start_time) >= date_from)
    if date_to:
        query = query.filter(func.date(Reservation.start_time) <= date_to)
    
    # 총 개수 계산
    total = query.count()
    
    # 페이지네이션 적용
    reservations = query.order_by(Reservation.created_at.desc()).offset(skip).limit(limit).all()
    
    return reservations, total


def update_reservation(db: Session, reservation_id: int, reservation_update: ReservationUpdate) -> Optional[Reservation]:
    """
    예약 정보 수정
    """
    db_reservation = get_reservation(db, reservation_id)
    if not db_reservation:
        return None
    
    update_data = reservation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reservation, field, value)
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def delete_reservation(db: Session, reservation_id: int) -> bool:
    """
    예약 삭제
    """
    db_reservation = get_reservation(db, reservation_id)
    if not db_reservation:
        return False
    
    db.delete(db_reservation)
    db.commit()
    return True


def approve_reservation(db: Session, reservation_id: int) -> Optional[Reservation]:
    """
    예약 승인
    """
    db_reservation = get_reservation(db, reservation_id)
    if not db_reservation:
        return None
    
    db_reservation.status = ReservationStatus.APPROVED
    db_reservation.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def reject_reservation(db: Session, reservation_id: int, admin_comment: Optional[str] = None) -> Optional[Reservation]:
    """
    예약 거부
    """
    db_reservation = get_reservation(db, reservation_id)
    if not db_reservation:
        return None
    
    db_reservation.status = ReservationStatus.REJECTED
    if admin_comment:
        db_reservation.admin_comment = admin_comment
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def check_time_conflict(db: Session, reservation_data: ReservationCreate, exclude_id: Optional[int] = None) -> bool:
    """
    시간 충돌 확인
    """
    query = db.query(Reservation).filter(
        and_(
            Reservation.reservation_type == reservation_data.reservation_type,
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.APPROVED]),
            or_(
                and_(
                    Reservation.start_time <= reservation_data.start_time,
                    Reservation.end_time > reservation_data.start_time
                ),
                and_(
                    Reservation.start_time < reservation_data.end_time,
                    Reservation.end_time >= reservation_data.end_time
                ),
                and_(
                    Reservation.start_time >= reservation_data.start_time,
                    Reservation.end_time <= reservation_data.end_time
                )
            )
        )
    )
    
    if exclude_id:
        query = query.filter(Reservation.id != exclude_id)
    
    return query.first() is not None


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