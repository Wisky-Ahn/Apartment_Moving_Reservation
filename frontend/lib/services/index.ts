/**
 * API 서비스 총 집합
 * 모든 서비스를 하나의 파일에서 export
 */

// 서비스 클래스들 import
export { AuthService } from './auth';
export { ReservationService } from './reservations';
export { NoticeService } from './notices';

// 타입들 export
export type {
  // Auth 관련 타입
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
  UserUpdateRequest,
} from './auth';

export type {
  // Reservation 관련 타입
  Reservation,
  CreateReservationRequest,
  UpdateReservationRequest,
  ReservationFilters,
  AdminReservationAction,
} from './reservations';

export type {
  // Notice 관련 타입
  Notice,
  CreateNoticeRequest,
  UpdateNoticeRequest,
  NoticeFilters,
  NoticeStats,
} from './notices';

// 공통 API 클라이언트와 유틸리티들
export { api, tokenUtils } from '../api';
export type { ApiResponse, PaginatedResponse } from '../api'; 