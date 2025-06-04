/**
 * 프론트엔드 에러 처리 시스템
 * 백엔드 ErrorCode 시스템과 호환되는 클라이언트 측 에러 관리
 */

// 백엔드 ErrorCode와 매핑되는 에러 타입 정의
export enum ErrorCode {
  // 인증 관련 에러
  UNAUTHORIZED = "AUTH_001",
  INVALID_CREDENTIALS = "AUTH_002",
  TOKEN_EXPIRED = "AUTH_003",
  INSUFFICIENT_PERMISSIONS = "AUTH_004",
  ACCOUNT_DISABLED = "AUTH_005",
  ADMIN_APPROVAL_REQUIRED = "AUTH_006",
  
  // 사용자 관련 에러
  USER_NOT_FOUND = "USER_001",
  USER_ALREADY_EXISTS = "USER_002",
  INVALID_USER_DATA = "USER_003",
  USER_INACTIVE = "USER_004",
  APARTMENT_NUMBER_REQUIRED = "USER_005",
  
  // 예약 관련 에러
  RESERVATION_NOT_FOUND = "RESERVATION_001",
  RESERVATION_TIME_CONFLICT = "RESERVATION_002",
  INVALID_RESERVATION_TIME = "RESERVATION_003",
  RESERVATION_ALREADY_APPROVED = "RESERVATION_004",
  RESERVATION_CANCELLED = "RESERVATION_005",
  PAST_DATE_RESERVATION = "RESERVATION_006",
  MAX_RESERVATIONS_EXCEEDED = "RESERVATION_007",
  
  // 공지사항 관련 에러
  NOTICE_NOT_FOUND = "NOTICE_001",
  INVALID_NOTICE_TYPE = "NOTICE_002",
  NOTICE_ALREADY_PUBLISHED = "NOTICE_003",
  
  // 데이터 검증 에러
  VALIDATION_ERROR = "VALIDATION_001",
  MISSING_REQUIRED_FIELD = "VALIDATION_002",
  INVALID_DATA_FORMAT = "VALIDATION_003",
  INVALID_DATE_RANGE = "VALIDATION_004",
  
  // 일반적인 상태 코드
  NOT_FOUND = "GENERAL_001",
  DUPLICATE_VALUE = "GENERAL_002",
  OPERATION_FAILED = "GENERAL_003",
  BAD_REQUEST = "GENERAL_004",
  FORBIDDEN = "GENERAL_005",
  
  // 네트워크 관련 에러
  NETWORK_ERROR = "NETWORK_001",
  TIMEOUT_ERROR = "NETWORK_002",
  CONNECTION_REFUSED = "NETWORK_003",
}

// 백엔드 에러 응답 형식
export interface BackendErrorResponse {
  error_code: ErrorCode;
  message: string;
  user_message: string;
  details?: Record<string, any>;
  success: false;
}

// 클라이언트 측 에러 클래스
export class AppError extends Error {
  public readonly code: ErrorCode;
  public readonly userMessage: string;
  public readonly details: Record<string, any>;
  public readonly statusCode?: number;
  public readonly timestamp: string;

  constructor(
    code: ErrorCode,
    message: string,
    userMessage?: string,
    details: Record<string, any> = {},
    statusCode?: number
  ) {
    super(message);
    this.name = 'AppError';
    this.code = code;
    this.userMessage = userMessage || this.getDefaultUserMessage(code);
    this.details = details;
    this.statusCode = statusCode;
    this.timestamp = new Date().toISOString();

    // Error 스택 트레이스 설정
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AppError);
    }
  }

  /**
   * 에러 코드에 따른 기본 사용자 메시지 반환
   */
  private getDefaultUserMessage(code: ErrorCode): string {
    const messageMap: Record<ErrorCode, string> = {
      // 인증 관련
      [ErrorCode.UNAUTHORIZED]: "로그인이 필요합니다.",
      [ErrorCode.INVALID_CREDENTIALS]: "잘못된 사용자명 또는 비밀번호입니다.",
      [ErrorCode.TOKEN_EXPIRED]: "로그인이 만료되었습니다. 다시 로그인해주세요.",
      [ErrorCode.INSUFFICIENT_PERMISSIONS]: "이 작업을 수행할 권한이 없습니다.",
      [ErrorCode.ACCOUNT_DISABLED]: "계정이 비활성화되었습니다.",
      [ErrorCode.ADMIN_APPROVAL_REQUIRED]: "관리자 승인이 필요합니다.",
      
      // 사용자 관련
      [ErrorCode.USER_NOT_FOUND]: "사용자를 찾을 수 없습니다.",
      [ErrorCode.USER_ALREADY_EXISTS]: "이미 존재하는 사용자입니다.",
      [ErrorCode.INVALID_USER_DATA]: "올바르지 않은 사용자 정보입니다.",
      [ErrorCode.USER_INACTIVE]: "비활성화된 계정입니다.",
      [ErrorCode.APARTMENT_NUMBER_REQUIRED]: "아파트 호수가 필요합니다.",
      
      // 예약 관련
      [ErrorCode.RESERVATION_NOT_FOUND]: "예약을 찾을 수 없습니다.",
      [ErrorCode.RESERVATION_TIME_CONFLICT]: "선택한 시간에 다른 예약이 있습니다.",
      [ErrorCode.INVALID_RESERVATION_TIME]: "올바르지 않은 예약 시간입니다.",
      [ErrorCode.RESERVATION_ALREADY_APPROVED]: "이미 승인된 예약입니다.",
      [ErrorCode.RESERVATION_CANCELLED]: "취소된 예약입니다.",
      [ErrorCode.PAST_DATE_RESERVATION]: "과거 날짜는 예약할 수 없습니다.",
      [ErrorCode.MAX_RESERVATIONS_EXCEEDED]: "최대 예약 수를 초과했습니다.",
      
      // 공지사항 관련
      [ErrorCode.NOTICE_NOT_FOUND]: "공지사항을 찾을 수 없습니다.",
      [ErrorCode.INVALID_NOTICE_TYPE]: "올바르지 않은 공지사항 타입입니다.",
      [ErrorCode.NOTICE_ALREADY_PUBLISHED]: "이미 게시된 공지사항입니다.",
      
      // 검증 관련
      [ErrorCode.VALIDATION_ERROR]: "입력된 정보가 올바르지 않습니다.",
      [ErrorCode.MISSING_REQUIRED_FIELD]: "필수 항목이 누락되었습니다.",
      [ErrorCode.INVALID_DATA_FORMAT]: "데이터 형식이 올바르지 않습니다.",
      [ErrorCode.INVALID_DATE_RANGE]: "날짜 범위가 올바르지 않습니다.",
      
      // 일반
      [ErrorCode.NOT_FOUND]: "요청한 정보를 찾을 수 없습니다.",
      [ErrorCode.DUPLICATE_VALUE]: "이미 존재하는 값입니다.",
      [ErrorCode.OPERATION_FAILED]: "작업 처리에 실패했습니다.",
      [ErrorCode.BAD_REQUEST]: "잘못된 요청입니다.",
      [ErrorCode.FORBIDDEN]: "접근이 금지되었습니다.",
      
      // 네트워크
      [ErrorCode.NETWORK_ERROR]: "네트워크 연결에 문제가 있습니다.",
      [ErrorCode.TIMEOUT_ERROR]: "요청 시간이 초과되었습니다.",
      [ErrorCode.CONNECTION_REFUSED]: "서버에 연결할 수 없습니다.",
    };

    return messageMap[code] || "알 수 없는 오류가 발생했습니다.";
  }

  /**
   * JSON 형태로 에러 정보 반환
   */
  toJSON() {
    return {
      name: this.name,
      code: this.code,
      message: this.message,
      userMessage: this.userMessage,
      details: this.details,
      statusCode: this.statusCode,
      timestamp: this.timestamp,
      stack: this.stack
    };
  }
}

/**
 * HTTP 에러를 AppError로 변환하는 헬퍼 함수
 */
export function parseApiError(error: any): AppError {
  // 네트워크 에러 처리
  if (!error.response) {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return new AppError(
        ErrorCode.TIMEOUT_ERROR,
        `Request timeout: ${error.message}`,
        "요청 시간이 초과되었습니다. 다시 시도해주세요."
      );
    }
    
    if (error.code === 'ECONNREFUSED' || error.message?.includes('ECONNREFUSED')) {
      return new AppError(
        ErrorCode.CONNECTION_REFUSED,
        `Connection refused: ${error.message}`,
        "서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요."
      );
    }
    
    return new AppError(
      ErrorCode.NETWORK_ERROR,
      `Network error: ${error.message}`,
      "네트워크 연결에 문제가 있습니다."
    );
  }

  const response = error.response;
  const data = response?.data;

  // 백엔드에서 온 구조화된 에러 응답 처리
  if (data && typeof data === 'object' && 'error_code' in data) {
    const backendError = data as BackendErrorResponse;
    return new AppError(
      backendError.error_code,
      backendError.message,
      backendError.user_message,
      backendError.details || {},
      response.status
    );
  }

  // 레거시 에러 응답 처리 (detail 필드만 있는 경우)
  if (data && typeof data === 'object' && 'detail' in data) {
    return new AppError(
      mapStatusCodeToErrorCode(response.status),
      data.detail,
      undefined,
      {},
      response.status
    );
  }

  // 기본 HTTP 에러 처리
  return new AppError(
    mapStatusCodeToErrorCode(response.status),
    `HTTP ${response.status}: ${response.statusText}`,
    undefined,
    { originalError: error },
    response.status
  );
}

/**
 * HTTP 상태 코드를 ErrorCode로 매핑
 */
function mapStatusCodeToErrorCode(statusCode: number): ErrorCode {
  switch (statusCode) {
    case 400:
      return ErrorCode.BAD_REQUEST;
    case 401:
      return ErrorCode.UNAUTHORIZED;
    case 403:
      return ErrorCode.FORBIDDEN;
    case 404:
      return ErrorCode.NOT_FOUND;
    case 409:
      return ErrorCode.DUPLICATE_VALUE;
    case 422:
      return ErrorCode.VALIDATION_ERROR;
    case 500:
    default:
      return ErrorCode.OPERATION_FAILED;
  }
}

/**
 * 자주 사용되는 에러를 쉽게 생성하는 헬퍼 함수들
 */
export const ErrorHelpers = {
  unauthorized: (message?: string) => 
    new AppError(ErrorCode.UNAUTHORIZED, message || "Unauthorized access", "로그인이 필요합니다."),
  
  forbidden: (message?: string) => 
    new AppError(ErrorCode.FORBIDDEN, message || "Forbidden access", "접근 권한이 없습니다."),
  
  notFound: (resource?: string) => 
    new AppError(ErrorCode.NOT_FOUND, `${resource || 'Resource'} not found`, `${resource || '요청한 정보'}를 찾을 수 없습니다.`),
  
  validationError: (field?: string, message?: string) => 
    new AppError(
      ErrorCode.VALIDATION_ERROR, 
      message || "Validation error", 
      field ? `${field}이(가) 올바르지 않습니다.` : "입력된 정보가 올바르지 않습니다.",
      field ? { field } : {}
    ),
  
  networkError: (message?: string) => 
    new AppError(ErrorCode.NETWORK_ERROR, message || "Network error", "네트워크 연결에 문제가 있습니다."),
};

/**
 * 에러 로깅 유틸리티
 */
export class ErrorLogger {
  private static instance: ErrorLogger;

  static getInstance(): ErrorLogger {
    if (!ErrorLogger.instance) {
      ErrorLogger.instance = new ErrorLogger();
    }
    return ErrorLogger.instance;
  }

  /**
   * 에러를 콘솔과 외부 서비스에 로깅
   */
  log(error: AppError | Error, context?: Record<string, any>) {
    const errorInfo = {
      timestamp: new Date().toISOString(),
      error: error instanceof AppError ? error.toJSON() : {
        name: error.name,
        message: error.message,
        stack: error.stack
      },
      context: context || {},
      userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown'
    };

    // 콘솔 로깅
    console.error('Error logged:', errorInfo);

    // 프로덕션 환경에서는 외부 로깅 서비스로 전송
    if (process.env.NODE_ENV === 'production') {
      this.sendToExternalService(errorInfo);
    }
  }

  /**
   * 외부 로깅 서비스로 에러 전송 (향후 구현)
   */
  private sendToExternalService(errorInfo: any) {
    // TODO: Sentry, LogRocket 등의 서비스로 에러 전송
    // 현재는 콘솔에만 로깅
  }
}

export const errorLogger = ErrorLogger.getInstance(); 