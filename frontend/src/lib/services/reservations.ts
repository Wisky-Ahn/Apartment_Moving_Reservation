/**
 * 예약 관련 API 서비스
 * FastAPI 백엔드의 예약 엔드포인트와 통신
 */
import { api, PaginatedResponse } from '../api';

// 예약 관련 타입 정의
export interface Reservation {
  id: number;
  user_id: number;
  reservation_type: 'elevator' | 'parking' | 'other';
  start_time: string;
  end_time: string;
  description?: string;
  status: 'pending' | 'approved' | 'rejected' | 'completed' | 'cancelled';
  admin_comment?: string;
  created_at: string;
  updated_at: string;
  user?: {
    id: number;
    username: string;
    name: string;
    apartment_number?: string;
  };
}

export interface CreateReservationRequest {
  reservation_type: 'elevator' | 'parking' | 'other';
  start_time: string;
  end_time: string;
  description?: string;
}

export interface UpdateReservationRequest {
  reservation_type?: 'elevator' | 'parking' | 'other';
  start_time?: string;
  end_time?: string;
  description?: string;
}

export interface ReservationFilters {
  status?: 'pending' | 'approved' | 'rejected' | 'completed' | 'cancelled';
  reservation_type?: 'elevator' | 'parking' | 'other';
  user_id?: number;
  start_date?: string;
  end_date?: string;
  page?: number;
  size?: number;
}

export interface AdminReservationAction {
  status: 'approved' | 'rejected';
  admin_comment?: string;
}

/**
 * 예약 서비스 클래스
 */
export class ReservationService {
  /**
   * 예약 생성
   */
  static async createReservation(reservationData: CreateReservationRequest): Promise<Reservation> {
    try {
      const response = await api.post<Reservation>('/api/reservations/', reservationData);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '예약 생성에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 예약 목록 조회 (페이지네이션 지원)
   */
  static async getReservations(filters: ReservationFilters = {}): Promise<PaginatedResponse<Reservation>> {
    try {
      const params = new URLSearchParams();
      
      // 필터 파라미터 추가
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });

      const response = await api.get<PaginatedResponse<Reservation>>(`/api/reservations/?${params.toString()}`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '예약 목록을 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 특정 예약 상세 조회
   */
  static async getReservation(reservationId: number): Promise<Reservation> {
    try {
      const response = await api.get<Reservation>(`/api/reservations/${reservationId}`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '예약 정보를 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 예약 정보 수정
   */
  static async updateReservation(reservationId: number, updateData: UpdateReservationRequest): Promise<Reservation> {
    try {
      const response = await api.put<Reservation>(`/api/reservations/${reservationId}`, updateData);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '예약 수정에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 예약 삭제
   */
  static async deleteReservation(reservationId: number): Promise<void> {
    try {
      await api.delete(`/api/reservations/${reservationId}`);
    } catch (error: any) {
      const message = error.response?.data?.detail || '예약 삭제에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 현재 사용자의 예약 목록 조회
   */
  static async getMyReservations(filters: Omit<ReservationFilters, 'user_id'> = {}): Promise<PaginatedResponse<Reservation>> {
    try {
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });

      const response = await api.get<PaginatedResponse<Reservation>>(`/api/reservations/my/?${params.toString()}`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '내 예약 목록을 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 예약 시간 충돌 검사 - 백엔드 엔드포인트와 맞춤
   */
  static async checkConflict(
    reservationType: 'elevator' | 'parking' | 'other',
    startTime: string,
    endTime: string,
    excludeReservationId?: number
  ): Promise<{ has_conflict: boolean; conflicting_reservations: Reservation[] }> {
    try {
      // 날짜와 시간 분리
      const startDate = new Date(startTime);
      const endDate = new Date(endTime);
      
      const params = new URLSearchParams({
        reservation_date: startDate.toISOString().split('T')[0], // YYYY-MM-DD 형식
        start_time: startDate.toTimeString().split(' ')[0].substring(0, 5), // HH:MM 형식
        end_time: endDate.toTimeString().split(' ')[0].substring(0, 5), // HH:MM 형식
        equipment_type: reservationType, // 백엔드에서 equipment_type으로 받음
      });

      if (excludeReservationId) {
        params.append('exclude_reservation_id', excludeReservationId.toString());
      }

      const response = await api.get<{ has_conflict: boolean; conflicting_reservations: Reservation[] }>(
        `/api/reservations/conflicts/check?${params.toString()}`
      );
      return response;
    } catch (error: any) {
      console.error('충돌 검사 오류:', error);
      // 충돌 검사 실패 시 안전하게 false 반환
      return { has_conflict: false, conflicting_reservations: [] };
    }
  }

  /**
   * 관리자: 예약 승인/거부
   */
  static async updateReservationStatus(reservationId: number, action: AdminReservationAction): Promise<Reservation> {
    try {
      const response = await api.post<Reservation>(`/api/reservations/${reservationId}/status`, action);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '예약 상태 변경에 실패했습니다.';
      throw new Error(message);
    }
  }

  /**
   * 관리자: 예약 승인
   */
  static async approveReservation(reservationId: number, adminComment?: string): Promise<Reservation> {
    return this.updateReservationStatus(reservationId, {
      status: 'approved',
      admin_comment: adminComment,
    });
  }

  /**
   * 관리자: 예약 거부
   */
  static async rejectReservation(reservationId: number, adminComment?: string): Promise<Reservation> {
    return this.updateReservationStatus(reservationId, {
      status: 'rejected',
      admin_comment: adminComment,
    });
  }

  /**
   * 예약 통계 조회 (관리자용)
   */
  static async getReservationStats(): Promise<{
    total: number;
    pending: number;
    approved: number;
    rejected: number;
    completed: number;
    cancelled: number;
    by_type: {
      elevator: number;
      parking: number;
      other: number;
    };
  }> {
    try {
      const response = await api.get('/api/reservations/stats');
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || '예약 통계를 가져올 수 없습니다.';
      throw new Error(message);
    }
  }

  /**
   * 호수당 예약 제한 검사 - 같은 호수에서 기존 예약이 있는지 확인
   */
  static async checkApartmentReservationLimit(): Promise<{ 
    has_existing_reservation: boolean; 
    existing_reservations: Reservation[] 
  }> {
    try {
      const response = await api.get<{ 
        has_existing_reservation: boolean; 
        existing_reservations: Reservation[] 
      }>('/api/reservations/check-apartment-limit');
      return response;
    } catch (error: any) {
      console.error('호수 예약 제한 검사 오류:', error);
      // 검사 실패 시 안전하게 제한 없음으로 반환
      return { has_existing_reservation: false, existing_reservations: [] };
    }
  }
}

export default ReservationService; 