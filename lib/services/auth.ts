/**
 * 사용자 인증 관련 API 서비스
 * FastAPI 백엔드의 사용자 인증 엔드포인트와 통신
 */
import { api, tokenUtils } from '../api';

// 인증 관련 타입 정의
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  name: string;
  phone?: string;
  apartment_number?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  name: string;
  phone?: string;
  apartment_number?: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserUpdateRequest {
  email?: string;
  name?: string;
  phone?: string;
  apartment_number?: string;
}

/**
 * 인증 서비스 클래스
 */
export class AuthService {
  /**
   * 사용자 로그인
   */
  static async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      // FormData로 전송 (FastAPI OAuth2PasswordRequestForm 형식)
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await api.post<LoginResponse>('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      // 토큰 저장
      if (response.access_token) {
        tokenUtils.setAccessToken(response.access_token);
        tokenUtils.setRefreshToken(response.refresh_token);
      }

      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '로그인에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 사용자 회원가입
   */
  static async register(userData: RegisterRequest): Promise<User> {
    try {
      const response = await api.post<User>('/auth/register', userData);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '회원가입에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 사용자 로그아웃
   */
  static async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.warn('로그아웃 API 호출 실패:', error);
    } finally {
      // 토큰 제거
      tokenUtils.clearTokens();
    }
  }

  /**
   * 현재 사용자 정보 조회
   */
  static async getCurrentUser(): Promise<User> {
    try {
      const response = await api.get<User>('/auth/me');
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '사용자 정보를 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 사용자 정보 업데이트
   */
  static async updateUser(userId: number, userData: UserUpdateRequest): Promise<User> {
    try {
      const response = await api.put<User>(`/users/${userId}`, userData);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '사용자 정보 업데이트에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 비밀번호 변경
   */
  static async changePassword(userId: number, currentPassword: string, newPassword: string): Promise<void> {
    try {
      await api.post(`/users/${userId}/change-password`, {
        current_password: currentPassword,
        new_password: newPassword,
      });
    } catch (error: any) {
      const message = error.response?.data?.detail || '비밀번호 변경에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 액세스 토큰 갱신
   */
  static async refreshToken(): Promise<string> {
    try {
      const refreshToken = tokenUtils.getRefreshToken();
      if (!refreshToken) {
        throw new Error('리프레시 토큰이 없습니다.');
      }

      const response = await api.post<{ access_token: string }>('/auth/refresh', {
        refresh_token: refreshToken,
      });

      // 새로운 액세스 토큰 저장
      tokenUtils.setAccessToken(response.access_token);
      return response.access_token;
    } catch (error: any) {
      // 리프레시 실패 시 모든 토큰 제거
      tokenUtils.clearTokens();
      const message = error.response?.data?.detail || '토큰 갱신에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 로그인 상태 확인
   */
  static isAuthenticated(): boolean {
    return !!tokenUtils.getAccessToken();
  }
}

export default AuthService; 