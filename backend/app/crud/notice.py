"""
공지사항 CRUD 연산
데이터베이스 공지사항 관련 생성, 조회, 수정, 삭제 작업
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, Tuple, List
from datetime import datetime
from app.models.notice import Notice, NoticeType
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeStats

def create_notice(db: Session, notice_data: NoticeCreate) -> Notice:
    """
    새로운 공지사항 생성
    """
    db_notice = Notice(**notice_data.dict())
    db.add(db_notice)
    db.commit()
    db.refresh(db_notice)
    return db_notice

def get_notice(db: Session, notice_id: int) -> Optional[Notice]:
    """
    ID로 공지사항 조회
    """
    return db.query(Notice).filter(Notice.id == notice_id).first()

def get_notices(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    notice_type: Optional[str] = None,
    is_important: Optional[bool] = None,
    is_pinned: Optional[bool] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> Tuple[List[Notice], int]:
    """
    공지사항 목록 조회 (필터링 포함)
    """
    query = db.query(Notice)
    
    # 필터 적용
    if notice_type:
        query = query.filter(Notice.notice_type == notice_type)
    if is_important is not None:
        query = query.filter(Notice.is_important == is_important)
    if is_pinned is not None:
        query = query.filter(Notice.is_pinned == is_pinned)
    if is_active is not None:
        query = query.filter(Notice.is_active == is_active)
    if search:
        query = query.filter(
            or_(
                Notice.title.contains(search),
                Notice.content.contains(search)
            )
        )
    
    # 총 개수 계산
    total = query.count()
    
    # 정렬: 고정 공지가 먼저, 그 다음 생성일시 역순
    query = query.order_by(desc(Notice.is_pinned), desc(Notice.created_at))
    
    # 페이지네이션 적용
    notices = query.offset(skip).limit(limit).all()
    
    return notices, total

def update_notice(db: Session, notice_id: int, notice_update: NoticeUpdate) -> Optional[Notice]:
    """
    공지사항 정보 수정
    """
    db_notice = get_notice(db, notice_id)
    if not db_notice:
        return None
    
    update_data = notice_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_notice, field, value)
    
    db.commit()
    db.refresh(db_notice)
    return db_notice

def delete_notice(db: Session, notice_id: int) -> bool:
    """
    공지사항 삭제
    """
    db_notice = get_notice(db, notice_id)
    if not db_notice:
        return False
    
    db.delete(db_notice)
    db.commit()
    return True

def increment_view_count(db: Session, notice_id: int) -> Optional[Notice]:
    """
    공지사항 조회수 증가
    """
    db_notice = get_notice(db, notice_id)
    if not db_notice:
        return None
    
    db_notice.increment_view_count()
    db.commit()
    db.refresh(db_notice)
    return db_notice

def get_notice_stats(db: Session) -> NoticeStats:
    """
    공지사항 통계 조회
    """
    total_notices = db.query(Notice).count()
    active_notices = db.query(Notice).filter(Notice.is_active == True).count()
    important_notices = db.query(Notice).filter(Notice.is_important == True).count()
    pinned_notices = db.query(Notice).filter(Notice.is_pinned == True).count()
    
    # 유형별 통계
    notices_by_type = {}
    for notice_type in NoticeType:
        count = db.query(Notice).filter(Notice.notice_type == notice_type).count()
        notices_by_type[notice_type.value] = count
    
    return NoticeStats(
        total_notices=total_notices,
        active_notices=active_notices,
        important_notices=important_notices,
        pinned_notices=pinned_notices,
        notices_by_type=notices_by_type
    )

def get_notices_by_type(
    db: Session,
    notice_type: str,
    limit: int = 10
) -> List[Notice]:
    """
    특정 유형의 공지사항을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        notice_type: 공지사항 유형
        limit: 가져올 최대 공지사항 수
        
    Returns:
        List[Notice]: 해당 유형의 공지사항 목록
    """
    return db.query(Notice).filter(
        and_(
            Notice.notice_type == notice_type,
            Notice.is_active == True
        )
    ).order_by(desc(Notice.created_at)).limit(limit).all()

def get_recent_notices(
    db: Session,
    limit: int = 5
) -> List[Notice]:
    """
    최근 공지사항을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        limit: 가져올 최대 공지사항 수
        
    Returns:
        List[Notice]: 최근 공지사항 목록
    """
    return db.query(Notice).filter(
        Notice.is_active == True
    ).order_by(desc(Notice.created_at)).limit(limit).all()

def get_popular_notices(
    db: Session,
    limit: int = 5
) -> List[Notice]:
    """
    인기 공지사항을 조회합니다. (조회수 기준)
    
    Args:
        db: 데이터베이스 세션
        limit: 가져올 최대 공지사항 수
        
    Returns:
        List[Notice]: 인기 공지사항 목록
    """
    return db.query(Notice).filter(
        Notice.is_active == True
    ).order_by(desc(Notice.view_count)).limit(limit).all()

def search_notices(
    db: Session,
    search_term: str,
    limit: int = 20
) -> List[Notice]:
    """
    공지사항을 검색합니다.
    
    Args:
        db: 데이터베이스 세션
        search_term: 검색어
        limit: 가져올 최대 공지사항 수
        
    Returns:
        List[Notice]: 검색 결과 공지사항 목록
    """
    search_filter = or_(
        Notice.title.ilike(f"%{search_term}%"),
        Notice.content.ilike(f"%{search_term}%")
    )
    
    return db.query(Notice).filter(
        and_(
            search_filter,
            Notice.is_active == True
        )
    ).order_by(desc(Notice.created_at)).limit(limit).all() 