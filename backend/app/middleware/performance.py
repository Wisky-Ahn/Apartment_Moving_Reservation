"""
API 성능 모니터링 미들웨어
요청별 성능 메트릭 수집 및 에러 패턴 분석
"""
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock
import asyncio
import json

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import app_logger, LogCategory
from app.core.exceptions import AppException


class PerformanceMetrics:
    """성능 메트릭 데이터 클래스"""
    
    def __init__(self):
        self._lock = Lock()
        # 최근 1시간 데이터 저장 (메모리 기반)
        self.metrics_window = deque(maxlen=3600)  # 1시간 = 3600초
        
        # 실시간 통계
        self.active_requests = 0
        self.total_requests = 0
        self.total_errors = 0
        
        # 엔드포인트별 통계
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'error_count': 0,
            'avg_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0,
            'last_error': None
        })
        
        # 에러 패턴 분석
        self.error_patterns = defaultdict(lambda: {
            'count': 0,
            'recent_occurrences': deque(maxlen=10),
            'first_seen': None,
            'last_seen': None
        })

    def add_metric(self, metric_data: Dict[str, Any]) -> None:
        """메트릭 데이터 추가"""
        with self._lock:
            current_time = datetime.now()
            metric_data['timestamp'] = current_time
            
            # 시간 윈도우에 추가
            self.metrics_window.append(metric_data)
            
            # 전체 통계 업데이트
            self.total_requests += 1
            if metric_data.get('status_code', 200) >= 400:
                self.total_errors += 1
            
            # 엔드포인트별 통계 업데이트
            endpoint = metric_data.get('endpoint', 'unknown')
            stats = self.endpoint_stats[endpoint]
            
            stats['count'] += 1
            response_time = metric_data.get('response_time', 0)
            stats['total_time'] += response_time
            stats['avg_response_time'] = stats['total_time'] / stats['count']
            stats['min_response_time'] = min(stats['min_response_time'], response_time)
            stats['max_response_time'] = max(stats['max_response_time'], response_time)
            
            if metric_data.get('status_code', 200) >= 400:
                stats['error_count'] += 1
                stats['last_error'] = {
                    'timestamp': current_time,
                    'status_code': metric_data.get('status_code'),
                    'error_message': metric_data.get('error_message')
                }
                
                # 에러 패턴 분석
                error_key = f"{endpoint}:{metric_data.get('status_code')}"
                pattern = self.error_patterns[error_key]
                pattern['count'] += 1
                pattern['recent_occurrences'].append(current_time)
                
                if pattern['first_seen'] is None:
                    pattern['first_seen'] = current_time
                pattern['last_seen'] = current_time

    def get_current_stats(self) -> Dict[str, Any]:
        """현재 통계 반환"""
        with self._lock:
            current_time = datetime.now()
            one_hour_ago = current_time - timedelta(hours=1)
            
            # 최근 1시간 데이터 필터링
            recent_metrics = [
                m for m in self.metrics_window 
                if m['timestamp'] > one_hour_ago
            ]
            
            if not recent_metrics:
                return self._empty_stats()
            
            # 응답 시간 통계
            response_times = [m['response_time'] for m in recent_metrics]
            avg_response_time = sum(response_times) / len(response_times)
            
            # 에러율 계산
            error_count = len([m for m in recent_metrics if m.get('status_code', 200) >= 400])
            error_rate = (error_count / len(recent_metrics)) * 100 if recent_metrics else 0
            
            # 처리량 계산 (요청/분)
            throughput = len(recent_metrics) / 60  # 최근 1시간 / 60분
            
            return {
                'timestamp': current_time.isoformat(),
                'active_requests': self.active_requests,
                'total_requests_hour': len(recent_metrics),
                'total_requests_all': self.total_requests,
                'error_count_hour': error_count,
                'error_rate_percent': round(error_rate, 2),
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'min_response_time_ms': round(min(response_times) * 1000, 2),
                'max_response_time_ms': round(max(response_times) * 1000, 2),
                'throughput_per_minute': round(throughput, 2),
                'endpoint_stats': dict(self.endpoint_stats),
                'top_errors': self._get_top_errors()
            }

    def _empty_stats(self) -> Dict[str, Any]:
        """빈 통계 데이터 반환"""
        return {
            'timestamp': datetime.now().isoformat(),
            'active_requests': 0,
            'total_requests_hour': 0,
            'total_requests_all': 0,
            'error_count_hour': 0,
            'error_rate_percent': 0,
            'avg_response_time_ms': 0,
            'min_response_time_ms': 0,
            'max_response_time_ms': 0,
            'throughput_per_minute': 0,
            'endpoint_stats': {},
            'top_errors': []
        }

    def _get_top_errors(self, limit: int = 10) -> list:
        """상위 에러 패턴 반환"""
        sorted_errors = sorted(
            self.error_patterns.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        return [
            {
                'error_key': error_key,
                'count': data['count'],
                'first_seen': data['first_seen'].isoformat() if data['first_seen'] else None,
                'last_seen': data['last_seen'].isoformat() if data['last_seen'] else None,
                'recent_frequency': len([
                    occ for occ in data['recent_occurrences']
                    if occ > datetime.now() - timedelta(minutes=30)
                ])
            }
            for error_key, data in sorted_errors[:limit]
        ]

    def detect_anomalies(self) -> list:
        """성능 이상 징후 감지"""
        anomalies = []
        
        with self._lock:
            current_time = datetime.now()
            
            # 1. 높은 에러율 감지 (30% 이상)
            recent_metrics = [
                m for m in self.metrics_window 
                if m['timestamp'] > current_time - timedelta(minutes=10)
            ]
            
            if recent_metrics:
                error_count = len([m for m in recent_metrics if m.get('status_code', 200) >= 400])
                error_rate = (error_count / len(recent_metrics)) * 100
                
                if error_rate > 30:
                    anomalies.append({
                        'type': 'high_error_rate',
                        'severity': 'critical',
                        'value': error_rate,
                        'message': f'에러율이 {error_rate:.1f}%로 임계치(30%)를 초과했습니다.',
                        'timestamp': current_time.isoformat()
                    })
            
            # 2. 느린 응답 시간 감지 (평균 > 2초)
            if recent_metrics:
                avg_time = sum(m['response_time'] for m in recent_metrics) / len(recent_metrics)
                if avg_time > 2.0:
                    anomalies.append({
                        'type': 'slow_response',
                        'severity': 'warning',
                        'value': avg_time * 1000,
                        'message': f'평균 응답 시간이 {avg_time*1000:.0f}ms로 임계치(2초)를 초과했습니다.',
                        'timestamp': current_time.isoformat()
                    })
            
            # 3. 반복되는 에러 패턴 감지
            for error_key, pattern in self.error_patterns.items():
                recent_count = len([
                    occ for occ in pattern['recent_occurrences']
                    if occ > current_time - timedelta(minutes=5)
                ])
                
                if recent_count >= 5:  # 5분 내 5회 이상
                    anomalies.append({
                        'type': 'repeated_error',
                        'severity': 'warning',
                        'value': recent_count,
                        'message': f'{error_key} 에러가 5분 내 {recent_count}회 발생했습니다.',
                        'timestamp': current_time.isoformat(),
                        'error_key': error_key
                    })
        
        return anomalies


# 전역 메트릭 인스턴스
performance_metrics = PerformanceMetrics()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """API 성능 모니터링 미들웨어"""
    
    def __init__(self, app: ASGIApp, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/docs', '/redoc', '/openapi.json', '/favicon.ico']

    async def dispatch(self, request: Request, call_next) -> Response:
        """요청 처리 및 메트릭 수집"""
        
        # 제외할 경로 체크
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # 요청 시작 시간 기록
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # 활성 요청 수 증가
        performance_metrics.active_requests += 1
        
        try:
            # 요청 정보 로깅
            app_logger.info(
                "API 요청 시작",
                category=LogCategory.API,
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'url': str(request.url),
                    'user_agent': request.headers.get('user-agent'),
                    'client_ip': request.client.host if request.client else None
                }
            )
            
            # 요청 처리
            response = await call_next(request)
            
            # 응답 시간 계산
            end_time = time.time()
            response_time = end_time - start_time
            
            # 메트릭 데이터 수집
            metric_data = {
                'request_id': request_id,
                'method': request.method,
                'endpoint': request.url.path,
                'status_code': response.status_code,
                'response_time': response_time,
                'user_agent': request.headers.get('user-agent'),
                'client_ip': request.client.host if request.client else None,
                'success': response.status_code < 400
            }
            
            # 에러인 경우 추가 정보 수집
            if response.status_code >= 400:
                try:
                    if hasattr(response, 'body'):
                        body = response.body.decode('utf-8')
                        response_data = json.loads(body)
                        metric_data['error_message'] = response_data.get('message', 'Unknown error')
                        metric_data['error_code'] = response_data.get('error_code')
                except:
                    metric_data['error_message'] = f'HTTP {response.status_code}'
            
            # 메트릭 추가
            performance_metrics.add_metric(metric_data)
            
            # 성공 로깅
            app_logger.info(
                f"API 요청 완료: {request.method} {request.url.path}",
                category=LogCategory.API,
                extra={
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'response_time_ms': round(response_time * 1000, 2),
                    'success': response.status_code < 400
                }
            )
            
            return response
            
        except Exception as e:
            # 예외 발생 시 처리
            end_time = time.time()
            response_time = end_time - start_time
            
            # 에러 메트릭 수집
            metric_data = {
                'request_id': request_id,
                'method': request.method,
                'endpoint': request.url.path,
                'status_code': 500,
                'response_time': response_time,
                'user_agent': request.headers.get('user-agent'),
                'client_ip': request.client.host if request.client else None,
                'success': False,
                'error_message': str(e),
                'exception_type': type(e).__name__
            }
            
            performance_metrics.add_metric(metric_data)
            
            # 에러 로깅
            app_logger.error(
                f"API 요청 에러: {request.method} {request.url.path}",
                category=LogCategory.API,
                extra={
                    'request_id': request_id,
                    'error': str(e),
                    'exception_type': type(e).__name__,
                    'response_time_ms': round(response_time * 1000, 2)
                },
                exc_info=True
            )
            
            # 예외를 다시 발생시켜 전역 예외 핸들러가 처리하도록 함
            raise
            
        finally:
            # 활성 요청 수 감소
            performance_metrics.active_requests -= 1


def setup_performance_monitoring(app: FastAPI) -> None:
    """성능 모니터링 미들웨어 설정"""
    app.add_middleware(
        PerformanceMiddleware,
        exclude_paths=['/docs', '/redoc', '/openapi.json', '/favicon.ico', '/metrics']
    )
    
    app_logger.info(
        "성능 모니터링 미들웨어가 설정되었습니다.",
        category=LogCategory.SYSTEM
    ) 