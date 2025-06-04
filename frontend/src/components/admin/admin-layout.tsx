/**
 * 관리자 전용 레이아웃 컴포넌트
 * 사이드바 네비게이션과 헤더를 포함한 관리자 페이지 레이아웃
 */
"use client";

import React from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useRouter, usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  LayoutDashboard, 
  Calendar, 
  Users, 
  FileText, 
  BarChart3, 
  Settings,
  LogOut,
  Home
} from 'lucide-react';

interface AdminLayoutProps {
  children: React.ReactNode;
}

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
  description: string;
}

const navigationItems: NavigationItem[] = [
  {
    name: '대시보드',
    href: '/admin/dashboard',
    icon: LayoutDashboard,
    description: '관리자 홈'
  },
  {
    name: '예약 관리',
    href: '/admin/reservations',
    icon: Calendar,
    description: '예약 승인/거부'
  },
  {
    name: '사용자 관리',
    href: '/admin/users',
    icon: Users,
    description: '입주민 관리'
  },
  {
    name: '공지사항 관리',
    href: '/admin/notices',
    icon: FileText,
    description: '공지사항 CRUD'
  },
  {
    name: '통계',
    href: '/admin/statistics',
    icon: BarChart3,
    description: '이용 현황 분석'
  },
];

/**
 * 관리자 페이지 레이아웃
 */
export function AdminLayout({ children }: AdminLayoutProps) {
  const { data: session } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  // 로그아웃 처리
  const handleLogout = async () => {
    await signOut({ redirect: false });
    router.push('/');
  };

  // 홈으로 돌아가기
  const handleGoHome = () => {
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 사이드바 */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-lg">
        {/* 로고 및 타이틀 */}
        <div className="flex items-center justify-center h-16 px-4 border-b">
          <h1 className="text-xl font-bold text-blue-600">FNM 관리자</h1>
        </div>

        {/* 네비게이션 메뉴 */}
        <nav className="mt-8 px-4">
          <ul className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              
              return (
                <li key={item.href}>
                  <button
                    onClick={() => router.push(item.href)}
                    className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-600 border-r-2 border-blue-600'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="h-5 w-5 mr-3" />
                    <div>
                      <div className="font-medium">{item.name}</div>
                      <div className="text-xs text-gray-500">{item.description}</div>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* 하단 버튼들 */}
        <div className="absolute bottom-4 left-4 right-4 space-y-2">
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={handleGoHome}
          >
            <Home className="h-4 w-4 mr-2" />
            홈으로 돌아가기
          </Button>
          <Button
            variant="outline"
            className="w-full justify-start text-red-600 hover:text-red-700"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4 mr-2" />
            로그아웃
          </Button>
        </div>
      </div>

      {/* 메인 컨텐츠 영역 */}
      <div className="ml-64">
        {/* 헤더 */}
        <header className="bg-white shadow-sm border-b h-16 flex items-center justify-between px-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              관리자 대시보드
            </h2>
            <p className="text-sm text-gray-500">
              FNM 아파트 예약 시스템 관리
            </p>
          </div>
        </header>

        {/* 페이지 컨텐츠 */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
} 