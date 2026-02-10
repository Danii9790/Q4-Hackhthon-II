'use client'

/**
 * Error Boundary for Chat Page.
 *
 * Catches and displays errors that occur during chat page rendering or interaction.
 * Provides user-friendly error messages and recovery options.
 *
 * Features:
 * - Catches JavaScript errors in component tree
 * - Displays user-friendly error message
 * - Provides recovery button to retry or go home
 * - Logs errors for debugging
 */
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { colors, borderRadius } from '@/styles/tokens'
import { fadeIn } from '@/lib/animations'

interface ErrorBoundaryProps {
  error: Error & { digest?: string }
  reset: () => void
}

/**
 * Chat Page Error Boundary Component.
 *
 * This component is automatically rendered by Next.js when an error
 * occurs in the chat page or its children.
 */
export default function ChatErrorBoundary({ error, reset }: ErrorBoundaryProps) {
  const router = useRouter()

  // Log error to console for debugging (T107)
  useEffect(() => {
    console.error('Chat page error:', error)
  }, [error])

  /**
   * Handle going back to home page.
   */
  const handleGoHome = () => {
    router.push('/')
  }

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-white to-orange-50 px-4"
    >
      <div className="max-w-md w-full">
        {/* Error Card */}
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="bg-white rounded-2xl shadow-xl p-8"
          style={{
            boxShadow: `0 20px 60px ${colors.error[200]}`,
          }}
        >
          {/* Error Icon */}
          <div className="flex justify-center mb-6">
            <motion.div
              initial={{ rotate: -10 }}
              animate={{ rotate: 0 }}
              transition={{
                delay: 0.2,
                type: 'spring',
                stiffness: 200,
              }}
              className="w-20 h-20 rounded-full flex items-center justify-center"
              style={{ backgroundColor: colors.error[100] }}
            >
              <svg
                className="w-10 h-10"
                style={{ color: colors.error[600] }}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </motion.div>
          </div>

          {/* Error Message */}
          <div className="text-center mb-8">
            <h1
              className="text-2xl font-bold mb-3"
              style={{ color: colors.error[900] }}
            >
              Oops! Something went wrong
            </h1>
            <p
              className="text-base leading-relaxed mb-2"
              style={{ color: colors.neutral[700] }}
            >
              An error occurred while loading the chat interface.
            </p>
            <p className="text-sm" style={{ color: colors.neutral[500] }}>
              {error.message || 'Please try again or contact support if the problem persists.'}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            {/* Retry Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={reset}
              className="w-full py-3 px-6 rounded-xl font-semibold text-white focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all"
              style={{
                backgroundColor: colors.primary[500],
              }}
            >
              Try Again
            </motion.button>

            {/* Go Home Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleGoHome}
              className="w-full py-3 px-6 rounded-xl font-semibold border-2 focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all"
              style={{
                borderColor: colors.neutral[300],
                color: colors.neutral[700],
                backgroundColor: colors.white,
              }}
            >
              Go to Home Page
            </motion.button>
          </div>

          {/* Error Details (for development) */}
          {process.env.NODE_ENV === 'development' && error.digest && (
            <details className="mt-6">
              <summary
                className="text-xs font-semibold cursor-pointer"
                style={{ color: colors.neutral[500] }}
              >
                Error Details (Development)
              </summary>
              <div
                className="mt-2 p-3 rounded-lg text-xs font-mono break-words"
                style={{
                  backgroundColor: colors.neutral[100],
                  color: colors.neutral[700],
                }}
              >
                <div className="mb-1">
                  <strong>Error Digest:</strong> {error.digest}
                </div>
                <div>
                  <strong>Message:</strong> {error.message}
                </div>
              </div>
            </details>
          )}
        </motion.div>

        {/* Help Text */}
        <p
          className="text-center text-sm mt-6"
          style={{ color: colors.neutral[500] }}
        >
          Need help? Contact support or check the{' '}
          <a
            href="https://github.com/anthropics/claude-code"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
            style={{ color: colors.primary[500] }}
          >
            documentation
          </a>
          .
        </p>
      </div>
    </motion.div>
  )
}
