"""
사용자 CRUD 연산
데이터베이스 사용자 관련 생성, 조회, 수정, 삭제 작업
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

def create_user(db: Session, user_data: UserCreate) -> User:
    """
    새로운 사용자 생성
    """
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name,
        phone=user_data.phone,
        apartment_number=user_data.apartment_number
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_super_admin(db: Session, username: str, email: str, password: str, name: str) -> User:
    """
    슈퍼관리자 생성
    """
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        name=name,
        is_admin=True,
        is_super_admin=True,
        admin_approved=True,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_admin_user(db: Session, user_data: UserCreate) -> User:
    """
    관리자 계정 생성 (승인 대기 상태)
    """
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name,
        phone=user_data.phone,
        apartment_number=user_data.apartment_number,
        is_admin=True,
        admin_approved=False,  # 승인 대기 상태
        is_active=False  # 승인될 때까지 비활성화
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_super_admin(db: Session) -> Optional[User]:
    """
    슈퍼관리자 조회
    """
    return db.query(User).filter(User.is_super_admin == True).first()

def get_pending_admin_users(db: Session) -> List[User]:
    """
    승인 대기 중인 관리자 계정들 조회
    """
    return db.query(User).filter(
        User.is_admin == True,
        User.admin_approved == False
    ).all()

def approve_admin_user(db: Session, user_id: int) -> Optional[User]:
    """
    관리자 계정 승인
    """
    db_user = get_user(db, user_id)
    if not db_user or not db_user.is_admin or db_user.admin_approved is not False:
        return None
    
    db_user.admin_approved = True
    db_user.is_active = True
    db.commit()
    db.refresh(db_user)
    return db_user

def reject_admin_user(db: Session, user_id: int) -> bool:
    """
    관리자 계정 거부 (계정 삭제)
    """
    db_user = get_user(db, user_id)
    if not db_user or not db_user.is_admin or db_user.admin_approved is not False:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

def get_user(db: Session, user_id: int) -> Optional[User]:
    """
    ID로 사용자 조회
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    사용자명으로 사용자 조회
    """
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    이메일로 사용자 조회
    """
    return db.query(User).filter(User.email == email).first()

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    사용자 정보 수정
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """
    사용자 삭제
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True 