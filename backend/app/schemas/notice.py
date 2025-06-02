"""
공지사항 관련 Pydantic 스키마
API 요청/응답 데이터 검증 및 직렬화를 담당합니다.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class NoticeBase(BaseModel):
    """
    공지사항 기본 스키마
    공통 필드들을 정의합니다.
    """
    title: str = Field(..., min_length=1, max_length=200, description="공지사항 제목")
    content: str = Field(..., min_length=1, description="공지사항 내용")
    notice_type: str = Field(..., description="공지사항 유형 (general, important, maintenance, event)")
    is_important: bool = Field(default=False, description="중요 공지 여부")
    is_pinned: bool = Field(default=False, description="상단 고정 여부")
    is_active: bool = Field(default=True, description="활성화 여부")


class NoticeCreate(NoticeBase):
    """
    공지사항 생성 스키마
    새로운 공지사항을 작성할 때 사용됩니다.
    """
    author_id: int = Field(..., description="작성자 ID (관리자)")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "엘리베이터 점검 안내",
                "content": "2024년 6월 3일 오전 9시부터 12시까지 엘리베이터 정기점검이 있습니다.",
                "notice_type": "maintenance",
                "is_important": True,
                "is_pinned": False,
                "is_active": True,
                "author_id": 1
            }
        }


class NoticeUpdate(BaseModel):
    """
    공지사항 수정 스키마
    기존 공지사항을 수정할 때 사용됩니다.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="공지사항 제목")
    content: Optional[str] = Field(None, min_length=1, description="공지사항 내용")
    notice_type: Optional[str] = Field(None, description="공지사항 유형")
    is_important: Optional[bool] = Field(None, description="중요 공지 여부")
    is_pinned: Optional[bool] = Field(None, description="상단 고정 여부")
    is_active: Optional[bool] = Field(None, description="활성화 여부")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "수정된 공지사항 제목",
                "content": "수정된 공지사항 내용",
                "is_important": False,
                "is_pinned": True
            }
        }


class NoticeResponse(NoticeBase):
    """
    공지사항 응답 스키마
    API 응답으로 반환되는 공지사항 정보입니다.
    """
    id: int = Field(..., description="공지사항 ID")
    author_id: int = Field(..., description="작성자 ID")
    author_name: Optional[str] = Field(None, description="작성자 이름")
    view_count: int = Field(default=0, description="조회수")
    created_at: datetime = Field(..., description="작성일시")
    updated_at: datetime = Field(..., description="수정일시")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "title": "엘리베이터 점검 안내",
                "content": "2024년 6월 3일 오전 9시부터 12시까지 엘리베이터 정기점검이 있습니다.",
                "notice_type": "maintenance",
                "is_important": True,
                "is_pinned": False,
                "is_active": True,
                "author_id": 1,
                "author_name": "관리사무소",
                "view_count": 25,
                "created_at": "2024-06-02T10:00:00Z",
                "updated_at": "2024-06-02T10:00:00Z"
            }
        }


class NoticeListResponse(BaseModel):
    """
    공지사항 목록 응답 스키마
    페이지네이션된 공지사항 목록을 반환합니다.
    """
    notices: List[NoticeResponse] = Field(..., description="공지사항 목록")
    total: int = Field(..., description="전체 공지사항 수")
    page: int = Field(..., description="현재 페이지")
    per_page: int = Field(..., description="페이지당 항목 수")
    
    class Config:
        schema_extra = {
            "example": {
                "notices": [
                    {
                        "id": 1,
                        "title": "엘리베이터 점검 안내",
                        "content": "점검 안내 내용...",
                        "notice_type": "maintenance",
                        "is_important": True,
                        "is_pinned": False,
                        "is_active": True,
                        "author_id": 1,
                        "author_name": "관리사무소",
                        "view_count": 25,
                        "created_at": "2024-06-02T10:00:00Z",
                        "updated_at": "2024-06-02T10:00:00Z"
                    }
                ],
                "total": 15,
                "page": 1,
                "per_page": 10
            }
        }


class NoticeTypeFilter(BaseModel):
    """
    공지사항 유형 필터 스키마
    공지사항 유형별 필터링에 사용됩니다.
    """
    notice_type: Optional[str] = Field(None, description="공지사항 유형")
    is_important: Optional[bool] = Field(None, description="중요 공지만 조회")
    is_pinned: Optional[bool] = Field(None, description="고정 공지만 조회")
    is_active: Optional[bool] = Field(True, description="활성화된 공지만 조회")


class NoticeStats(BaseModel):
    """
    공지사항 통계 스키마
    관리자 대시보드용 통계 정보입니다.
    """
    total_notices: int = Field(..., description="전체 공지사항 수")
    active_notices: int = Field(..., description="활성화된 공지사항 수")
    important_notices: int = Field(..., description="중요 공지사항 수")
    pinned_notices: int = Field(..., description="고정된 공지사항 수")
    notices_by_type: dict = Field(..., description="유형별 공지사항 수")
    
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