"""
통계 및 분석 데이터 API
예약 통계, 월별/일별 이용률, 인기 시간대 등의 데이터 제공
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from app.db.database import get_db
from app.models.user import User
from app.models.reservation import Reservation

router = APIRouter()

@router.get("/dashboard-stats")
async def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    대시보드 기본 통계 데이터 조회
    전체 사용자 수, 예약 수, 승인률 등
    """
    try:
        # 전체 사용자 수
        total_users = db.query(User).filter(User.is_active == True).count()
        
        # 전체 예약 수
        total_reservations = db.query(Reservation).count()
        
        # 이번 달 예약 수
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_reservations = db.query(Reservation).filter(
            Reservation.created_at >= current_month_start
        ).count()
        
        # 승인된 예약 수
        approved_reservations = db.query(Reservation).filter(
            Reservation.status == 'approved'
        ).count()
        
        # 대기 중인 예약 수
        pending_reservations = db.query(Reservation).filter(
            Reservation.status == 'pending'
        ).count()
        
        # 승인률 계산
        approval_rate = (approved_reservations / total_reservations * 100) if total_reservations > 0 else 0
        
        return {
            "total_users": total_users,
            "total_reservations": total_reservations,
            "monthly_reservations": monthly_reservations,
            "approved_reservations": approved_reservations,
            "pending_reservations": pending_reservations,
            "approval_rate": round(approval_rate, 1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 데이터 조회 실패: {str(e)}")

@router.get("/monthly-stats")
async def get_monthly_stats(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    월별 예약 통계 데이터 조회
    최근 12개월간의 예약 현황
    """
    try:
        # 현재 날짜 기준으로 12개월 전부터 조회
        current_date = datetime.now()
        twelve_months_ago = current_date - timedelta(days=365)
        
        # 월별 예약 수 집계
        monthly_data = db.query(
            extract('year', Reservation.created_at).label('year'),
            extract('month', Reservation.created_at).label('month'),
            func.count(Reservation.id).label('total'),
            func.sum(func.case([(Reservation.status == 'approved', 1)], else_=0)).label('approved'),
            func.sum(func.case([(Reservation.status == 'rejected', 1)], else_=0)).label('rejected'),
            func.sum(func.case([(Reservation.status == 'pending', 1)], else_=0)).label('pending')
        ).filter(
            Reservation.created_at >= twelve_months_ago
        ).group_by(
            extract('year', Reservation.created_at),
            extract('month', Reservation.created_at)
        ).order_by(
            extract('year', Reservation.created_at),
            extract('month', Reservation.created_at)
        ).all()
        
        # 데이터 포맷팅
        result = []
        for row in monthly_data:
            month_name = f"{int(row.year)}-{int(row.month):02d}"
            result.append({
                "month": month_name,
                "total": int(row.total),
                "approved": int(row.approved or 0),
                "rejected": int(row.rejected or 0),
                "pending": int(row.pending or 0)
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"월별 통계 조회 실패: {str(e)}")

@router.get("/daily-stats")
async def get_daily_stats(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    최근 30일간의 일별 예약 통계
    """
    try:
        # 30일 전부터 현재까지
        current_date = datetime.now()
        thirty_days_ago = current_date - timedelta(days=30)
        
        # 일별 예약 수 집계
        daily_data = db.query(
            func.date(Reservation.created_at).label('date'),
            func.count(Reservation.id).label('total'),
            func.sum(func.case([(Reservation.status == 'approved', 1)], else_=0)).label('approved')
        ).filter(
            Reservation.created_at >= thirty_days_ago
        ).group_by(
            func.date(Reservation.created_at)
        ).order_by(
            func.date(Reservation.created_at)
        ).all()
        
        # 데이터 포맷팅
        result = []
        for row in daily_data:
            result.append({
                "date": row.date.strftime("%m-%d"),
                "total": int(row.total),
                "approved": int(row.approved or 0)
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일별 통계 조회 실패: {str(e)}")

@router.get("/time-slots-stats")
async def get_time_slots_stats(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    시간대별 예약 통계
    인기 시간대 분석
    """
    try:
        # 시간대별 예약 수 집계
        time_slots_data = db.query(
            extract('hour', Reservation.created_at).label('hour'),
            func.count(Reservation.id).label('count')
        ).group_by(
            extract('hour', Reservation.created_at)
        ).order_by(
            extract('hour', Reservation.created_at)
        ).all()
        
        # 데이터 포맷팅
        result = []
        for row in time_slots_data:
            hour = int(row.hour)
            time_label = f"{hour:02d}:00"
            result.append({
                "time": time_label,
                "count": int(row.count)
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시간대별 통계 조회 실패: {str(e)}")

@router.get("/status-distribution")
async def get_status_distribution(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    예약 상태별 분포 통계
    파이 차트용 데이터
    """
    try:
        # 상태별 예약 수 집계
        status_data = db.query(
            Reservation.status,
            func.count(Reservation.id).label('count')
        ).group_by(
            Reservation.status
        ).all()
        
        # 데이터 포맷팅
        result = []
        status_labels = {
            'pending': '대기중',
            'approved': '승인됨',
            'rejected': '거부됨',
            'cancelled': '취소됨'
        }
        
        for row in status_data:
            result.append({
                "status": status_labels.get(row.status, row.status),
                "count": int(row.count),
                "status_key": row.status
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태별 분포 조회 실패: {str(e)}") 