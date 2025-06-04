/**
 * Axios 기반 HTTP 클라이언트 설정
 * FastAPI 백엔드와의 모든 API 통신을 담당
 * 강화된 에러 처리 시스템 적용
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { parseApiError, AppError, ErrorCode, errorLogger } from './errors';
import { toast } from './toast';

// API 기본 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Axios 인스턴스 생성 및 기본 설정
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30초 타임아웃
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

/**
 * 재시도 설정
 */
const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // 1초
  retryOn: [ErrorCode.NETWORK_ERROR, ErrorCode.TIMEOUT_ERROR, ErrorCode.CONNECTION_REFUSED]
};

/**
 * 네트워크 상태 감지
 */
let isOnline = typeof window !== 'undefined' ? window.navigator.onLine : true;

if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    isOnline = true;
    toast.success('네트워크 연결이 복원되었습니다.');
  });
  
  window.addEventListener('offline', () => {
    isOnline = false;
    toast.warning('네트워크 연결이 끊어졌습니다.');
  });
}

/**
 * 요청 인터셉터 - 모든 요청에 공통 설정 적용
 */
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig): any => {
    // 네트워크 상태 확인
    if (!isOnline) {
      return Promise.reject(new AppError(
        ErrorCode.NETWORK_ERROR,
        'No internet connection',
        '인터넷 연결을 확인해주세요.'
      ));
    }

    // JWT 토큰이 있는 경우 Authorization 헤더에 추가
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // 요청 ID 추가 (로깅용)
    const requestId = Math.random().toString(36).substr(2, 9);
    config.headers = { ...config.headers, 'X-Request-Id': requestId };
    
    console.log(`🚀 API Request [${requestId}]: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    const appError = parseApiError(error);
    errorLogger.log(appError, { context: 'request_interceptor' });
    return Promise.reject(appError);
  }
);

/**
 * 응답 인터셉터 - 응답 처리 및 에러 핸들링
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    const requestId = response.config.headers?.['X-Request-Id'];
    console.log(`✅ API Response [${requestId}]: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    const requestId = originalRequest?.headers?.['X-Request-Id'];

    // AppError로 변환
    const appError = parseApiError(error);
    
    // 로깅
    errorLogger.log(appError, { 
      context: 'response_interceptor',
      requestId,
      url: originalRequest?.url,
      method: originalRequest?.method
    });

    // 401 Unauthorized 처리 - 토큰 만료 시 로그아웃
    if (appError.statusCode === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // 토큰 제거 및 로그인 페이지로 리다이렉트
      tokenUtils.clearTokens();
      
      if (typeof window !== 'undefined') {
        toast.error('로그인이 만료되었습니다. 다시 로그인해주세요.');
        setTimeout(() => {
          window.location.href = '/login';
        }, 1000);
      }
    }

    // 자동 재시도 로직
    if (shouldRetry(appError, originalRequest)) {
      return retryRequest(originalRequest);
    }

    // 사용자에게 에러 표시 (특정 상황 제외)
    if (shouldShowErrorToUser(appError)) {
      toast.error(appError.userMessage);
    }

    console.error(`❌ API Error [${requestId}]:`, {
      code: appError.code,
      message: appError.message,
      userMessage: appError.userMessage,
      statusCode: appError.statusCode,
      url: originalRequest?.url,
    });

    return Promise.reject(appError);
  }
);

/**
 * 재시도 여부 결정
 */
function shouldRetry(error: AppError, originalRequest: any): boolean {
  if (originalRequest._retryCount >= RETRY_CONFIG.maxRetries) {
    return false;
  }
  
  return RETRY_CONFIG.retryOn.includes(error.code);
}

/**
 * 요청 재시도
 */
async function retryRequest(originalRequest: any): Promise<any> {
  originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;
  
  const delay = RETRY_CONFIG.retryDelay * originalRequest._retryCount;
  
  console.log(`🔄 Retrying request (${originalRequest._retryCount}/${RETRY_CONFIG.maxRetries}) in ${delay}ms`);
  
  await new Promise(resolve => setTimeout(resolve, delay));
  
  return apiClient(originalRequest);
}

/**
 * 사용자에게 에러를 표시할지 결정
 */
function shouldShowErrorToUser(error: AppError): boolean {
  // 401 에러는 이미 처리했으므로 표시하지 않음
  if (error.statusCode === 401) {
    return false;
  }
  
  // 네트워크 에러는 이미 이벤트 리스너에서 처리
  if (error.code === ErrorCode.NETWORK_ERROR) {
    return false;
  }
  
  return true;
}

/**
 * API 응답 타입 정의
 */
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
  success: boolean;
}

/**
 * 페이지네이션 응답 타입
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

/**
 * 강화된 API 메서드들
 */
export const api = {
  // GET 요청
  get: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await apiClient.get<T>(url, config);
      return response.data;
    } catch (error) {
      throw error instanceof AppError ? error : parseApiError(error);
    }
  },

  // POST 요청
  post: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await apiClient.post<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw error instanceof AppError ? error : parseApiError(error);
    }
  },

  // PUT 요청
  put: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await apiClient.put<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw error instanceof AppError ? error : parseApiError(error);
    }
  },

  // DELETE 요청
  delete: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await apiClient.delete<T>(url, config);
      return response.data;
    } catch (error) {
      throw error instanceof AppError ? error : parseApiError(error);
    }
  },

  // PATCH 요청
  patch: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await apiClient.patch<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw error instanceof AppError ? error : parseApiError(error);
    }
  },

  // 파일 업로드
  upload: async <T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post<T>(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      });
      return response.data;
    } catch (error) {
      throw error instanceof AppError ? error : parseApiError(error);
    }
  },

  // 병렬 요청
  parallel: async <T = any>(requests: Promise<T>[]): Promise<T[]> => {
    try {
      return await Promise.all(requests);
    } catch (error) {
      throw error instanceof AppError ? error : parseApiError(error);
    }
  },

  // 순차적 요청
  sequential: async <T = any>(requestFunctions: (() => Promise<T>)[]): Promise<T[]> => {
    const results: T[] = [];
    
    for (const requestFunction of requestFunctions) {
      try {
        const result = await requestFunction();
        results.push(result);
      } catch (error) {
        throw error instanceof AppError ? error : parseApiError(error);
      }
    }
    
    return results;
  },
};

/**
 * 토큰 관리 유틸리티 (강화됨)
 */
export const tokenUtils = {
  // 액세스 토큰 저장
  setAccessToken: (token: string) => {
    try {
      localStorage.setItem('access_token', token);
    } catch (error) {
      console.error('Failed to save access token:', error);
    }
  },

  // 리프레시 토큰 저장
  setRefreshToken: (token: string) => {
    try {
      localStorage.setItem('refresh_token', token);
    } catch (error) {
      console.error('Failed to save refresh token:', error);
    }
  },

  // 액세스 토큰 가져오기
  getAccessToken: (): string | null => {
    try {
      return localStorage.getItem('access_token');
    } catch (error) {
      console.error('Failed to get access token:', error);
      return null;
    }
  },

  // 리프레시 토큰 가져오기
  getRefreshToken: (): string | null => {
    try {
      return localStorage.getItem('refresh_token');
    } catch (error) {
      console.error('Failed to get refresh token:', error);
      return null;
    }
  },

  // 모든 토큰 제거
  clearTokens: () => {
    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } catch (error) {
      console.error('Failed to clear tokens:', error);
    }
  },

  // 토큰 유효성 검사 (간단한 형식 검사)
  isValidToken: (token: string): boolean => {
    if (!token) return false;
    
    try {
      // JWT 토큰의 기본 구조 검사 (3개 부분으로 나뉘어 있는지)
      const parts = token.split('.');
      return parts.length === 3;
    } catch {
      return false;
    }
  },
};

/**
 * API 상태 유틸리티
 */
export const apiStatus = {
  // 서버 상태 확인
  checkHealth: async (): Promise<boolean> => {
    try {
      await api.get('/health');
      return true;
    } catch {
      return false;
    }
  },

  // 네트워크 연결 상태
  isOnline: () => isOnline,

  // API 기본 URL
  getBaseUrl: () => API_BASE_URL,
};

export default apiClient; 