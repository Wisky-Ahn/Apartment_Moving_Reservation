"""
API별 세밀한 검증 확장 기능
특정 엔드포인트에 대한 커스텀 검증 로직
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.core.validators import CompositeValidator
from app.core.exceptions import ValidationException, ErrorCode
from app.core.logging import app_logger, LogCategory
from app.crud.user import get_user_by_username, get_user_by_email
from app.crud.reservation import get_reservation_conflicts


class APIValidationExtensions:
    """API별 확장 검증 기능"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = CompositeValidator()
    
    def validate_user_registration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자 등록 특화 검증
        
        Args:
            data: 사용자 등록 데이터
            
        Returns:
            Dict[str, Any]: 검증된 데이터
            
        Raises:
            ValidationException: 검증 실패 시
        """
        app_logger.info(
            "Starting user registration validation",
            category=LogCategory.VALIDATION,
            username=data.get('username'),
            email=data.get('email')
        )
        
        # 기본 검증
        validated_data = self.validator.validate_user_input(data)
        
        # 사용자명 중복 검사
        if validated_data.get('username'):
            existing_user = get_user_by_username(self.db, validated_data['username'])
            if existing_user:
                raise ValidationException(
                    error_code=ErrorCode.DUPLICATE_VALUE,
                    message=f"사용자명이 이미 사용중입니다: {validated_data['username']}",
                    user_message="이미 사용중인 사용자명입니다. 다른 사용자명을 선택해주세요.",
                    details={"field": "username", "value": validated_data['username']}
                )
        
        # 이메일 중복 검사
        if validated_data.get('email'):
            existing_user = get_user_by_email(self.db, validated_data['email'])
            if existing_user:
                raise ValidationException(
                    error_code=ErrorCode.DUPLICATE_VALUE,
                    message=f"이메일이 이미 등록되어 있습니다: {validated_data['email']}",
                    user_message="이미 등록된 이메일 주소입니다. 다른 이메일을 사용해주세요.",
                    details={"field": "email", "value": validated_data['email']}
                )
        
        # 비밀번호 확인 매칭 검사 (confirm_password가 있는 경우)
        if 'confirm_password' in validated_data:
            if validated_data.get('password') != validated_data.get('confirm_password'):
                raise ValidationException(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="비밀번호와 비밀번호 확인이 일치하지 않습니다.",
                    user_message="비밀번호 확인란을 다시 확인해주세요.",
                    details={"field": "confirm_password"}
                )
            # confirm_password는 저장하지 않음
            del validated_data['confirm_password']
        
        app_logger.info(
            "User registration validation completed",
            category=LogCategory.VALIDATION,
            username=validated_data.get('username')
        )
        
        return validated_data
    
    def validate_user_login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자 로그인 특화 검증
        
        Args:
            data: 로그인 데이터
            
        Returns:
            Dict[str, Any]: 검증된 데이터
        """
        app_logger.info(
            "Starting user login validation",
            category=LogCategory.VALIDATION,
            username=data.get('username', 'unknown')
        )
        
        # 기본 검증
        validated_data = self.validator.validate_user_input(data)
        
        # 필수 필드 확인
        if not validated_data.get('username'):
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="사용자명 또는 이메일이 필요합니다.",
                user_message="사용자명 또는 이메일을 입력해주세요.",
                details={"field": "username"}
            )
        
        if not validated_data.get('password'):
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="비밀번호가 필요합니다.",
                user_message="비밀번호를 입력해주세요.",
                details={"field": "password"}
            )
        
        # 로그인 시도 횟수 제한 등은 보안 로직에서 처리
        
        return validated_data
    
    def validate_reservation_creation(self, data: Dict[str, Any], user_id: int = None) -> Dict[str, Any]:
        """
        예약 생성 특화 검증
        
        Args:
            data: 예약 데이터
            user_id: 예약자 ID
            
        Returns:
            Dict[str, Any]: 검증된 데이터
        """
        app_logger.info(
            "Starting reservation creation validation",
            category=LogCategory.VALIDATION,
            user_id=user_id,
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )
        
        # 기본 검증
        validated_data = self.validator.validate_reservation_input(data)
        
        # 시간 중복 검사 (데이터베이스 조회)
        if validated_data.get('start_time') and validated_data.get('end_time'):
            conflicts = get_reservation_conflicts(
                db=self.db,
                start_time=validated_data['start_time'],
                end_time=validated_data['end_time'],
                exclude_reservation_id=None
            )
            
            if conflicts:
                conflicting_times = [
                    f"{conflict.start_time.strftime('%Y-%m-%d %H:%M')} - {conflict.end_time.strftime('%H:%M')}"
                    for conflict in conflicts
                ]
                
                raise ValidationException(
                    error_code=ErrorCode.RESERVATION_TIME_CONFLICT,
                    message=f"선택한 시간대에 이미 예약이 있습니다: {', '.join(conflicting_times)}",
                    user_message="선택한 시간대에 다른 예약이 있습니다. 다른 시간을 선택해주세요.",
                    details={
                        "field": "time_slot",
                        "conflicts": conflicting_times,
                        "conflict_count": len(conflicts)
                    }
                )
        
        # 사용자별 예약 제한 검사 (예: 하루 최대 1건)
        if user_id and validated_data.get('start_time'):
            from app.crud.reservation import get_user_reservations_by_date
            
            reservation_date = validated_data['start_time'].date()
            existing_reservations = get_user_reservations_by_date(
                db=self.db,
                user_id=user_id,
                target_date=reservation_date
            )
            
            if existing_reservations:
                raise ValidationException(
                    error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                    message="하루에 최대 1건의 예약만 가능합니다.",
                    user_message="같은 날짜에 이미 예약이 있습니다. 다른 날짜를 선택해주세요.",
                    details={
                        "field": "reservation_date", 
                        "existing_count": len(existing_reservations)
                    }
                )
        
        app_logger.info(
            "Reservation creation validation completed",
            category=LogCategory.VALIDATION,
            user_id=user_id
        )
        
        return validated_data
    
    def validate_reservation_update(self, data: Dict[str, Any], reservation_id: int, user_id: int = None) -> Dict[str, Any]:
        """
        예약 수정 특화 검증
        
        Args:
            data: 수정할 예약 데이터
            reservation_id: 예약 ID
            user_id: 수정자 ID
            
        Returns:
            Dict[str, Any]: 검증된 데이터
        """
        app_logger.info(
            "Starting reservation update validation",
            category=LogCategory.VALIDATION,
            reservation_id=reservation_id,
            user_id=user_id
        )
        
        # 기본 검증
        validated_data = self.validator.validate_reservation_input(data)
        
        # 시간 변경이 있는 경우 중복 검사
        if validated_data.get('start_time') and validated_data.get('end_time'):
            conflicts = get_reservation_conflicts(
                db=self.db,
                start_time=validated_data['start_time'],
                end_time=validated_data['end_time'],
                exclude_reservation_id=reservation_id  # 자기 자신은 제외
            )
            
            if conflicts:
                conflicting_times = [
                    f"{conflict.start_time.strftime('%Y-%m-%d %H:%M')} - {conflict.end_time.strftime('%H:%M')}"
                    for conflict in conflicts
                ]
                
                raise ValidationException(
                    error_code=ErrorCode.RESERVATION_TIME_CONFLICT,
                    message=f"변경하려는 시간대에 다른 예약이 있습니다: {', '.join(conflicting_times)}",
                    user_message="변경하려는 시간대에 다른 예약이 있습니다. 다른 시간을 선택해주세요.",
                    details={
                        "field": "time_slot",
                        "conflicts": conflicting_times
                    }
                )
        
        # 예약 수정 제한 시간 검사 (예: 예약 1시간 전까지만 수정 가능)
        from app.crud.reservation import get_reservation
        
        existing_reservation = get_reservation(self.db, reservation_id)
        if existing_reservation:
            now = datetime.now()
            time_until_reservation = (existing_reservation.start_time - now).total_seconds() / 3600
            
            if time_until_reservation < 1:  # 1시간 미만
                raise ValidationException(
                    error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                    message="예약 시작 1시간 전까지만 수정 가능합니다.",
                    user_message="예약 시간이 임박하여 수정할 수 없습니다.",
                    details={"field": "modification_deadline"}
                )
        
        return validated_data
    
    def validate_notice_creation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        공지사항 생성 특화 검증
        
        Args:
            data: 공지사항 데이터
            
        Returns:
            Dict[str, Any]: 검증된 데이터
        """
        app_logger.info(
            "Starting notice creation validation",
            category=LogCategory.VALIDATION,
            title=data.get('title', 'unknown')[:50]
        )
        
        # 기본 검증
        validated_data = self.validator.validate_user_input(data)
        
        # 제목 길이 추가 검증
        if validated_data.get('title'):
            if len(validated_data['title']) < 5:
                raise ValidationException(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="공지사항 제목은 최소 5자 이상이어야 합니다.",
                    user_message="제목을 5자 이상 입력해주세요.",
                    details={"field": "title", "min_length": 5}
                )
            
            if len(validated_data['title']) > 200:
                raise ValidationException(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="공지사항 제목은 최대 200자까지 가능합니다.",
                    user_message="제목을 200자 이하로 입력해주세요.",
                    details={"field": "title", "max_length": 200}
                )
        
        # 내용 길이 검증
        if validated_data.get('content'):
            if len(validated_data['content']) < 10:
                raise ValidationException(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="공지사항 내용은 최소 10자 이상이어야 합니다.",
                    user_message="내용을 10자 이상 입력해주세요.",
                    details={"field": "content", "min_length": 10}
                )
        
        # 중요 공지사항 개수 제한 (예: 최대 5개)
        if validated_data.get('is_important'):
            from app.crud.notice import get_important_notices_count
            
            important_count = get_important_notices_count(self.db)
            if important_count >= 5:
                raise ValidationException(
                    error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                    message="중요 공지사항은 최대 5개까지만 설정할 수 있습니다.",
                    user_message="중요 공지사항이 이미 5개입니다. 기존 중요 공지를 해제하고 다시 시도해주세요.",
                    details={"field": "is_important", "current_count": important_count, "max_count": 5}
                )
        
        return validated_data
    
    def validate_admin_operation(self, data: Dict[str, Any], operation: str) -> Dict[str, Any]:
        """
        관리자 작업 특화 검증
        
        Args:
            data: 작업 데이터
            operation: 작업 유형 (approve, reject, delete, etc.)
            
        Returns:
            Dict[str, Any]: 검증된 데이터
        """
        app_logger.info(
            "Starting admin operation validation",
            category=LogCategory.VALIDATION,
            operation=operation
        )
        
        # 기본 검증
        validated_data = self.validator.validate_user_input(data)
        
        # 작업별 추가 검증
        if operation == "reject" and not validated_data.get('reason'):
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="거부 사유가 필요합니다.",
                user_message="거부 사유를 입력해주세요.",
                details={"field": "reason", "operation": operation}
            )
        
        if operation in ["bulk_delete", "bulk_approve"] and not validated_data.get('target_ids'):
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="대상 ID 목록이 필요합니다.",
                user_message="작업할 대상을 선택해주세요.",
                details={"field": "target_ids", "operation": operation}
            )
        
        # 대량 작업 제한 (한 번에 최대 50개)
        if operation.startswith('bulk_'):
            target_ids = validated_data.get('target_ids', [])
            if len(target_ids) > 50:
                raise ValidationException(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="한 번에 최대 50개까지만 처리할 수 있습니다.",
                    user_message="선택된 항목이 너무 많습니다. 50개 이하로 선택해주세요.",
                    details={"field": "target_ids", "count": len(target_ids), "max_count": 50}
                )
        
        return validated_data


def get_api_validator(db: Session) -> APIValidationExtensions:
    """API 검증 확장 인스턴스 반환"""
    return APIValidationExtensions(db) 