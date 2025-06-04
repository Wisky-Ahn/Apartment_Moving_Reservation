"""
공지사항 모델
SQLAlchemy를 사용한 Notice 테이블 정의
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base

class NoticeType(str, enum.Enum):
    """공지사항 유형 열거형"""
    GENERAL = "general"
    ANNOUNCEMENT = "announcement"
    EVENT = "event"

class Notice(Base):
    """
    공지사항 테이블 모델
    아파트 공지사항 정보를 저장
    """
    __tablename__ = "notices"

    # 기본 필드
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True, comment="제목")
    content = Column(Text, nullable=False, comment="내용")
    
    # 분류 및 속성
    notice_type = Column(Enum(NoticeType), default=NoticeType.GENERAL, comment="공지 유형")
    is_pinned = Column(Boolean, default=False, comment="상단 고정 여부")
    is_important = Column(Boolean, default=False, comment="중요 공지 여부")
    is_active = Column(Boolean, default=True, comment="활성화 여부")
    
    # 조회 및 통계
    view_count = Column(Integer, default=0, comment="조회수")
    
    # 작성자 정보
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="작성자 ID")
    
    # 시간 필드
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정일시")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="게시일시")
    
    # 관계 설정
    author = relationship("User", back_populates="notices")
    
    def __repr__(self):
        return f"<Notice(id={self.id}, title='{self.title[:30]}...', type={self.notice_type})>"
    
    @property
    def is_new(self):
        """신규 공지사항인지 확인 (7일 이내)"""
        if self.created_at:
            from datetime import datetime, timedelta
            return datetime.utcnow() - self.created_at.replace(tzinfo=None) < timedelta(days=7)
        return False
    
    @property
    def display_type(self):
        """표시용 유형명"""
        type_mapping = {
            NoticeType.GENERAL: "일반",
            NoticeType.ANNOUNCEMENT: "공지",
            NoticeType.EVENT: "이벤트"
        }
        return type_mapping.get(self.notice_type, "일반")
    
    def increment_view_count(self):
        """조회수 증가"""
        self.view_count += 1
    
    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "notice_type": self.notice_type.value if self.notice_type else None,
            "is_pinned": self.is_pinned,
            "is_important": self.is_important,
            "is_active": self.is_active,
            "view_count": self.view_count,
            "author_id": self.author_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "is_new": self.is_new,
            "display_type": self.display_type,
        } 