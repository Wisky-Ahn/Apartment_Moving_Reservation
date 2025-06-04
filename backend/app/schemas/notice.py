"""
공지사항 Pydantic 스키마
API 요청/응답 데이터 검증을 위한 스키마 정의
"""
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.models.notice import NoticeType

class NoticeBase(BaseModel):
    """공지사항 기본 스키마"""
    title: str
    content: str
    notice_type: NoticeType = NoticeType.GENERAL
    is_pinned: bool = False
    is_important: bool = False
    
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('제목은 최소 5자 이상이어야 합니다')
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('내용은 최소 10자 이상이어야 합니다')
        return v.strip()

class NoticeCreate(NoticeBase):
    """공지사항 생성 스키마"""
    pass

class NoticeUpdate(BaseModel):
    """공지사항 수정 스키마"""
    title: Optional[str] = None
    content: Optional[str] = None
    notice_type: Optional[NoticeType] = None
    is_pinned: Optional[bool] = None
    is_important: Optional[bool] = None
    is_active: Optional[bool] = None
    published_at: Optional[datetime] = None

class NoticeInDB(NoticeBase):
    """데이터베이스의 공지사항 스키마"""
    id: int
    author_id: int
    is_active: bool
    view_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class NoticeResponse(NoticeInDB):
    """공지사항 응답 스키마"""
    is_new: bool
    display_type: str

class NoticeListItem(BaseModel):
    """공지사항 목록 아이템 스키마"""
    id: int
    title: str
    notice_type: NoticeType
    is_pinned: bool
    is_important: bool
    is_new: bool
    view_count: int
    author_id: int
    created_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class NoticeListResponse(BaseModel):
    """공지사항 목록 응답 스키마"""
    notices: List[NoticeResponse]
    total: int
    page: int
    per_page: int

class NoticeTypeFilter(BaseModel):
    """
    공지사항 유형 필터 스키마
    공지사항 유형별 필터링에 사용됩니다.
    """
    notice_type: Optional[str] = None
    is_important: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_active: Optional[bool] = True

class NoticeStats(BaseModel):
    """
    공지사항 통계 스키마
    관리자 대시보드용 통계 정보입니다.
    """
    total_notices: int
    active_notices: int
    important_notices: int
    pinned_notices: int
    notices_by_type: dict
    
    class Config:
        schema_extra = {
            "example": {
                "total_notices": 25,
                "active_notices": 23,
                "important_notices": 5,
                "pinned_notices": 2,
                "notices_by_type": {
                    "general": 15,
                    "important": 5,
                    "maintenance": 3,
                    "event": 2
                }
            }
        } 