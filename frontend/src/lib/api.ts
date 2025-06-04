/**
 * Axios 기반 HTTP 클라이언트 설정
 * FastAPI 백엔드와의 모든 API 통신을 담당
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

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
 * 요청 인터셉터 - 모든 요청에 공통 설정 적용
 */
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig): any => {
    // JWT 토큰이 있는 경우 Authorization 헤더에 추가
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

/**
 * 응답 인터셉터 - 응답 처리 및 에러 핸들링
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // 401 Unauthorized 처리 - 토큰 만료 시 로그아웃
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // 토큰 제거 및 로그인 페이지로 리다이렉트
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }

    // 에러 로깅
    console.error('❌ API Error:', {
      status: error.response?.status,
      message: error.response?.data?.detail || error.message,
      url: error.config?.url,
    });

    return Promise.reject(error);
  }
);

/**
 * API 응답 타입 정의
 */
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
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
 * 공통 API 메서드들
 */
export const api = {
  // GET 요청
  get: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.get<T>(url, config);
    return response.data;
  },

  // POST 요청
  post: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.post<T>(url, data, config);
    return response.data;
  },

  // PUT 요청
  put: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.put<T>(url, data, config);
    return response.data;
  },

  // DELETE 요청
  delete: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.delete<T>(url, config);
    return response.data;
  },

  // PATCH 요청
  patch: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.patch<T>(url, data, config);
    return response.data;
  },
};

/**
 * 토큰 관리 유틸리티
 */
export const tokenUtils = {
  // 액세스 토큰 저장
  setAccessToken: (token: string) => {
    localStorage.setItem('access_token', token);
  },

  // 리프레시 토큰 저장
  setRefreshToken: (token: string) => {
    localStorage.setItem('refresh_token', token);
  },

  // 액세스 토큰 가져오기
  getAccessToken: (): string | null => {
    return localStorage.getItem('access_token');
  },

  // 리프레시 토큰 가져오기
  getRefreshToken: (): string | null => {
    return localStorage.getItem('refresh_token');
  },

  // 모든 토큰 제거
  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

export default apiClient; 