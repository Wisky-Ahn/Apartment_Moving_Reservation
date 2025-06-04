"""
데이터베이스 예외 처리 시스템
다양한 데이터베이스 예외를 체계적으로 처리하고 사용자 친화적 메시지 제공
"""
import re
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    DataError,
    OperationalError,
    DatabaseError,
    InvalidRequestError,
    TimeoutError,
    DisconnectionError,
    CompileError,
    ArgumentError,
    NoResultFound,
    MultipleResultsFound
)
from psycopg2.errors import (
    UniqueViolation,
    ForeignKeyViolation,
    CheckViolation,
    NotNullViolation,
    NumericValueOutOfRange,
    StringDataRightTruncation,
    DeadlockDetected,
    ConnectionException as PgConnectionException
)

from app.core.exceptions import (
    DatabaseException,
    ValidationException,
    BusinessLogicException,
    ErrorCode
)
from app.core.logging import db_logger, LogCategory


class DatabaseErrorType(str, Enum):
    """데이터베이스 에러 유형"""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    INTEGRITY_CONSTRAINT = "integrity_constraint"
    UNIQUE_VIOLATION = "unique_violation"
    FOREIGN_KEY_VIOLATION = "foreign_key_violation"
    NOT_NULL_VIOLATION = "not_null_violation"
    CHECK_VIOLATION = "check_violation"
    DATA_ERROR = "data_error"
    DEADLOCK = "deadlock"
    PERMISSION_DENIED = "permission_denied"
    INVALID_QUERY = "invalid_query"
    RESOURCE_LIMIT = "resource_limit"
    UNKNOWN_ERROR = "unknown_error"


class DatabaseErrorMapper:
    """데이터베이스 에러를 사용자 친화적 메시지로 변환하는 매퍼"""
    
    # 테이블별 사용자 친화적 이름
    TABLE_NAMES = {
        'users': '사용자',
        'reservations': '예약',
        'notices': '공지사항',
        'user_roles': '사용자 권한',
        'reservation_conflicts': '예약 충돌'
    }
    
    # 컬럼별 사용자 친화적 이름
    COLUMN_NAMES = {
        'username': '사용자명',
        'email': '이메일',
        'phone': '전화번호',
        'apartment_number': '동호수',
        'start_time': '시작시간',
        'end_time': '종료시간',
        'title': '제목',
        'content': '내용',
        'password': '비밀번호',
        'name': '이름'
    }
    
    # 제약조건별 메시지
    CONSTRAINT_MESSAGES = {
        'users_username_key': '이미 사용중인 사용자명입니다.',
        'users_email_key': '이미 등록된 이메일 주소입니다.',
        'users_phone_key': '이미 등록된 전화번호입니다.',
        'reservations_time_check': '예약 시간이 올바르지 않습니다.',
        'users_apartment_number_key': '이미 등록된 동호수입니다.',
        'reservation_user_fkey': '존재하지 않는 사용자입니다.',
        'notice_author_fkey': '존재하지 않는 작성자입니다.'
    }
    
    @staticmethod
    def map_error(error: SQLAlchemyError) -> Tuple[DatabaseErrorType, str, str, Dict[str, Any]]:
        """
        데이터베이스 에러를 분류하고 사용자 친화적 메시지로 변환
        
        Args:
            error: SQLAlchemy 에러 객체
            
        Returns:
            Tuple[DatabaseErrorType, str, str, Dict[str, Any]]: 
            (에러 타입, 기술적 메시지, 사용자 메시지, 상세 정보)
        """
        error_str = str(error).lower()
        original_error = getattr(error, 'orig', None)
        
        db_logger.info(
            f"Mapping database error: {type(error).__name__}",
            category=LogCategory.DATABASE,
            error_type=type(error).__name__,
            error_message=str(error)[:200]
        )
        
        # PostgreSQL 특정 에러 처리
        if original_error:
            return DatabaseErrorMapper._map_postgresql_error(original_error, error_str)
        
        # SQLAlchemy 일반 에러 처리
        return DatabaseErrorMapper._map_sqlalchemy_error(error, error_str)
    
    @staticmethod
    def _map_postgresql_error(pg_error, error_str: str) -> Tuple[DatabaseErrorType, str, str, Dict[str, Any]]:
        """PostgreSQL 특정 에러 매핑"""
        
        error_details = {}
        
        if isinstance(pg_error, UniqueViolation):
            # 고유 제약조건 위반
            constraint_name = DatabaseErrorMapper._extract_constraint_name(error_str)
            field_name = DatabaseErrorMapper._extract_field_name(error_str)
            
            if constraint_name in DatabaseErrorMapper.CONSTRAINT_MESSAGES:
                user_message = DatabaseErrorMapper.CONSTRAINT_MESSAGES[constraint_name]
            else:
                field_display = DatabaseErrorMapper.COLUMN_NAMES.get(field_name, field_name)
                user_message = f"이미 존재하는 {field_display}입니다."
            
            error_details = {
                "constraint": constraint_name,
                "field": field_name,
                "violation_type": "unique"
            }
            
            return (
                DatabaseErrorType.UNIQUE_VIOLATION,
                f"Unique constraint violation: {constraint_name}",
                user_message,
                error_details
            )
        
        elif isinstance(pg_error, ForeignKeyViolation):
            # 외래키 제약조건 위반
            constraint_name = DatabaseErrorMapper._extract_constraint_name(error_str)
            table_name = DatabaseErrorMapper._extract_table_name(error_str)
            
            table_display = DatabaseErrorMapper.TABLE_NAMES.get(table_name, table_name)
            user_message = f"연관된 {table_display} 정보가 존재하지 않습니다."
            
            error_details = {
                "constraint": constraint_name,
                "table": table_name,
                "violation_type": "foreign_key"
            }
            
            return (
                DatabaseErrorType.FOREIGN_KEY_VIOLATION,
                f"Foreign key constraint violation: {constraint_name}",
                user_message,
                error_details
            )
        
        elif isinstance(pg_error, NotNullViolation):
            # NOT NULL 제약조건 위반
            field_name = DatabaseErrorMapper._extract_field_name(error_str)
            field_display = DatabaseErrorMapper.COLUMN_NAMES.get(field_name, field_name)
            
            user_message = f"{field_display}은(는) 필수 입력 항목입니다."
            
            error_details = {
                "field": field_name,
                "violation_type": "not_null"
            }
            
            return (
                DatabaseErrorType.NOT_NULL_VIOLATION,
                f"Not null constraint violation on field: {field_name}",
                user_message,
                error_details
            )
        
        elif isinstance(pg_error, CheckViolation):
            # CHECK 제약조건 위반
            constraint_name = DatabaseErrorMapper._extract_constraint_name(error_str)
            
            if 'email' in constraint_name:
                user_message = "올바른 이메일 형식을 입력해주세요."
            elif 'phone' in constraint_name:
                user_message = "올바른 전화번호 형식을 입력해주세요."
            elif 'time' in constraint_name:
                user_message = "올바른 시간을 입력해주세요."
            else:
                user_message = "입력값이 허용된 범위를 벗어났습니다."
            
            error_details = {
                "constraint": constraint_name,
                "violation_type": "check"
            }
            
            return (
                DatabaseErrorType.CHECK_VIOLATION,
                f"Check constraint violation: {constraint_name}",
                user_message,
                error_details
            )
        
        elif isinstance(pg_error, NumericValueOutOfRange):
            return (
                DatabaseErrorType.DATA_ERROR,
                "Numeric value out of range",
                "입력된 숫자가 허용된 범위를 벗어났습니다.",
                {"violation_type": "numeric_range"}
            )
        
        elif isinstance(pg_error, StringDataRightTruncation):
            return (
                DatabaseErrorType.DATA_ERROR,
                "String data too long",
                "입력된 텍스트가 허용된 길이를 초과했습니다.",
                {"violation_type": "string_length"}
            )
        
        elif isinstance(pg_error, DeadlockDetected):
            return (
                DatabaseErrorType.DEADLOCK,
                "Database deadlock detected",
                "다른 사용자와 동시에 같은 데이터를 수정하려고 시도했습니다. 잠시 후 다시 시도해주세요.",
                {"violation_type": "deadlock"}
            )
        
        elif isinstance(pg_error, PgConnectionException):
            return (
                DatabaseErrorType.CONNECTION_ERROR,
                "Database connection error",
                "데이터베이스 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
                {"violation_type": "connection"}
            )
        
        # 알려지지 않은 PostgreSQL 에러
        return (
            DatabaseErrorType.UNKNOWN_ERROR,
            f"Unknown PostgreSQL error: {str(pg_error)}",
            "데이터베이스 처리 중 오류가 발생했습니다.",
            {"postgres_error": type(pg_error).__name__}
        )
    
    @staticmethod
    def _map_sqlalchemy_error(error: SQLAlchemyError, error_str: str) -> Tuple[DatabaseErrorType, str, str, Dict[str, Any]]:
        """SQLAlchemy 일반 에러 매핑"""
        
        if isinstance(error, IntegrityError):
            return (
                DatabaseErrorType.INTEGRITY_CONSTRAINT,
                f"Database integrity error: {str(error)}",
                "데이터 무결성 위반이 발생했습니다. 입력 데이터를 확인해주세요.",
                {"sqlalchemy_error": "IntegrityError"}
            )
        
        elif isinstance(error, DataError):
            return (
                DatabaseErrorType.DATA_ERROR,
                f"Database data error: {str(error)}",
                "입력된 데이터 형식이 올바르지 않습니다.",
                {"sqlalchemy_error": "DataError"}
            )
        
        elif isinstance(error, OperationalError):
            if 'timeout' in error_str or 'timed out' in error_str:
                return (
                    DatabaseErrorType.TIMEOUT_ERROR,
                    f"Database operation timeout: {str(error)}",
                    "데이터베이스 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.",
                    {"sqlalchemy_error": "OperationalError", "timeout": True}
                )
            elif 'connection' in error_str:
                return (
                    DatabaseErrorType.CONNECTION_ERROR,
                    f"Database connection error: {str(error)}",
                    "데이터베이스 연결에 문제가 발생했습니다.",
                    {"sqlalchemy_error": "OperationalError", "connection": True}
                )
            else:
                return (
                    DatabaseErrorType.UNKNOWN_ERROR,
                    f"Database operational error: {str(error)}",
                    "데이터베이스 작업 중 오류가 발생했습니다.",
                    {"sqlalchemy_error": "OperationalError"}
                )
        
        elif isinstance(error, TimeoutError):
            return (
                DatabaseErrorType.TIMEOUT_ERROR,
                f"Database timeout: {str(error)}",
                "데이터베이스 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.",
                {"sqlalchemy_error": "TimeoutError"}
            )
        
        elif isinstance(error, DisconnectionError):
            return (
                DatabaseErrorType.CONNECTION_ERROR,
                f"Database disconnection: {str(error)}",
                "데이터베이스 연결이 끊어졌습니다. 다시 연결을 시도해주세요.",
                {"sqlalchemy_error": "DisconnectionError"}
            )
        
        elif isinstance(error, InvalidRequestError):
            return (
                DatabaseErrorType.INVALID_QUERY,
                f"Invalid database request: {str(error)}",
                "잘못된 요청입니다. 다시 시도해주세요.",
                {"sqlalchemy_error": "InvalidRequestError"}
            )
        
        elif isinstance(error, NoResultFound):
            return (
                DatabaseErrorType.UNKNOWN_ERROR,
                f"No result found: {str(error)}",
                "요청하신 데이터를 찾을 수 없습니다.",
                {"sqlalchemy_error": "NoResultFound"}
            )
        
        elif isinstance(error, MultipleResultsFound):
            return (
                DatabaseErrorType.UNKNOWN_ERROR,
                f"Multiple results found: {str(error)}",
                "중복된 데이터가 발견되었습니다. 관리자에게 문의해주세요.",
                {"sqlalchemy_error": "MultipleResultsFound"}
            )
        
        # 알려지지 않은 SQLAlchemy 에러
        return (
            DatabaseErrorType.UNKNOWN_ERROR,
            f"Unknown SQLAlchemy error: {str(error)}",
            "데이터베이스 처리 중 예상치 못한 오류가 발생했습니다.",
            {"sqlalchemy_error": type(error).__name__}
        )
    
    @staticmethod
    def _extract_constraint_name(error_str: str) -> Optional[str]:
        """에러 메시지에서 제약조건 이름 추출"""
        patterns = [
            r'constraint "([^"]+)"',
            r'constraint (\w+)',
            r'Key \(([^)]+)\)',
            r'violates (\w+) constraint'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _extract_field_name(error_str: str) -> Optional[str]:
        """에러 메시지에서 필드 이름 추출"""
        patterns = [
            r'column "([^"]+)"',
            r'Key \(([^)]+)\)',
            r'null value in column "([^"]+)"',
            r'duplicate key value violates.*\(([^)]+)\)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                field = match.group(1)
                # 복합 키인 경우 첫 번째 필드만 반환
                if ',' in field:
                    field = field.split(',')[0].strip()
                return field
        
        return None
    
    @staticmethod 
    def _extract_table_name(error_str: str) -> Optional[str]:
        """에러 메시지에서 테이블 이름 추출"""
        patterns = [
            r'table "([^"]+)"',
            r'relation "([^"]+)"',
            r'on table (\w+)',
            r'insert or update on table "([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None


class DatabaseExceptionHandler:
    """데이터베이스 예외 통합 처리기"""
    
    @staticmethod
    def handle_database_error(error: SQLAlchemyError, operation: str = "database operation") -> None:
        """
        데이터베이스 에러를 처리하고 적절한 예외를 발생시킴
        
        Args:
            error: SQLAlchemy 에러 객체
            operation: 수행 중이던 작업 설명
            
        Raises:
            DatabaseException: 데이터베이스 관련 예외
            ValidationException: 데이터 검증 관련 예외
            BusinessLogicException: 비즈니스 로직 관련 예외
        """
        error_type, technical_message, user_message, details = DatabaseErrorMapper.map_error(error)
        
        # 로깅
        db_logger.error(
            f"Database error during {operation}: {technical_message}",
            category=LogCategory.DATABASE,
            exc_info=True,
            error_type=error_type.value,
            operation=operation,
            details=details
        )
        
        # 에러 타입에 따른 예외 발생
        if error_type in [DatabaseErrorType.UNIQUE_VIOLATION, 
                         DatabaseErrorType.NOT_NULL_VIOLATION,
                         DatabaseErrorType.CHECK_VIOLATION,
                         DatabaseErrorType.DATA_ERROR]:
            # 데이터 검증 관련 에러
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=technical_message,
                user_message=user_message,
                details=details
            )
        
        elif error_type == DatabaseErrorType.FOREIGN_KEY_VIOLATION:
            # 비즈니스 로직 위반
            raise BusinessLogicException(
                error_code=ErrorCode.FOREIGN_KEY_ERROR,
                message=technical_message,
                user_message=user_message,
                details=details
            )
        
        elif error_type in [DatabaseErrorType.CONNECTION_ERROR,
                           DatabaseErrorType.TIMEOUT_ERROR]:
            # 연결/시간 초과 에러
            raise DatabaseException(
                error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message=technical_message,
                user_message=user_message,
                details=details
            )
        
        elif error_type == DatabaseErrorType.DEADLOCK:
            # 데드락
            raise DatabaseException(
                error_code=ErrorCode.DATABASE_ERROR,
                message=technical_message,
                user_message=user_message,
                details=details
            )
        
        else:
            # 기타 데이터베이스 에러
            raise DatabaseException(
                error_code=ErrorCode.DATABASE_ERROR,
                message=technical_message,
                user_message=user_message,
                details=details
            )
    
    @staticmethod
    def handle_transaction_error(error: Exception, operation: str) -> None:
        """트랜잭션 에러 특별 처리"""
        if isinstance(error, SQLAlchemyError):
            DatabaseExceptionHandler.handle_database_error(error, f"transaction {operation}")
        else:
            # SQLAlchemy 외의 에러
            db_logger.error(
                f"Transaction error during {operation}: {str(error)}",
                category=LogCategory.DATABASE,
                exc_info=True,
                operation=operation
            )
            
            raise DatabaseException(
                error_code=ErrorCode.DATABASE_ERROR,
                message=f"Transaction failed during {operation}: {str(error)}",
                user_message="데이터 처리 중 오류가 발생했습니다. 다시 시도해주세요."
            )


# 편의 함수들
def handle_db_error(error: SQLAlchemyError, operation: str = "database operation") -> None:
    """데이터베이스 에러 처리 편의 함수"""
    DatabaseExceptionHandler.handle_database_error(error, operation)


def handle_transaction_error(error: Exception, operation: str) -> None:
    """트랜잭션 에러 처리 편의 함수"""
    DatabaseExceptionHandler.handle_transaction_error(error, operation) 