/**
 * 관리자 내정보 페이지
 * 관리자 계정 정보 조회 및 관리 기능 제공
 */
"use client";

import React, { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { AdminGuard } from '../../../../lib/auth/admin-guard';
import { AdminLayout } from '@/components/admin/admin-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Calendar,
  Shield,
  Edit,
  Save,
  X
} from 'lucide-react';

/**
 * 관리자 정보 수정 폼 컴포넌트
 */
interface AdminProfileEditProps {
  profile: any;
  onSave: (data: any) => void;
  onCancel: () => void;
}

function AdminProfileEdit({ profile, onSave, onCancel }: AdminProfileEditProps) {
  const [formData, setFormData] = useState({
    name: profile.name || '',
    email: profile.email || '',
    phone: profile.phone || '',
    apartment_number: profile.apartment_number || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Edit className="h-5 w-5" />
          내정보 수정
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="name">이름</label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="이름을 입력하세요"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="email">이메일</label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="이메일을 입력하세요"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="phone">전화번호</label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="전화번호를 입력하세요"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="apartment">관리 단지</label>
              <Input
                id="apartment"
                value={formData.apartment_number}
                onChange={(e) => setFormData({ ...formData, apartment_number: e.target.value })}
                placeholder="관리 단지를 입력하세요"
              />
            </div>
          </div>
          
          <div className="flex gap-2 justify-end">
            <Button type="button" variant="outline" onClick={onCancel}>
              <X className="h-4 w-4 mr-2" />
              취소
            </Button>
            <Button type="submit">
              <Save className="h-4 w-4 mr-2" />
              저장
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

/**
 * 관리자 내정보 페이지
 */
export default function AdminProfile() {
  const { data: session } = useSession();
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState({
    name: '김관리',
    email: 'admin@fnm.com',
    phone: '010-1234-5678',
    apartment_number: 'FNM 아파트 전체',
    role: '시스템 관리자',
    created_at: '2024-01-01',
    last_login: '2024-12-20T10:30:00',
    permissions: ['사용자 관리', '예약 관리', '공지사항 관리', '통계 조회']
  });

  // 프로필 정보 저장
  const handleSaveProfile = async (data: any) => {
    try {
      // TODO: 실제 API 호출로 교체
      setProfile({ ...profile, ...data });
      setIsEditing(false);
      alert('프로필이 성공적으로 업데이트되었습니다.');
    } catch (error) {
      console.error('프로필 업데이트 실패:', error);
      alert('프로필 업데이트에 실패했습니다.');
    }
  };

  // 날짜 포맷팅
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <AdminGuard>
      <AdminLayout>
        <div className="space-y-6">
          {/* 페이지 헤더 */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">내 정보</h1>
            <p className="text-gray-600">관리자 계정 정보를 확인하고 수정할 수 있습니다.</p>
          </div>

          {isEditing ? (
            <AdminProfileEdit
              profile={profile}
              onSave={handleSaveProfile}
              onCancel={() => setIsEditing(false)}
            />
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 프로필 카드 */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <User className="h-5 w-5" />
                      기본 정보
                    </CardTitle>
                    <Button variant="outline" onClick={() => setIsEditing(true)}>
                      <Edit className="h-4 w-4 mr-2" />
                      수정
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-start space-x-4">
                    <Avatar className="h-20 w-20">
                      <AvatarImage src="" />
                      <AvatarFallback className="bg-blue-100 text-blue-600 text-xl font-bold">
                        {profile.name.slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 space-y-3">
                      <div>
                        <h3 className="text-xl font-semibold text-gray-900">{profile.name}</h3>
                        <Badge variant="outline" className="mt-1">
                          <Shield className="h-3 w-3 mr-1" />
                          {profile.role}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div className="flex items-center space-x-2">
                          <Mail className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-600">이메일:</span>
                          <span className="font-medium">{profile.email}</span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Phone className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-600">전화번호:</span>
                          <span className="font-medium">{profile.phone}</span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <MapPin className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-600">관리 단지:</span>
                          <span className="font-medium">{profile.apartment_number}</span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Calendar className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-600">가입일:</span>
                          <span className="font-medium">{formatDate(profile.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 접속 정보 카드 */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">접속 정보</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">최근 로그인</label>
                    <p className="text-sm font-medium mt-1">{formatDate(profile.last_login)}</p>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <label className="text-sm font-medium text-gray-600">접속 상태</label>
                    <div className="flex items-center space-x-2 mt-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-sm font-medium text-green-600">온라인</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 권한 정보 카드 */}
              <Card className="lg:col-span-3">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    관리자 권한
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {profile.permissions.map((permission, index) => (
                      <Badge key={index} variant="secondary" className="justify-center py-2">
                        {permission}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </AdminLayout>
    </AdminGuard>
  );
} 