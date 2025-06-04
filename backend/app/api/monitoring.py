"""
API 모니터링 및 성능 분석 엔드포인트
실시간 성능 메트릭 및 에러 분석 데이터 제공
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.middleware.performance import performance_metrics
from app.core.logging import app_logger, LogCategory
from app.core.exceptions import AppException, ErrorCode


# 응답 스키마 정의
class PerformanceStatsResponse(BaseModel):
    """성능 통계 응답 스키마"""
    timestamp: str = Field(..., description="통계 생성 시간")
    active_requests: int = Field(..., description="현재 처리 중인 요청 수")
    total_requests_hour: int = Field(..., description="최근 1시간 총 요청 수")
    total_requests_all: int = Field(..., description="전체 누적 요청 수")
    error_count_hour: int = Field(..., description="최근 1시간 에러 수")
    error_rate_percent: float = Field(..., description="에러율 (%)")
    avg_response_time_ms: float = Field(..., description="평균 응답 시간 (ms)")
    min_response_time_ms: float = Field(..., description="최소 응답 시간 (ms)")
    max_response_time_ms: float = Field(..., description="최대 응답 시간 (ms)")
    throughput_per_minute: float = Field(..., description="분당 처리량 (요청/분)")


class EndpointStatsResponse(BaseModel):
    """엔드포인트별 통계 응답 스키마"""
    endpoint: str = Field(..., description="API 엔드포인트")
    count: int = Field(..., description="총 요청 수")
    error_count: int = Field(..., description="에러 수")
    error_rate_percent: float = Field(..., description="에러율 (%)")
    avg_response_time_ms: float = Field(..., description="평균 응답 시간 (ms)")
    min_response_time_ms: float = Field(..., description="최소 응답 시간 (ms)")
    max_response_time_ms: float = Field(..., description="최대 응답 시간 (ms)")
    last_error: Optional[Dict[str, Any]] = Field(None, description="마지막 에러 정보")


class ErrorPatternResponse(BaseModel):
    """에러 패턴 응답 스키마"""
    error_key: str = Field(..., description="에러 키 (엔드포인트:상태코드)")
    count: int = Field(..., description="총 발생 횟수")
    first_seen: Optional[str] = Field(None, description="최초 발생 시간")
    last_seen: Optional[str] = Field(None, description="마지막 발생 시간")
    recent_frequency: int = Field(..., description="최근 30분 내 발생 횟수")


class AnomalyResponse(BaseModel):
    """이상 징후 응답 스키마"""
    type: str = Field(..., description="이상 징후 유형")
    severity: str = Field(..., description="심각도 (critical/warning/info)")
    value: float = Field(..., description="측정값")
    message: str = Field(..., description="이상 징후 설명")
    timestamp: str = Field(..., description="감지 시간")
    error_key: Optional[str] = Field(None, description="관련 에러 키")


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답 스키마"""
    status: str = Field(..., description="서비스 상태")
    timestamp: str = Field(..., description="체크 시간")
    version: str = Field(..., description="애플리케이션 버전")
    uptime_seconds: float = Field(..., description="서비스 가동 시간 (초)")
    performance_summary: Dict[str, Any] = Field(..., description="성능 요약")
    anomalies_count: int = Field(..., description="현재 감지된 이상 징후 수")


# API 라우터 설정
router = APIRouter(prefix="/monitoring", tags=["모니터링"])

# 서비스 시작 시간 기록
SERVICE_START_TIME = datetime.now()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    헬스 체크 엔드포인트
    서비스 상태 및 기본 성능 정보 제공
    """
    try:
        current_time = datetime.now()
        uptime = (current_time - SERVICE_START_TIME).total_seconds()
        
        # 기본 성능 통계 수집
        stats = performance_metrics.get_current_stats()
        
        # 이상 징후 감지
        anomalies = performance_metrics.detect_anomalies()
        
        # 서비스 상태 결정
        status = "healthy"
        if len(anomalies) > 0:
            critical_anomalies = [a for a in anomalies if a['severity'] == 'critical']
            if critical_anomalies:
                status = "unhealthy"
            else:
                status = "degraded"
        
        return HealthCheckResponse(
            status=status,
            timestamp=current_time.isoformat(),
            version="1.0.0",  # 실제 버전으로 교체 필요
            uptime_seconds=uptime,
            performance_summary={
                'active_requests': stats['active_requests'],
                'error_rate_percent': stats['error_rate_percent'],
                'avg_response_time_ms': stats['avg_response_time_ms'],
                'throughput_per_minute': stats['throughput_per_minute']
            },
            anomalies_count=len(anomalies)
        )
        
    except Exception as e:
        app_logger.error(
            "헬스 체크 실행 중 오류 발생",
            category=LogCategory.SYSTEM,
            extra={'error': str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="헬스 체크를 수행할 수 없습니다."
        )


@router.get("/stats", response_model=PerformanceStatsResponse)
async def get_performance_stats():
    """
    성능 통계 조회 (임시로 인증 제거)
    실시간 API 성능 메트릭 제공
    """
    try:
        stats = performance_metrics.get_current_stats()
        
        app_logger.info(
            "성능 통계 조회",
            category=LogCategory.AUDIT,
            extra={
                'action': 'view_performance_stats'
            }
        )
        
        return PerformanceStatsResponse(**stats)
        
    except Exception as e:
        app_logger.error(
            "성능 통계 조회 중 오류 발생",
            category=LogCategory.SYSTEM,
            extra={
                'error': str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="성능 통계를 조회할 수 없습니다."
        )


@router.get("/endpoints", response_model=List[EndpointStatsResponse])
async def get_endpoint_stats(
    limit: int = Query(20, ge=1, le=100, description="조회할 엔드포인트 수"),
    sort_by: str = Query("count", description="정렬 기준 (count/error_count/avg_response_time)")
):
    """
    엔드포인트별 성능 통계 조회 (임시로 인증 제거)
    각 API 엔드포인트의 상세 성능 메트릭 제공
    """
    try:
        stats = performance_metrics.get_current_stats()
        endpoint_stats = stats.get('endpoint_stats', {})
        
        # 정렬 기준에 따라 데이터 정렬
        sort_key_map = {
            'count': lambda x: x[1]['count'],
            'error_count': lambda x: x[1]['error_count'],
            'avg_response_time': lambda x: x[1]['avg_response_time']
        }
        
        sort_key = sort_key_map.get(sort_by, sort_key_map['count'])
        sorted_endpoints = sorted(
            endpoint_stats.items(),
            key=sort_key,
            reverse=True
        )[:limit]
        
        # 응답 데이터 변환
        result = []
        for endpoint, data in sorted_endpoints:
            error_rate = (data['error_count'] / data['count'] * 100) if data['count'] > 0 else 0
            
            result.append(EndpointStatsResponse(
                endpoint=endpoint,
                count=data['count'],
                error_count=data['error_count'],
                error_rate_percent=round(error_rate, 2),
                avg_response_time_ms=round(data['avg_response_time'] * 1000, 2),
                min_response_time_ms=round(data['min_response_time'] * 1000, 2) if data['min_response_time'] != float('inf') else 0,
                max_response_time_ms=round(data['max_response_time'] * 1000, 2),
                last_error=data['last_error']
            ))
        
        app_logger.info(
            "엔드포인트 통계 조회",
            category=LogCategory.AUDIT,
            extra={
                'action': 'view_endpoint_stats',
                'sort_by': sort_by,
                'limit': limit
            }
        )
        
        return result
        
    except Exception as e:
        app_logger.error(
            "엔드포인트 통계 조회 중 오류 발생",
            category=LogCategory.SYSTEM,
            extra={
                'error': str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="엔드포인트 통계를 조회할 수 없습니다."
        )


@router.get("/errors", response_model=List[ErrorPatternResponse])
async def get_error_patterns(
    limit: int = Query(20, ge=1, le=100, description="조회할 에러 패턴 수")
):
    """
    에러 패턴 분석 조회 (임시로 인증 제거)
    반복되는 에러 패턴 및 빈도 분석 결과 제공
    """
    try:
        stats = performance_metrics.get_current_stats()
        top_errors = stats.get('top_errors', [])[:limit]
        
        result = [ErrorPatternResponse(**error) for error in top_errors]
        
        app_logger.info(
            "에러 패턴 조회",
            category=LogCategory.AUDIT,
            extra={
                'action': 'view_error_patterns',
                'limit': limit
            }
        )
        
        return result
        
    except Exception as e:
        app_logger.error(
            "에러 패턴 조회 중 오류 발생",
            category=LogCategory.SYSTEM,
            extra={
                'error': str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="에러 패턴을 조회할 수 없습니다."
        )


@router.get("/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies():
    """
    이상 징후 감지 결과 조회 (임시로 인증 제거)
    현재 감지된 성능 이상 징후 및 경고 사항 제공
    """
    try:
        anomalies = performance_metrics.detect_anomalies()
        result = [AnomalyResponse(**anomaly) for anomaly in anomalies]
        
        app_logger.info(
            "이상 징후 조회",
            category=LogCategory.AUDIT,
            extra={
                'action': 'view_anomalies',
                'anomalies_count': len(result)
            }
        )
        
        return result
        
    except Exception as e:
        app_logger.error(
            "이상 징후 조회 중 오류 발생",
            category=LogCategory.SYSTEM,
            extra={
                'error': str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="이상 징후를 조회할 수 없습니다."
        ) 