"use client"; // This is a client component

import React, { useState } from "react";
import { Main } from "@/components/component/main";
import { Reservation } from "@/components/component/reservation";
import { Login } from "@/components/component/login";
import { Notice } from "@/components/component/notice";

export default function Home() {
  const [showReservation, setShowReservation] = useState(false); // 예약 화면을 보여주는 상태를 관리합니다.
  const [showLogin, setShowLogin] = useState(false); // 로그인 화면을 보여주는 상태를 관리합니다.
  const [showNotice, setShowNotice] = useState(false); // 공지사항 화면을 보여주는 상태를 관리합니다.

  const handleCheckIconClick = () => {
    setShowReservation(true);
    setShowLogin(false); // 예약 화면을 보여줄 때 로그인 화면은 숨깁니다.
    setShowNotice(false); // 예약 화면을 보여줄 때 공지사항 화면은 숨깁니다.
  };

  const handleLoginButtonClick = () => {
    setShowLogin(true);
    setShowReservation(false); // 로그인 화면을 보여줄 때 예약 화면은 숨깁니다.
    setShowNotice(false); // 로그인 화면을 보여줄 때 공지사항 화면은 숨깁니다.
  };

  const handleNoticeButtonClick = () => {
    setShowNotice(true);
    setShowReservation(false); // 공지사항 화면을 보여줄 때 예약 화면은 숨깁니다.
    setShowLogin(false); // 공지사항 화면을 보여줄 때 로그인 화면은 숨깁니다.
  };

  const handleBackClick = () => {
    setShowReservation(false);
    setShowLogin(false);
    setShowNotice(false);
  };

  return (
    <main>
      {/* 조건부 렌더링을 이용하여 예약 화면, 로그인 화면, 공지사항 화면을 보여줍니다. */}
      {showReservation ? (
        <Reservation />
      ) : showLogin ? (
        <Login />
      ) : showNotice ? (
        <Notice />
      ) : (
        <Main 
          onCheckIconClick={handleCheckIconClick} 
          onLoginButtonClick={handleLoginButtonClick} 
          onNoticeClick={handleNoticeButtonClick} 
        />
      )}
      {/* 예약 화면, 로그인 화면, 공지사항 화면에서 뒤로 가기 버튼을 누르면 메인 화면을 보여줍니다. */}
      {(showReservation || showLogin || showNotice) && (
        <div className="flex justify-center mt-4">
          <button className="mr-2" onClick={handleBackClick}>뒤로 가기</button>
        </div>
      )}
    </main>
  );
}
