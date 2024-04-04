"use client"; // This is a client component

import React, { useState } from "react";
import { Main } from "@/components/component/main";
import { Reservation } from "@/components/component/reservation";
import { Login } from "@/components/component/login";
import { User } from "@/components/component/user";
import { Notice } from "@/components/component/notice";

export default function Home() {
  const [showReservation, setShowReservation] = useState(false); // 예약 화면을 보여주는 상태를 관리합니다.
  const [showLogin, setShowLogin] = useState(false); // 로그인 화면을 보여주는 상태를 관리합니다.
  const [showNotice, setShowNotice] = useState(false); // 공지사항 화면을 보여주는 상태를 관리합니다.
  const [showUser, setShowUser] = useState(false);
  
  const handleCheckIconClick = () => {
    setShowReservation(true);
    setShowLogin(false); // 예약 화면을 보여줄 때 로그인 화면은 숨깁니다.
    setShowNotice(false); // 예약 화면을 보여줄 때 공지사항 화면은 숨깁니다.
  };

  const handleLoginButtonClick = () => {
    setShowLogin(true); // 로그인 버튼 클릭 시 로그인 화면 표시
    setShowReservation(false); // 로그인 화면을 보여줄 때 예약 화면은 숨깁니다.
    setShowNotice(false); // 로그인 화면을 보여줄 때 공지사항 화면은 숨깁니다.
  };

  const handleCloseButtonClick = () => {
    setShowReservation(false);
    setShowLogin(false); // 예약 화면을 보여줄 때 로그인 화면은 숨깁니다.
    setShowNotice(false); // 예약 화면을 보여줄 때 공지사항 화면은 숨깁니다.
  };

  const handleUserButtonClick = () => {
    setShowUser(true);
    setShowReservation(false);
    setShowLogin(false); // 로그인 버튼을 클릭하면 로그인 화면을 닫습니다.
    setShowNotice(false); // 예약 화면을 보여줄 때 공지사항 화면은 숨깁니다.
  };

  const handleNoticeButtonClick = () => {
    setShowNotice(true);
    setShowReservation(false); // 공지사항 화면을 보여줄 때 예약 화면은 숨깁니다.
    setShowLogin(false); // 공지사항 화면을 보여줄 때 로그인 화면은 숨깁니다.
  };

  const handleBackClick = () => {
    setShowReservation(false);
    setShowNotice(false);
  };

  return (
    <main>
      {/* 조건부 렌더링을 이용하여 예약 화면, 로그인 화면, 공지사항 화면을 보여줍니다. */}
      {showReservation ? (
        <Reservation />
      ) : showLogin ? (
        <Login onCloseButtonClick={handleCloseButtonClick} 
               onUserButtonClick={handleUserButtonClick} /> // 로그인 화면 표시 및 onCloseButtonClick 이벤트 핸들러 전달
      ) : showNotice ? (
        <Notice />
      ) : showUser ? (
        <User
                
                onCheckIconClick={handleCheckIconClick}
                onLoginButtonClick={handleLoginButtonClick}
                onNoticeClick={handleNoticeButtonClick} onUserButtonClick={function (): void {
                  throw new Error("Function not implemented.");
                } }        />
      ) : (
        <Main
          onLoginButtonClick={handleLoginButtonClick} 
        />
      )}
      {/* 예약 화면, 로그인 화면, 공지사항 화면에서 뒤로 가기 버튼을 누르면 메인 화면을 보여줍니다. */}
      {(showReservation || showNotice) && (
        <div className="flex justify-center mt-4">
          <button className="mr-2" onClick={handleBackClick}>뒤로 가기</button>
        </div>
      )}
    </main>
  );
}
