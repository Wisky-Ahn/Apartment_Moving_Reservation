/**
 * NextAuth 세션 Provider
 * 클라이언트 사이드에서 세션 관리
 */
'use client'

import { SessionProvider } from "next-auth/react"

export function Providers({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>
} 