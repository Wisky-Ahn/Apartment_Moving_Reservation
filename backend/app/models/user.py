"""
사용자 모델
SQLAlchemy를 사용한 User 테이블 정의
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    """
    사용자 테이블 모델
    아파트 거주자 정보를 저장
    """
    __tablename__ = "users"

    # 기본 필드
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="사용자 아이디")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="이메일 주소")
    hashed_password = Column(String(128), nullable=False, comment="암호화된 비밀번호")
    
    # 개인 정보
    name = Column(String(50), nullable=False, comment="실명")
    phone = Column(String(20), nullable=True, comment="전화번호")
    apartment_number = Column(String(20), nullable=True, comment="아파트 호수")
    
    # 권한 및 상태
    is_admin = Column(Boolean, default=False, comment="관리자 여부")
    is_active = Column(Boolean, default=True, comment="계정 활성화 여부")
    
    # 시간 필드
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정일시")
    last_login = Column(DateTime(timezone=True), nullable=True, comment="마지막 로그인")
    
    # 추가 정보
    profile_image = Column(String(255), nullable=True, comment="프로필 이미지 URL")
    bio = Column(Text, nullable=True, comment="자기소개")
    
    # 관계 설정
    reservations = relationship("Reservation", back_populates="user", cascade="all, delete-orphan")
    notices = relationship("Notice", back_populates="author", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', name='{self.name}')>"
    
    @property
    def display_name(self):
        """표시용 이름 (이름 + 호수)"""
        if self.apartment_number:
            return f"{self.name} ({self.apartment_number})"
        return self.name
    
    def to_dict(self):
        """딕셔너리로 변환 (비밀번호 제외)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "apartment_number": self.apartment_number,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "profile_image": self.profile_image,
            "bio": self.bio,
        } 