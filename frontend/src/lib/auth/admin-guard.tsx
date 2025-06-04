/**
 * 관리자 권한 체크 HOC
 * 관리자가 아닌 사용자의 접근을 차단하고 적절한 페이지로 리다이렉트
 */
"use client";

import React, { useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

interface AdminGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  redirectTo?: string;
}

/**
 * 관리자 권한이 필요한 컴포넌트를 감싸는 HOC
 */
export function AdminGuard({ 
  children, 
  fallback = <div className="min-h-screen flex items-center justify-center">
    <div className="text-lg text-red-600">관리자 권한이 필요합니다.</div>
  </div>,
  redirectTo = '/'
}: AdminGuardProps) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    // 로딩이 완료된 후 권한 체크
    if (status === 'loading') return;

    // 로그인하지 않은 경우 로그인 페이지로 리다이렉트
    if (status === 'unauthenticated') {
      router.push('/login');
      return;
    }

    // 관리자가 아닌 경우 홈으로 리다이렉트
    if (session && !session.user?.isAdmin) {
      router.push(redirectTo);
      return;
    }
  }, [session, status, router, redirectTo]);

  // 로딩 중 표시
  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">권한 확인 중...</div>
      </div>
    );
  }

  // 로그인하지 않은 경우
  if (status === 'unauthenticated') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">로그인이 필요합니다.</div>
      </div>
    );
  }

  // 관리자가 아닌 경우
  if (!session?.user?.isAdmin) {
    return fallback;
  }

  // 관리자인 경우 자식 컴포넌트 렌더링
  return <>{children}</>;
}

/**
 * 관리자 권한 체크 훅
 */
export function useAdminAuth() {
  const { data: session, status } = useSession();

  const isLoading = status === 'loading';
  const isAuthenticated = status === 'authenticated';
  const isAdmin = session?.user?.isAdmin ?? false;

  return {
    isLoading,
    isAuthenticated,
    isAdmin,
    session,
    hasAdminAccess: isAuthenticated && isAdmin
  };
}

/**
 * 관리자 여부를 확인하는 유틸리티 함수
 */
export const checkAdminAccess = (session: any): boolean => {
  return session?.user?.isAdmin === true;
}; 