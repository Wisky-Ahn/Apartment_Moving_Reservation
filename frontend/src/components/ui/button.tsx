"use client"

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-95 hover:shadow-md",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-lg active:bg-primary/95 focus:ring-primary/50",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 hover:shadow-lg active:bg-destructive/95 focus:ring-destructive/50",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground hover:border-accent-foreground/20 active:bg-accent/80 focus:ring-accent/50",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80 hover:shadow-md active:bg-secondary/90 focus:ring-secondary/50",
        ghost: "hover:bg-accent hover:text-accent-foreground hover:shadow-sm active:bg-accent/80 focus:ring-accent/50",
        link: "text-primary underline-offset-4 hover:underline hover:text-primary/80 focus:ring-primary/30",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
  debounceMs?: number
  success?: boolean
}

const Button = React.memo(React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, debounceMs = 0, success = false, onClick, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    const [isDebouncing, setIsDebouncing] = React.useState(false)
    const [showSuccess, setShowSuccess] = React.useState(false)

    // 성공 상태 처리 - 메모이제이션으로 최적화
    React.useEffect(() => {
      if (success) {
        setShowSuccess(true)
        const timer = setTimeout(() => setShowSuccess(false), 2000)
        return () => clearTimeout(timer)
      }
    }, [success])

    // 디바운싱이 필요한 경우 처리 - useCallback으로 최적화
    const handleClick = React.useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
      if (loading || disabled || isDebouncing) {
        e.preventDefault()
        return
      }

      // 클릭 시 ripple 효과를 위한 애니메이션 - 성능 최적화
      const button = e.currentTarget
      const ripple = document.createElement('span')
      const rect = button.getBoundingClientRect()
      const size = Math.max(rect.width, rect.height)
      const x = e.clientX - rect.left - size / 2
      const y = e.clientY - rect.top - size / 2
      
      ripple.className = 'absolute rounded-full bg-white/20 pointer-events-none animate-ping'
      ripple.style.width = ripple.style.height = size + 'px'
      ripple.style.left = x + 'px'
      ripple.style.top = y + 'px'
      
      button.appendChild(ripple)
      
      // 메모리 누수 방지를 위한 정리
      const cleanup = () => {
        if (ripple.parentNode) {
          ripple.parentNode.removeChild(ripple)
        }
      }
      setTimeout(cleanup, 600)

      if (debounceMs > 0) {
        setIsDebouncing(true)
        setTimeout(() => setIsDebouncing(false), debounceMs)
      }

      onClick?.(e)
    }, [loading, disabled, isDebouncing, debounceMs, onClick])

    const isButtonDisabled = loading || disabled || isDebouncing
    const buttonVariant = showSuccess ? "default" : variant

    return (
      <Comp
        className={cn(
          buttonVariants({ variant: buttonVariant, size, className }),
          "relative overflow-hidden",
          showSuccess && "bg-green-600 hover:bg-green-700 text-white",
          isDebouncing && "cursor-wait"
        )}
        ref={ref}
        onClick={handleClick}
        disabled={isButtonDisabled}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {showSuccess && !loading && <span className="mr-2">✓</span>}
        {children}
      </Comp>
    )
  }
))
Button.displayName = "Button"

export { Button, buttonVariants }
