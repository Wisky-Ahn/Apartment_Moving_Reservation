/**
 * 프론트엔드 폼 검증 시스템
 * 백엔드 검증 규칙과 일치하는 클라이언트 측 검증
 */

import { AppError, ErrorCode } from './errors';

// 검증 결과 타입
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

// 검증 에러 타입
export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// 검증 규칙 타입
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | null;
  email?: boolean;
  phone?: boolean;
  apartmentNumber?: boolean;
  password?: boolean;
  dateRange?: { min?: Date; max?: Date };
  numeric?: boolean;
  min?: number;
  max?: number;
}

/**
 * 필드 검증 스키마 정의
 */
export interface ValidationSchema {
  [fieldName: string]: ValidationRule;
}

/**
 * 메인 검증 클래스
 */
export class FormValidator {
  private schema: ValidationSchema;
  private errors: ValidationError[] = [];

  constructor(schema: ValidationSchema) {
    this.schema = schema;
  }

  /**
   * 전체 폼 데이터 검증
   */
  validate(data: Record<string, any>): ValidationResult {
    this.errors = [];

    for (const [fieldName, rule] of Object.entries(this.schema)) {
      const value = data[fieldName];
      this.validateField(fieldName, value, rule);
    }

    return {
      isValid: this.errors.length === 0,
      errors: this.errors
    };
  }

  /**
   * 개별 필드 검증
   */
  validateField(fieldName: string, value: any, rule: ValidationRule): boolean {
    const fieldErrors: string[] = [];

    // 필수 필드 검증
    if (rule.required && this.isEmpty(value)) {
      fieldErrors.push('필수 항목입니다.');
    }

    // 값이 비어있고 필수가 아니면 다른 검증 스킵
    if (this.isEmpty(value) && !rule.required) {
      return true;
    }

    // 최소 길이 검증
    if (rule.minLength && value && value.length < rule.minLength) {
      fieldErrors.push(`최소 ${rule.minLength}자 이상 입력해주세요.`);
    }

    // 최대 길이 검증
    if (rule.maxLength && value && value.length > rule.maxLength) {
      fieldErrors.push(`최대 ${rule.maxLength}자까지 입력 가능합니다.`);
    }

    // 패턴 검증
    if (rule.pattern && value && !rule.pattern.test(value)) {
      fieldErrors.push('올바른 형식이 아닙니다.');
    }

    // 이메일 검증
    if (rule.email && value && !this.isValidEmail(value)) {
      fieldErrors.push('올바른 이메일 형식이 아닙니다.');
    }

    // 전화번호 검증
    if (rule.phone && value && !this.isValidPhone(value)) {
      fieldErrors.push('올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678)');
    }

    // 아파트 호수 검증
    if (rule.apartmentNumber && value && !this.isValidApartmentNumber(value)) {
      fieldErrors.push('올바른 아파트 호수 형식이 아닙니다. (예: 101동 1001호)');
    }

    // 비밀번호 복잡성 검증
    if (rule.password && value && !this.isValidPassword(value)) {
      fieldErrors.push('비밀번호는 8-100자, 대문자, 소문자, 숫자, 특수문자를 포함해야 합니다.');
    }

    // 숫자 검증
    if (rule.numeric && value !== undefined && value !== null && isNaN(Number(value))) {
      fieldErrors.push('숫자만 입력 가능합니다.');
    }

    // 최솟값 검증
    if (rule.min !== undefined && value !== undefined && Number(value) < rule.min) {
      fieldErrors.push(`${rule.min} 이상의 값을 입력해주세요.`);
    }

    // 최댓값 검증
    if (rule.max !== undefined && value !== undefined && Number(value) > rule.max) {
      fieldErrors.push(`${rule.max} 이하의 값을 입력해주세요.`);
    }

    // 날짜 범위 검증
    if (rule.dateRange && value) {
      const date = new Date(value);
      if (isNaN(date.getTime())) {
        fieldErrors.push('올바른 날짜 형식이 아닙니다.');
      } else {
        if (rule.dateRange.min && date < rule.dateRange.min) {
          fieldErrors.push(`${rule.dateRange.min.toLocaleDateString()} 이후 날짜를 선택해주세요.`);
        }
        if (rule.dateRange.max && date > rule.dateRange.max) {
          fieldErrors.push(`${rule.dateRange.max.toLocaleDateString()} 이전 날짜를 선택해주세요.`);
        }
      }
    }

    // 커스텀 검증
    if (rule.custom && value) {
      const customError = rule.custom(value);
      if (customError) {
        fieldErrors.push(customError);
      }
    }

    // 에러가 있으면 저장
    fieldErrors.forEach(message => {
      this.errors.push({
        field: fieldName,
        message,
        code: 'VALIDATION_ERROR'
      });
    });

    return fieldErrors.length === 0;
  }

  /**
   * 값이 비어있는지 확인
   */
  private isEmpty(value: any): boolean {
    return value === null || value === undefined || value === '' || 
           (Array.isArray(value) && value.length === 0);
  }

  /**
   * 이메일 형식 검증
   */
  private isValidEmail(email: string): boolean {
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailPattern.test(email);
  }

  /**
   * 전화번호 형식 검증 (한국 형식)
   */
  private isValidPhone(phone: string): boolean {
    const phonePattern = /^010-\d{4}-\d{4}$/;
    return phonePattern.test(phone);
  }

  /**
   * 아파트 호수 형식 검증
   */
  private isValidApartmentNumber(apartment: string): boolean {
    const apartmentPattern = /^\d{1,3}동 \d{1,4}호$/;
    return apartmentPattern.test(apartment);
  }

  /**
   * 비밀번호 복잡성 검증
   */
  private isValidPassword(password: string): boolean {
    if (password.length < 8 || password.length > 100) {
      return false;
    }

    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    return hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar;
  }

  /**
   * 특정 필드의 에러만 가져오기
   */
  getFieldErrors(fieldName: string): ValidationError[] {
    return this.errors.filter(error => error.field === fieldName);
  }

  /**
   * 모든 에러 메시지를 문자열 배열로 반환
   */
  getErrorMessages(): string[] {
    return this.errors.map(error => `${error.field}: ${error.message}`);
  }

  /**
   * 에러 초기화
   */
  clearErrors(): void {
    this.errors = [];
  }
}

/**
 * 미리 정의된 검증 스키마들
 */
export const ValidationSchemas = {
  // 사용자 등록 스키마
  userRegistration: {
    username: {
      required: true,
      minLength: 3,
      maxLength: 50,
      pattern: /^[a-zA-Z0-9_]+$/,
      custom: (value: string) => {
        const reserved = ['admin', 'root', 'system', 'guest', 'test'];
        if (reserved.includes(value.toLowerCase())) {
          return '사용할 수 없는 사용자명입니다.';
        }
        return null;
      }
    },
    email: {
      required: true,
      email: true,
      maxLength: 255
    },
    password: {
      required: true,
      password: true
    },
    name: {
      required: true,
      minLength: 2,
      maxLength: 100
    },
    phone: {
      required: true,
      phone: true
    },
    apartment_number: {
      required: true,
      apartmentNumber: true
    }
  },

  // 사용자 로그인 스키마
  userLogin: {
    username: {
      required: true,
      minLength: 3
    },
    password: {
      required: true,
      minLength: 1
    }
  },

  // 사용자 정보 수정 스키마
  userUpdate: {
    email: {
      email: true,
      maxLength: 255
    },
    name: {
      minLength: 2,
      maxLength: 100
    },
    phone: {
      phone: true
    },
    apartment_number: {
      apartmentNumber: true
    }
  },

  // 예약 생성 스키마
  reservationCreate: {
    reservation_date: {
      required: true,
      dateRange: {
        min: new Date(), // 오늘 이후만 가능
        max: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30일 후까지
      }
    },
    start_time: {
      required: true,
      pattern: /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/
    },
    end_time: {
      required: true,
      pattern: /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/
    },
    purpose: {
      required: true,
      minLength: 5,
      maxLength: 500
    }
  },

  // 공지사항 생성 스키마
  noticeCreate: {
    title: {
      required: true,
      minLength: 5,
      maxLength: 200
    },
    content: {
      required: true,
      minLength: 10,
      maxLength: 5000
    },
    notice_type: {
      required: true,
      custom: (value: string) => {
        const validTypes = ['일반', '긴급', '공지', '이벤트'];
        if (!validTypes.includes(value)) {
          return '올바른 공지사항 타입을 선택해주세요.';
        }
        return null;
      }
    }
  }
};

/**
 * 실시간 검증을 위한 디바운스된 검증 함수
 */
export function createDebouncedValidator(
  validator: FormValidator,
  delay: number = 300
): (fieldName: string, value: any, rule: ValidationRule) => Promise<boolean> {
  const timeouts = new Map<string, number>();

  return (fieldName: string, value: any, rule: ValidationRule): Promise<boolean> => {
    return new Promise((resolve) => {
      // 이전 타이머 제거
      const existingTimeout = timeouts.get(fieldName);
      if (existingTimeout) {
        clearTimeout(existingTimeout);
      }

      // 새 타이머 설정
      const timeoutId = window.setTimeout(() => {
        const isValid = validator.validateField(fieldName, value, rule);
        timeouts.delete(fieldName);
        resolve(isValid);
      }, delay);

      timeouts.set(fieldName, timeoutId);
    });
  };
}

/**
 * React Hook 스타일의 검증 유틸리티
 */
export function useFormValidation(schema: ValidationSchema) {
  let validator: FormValidator;
  let errors: Record<string, string[]> = {};

  const initValidator = () => {
    validator = new FormValidator(schema);
  };

  const validateForm = (data: Record<string, any>) => {
    if (!validator) initValidator();
    
    const result = validator.validate(data);
    
    // 필드별로 에러 그룹화
    errors = {};
    result.errors.forEach(error => {
      if (!errors[error.field]) {
        errors[error.field] = [];
      }
      errors[error.field].push(error.message);
    });

    return {
      isValid: result.isValid,
      errors,
      getFieldError: (fieldName: string) => errors[fieldName]?.[0] || null,
      hasFieldError: (fieldName: string) => Boolean(errors[fieldName]?.length)
    };
  };

  const validateField = (fieldName: string, value: any) => {
    if (!validator) initValidator();
    
    const rule = schema[fieldName];
    if (!rule) return { isValid: true, error: null };

    validator.clearErrors();
    const isValid = validator.validateField(fieldName, value, rule);
    const fieldErrors = validator.getFieldErrors(fieldName);

    return {
      isValid,
      error: fieldErrors[0]?.message || null
    };
  };

  return {
    validateForm,
    validateField,
    schemas: ValidationSchemas
  };
}

/**
 * 비즈니스 로직 검증 헬퍼들
 */
export const BusinessValidation = {
  // 예약 시간 검증
  validateReservationTime: (startTime: string, endTime: string): string | null => {
    const start = new Date(`1970-01-01T${startTime}:00`);
    const end = new Date(`1970-01-01T${endTime}:00`);

    if (start >= end) {
      return '종료 시간은 시작 시간보다 늦어야 합니다.';
    }

    const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
    if (diffHours > 4) {
      return '예약 시간은 최대 4시간까지 가능합니다.';
    }

    if (diffHours < 1) {
      return '예약 시간은 최소 1시간 이상이어야 합니다.';
    }

    return null;
  },

  // 근무 시간 검증
  validateWorkingHours: (time: string): string | null => {
    const timeDate = new Date(`1970-01-01T${time}:00`);
    const hour = timeDate.getHours();

    if (hour < 9 || hour >= 18) {
      return '예약 가능 시간은 09:00 ~ 18:00입니다.';
    }

    return null;
  },

  // 주말 예약 검증
  validateWeekend: (date: Date): string | null => {
    const dayOfWeek = date.getDay();
    if (dayOfWeek === 0 || dayOfWeek === 6) {
      return '주말에는 예약할 수 없습니다.';
    }
    return null;
  }
}; 