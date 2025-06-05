/**
 * NextAuth 설정
 * JWT 전략을 사용한 세션 관리
 */
import { NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        username: { label: "사용자명", type: "text" },
        password: { label: "비밀번호", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) {
          console.log('🔍 Missing credentials')
          return null
        }

        try {
          // 백엔드 API로 로그인 요청 (임시 하드코딩)
          const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
          console.log('🔍 NextAuth API URL:', API_URL) // 디버깅용
          
          const response = await fetch(`${API_URL}/api/users/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username: credentials.username,
              password: credentials.password,
            }),
          })

          console.log('🔍 Response status:', response.status) // 디버깅용

          if (!response.ok) {
            const errorData = await response.json()
            console.error('🔍 Login failed:', errorData) // 디버깅용
            return null
          }

          const data = await response.json()
          console.log('🔍 Login success:', data) // 디버깅용
          
          if (data.success && data.data?.access_token && data.data?.user) {
            const user = {
              id: data.data.user.id.toString(),
              email: data.data.user.email,
              name: data.data.user.name,
              username: data.data.user.username,
              isAdmin: data.data.user.is_admin,
              accessToken: data.data.access_token,
            }
            console.log('🔍 Returning user object:', user)
            return user
          }

          console.log('🔍 Invalid response structure')
          return null
        } catch (error) {
          console.error('🔍 로그인 에러:', error)
          return null
        }
      }
    })
  ],
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30일
  },
  callbacks: {
    async jwt({ token, user, account }) {
      console.log('🔍 JWT callback - token:', token, 'user:', user, 'account:', account)
      if (user) {
        token.id = user.id
        token.isAdmin = (user as any).isAdmin
        token.accessToken = (user as any).accessToken
        token.username = (user as any).username
      }
      return token
    },
    async session({ session, token }) {
      console.log('🔍 Session callback - session:', session, 'token:', token)
      if (session.user && token) {
        (session.user as any).id = token.id as string
        (session.user as any).username = token.username as string
        (session.user as any).isAdmin = token.isAdmin as boolean
        (session.user as any).accessToken = token.accessToken as string
      }
      return session
    }
  },
  pages: {
    signIn: '/login',
    signOut: '/auth/signout',
    error: '/auth/error',
  },
  secret: process.env.NEXTAUTH_SECRET || "your-secret-key-change-this-in-production-please",
  debug: true, // 디버깅 활성화
}

export default authOptions 