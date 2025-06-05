"""
데이터베이스 연결 및 세션 관리
PostgreSQL 데이터베이스와의 연결을 담당
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 연결 확인
    pool_recycle=300,    # 5분마다 연결 재활용
    pool_size=20,        # 연결 풀 크기 증가 (기본값: 5)
    max_overflow=30,     # 추가 연결 허용 (기본값: 10)
    pool_timeout=30,     # 연결 대기 타임아웃 (기본값: 30초)
    echo=False           # SQL 쿼리 로깅 비활성화 (성능 향상)
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성 (모든 모델의 부모 클래스)
Base = declarative_base()

# 메타데이터 객체
metadata = MetaData()

def get_db():
    """
    데이터베이스 세션 의존성
    FastAPI 의존성 주입에서 사용
    연결 누수 방지를 위한 강화된 예외 처리
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # 예외 발생 시 롤백
        db.rollback()
        raise e
    finally:
        # 반드시 연결 종료
        db.close()

def init_db():
    """
    데이터베이스 초기화
    기존 테이블을 삭제하고 새로 생성
    """
    # 기존 테이블 모두 삭제 (개발용)
    Base.metadata.drop_all(bind=engine)
    print("🗑️ 기존 데이터베이스 테이블이 삭제되었습니다.")
    
    # 모든 테이블 새로 생성
    Base.metadata.create_all(bind=engine)
    print("✅ 데이터베이스 테이블이 생성되었습니다.")

def check_db_connection():
    """
    데이터베이스 연결 상태 확인
    """
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            connection.execute(text("SELECT 1"))
        print("✅ 데이터베이스 연결 성공")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False 