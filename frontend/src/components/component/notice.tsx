/**
 * 공지사항 컴포넌트
 * 공지사항 목록 조회, 작성, 수정, 삭제 기능 제공
 */
"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/lib/toast";
import { 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  Search, 
  Filter,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

// 공지사항 타입 정의
interface Notice {
  id: number;
  title: string;
  content: string;
  author: string;
  created_at: string;
  updated_at: string;
  is_important: boolean;
  view_count: number;
}

export function Notice() {
  const router = useRouter();
  const { data: session } = useSession();
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedNotice, setSelectedNotice] = useState<Notice | null>(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);

  // 새 공지사항 폼 상태
  const [newNotice, setNewNotice] = useState({
    title: "",
    content: "",
    is_important: false
  });

  // 공지사항 목록 가져오기
  const fetchNotices = async () => {
    setLoading(true);
    try {
      // TODO: 실제 API 호출로 교체
      const mockNotices: Notice[] = [
        {
          id: 1,
          title: "아파트 입주 안내",
          content: "아파트 입주와 관련된 중요한 안내사항입니다. 입주 시 필요한 서류와 절차에 대해 상세히 설명드립니다.",
          author: "관리사무소",
          created_at: "2024-12-20T10:00:00Z",
          updated_at: "2024-12-20T10:00:00Z",
          is_important: true,
          view_count: 125
        },
        {
          id: 2,
          title: "이사 예약 확인 방법 안내",
          content: "이사 예약을 확인하는 방법에 대한 안내입니다. 예약 시스템 사용법과 주의사항을 확인해주세요.",
          author: "관리사무소",
          created_at: "2024-12-19T14:30:00Z",
          updated_at: "2024-12-19T14:30:00Z",
          is_important: false,
          view_count: 89
        },
        {
          id: 3,
          title: "1차 하자 신고 안내 및 방법",
          content: "아파트 하자 신고 절차와 방법에 대한 안내입니다. 신고 기간과 처리 절차를 확인해주세요.",
          author: "관리사무소",
          created_at: "2024-12-18T09:00:00Z",
          updated_at: "2024-12-18T09:00:00Z",
          is_important: false,
          view_count: 156
        },
        {
          id: 4,
          title: "아파트 대표자 선거 일정 안내",
          content: "아파트 대표자 선거 일정과 관련된 공지사항입니다. 선거 일정과 투표 방법을 확인해주세요.",
          author: "관리사무소",
          created_at: "2024-12-17T16:00:00Z",
          updated_at: "2024-12-17T16:00:00Z",
          is_important: true,
          view_count: 203
        }
      ];
      
      setNotices(mockNotices);
      setTotalPages(Math.ceil(mockNotices.length / pageSize));
      toast.success("공지사항을 불러왔습니다.");
    } catch (error) {
      console.error("공지사항 조회 실패:", error);
      toast.error("공지사항을 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotices();
  }, [page, searchTerm]);

  // 공지사항 상세보기
  const handleViewNotice = (notice: Notice) => {
    setSelectedNotice(notice);
    setShowDetailDialog(true);
  };

  // 공지사항 생성
  const handleCreateNotice = async () => {
    if (!newNotice.title.trim() || !newNotice.content.trim()) {
      toast.error("제목과 내용을 입력해주세요.");
      return;
    }

    try {
      // TODO: 실제 API 호출로 교체
      const mockNewNotice: Notice = {
        id: notices.length + 1,
        title: newNotice.title,
        content: newNotice.content,
        author: session?.user?.name || "관리자",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_important: newNotice.is_important,
        view_count: 0
      };

      setNotices([mockNewNotice, ...notices]);
      setNewNotice({ title: "", content: "", is_important: false });
      setShowCreateDialog(false);
      toast.success("공지사항이 작성되었습니다.");
    } catch (error) {
      console.error("공지사항 작성 실패:", error);
      toast.error("공지사항 작성에 실패했습니다.");
    }
  };

  // 공지사항 수정
  const handleEditNotice = (notice: Notice) => {
    setSelectedNotice(notice);
    setNewNotice({
      title: notice.title,
      content: notice.content,
      is_important: notice.is_important
    });
    setShowEditDialog(true);
  };

  // 공지사항 수정 저장
  const handleUpdateNotice = async () => {
    if (!selectedNotice || !newNotice.title.trim() || !newNotice.content.trim()) {
      toast.error("제목과 내용을 입력해주세요.");
      return;
    }

    try {
      // TODO: 실제 API 호출로 교체
      const updatedNotices = notices.map(notice => 
        notice.id === selectedNotice.id 
          ? {
              ...notice,
              title: newNotice.title,
              content: newNotice.content,
              is_important: newNotice.is_important,
              updated_at: new Date().toISOString()
            }
          : notice
      );

      setNotices(updatedNotices);
      setNewNotice({ title: "", content: "", is_important: false });
      setSelectedNotice(null);
      setShowEditDialog(false);
      toast.success("공지사항이 수정되었습니다.");
    } catch (error) {
      console.error("공지사항 수정 실패:", error);
      toast.error("공지사항 수정에 실패했습니다.");
    }
  };

  // 공지사항 삭제
  const handleDeleteNotice = async (noticeId: number) => {
    if (!confirm("정말로 이 공지사항을 삭제하시겠습니까?")) {
      return;
    }

    try {
      // TODO: 실제 API 호출로 교체
      const filteredNotices = notices.filter(notice => notice.id !== noticeId);
      setNotices(filteredNotices);
      toast.success("공지사항이 삭제되었습니다.");
    } catch (error) {
      console.error("공지사항 삭제 실패:", error);
      toast.error("공지사항 삭제에 실패했습니다.");
    }
  };

  // 날짜 포맷팅
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  // 필터링된 공지사항
  const filteredNotices = notices.filter(notice =>
    notice.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    notice.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      {/* 헤더 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">공지사항</h1>
        <p className="text-gray-600">아파트 관련 중요한 공지사항을 확인하세요</p>
      </div>

      {/* 검색 및 액션 바 */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="공지사항 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        {session?.user?.isAdmin && (
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            공지사항 작성
          </Button>
        )}
      </div>

      {/* 공지사항 목록 */}
      <Card className="shadow-sm border-0 bg-white">
        <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
          <CardTitle className="text-xl text-gray-800 flex items-center gap-2">
            <span className="text-2xl">📢</span>
            전체 공지사항
          </CardTitle>
          <CardDescription className="text-gray-600">
            총 <span className="font-semibold text-blue-600">{filteredNotices.length}개</span>의 공지사항이 있습니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <div className="text-lg mt-4 text-gray-600">로딩 중...</div>
            </div>
          ) : filteredNotices.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-50/50 hover:bg-gray-50/80">
                  <TableHead className="font-semibold text-gray-700 py-4">제목</TableHead>
                  <TableHead className="font-semibold text-gray-700 py-4">작성자</TableHead>
                  <TableHead className="font-semibold text-gray-700 py-4">작성일</TableHead>
                  <TableHead className="font-semibold text-gray-700 py-4">조회수</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredNotices.map((notice) => (
                  <TableRow 
                    key={notice.id} 
                    className="cursor-pointer hover:bg-blue-50/50 transition-colors duration-200 border-b border-gray-100"
                    onClick={() => handleViewNotice(notice)}
                  >
                    <TableCell className="font-medium py-4">
                      <div className="flex items-center gap-3">
                        {notice.is_important && (
                          <Badge variant="destructive" className="px-2 py-1 text-xs">
                            <span className="mr-1">🔥</span>
                            중요
                          </Badge>
                        )}
                        <span className="text-gray-900 hover:text-blue-600 transition-colors">
                          {notice.title}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-blue-600 text-xs">👤</span>
                        </div>
                        <span className="text-gray-700">{notice.author}</span>
                      </div>
                    </TableCell>
                    <TableCell className="py-4 text-gray-600">
                      {formatDate(notice.created_at)}
                    </TableCell>
                    <TableCell className="py-4">
                      <div className="flex items-center gap-1 text-gray-600">
                        <span className="text-purple-600">👁️</span>
                        <span>{notice.view_count}</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-16 text-gray-500">
              <div className="text-6xl mb-6 opacity-50">📢</div>
              <p className="text-lg font-medium mb-2">공지사항이 없습니다</p>
              <p className="text-sm text-gray-400">새로운 공지사항을 작성해보세요</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex justify-center mt-6 gap-2">
          <Button 
            variant="outline" 
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="flex items-center px-4">
            {page} / {totalPages}
          </span>
          <Button 
            variant="outline" 
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* 공지사항 상세보기 다이얼로그 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader className="space-y-4 pb-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <DialogTitle className="text-2xl font-bold leading-relaxed pr-8">
                  <div className="flex items-center gap-3 mb-2">
                    {selectedNotice?.is_important && (
                      <Badge variant="destructive" className="px-3 py-1">
                        <span className="text-xs font-semibold">🔥 중요</span>
                      </Badge>
                    )}
                  </div>
                  {selectedNotice?.title}
                </DialogTitle>
              </div>
            </div>
            
            {/* 메타 정보 카드 */}
            <div className="bg-gray-50 rounded-lg p-4 border">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 text-sm">👤</span>
                  </div>
                  <div>
                    <p className="text-gray-500">작성자</p>
                    <p className="font-medium text-gray-900">{selectedNotice?.author}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 text-sm">📅</span>
                  </div>
                  <div>
                    <p className="text-gray-500">작성일</p>
                    <p className="font-medium text-gray-900">
                      {selectedNotice && formatDate(selectedNotice.created_at)}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <span className="text-purple-600 text-sm">👁️</span>
                  </div>
                  <div>
                    <p className="text-gray-500">조회수</p>
                    <p className="font-medium text-gray-900">{selectedNotice?.view_count}회</p>
                  </div>
                </div>
              </div>
            </div>
          </DialogHeader>
          
          {/* 본문 내용 */}
          <div className="py-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="prose prose-gray max-w-none">
                <div className="text-gray-800 leading-relaxed whitespace-pre-wrap text-base">
                  {selectedNotice?.content}
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 공지사항 작성 다이얼로그 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader className="space-y-3 pb-6">
            <DialogTitle className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <Plus className="h-5 w-5 text-blue-600" />
              </div>
              새 공지사항 작성
            </DialogTitle>
            <p className="text-gray-600">아파트 입주민들에게 중요한 정보를 전달하세요</p>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* 제목 입력 */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <span className="text-blue-600">📝</span>
                제목
                <span className="text-red-500">*</span>
              </label>
              <Input
                placeholder="공지사항 제목을 입력하세요 (예: 아파트 입주 안내)"
                value={newNotice.title}
                onChange={(e) => setNewNotice({ ...newNotice, title: e.target.value })}
                className="text-base p-3 border-2 focus:border-blue-500 transition-colors"
              />
            </div>
            
            {/* 내용 입력 */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <span className="text-green-600">📄</span>
                내용
                <span className="text-red-500">*</span>
              </label>
              <Textarea
                placeholder="공지사항 내용을 자세히 입력하세요..."
                value={newNotice.content}
                onChange={(e) => setNewNotice({ ...newNotice, content: e.target.value })}
                rows={10}
                className="text-base p-3 border-2 focus:border-blue-500 transition-colors resize-none"
              />
              <p className="text-xs text-gray-500">
                현재 {newNotice.content.length}자 | 최소 10자 이상 입력해주세요
              </p>
            </div>
            
            {/* 중요 공지사항 설정 */}
            <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="important"
                  checked={newNotice.is_important}
                  onChange={(e) => setNewNotice({ ...newNotice, is_important: e.target.checked })}
                  className="w-4 h-4 text-orange-600 border-2 border-orange-300 rounded focus:ring-orange-500"
                />
                <label htmlFor="important" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <span className="text-orange-600">🔥</span>
                  중요 공지사항으로 설정
                </label>
              </div>
              <p className="text-xs text-gray-600 mt-2 ml-7">
                중요 공지사항은 목록 상단에 표시되며 빨간색 배지가 표시됩니다
              </p>
            </div>
          </div>
          
          {/* 하단 버튼 */}
          <div className="flex gap-3 justify-end pt-6 border-t mt-6">
            <Button 
              variant="outline" 
              onClick={() => setShowCreateDialog(false)}
              className="px-6"
            >
              취소
            </Button>
            <Button 
              onClick={handleCreateNotice}
              disabled={!newNotice.title.trim() || !newNotice.content.trim()}
              className="px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300"
            >
              <Plus className="h-4 w-4 mr-2" />
              공지사항 작성
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* 공지사항 수정 다이얼로그 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader className="space-y-3 pb-6">
            <DialogTitle className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <Edit className="h-5 w-5 text-green-600" />
              </div>
              공지사항 수정
            </DialogTitle>
            <p className="text-gray-600">공지사항 내용을 수정합니다</p>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* 제목 입력 */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <span className="text-blue-600">📝</span>
                제목
                <span className="text-red-500">*</span>
              </label>
              <Input
                placeholder="공지사항 제목을 입력하세요"
                value={newNotice.title}
                onChange={(e) => setNewNotice({ ...newNotice, title: e.target.value })}
                className="text-base p-3 border-2 focus:border-blue-500 transition-colors"
              />
            </div>
            
            {/* 내용 입력 */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <span className="text-green-600">📄</span>
                내용
                <span className="text-red-500">*</span>
              </label>
              <Textarea
                placeholder="공지사항 내용을 자세히 입력하세요..."
                value={newNotice.content}
                onChange={(e) => setNewNotice({ ...newNotice, content: e.target.value })}
                rows={10}
                className="text-base p-3 border-2 focus:border-blue-500 transition-colors resize-none"
              />
              <p className="text-xs text-gray-500">
                현재 {newNotice.content.length}자
              </p>
            </div>
            
            {/* 중요 공지사항 설정 */}
            <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="important-edit"
                  checked={newNotice.is_important}
                  onChange={(e) => setNewNotice({ ...newNotice, is_important: e.target.checked })}
                  className="w-4 h-4 text-orange-600 border-2 border-orange-300 rounded focus:ring-orange-500"
                />
                <label htmlFor="important-edit" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <span className="text-orange-600">🔥</span>
                  중요 공지사항으로 설정
                </label>
              </div>
              <p className="text-xs text-gray-600 mt-2 ml-7">
                중요 공지사항은 목록 상단에 표시되며 빨간색 배지가 표시됩니다
              </p>
            </div>
          </div>
          
          {/* 하단 버튼 */}
          <div className="flex gap-3 justify-end pt-6 border-t mt-6">
            <Button 
              variant="outline" 
              onClick={() => setShowEditDialog(false)}
              className="px-6"
            >
              취소
            </Button>
            <Button 
              onClick={handleUpdateNotice}
              disabled={!newNotice.title.trim() || !newNotice.content.trim()}
              className="px-6 bg-green-600 hover:bg-green-700 disabled:bg-gray-300"
            >
              <Edit className="h-4 w-4 mr-2" />
              수정 완료
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
