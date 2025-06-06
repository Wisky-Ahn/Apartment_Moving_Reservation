/**
 * NextAuth API 라우트
 * [...nextauth] 동적 라우트
 */
import NextAuth from "next-auth"
import { authOptions } from "../../../../../lib/auth"

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST } 