/**
 * 관리자 대시보드 메인 페이지
 * 시스템 현황과 주요 통계를 한눈에 보여주는 대시보드
 */
"use client";

import React, { useState, useEffect } from 'react';
import { AdminGuard } from '../../../../lib/auth/admin-guard';
import { AdminLayout } from '@/components/admin/admin-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Calendar, 
  Users, 
  FileText, 
  CheckCircle, 
  Clock, 
  XCircle,
  TrendingUp,
  AlertCircle
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api'; // API 클라이언트 import 추가

// 예약 상태 타입 정의
type ReservationStatus = 'pending' | 'approved' | 'rejected';

/**
 * 대시보드 통계 카드 컴포넌트
 */
interface StatCardProps {
  title: string;
  value: string | number;
  description: string;
  icon: React.ComponentType<any>;
  trend?: string;
  color?: 'blue' | 'green' | 'yellow' | 'red';
}

function StatCard({ title, value, description, icon: Icon, trend, color = 'blue' }: StatCardProps) {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    yellow: 'text-yellow-600 bg-yellow-50',
    red: 'text-red-600 bg-red-50',
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">
          {title}
        </CardTitle>
        <div className={`p-2 rounded-full ${colorClasses[color]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-gray-500 mt-1">
          {description}
          {trend && (
            <span className="ml-1 text-green-600">
              <TrendingUp className="inline h-3 w-3" /> {trend}
            </span>
          )}
        </p>
      </CardContent>
    </Card>
  );
}

interface PendingAdmin {
  id: number;
  username: string;
  email: string;
  name: string;
  phone?: string;
  apartment_number?: string;
  created_at: string;
}

/**
 * 관리자 대시보드 페이지
 */
export default function AdminDashboard() {
  const [pendingAdmins, setPendingAdmins] = useState<PendingAdmin[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);

  /**
   * 현재 사용자 정보 확인 (슈퍼관리자 여부)
   */
  useEffect(() => {
    // 임시로 슈퍼관리자로 설정 (실제로는 로그인 토큰에서 가져와야 함)
    setCurrentUser({ is_super_admin: true });
  }, []);

  /**
   * 승인 대기 중인 관리자 목록 조회
   */
  const fetchPendingAdmins = async () => {
    try {
      setIsLoading(true);
      // API 클라이언트 사용으로 변경 (NextAuth 토큰 포함)
      const response = await api.get('/api/users/admin/pending');
      setPendingAdmins(response.data || response);
    } catch (error) {
      console.error('승인 대기 관리자 목록 조회 실패:', error);
      setError('승인 대기 관리자 목록을 가져오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 관리자 승인 처리
   */
  const approveAdmin = async (userId: number, username: string) => {
    if (!confirm(`'${username}' 사용자를 관리자로 승인하시겠습니까?`)) {
      return;
    }

    try {
      // API 클라이언트 사용으로 변경 (NextAuth 토큰 포함)
      const response = await api.put(`/api/users/admin/${userId}/approve`);

      alert('관리자 승인이 완료되었습니다.');
      fetchPendingAdmins(); // 목록 새로고침
    } catch (error: any) {
      console.error('관리자 승인 실패:', error);
      alert('관리자 승인에 실패했습니다: ' + error.message);
    }
  };

  /**
   * 관리자 거부 처리
   */
  const rejectAdmin = async (userId: number, username: string) => {
    if (!confirm(`'${username}' 사용자의 관리자 신청을 거부하시겠습니까?`)) {
      return;
    }

    try {
      // API 클라이언트 사용으로 변경 (NextAuth 토큰 포함)
      const response = await api.put(`/api/users/admin/${userId}/reject`);

      alert('관리자 신청이 거부되었습니다.');
      fetchPendingAdmins(); // 목록 새로고침
    } catch (error: any) {
      console.error('관리자 거부 실패:', error);
      alert('관리자 거부에 실패했습니다: ' + error.message);
    }
  };

  useEffect(() => {
    if (currentUser?.is_super_admin) {
      fetchPendingAdmins();
    }
  }, [currentUser]);

  // TODO: 실제 API에서 데이터를 가져오는 로직 구현
  const stats = {
    totalReservations: 156,
    pendingReservations: 12,
    approvedReservations: 128,
    totalUsers: 89,
    totalNotices: 15,
    activeNotices: 8,
  };

  const recentReservations = [
    { id: 1, user: '김철수', apartment: '101동 501호', date: '2025-06-05', status: 'pending' as ReservationStatus },
    { id: 2, user: '이영희', apartment: '102동 302호', date: '2025-06-06', status: 'approved' as ReservationStatus },
    { id: 3, user: '박민수', apartment: '103동 701호', date: '2025-06-07', status: 'pending' as ReservationStatus },
    { id: 4, user: '최지영', apartment: '101동 203호', date: '2025-06-08', status: 'approved' as ReservationStatus },
  ];

  const statusColors: Record<ReservationStatus, string> = {
    pending: 'text-yellow-600 bg-yellow-50',
    approved: 'text-green-600 bg-green-50',
    rejected: 'text-red-600 bg-red-50',
  };

  const statusTexts: Record<ReservationStatus, string> = {
    pending: '대기중',
    approved: '승인됨',
    rejected: '거부됨',
  };

  return (
    <AdminGuard>
      <AdminLayout>
        <div className="space-y-6">
          {/* 페이지 헤더 */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
            <p className="text-gray-600">FNM 아파트 예약 시스템 현황을 한눈에 확인하세요.</p>
          </div>

          {/* 통계 카드들 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="총 예약"
              value={stats.totalReservations}
              description="전체 예약 건수"
              icon={Calendar}
              trend="+12% from last month"
              color="blue"
            />
            <StatCard
              title="대기중 예약"
              value={stats.pendingReservations}
              description="승인 대기중인 예약"
              icon={Clock}
              color="yellow"
            />
            <StatCard
              title="승인된 예약"
              value={stats.approvedReservations}
              description="승인된 예약 건수"
              icon={CheckCircle}
              color="green"
            />
            <StatCard
              title="총 사용자"
              value={stats.totalUsers}
              description="등록된 입주민 수"
              icon={Users}
              trend="+5% from last month"
              color="blue"
            />
          </div>

          {/* 슈퍼관리자 전용 - 관리자 승인 섹션 */}
          {currentUser?.is_super_admin && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-800">관리자 승인 대기</h2>
                <Badge variant="destructive">{pendingAdmins.length}</Badge>
              </div>
              
              {isLoading ? (
                <div className="text-center py-4">승인 대기 목록을 불러오는 중...</div>
              ) : error ? (
                <div className="text-center py-4 text-red-600">{error}</div>
              ) : pendingAdmins.length === 0 ? (
                <div className="text-center py-4 text-gray-500">승인 대기 중인 관리자가 없습니다.</div>
              ) : (
                <div className="space-y-4">
                  {pendingAdmins.map((admin) => (
                    <div key={admin.id} className="border rounded-lg p-4 flex justify-between items-center">
                      <div>
                        <div className="font-medium">{admin.name} ({admin.username})</div>
                        <div className="text-sm text-gray-600">{admin.email}</div>
                        {admin.apartment_number && (
                          <div className="text-sm text-gray-600">📍 {admin.apartment_number}</div>
                        )}
                        <div className="text-xs text-gray-400">
                          신청일: {new Date(admin.created_at).toLocaleDateString('ko-KR')}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button 
                          onClick={() => approveAdmin(admin.id, admin.username)}
                          size="sm"
                          className="bg-green-600 hover:bg-green-700"
                        >
                          승인
                        </Button>
                        <Button 
                          onClick={() => rejectAdmin(admin.id, admin.username)}
                          size="sm"
                          variant="destructive"
                        >
                          거부
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 메인 컨텐츠 영역 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 최근 예약 현황 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Calendar className="h-5 w-5 mr-2" />
                  최근 예약 현황
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentReservations.map((reservation) => (
                    <div 
                      key={reservation.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <div className="font-medium">{reservation.user}</div>
                        <div className="text-sm text-gray-500">
                          {reservation.apartment} • {reservation.date}
                        </div>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${statusColors[reservation.status]}`}>
                        {statusTexts[reservation.status]}
                      </span>
                    </div>
                  ))}
                </div>
                <Button className="w-full mt-4" variant="outline">
                  모든 예약 보기
                </Button>
              </CardContent>
            </Card>

            {/* 시스템 상태 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2" />
                  시스템 상태
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">데이터베이스 연결</span>
                    <div className="flex items-center">
                      <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                      <span className="text-sm text-green-600">정상</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">API 서버</span>
                    <div className="flex items-center">
                      <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                      <span className="text-sm text-green-600">정상</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">공지사항 시스템</span>
                    <div className="flex items-center">
                      <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                      <span className="text-sm text-green-600">정상</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">활성 공지사항</span>
                    <span className="text-sm font-medium">{stats.activeNotices}개</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 빠른 액션 버튼들 */}
          <Card>
            <CardHeader>
              <CardTitle>빠른 액션</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Button className="h-16 flex flex-col">
                  <Calendar className="h-6 w-6 mb-1" />
                  예약 관리
                </Button>
                <Button variant="outline" className="h-16 flex flex-col">
                  <Users className="h-6 w-6 mb-1" />
                  사용자 관리
                </Button>
                <Button variant="outline" className="h-16 flex flex-col">
                  <FileText className="h-6 w-6 mb-1" />
                  공지사항 작성
                </Button>
                <Button variant="outline" className="h-16 flex flex-col">
                  <TrendingUp className="h-6 w-6 mb-1" />
                  통계 보기
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </AdminLayout>
    </AdminGuard>
  );
} 