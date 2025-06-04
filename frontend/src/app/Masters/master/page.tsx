/**
 * 기존 관리자 페이지 - 새로운 대시보드로 리다이렉트
 */
"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';

export default function MasterPage() {
  const router = useRouter();
  const { data: session, status } = useSession();

  useEffect(() => {
    // 로딩이 완료된 후 처리
    if (status === 'loading') return;

    // 로그인하지 않은 경우 로그인 페이지로
    if (!session) {
      router.push('/login');
      return;
    }

    // 관리자가 아닌 경우 홈으로
    if (!session.user?.isAdmin) {
      router.push('/');
      return;
    }

    // 관리자인 경우 새로운 대시보드로 리다이렉트
    router.push('/admin/dashboard');
  }, [session, status, router]);

  // 로딩 표시
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-lg">관리자 페이지로 이동 중...</div>
    </div>
  );
}