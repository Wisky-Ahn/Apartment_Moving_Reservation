"use client"

/**
 * 회원가입 페이지
 * 일반 사용자 및 관리자 회원가입 기능
 */
import { useState } from "react"
import { useRouter } from "next/navigation"
import { useSession } from "next-auth/react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"

// 폼 데이터 타입 정의
interface RegisterFormData {
  username: string
  email: string
  password: string
  confirmPassword: string
  name: string
  phone: string
  apartment_number: string
  isAdmin: boolean
}

// 에러 상태 타입 정의
interface FormErrors {
  username?: string
  email?: string
  password?: string
  confirmPassword?: string
  name?: string
  phone?: string
  apartment_number?: string
  general?: string
}

export default function RegisterPage() {
  const router = useRouter()
  const { data: session } = useSession()
  
  // 폼 상태 관리
  const [formData, setFormData] = useState<RegisterFormData>({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    name: "",
    phone: "",
    apartment_number: "",
    isAdmin: false
  })
  
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState<string | null>(null)

  // 이미 로그인된 사용자는 홈으로 리다이렉트
  if (session) {
    router.push("/")
    return null
  }

  /**
   * 입력 필드 변경 핸들러
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
    // 입력 시 해당 필드 에러 제거
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined
      }))
    }
  }

  /**
   * 관리자 체크박스 변경 핸들러
   */
  const handleAdminCheckChange = (checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      isAdmin: checked
    }))
  }

  /**
   * 폼 유효성 검증 함수
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // 사용자명 검증
    if (!formData.username.trim()) {
      newErrors.username = "사용자명을 입력해주세요."
    } else if (formData.username.length < 3) {
      newErrors.username = "사용자명은 3글자 이상이어야 합니다."
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = "사용자명은 영문, 숫자, 언더스코어만 사용 가능합니다."
    }

    // 이메일 검증
    if (!formData.email.trim()) {
      newErrors.email = "이메일을 입력해주세요."
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "올바른 이메일 형식을 입력해주세요."
    }

    // 이름 검증
    if (!formData.name.trim()) {
      newErrors.name = "이름을 입력해주세요."
    } else if (formData.name.length < 2) {
      newErrors.name = "이름은 2글자 이상이어야 합니다."
    }

    // 비밀번호 검증
    if (!formData.password) {
      newErrors.password = "비밀번호를 입력해주세요."
    } else if (formData.password.length < 6) {
      newErrors.password = "비밀번호는 6글자 이상이어야 합니다."
    }

    // 비밀번호 확인 검증
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "비밀번호 확인을 입력해주세요."
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "비밀번호가 일치하지 않습니다."
    }

    // 아파트 호수 검증 (필수)
    if (!formData.apartment_number.trim()) {
      newErrors.apartment_number = "아파트 호수를 입력해주세요."
    } else if (!/^[0-9]{1,4}동\s?[0-9]{1,4}호$/.test(formData.apartment_number.trim())) {
      newErrors.apartment_number = "올바른 형식으로 입력해주세요. (예: 101동 1001호)"
    }

    // 전화번호 검증 (선택사항이지만 입력 시 형식 확인)
    if (formData.phone.trim() && !/^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$/.test(formData.phone.trim())) {
      newErrors.phone = "올바른 전화번호 형식을 입력해주세요. (예: 010-1234-5678)"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  /**
   * 회원가입 제출 핸들러
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsLoading(true)
    setErrors({})
    setIsSuccess(null)

    try {
      const endpoint = formData.isAdmin ? '/api/users/register-admin' : '/api/users/register'
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          name: formData.name,
          phone: formData.phone.trim() || null,
          apartment_number: formData.apartment_number.trim()
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        if (response.status === 400) {
          setErrors({ general: data.detail || "회원가입에 실패했습니다." })
        } else {
          setErrors({ general: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요." })
        }
        return
      }

      if (formData.isAdmin) {
        setIsSuccess("관리자 계정 신청이 완료되었습니다. 슈퍼관리자의 승인을 기다려주세요.")
      } else {
        setIsSuccess("회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.")
        setTimeout(() => {
          router.push("/login?message=registration_success")
        }, 2000)
      }

    } catch (error) {
      console.error('회원가입 오류:', error)
      setErrors({ 
        general: "네트워크 오류가 발생했습니다. 인터넷 연결을 확인하고 다시 시도해주세요." 
      })
    } finally {
      setIsLoading(false)
    }
  }

  // 성공 화면
  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto h-12 w-12 text-green-600">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              회원가입 완료!
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              회원가입이 성공적으로 완료되었습니다.<br />
              로그인 페이지로 이동합니다...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            FNM 회원가입
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            아파트 이사 예약 시스템에 가입하세요
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {errors.general && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{errors.general}</div>
            </div>
          )}

          <div className="space-y-4">
            {/* 관리자 계정 여부 */}
            <div className="flex items-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <Checkbox 
                id="admin-account"
                checked={formData.isAdmin}
                onCheckedChange={handleAdminCheckChange}
              />
              <label htmlFor="admin-account" className="text-sm font-medium text-blue-900">
                관리자 계정으로 신청 (슈퍼관리자 승인 필요)
              </label>
            </div>

            {/* 사용자명 입력 */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                사용자명 *
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleInputChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.username ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="hong123"
              />
              {errors.username && <p className="mt-1 text-sm text-red-600">{errors.username}</p>}
            </div>

            {/* 이메일 입력 */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                이메일 *
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.email ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="hong@example.com"
              />
              {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
            </div>

            {/* 이름 입력 */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                이름 *
              </label>
              <Input
                id="name"
                name="name"
                type="text"
                required
                value={formData.name}
                onChange={handleInputChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.name ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="홍길동"
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            </div>

            {/* 전화번호 입력 */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                전화번호 (선택사항)
              </label>
              <Input
                id="phone"
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleInputChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.phone ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="010-1234-5678"
              />
              {errors.phone && <p className="mt-1 text-sm text-red-600">{errors.phone}</p>}
            </div>

            {/* 아파트 호수 입력 */}
            <div>
              <label htmlFor="apartment_number" className="block text-sm font-medium text-gray-700">
                아파트 호수 *
              </label>
              <Input
                id="apartment_number"
                name="apartment_number"
                type="text"
                required
                value={formData.apartment_number}
                onChange={handleInputChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.apartment_number ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="101동 1001호"
              />
              {errors.apartment_number && <p className="mt-1 text-sm text-red-600">{errors.apartment_number}</p>}
            </div>

            {/* 비밀번호 입력 */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                비밀번호 *
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.password ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="6글자 이상"
              />
              {errors.password && <p className="mt-1 text-sm text-red-600">{errors.password}</p>}
            </div>

            {/* 비밀번호 확인 입력 */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                비밀번호 확인 *
              </label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={formData.confirmPassword}
                onChange={handleInputChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  errors.confirmPassword ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="비밀번호를 다시 입력하세요"
              />
              {errors.confirmPassword && <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>}
            </div>
          </div>

          <div>
            <Button
              type="submit"
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
                isLoading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
              }`}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  가입 중...
                </>
              ) : (
                '회원가입'
              )}
            </Button>
          </div>

          <div className="text-center">
            <span className="text-sm text-gray-600">
              이미 계정이 있으신가요?{' '}
              <Link href="/login" className="font-medium text-blue-600 hover:text-blue-500">
                로그인하기
              </Link>
            </span>
          </div>
        </form>
      </div>
    </div>
  )
} 