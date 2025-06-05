/**
 * 관리자 공지사항 관리 페이지
 * 공지사항의 생성, 수정, 삭제 및 상태 관리 기능
 */
"use client";

import React, { useState, useEffect } from 'react';
import { AdminGuard } from '../../../../lib/auth/admin-guard';
import { AdminLayout } from '@/components/admin/admin-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  FileText, 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  Trash2, 
  Eye,
  Pin,
  PinOff,
  ToggleLeft,
  ToggleRight,
  Star,
  Clock
} from 'lucide-react';
import { api } from '@/lib/api'; // API 클라이언트 import 추가
import { getSession } from 'next-auth/react';
import { getCurrentAuthToken } from '@/lib/api';

// 공지사항 타입 정의
interface Notice {
  id: number;
  title: string;
  content: string;
  notice_type: 'general' | 'announcement' | 'event';
  is_pinned: boolean;
  is_important: boolean;
  is_active: boolean;
  view_count: number;
  author_id: number;
  author_name?: string;
  created_at: string;
  updated_at: string;
  published_at?: string;
}

interface NoticeStats {
  total_notices: number;
  active_notices: number;
  pinned_notices: number;
  important_notices: number;
  draft_notices: number;
  total_views: number;
}

interface NoticeFormData {
  title: string;
  content: string;
  notice_type: 'general' | 'announcement' | 'event';
  is_pinned: boolean;
  is_important: boolean;
  is_active: boolean;
}

/**
 * 공지사항 상태 배지 컴포넌트
 */
function NoticeStatusBadge({ notice }: { notice: Notice }) {
  const badges = [];
  
  if (notice.is_pinned) {
    badges.push(<Badge key="pinned" className="bg-red-600">고정</Badge>);
  }
  if (notice.is_important) {
    badges.push(<Badge key="important" className="bg-yellow-600">중요</Badge>);
  }
  if (!notice.is_active) {
    badges.push(<Badge key="inactive" variant="destructive">비활성</Badge>);
  }
  
  // 공지사항 유형별 배지
  const typeColors = {
    general: "bg-blue-600",
    announcement: "bg-orange-600", 
    event: "bg-green-600"
  };
  
  const typeNames = {
    general: "일반",
    announcement: "공지",
    event: "이벤트"
  };
  
  badges.push(
    <Badge key="type" className={typeColors[notice.notice_type]}>
      {typeNames[notice.notice_type]}
    </Badge>
  );
  
  return <div className="flex gap-1 flex-wrap">{badges}</div>;
}

/**
 * 공지사항 상세 보기 다이얼로그
 */
function NoticeDetailDialog({ notice }: { notice: Notice }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)}>
        <Eye className="h-4 w-4 mr-1" />
        보기
      </Button>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {notice.title}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <NoticeStatusBadge notice={notice} />
              <div className="text-sm text-gray-500">
                조회수: {notice.view_count}회
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-500">내용</label>
              <div 
                className="mt-1 p-4 border rounded-md bg-gray-50 whitespace-pre-wrap"
                dangerouslySetInnerHTML={{ __html: notice.content }}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="font-medium text-gray-500">작성일</label>
                <p>{new Date(notice.created_at).toLocaleString('ko-KR')}</p>
              </div>
              <div>
                <label className="font-medium text-gray-500">수정일</label>
                <p>{new Date(notice.updated_at).toLocaleString('ko-KR')}</p>
              </div>
              {notice.published_at && (
                <div>
                  <label className="font-medium text-gray-500">게시일</label>
                  <p>{new Date(notice.published_at).toLocaleString('ko-KR')}</p>
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

/**
 * 공지사항 작성/편집 폼 다이얼로그
 */
function NoticeFormDialog({ 
  notice, 
  onNoticeUpdated,
  trigger 
}: { 
  notice?: Notice; 
  onNoticeUpdated: () => void;
  trigger: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<NoticeFormData>({
    title: notice?.title || '',
    content: notice?.content || '',
    notice_type: notice?.notice_type || 'general',
    is_pinned: notice?.is_pinned || false,
    is_important: notice?.is_important || false,
    is_active: notice?.is_active || true
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 프론트엔드 validation 추가
    if (formData.title.trim().length < 5) {
      alert('제목은 최소 5자 이상이어야 합니다.');
      return;
    }
    
    if (formData.content.trim().length < 10) {
      alert('내용은 최소 10자 이상이어야 합니다.');
      return;
    }
    
    setIsSubmitting(true);

    try {
      // 전송할 데이터 구성
      const requestData = {
        title: formData.title.trim(),
        content: formData.content.trim(),
        notice_type: formData.notice_type,
        is_pinned: formData.is_pinned,
        is_important: formData.is_important
      };
      
      // 디버깅을 위한 로깅
      console.log('📤 공지사항 전송 데이터:', requestData);

      if (notice) {
        // 수정 - API 클라이언트 사용
        const response = await api.put(`/api/notices/${notice.id}`, requestData);
        console.log('✅ 공지사항 수정 응답:', response);
      } else {
        // 생성 - API 클라이언트 사용  
        const response = await api.post('/api/notices/', requestData);
        console.log('✅ 공지사항 생성 응답:', response);
      }

      setIsOpen(false);
      onNoticeUpdated();
      alert(notice ? '공지사항이 수정되었습니다.' : '공지사항이 작성되었습니다.');
    } catch (error: any) {
      console.error('❌ 공지사항 저장 실패:', error);
      console.error('❌ 응답 데이터:', error.response?.data);
      
      const errorMsg = error.response?.data?.detail || error.message || '알 수 없는 오류가 발생했습니다.';
      alert('공지사항 저장에 실패했습니다: ' + errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <div onClick={() => setIsOpen(true)}>
        {trigger}
      </div>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {notice ? '공지사항 수정' : '새 공지사항 작성'}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-1">제목</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="공지사항 제목을 입력하세요"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">공지 유형</label>
                <select
                  value={formData.notice_type}
                  onChange={(e) => setFormData({ ...formData, notice_type: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="general">일반</option>
                  <option value="announcement">공지</option>
                  <option value="event">이벤트</option>
                </select>
              </div>
              <div className="flex items-end">
                <div className="space-y-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.is_pinned}
                      onChange={(e) => setFormData({ ...formData, is_pinned: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm">상단 고정</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.is_important}
                      onChange={(e) => setFormData({ ...formData, is_important: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm">중요 공지</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm">즉시 게시</span>
                  </label>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">내용</label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="w-full h-64 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="공지사항 내용을 입력하세요"
                required
              />
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsOpen(false)}
                disabled={isSubmitting}
              >
                취소
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? '저장 중...' : (notice ? '수정' : '작성')}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}

/**
 * 관리자 공지사항 관리 페이지
 */
export default function AdminNotices() {
  const [notices, setNotices] = useState<Notice[]>([]);
  const [stats, setStats] = useState<NoticeStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 필터 및 검색 상태
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  
  // 페이지네이션
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  // 디버깅용: 컴포넌트 로드 시 토큰 상태 확인
  useEffect(() => {
    console.log('🔍 AdminNotices 컴포넌트 로드됨');
    
    const checkToken = async () => {
      const session = await getSession();
      console.log('🔍 세션 정보:', session);
      console.log('🔍 액세스 토큰:', session?.accessToken ? '존재' : '없음');
      
      const currentToken = getCurrentAuthToken();
      console.log('🔍 현재 설정된 토큰:', currentToken ? '존재' : '없음');
    };
    
    checkToken();
  }, []);

  /**
   * 공지사항 목록 조회
   */
  const fetchNotices = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams({
        skip: ((currentPage - 1) * itemsPerPage).toString(),
        limit: itemsPerPage.toString(),
      });

      if (searchTerm) params.append('search', searchTerm);
      if (filterType !== 'all') params.append('notice_type', filterType);
      
      if (filterStatus === 'active') params.append('is_active', 'true');
      else if (filterStatus === 'inactive') params.append('is_active', 'false');
      else if (filterStatus === 'pinned') params.append('is_pinned', 'true');
      else if (filterStatus === 'important') params.append('is_important', 'true');

      // API 클라이언트 사용
      const data = await api.get(`/api/notices/?${params}`);
      setNotices(data.notices || data);
    } catch (error: any) {
      console.error('공지사항 목록 조회 실패:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 공지사항 통계 조회
   */
  const fetchStats = async () => {
    try {
      // API 클라이언트 사용
      const data = await api.get('/api/notices/stats');
      setStats(data.data || data);
    } catch (error) {
      console.error('공지사항 통계 조회 실패:', error);
    }
  };

  /**
   * 공지사항 고정 토글
   */
  const togglePin = async (noticeId: number) => {
    try {
      // API 클라이언트 사용
      const response = await api.put(`/api/notices/${noticeId}/toggle-pin`);

      fetchNotices();
      fetchStats();
      alert('공지사항 고정 상태가 변경되었습니다.');
    } catch (error: any) {
      console.error('공지사항 고정 설정 실패:', error);
      alert('공지사항 고정 설정에 실패했습니다: ' + error.message);
    }
  };

  /**
   * 공지사항 활성화 토글
   */
  const toggleActive = async (noticeId: number) => {
    try {
      // API 클라이언트 사용
      const response = await api.put(`/api/notices/${noticeId}/toggle-active`);

      fetchNotices();
      fetchStats();
      alert('공지사항 활성화 상태가 변경되었습니다.');
    } catch (error: any) {
      console.error('공지사항 활성화 설정 실패:', error);
      alert('공지사항 활성화 설정에 실패했습니다: ' + error.message);
    }
  };

  /**
   * 공지사항 삭제
   */
  const deleteNotice = async (noticeId: number, title: string) => {
    if (!confirm(`정말로 '${title}' 공지사항을 삭제하시겠습니까?`)) {
      return;
    }

    try {
      // API 클라이언트 사용
      const response = await api.delete(`/api/notices/${noticeId}`);

      fetchNotices();
      fetchStats();
      alert('공지사항이 삭제되었습니다.');
    } catch (error: any) {
      console.error('공지사항 삭제 실패:', error);
      alert('공지사항 삭제에 실패했습니다: ' + error.message);
    }
  };

  // 데이터 로드
  useEffect(() => {
    fetchNotices();
    fetchStats();
  }, [currentPage, searchTerm, filterType, filterStatus]);

  // 검색어나 필터 변경 시 첫 페이지로 이동
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, filterType, filterStatus]);

  if (isLoading && notices.length === 0) {
    return (
      <AdminGuard>
        <AdminLayout>
          <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">공지사항 데이터를 불러오는 중...</p>
            </div>
          </div>
        </AdminLayout>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard>
      <AdminLayout>
        <div className="space-y-6">
          {/* 페이지 헤더 */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">공지사항 관리</h1>
              <p className="text-gray-600">아파트 공지사항 작성 및 관리</p>
            </div>
            <NoticeFormDialog
              onNoticeUpdated={() => {
                fetchNotices();
                fetchStats();
              }}
              trigger={
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  새 공지사항 작성
                </Button>
              }
            />
          </div>

          {/* 통계 카드들 */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-blue-600">{stats.total_notices}</div>
                  <div className="text-sm text-gray-600">총 공지사항</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-green-600">{stats.active_notices}</div>
                  <div className="text-sm text-gray-600">활성 공지</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-red-600">{stats.pinned_notices}</div>
                  <div className="text-sm text-gray-600">고정 공지</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-yellow-600">{stats.important_notices}</div>
                  <div className="text-sm text-gray-600">중요 공지</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-gray-600">{stats.draft_notices}</div>
                  <div className="text-sm text-gray-600">비활성 공지</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-purple-600">{stats.total_views}</div>
                  <div className="text-sm text-gray-600">총 조회수</div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 검색 및 필터 */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <input
                      type="text"
                      placeholder="제목, 내용으로 검색..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 w-full border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">모든 유형</option>
                    <option value="general">일반</option>
                    <option value="announcement">공지</option>
                    <option value="event">이벤트</option>
                  </select>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">모든 상태</option>
                    <option value="active">활성</option>
                    <option value="inactive">비활성</option>
                    <option value="pinned">고정</option>
                    <option value="important">중요</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 공지사항 목록 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <FileText className="h-5 w-5 mr-2" />
                  공지사항 목록
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchNotices()}
                  disabled={isLoading}
                >
                  새로고침
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {error ? (
                <div className="text-center py-8">
                  <p className="text-red-600">{error}</p>
                  <Button onClick={() => fetchNotices()} className="mt-4">
                    다시 시도
                  </Button>
                </div>
              ) : notices.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">공지사항이 없습니다.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {notices.map((notice) => (
                    <div
                      key={notice.id}
                      className="p-4 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-semibold text-lg">{notice.title}</h3>
                            <NoticeStatusBadge notice={notice} />
                          </div>
                          <p className="text-gray-600 text-sm line-clamp-2 mb-2">
                            {notice.content.replace(/<[^>]*>/g, '').substring(0, 150)}...
                          </p>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span className="flex items-center gap-1">
                              <Eye className="h-3 w-3" />
                              {notice.view_count}회
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {new Date(notice.created_at).toLocaleDateString('ko-KR')}
                            </span>
                          </div>
                        </div>
                        <div className="flex gap-1 ml-4">
                          <NoticeDetailDialog notice={notice} />
                          <NoticeFormDialog
                            notice={notice}
                            onNoticeUpdated={() => {
                              fetchNotices();
                              fetchStats();
                            }}
                            trigger={
                              <Button variant="outline" size="sm">
                                <Edit className="h-4 w-4 mr-1" />
                                편집
                              </Button>
                            }
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => togglePin(notice.id)}
                          >
                            {notice.is_pinned ? (
                              <PinOff className="h-4 w-4" />
                            ) : (
                              <Pin className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => toggleActive(notice.id)}
                          >
                            {notice.is_active ? (
                              <ToggleRight className="h-4 w-4 text-green-600" />
                            ) : (
                              <ToggleLeft className="h-4 w-4 text-gray-400" />
                            )}
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => deleteNotice(notice.id, notice.title)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 페이지네이션 */}
              {notices.length > 0 && (
                <div className="flex justify-center items-center space-x-2 mt-6">
                  <Button
                    variant="outline"
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  >
                    이전
                  </Button>
                  <span className="px-4 py-2 text-sm">
                    페이지 {currentPage}
                  </span>
                  <Button
                    variant="outline"
                    disabled={notices.length < itemsPerPage}
                    onClick={() => setCurrentPage(prev => prev + 1)}
                  >
                    다음
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </AdminLayout>
    </AdminGuard>
  );
} 