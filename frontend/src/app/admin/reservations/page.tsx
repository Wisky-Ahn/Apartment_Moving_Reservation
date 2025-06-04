/**
 * 관리자 예약 관리 페이지
 * 예약 승인/거부 및 현황 관리 기능
 */
"use client";

import React, { useState, useEffect } from 'react';
import { AdminGuard } from '../../../../lib/auth/admin-guard';
import { AdminLayout } from '@/components/admin/admin-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { 
  Calendar, 
  Clock, 
  User, 
  Building, 
  Search,
  Filter,
  CheckCircle,
  XCircle,
  MessageSquare,
  RefreshCw
} from 'lucide-react';
import { toast } from '../../../../lib/toast';

// 임시 타입 정의 (실제 API 연동 시 제거)
interface User {
  id: number;
  username: string;
  name: string;
  apartment_number?: string;
}

interface Reservation {
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
  user?: User;
}

interface ReservationFilters {
  status?: 'pending' | 'approved' | 'rejected' | 'completed' | 'cancelled';
  reservation_type?: 'elevator' | 'parking' | 'other';
  user_id?: number;
  start_date?: string;
  end_date?: string;
  page?: number;
  size?: number;
}

// 임시 서비스 (실제 API 연동 시 제거)
const ReservationService = {
  async getReservations(filters: ReservationFilters = {}) {
    // 임시 데이터
    const mockReservations: Reservation[] = [
      {
        id: 1,
        user_id: 1,
        reservation_type: 'elevator',
        start_time: '2025-01-20T09:00:00Z',
        end_time: '2025-01-20T12:00:00Z',
        description: '이사 예약',
        status: 'pending',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
        user: {
          id: 1,
          username: 'user1',
          name: '김철수',
          apartment_number: '101동 501호'
        }
      },
      {
        id: 2,
        user_id: 2,
        reservation_type: 'parking',
        start_time: '2025-01-21T14:00:00Z',
        end_time: '2025-01-21T18:00:00Z',
        description: '주차장 이용',
        status: 'approved',
        created_at: '2025-01-16T11:00:00Z',
        updated_at: '2025-01-16T11:00:00Z',
        user: {
          id: 2,
          username: 'user2',
          name: '이영희',
          apartment_number: '102동 302호'
        }
      }
    ];

    return {
      items: mockReservations,
      total: mockReservations.length,
      page: 1,
      size: 10
    };
  },

  async approveReservation(id: number, comment?: string): Promise<Reservation> {
    // 임시 구현
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      id,
      user_id: 1,
      reservation_type: 'elevator',
      start_time: '2025-01-20T09:00:00Z',
      end_time: '2025-01-20T12:00:00Z',
      status: 'approved',
      admin_comment: comment,
      created_at: '2025-01-15T10:00:00Z',
      updated_at: new Date().toISOString(),
      user: {
        id: 1,
        username: 'user1',
        name: '김철수',
        apartment_number: '101동 501호'
      }
    };
  },

  async rejectReservation(id: number, comment?: string): Promise<Reservation> {
    // 임시 구현
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      id,
      user_id: 1,
      reservation_type: 'elevator',
      start_time: '2025-01-20T09:00:00Z',
      end_time: '2025-01-20T12:00:00Z',
      status: 'rejected',
      admin_comment: comment,
      created_at: '2025-01-15T10:00:00Z',
      updated_at: new Date().toISOString(),
      user: {
        id: 1,
        username: 'user1',
        name: '김철수',
        apartment_number: '101동 501호'
      }
    };
  }
};

type ReservationStatus = 'pending' | 'approved' | 'rejected' | 'completed' | 'cancelled';
type ReservationType = 'elevator' | 'parking' | 'other';

/**
 * 예약 상태별 색상 및 텍스트 매핑
 */
const statusConfig: Record<ReservationStatus, { color: string; text: string; bgColor: string }> = {
  pending: { color: 'text-yellow-700', text: '대기중', bgColor: 'bg-yellow-100' },
  approved: { color: 'text-green-700', text: '승인됨', bgColor: 'bg-green-100' },
  rejected: { color: 'text-red-700', text: '거부됨', bgColor: 'bg-red-100' },
  completed: { color: 'text-blue-700', text: '완료됨', bgColor: 'bg-blue-100' },
  cancelled: { color: 'text-gray-700', text: '취소됨', bgColor: 'bg-gray-100' },
};

const typeConfig: Record<ReservationType, string> = {
  elevator: '엘리베이터',
  parking: '주차장',
  other: '기타',
};

/**
 * 예약 승인/거부 다이얼로그
 */
interface ActionDialogProps {
  reservation: Reservation;
  action: 'approve' | 'reject';
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (comment?: string) => void;
}

function ActionDialog({ reservation, action, isOpen, onClose, onConfirm }: ActionDialogProps) {
  const [comment, setComment] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirm(comment);
      setComment('');
      onClose();
    } catch (error) {
      // 에러는 상위에서 처리됨
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            예약 {action === 'approve' ? '승인' : '거부'}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 p-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="font-medium">{reservation.user?.name}</div>
            <div className="text-sm text-gray-600">
              {typeConfig[reservation.reservation_type]} • {reservation.user?.apartment_number}
            </div>
            <div className="text-sm text-gray-600">
              {new Date(reservation.start_time).toLocaleString()} ~ {new Date(reservation.end_time).toLocaleString()}
            </div>
            {reservation.description && (
              <div className="text-sm text-gray-600 mt-2">
                상세: {reservation.description}
              </div>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">
              관리자 메모 (선택사항)
            </label>
            <Textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={`${action === 'approve' ? '승인' : '거부'} 사유를 입력하세요...`}
              rows={3}
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose} disabled={isLoading}>
              취소
            </Button>
            <Button 
              onClick={handleConfirm}
              disabled={isLoading}
              className={action === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
            >
              {isLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              ) : action === 'approve' ? (
                <CheckCircle className="h-4 w-4 mr-2" />
              ) : (
                <XCircle className="h-4 w-4 mr-2" />
              )}
              {action === 'approve' ? '승인' : '거부'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * 관리자 예약 관리 페이지
 */
export default function AdminReservations() {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<ReservationFilters>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedReservation, setSelectedReservation] = useState<Reservation | null>(null);
  const [actionDialog, setActionDialog] = useState<{
    reservation: Reservation;
    action: 'approve' | 'reject';
  } | null>(null);

  // 예약 목록 조회
  const fetchReservations = async () => {
    try {
      setLoading(true);
      const response = await ReservationService.getReservations({
        ...filters,
        page: currentPage,
        size: 10,
      });
      setReservations(response.items);
      setTotalCount(response.total);
    } catch (error) {
      toast.error('예약 목록을 불러올 수 없습니다.');
      console.error('Failed to fetch reservations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReservations();
  }, [currentPage, filters]);

  // 필터 적용
  const handleFilterChange = (key: keyof ReservationFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
    setCurrentPage(1);
  };

  // 검색 처리
  const handleSearch = () => {
    // TODO: 실제 검색 로직 구현 (사용자명, 아파트 번호로 검색)
    toast.info('검색 기능은 곧 구현될 예정입니다.');
  };

  // 예약 승인/거부 처리
  const handleReservationAction = async (action: 'approve' | 'reject', comment?: string) => {
    if (!actionDialog) return;

    try {
      const updatedReservation = action === 'approve' 
        ? await ReservationService.approveReservation(actionDialog.reservation.id, comment)
        : await ReservationService.rejectReservation(actionDialog.reservation.id, comment);

      // 목록 업데이트
      setReservations(prev => 
        prev.map(r => r.id === updatedReservation.id ? updatedReservation : r)
      );

      toast.success(`예약이 ${action === 'approve' ? '승인' : '거부'}되었습니다.`);
    } catch (error: any) {
      toast.error(error.message || `예약 ${action === 'approve' ? '승인' : '거부'}에 실패했습니다.`);
    }
  };

  // 상태 필터 변경 핸들러
  const handleStatusFilterChange = (value: string) => {
    handleFilterChange('status', value);
  };

  // 타입 필터 변경 핸들러
  const handleTypeFilterChange = (value: string) => {
    handleFilterChange('reservation_type', value);
  };

  return (
    <AdminGuard>
      <AdminLayout>
        <div className="space-y-6">
          {/* 페이지 헤더 */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">예약 관리</h1>
            <p className="text-gray-600">이사 예약 승인/거부 및 현황을 관리합니다.</p>
          </div>

          {/* 필터 및 검색 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Filter className="h-5 w-5 mr-2" />
                필터 및 검색
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">상태</label>
                  <Select value={filters.status || ''} onValueChange={(value) => handleStatusFilterChange(value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="모든 상태" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">모든 상태</SelectItem>
                      <SelectItem value="pending">대기중</SelectItem>
                      <SelectItem value="approved">승인됨</SelectItem>
                      <SelectItem value="rejected">거부됨</SelectItem>
                      <SelectItem value="completed">완료됨</SelectItem>
                      <SelectItem value="cancelled">취소됨</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">예약 타입</label>
                  <Select value={filters.reservation_type || ''} onValueChange={(value) => handleTypeFilterChange(value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="모든 타입" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">모든 타입</SelectItem>
                      <SelectItem value="elevator">엘리베이터</SelectItem>
                      <SelectItem value="parking">주차장</SelectItem>
                      <SelectItem value="other">기타</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">검색</label>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="사용자명, 아파트 번호"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <Button onClick={handleSearch} size="sm">
                      <Search className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">새로고침</label>
                  <Button onClick={fetchReservations} variant="outline" className="w-full">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    새로고침
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 예약 목록 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <Calendar className="h-5 w-5 mr-2" />
                  예약 목록 ({totalCount}건)
                </span>
                {filters.status === 'pending' && (
                  <Badge variant="secondary">승인 대기: {reservations.filter(r => r.status === 'pending').length}건</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
                  <p>예약 목록을 불러오는 중...</p>
                </div>
              ) : reservations.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  예약이 없습니다.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>사용자</TableHead>
                        <TableHead>아파트</TableHead>
                        <TableHead>예약 타입</TableHead>
                        <TableHead>예약 시간</TableHead>
                        <TableHead>상태</TableHead>
                        <TableHead>신청일</TableHead>
                        <TableHead>액션</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {reservations.map((reservation) => (
                        <TableRow key={reservation.id}>
                          <TableCell>
                            <div className="flex items-center">
                              <User className="h-4 w-4 mr-2 text-gray-500" />
                              <div>
                                <div className="font-medium">{reservation.user?.name}</div>
                                <div className="text-sm text-gray-500">{reservation.user?.username}</div>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center">
                              <Building className="h-4 w-4 mr-2 text-gray-500" />
                              {reservation.user?.apartment_number || 'N/A'}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {typeConfig[reservation.reservation_type]}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center">
                              <Clock className="h-4 w-4 mr-2 text-gray-500" />
                              <div className="text-sm">
                                <div>{new Date(reservation.start_time).toLocaleDateString()}</div>
                                <div className="text-gray-500">
                                  {new Date(reservation.start_time).toLocaleTimeString()} ~ {new Date(reservation.end_time).toLocaleTimeString()}
                                </div>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge 
                              className={`${statusConfig[reservation.status].color} ${statusConfig[reservation.status].bgColor}`}
                            >
                              {statusConfig[reservation.status].text}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm text-gray-500">
                            {new Date(reservation.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <div className="flex space-x-2">
                              {reservation.status === 'pending' && (
                                <>
                                  <Button
                                    size="sm"
                                    onClick={() => setActionDialog({ reservation, action: 'approve' })}
                                    className="bg-green-600 hover:bg-green-700"
                                  >
                                    <CheckCircle className="h-3 w-3 mr-1" />
                                    승인
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() => setActionDialog({ reservation, action: 'reject' })}
                                  >
                                    <XCircle className="h-3 w-3 mr-1" />
                                    거부
                                  </Button>
                                </>
                              )}
                              {reservation.admin_comment && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setSelectedReservation(reservation)}
                                >
                                  <MessageSquare className="h-3 w-3 mr-1" />
                                  메모
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* 페이지네이션 */}
              {totalCount > 10 && (
                <div className="flex justify-center items-center space-x-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(prev => prev - 1)}
                  >
                    이전
                  </Button>
                  <span className="text-sm">
                    {currentPage} / {Math.ceil(totalCount / 10)}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage >= Math.ceil(totalCount / 10)}
                    onClick={() => setCurrentPage(prev => prev + 1)}
                  >
                    다음
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 액션 다이얼로그 */}
          {actionDialog && (
            <ActionDialog
              reservation={actionDialog.reservation}
              action={actionDialog.action}
              isOpen={true}
              onClose={() => setActionDialog(null)}
              onConfirm={(comment) => handleReservationAction(actionDialog.action, comment)}
            />
          )}

          {/* 관리자 메모 보기 다이얼로그 */}
          {selectedReservation && (
            <Dialog open={true} onOpenChange={() => setSelectedReservation(null)}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>관리자 메모</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 p-6">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="font-medium">{selectedReservation.user?.name}</div>
                    <div className="text-sm text-gray-600">
                      {typeConfig[selectedReservation.reservation_type]} • {selectedReservation.user?.apartment_number}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">관리자 메모</label>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      {selectedReservation.admin_comment || '메모가 없습니다.'}
                    </div>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </AdminLayout>
    </AdminGuard>
  );
} 