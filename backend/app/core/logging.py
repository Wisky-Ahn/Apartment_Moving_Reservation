"""
강화된 로깅 시스템
구조화된 로그 형식, 레벨별 처리, 컨텍스트 정보 포함
"""
import logging
import logging.config
import json
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
from enum import Enum
import sys
import os

from app.core.config import settings


class LogLevel(str, Enum):
    """로그 레벨 정의"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """로그 카테고리 정의"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"


class ContextualFormatter(logging.Formatter):
    """
    구조화된 로그 형식을 제공하는 커스텀 포매터
    JSON 형태로 로그를 출력하여 파싱과 분석이 용이함
    """
    
    def format(self, record):
        """로그 레코드를 구조화된 JSON 형태로 포맷팅"""
        
        # 기본 로그 정보
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": os.getpid(),
            "thread_id": record.thread,
        }
        
        # 추가 컨텍스트 정보가 있으면 포함
        if hasattr(record, 'extra_context') and record.extra_context:
            log_entry["context"] = record.extra_context
        
        # 요청 ID가 있으면 포함 (추적을 위해)
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        # 사용자 정보가 있으면 포함
        if hasattr(record, 'user_info'):
            log_entry["user"] = record.user_info
        
        # 에러 정보가 있으면 포함
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # 카테고리 정보
        if hasattr(record, 'category'):
            log_entry["category"] = record.category
        
        # 비즈니스 메트릭
        if hasattr(record, 'metrics'):
            log_entry["metrics"] = record.metrics
        
        return json.dumps(log_entry, ensure_ascii=False, indent=2 if settings.DEBUG else None)


class SecurityFilter(logging.Filter):
    """
    보안에 민감한 정보를 필터링하는 필터
    비밀번호, 토큰 등의 정보가 로그에 노출되지 않도록 방지
    """
    
    SENSITIVE_FIELDS = [
        'password', 'token', 'secret', 'key', 'authorization',
        'hashed_password', 'access_token', 'refresh_token'
    ]
    
    def filter(self, record):
        """민감한 정보를 마스킹 처리"""
        if hasattr(record, 'extra_context') and record.extra_context:
            record.extra_context = self._mask_sensitive_data(record.extra_context)
        
        # 메시지에서도 민감한 정보 검사
        message = record.getMessage()
        for field in self.SENSITIVE_FIELDS:
            if field in message.lower():
                # 로그 레벨을 WARNING으로 변경하여 주의 표시
                if record.levelno < logging.WARNING:
                    record.levelno = logging.WARNING
                    record.levelname = "WARNING"
                break
        
        return True
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """딕셔너리에서 민감한 데이터를 마스킹"""
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                masked_data[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data


class EnhancedLogger:
    """
    강화된 로거 클래스
    구조화된 로깅과 컨텍스트 정보를 쉽게 추가할 수 있는 메서드 제공
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
        self.request_id: Optional[str] = None
        self.user_info: Optional[Dict[str, Any]] = None
    
    def set_context(self, **kwargs):
        """로깅 컨텍스트 설정"""
        self.context.update(kwargs)
        return self
    
    def set_request_id(self, request_id: str):
        """요청 ID 설정"""
        self.request_id = request_id
        return self
    
    def set_user_info(self, user_id: Union[int, str], username: str = None, **extra):
        """사용자 정보 설정"""
        self.user_info = {
            "user_id": user_id,
            "username": username,
            **extra
        }
        return self
    
    def _log(self, level: int, message: str, category: LogCategory = None, 
             metrics: Dict[str, Any] = None, **extra_context):
        """내부 로깅 메서드"""
        
        # 추가 컨텍스트 정보 준비
        combined_context = {**self.context, **extra_context}
        
        extra = {
            'extra_context': combined_context if combined_context else None,
            'category': category.value if category else None,
            'metrics': metrics,
        }
        
        if self.request_id:
            extra['request_id'] = self.request_id
            
        if self.user_info:
            extra['user_info'] = self.user_info
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, category: LogCategory = None, **kwargs):
        """디버그 로그"""
        self._log(logging.DEBUG, message, category, **kwargs)
    
    def info(self, message: str, category: LogCategory = None, **kwargs):
        """정보 로그"""
        self._log(logging.INFO, message, category, **kwargs)
    
    def warning(self, message: str, category: LogCategory = None, **kwargs):
        """경고 로그"""
        self._log(logging.WARNING, message, category, **kwargs)
    
    def error(self, message: str, category: LogCategory = None, exc_info=None, **kwargs):
        """에러 로그"""
        if exc_info is True:
            exc_info = sys.exc_info()
        self.logger.error(message, exc_info=exc_info, extra={
            'extra_context': {**self.context, **kwargs} if (self.context or kwargs) else None,
            'category': category.value if category else None,
            'request_id': self.request_id,
            'user_info': self.user_info
        })
    
    def critical(self, message: str, category: LogCategory = None, exc_info=None, **kwargs):
        """치명적 에러 로그"""
        if exc_info is True:
            exc_info = sys.exc_info()
        self.logger.critical(message, exc_info=exc_info, extra={
            'extra_context': {**self.context, **kwargs} if (self.context or kwargs) else None,
            'category': category.value if category else None,
            'request_id': self.request_id,
            'user_info': self.user_info
        })
    
    def log_api_request(self, method: str, path: str, user_id: Optional[int] = None, 
                       request_data: Dict[str, Any] = None, **kwargs):
        """API 요청 로그"""
        self.info(
            f"API Request: {method} {path}",
            category=LogCategory.API_REQUEST,
            method=method,
            path=path,
            user_id=user_id,
            request_data=request_data,
            **kwargs
        )
    
    def log_api_response(self, method: str, path: str, status_code: int, 
                        response_time_ms: float, **kwargs):
        """API 응답 로그"""
        self.info(
            f"API Response: {method} {path} - {status_code} ({response_time_ms:.2f}ms)",
            category=LogCategory.API_RESPONSE,
            method=method,
            path=path,
            status_code=status_code,
            response_time_ms=response_time_ms,
            metrics={"response_time_ms": response_time_ms},
            **kwargs
        )
    
    def log_authentication(self, event: str, username: str = None, success: bool = True, **kwargs):
        """인증 관련 로그"""
        level = logging.INFO if success else logging.WARNING
        self._log(
            level,
            f"Authentication {event}: {'Success' if success else 'Failed'}",
            category=LogCategory.AUTHENTICATION,
            event=event,
            username=username,
            success=success,
            **kwargs
        )
    
    def log_database_operation(self, operation: str, table: str = None, 
                              execution_time_ms: float = None, **kwargs):
        """데이터베이스 작업 로그"""
        metrics = {}
        if execution_time_ms is not None:
            metrics["execution_time_ms"] = execution_time_ms
        
        self.info(
            f"Database {operation}" + (f" on {table}" if table else ""),
            category=LogCategory.DATABASE,
            operation=operation,
            table=table,
            metrics=metrics if metrics else None,
            **kwargs
        )
    
    def log_validation_error(self, field: str, value: Any, error_message: str, **kwargs):
        """검증 에러 로그"""
        self.warning(
            f"Validation error on field '{field}': {error_message}",
            category=LogCategory.VALIDATION,
            field=field,
            value=str(value),
            error_message=error_message,
            **kwargs
        )
    
    def log_security_event(self, event: str, severity: str = "medium", **kwargs):
        """보안 이벤트 로그"""
        level_map = {
            "low": logging.INFO,
            "medium": logging.WARNING,
            "high": logging.ERROR,
            "critical": logging.CRITICAL
        }
        
        self._log(
            level_map.get(severity, logging.WARNING),
            f"Security Event: {event}",
            category=LogCategory.SECURITY,
            event=event,
            severity=severity,
            **kwargs
        )


def setup_logging():
    """
    로깅 시스템 초기화
    파일 핸들러, 콘솔 핸들러 등을 설정
    """
    
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 로깅 설정
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "contextual": {
                "()": ContextualFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "filters": {
            "security_filter": {
                "()": SecurityFilter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO" if not settings.DEBUG else "DEBUG",
                "formatter": "simple" if settings.DEBUG else "contextual",
                "stream": "ext://sys.stdout",
                "filters": ["security_filter"]
            },
            "file_all": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "contextual",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "filters": ["security_filter"]
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "contextual",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "filters": ["security_filter"]
            },
            "file_security": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "contextual",
                "filename": "logs/security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "filters": ["security_filter"]
            }
        },
        "loggers": {
            "app": {
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "handlers": ["console", "file_all", "file_error"],
                "propagate": False
            },
            "app.security": {
                "level": "WARNING",
                "handlers": ["console", "file_security"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING",  # SQL 쿼리 로그는 WARNING 이상만
                "handlers": ["file_all"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file_all"]
        }
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> EnhancedLogger:
    """강화된 로거 인스턴스 반환"""
    return EnhancedLogger(name)


# 전역 로거 인스턴스들
app_logger = get_logger("app")
security_logger = get_logger("app.security")
api_logger = get_logger("app.api")
db_logger = get_logger("app.database")


class LogContext:
    """
    로그 컨텍스트 관리를 위한 컨텍스트 매니저
    특정 스코프 내에서 로그에 공통 컨텍스트를 자동으로 추가
    """
    
    def __init__(self, logger: EnhancedLogger, **context):
        self.logger = logger
        self.context = context
        self.original_context = {}
    
    def __enter__(self):
        # 기존 컨텍스트 백업
        self.original_context = self.logger.context.copy()
        # 새 컨텍스트 설정
        self.logger.set_context(**self.context)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 원래 컨텍스트 복원
        self.logger.context = self.original_context


# 편의 함수들
def log_with_context(logger: EnhancedLogger, **context):
    """컨텍스트와 함께 로깅하는 컨텍스트 매니저 반환"""
    return LogContext(logger, **context)


def generate_request_id() -> str:
    """요청 추적을 위한 고유 ID 생성"""
    return str(uuid.uuid4()) 