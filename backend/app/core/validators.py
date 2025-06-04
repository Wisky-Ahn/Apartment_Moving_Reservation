"""
고급 데이터 검증 시스템
보안 강화된 검증기 및 커스텀 검증 로직 구현
"""
import re
import html
import json
import ipaddress
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date, time, timedelta
from pydantic import validator, Field
from email_validator import validate_email, EmailNotValidError
import bleach
from urllib.parse import urlparse

from app.core.exceptions import ValidationException, ErrorCode
from app.core.logging import app_logger, LogCategory


class SecurityValidator:
    """보안 관련 검증기"""
    
    # XSS 방지용 허용 태그
    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    
    # SQL 인젝션 의심 패턴
    SQL_INJECTION_PATTERNS = [
        r'(\bunion\b.*\bselect\b)',
        r'(\bselect\b.*\bfrom\b)',
        r'(\binsert\b.*\binto\b)',
        r'(\bupdate\b.*\bset\b)',
        r'(\bdelete\b.*\bfrom\b)',
        r'(\bdrop\b.*\btable\b)',
        r'(\balter\b.*\btable\b)',
        r'(\bexec\b.*\()',
        r'(\bexecute\b.*\()',
        r'(\bcreate\b.*\btable\b)',
        r'(--|#|\/\*|\*\/)',
        r'(\bor\b.*=.*\bor\b)',
        r'(\band\b.*=.*\band\b)',
        r'([\'"]\s*;\s*)',
        r'(\bsleep\b\s*\()',
        r'(\bwaitfor\b\s+\bdelay\b)',
    ]
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """HTML 태그 정리 및 XSS 방지"""
        if not text:
            return text
        
        # HTML 엔티티 디코딩 후 허용된 태그만 남기기
        cleaned = bleach.clean(
            text,
            tags=SecurityValidator.ALLOWED_TAGS,
            attributes={},
            strip=True
        )
        
        return cleaned.strip()
    
    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """SQL 인젝션 패턴 검사"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                app_logger.log_security_event(
                    event="Potential SQL injection attempt detected",
                    severity="high",
                    pattern=pattern,
                    input_text=text[:100]  # 처음 100자만 로깅
                )
                return True
        
        return False
    
    @staticmethod
    def validate_safe_string(text: str, field_name: str = "입력값") -> str:
        """안전한 문자열 검증"""
        if not text:
            return text
        
        # SQL 인젝션 검사
        if SecurityValidator.check_sql_injection(text):
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=f"{field_name}에 허용되지 않는 문자가 포함되어 있습니다.",
                user_message="입력값에 특수 문자나 스크립트가 포함되어 있습니다.",
                details={"field": field_name, "reason": "sql_injection_detected"}
            )
        
        # HTML 정리
        cleaned = SecurityValidator.sanitize_html(text)
        
        # 길이 제한 (기본 10000자)
        if len(cleaned) > 10000:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=f"{field_name}이 너무 깁니다.",
                user_message="입력값이 허용된 길이를 초과했습니다.",
                details={"field": field_name, "max_length": 10000}
            )
        
        return cleaned


class BusinessRuleValidator:
    """비즈니스 로직 검증기"""
    
    @staticmethod
    def validate_korean_name(name: str) -> bool:
        """한국인 이름 형식 검증"""
        if not name:
            return False
        
        # 한글 이름: 2-5자, 공백 없음
        korean_pattern = r'^[가-힣]{2,5}$'
        
        # 영문 이름: 2-50자, 공백 허용
        english_pattern = r'^[a-zA-Z\s]{2,50}$'
        
        return bool(re.match(korean_pattern, name) or re.match(english_pattern, name))
    
    @staticmethod
    def validate_phone_number(phone: str) -> str:
        """전화번호 검증 및 정규화"""
        if not phone:
            return phone
        
        # 숫자만 추출
        digits = re.sub(r'[^0-9]', '', phone)
        
        # 한국 휴대폰 번호 패턴
        mobile_patterns = [
            r'^010[0-9]{8}$',  # 010-xxxx-xxxx
            r'^011[0-9]{7,8}$',  # 011-xxx-xxxx
            r'^016[0-9]{7,8}$',  # 016-xxx-xxxx
            r'^017[0-9]{7,8}$',  # 017-xxx-xxxx
            r'^018[0-9]{7,8}$',  # 018-xxx-xxxx
            r'^019[0-9]{7,8}$',  # 019-xxx-xxxx
        ]
        
        # 유효한 패턴 확인
        is_valid = any(re.match(pattern, digits) for pattern in mobile_patterns)
        
        if not is_valid:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="올바른 휴대폰 번호 형식이 아닙니다.",
                user_message="휴대폰 번호를 다시 확인해주세요. (예: 010-1234-5678)",
                details={"field": "phone", "format": "010-xxxx-xxxx"}
            )
        
        # 표준 형식으로 변환 (010-xxxx-xxxx)
        if digits.startswith('010'):
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        else:
            # 다른 통신사 번호 형식
            if len(digits) == 10:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            else:
                return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    
    @staticmethod
    def validate_apartment_number(apt_num: str) -> str:
        """아파트 동호수 검증 및 정규화"""
        if not apt_num:
            return apt_num
        
        # 동호수 패턴: 숫자동 숫자호 (공백 허용)
        pattern = r'^(\d{1,4})동\s*(\d{1,4})호$'
        match = re.match(pattern, apt_num.strip())
        
        if not match:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="올바른 아파트 동호수 형식이 아닙니다.",
                user_message="동호수를 올바른 형식으로 입력해주세요. (예: 101동 1001호)",
                details={"field": "apartment_number", "format": "XXX동 XXXX호"}
            )
        
        dong, ho = match.groups()
        
        # 범위 검증
        if not (1 <= int(dong) <= 999):
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="동 번호는 1-999 사이여야 합니다.",
                user_message="올바른 동 번호를 입력해주세요."
            )
        
        if not (1 <= int(ho) <= 9999):
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="호수는 1-9999 사이여야 합니다.",
                user_message="올바른 호수를 입력해주세요."
            )
        
        # 표준 형식으로 변환
        return f"{dong}동 {ho}호"
    
    @staticmethod
    def validate_reservation_time(start_time: datetime, end_time: datetime) -> None:
        """예약 시간 비즈니스 로직 검증"""
        now = datetime.now()
        
        # 1. 과거 시간 체크
        if start_time < now:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="과거 시간으로는 예약할 수 없습니다.",
                user_message="현재 시간 이후로 예약해주세요."
            )
        
        # 2. 너무 먼 미래 체크 (6개월)
        max_future = now + timedelta(days=180)
        if start_time > max_future:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="6개월 이후의 날짜는 예약할 수 없습니다.",
                user_message="6개월 이내의 날짜로 예약해주세요."
            )
        
        # 3. 영업시간 체크 (9:00 - 18:00)
        if start_time.hour < 9 or start_time.hour >= 18:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="영업시간(9:00-18:00) 내에서만 예약 가능합니다.",
                user_message="오전 9시부터 오후 6시 사이의 시간으로 예약해주세요."
            )
        
        if end_time.hour > 18:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="예약 종료 시간은 오후 6시를 넘을 수 없습니다.",
                user_message="오후 6시 이전에 예약이 종료되도록 해주세요."
            )
        
        # 4. 주말 체크
        if start_time.weekday() >= 5:  # 토요일(5), 일요일(6)
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="주말에는 예약할 수 없습니다.",
                user_message="평일(월-금)에만 예약 가능합니다."
            )
        
        # 5. 30분 단위 체크
        if start_time.minute not in [0, 30] or end_time.minute not in [0, 30]:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="예약은 30분 단위로만 가능합니다.",
                user_message="정시 또는 30분 단위로 예약해주세요. (예: 9:00, 9:30)"
            )
        
        # 6. 시간 순서 체크
        if end_time <= start_time:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="종료 시간은 시작 시간보다 늦어야 합니다.",
                user_message="종료 시간을 시작 시간보다 늦게 설정해주세요."
            )
        
        # 7. 최소/최대 시간 체크
        duration = end_time - start_time
        
        if duration < timedelta(hours=1):
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="최소 1시간 이상 예약해야 합니다.",
                user_message="최소 1시간 이상으로 예약해주세요."
            )
        
        if duration > timedelta(hours=8):
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="최대 8시간까지만 예약 가능합니다.",
                user_message="최대 8시간까지만 예약할 수 있습니다."
            )


class NetworkValidator:
    """네트워크 관련 검증기"""
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """IP 주소 형식 검증"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_url(url: str, allowed_schemes: List[str] = None) -> bool:
        """URL 형식 검증"""
        if not url:
            return False
        
        allowed_schemes = allowed_schemes or ['http', 'https']
        
        try:
            parsed = urlparse(url)
            return parsed.scheme in allowed_schemes and bool(parsed.netloc)
        except Exception:
            return False
    
    @staticmethod
    def validate_email_advanced(email: str) -> str:
        """고급 이메일 검증"""
        if not email:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="이메일 주소가 필요합니다.",
                user_message="이메일 주소를 입력해주세요."
            )
        
        try:
            # email-validator 라이브러리 사용
            valid_email = validate_email(email)
            normalized_email = valid_email.email
            
            # 금지된 도메인 체크
            forbidden_domains = [
                'tempmail.org', '10minutemail.com', 'guerrillamail.com',
                'mailinator.com', 'trashmail.com'
            ]
            
            domain = normalized_email.split('@')[1].lower()
            if domain in forbidden_domains:
                raise ValidationException(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="임시 이메일 주소는 사용할 수 없습니다.",
                    user_message="일반적인 이메일 서비스를 사용해주세요."
                )
            
            return normalized_email
            
        except EmailNotValidError as e:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=f"올바르지 않은 이메일 형식입니다: {str(e)}",
                user_message="올바른 이메일 주소를 입력해주세요."
            )


class DataTypeValidator:
    """데이터 타입 검증기"""
    
    @staticmethod
    def validate_json(data: str) -> Dict[str, Any]:
        """JSON 형식 검증"""
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=f"올바르지 않은 JSON 형식입니다: {str(e)}",
                user_message="올바른 JSON 형식으로 입력해주세요."
            )
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date, max_days: int = 365) -> None:
        """날짜 범위 검증"""
        if end_date < start_date:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="종료 날짜는 시작 날짜보다 늦어야 합니다.",
                user_message="날짜 범위를 다시 확인해주세요."
            )
        
        if (end_date - start_date).days > max_days:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=f"최대 {max_days}일 범위까지만 선택할 수 있습니다.",
                user_message=f"최대 {max_days}일 범위로 설정해주세요."
            )
    
    @staticmethod
    def validate_numeric_range(value: Union[int, float], min_val: Union[int, float] = None, 
                             max_val: Union[int, float] = None, field_name: str = "값") -> None:
        """숫자 범위 검증"""
        if min_val is not None and value < min_val:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=f"{field_name}은 {min_val} 이상이어야 합니다.",
                user_message=f"{field_name}을 {min_val} 이상으로 입력해주세요."
            )
        
        if max_val is not None and value > max_val:
            raise ValidationException(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=f"{field_name}은 {max_val} 이하여야 합니다.",
                user_message=f"{field_name}을 {max_val} 이하로 입력해주세요."
            )


class CompositeValidator:
    """복합 검증기 - 여러 검증을 조합"""
    
    def __init__(self):
        self.security = SecurityValidator()
        self.business = BusinessRuleValidator()
        self.network = NetworkValidator()
        self.datatype = DataTypeValidator()
    
    def validate_user_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 입력 통합 검증"""
        validated_data = {}
        
        for field, value in data.items():
            if value is None:
                validated_data[field] = value
                continue
            
            # 문자열 필드 보안 검증
            if isinstance(value, str):
                validated_data[field] = self.security.validate_safe_string(value, field)
            else:
                validated_data[field] = value
        
        # 특정 필드별 추가 검증
        if 'email' in validated_data and validated_data['email']:
            validated_data['email'] = self.network.validate_email_advanced(validated_data['email'])
        
        if 'phone' in validated_data and validated_data['phone']:
            validated_data['phone'] = self.business.validate_phone_number(validated_data['phone'])
        
        if 'apartment_number' in validated_data and validated_data['apartment_number']:
            validated_data['apartment_number'] = self.business.validate_apartment_number(validated_data['apartment_number'])
        
        if 'name' in validated_data and validated_data['name']:
            if not self.business.validate_korean_name(validated_data['name']):
                raise ValidationException(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="올바른 이름 형식이 아닙니다.",
                    user_message="한글 2-5자 또는 영문 2-50자로 입력해주세요."
                )
        
        return validated_data
    
    def validate_reservation_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """예약 입력 통합 검증"""
        validated_data = self.validate_user_input(data)
        
        # 예약 시간 검증
        if 'start_time' in validated_data and 'end_time' in validated_data:
            if validated_data['start_time'] and validated_data['end_time']:
                self.business.validate_reservation_time(
                    validated_data['start_time'],
                    validated_data['end_time']
                )
        
        return validated_data


# 전역 검증기 인스턴스
validator_instance = CompositeValidator()


def validate_request_data(data: Dict[str, Any], validation_type: str = "user") -> Dict[str, Any]:
    """요청 데이터 검증 메인 함수"""
    
    app_logger.info(
        f"Validating request data: {validation_type}",
        category=LogCategory.VALIDATION,
        validation_type=validation_type,
        field_count=len(data)
    )
    
    try:
        if validation_type == "user":
            return validator_instance.validate_user_input(data)
        elif validation_type == "reservation":
            return validator_instance.validate_reservation_input(data)
        else:
            return validator_instance.validate_user_input(data)
    
    except ValidationException as e:
        app_logger.log_validation_error(
            field=e.details.get('field', 'unknown') if e.details else 'unknown',
            value=str(data),
            error_message=e.message
        )
        raise
    except Exception as e:
        app_logger.error(
            f"Unexpected validation error: {str(e)}",
            category=LogCategory.VALIDATION,
            exc_info=True
        )
        raise ValidationException(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="검증 중 예상치 못한 오류가 발생했습니다.",
            user_message="잠시 후 다시 시도해주세요."
        ) 