'use client'

/**
 * ConfirmDeleteDialog component for task deletion confirmation.
 *
 * This component provides:
 * - Modal dialog with backdrop overlay
 * - Warning message with task title
 * - Confirm and cancel buttons
 * - Keyboard accessibility (ESC to close)
 * - Focus management
 * - Smooth animations and modern design
 * - Animated warning icon
 * - Gradient danger button
 */
import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { colors, borderRadius, shadows } from '@/styles/tokens'
import { modalOverlay, modalContent, buttonHover, buttonTap } from '@/lib/animations'

interface ConfirmDeleteDialogProps {
  isOpen: boolean
  taskTitle: string
  onConfirm: () => void
  onCancel: () => void
  isLoading?: boolean
}

export default function ConfirmDeleteDialog({
  isOpen,
  taskTitle,
  onConfirm,
  onCancel,
  isLoading = false,
}: ConfirmDeleteDialogProps) {
  const cancelButtonRef = useRef<HTMLButtonElement>(null)

  // Focus management: focus cancel button when dialog opens
  useEffect(() => {
    if (isOpen && cancelButtonRef.current) {
      cancelButtonRef.current.focus()
    }
  }, [isOpen])

  // Handle ESC key to close dialog
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen && !isLoading) {
        onCancel()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll when dialog is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onCancel, isLoading])

  // Handle backdrop click
  const handleBackdropClick = () => {
    if (!isLoading) {
      onCancel()
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop with blur */}
          <motion.div
            variants={modalOverlay}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={handleBackdropClick}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
            }}
          >
            <div className="absolute inset-0 backdrop-blur-sm" />
          </motion.div>

          {/* Dialog */}
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-dialog-title"
            aria-describedby="delete-dialog-description"
          >
            <motion.div
              variants={modalContent}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="relative w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl mx-4"
            >
              {/* Warning icon with animated pulse */}
              <div className="pt-8 pb-4 px-6 flex flex-col items-center">
                <motion.div
                  className="relative mb-5"
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{
                    type: 'spring',
                    stiffness: 200,
                    damping: 15,
                    delay: 0.1,
                  }}
                >
                  {/* Animated outer ring */}
                  <motion.div
                    className="absolute inset-0 rounded-full opacity-20"
                    style={{
                      backgroundColor: colors.error[500],
                      width: '80px',
                      height: '80px',
                      left: '50%',
                      top: '50%',
                      marginLeft: '-40px',
                      marginTop: '-40px',
                    }}
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [0.2, 0.1, 0.2],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: 'easeInOut',
                    }}
                  />
                  {/* Icon container */}
                  <div
                    className="relative w-20 h-20 rounded-full flex items-center justify-center"
                    style={{
                      backgroundColor: colors.error[100],
                    }}
                  >
                    <svg
                      className="w-10 h-10"
                      style={{ color: colors.error[600] }}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <motion.path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        initial={{ pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{ duration: 0.8, delay: 0.3, ease: 'easeInOut' }}
                      />
                    </svg>
                  </div>
                </motion.div>

                {/* Dialog title */}
                <motion.h2
                  id="delete-dialog-title"
                  className="text-2xl font-bold text-center mb-2"
                  style={{ color: colors.neutral[900] }}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  Delete Task
                </motion.h2>

                {/* Dialog description */}
                <motion.div
                  className="text-center space-y-2 px-2"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <p
                    id="delete-dialog-description"
                    className="text-base"
                    style={{ color: colors.neutral[600] }}
                  >
                    Are you sure you want to delete this task?
                  </p>
                  <p
                    className="text-sm font-medium px-4 py-2 rounded-lg inline-block"
                    style={{
                      color: colors.neutral[700],
                      backgroundColor: colors.neutral[100],
                    }}
                  >
                    <span style={{ color: colors.neutral[900] }}>Task:</span>{' '}
                    <span className="italic">&quot;{taskTitle}&quot;</span>
                  </p>
                  <motion.p
                    className="text-xs font-semibold mt-4 flex items-center justify-center gap-1.5"
                    style={{ color: colors.error[600] }}
                    animate={{ opacity: [1, 0.7, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                    This action cannot be undone
                  </motion.p>
                </motion.div>
              </div>

              {/* Action buttons */}
              <div
                className="px-6 pb-6 pt-2 flex flex-col sm:flex-row gap-3"
                style={{
                  borderTop: `1px solid ${colors.neutral[200]}`,
                }}
              >
                {/* Cancel button */}
                <motion.button
                  ref={cancelButtonRef}
                  type="button"
                  onClick={onCancel}
                  disabled={isLoading}
                  className="flex-1 px-5 py-3 rounded-xl border-2 font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed min-h-[48px] sm:min-h-0 flex items-center justify-center gap-2"
                  style={{
                    borderColor: colors.neutral[300],
                    backgroundColor: colors.white,
                    color: colors.neutral[700],
                    fontSize: '0.9375rem',
                  }}
                  whileHover={!isLoading ? {
                    borderColor: colors.neutral[400],
                    backgroundColor: colors.neutral[50],
                  } : undefined}
                  whileTap={!isLoading ? buttonTap : undefined}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                  Cancel
                </motion.button>

                {/* Delete button with gradient */}
                <motion.button
                  type="button"
                  onClick={onConfirm}
                  disabled={isLoading}
                  className="flex-1 px-5 py-3 rounded-xl text-white font-semibold shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed min-h-[48px] sm:min-h-0 flex items-center justify-center gap-2"
                  style={{
                    background: isLoading
                      ? colors.neutral[400]
                      : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    boxShadow: isLoading ? 'none' : shadows['error-sm'],
                    fontSize: '0.9375rem',
                  }}
                  whileHover={!isLoading ? buttonHover : undefined}
                  whileTap={!isLoading ? buttonTap : undefined}
                >
                  {isLoading ? (
                    <>
                      <motion.svg
                        className="w-4 h-4"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </motion.svg>
                      Deleting...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                      Delete Task
                    </>
                  )}
                </motion.button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
