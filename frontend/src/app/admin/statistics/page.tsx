/**
 * 관리자 통계 페이지
 * 예약 통계, 월별/일별 이용률, 인기 시간대 등을 차트로 시각화
 */
"use client";

import React, { useState, useEffect } from 'react';
import { AdminGuard } from '../../../../lib/auth/admin-guard';
import { AdminLayout } from '@/components/admin/admin-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BarChart3, TrendingUp, Users, Calendar, Clock, PieChart } from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api'; // API 클라이언트 import 추가

// 색상 팔레트
const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

interface DashboardStats {
  total_users: number;
  total_reservations: number;
  monthly_reservations: number;
  approved_reservations: number;
  pending_reservations: number;
  approval_rate: number;
}

interface MonthlyData {
  month: string;
  total: number;
  approved: number;
  rejected: number;
  pending: number;
}

interface DailyData {
  date: string;
  total: number;
  approved: number;
}

interface TimeSlotData {
  time: string;
  count: number;
}

interface StatusData {
  status: string;
  count: number;
  status_key: string;
}

/**
 * 통계 카드 컴포넌트
 */
interface StatCardProps {
  title: string;
  value: string | number;
  description: string;
  icon: React.ComponentType<any>;
  color?: 'blue' | 'green' | 'yellow' | 'red';
}

function StatCard({ title, value, description, icon: Icon, color = 'blue' }: StatCardProps) {
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
        <p className="text-xs text-gray-500 mt-1">{description}</p>
      </CardContent>
    </Card>
  );
}

/**
 * 관리자 통계 대시보드
 */
export default function AdminStatistics() {
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [monthlyData, setMonthlyData] = useState<MonthlyData[]>([]);
  const [dailyData, setDailyData] = useState<DailyData[]>([]);
  const [timeSlotData, setTimeSlotData] = useState<TimeSlotData[]>([]);
  const [statusData, setStatusData] = useState<StatusData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * 통계 데이터 조회
   */
  const fetchStatistics = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // API 클라이언트를 사용하여 병렬로 모든 통계 데이터 요청
      const [dashboard, monthly, daily, timeSlot, status] = await Promise.all([
        api.get('/api/statistics/dashboard-stats'),
        api.get('/api/statistics/monthly-stats'),
        api.get('/api/statistics/daily-stats'),
        api.get('/api/statistics/time-slots-stats'),
        api.get('/api/statistics/status-distribution')
      ]);

      setDashboardStats(dashboard.data || dashboard);
      setMonthlyData(monthly.data || monthly);
      setDailyData(daily.data || daily);
      setTimeSlotData(timeSlot.data || timeSlot);
      setStatusData(status.data || status);
    } catch (error: any) {
      console.error('통계 데이터 로드 실패:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 데이터 새로고침
   */
  const handleRefresh = () => {
    fetchStatistics();
  };

  useEffect(() => {
    fetchStatistics();
  }, []);

  if (isLoading) {
    return (
      <AdminGuard>
        <AdminLayout>
          <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">통계 데이터를 불러오는 중...</p>
            </div>
          </div>
        </AdminLayout>
      </AdminGuard>
    );
  }

  if (error) {
    return (
      <AdminGuard>
        <AdminLayout>
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">통계 대시보드</h1>
                <p className="text-gray-600">시스템 통계 및 분석</p>
              </div>
              <Button onClick={handleRefresh}>
                <TrendingUp className="h-4 w-4 mr-2" />
                새로고침
              </Button>
            </div>
            
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-red-600">{error}</p>
                <Button onClick={handleRefresh} className="mt-4">
                  다시 시도
                </Button>
              </CardContent>
            </Card>
          </div>
        </AdminLayout>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard>
      <AdminLayout>
        <div className="space-y-6">
          {/* 페이지 헤더 */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">통계 대시보드</h1>
              <p className="text-gray-600">시스템 통계 및 분석</p>
            </div>
            <Button onClick={handleRefresh}>
              <TrendingUp className="h-4 w-4 mr-2" />
              새로고침
            </Button>
          </div>

          {/* 기본 통계 카드들 */}
          {dashboardStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="총 사용자"
                value={dashboardStats.total_users}
                description="등록된 전체 사용자"
                icon={Users}
                color="blue"
              />
              <StatCard
                title="총 예약"
                value={dashboardStats.total_reservations}
                description="전체 예약 건수"
                icon={Calendar}
                color="green"
              />
              <StatCard
                title="이번 달 예약"
                value={dashboardStats.monthly_reservations}
                description="현재 월 예약 수"
                icon={TrendingUp}
                color="yellow"
              />
              <StatCard
                title="승인률"
                value={`${dashboardStats.approval_rate}%`}
                description="예약 승인 비율"
                icon={BarChart3}
                color="green"
              />
            </div>
          )}

          {/* 차트 영역 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 월별 예약 현황 차트 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" />
                  월별 예약 현황
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="total" fill="#3B82F6" name="전체" />
                    <Bar dataKey="approved" fill="#10B981" name="승인됨" />
                    <Bar dataKey="rejected" fill="#EF4444" name="거부됨" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 예약 상태별 분포 파이 차트 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PieChart className="h-5 w-5 mr-2" />
                  예약 상태별 분포
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="count"
                      nameKey="status"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 최근 30일 일별 예약 추이 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  최근 30일 예약 추이
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={dailyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="total" stroke="#3B82F6" name="전체" />
                    <Line type="monotone" dataKey="approved" stroke="#10B981" name="승인됨" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 시간대별 예약 현황 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Clock className="h-5 w-5 mr-2" />
                  시간대별 예약 현황
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={timeSlotData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8B5CF6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </div>
      </AdminLayout>
    </AdminGuard>
  );
} 