'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

/**
 * 관리자 페이지 리다이렉트 컴포넌트
 * /admin 접속 시 자동으로 /admin/dashboard로 리다이렉트
 */
export default function AdminRedirectPage() {
  const router = useRouter()

  useEffect(() => {
    // 관리자 대시보드로 자동 리다이렉트
    router.replace('/admin/dashboard')
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">관리자 대시보드로 이동 중...</p>
      </div>
    </div>
  )
} 