"""
애플리케이션 설정
환경변수 및 기본 설정을 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    환경변수에서 설정값을 읽어옴
    """
    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql://user:password@localhost/fnm_db"
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # 애플리케이션 설정
    PROJECT_NAME: str = "FNM - File & Note Manager"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "아파트 이사예약 관리 시스템"
    DEBUG: bool = True
    
    # CORS 설정
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 페이지네이션 설정
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 전역 설정 인스턴스
settings = Settings() 