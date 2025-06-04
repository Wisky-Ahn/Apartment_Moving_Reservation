"""
예약 모델
SQLAlchemy를 사용한 Reservation 테이블 정의
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base

class ReservationType(str, enum.Enum):
    """예약 유형 열거형"""
    ELEVATOR = "elevator"
    PARKING = "parking"
    OTHER = "other"

class ReservationStatus(str, enum.Enum):
    """예약 상태 열거형"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Reservation(Base):
    """
    예약 테이블 모델
    이사 예약 정보를 저장
    """
    __tablename__ = "reservations"

    # 기본 필드
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="예약자 ID")
    
    # 예약 정보
    reservation_type = Column(Enum(ReservationType), nullable=False, comment="예약 유형")
    start_time = Column(DateTime(timezone=True), nullable=False, comment="시작 시간")
    end_time = Column(DateTime(timezone=True), nullable=False, comment="종료 시간")
    description = Column(Text, nullable=True, comment="요청사항 및 설명")
    
    # 상태 관리
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING, comment="예약 상태")
    admin_comment = Column(Text, nullable=True, comment="관리자 코멘트")
    
    # 시간 필드
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정일시")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="승인일시")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="완료일시")
    
    # 관계 설정
    user = relationship("User", back_populates="reservations")
    
    def __repr__(self):
        return f"<Reservation(id={self.id}, user_id={self.user_id}, type={self.reservation_type}, status={self.status})>"
    
    @property
    def duration_hours(self):
        """예약 시간 계산 (시간 단위)"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 3600
        return 0
    
    @property
    def is_active(self):
        """현재 활성화된 예약인지 확인"""
        return self.status in [ReservationStatus.PENDING, ReservationStatus.APPROVED]
    
    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "reservation_type": self.reservation_type.value if self.reservation_type else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "admin_comment": self.admin_comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_hours": self.duration_hours,
            "is_active": self.is_active,
        } 