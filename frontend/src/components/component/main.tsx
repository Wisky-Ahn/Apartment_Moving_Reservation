/**
 * 메인 홈페이지 컴포넌트
 * 프로페셔널한 아파트 관리 시스템 UI 제공
 * 통합된 예약 시스템과 신뢰감 있는 디자인 구현
 */
import React from "react";
import { Button } from "@/components/ui/button"
import { CardTitle, CardHeader, CardContent, Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  Calendar, 
  Clock, 
  Bell, 
  Home, 
  Shield, 
  Users, 
  ArrowRight,
  CheckCircle,
  Info,
  AlertTriangle
} from "lucide-react"

interface MainProps {
  onLoginButtonClick: () => void;
  onReservationClick?: () => void;
  onNoticeClick?: () => void;
  onUserClick?: () => void;
}

export function Main({ onLoginButtonClick, onReservationClick, onNoticeClick, onUserClick }: MainProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        
        {/* 웰컴 섹션 */}
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-800 mb-2">
            FNM 아파트 관리 시스템
          </h1>
          <p className="text-slate-600 text-base sm:text-lg">
            편리하고 안전한 이사 예약 서비스
          </p>
        </div>

        {/* 메인 액션 카드들 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
          
          {/* 이사 예약 카드 */}
          <Card className="group hover:shadow-2xl transition-all duration-500 border-0 shadow-lg bg-gradient-to-br from-blue-600 to-blue-700 text-white cursor-pointer transform hover:scale-105 hover:-translate-y-1 btn-hover-disable" onClick={onReservationClick}>
            <CardHeader className="pb-3 sm:pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 sm:space-x-3">
                  <div className="p-2 sm:p-3 bg-white/20 rounded-lg group-hover:bg-white/30 transition-all duration-300 group-hover:scale-110">
                    <Calendar className="h-6 w-6 sm:h-8 sm:w-8" />
                  </div>
                  <div>
                    <CardTitle className="text-lg sm:text-xl text-white group-hover:text-blue-100 transition-colors">이사 예약하기</CardTitle>
                    <p className="text-blue-100 text-xs sm:text-sm mt-1 group-hover:text-blue-50 transition-colors">원하는 날짜와 시간 선택</p>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 sm:h-6 sm:w-6 text-white/70 group-hover:translate-x-2 group-hover:text-white transition-all duration-300" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-2 sm:gap-3 text-center">
                <div className="bg-white/10 rounded-lg p-2 sm:p-3 group-hover:bg-white/20 transition-all duration-300 group-hover:scale-105">
                  <Clock className="h-4 w-4 sm:h-5 sm:w-5 mx-auto mb-1 group-hover:scale-110 transition-transform" />
                  <p className="text-xs text-blue-100">시간 선택</p>
                </div>
                <div className="bg-white/10 rounded-lg p-2 sm:p-3 group-hover:bg-white/20 transition-all duration-300 group-hover:scale-105">
                  <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 mx-auto mb-1 group-hover:scale-110 transition-transform" />
                  <p className="text-xs text-blue-100">즉시 승인</p>
                </div>
                <div className="bg-white/10 rounded-lg p-2 sm:p-3 group-hover:bg-white/20 transition-all duration-300 group-hover:scale-105">
                  <Shield className="h-4 w-4 sm:h-5 sm:w-5 mx-auto mb-1 group-hover:scale-110 transition-transform" />
                  <p className="text-xs text-blue-100">안전 보장</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 공지사항 카드 */}
          <Card className="group hover:shadow-2xl transition-all duration-500 border-0 shadow-lg bg-white cursor-pointer transform hover:scale-105 hover:-translate-y-1 btn-hover-disable" onClick={onNoticeClick}>
            <CardHeader className="pb-3 sm:pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 sm:space-x-3">
                  <div className="p-2 sm:p-3 bg-amber-100 rounded-lg group-hover:bg-amber-200 transition-all duration-300 group-hover:scale-110">
                    <Bell className="h-6 w-6 sm:h-8 sm:w-8 text-amber-600" />
                  </div>
                  <div>
                    <CardTitle className="text-lg sm:text-xl text-slate-800 group-hover:text-amber-700 transition-colors">공지사항</CardTitle>
                    <p className="text-slate-600 text-xs sm:text-sm mt-1 group-hover:text-amber-600 transition-colors">중요한 소식을 확인하세요</p>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 sm:h-6 sm:w-6 text-slate-400 group-hover:translate-x-2 group-hover:text-amber-600 transition-all duration-300" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center space-x-2 group-hover:translate-x-1 transition-transform duration-300">
                  <Badge variant="destructive" className="text-xs group-hover:scale-105 transition-transform">중요</Badge>
                  <span className="text-xs sm:text-sm text-slate-700 group-hover:text-slate-800 transition-colors">아파트 입주 전화</span>
                </div>
                <div className="flex items-center space-x-2 group-hover:translate-x-1 transition-transform duration-300">
                  <Badge variant="secondary" className="text-xs group-hover:scale-105 transition-transform">안내</Badge>
                  <span className="text-xs sm:text-sm text-slate-700 group-hover:text-slate-800 transition-colors">1차 하자 신고 안내</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 최근 공지사항 상세 */}
        <Card className="mb-6 sm:mb-8 border-0 shadow-lg">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Info className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600" />
              <CardTitle className="text-base sm:text-lg text-slate-800">최근 공지사항</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3 sm:space-y-4">
            <div className="border-l-4 border-red-400 bg-red-50 p-3 sm:p-4 rounded-r-lg">
              <div className="flex items-start space-x-2 sm:space-x-3">
                <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5 text-red-500 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-red-800 text-sm sm:text-base">아파트 입주 전화</h3>
                  <p className="text-red-700 text-xs sm:text-sm mt-1">이사 예약 확인 및 방법 안내</p>
                  <p className="text-red-600 text-xs mt-2">2023.10.10</p>
                </div>
              </div>
            </div>
            
            <div className="border-l-4 border-blue-400 bg-blue-50 p-3 sm:p-4 rounded-r-lg">
              <div className="flex items-start space-x-2 sm:space-x-3">
                <Info className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-blue-800 text-sm sm:text-base">1차 하자 신고 안내 및 방법</h3>
                  <p className="text-blue-700 text-xs sm:text-sm mt-1">하자 신고 절차 안내</p>
                  <p className="text-blue-600 text-xs mt-2">2023.10.10</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 서비스 안내 카드들 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          <Card className="text-center border-0 shadow-lg bg-white hover:shadow-xl transition-shadow btn-hover-disable">
            <CardContent className="pt-4 sm:pt-6">
              <div className="p-3 sm:p-4 bg-green-100 rounded-full inline-block mb-3 sm:mb-4">
                <Home className="h-6 w-6 sm:h-8 sm:w-8 text-green-600" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2 text-sm sm:text-base">안전한 이사</h3>
              <p className="text-slate-600 text-xs sm:text-sm">
                체계적인 예약 시스템으로 안전하고 편리한 이사를 도와드립니다.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center border-0 shadow-lg bg-white hover:shadow-xl transition-shadow btn-hover-disable">
            <CardContent className="pt-4 sm:pt-6">
              <div className="p-3 sm:p-4 bg-purple-100 rounded-full inline-block mb-3 sm:mb-4">
                <Users className="h-6 w-6 sm:h-8 sm:w-8 text-purple-600" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2 text-sm sm:text-base">입주민 관리</h3>
              <p className="text-slate-600 text-xs sm:text-sm">
                체계적인 입주민 관리와 커뮤니티 소통을 지원합니다.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center border-0 shadow-lg bg-white hover:shadow-xl transition-shadow btn-hover-disable sm:col-span-2 lg:col-span-1">
            <CardContent className="pt-4 sm:pt-6">
              <div className="p-3 sm:p-4 bg-blue-100 rounded-full inline-block mb-3 sm:mb-4">
                <Shield className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2 text-sm sm:text-base">신뢰할 수 있는</h3>
              <p className="text-slate-600 text-xs sm:text-sm">
                안전하고 투명한 관리 시스템으로 신뢰할 수 있는 서비스를 제공합니다.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
