/**
 * 사용자 페이지
 * 사용자 정보 및 내 예약 관리
 */
"use client";

import { User } from "@/components/component/user";
import { useRouter } from "next/navigation";

export default function UserPage() {
  const router = useRouter();

  const handleReservationClick = () => {
    router.push('/reservations');
  };

  const handleLoginClick = () => {
    router.push('/login');
  };

  const handleNoticeClick = () => {
    router.push('/notices');
  };

  return (
    <main>
      <User 
        onCheckIconClick={handleReservationClick}
        onLoginButtonClick={handleLoginClick}
        onNoticeClick={handleNoticeClick}
        onUserButtonClick={() => {}}
      />
    </main>
  );
} 