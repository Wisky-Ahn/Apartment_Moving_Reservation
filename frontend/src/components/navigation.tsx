/**
 * 공통 네비게이션 컴포넌트
 * 페이지 간 이동을 위한 네비게이션 바
 */
'use client'

import { useRouter, usePathname } from 'next/navigation'
import { useSession, signOut } from 'next-auth/react'
import { Button } from "@/components/ui/button"

export function Navigation() {
  const router = useRouter()
  const pathname = usePathname()
  const { data: session } = useSession()

  const handleLogout = async () => {
    await signOut({ redirect: false })
    router.push('/')
  }

  // 로그인/회원가입 페이지에서는 네비게이션을 숨김
  if (pathname === '/login' || pathname === '/register') {
    return null
  }

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <button 
                onClick={() => router.push('/')}
                className="text-xl font-bold text-blue-600 hover:text-blue-700"
              >
                FNM
              </button>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <button
                onClick={() => router.push('/')}
                className={`${
                  pathname === '/' 
                    ? 'border-blue-500 text-gray-900' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
              >
                홈
              </button>
              <button
                onClick={() => router.push('/Reservations/reservations')}
                className={`${
                  pathname.includes('/Reservations') 
                    ? 'border-blue-500 text-gray-900' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
              >
                예약
              </button>
              <button
                onClick={() => router.push('/Notices/notices')}
                className={`${
                  pathname.includes('/Notices') 
                    ? 'border-blue-500 text-gray-900' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
              >
                공지사항
              </button>
              {session && (
                <button
                  onClick={() => router.push('/user')}
                  className={`${
                    pathname === '/user' 
                      ? 'border-blue-500 text-gray-900' 
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                >
                  내 정보
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center">
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
                  onClick={() => router.push('/register')}
                >
                  회원가입
                </Button>
              <Button 
                variant="default" 
                size="sm"
                onClick={() => router.push('/login')}
              >
                로그인
              </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
} 