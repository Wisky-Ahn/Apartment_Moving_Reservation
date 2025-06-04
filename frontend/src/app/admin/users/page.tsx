/**
 * 관리자 사용자 관리 페이지
 * 아파트 입주민 정보 관리 및 사용자 계정 관리 기능
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
  Users, 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  Trash2, 
  UserCheck, 
  UserX,
  Eye,
  MoreHorizontal
} from 'lucide-react';

// 사용자 타입 정의
interface User {
  id: number;
  username: string;
  email: string;
  name: string;
  phone?: string;
  apartment_number?: string;
  is_admin: boolean;
  is_super_admin: boolean;
  admin_approved: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

interface UserStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  admin_users: number;
  pending_admins: number;
  recent_users: number;
}

/**
 * 사용자 상태 배지 컴포넌트
 */
function UserStatusBadge({ user }: { user: User }) {
  if (user.is_super_admin) {
    return <Badge className="bg-purple-600">슈퍼관리자</Badge>;
  }
  if (user.is_admin) {
    if (!user.admin_approved) {
      return <Badge variant="destructive">승인대기</Badge>;
    }
    return <Badge className="bg-blue-600">관리자</Badge>;
  }
  if (!user.is_active) {
    return <Badge variant="destructive">비활성</Badge>;
  }
  return <Badge className="bg-green-600">일반사용자</Badge>;
}

/**
 * 사용자 상세 정보 다이얼로그
 */
function UserDetailDialog({ user }: { user: User }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)}>
        <Eye className="h-4 w-4 mr-1" />
        보기
      </Button>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>사용자 상세 정보</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-500">이름</label>
              <p className="font-medium">{user.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">사용자명</label>
              <p>{user.username}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">이메일</label>
              <p>{user.email}</p>
            </div>
            {user.phone && (
              <div>
                <label className="text-sm font-medium text-gray-500">전화번호</label>
                <p>{user.phone}</p>
              </div>
            )}
            {user.apartment_number && (
              <div>
                <label className="text-sm font-medium text-gray-500">동/호수</label>
                <p>{user.apartment_number}</p>
              </div>
            )}
            <div>
              <label className="text-sm font-medium text-gray-500">상태</label>
              <div className="mt-1">
                <UserStatusBadge user={user} />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">가입일</label>
              <p>{new Date(user.created_at).toLocaleDateString('ko-KR')}</p>
            </div>
            {user.last_login && (
              <div>
                <label className="text-sm font-medium text-gray-500">최근 로그인</label>
                <p>{new Date(user.last_login).toLocaleDateString('ko-KR')}</p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

/**
 * 사용자 편집 다이얼로그
 */
function UserEditDialog({ user, onUserUpdated }: { user: User; onUserUpdated: () => void }) {
  const [formData, setFormData] = useState({
    name: user.name,
    email: user.email,
    phone: user.phone || '',
    apartment_number: user.apartment_number || ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch(`http://localhost:8000/api/users/${user.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('사용자 정보 수정에 실패했습니다.');
      }

      setIsOpen(false);
      onUserUpdated();
      alert('사용자 정보가 수정되었습니다.');
    } catch (error: any) {
      console.error('사용자 정보 수정 실패:', error);
      alert('사용자 정보 수정에 실패했습니다: ' + error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)}>
        <Edit className="h-4 w-4 mr-1" />
        편집
      </Button>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>사용자 정보 수정</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">이름</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">이메일</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">전화번호</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">동/호수</label>
              <input
                type="text"
                value={formData.apartment_number}
                onChange={(e) => setFormData({ ...formData, apartment_number: e.target.value })}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="예: 101동 501호"
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
                {isSubmitting ? '수정 중...' : '수정'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}

/**
 * 관리자 사용자 관리 페이지
 */
export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 필터 및 검색 상태
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive' | 'admin'>('all');
  const [apartmentFilter, setApartmentFilter] = useState('');
  
  // 페이지네이션
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  // 선택된 사용자들
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);

  /**
   * 사용자 목록 조회
   */
  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // 필터 파라미터 구성
      const params = new URLSearchParams({
        skip: ((currentPage - 1) * itemsPerPage).toString(),
        limit: itemsPerPage.toString(),
      });

      if (searchTerm) params.append('search', searchTerm);
      if (apartmentFilter) params.append('apartment_number', apartmentFilter);
      
      if (filterStatus === 'active') params.append('is_active', 'true');
      else if (filterStatus === 'inactive') params.append('is_active', 'false');
      else if (filterStatus === 'admin') params.append('is_admin', 'true');

      const response = await fetch(`http://localhost:8000/api/users/admin/users?${params}`);
      
      if (!response.ok) {
        throw new Error('사용자 목록을 가져오는데 실패했습니다.');
      }

      const data = await response.json();
      setUsers(data);
    } catch (error: any) {
      console.error('사용자 목록 조회 실패:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 사용자 통계 조회
   */
  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/users/admin/users/stats');
      
      if (!response.ok) {
        throw new Error('사용자 통계를 가져오는데 실패했습니다.');
      }

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('사용자 통계 조회 실패:', error);
    }
  };

  /**
   * 사용자 상태 토글
   */
  const toggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      const response = await fetch(`http://localhost:8000/api/users/admin/users/${userId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(!currentStatus),
      });

      if (!response.ok) {
        throw new Error('사용자 상태 변경에 실패했습니다.');
      }

      // 목록 새로고침
      fetchUsers();
      fetchStats();
      alert('사용자 상태가 변경되었습니다.');
    } catch (error: any) {
      console.error('사용자 상태 변경 실패:', error);
      alert('사용자 상태 변경에 실패했습니다: ' + error.message);
    }
  };

  /**
   * 사용자 삭제
   */
  const deleteUser = async (userId: number, userName: string) => {
    if (!confirm(`정말로 '${userName}' 사용자를 삭제하시겠습니까?`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/users/${userId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('사용자 삭제에 실패했습니다.');
      }

      // 목록 새로고침
      fetchUsers();
      fetchStats();
      alert('사용자가 삭제되었습니다.');
    } catch (error: any) {
      console.error('사용자 삭제 실패:', error);
      alert('사용자 삭제에 실패했습니다: ' + error.message);
    }
  };

  /**
   * 선택된 사용자들 대량 삭제
   */
  const bulkDeleteUsers = async () => {
    if (selectedUsers.length === 0) {
      alert('삭제할 사용자를 선택해주세요.');
      return;
    }

    if (!confirm(`선택된 ${selectedUsers.length}명의 사용자를 정말로 삭제하시겠습니까?`)) {
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/users/admin/users/bulk', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(selectedUsers),
      });

      if (!response.ok) {
        throw new Error('대량 삭제에 실패했습니다.');
      }

      const result = await response.json();
      
      // 선택 해제 및 목록 새로고침
      setSelectedUsers([]);
      fetchUsers();
      fetchStats();
      
      alert(result.message);
      if (result.failed_users && result.failed_users.length > 0) {
        console.warn('삭제 실패한 사용자들:', result.failed_users);
      }
    } catch (error: any) {
      console.error('대량 삭제 실패:', error);
      alert('대량 삭제에 실패했습니다: ' + error.message);
    }
  };

  /**
   * 전체 선택/해제
   */
  const toggleAllSelection = () => {
    if (selectedUsers.length === users.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(users.map(user => user.id));
    }
  };

  /**
   * 개별 사용자 선택/해제
   */
  const toggleUserSelection = (userId: number) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  // 데이터 로드
  useEffect(() => {
    fetchUsers();
    fetchStats();
  }, [currentPage, searchTerm, filterStatus, apartmentFilter]);

  // 검색어나 필터 변경 시 첫 페이지로 이동
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, filterStatus, apartmentFilter]);

  if (isLoading && users.length === 0) {
    return (
      <AdminGuard>
        <AdminLayout>
          <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">사용자 데이터를 불러오는 중...</p>
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
              <h1 className="text-2xl font-bold text-gray-900">사용자 관리</h1>
              <p className="text-gray-600">아파트 입주민 정보 관리</p>
            </div>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              새 사용자 추가
            </Button>
          </div>

          {/* 통계 카드들 */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-blue-600">{stats.total_users}</div>
                  <div className="text-sm text-gray-600">총 사용자</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-green-600">{stats.active_users}</div>
                  <div className="text-sm text-gray-600">활성 사용자</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-red-600">{stats.inactive_users}</div>
                  <div className="text-sm text-gray-600">비활성 사용자</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-purple-600">{stats.admin_users}</div>
                  <div className="text-sm text-gray-600">관리자</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-yellow-600">{stats.pending_admins}</div>
                  <div className="text-sm text-gray-600">승인 대기</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-indigo-600">{stats.recent_users}</div>
                  <div className="text-sm text-gray-600">최근 가입</div>
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
                      placeholder="이름, 사용자명, 이메일로 검색..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 w-full border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value as any)}
                    className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">전체</option>
                    <option value="active">활성 사용자</option>
                    <option value="inactive">비활성 사용자</option>
                    <option value="admin">관리자</option>
                  </select>
                  <input
                    type="text"
                    placeholder="동/호수 필터"
                    value={apartmentFilter}
                    onChange={(e) => setApartmentFilter(e.target.value)}
                    className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 선택된 사용자 액션 */}
          {selectedUsers.length > 0 && (
            <Card>
              <CardContent className="p-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">
                    {selectedUsers.length}명의 사용자가 선택됨
                  </span>
                  <Button
                    variant="destructive"
                    onClick={bulkDeleteUsers}
                    size="sm"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    선택된 사용자 삭제
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 사용자 목록 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <Users className="h-5 w-5 mr-2" />
                  사용자 목록
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchUsers()}
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
                  <Button onClick={() => fetchUsers()} className="mt-4">
                    다시 시도
                  </Button>
                </div>
              ) : users.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">사용자가 없습니다.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* 테이블 헤더 */}
                  <div className="flex items-center px-4 py-2 bg-gray-50 rounded-lg font-medium text-sm">
                    <div className="w-8">
                      <input
                        type="checkbox"
                        checked={selectedUsers.length === users.length}
                        onChange={toggleAllSelection}
                        className="rounded"
                      />
                    </div>
                    <div className="flex-1">이름</div>
                    <div className="w-32">사용자명</div>
                    <div className="w-48">이메일</div>
                    <div className="w-32">동/호수</div>
                    <div className="w-24">상태</div>
                    <div className="w-24">가입일</div>
                    <div className="w-32">액션</div>
                  </div>

                  {/* 사용자 목록 */}
                  {users.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center px-4 py-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="w-8">
                        <input
                          type="checkbox"
                          checked={selectedUsers.includes(user.id)}
                          onChange={() => toggleUserSelection(user.id)}
                          className="rounded"
                        />
                      </div>
                      <div className="flex-1">
                        <div className="font-medium">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.phone}</div>
                      </div>
                      <div className="w-32 text-sm">{user.username}</div>
                      <div className="w-48 text-sm">{user.email}</div>
                      <div className="w-32 text-sm">{user.apartment_number || '-'}</div>
                      <div className="w-24">
                        <UserStatusBadge user={user} />
                      </div>
                      <div className="w-24 text-xs text-gray-500">
                        {new Date(user.created_at).toLocaleDateString('ko-KR')}
                      </div>
                      <div className="w-32 flex space-x-1">
                        <UserDetailDialog user={user} />
                        <UserEditDialog user={user} onUserUpdated={fetchUsers} />
                        {!user.is_super_admin && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => toggleUserStatus(user.id, user.is_active)}
                            >
                              {user.is_active ? (
                                <UserX className="h-4 w-4" />
                              ) : (
                                <UserCheck className="h-4 w-4" />
                              )}
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => deleteUser(user.id, user.name)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 페이지네이션 */}
              {users.length > 0 && (
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
                    disabled={users.length < itemsPerPage}
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