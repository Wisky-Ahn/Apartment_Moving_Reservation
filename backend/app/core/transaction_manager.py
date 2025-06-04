"""
트랜잭션 관리 및 롤백 시스템
데이터베이스 트랜잭션의 안전한 관리와 자동 롤백 메커니즘 제공
"""
import functools
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Generic
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

from app.core.database_exceptions import DatabaseExceptionHandler
from app.core.logging import db_logger, LogCategory
from app.core.exceptions import DatabaseException, ErrorCode
from app.db.database import get_db

T = TypeVar('T')


class TransactionContext:
    """트랜잭션 컨텍스트 정보"""
    
    def __init__(self, operation: str, auto_commit: bool = True, auto_rollback: bool = True):
        self.operation = operation
        self.auto_commit = auto_commit
        self.auto_rollback = auto_rollback
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.status: str = "pending"
        self.rollback_points: List[str] = []
        self.error: Optional[Exception] = None
        
    def add_rollback_point(self, point_name: str):
        """롤백 포인트 추가"""
        self.rollback_points.append(f"{point_name}_{datetime.now().isoformat()}")
        
    def mark_completed(self):
        """트랜잭션 완료 표시"""
        self.end_time = datetime.now()
        self.status = "completed"
        
    def mark_failed(self, error: Exception):
        """트랜잭션 실패 표시"""
        self.end_time = datetime.now()
        self.status = "failed"
        self.error = error
        
    @property
    def duration(self) -> float:
        """트랜잭션 실행 시간 (초)"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


class DatabaseTransactionManager:
    """데이터베이스 트랜잭션 관리자"""
    
    def __init__(self):
        self.active_transactions: Dict[str, TransactionContext] = {}
        self.transaction_stats = {
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "rollback_count": 0,
            "avg_duration": 0.0
        }
    
    @contextmanager
    def managed_transaction(
        self, 
        db: Session, 
        operation: str,
        auto_commit: bool = True,
        auto_rollback: bool = True,
        timeout_seconds: int = 30
    ):
        """
        관리되는 트랜잭션 컨텍스트 매니저
        
        Args:
            db: 데이터베이스 세션
            operation: 작업 설명
            auto_commit: 자동 커밋 여부
            auto_rollback: 자동 롤백 여부
            timeout_seconds: 타임아웃 시간(초)
            
        Yields:
            TransactionContext: 트랜잭션 컨텍스트
            
        Raises:
            DatabaseException: 트랜잭션 관련 오류
        """
        transaction_id = f"{operation}_{datetime.now().isoformat()}"
        context = TransactionContext(operation, auto_commit, auto_rollback)
        
        self.active_transactions[transaction_id] = context
        self.transaction_stats["total_transactions"] += 1
        
        db_logger.info(
            f"Starting transaction: {operation}",
            category=LogCategory.DATABASE,
            transaction_id=transaction_id,
            operation=operation,
            auto_commit=auto_commit,
            auto_rollback=auto_rollback
        )
        
        try:
            # 트랜잭션 시작
            if not db.in_transaction():
                db.begin()
            
            # 타임아웃 체크를 위한 시작 시간 기록
            start_time = datetime.now()
            
            yield context
            
            # 타임아웃 체크
            if context.duration > timeout_seconds:
                raise DatabaseException(
                    error_code=ErrorCode.DATABASE_TIMEOUT,
                    message=f"Transaction timeout after {context.duration:.2f} seconds",
                    user_message="데이터베이스 작업 시간이 초과되었습니다."
                )
            
            # 자동 커밋
            if auto_commit:
                db.commit()
                context.mark_completed()
                
                db_logger.info(
                    f"Transaction committed successfully: {operation}",
                    category=LogCategory.DATABASE,
                    transaction_id=transaction_id,
                    duration=context.duration
                )
                
                self.transaction_stats["successful_transactions"] += 1
            
        except SQLAlchemyError as e:
            # 데이터베이스 관련 에러
            context.mark_failed(e)
            
            if auto_rollback:
                try:
                    db.rollback()
                    self.transaction_stats["rollback_count"] += 1
                    
                    db_logger.warning(
                        f"Transaction rolled back due to SQLAlchemy error: {operation}",
                        category=LogCategory.DATABASE,
                        transaction_id=transaction_id,
                        error_type=type(e).__name__,
                        duration=context.duration
                    )
                    
                except Exception as rollback_error:
                    db_logger.error(
                        f"Failed to rollback transaction: {operation}",
                        category=LogCategory.DATABASE,
                        transaction_id=transaction_id,
                        rollback_error=str(rollback_error),
                        exc_info=True
                    )
            
            self.transaction_stats["failed_transactions"] += 1
            
            # 구조화된 예외 처리
            DatabaseExceptionHandler.handle_database_error(e, operation)
            
        except Exception as e:
            # 기타 에러
            context.mark_failed(e)
            
            if auto_rollback:
                try:
                    db.rollback()
                    self.transaction_stats["rollback_count"] += 1
                    
                    db_logger.warning(
                        f"Transaction rolled back due to general error: {operation}",
                        category=LogCategory.DATABASE,
                        transaction_id=transaction_id,
                        error_type=type(e).__name__,
                        duration=context.duration
                    )
                    
                except Exception as rollback_error:
                    db_logger.error(
                        f"Failed to rollback transaction: {operation}",
                        category=LogCategory.DATABASE,
                        transaction_id=transaction_id,
                        rollback_error=str(rollback_error),
                        exc_info=True
                    )
            
            self.transaction_stats["failed_transactions"] += 1
            
            DatabaseExceptionHandler.handle_transaction_error(e, operation)
            
        finally:
            # 트랜잭션 정리
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
            
            # 통계 업데이트
            if self.transaction_stats["total_transactions"] > 0:
                total_duration = sum([
                    ctx.duration for ctx in self.active_transactions.values()
                ]) + context.duration
                
                self.transaction_stats["avg_duration"] = (
                    total_duration / self.transaction_stats["total_transactions"]
                )
    
    def create_savepoint(self, db: Session, savepoint_name: str) -> str:
        """
        세이브포인트 생성
        
        Args:
            db: 데이터베이스 세션
            savepoint_name: 세이브포인트 이름
            
        Returns:
            str: 생성된 세이브포인트 ID
        """
        try:
            # PostgreSQL 세이브포인트 생성
            savepoint_id = f"{savepoint_name}_{datetime.now().timestamp()}"
            db.execute(f"SAVEPOINT {savepoint_id}")
            
            db_logger.info(
                f"Savepoint created: {savepoint_id}",
                category=LogCategory.DATABASE,
                savepoint_name=savepoint_name
            )
            
            return savepoint_id
            
        except SQLAlchemyError as e:
            db_logger.error(
                f"Failed to create savepoint: {savepoint_name}",
                category=LogCategory.DATABASE,
                exc_info=True
            )
            DatabaseExceptionHandler.handle_database_error(e, f"create savepoint {savepoint_name}")
    
    def rollback_to_savepoint(self, db: Session, savepoint_id: str):
        """
        세이브포인트로 롤백
        
        Args:
            db: 데이터베이스 세션
            savepoint_id: 세이브포인트 ID
        """
        try:
            db.execute(f"ROLLBACK TO SAVEPOINT {savepoint_id}")
            self.transaction_stats["rollback_count"] += 1
            
            db_logger.info(
                f"Rolled back to savepoint: {savepoint_id}",
                category=LogCategory.DATABASE,
                savepoint_id=savepoint_id
            )
            
        except SQLAlchemyError as e:
            db_logger.error(
                f"Failed to rollback to savepoint: {savepoint_id}",
                category=LogCategory.DATABASE,
                exc_info=True
            )
            DatabaseExceptionHandler.handle_database_error(e, f"rollback to savepoint {savepoint_id}")
    
    def release_savepoint(self, db: Session, savepoint_id: str):
        """
        세이브포인트 해제
        
        Args:
            db: 데이터베이스 세션
            savepoint_id: 세이브포인트 ID
        """
        try:
            db.execute(f"RELEASE SAVEPOINT {savepoint_id}")
            
            db_logger.info(
                f"Released savepoint: {savepoint_id}",
                category=LogCategory.DATABASE,
                savepoint_id=savepoint_id
            )
            
        except SQLAlchemyError as e:
            db_logger.error(
                f"Failed to release savepoint: {savepoint_id}",
                category=LogCategory.DATABASE,
                exc_info=True
            )
            # 세이브포인트 해제 실패는 치명적이지 않으므로 로그만 남김
    
    def get_transaction_stats(self) -> Dict[str, Any]:
        """트랜잭션 통계 반환"""
        stats = self.transaction_stats.copy()
        stats["active_transactions"] = len(self.active_transactions)
        stats["success_rate"] = (
            stats["successful_transactions"] / max(stats["total_transactions"], 1) * 100
        )
        return stats
    
    def get_active_transactions(self) -> Dict[str, Dict[str, Any]]:
        """활성 트랜잭션 목록 반환"""
        return {
            tx_id: {
                "operation": ctx.operation,
                "duration": ctx.duration,
                "status": ctx.status,
                "rollback_points": ctx.rollback_points
            }
            for tx_id, ctx in self.active_transactions.items()
        }


# 전역 트랜잭션 매니저 인스턴스
transaction_manager = DatabaseTransactionManager()


def transactional(
    operation: str = None,
    auto_commit: bool = True,
    auto_rollback: bool = True,
    timeout_seconds: int = 30
):
    """
    트랜잭션 데코레이터
    
    Args:
        operation: 작업 설명 (없으면 함수명 사용)
        auto_commit: 자동 커밋 여부
        auto_rollback: 자동 롤백 여부
        timeout_seconds: 타임아웃 시간(초)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 함수 시그니처에서 db 파라미터 찾기
            db = None
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break
            
            if not db and 'db' in kwargs:
                db = kwargs['db']
            
            if not db:
                raise ValueError("Database session not found in function arguments")
            
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            with transaction_manager.managed_transaction(
                db=db,
                operation=op_name,
                auto_commit=auto_commit,
                auto_rollback=auto_rollback,
                timeout_seconds=timeout_seconds
            ):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


@contextmanager
def database_transaction(
    operation: str,
    auto_commit: bool = True,
    auto_rollback: bool = True,
    timeout_seconds: int = 30
):
    """
    데이터베이스 트랜잭션 컨텍스트 매니저
    
    Args:
        operation: 작업 설명
        auto_commit: 자동 커밋 여부
        auto_rollback: 자동 롤백 여부
        timeout_seconds: 타임아웃 시간(초)
        
    Yields:
        Tuple[Session, TransactionContext]: (데이터베이스 세션, 트랜잭션 컨텍스트)
    """
    db = next(get_db())
    
    try:
        with transaction_manager.managed_transaction(
            db=db,
            operation=operation,
            auto_commit=auto_commit,
            auto_rollback=auto_rollback,
            timeout_seconds=timeout_seconds
        ) as context:
            yield db, context
    finally:
        db.close()


# 편의 함수들
def get_transaction_stats() -> Dict[str, Any]:
    """트랜잭션 통계 반환"""
    return transaction_manager.get_transaction_stats()


def get_active_transactions() -> Dict[str, Dict[str, Any]]:
    """활성 트랜잭션 목록 반환"""
    return transaction_manager.get_active_transactions()


def create_savepoint(db: Session, savepoint_name: str) -> str:
    """세이브포인트 생성"""
    return transaction_manager.create_savepoint(db, savepoint_name)


def rollback_to_savepoint(db: Session, savepoint_id: str):
    """세이브포인트로 롤백"""
    transaction_manager.rollback_to_savepoint(db, savepoint_id)


def release_savepoint(db: Session, savepoint_id: str):
    """세이브포인트 해제"""
    transaction_manager.release_savepoint(db, savepoint_id) 