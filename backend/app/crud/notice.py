"""
공지사항 관리 CRUD 함수들
데이터베이스와의 공지사항 관련 작업을 처리합니다.
"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.notice import Notice
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeStats


def create_notice(db: Session, notice_data: NoticeCreate) -> Notice:
    """
    새로운 공지사항을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        notice_data: 공지사항 생성 데이터
        
    Returns:
        Notice: 생성된 공지사항 객체
    """
    db_notice = Notice(
        title=notice_data.title,
        content=notice_data.content,
        notice_type=notice_data.notice_type,
        is_important=notice_data.is_important,
        is_pinned=notice_data.is_pinned,
        is_active=notice_data.is_active,
        author_id=notice_data.author_id,
        view_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_notice)
    db.commit()
    db.refresh(db_notice)
    return db_notice


def get_notice(db: Session, notice_id: int) -> Optional[Notice]:
    """
    특정 공지사항을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        notice_id: 공지사항 ID
        
    Returns:
        Optional[Notice]: 공지사항 객체 또는 None
    """
    return db.query(Notice).filter(Notice.id == notice_id).first()


def get_notices(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    notice_type: Optional[str] = None,
    is_important: Optional[bool] = None,
    is_pinned: Optional[bool] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None
) -> Tuple[List[Notice], int]:
    """
    공지사항 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        skip: 건너뛸 공지사항 수
        limit: 가져올 최대 공지사항 수
        notice_type: 공지사항 유형 필터
        is_important: 중요 공지만 조회
        is_pinned: 고정 공지만 조회
        is_active: 활성화된 공지만 조회
        search: 제목/내용 검색어
        
    Returns:
        Tuple[List[Notice], int]: 공지사항 목록과 총 개수
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
    
    # 검색 기능
    if search:
        search_filter = or_(
            Notice.title.ilike(f"%{search}%"),
            Notice.content.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # 총 개수 계산
    total = query.count()
    
    # 정렬: 고정 공지 우선, 그 다음 중요 공지, 마지막으로 생성일 역순
    notices = query.order_by(
        desc(Notice.is_pinned),
        desc(Notice.is_important),
        desc(Notice.created_at)
    ).offset(skip).limit(limit).all()
    
    return notices, total


def update_notice(
    db: Session, 
    notice_id: int, 
    notice_update: NoticeUpdate
) -> Optional[Notice]:
    """
    공지사항 정보를 수정합니다.
    
    Args:
        db: 데이터베이스 세션
        notice_id: 공지사항 ID
        notice_update: 수정할 데이터
        
    Returns:
        Optional[Notice]: 수정된 공지사항 객체 또는 None
    """
    db_notice = db.query(Notice).filter(Notice.id == notice_id).first()
    
    if not db_notice:
        return None
    
    # 수정할 필드들 업데이트
    update_data = notice_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_notice, field, value)
    
    # 수정 시간 업데이트
    db_notice.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_notice)
    return db_notice


def delete_notice(db: Session, notice_id: int) -> bool:
    """
    공지사항을 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        notice_id: 공지사항 ID
        
    Returns:
        bool: 삭제 성공 여부
    """
    db_notice = db.query(Notice).filter(Notice.id == notice_id).first()
    
    if not db_notice:
        return False
    
    db.delete(db_notice)
    db.commit()
    return True


def increment_view_count(db: Session, notice_id: int) -> bool:
    """
    공지사항의 조회수를 증가시킵니다.
    
    Args:
        db: 데이터베이스 세션
        notice_id: 공지사항 ID
        
    Returns:
        bool: 조회수 증가 성공 여부
    """
    db_notice = db.query(Notice).filter(Notice.id == notice_id).first()
    
    if not db_notice:
        return False
    
    db_notice.view_count += 1
    db.commit()
    return True


def get_notice_stats(db: Session) -> NoticeStats:
    """
    공지사항 통계를 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        NoticeStats: 공지사항 통계 정보
    """
    # 전체 공지사항 수
    total_notices = db.query(Notice).count()
    
    # 활성화된 공지사항 수
    active_notices = db.query(Notice).filter(Notice.is_active == True).count()
    
    # 중요 공지사항 수
    important_notices = db.query(Notice).filter(
        and_(Notice.is_important == True, Notice.is_active == True)
    ).count()
    
    # 고정된 공지사항 수
    pinned_notices = db.query(Notice).filter(
        and_(Notice.is_pinned == True, Notice.is_active == True)
    ).count()
    
    # 유형별 공지사항 수
    type_stats = db.query(
        Notice.notice_type,
        func.count(Notice.id).label('count')
    ).filter(Notice.is_active == True).group_by(Notice.notice_type).all()
    
    notices_by_type = {stat.notice_type: stat.count for stat in type_stats}
    
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