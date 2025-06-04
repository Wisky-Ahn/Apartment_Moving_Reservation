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
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-800 mb-2">
            FNM 아파트 관리 시스템
          </h1>
          <p className="text-slate-600 text-lg">
            편리하고 안전한 이사 예약 서비스
          </p>
        </div>

        {/* 메인 액션 카드들 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          
          {/* 이사 예약 카드 */}
          <Card className="group hover:shadow-xl transition-all duration-300 border-0 shadow-lg bg-gradient-to-br from-blue-600 to-blue-700 text-white cursor-pointer" onClick={onReservationClick}>
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-white/20 rounded-lg">
                    <Calendar className="h-8 w-8" />
                  </div>
                  <div>
                    <CardTitle className="text-xl text-white">이사 예약하기</CardTitle>
                    <p className="text-blue-100 text-sm mt-1">원하는 날짜와 시간 선택</p>
                  </div>
                </div>
                <ArrowRight className="h-6 w-6 text-white/70 group-hover:translate-x-1 transition-transform" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-white/10 rounded-lg p-3">
                  <Clock className="h-5 w-5 mx-auto mb-1" />
                  <p className="text-xs text-blue-100">시간 선택</p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <CheckCircle className="h-5 w-5 mx-auto mb-1" />
                  <p className="text-xs text-blue-100">즉시 승인</p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <Shield className="h-5 w-5 mx-auto mb-1" />
                  <p className="text-xs text-blue-100">안전 보장</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 공지사항 카드 */}
          <Card className="group hover:shadow-xl transition-all duration-300 border-0 shadow-lg bg-white cursor-pointer" onClick={onNoticeClick}>
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-amber-100 rounded-lg">
                    <Bell className="h-8 w-8 text-amber-600" />
                  </div>
                  <div>
                    <CardTitle className="text-xl text-slate-800">공지사항</CardTitle>
                    <p className="text-slate-600 text-sm mt-1">중요한 소식을 확인하세요</p>
                  </div>
                </div>
                <ArrowRight className="h-6 w-6 text-slate-400 group-hover:translate-x-1 transition-transform" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Badge variant="destructive" className="text-xs">중요</Badge>
                  <span className="text-sm text-slate-700">아파트 입주 전화</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="secondary" className="text-xs">안내</Badge>
                  <span className="text-sm text-slate-700">1차 하자 신고 안내</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 최근 공지사항 상세 */}
        <Card className="mb-8 border-0 shadow-lg">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Info className="h-5 w-5 text-blue-600" />
              <CardTitle className="text-lg text-slate-800">최근 공지사항</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-l-4 border-red-400 bg-red-50 p-4 rounded-r-lg">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-red-800">아파트 입주 전화</h3>
                  <p className="text-red-700 text-sm mt-1">이사 예약 확인 및 방법 안내</p>
                  <p className="text-red-600 text-xs mt-2">2023.10.10</p>
                </div>
              </div>
            </div>
            
            <div className="border-l-4 border-blue-400 bg-blue-50 p-4 rounded-r-lg">
              <div className="flex items-start space-x-3">
                <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-blue-800">1차 하자 신고 안내 및 방법</h3>
                  <p className="text-blue-700 text-sm mt-1">하자 신고 절차 안내</p>
                  <p className="text-blue-600 text-xs mt-2">2023.10.10</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 서비스 안내 카드들 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="text-center border-0 shadow-lg bg-white hover:shadow-xl transition-shadow">
            <CardContent className="pt-6">
              <div className="p-4 bg-green-100 rounded-full inline-block mb-4">
                <Home className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">안전한 이사</h3>
              <p className="text-slate-600 text-sm">
                체계적인 예약 시스템으로 안전하고 편리한 이사를 도와드립니다.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center border-0 shadow-lg bg-white hover:shadow-xl transition-shadow">
            <CardContent className="pt-6">
              <div className="p-4 bg-purple-100 rounded-full inline-block mb-4">
                <Users className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">입주민 관리</h3>
              <p className="text-slate-600 text-sm">
                체계적인 입주민 관리와 커뮤니티 소통을 지원합니다.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center border-0 shadow-lg bg-white hover:shadow-xl transition-shadow">
            <CardContent className="pt-6">
              <div className="p-4 bg-blue-100 rounded-full inline-block mb-4">
                <Shield className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">신뢰할 수 있는</h3>
              <p className="text-slate-600 text-sm">
                안전하고 투명한 관리 시스템으로 신뢰할 수 있는 서비스를 제공합니다.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
