import "next-auth"
import "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    user: {
      id: string
      email: string
      name?: string | null
      username?: string | null
      isAdmin?: boolean
    }
  }

  interface User {
    id: string
    email: string
    name?: string | null
    username?: string | null
    isAdmin?: boolean
    accessToken?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string
    username?: string | null
    isAdmin?: boolean
    accessToken?: string
  }
} 