/**
 * 관리자 전용 레이아웃 컴포넌트
 * 사이드바 네비게이션과 헤더를 포함한 관리자 페이지 레이아웃
 */
"use client";

import React, { ReactNode } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useRouter, usePathname } from 'next/navigation';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard,
  Users,
  Calendar,
  FileText,
  BarChart3,
  Settings,
  LogOut,
  Home,
  User
} from 'lucide-react';
import { setAuthToken } from '@/lib/api';

interface AdminLayoutProps {
  children: ReactNode;
}

// 네비게이션 아이템 정의
const navigationItems = [
  {
    name: '대시보드',
    href: '/admin/dashboard',
    icon: LayoutDashboard,
    description: '시스템 현황'
  },
  {
    name: '사용자 관리',
    href: '/admin/users',
    icon: Users,
    description: '입주민 관리'
  },
  {
    name: '예약 관리',
    href: '/admin/reservations',
    icon: Calendar,
    description: '예약 현황'
  },
  {
    name: '공지사항',
    href: '/admin/notices',
    icon: FileText,
    description: '공지 관리'
  },
  {
    name: '통계',
    href: '/admin/statistics',
    icon: BarChart3,
    description: '이용 통계'
  },
  {
    name: '프로필',
    href: '/admin/profile',
    icon: User,
    description: '내 정보'
  },
  {
    name: '시스템 설정',
    href: '/admin/settings',
    icon: Settings,
    description: '시스템 관리'
  },
];

interface ExtendedSession {
  accessToken?: string;
  user: {
    id?: string;
    name?: string | null;
    email?: string | null;
    image?: string | null;
    isAdmin?: boolean;
    username?: string;
  };
}

/**
 * 관리자 페이지 레이아웃
 */
export function AdminLayout({ children }: AdminLayoutProps) {
  const { data: session } = useSession() as { data: ExtendedSession | null };
  const router = useRouter();
  const pathname = usePathname();

  // 세션이 있을 때 API 클라이언트에 토큰 설정
  React.useEffect(() => {
    if (session?.accessToken) {
      setAuthToken(session.accessToken);
      console.log('🔑 NextAuth token set in AdminLayout');
    } else {
      setAuthToken(null);
      console.log('⚠️ No NextAuth token available in AdminLayout');
    }
  }, [session]);

  // 로그아웃 처리
  const handleLogout = async () => {
    if (confirm('로그아웃 하시겠습니까?')) {
      await signOut({ callbackUrl: '/login' });
    }
  };

  // 홈으로 이동
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

        {/* 관리자 프로필 섹션 */}
        <div className="px-4 py-4 border-b bg-gray-50">
          <div className="flex items-center space-x-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src="" />
              <AvatarFallback className="bg-blue-100 text-blue-600 font-semibold">
                {session?.user?.name?.slice(0, 2) || 'AD'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {session?.user?.name || '관리자'}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {session?.user?.email || 'admin@fnm.com'}
              </p>
              <p className="text-xs text-blue-600 font-medium">
                시스템 관리자
              </p>
            </div>
          </div>
        </div>

        {/* 네비게이션 메뉴 */}
        <nav className="mt-4 px-4">
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