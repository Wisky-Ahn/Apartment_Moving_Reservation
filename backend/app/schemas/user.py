"""
사용자 Pydantic 스키마
API 요청/응답 데이터 검증을 위한 스키마 정의
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    apartment_number: Optional[str] = None

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        return v

class UserUpdate(BaseModel):
    """사용자 수정 스키마"""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    apartment_number: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None

class UserInDB(UserBase):
    """데이터베이스의 사용자 스키마"""
    id: int
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    """사용자 응답 스키마"""
    pass

class UserLogin(BaseModel):
    """로그인 스키마"""
    username: str
    password: str 