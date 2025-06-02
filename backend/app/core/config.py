"""
FastAPI 애플리케이션 환경 설정
환경 변수와 앱 구성을 중앙에서 관리합니다.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    환경 변수에서 값을 읽어와 앱 설정을 구성합니다.
    """
    
    # 기본 앱 설정
    PROJECT_NAME: str = "FNM - File & Note Manager"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "아파트 이사예약 관리 시스템"
    
    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql://fnmuser:fnmpassword@localhost:5432/fnm_db"
    
    # JWT 토큰 설정
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS 설정
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 개발 환경 설정
    DEBUG: bool = True
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: Optional[str]) -> str:
        """
        데이터베이스 URL 유효성 검증
        PostgreSQL URL 형식을 확인합니다.
        """
        if v and not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must start with 'postgresql://'")
        return v
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"  # .env 파일에서 환경 변수 읽기
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings() 