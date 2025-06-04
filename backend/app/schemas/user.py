"""
사용자 Pydantic 스키마
API 요청/응답 데이터 검증을 위한 스키마 정의
강화된 데이터 검증 및 보안 규칙 적용
"""
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Annotated
from datetime import datetime
import re

class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="사용자명 (3-50자, 영문/숫자/언더바/하이픈만 허용)"
    )
    
    email: EmailStr = Field(..., description="이메일 주소")
    
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=50,
        description="실명 (2-50자)"
    )
    
    phone: Optional[str] = Field(
        None, 
        pattern=r'^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$',
        description="휴대폰 번호 (010-1234-5678 형식)"
    )
    
    apartment_number: Optional[str] = Field(
        None, 
        pattern=r'^[0-9]{1,4}동\s?[0-9]{1,4}호$',
        description="아파트 동호수 (예: 101동 1001호)"
    )

    @validator('username')
    def validate_username(cls, v):
        """사용자명 검증"""
        if v.lower() in ['admin', 'root', 'system', 'superuser', 'administrator']:
            raise ValueError('예약된 사용자명은 사용할 수 없습니다.')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """이름 검증"""
        if not re.match(r'^[가-힣a-zA-Z\s]+$', v):
            raise ValueError('이름은 한글, 영문, 공백만 허용됩니다.')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        """휴대폰 번호 검증"""
        if v is None:
            return v
        
        # 하이픈 제거 후 검증
        phone_digits = re.sub(r'[^0-9]', '', v)
        if not re.match(r'^01[0-9][0-9]{7,8}$', phone_digits):
            raise ValueError('올바른 휴대폰 번호 형식이 아닙니다. (010-1234-5678)')
        
        # 표준 형식으로 변환
        return f"{phone_digits[:3]}-{phone_digits[3:7]}-{phone_digits[7:]}"


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="비밀번호 (8-128자, 영문+숫자+특수문자 조합 권장)"
    )
    
    confirm_password: Optional[str] = Field(None, description="비밀번호 확인")
    
    @validator('password')
    def validate_password(cls, v):
        """비밀번호 강도 검증"""
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다.')
        
        # 비밀번호 강도 체크
        has_upper = bool(re.search(r'[A-Z]', v))
        has_lower = bool(re.search(r'[a-z]', v))
        has_digit = bool(re.search(r'\d', v))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', v))
        
        strength_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength_score < 2:
            raise ValueError('비밀번호는 영문 대소문자, 숫자, 특수문자 중 최소 2가지 이상 포함해야 합니다.')
        
        # 일반적인 약한 비밀번호 패턴 체크
        weak_patterns = [
            r'12345678', r'password', r'qwerty', r'admin123',
            r'00000000', r'11111111', r'abcdefgh'
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, v.lower()):
                raise ValueError('일반적으로 사용되는 약한 비밀번호는 사용할 수 없습니다.')
        
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        """비밀번호 확인 검증"""
        if 'password' in values and v != values['password']:
            raise ValueError('비밀번호와 비밀번호 확인이 일치하지 않습니다.')
        return v


class UserUpdate(BaseModel):
    """사용자 수정 스키마"""
    email: Optional[EmailStr] = Field(None, description="이메일 주소")
    
    name: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=50,
        description="실명 (2-50자)"
    )
    
    phone: Optional[str] = Field(
        None, 
        pattern=r'^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$',
        description="휴대폰 번호"
    )
    
    apartment_number: Optional[str] = Field(
        None, 
        pattern=r'^[0-9]{1,4}동\s?[0-9]{1,4}호$',
        description="아파트 동호수"
    )
    
    bio: Optional[str] = Field(
        None, 
        max_length=500,
        description="자기소개 (최대 500자)"
    )
    
    profile_image: Optional[str] = Field(None, description="프로필 이미지 URL")

    @validator('name')
    def validate_name(cls, v):
        """이름 검증"""
        if v is not None and not re.match(r'^[가-힣a-zA-Z\s]+$', v):
            raise ValueError('이름은 한글, 영문, 공백만 허용됩니다.')
        return v.strip() if v else v
    
    @validator('phone')
    def validate_phone(cls, v):
        """휴대폰 번호 검증"""
        if v is None:
            return v
        
        phone_digits = re.sub(r'[^0-9]', '', v)
        if not re.match(r'^01[0-9][0-9]{7,8}$', phone_digits):
            raise ValueError('올바른 휴대폰 번호 형식이 아닙니다.')
        
        return f"{phone_digits[:3]}-{phone_digits[3:7]}-{phone_digits[7:]}"
    
    @validator('bio')
    def validate_bio(cls, v):
        """자기소개 검증"""
        if v is not None:
            # 욕설이나 부적절한 내용 필터링 (간단한 예시)
            inappropriate_words = ['욕설1', '욕설2']  # 실제로는 더 포괄적인 필터 필요
            for word in inappropriate_words:
                if word in v:
                    raise ValueError('부적절한 내용이 포함되어 있습니다.')
        return v


class UserPasswordChange(BaseModel):
    """비밀번호 변경 스키마"""
    current_password: str = Field(..., description="현재 비밀번호")
    
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="새 비밀번호"
    )
    
    confirm_new_password: str = Field(..., description="새 비밀번호 확인")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """새 비밀번호 검증 (UserCreate와 동일한 규칙)"""
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다.')
        
        has_upper = bool(re.search(r'[A-Z]', v))
        has_lower = bool(re.search(r'[a-z]', v))
        has_digit = bool(re.search(r'\d', v))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', v))
        
        strength_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength_score < 2:
            raise ValueError('비밀번호는 영문 대소문자, 숫자, 특수문자 중 최소 2가지 이상 포함해야 합니다.')
        
        return v
    
    @validator('confirm_new_password')
    def validate_confirm_new_password(cls, v, values):
        """새 비밀번호 확인 검증"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('새 비밀번호와 비밀번호 확인이 일치하지 않습니다.')
        return v


class UserInDB(UserBase):
    """데이터베이스의 사용자 스키마"""
    id: int = Field(..., description="사용자 ID")
    is_admin: bool = Field(..., description="관리자 여부")
    is_super_admin: bool = Field(False, description="슈퍼관리자 여부")
    admin_approved: bool = Field(False, description="관리자 승인 여부")
    is_active: bool = Field(..., description="활성 상태")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    last_login: Optional[datetime] = Field(None, description="마지막 로그인")
    profile_image: Optional[str] = Field(None, description="프로필 이미지 URL")
    bio: Optional[str] = Field(None, description="자기소개")
    
    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """사용자 응답 스키마 (비밀번호 제외)"""
    pass


class UserListResponse(BaseModel):
    """사용자 목록 응답 스키마"""
    users: List[UserResponse] = Field(..., description="사용자 목록")
    total: int = Field(..., description="전체 사용자 수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """로그인 스키마"""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="사용자명 또는 이메일"
    )
    password: str = Field(
        ..., 
        min_length=1, 
        max_length=128,
        description="비밀번호"
    )
    
    @validator('username')
    def validate_username(cls, v):
        """로그인 사용자명 검증"""
        # 이메일 형식이거나 일반 사용자명 형식이어야 함
        if '@' in v:
            # 이메일 형식 체크
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
                raise ValueError('올바른 이메일 형식이 아닙니다.')
        else:
            # 사용자명 형식 체크
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('사용자명은 영문, 숫자, 언더바, 하이픈만 허용됩니다.')
        
        return v.lower().strip()


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간(초)")
    user: UserResponse = Field(..., description="사용자 정보")
    
    class Config:
        from_attributes = True 