'use client'

/**
 * Toast component for displaying notifications.
 *
 * This component provides:
 * - Success, error, warning, and info message display
 * - Auto-dismiss with configurable duration
 * - Manual dismiss capability
 * - Smooth Framer Motion animations
 * - Progress bar showing time remaining
 * - Hover to pause timeout
 * - Accessible with ARIA attributes
 * - Modern design with tokens and shadows
 */
import { useEffect, useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { slideInRight } from '@/lib/animations'
import { colors, shadows, borderRadius } from '@/styles/tokens'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastProps {
  message: string
  type: ToastType
  onClose: () => void
  duration?: number
}

// Type-specific configuration
const typeConfig = {
  success: {
    bgColor: colors.success[50],
    borderColor: colors.success[500],
    iconColor: colors.success[600],
    iconBgColor: colors.success[100],
    textColor: colors.success[900],
    progressColor: colors.success[500],
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  error: {
    bgColor: colors.error[50],
    borderColor: colors.error[500],
    iconColor: colors.error[600],
    iconBgColor: colors.error[100],
    textColor: colors.error[900],
    progressColor: colors.error[500],
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  warning: {
    bgColor: colors.warning[50],
    borderColor: colors.warning[500],
    iconColor: colors.warning[600],
    iconBgColor: colors.warning[100],
    textColor: colors.warning[900],
    progressColor: colors.warning[500],
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  },
  info: {
    bgColor: colors.primary[50],
    borderColor: colors.primary[500],
    iconColor: colors.primary[600],
    iconBgColor: colors.primary[100],
    textColor: colors.primary[900],
    progressColor: colors.primary[500],
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
}

export default function Toast({
  message,
  type,
  onClose,
  duration = 3000,
}: ToastProps) {
  const [progress, setProgress] = useState(100)
  const [isPaused, setIsPaused] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const startTimeRef = useRef<number>(Date.now())
  const remainingTimeRef = useRef<number>(duration)

  useEffect(() => {
    if (!isPaused) {
      intervalRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current
        const remaining = Math.max(0, remainingTimeRef.current - elapsed)
        const progressPercent = (remaining / duration) * 100

        setProgress(progressPercent)

        if (remaining <= 0) {
          handleClose()
        }
      }, 16) // ~60fps

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
      }
    }
  }, [isPaused, duration])

  const handleMouseEnter = () => {
    setIsPaused(true)
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
    // Store remaining time
    remainingTimeRef.current = Math.max(0, remainingTimeRef.current - (Date.now() - startTimeRef.current))
  }

  const handleMouseLeave = () => {
    setIsPaused(false)
    startTimeRef.current = Date.now()
  }

  const handleClose = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
    onClose()
  }

  const config = typeConfig[type]

  return (
    <motion.div
      variants={slideInRight}
      initial="hidden"
      animate="visible"
      exit="exit"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="relative w-full max-w-md overflow-hidden"
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      {/* Main toast card */}
      <div
        className="relative backdrop-blur-sm rounded-lg shadow-lg border-l-4 p-4"
        style={{
          backgroundColor: config.bgColor,
          borderColor: config.borderColor,
          boxShadow: shadows.lg,
          borderRadius: borderRadius.lg,
        }}
      >
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div
            className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
            style={{
              backgroundColor: config.iconBgColor,
              color: config.iconColor,
            }}
          >
            {config.icon}
          </div>

          {/* Message */}
          <div className="flex-1 min-w-0">
            <p
              className="text-sm font-medium leading-tight"
              style={{ color: config.textColor }}
            >
              {message}
            </p>
          </div>

          {/* Close Button */}
          <button
            onClick={handleClose}
            className="flex-shrink-0 inline-flex rounded-md p-1 transition-all duration-200 hover:bg-black/5 focus:outline-none focus:ring-2 focus:ring-offset-1"
            style={{ color: colors.neutral[400] }}
            aria-label="Close notification"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Progress bar */}
        <div
          className="absolute bottom-0 left-0 h-1 transition-all duration-100 ease-linear"
          style={{
            width: `${progress}%`,
            backgroundColor: config.progressColor,
            transition: isPaused ? 'none' : 'width 100ms linear',
          }}
        />
      </div>
    </motion.div>
  )
}
