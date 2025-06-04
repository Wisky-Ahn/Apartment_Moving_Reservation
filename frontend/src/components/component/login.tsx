/**
 * 로그인 컴포넌트 - FastAPI 백엔드와 연결
 * 사용자 인증 및 토큰 관리 기능 포함
 */
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AuthService } from '@/lib/services/auth';
import type { LoginRequest } from '@/lib/services/auth';

interface LoginProps {
  onCloseButtonClick?: () => void;
  onUserButtonClick?: () => void;
}

export function Login({ onCloseButtonClick, onUserButtonClick }: LoginProps) {
  const router = useRouter();
  const [formData, setFormData] = useState<LoginRequest>({
    username: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 입력 필드 변경 처리
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev: LoginRequest) => ({
      ...prev,
      [name]: value,
    }));
    // 에러 메시지 초기화
    if (error) setError(null);
  };

  /**
   * 로그인 폼 제출 처리
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 입력 검증
    if (!formData.username.trim() || !formData.password.trim()) {
      setError('아이디와 비밀번호를 모두 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // FastAPI 백엔드 로그인 API 호출
      const response = await AuthService.login(formData);
      
      console.log('로그인 성공:', response);
      
      // 로그인 성공 시 메인 페이지로 이동
      if (onUserButtonClick) {
        onUserButtonClick();
      } else {
        router.push('/'); // 메인 페이지로 리다이렉트
      }
      
    } catch (error: any) {
      console.error('로그인 실패:', error);
      setError(error.message || '로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 엔터 키 처리
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit(e as React.FormEvent);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-md shadow-lg">
        <div className="flex justify-between">
          <h1 className="text-xl font-bold">로그인</h1>
          {onCloseButtonClick && (
            <button 
              className="text-xl hover:text-gray-600" 
              onClick={onCloseButtonClick}
              type="button"
            >
              ×
            </button>
          )}
        </div>
        
        <div className="border-t border-gray-300 pt-4">
          <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
            {/* 에러 메시지 표시 */}
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
                {error}
              </div>
            )}
            
            {/* 아이디 입력 */}
            <div className="flex flex-col space-y-1">
              <label className="text-sm font-medium" htmlFor="username">
                아이디
              </label>
              <Input 
                className="flex-1" 
                id="username"
                name="username"
                placeholder="아이디를 입력하세요"
                value={formData.username}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                required
              />
            </div>
            
            {/* 비밀번호 입력 */}
            <div className="flex flex-col space-y-1">
              <label className="text-sm font-medium" htmlFor="password">
                비밀번호
              </label>
              <Input 
                id="password"
                name="password"
                placeholder="비밀번호를 입력하세요"
                type="password"
                value={formData.password}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                required
              />
            </div>
            
            {/* 안내 메시지 */}
            <p className="text-xs text-gray-600">
              로그인 정보를 잊으셨다면, 관리사무소에 문의하여 새로운 비밀번호를 요청하실 수 있습니다.
            </p>
            
            {/* 로그인 버튼 */}
            <Button 
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? '로그인 중...' : '로그인'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
