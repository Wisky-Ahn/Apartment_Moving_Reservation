"""
애플리케이션 설정
환경변수 및 기본 설정을 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional, List, Union

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
    
    # 알림 시스템 설정
    # 이메일 알림 설정
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    ALERT_EMAIL_FROM: Optional[str] = None
    ALERT_EMAIL_TO: Optional[Union[str, List[str]]] = None
    
    # Slack 알림 설정
    SLACK_WEBHOOK_URL: Optional[str] = None
    SLACK_CHANNEL: Optional[str] = None
    
    # 웹훅 알림 설정
    ALERT_WEBHOOK_URL: Optional[str] = None
    ALERT_WEBHOOK_HEADERS: Optional[dict] = None
    
    # 알림 레벨 설정 (LOW, MEDIUM, HIGH, CRITICAL)
    ALERT_LEVELS: str = "HIGH,CRITICAL"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 전역 설정 인스턴스
settings = Settings() 