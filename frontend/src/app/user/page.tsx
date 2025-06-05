/**
 * 사용자 프로필 페이지
 * 로그인한 사용자의 정보 및 예약 내역을 표시
 */
"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback, useMemo } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { reservationApi, type Reservation } from "@/lib/api";
import { toast } from "@/lib/toast";

// 성능 모니터링 훅
const usePerformanceMonitor = (componentName: string) => {
  useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // 개발 환경에서만 로그 출력
      if (process.env.NODE_ENV === 'development') {
        console.log(`🚀 ${componentName} 렌더링 시간: ${renderTime.toFixed(2)}ms`);
        
        // 성능 경고 (100ms 이상 시)
        if (renderTime > 100) {
          console.warn(`⚠️ ${componentName} 렌더링이 느립니다: ${renderTime.toFixed(2)}ms`);
        }
      }
    };
  });
};

export default function UserPage() {
  // 성능 모니터링 시작
  usePerformanceMonitor('UserPage');

  const { data: session, status } = useSession();
  const router = useRouter();
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("profile");

  useEffect(() => {
    if (status === "loading") return; // 로딩 중일 때는 아무것도 하지 않음
    if (!session) {
      router.push("/login"); // 세션이 없으면 로그인 페이지로 리디렉션
    }
  }, [session, status, router]);

  // 내 예약 목록 가져오기
  const fetchMyReservations = async () => {
    setLoading(true);
    try {
      const response = await reservationApi.getMyReservations(1, 10);
      setReservations(response.data.items || []);
    } catch (error: any) {
      console.error("예약 목록 조회 실패:", error);
      
      // 개발 환경에서 API가 없는 경우 임시 데이터 사용
      if (process.env.NODE_ENV === "development") {
        const mockReservations: Reservation[] = [
          {
            id: 1,
            user_id: 1,
            date: "2024-12-20",
            time: "14:00",
            status: "confirmed",
            type: "moving",
            description: "아파트 이사 예약",
            created_at: "2024-12-15T10:00:00Z",
            updated_at: "2024-12-15T10:00:00Z"
          },
          {
            id: 2,
            user_id: 1,
            date: "2024-12-25",
            time: "10:00",
            status: "pending",
            type: "inspection",
            description: "하자 점검 예약",
            created_at: "2024-12-15T11:00:00Z",
            updated_at: "2024-12-15T11:00:00Z"
          }
        ];
        setReservations(mockReservations);
        toast.warning("개발 모드: 임시 데이터를 사용합니다.");
      } else {
        toast.error("예약 목록을 불러오는데 실패했습니다.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (session) {
      fetchMyReservations();
    }
  }, [session]);

  const getStatusBadge = useMemo(() => (status: string) => {
    const statusConfig = {
      confirmed: { variant: "default" as const, label: "확정" },
      pending: { variant: "secondary" as const, label: "대기중" },
      cancelled: { variant: "destructive" as const, label: "취소됨" },
      completed: { variant: "outline" as const, label: "완료" }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    
    return (
      <Badge variant={config.variant}>{config.label}</Badge>
    );
  }, []);

  const getTypeLabel = useMemo(() => (type: string) => {
    const typeConfig = {
      moving: "이사",
      inspection: "점검",
      maintenance: "정비"
    };
    
    return typeConfig[type as keyof typeof typeConfig] || type;
  }, []);

  // 미구현 페이지 핸들러 함수들 추가
  const handleUnavailablePage = useCallback((pageName: string) => {
    alert(`${pageName} 페이지는 현재 준비 중입니다. 빠른 시일 내에 제공할 예정입니다.`);
  }, []);

  // 에러 처리가 개선된 예약 취소 핸들러
  const handleCancelReservation = useCallback(async (id: number) => {
    if (!confirm('정말로 예약을 취소하시겠습니까?')) {
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/reservations/${id}/cancel`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${session?.accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '예약 취소에 실패했습니다.');
      }

      alert('예약이 성공적으로 취소되었습니다.');
      await fetchMyReservations(); // 목록 새로고침
    } catch (error) {
      console.error('예약 취소 오류:', error);
      alert(error instanceof Error ? error.message : '예약 취소 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, [session?.accessToken]);

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">로딩 중...</div>
      </div>
    );
  }

  if (!session) {
    return null; // 리디렉션 중이므로 아무것도 렌더링하지 않음
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">내 정보</h1>
          <p className="mt-2 text-gray-600">계정 정보와 예약 내역을 확인하세요</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 프로필 사이드바 */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader className="text-center">
                <Avatar className="w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-4">
                  <AvatarImage src={""} alt="프로필 이미지" />
                  <AvatarFallback className="text-xl sm:text-2xl">
                    {session.user?.name?.[0] || session.user?.email?.[0] || "U"}
                  </AvatarFallback>
                </Avatar>
                <CardTitle className="text-lg sm:text-xl">{session.user?.name || "사용자"}</CardTitle>
                <CardDescription className="text-sm">{session.user?.email}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  variant="outline" 
                  className="w-full btn-touch-optimized"
                  onClick={() => router.push("/profile/edit")}
                >
                  프로필 수정
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full btn-touch-optimized"
                  onClick={() => setActiveTab("reservations")}
                >
                  내 예약 보기
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full btn-touch-optimized"
                  onClick={() => setActiveTab("settings")}
                >
                  설정
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* 메인 콘텐츠 */}
          <div className="lg:col-span-3">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-6">
                <TabsTrigger value="profile" className="text-xs sm:text-sm">프로필</TabsTrigger>
                <TabsTrigger value="reservations" className="text-xs sm:text-sm">내 예약</TabsTrigger>
                <TabsTrigger value="settings" className="text-xs sm:text-sm">설정</TabsTrigger>
              </TabsList>

              {/* 프로필 탭 */}
              <TabsContent value="profile" className="space-y-6">
                {/* 빠른 액션 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg sm:text-xl">빠른 액션</CardTitle>
                    <CardDescription className="text-sm">자주 사용하는 기능들</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Button 
                        variant="outline" 
                        className="h-16 sm:h-20 flex flex-col transition-all duration-300 hover:scale-105 hover:shadow-lg group border-2 hover:border-blue-300 btn-touch-optimized"
                        onClick={() => router.push("/Reservations/reservations")}
                        debounceMs={500}
                      >
                        <div className="text-xl sm:text-2xl mb-2 group-hover:scale-110 transition-transform">📅</div>
                        <div className="text-sm sm:text-base group-hover:text-blue-600 transition-colors">새 예약</div>
                      </Button>
                      <Button 
                        variant="outline" 
                        className="h-16 sm:h-20 flex flex-col transition-all duration-300 hover:scale-105 hover:shadow-lg group border-2 hover:border-green-300 btn-touch-optimized"
                        onClick={() => setActiveTab("reservations")}
                      >
                        <div className="text-xl sm:text-2xl mb-2 group-hover:scale-110 transition-transform">📋</div>
                        <div className="text-sm sm:text-base group-hover:text-green-600 transition-colors">내 예약</div>
                      </Button>
                      <Button 
                        variant="outline" 
                        className="h-16 sm:h-20 flex flex-col transition-all duration-300 hover:scale-105 hover:shadow-lg group border-2 hover:border-orange-300 btn-touch-optimized"
                        onClick={() => router.push("/Notices/notices")}
                        debounceMs={500}
                      >
                        <div className="text-xl sm:text-2xl mb-2 group-hover:scale-110 transition-transform">📢</div>
                        <div className="text-sm sm:text-base group-hover:text-orange-600 transition-colors">공지사항</div>
                      </Button>
                      <Button 
                        variant="outline" 
                        className="h-16 sm:h-20 flex flex-col transition-all duration-300 hover:scale-105 hover:shadow-lg group border-2 hover:border-purple-300 btn-touch-optimized"
                        onClick={() => handleUnavailablePage("고객지원")}
                      >
                        <div className="text-xl sm:text-2xl mb-2 group-hover:scale-110 transition-transform">💬</div>
                        <div className="text-sm sm:text-base group-hover:text-purple-600 transition-colors">고객지원</div>
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* 계정 정보 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg sm:text-xl">계정 정보</CardTitle>
                    <CardDescription className="text-sm">기본 계정 정보를 확인하세요</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-500">이름</label>
                        <p className="text-gray-900 text-sm sm:text-base">{session.user?.name || "설정되지 않음"}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">이메일</label>
                        <p className="text-gray-900 text-sm sm:text-base break-all">{session.user?.email}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">사용자명</label>
                        <p className="text-gray-900 text-sm sm:text-base">{session.user?.username || "설정되지 않음"}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">계정 유형</label>
                        <p className="text-gray-900 text-sm sm:text-base">
                          {session.user?.isAdmin ? "관리자" : "일반 사용자"}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* 내 예약 탭 */}
              <TabsContent value="reservations" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <span className="text-lg sm:text-xl">내 예약 목록</span>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => router.push("/Reservations/reservations")}
                        className="btn-touch-optimized w-full sm:w-auto"
                      >
                        새 예약
                      </Button>
                    </CardTitle>
                    <CardDescription className="text-sm">예약 내역을 확인하고 관리하세요</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="text-center py-8">
                        <div className="text-base sm:text-lg">로딩 중...</div>
                      </div>
                    ) : reservations.length > 0 ? (
                      <div className="space-y-4">
                        {reservations.map((reservation) => (
                          <div key={reservation.id} className="border rounded-lg p-4">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2 gap-2">
                              <h3 className="font-medium text-sm sm:text-base">{reservation.description}</h3>
                              {getStatusBadge(reservation.status)}
                            </div>
                            <div className="text-sm text-gray-600 space-y-1">
                              <p>📅 {reservation.date} {reservation.time}</p>
                              <p>📝 {getTypeLabel(reservation.type)}</p>
                              {reservation.notes && <p>📝 {reservation.notes}</p>}
                            </div>
                            <Separator className="my-3" />
                            <div className="flex flex-col sm:flex-row gap-2">
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => router.push(`/Reservations/${reservation.id}/edit`)}
                                debounceMs={500}
                                className="btn-touch-optimized"
                              >
                                수정
                              </Button>
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => handleCancelReservation(reservation.id)}
                                disabled={reservation.status === 'cancelled' || reservation.status === 'completed'}
                                loading={loading}
                                debounceMs={1000}
                                className="btn-touch-optimized"
                              >
                                취소
                              </Button>
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => router.push(`/Reservations/${reservation.id}`)}
                                debounceMs={500}
                                className="btn-touch-optimized"
                              >
                                상세보기
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <div className="text-3xl sm:text-4xl mb-4">📝</div>
                        <p className="text-sm sm:text-base">예약 내역이 없습니다.</p>
                        <Button 
                          variant="link" 
                          className="mt-2 btn-touch-optimized"
                          onClick={() => router.push("/Reservations/reservations")}
                        >
                          첫 예약 하기
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* 설정 탭 */}
              <TabsContent value="settings" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg sm:text-xl">계정 설정</CardTitle>
                    <CardDescription className="text-sm">보안 및 개인정보 설정</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start group hover:shadow-md transition-all duration-300 hover:border-blue-300 btn-touch-optimized"
                      onClick={() => handleUnavailablePage("비밀번호 변경")}
                    >
                      <span className="mr-2 group-hover:scale-110 transition-transform">🔒</span>
                      <span className="group-hover:text-blue-600 transition-colors text-sm sm:text-base">비밀번호 변경</span>
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start group hover:shadow-md transition-all duration-300 hover:border-yellow-300 btn-touch-optimized"
                      onClick={() => handleUnavailablePage("알림 설정")}
                    >
                      <span className="mr-2 group-hover:scale-110 transition-transform">🔔</span>
                      <span className="group-hover:text-yellow-600 transition-colors text-sm sm:text-base">알림 설정</span>
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start group hover:shadow-md transition-all duration-300 hover:border-green-300 btn-touch-optimized"
                      onClick={() => handleUnavailablePage("개인정보 설정")}
                    >
                      <span className="mr-2 group-hover:scale-110 transition-transform">🛡️</span>
                      <span className="group-hover:text-green-600 transition-colors text-sm sm:text-base">개인정보 설정</span>
                    </Button>
                    <Separator />
                    <Button 
                      variant="outline" 
                      className="w-full justify-start group hover:shadow-md transition-all duration-300 hover:border-indigo-300 btn-touch-optimized"
                      onClick={() => handleUnavailablePage("데이터 내보내기")}
                    >
                      <span className="mr-2 group-hover:scale-110 transition-transform">📤</span>
                      <span className="group-hover:text-indigo-600 transition-colors text-sm sm:text-base">데이터 내보내기</span>
                    </Button>
                    <Button 
                      variant="destructive" 
                      className="w-full justify-start group hover:shadow-lg transition-all duration-300 btn-touch-optimized"
                      onClick={() => handleUnavailablePage("계정 삭제")}
                    >
                      <span className="mr-2 group-hover:scale-110 transition-transform">🗑️</span>
                      <span className="group-hover:text-red-100 transition-colors text-sm sm:text-base">계정 삭제</span>
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
} 