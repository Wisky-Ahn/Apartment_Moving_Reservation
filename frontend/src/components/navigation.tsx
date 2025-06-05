/**
 * 공통 네비게이션 컴포넌트
 * 페이지 간 이동을 위한 네비게이션 바
 */
'use client'

import { useRouter, usePathname } from 'next/navigation'
import { useSession, signOut } from 'next-auth/react'
import { Button } from "@/components/ui/button"
import { useState } from 'react'
import { Menu, X } from 'lucide-react'

export function Navigation() {
  const router = useRouter()
  const pathname = usePathname()
  const { data: session } = useSession()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleLogout = async () => {
    await signOut({ redirect: false })
    router.push('/')
  }

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false)
  }

  const handleNavigation = (path: string) => {
    router.push(path)
    closeMobileMenu()
  }

  // 로그인/회원가입 페이지에서는 네비게이션을 숨김
  if (pathname === '/login' || pathname === '/register') {
    return null
  }

  // 관리자 페이지에서는 네비게이션을 숨김 (AdminLayout의 sidebar와 겹침 방지)
  if (pathname.startsWith('/admin')) {
    return null
  }

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <button 
                onClick={() => handleNavigation('/')}
                className="text-xl font-bold text-blue-600 hover:text-blue-700 transition-colors"
              >
                FNM
              </button>
            </div>
            
            {/* 데스크톱 네비게이션 */}
            <div className="hidden md:ml-6 md:flex md:space-x-8">
              <button
                onClick={() => handleNavigation('/')}
                className={`${
                  pathname === '/' 
                    ? 'border-blue-500 text-gray-900' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-all duration-200`}
              >
                홈
              </button>
              <button
                onClick={() => handleNavigation('/Reservations/reservations')}
                className={`${
                  pathname.includes('/Reservations') 
                    ? 'border-blue-500 text-gray-900' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-all duration-200`}
              >
                예약
              </button>
              <button
                onClick={() => handleNavigation('/Notices/notices')}
                className={`${
                  pathname.includes('/Notices') 
                    ? 'border-blue-500 text-gray-900' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-all duration-200`}
              >
                공지사항
              </button>
              {session && (
                <button
                  onClick={() => handleNavigation('/user')}
                  className={`${
                    pathname === '/user' 
                      ? 'border-blue-500 text-gray-900' 
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-all duration-200`}
                >
                  내 정보
                </button>
              )}
            </div>
          </div>
          
          {/* 데스크톱 우측 메뉴 */}
          <div className="hidden md:flex md:items-center">
            {session ? (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-700">
                  {session.user?.name || session.user?.email}님
                </span>
                <Button variant="outline" size="sm" onClick={handleLogout}>
                  로그아웃
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleNavigation('/register')}
                >
                  회원가입
                </Button>
                <Button 
                  variant="default" 
                  size="sm"
                  onClick={() => handleNavigation('/login')}
                >
                  로그인
                </Button>
              </div>
            )}
          </div>

          {/* 모바일 햄버거 메뉴 버튼 */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 transition-colors"
              aria-expanded="false"
            >
              <span className="sr-only">메뉴 열기</span>
              {isMobileMenuOpen ? (
                <X className="block h-6 w-6" aria-hidden="true" />
              ) : (
                <Menu className="block h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 모바일 메뉴 */}
      {isMobileMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t">
            <button
              onClick={() => handleNavigation('/')}
              className={`${
                pathname === '/' 
                  ? 'bg-blue-50 border-blue-500 text-blue-700' 
                  : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'
              } block w-full text-left pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-all duration-200`}
            >
              홈
            </button>
            <button
              onClick={() => handleNavigation('/Reservations/reservations')}
              className={`${
                pathname.includes('/Reservations') 
                  ? 'bg-blue-50 border-blue-500 text-blue-700' 
                  : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'
              } block w-full text-left pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-all duration-200`}
            >
              예약
            </button>
            <button
              onClick={() => handleNavigation('/Notices/notices')}
              className={`${
                pathname.includes('/Notices') 
                  ? 'bg-blue-50 border-blue-500 text-blue-700' 
                  : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'
              } block w-full text-left pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-all duration-200`}
            >
              공지사항
            </button>
            {session && (
              <button
                onClick={() => handleNavigation('/user')}
                className={`${
                  pathname === '/user' 
                    ? 'bg-blue-50 border-blue-500 text-blue-700' 
                    : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'
                } block w-full text-left pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-all duration-200`}
              >
                내 정보
              </button>
            )}
          </div>
          
          {/* 모바일 사용자 메뉴 */}
          <div className="pt-4 pb-3 border-t border-gray-200">
            {session ? (
              <div className="px-4 space-y-3">
                <div className="text-base font-medium text-gray-800">
                  {session.user?.name || session.user?.email}님
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleLogout}
                  className="w-full"
                >
                  로그아웃
                </Button>
              </div>
            ) : (
              <div className="px-4 space-y-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleNavigation('/register')}
                  className="w-full"
                >
                  회원가입
                </Button>
                <Button 
                  variant="default" 
                  size="sm"
                  onClick={() => handleNavigation('/login')}
                  className="w-full"
                >
                  로그인
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  )
} 