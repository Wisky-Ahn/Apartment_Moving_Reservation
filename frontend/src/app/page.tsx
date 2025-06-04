/**
 * 메인 홈 페이지
 * Next.js App Router 기반 네비게이션
 */
"use client";

import React, { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Main } from "@/components/component/main";

export default function Home() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [showContent, setShowContent] = useState(false);

  // 5초 후에는 강제로 콘텐츠 표시
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowContent(true);
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  // 2초 이상 로딩 중이거나 showContent가 true이면 콘텐츠 표시
  useEffect(() => {
    if (status !== "loading" || showContent) {
      setShowContent(true);
    }
  }, [status, showContent]);

  // 로딩 중 표시 (단, 2초 이내에만)
  if (status === "loading" && !showContent) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">로딩 중...</div>
      </div>
    );
  }

  // 네비게이션 핸들러들
  const handleLoginClick = () => {
    router.push('/login');
  };

  const handleReservationClick = () => {
    router.push('/reservations');
  };

  const handleNoticeClick = () => {
    router.push('/notices');
  };

  const handleUserClick = () => {
    router.push('/user');
  };

  return (
    <main>
      <Main 
        onLoginButtonClick={handleLoginClick}
        onReservationClick={handleReservationClick}
        onNoticeClick={handleNoticeClick}
        onUserClick={handleUserClick}
      />
    </main>
  );
}
