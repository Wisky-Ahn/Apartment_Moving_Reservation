/**
 * 공지사항 관련 API 서비스
 * FastAPI 백엔드의 공지사항 엔드포인트와 통신
 */
import { api, PaginatedResponse } from '../api';

// 공지사항 관련 타입 정의
export interface Notice {
  id: number;
  title: string;
  content: string;
  notice_type: 'general' | 'announcement' | 'event';
  is_pinned: boolean;
  is_important: boolean;
  is_active: boolean;
  view_count: number;
  author_id: number;
  created_at: string;
  updated_at: string;
  author?: {
    id: number;
    username: string;
    name: string;
  };
}

export interface CreateNoticeRequest {
  title: string;
  content: string;
  notice_type: 'general' | 'announcement' | 'event';
  is_pinned?: boolean;
  is_important?: boolean;
  is_active?: boolean;
}

export interface UpdateNoticeRequest {
  title?: string;
  content?: string;
  notice_type?: 'general' | 'announcement' | 'event';
  is_pinned?: boolean;
  is_important?: boolean;
  is_active?: boolean;
}

export interface NoticeFilters {
  notice_type?: 'general' | 'announcement' | 'event';
  is_pinned?: boolean;
  is_important?: boolean;
  is_active?: boolean;
  search?: string;
  page?: number;
  size?: number;
}

export interface NoticeStats {
  total: number;
  active: number;
  pinned: number;
  important: number;
  by_type: {
    general: number;
    announcement: number;
    event: number;
  };
  total_views: number;
}

/**
 * 공지사항 서비스 클래스
 */
export class NoticeService {
  /**
   * 공지사항 생성 (관리자만)
   */
  static async createNotice(noticeData: CreateNoticeRequest): Promise<Notice> {
    try {
      const response = await api.post<Notice>('/notices/', noticeData);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항 생성에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 공지사항 목록 조회 (페이지네이션 지원)
   */
  static async getNotices(filters: NoticeFilters = {}): Promise<PaginatedResponse<Notice>> {
    try {
      const params = new URLSearchParams();
      
      // 필터 파라미터 추가
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });

      const response = await api.get<PaginatedResponse<Notice>>(`/notices/?${params.toString()}`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항 목록을 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 특정 공지사항 상세 조회 (조회수 자동 증가)
   */
  static async getNotice(noticeId: number): Promise<Notice> {
    try {
      const response = await api.get<Notice>(`/notices/${noticeId}`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항을 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 공지사항 수정 (관리자만)
   */
  static async updateNotice(noticeId: number, updateData: UpdateNoticeRequest): Promise<Notice> {
    try {
      const response = await api.put<Notice>(`/notices/${noticeId}`, updateData);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항 수정에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 공지사항 삭제 (관리자만)
   */
  static async deleteNotice(noticeId: number): Promise<void> {
    try {
      await api.delete(`/notices/${noticeId}`);
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항 삭제에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 고정 공지사항 목록 조회
   */
  static async getPinnedNotices(): Promise<Notice[]> {
    try {
      const response = await api.get<Notice[]>('/notices/pinned');
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '고정 공지사항을 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 중요 공지사항 목록 조회
   */
  static async getImportantNotices(): Promise<Notice[]> {
    try {
      const response = await api.get<Notice[]>('/notices/important');
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '중요 공지사항을 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 유형별 공지사항 조회
   */
  static async getNoticesByType(noticeType: 'general' | 'announcement' | 'event', page: number = 1, size: number = 10): Promise<PaginatedResponse<Notice>> {
    try {
      const response = await api.get<PaginatedResponse<Notice>>(`/notices/type/${noticeType}?page=${page}&size=${size}`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항을 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 공지사항 검색
   */
  static async searchNotices(query: string, page: number = 1, size: number = 10): Promise<PaginatedResponse<Notice>> {
    try {
      const params = new URLSearchParams({
        search: query,
        page: page.toString(),
        size: size.toString(),
      });

      const response = await api.get<PaginatedResponse<Notice>>(`/notices/search?${params.toString()}`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항 검색에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 공지사항 고정 상태 토글 (관리자만)
   */
  static async togglePinned(noticeId: number): Promise<Notice> {
    try {
      const response = await api.post<Notice>(`/notices/${noticeId}/toggle-pinned`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항 고정 상태 변경에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 공지사항 활성화 상태 토글 (관리자만)
   */
  static async toggleActive(noticeId: number): Promise<Notice> {
    try {
      const response = await api.post<Notice>(`/notices/${noticeId}/toggle-active`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항 활성화 상태 변경에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 공지사항 중요도 상태 토글 (관리자만)
   */
  static async toggleImportant(noticeId: number): Promise<Notice> {
    try {
      const response = await api.post<Notice>(`/notices/${noticeId}/toggle-important`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항 중요도 상태 변경에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 공지사항 통계 조회 (관리자용)
   */
  static async getNoticeStats(): Promise<NoticeStats> {
    try {
      const response = await api.get<NoticeStats>('/notices/stats');
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '공지사항 통계를 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 최근 공지사항 조회 (홈페이지용)
   */
  static async getRecentNotices(limit: number = 5): Promise<Notice[]> {
    try {
      const response = await api.get<Notice[]>(`/notices/recent?limit=${limit}`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '최근 공지사항을 가져올 수 없습니다.';
      throw new Error(message);
    }
  }
}

export default NoticeService; 