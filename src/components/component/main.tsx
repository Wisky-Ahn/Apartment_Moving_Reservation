import React from "react";
import { AvatarImage, AvatarFallback, Avatar } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { CardTitle, CardHeader, CardContent, Card } from "@/components/ui/card"
import { JSX, SVGProps } from "react"

interface MainProps {
  onCheckIconClick: () => void; // onCheckIconClick 속성을 정의합니다. 2024.03.24
  onLoginButtonClick: () => void; // onLoginButtonClick 속성을 정의합니다.
  onNoticeClick: () => void; // onNoticeClick 속성을 정의합니다.
}

export function Main({ onCheckIconClick, onLoginButtonClick, onNoticeClick }: MainProps) {

  return (
    <div className="min-h-screen bg-white py-8 px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-blue-600">FNM</h1>
        <Avatar>
          <AvatarImage alt="Profile" src="/placeholder.svg?height=32&width=32" />
          <AvatarFallback>U</AvatarFallback>
        </Avatar>
      </div>
      <div className="mt-8 flex justify-between space-x-4">
        <Button className="flex-1" variant="outline">
          오늘 예약
        </Button>
        <Button className="flex-1" variant="outline">
          내일 예약
        </Button>
        <Button className="flex-1" variant="outline">
          전날 예약
        </Button>
        {/* 수정된 부분: 공지사항 버튼 클릭 시 공지사항 페이지로 이동하는 함수를 추가 */}
        <Button className="flex-none" onClick={onNoticeClick}>공지사항</Button>
      </div>
      <div className="mt-6">
        <h2 className="text-lg font-semibold">공지사항</h2>
        <div className="mt-4 grid grid-cols-1 gap-4">
          <div className="border-t border-b py-4">
            <h3 className="text-md">아파트 입주 전화</h3>
            <p className="text-sm text-gray-600">이사 예약 확인 및 방법 안내</p>
            <p className="text-right text-sm text-gray-500">2023.10.10</p>
          </div>
          <div className="border-t border-b py-4">
            <h3 className="text-md">1차 하자 신고 안내 및 방법</h3>
            <p className="text-right text-sm text-gray-500">2023.10.10</p>
          </div>
        </div>
      </div>
      <div className="mt-6 grid grid-cols-1 gap-4">
        <Card className="w-full">
          <CardHeader>
            <CardTitle>이사 예약/확인</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex justify-center">
              <CheckIcon onClick={onCheckIconClick} className="h-24 w-24 text-gray-700" />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* 수정된 부분: 로그인 버튼 클릭 시 로그인 페이지로 이동하는 함수를 추가 */}
      <div className="mt-6 flex justify-center">
        <Button onClick={onLoginButtonClick}>로그인</Button>
      </div>
    </div>
  )
}


function CheckIcon(props: JSX.IntrinsicAttributes & SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}
