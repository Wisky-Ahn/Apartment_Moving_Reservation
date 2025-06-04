/**
 * 사용자 프로필 페이지
 * 로그인한 사용자의 정보 및 예약 내역을 표시
 */
"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { reservationApi, type Reservation } from "@/lib/api";
import { toast } from "@/lib/toast";

export default function UserPage() {
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

  const getStatusBadge = (status: string) => {
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
  };

  const getTypeLabel = (type: string) => {
    const typeConfig = {
      moving: "이사",
      inspection: "점검",
      maintenance: "정비"
    };
    
    return typeConfig[type as keyof typeof typeConfig] || type;
  };

  // 예약 취소 핸들러
  const handleCancelReservation = async (id: number) => {
    if (!confirm("정말로 이 예약을 취소하시겠습니까?")) {
      return;
    }

    try {
      await reservationApi.cancelReservation(id);
      toast.success("예약이 취소되었습니다.");
      fetchMyReservations(); // 목록 새로고침
    } catch (error) {
      console.error("예약 취소 실패:", error);
      toast.error("예약 취소에 실패했습니다.");
    }
  };

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
                <Avatar className="w-24 h-24 mx-auto mb-4">
                  <AvatarImage src={""} alt="프로필 이미지" />
                  <AvatarFallback className="text-2xl">
                    {session.user?.name?.[0] || session.user?.email?.[0] || "U"}
                  </AvatarFallback>
                </Avatar>
                <CardTitle className="text-xl">{session.user?.name || "사용자"}</CardTitle>
                <CardDescription>{session.user?.email}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => router.push("/profile/edit")}
                >
                  프로필 수정
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => setActiveTab("reservations")}
                >
                  내 예약 보기
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full"
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
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="profile">프로필</TabsTrigger>
                <TabsTrigger value="reservations">내 예약</TabsTrigger>
                <TabsTrigger value="settings">설정</TabsTrigger>
              </TabsList>

              {/* 프로필 탭 */}
              <TabsContent value="profile" className="space-y-6">
                {/* 빠른 액션 */}
                <Card>
                  <CardHeader>
                    <CardTitle>빠른 액션</CardTitle>
                    <CardDescription>자주 사용하는 기능들</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <Button 
                        variant="outline" 
                        className="h-20 flex flex-col"
                        onClick={() => router.push("/Reservations/reservations")}
                      >
                        <div className="text-2xl mb-2">📅</div>
                        <div>새 예약</div>
                      </Button>
                      <Button 
                        variant="outline" 
                        className="h-20 flex flex-col"
                        onClick={() => setActiveTab("reservations")}
                      >
                        <div className="text-2xl mb-2">📋</div>
                        <div>내 예약</div>
                      </Button>
                      <Button 
                        variant="outline" 
                        className="h-20 flex flex-col"
                        onClick={() => router.push("/Notices/notices")}
                      >
                        <div className="text-2xl mb-2">📢</div>
                        <div>공지사항</div>
                      </Button>
                      <Button 
                        variant="outline" 
                        className="h-20 flex flex-col"
                        onClick={() => router.push("/support")}
                      >
                        <div className="text-2xl mb-2">💬</div>
                        <div>고객지원</div>
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* 계정 정보 */}
                <Card>
                  <CardHeader>
                    <CardTitle>계정 정보</CardTitle>
                    <CardDescription>기본 계정 정보를 확인하세요</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-500">이름</label>
                        <p className="text-gray-900">{session.user?.name || "설정되지 않음"}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">이메일</label>
                        <p className="text-gray-900">{session.user?.email}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">사용자명</label>
                        <p className="text-gray-900">{session.user?.username || "설정되지 않음"}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">계정 유형</label>
                        <p className="text-gray-900">
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
                    <CardTitle className="flex items-center justify-between">
                      내 예약 목록
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => router.push("/Reservations/reservations")}
                      >
                        새 예약
                      </Button>
                    </CardTitle>
                    <CardDescription>예약 내역을 확인하고 관리하세요</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="text-center py-8">
                        <div className="text-lg">로딩 중...</div>
                      </div>
                    ) : reservations.length > 0 ? (
                      <div className="space-y-4">
                        {reservations.map((reservation) => (
                          <div key={reservation.id} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="font-medium">{reservation.description}</h3>
                              {getStatusBadge(reservation.status)}
                            </div>
                            <div className="text-sm text-gray-600 space-y-1">
                              <p>📅 {reservation.date} {reservation.time}</p>
                              <p>📝 {getTypeLabel(reservation.type)}</p>
                              {reservation.notes && <p>📝 {reservation.notes}</p>}
                            </div>
                            <Separator className="my-3" />
                            <div className="flex gap-2">
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => router.push(`/reservations/${reservation.id}/edit`)}
                              >
                                수정
                              </Button>
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => handleCancelReservation(reservation.id)}
                                disabled={reservation.status === 'cancelled' || reservation.status === 'completed'}
                              >
                                취소
                              </Button>
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => router.push(`/reservations/${reservation.id}`)}
                              >
                                상세보기
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <div className="text-4xl mb-4">📝</div>
                        <p>예약 내역이 없습니다.</p>
                        <Button 
                          variant="link" 
                          className="mt-2"
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
                    <CardTitle>계정 설정</CardTitle>
                    <CardDescription>보안 및 개인정보 설정</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => router.push("/profile/password")}
                    >
                      🔒 비밀번호 변경
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => router.push("/profile/notifications")}
                    >
                      🔔 알림 설정
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => router.push("/profile/privacy")}
                    >
                      🛡️ 개인정보 설정
                    </Button>
                    <Separator />
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => router.push("/profile/export")}
                    >
                      📤 데이터 내보내기
                    </Button>
                    <Button 
                      variant="destructive" 
                      className="w-full justify-start"
                      onClick={() => router.push("/profile/delete")}
                    >
                      🗑️ 계정 삭제
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