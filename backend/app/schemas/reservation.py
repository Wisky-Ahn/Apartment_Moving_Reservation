"""
예약 Pydantic 스키마
API 요청/응답 데이터 검증을 위한 스키마 정의
"""
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.models.reservation import ReservationType, ReservationStatus

class ReservationBase(BaseModel):
    """예약 기본 스키마"""
    reservation_type: ReservationType
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('종료 시간은 시작 시간보다 늦어야 합니다')
        return v

class ReservationCreate(ReservationBase):
    """예약 생성 스키마"""
    pass

class ReservationUpdate(BaseModel):
    """예약 수정 스키마"""
    reservation_type: Optional[ReservationType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    status: Optional[ReservationStatus] = None
    admin_comment: Optional[str] = None

class ReservationInDB(ReservationBase):
    """데이터베이스의 예약 스키마"""
    id: int
    user_id: int
    status: ReservationStatus
    admin_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ReservationResponse(ReservationInDB):
    """예약 응답 스키마"""
    duration_hours: float
    is_active: bool

class ReservationListResponse(BaseModel):
    """예약 목록 응답 스키마"""
    reservations: List[ReservationResponse]
    total: int
    page: int
    per_page: int

class ReservationStatusUpdate(BaseModel):
    """예약 상태 업데이트 스키마"""
    status: ReservationStatus
    admin_comment: Optional[str] = None 