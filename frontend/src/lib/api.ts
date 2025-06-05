/**
 * Axios 기반 HTTP 클라이언트 설정
 * FastAPI 백엔드와의 모든 API 통신을 담당
 * 강화된 에러 처리 시스템 적용
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { parseApiError, AppError, ErrorCode, errorLogger } from './errors';
import { toast } from './toast';
import { getSession } from 'next-auth/react';
import type { Session } from 'next-auth';

// API 기본 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// NextAuth Session 확장 타입
interface ExtendedSession extends Session {
  accessToken?: string;
}

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

// 전역 토큰 저장소
let currentAuthToken: string | null = null;

/**
 * 인증 토큰 설정 (컴포넌트에서 호출)
 */
export function setAuthToken(token: string | null) {
  currentAuthToken = token;
  console.log(`🔑 Auth token ${token ? 'set' : 'cleared'}`);
}

/**
 * 현재 인증 토큰 가져오기
 */
export function getCurrentAuthToken(): string | null {
  return currentAuthToken;
}

/**
 * 요청 인터셉터 - 토큰 추가 및 요청 로깅
 */
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // 요청 헤더가 없으면 초기화
    if (!config.headers) {
      config.headers = {} as any;
    }

    // NextAuth 세션에서 토큰 가져오기
    try {
      const session = await getSession() as ExtendedSession;
      if (session?.accessToken) {
        config.headers.Authorization = `Bearer ${session.accessToken}`;
        console.log(`🔑 Using NextAuth accessToken for request: ${config.url}`);
      } else {
        console.log(`⚠️ No NextAuth token available for request: ${config.url}`);
        
        // Fallback: 전역 토큰 저장소에서 가져오기
        const globalToken = getCurrentAuthToken();
        if (globalToken) {
          config.headers.Authorization = `Bearer ${globalToken}`;
          console.log(`🔑 Using global token for request: ${config.url}`);
        } else {
          // Last fallback: localStorage에서 토큰 가져오기
          const fallbackToken = localStorage.getItem('access_token');
          if (fallbackToken) {
            config.headers.Authorization = `Bearer ${fallbackToken}`;
            console.log(`🔑 Using localStorage token for request: ${config.url}`);
          } else {
            console.log(`❌ No token available for request: ${config.url}`);
          }
        }
      }
    } catch (error) {
      console.error('세션 가져오기 실패:', error);
      
      // NextAuth 실패 시 fallback 토큰 사용
      const globalToken = getCurrentAuthToken();
      if (globalToken) {
        config.headers.Authorization = `Bearer ${globalToken}`;
        console.log(`🔑 Using fallback global token for request: ${config.url}`);
      }
    }
    
    // 요청 ID 추가 (로깅용)
    const requestId = Math.random().toString(36).substr(2, 9);
    config.headers['X-Request-Id'] = requestId;
    
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
 * 사용자 타입 정의
 */
export interface User {
  id: number;
  username: string;
  email: string;
  name?: string;
  phone?: string;
  apartment_number?: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * 예약 타입 정의
 */
export interface Reservation {
  id: number;
  user_id: number;
  date: string;
  time: string;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  type: 'moving' | 'inspection' | 'maintenance';
  description?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 예약 생성 요청 타입
 */
export interface CreateReservationRequest {
  date: string;
  time: string;
  type: 'moving' | 'inspection' | 'maintenance';
  description?: string;
  notes?: string;
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

/**
 * 사용자 관련 API 함수들
 */
export const userApi = {
  /**
   * 현재 사용자 정보 조회
   */
  getCurrentUser: async (): Promise<ApiResponse<User>> => {
    try {
      const response = await apiClient.get('/api/users/me');
      return response.data;
    } catch (error) {
      console.error('사용자 정보 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 사용자 프로필 업데이트
   */
  updateProfile: async (userData: Partial<User>): Promise<ApiResponse<User>> => {
    try {
      const response = await apiClient.put('/api/users/me', userData);
      return response.data;
    } catch (error) {
      console.error('프로필 업데이트 실패:', error);
      throw error;
    }
  },
};

/**
 * 예약 관련 API 함수들
 */
export const reservationApi = {
  /**
   * 내 예약 목록 조회
   */
  getMyReservations: async (page: number = 1, size: number = 10): Promise<ApiResponse<PaginatedResponse<Reservation>>> => {
    try {
      const response = await apiClient.get('/api/reservations/my', {
        params: { page, size }
      });
      return response.data;
    } catch (error) {
      console.error('내 예약 목록 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 예약 상세 정보 조회
   */
  getReservationDetail: async (id: number): Promise<ApiResponse<Reservation>> => {
    try {
      const response = await apiClient.get(`/api/reservations/${id}`);
      return response.data;
    } catch (error) {
      console.error('예약 상세 정보 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 예약 생성
   */
  createReservation: async (reservationData: CreateReservationRequest): Promise<ApiResponse<Reservation>> => {
    try {
      const response = await apiClient.post('/api/reservations', reservationData);
      return response.data;
    } catch (error) {
      console.error('예약 생성 실패:', error);
      throw error;
    }
  },

  /**
   * 예약 수정
   */
  updateReservation: async (id: number, reservationData: Partial<CreateReservationRequest>): Promise<ApiResponse<Reservation>> => {
    try {
      const response = await apiClient.put(`/api/reservations/${id}`, reservationData);
      return response.data;
    } catch (error) {
      console.error('예약 수정 실패:', error);
      throw error;
    }
  },

  /**
   * 예약 취소
   */
  cancelReservation: async (id: number): Promise<ApiResponse<{ success: boolean }>> => {
    try {
      const response = await apiClient.delete(`/api/reservations/${id}`);
      return response.data;
    } catch (error) {
      console.error('예약 취소 실패:', error);
      throw error;
    }
  },
};

export default apiClient; 