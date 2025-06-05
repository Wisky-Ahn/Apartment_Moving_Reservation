"""
예약 Pydantic 스키마
API 요청/응답 데이터 검증을 위한 스키마 정의
강화된 데이터 검증 및 비즈니스 로직 검증 적용
"""
from pydantic import BaseModel, validator, Field, constr
from typing import Optional, List, Annotated
from datetime import datetime, date, time, timedelta
from app.models.reservation import ReservationType, ReservationStatus
import re

class ReservationBase(BaseModel):
    """예약 기본 스키마"""
    reservation_type: ReservationType = Field(..., description="예약 유형 (입주/이사)")
    start_time: datetime = Field(..., description="예약 시작 시간")
    end_time: datetime = Field(..., description="예약 종료 시간")
    description: Optional[str] = Field(None, max_length=1000, description="예약 설명 (최대 1000자)")
    
    @validator('start_time')
    def validate_start_time(cls, v):
        """시작 시간 검증"""
        now = datetime.now()
        
        # 과거 시간 예약 불가
        if v < now:
            raise ValueError('과거 시간으로는 예약할 수 없습니다.')
        
        # 너무 먼 미래 예약 불가 (6개월 이후)
        max_future = now + timedelta(days=180)
        if v > max_future:
            raise ValueError('6개월 이후의 날짜는 예약할 수 없습니다.')
        
        # 예약 가능 시간 체크 (오전 9시 ~ 오후 6시)
        if v.hour < 9 or v.hour >= 18:
            raise ValueError('예약 가능 시간은 오전 9시부터 오후 6시까지입니다.')
        
        # 주말 예약 불가 (토요일=5, 일요일=6)
        if v.weekday() >= 5:
            raise ValueError('주말에는 예약할 수 없습니다.')
        
        # 30분 단위로만 예약 가능
        if v.minute not in [0, 30]:
            raise ValueError('예약은 30분 단위로만 가능합니다.')
        
        return v
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """종료 시간 검증"""
        if 'start_time' not in values:
            return v
        
        start_time = values['start_time']
        
        # 종료 시간이 시작 시간보다 늦어야 함
        if v <= start_time:
            raise ValueError('종료 시간은 시작 시간보다 늦어야 합니다.')
        
        # 예약 최소 시간 (1시간)
        min_duration = timedelta(hours=1)
        if v - start_time < min_duration:
            raise ValueError('최소 1시간 이상 예약해야 합니다.')
        
        # 예약 최대 시간 (8시간)
        max_duration = timedelta(hours=8)
        if v - start_time > max_duration:
            raise ValueError('최대 8시간까지만 예약 가능합니다.')
        
        # 종료 시간도 영업시간 내여야 함
        if v.hour > 18:
            raise ValueError('예약 종료 시간은 오후 6시를 넘을 수 없습니다.')
        
        # 30분 단위로만 예약 가능
        if v.minute not in [0, 30]:
            raise ValueError('예약은 30분 단위로만 가능합니다.')
        
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """설명 검증"""
        if v is not None:
            # HTML 태그 제거 (보안)
            v = re.sub(r'<[^>]+>', '', v)
            
            # 연속 공백 제거
            v = re.sub(r'\s+', ' ', v).strip()
            
            # 부적절한 내용 필터링 (간단한 예시)
            inappropriate_words = ['욕설1', '욕설2']
            for word in inappropriate_words:
                if word in v:
                    raise ValueError('부적절한 내용이 포함되어 있습니다.')
        
        return v


class ReservationCreate(ReservationBase):
    """예약 생성 스키마"""
    
    @validator('reservation_type')
    def validate_reservation_type(cls, v):
        """예약 유형 검증"""
        if v not in [ReservationType.move_in, ReservationType.move_out]:
            raise ValueError('올바른 예약 유형을 선택해주세요.')
        return v


class ReservationUpdate(BaseModel):
    """예약 수정 스키마"""
    reservation_type: Optional[ReservationType] = Field(None, description="예약 유형")
    start_time: Optional[datetime] = Field(None, description="예약 시작 시간")
    end_time: Optional[datetime] = Field(None, description="예약 종료 시간")
    description: Optional[str] = Field(None, max_length=1000, description="예약 설명")
    status: Optional[ReservationStatus] = Field(None, description="예약 상태")
    admin_comment: Optional[str] = Field(None, max_length=500, description="관리자 코멘트 (최대 500자)")

    @validator('start_time')
    def validate_start_time(cls, v):
        """시작 시간 검증 (수정 시에는 조건 완화)"""
        if v is None:
            return v
        
        now = datetime.now()
        
        # 과거 시간으로의 수정은 관리자만 가능 (별도 로직에서 처리)
        if v < now:
            raise ValueError('과거 시간으로는 수정할 수 없습니다.')
        
        # 예약 가능 시간 체크
        if v.hour < 9 or v.hour >= 18:
            raise ValueError('예약 가능 시간은 오전 9시부터 오후 6시까지입니다.')
        
        # 주말 예약 불가
        if v.weekday() >= 5:
            raise ValueError('주말에는 예약할 수 없습니다.')
        
        return v
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """종료 시간 검증"""
        if v is None:
            return v
        
        if 'start_time' in values and values['start_time'] is not None:
            start_time = values['start_time']
            
            if v <= start_time:
                raise ValueError('종료 시간은 시작 시간보다 늦어야 합니다.')
            
            if v - start_time < timedelta(hours=1):
                raise ValueError('최소 1시간 이상 예약해야 합니다.')
            
            if v - start_time > timedelta(hours=8):
                raise ValueError('최대 8시간까지만 예약 가능합니다.')
        
        return v
    
    @validator('admin_comment')
    def validate_admin_comment(cls, v):
        """관리자 코멘트 검증"""
        if v is not None:
            # HTML 태그 제거
            v = re.sub(r'<[^>]+>', '', v)
            v = re.sub(r'\s+', ' ', v).strip()
        return v


class ReservationStatusUpdate(BaseModel):
    """예약 상태 업데이트 스키마 (관리자 전용)"""
    status: ReservationStatus = Field(..., description="변경할 예약 상태")
    admin_comment: Optional[str] = Field(None, max_length=500, description="관리자 코멘트")
    
    @validator('status')
    def validate_status(cls, v):
        """상태 검증"""
        valid_statuses = [
            ReservationStatus.approved,
            ReservationStatus.rejected,
            ReservationStatus.cancelled,
            ReservationStatus.completed
        ]
        
        if v not in valid_statuses:
            raise ValueError('올바른 상태를 선택해주세요.')
        return v
    
    @validator('admin_comment')
    def validate_admin_comment(cls, v, values):
        """관리자 코멘트 검증"""
        if v is not None:
            # HTML 태그 제거
            v = re.sub(r'<[^>]+>', '', v)
            v = re.sub(r'\s+', ' ', v).strip()
            
            # 거부 상태일 때는 코멘트 필수
            if 'status' in values and values['status'] == ReservationStatus.rejected:
                if not v:
                    raise ValueError('예약 거부 시 사유를 입력해주세요.')
        
        return v


class ReservationInDB(ReservationBase):
    """데이터베이스의 예약 스키마"""
    id: int = Field(..., description="예약 ID")
    user_id: int = Field(..., description="사용자 ID")
    status: ReservationStatus = Field(..., description="예약 상태")
    admin_comment: Optional[str] = Field(None, description="관리자 코멘트")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    approved_at: Optional[datetime] = Field(None, description="승인일시")
    completed_at: Optional[datetime] = Field(None, description="완료일시")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ReservationResponse(ReservationInDB):
    """예약 응답 스키마"""
    duration_hours: float = Field(..., description="예약 시간 (시간 단위)")
    is_active: bool = Field(..., description="활성 상태")
    can_edit: bool = Field(False, description="수정 가능 여부")
    can_cancel: bool = Field(False, description="취소 가능 여부")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ReservationListResponse(BaseModel):
    """예약 목록 응답 스키마"""
    reservations: List[ReservationResponse] = Field(..., description="예약 목록")
    total: int = Field(..., description="전체 예약 수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ReservationSearchParams(BaseModel):
    """예약 검색 파라미터 스키마"""
    status: Optional[ReservationStatus] = Field(None, description="예약 상태")
    reservation_type: Optional[ReservationType] = Field(None, description="예약 유형")
    start_date: Optional[date] = Field(None, description="검색 시작 날짜")
    end_date: Optional[date] = Field(None, description="검색 종료 날짜")
    user_id: Optional[int] = Field(None, description="사용자 ID")
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(10, ge=1, le=100, description="페이지 크기")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """날짜 범위 검증"""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('종료 날짜는 시작 날짜보다 늦어야 합니다.')
            
            # 최대 1년 범위
            if (v - values['start_date']).days > 365:
                raise ValueError('검색 범위는 최대 1년까지입니다.')
        
        return v


class ReservationStatistics(BaseModel):
    """예약 통계 스키마"""
    total_reservations: int = Field(..., description="전체 예약 수")
    pending_reservations: int = Field(..., description="대기중 예약 수")
    approved_reservations: int = Field(..., description="승인된 예약 수")
    rejected_reservations: int = Field(..., description="거부된 예약 수")
    completed_reservations: int = Field(..., description="완료된 예약 수")
    approval_rate: float = Field(..., description="승인률 (%)")
    
    class Config:
        from_attributes = True 