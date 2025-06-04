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
    echo=True            # SQL 쿼리 로깅 (개발용)
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
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    데이터베이스 초기화
    테이블 생성 및 초기 데이터 설정
    """
    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("✅ 데이터베이스 테이블이 생성되었습니다.")

def check_db_connection():
    """
    데이터베이스 연결 상태 확인
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        print("✅ 데이터베이스 연결 성공")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False 