import "next-auth"
import "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    accessToken?: string
    user: {
      id: string
      email: string
      name?: string | null
      username?: string | null
      isAdmin?: boolean
      isSuperAdmin?: boolean
    }
  }

  interface User {
    id: string
    email: string
    name?: string | null
    username?: string | null
    isAdmin?: boolean
    isSuperAdmin?: boolean
    accessToken?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string
    username?: string | null
    isAdmin?: boolean
    isSuperAdmin?: boolean
    accessToken?: string
  }
} 