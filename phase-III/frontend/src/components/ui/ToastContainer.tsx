'use client'

/**
 * ToastContainer component for managing multiple toasts.
 *
 * This component provides:
 * - Manages array of toasts with unique IDs
 * - Renders toasts stacked vertically with smooth animations
 * - Removes toasts after dismissal with AnimatePresence
 * - Provides methods to show success/error/warning/info toasts
 * - Responsive positioning (top-right on desktop, bottom-right on mobile)
 * - Limits maximum number of visible toasts
 */
import { useState, useCallback, createContext, useContext } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import Toast, { ToastType } from './Toast'
import { colors } from '@/styles/tokens'

interface ToastMessage {
  id: string
  message: string
  type: ToastType
}

interface ToastContextType {
  showSuccess: (message: string, duration?: number) => void
  showError: (message: string, duration?: number) => void
  showWarning: (message: string, duration?: number) => void
  showInfo: (message: string, duration?: number) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

interface ToastContainerProps {
  children: React.ReactNode
  position?: 'top-right' | 'bottom-right' | 'top-left' | 'bottom-left'
  maxToasts?: number
}

const positionClasses = {
  'top-right': 'top-4 right-4 flex-col',
  'bottom-right': 'bottom-4 right-4 flex-col-reverse',
  'top-left': 'top-4 left-4 flex-col',
  'bottom-left': 'bottom-4 left-4 flex-col-reverse',
}

export function ToastProvider({
  children,
  position = 'top-right',
  maxToasts = 5,
}: ToastContainerProps) {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const addToast = useCallback((message: string, type: ToastType, duration?: number) => {
    const id = Math.random().toString(36).substring(7)

    setToasts((prev) => {
      const newToasts = [...prev, { id, message, type }]

      // Limit maximum number of toasts
      if (newToasts.length > maxToasts) {
        newToasts.shift() // Remove oldest toast
      }

      return newToasts
    })
  }, [maxToasts])

  const showSuccess = useCallback((message: string, duration?: number) => {
    addToast(message, 'success', duration)
  }, [addToast])

  const showError = useCallback((message: string, duration?: number) => {
    addToast(message, 'error', duration)
  }, [addToast])

  const showWarning = useCallback((message: string, duration?: number) => {
    addToast(message, 'warning', duration)
  }, [addToast])

  const showInfo = useCallback((message: string, duration?: number) => {
    addToast(message, 'info', duration)
  }, [addToast])

  const contextValue: ToastContextType = {
    showSuccess,
    showError,
    showWarning,
    showInfo,
  }

  const containerClasses = positionClasses[position]

  return (
    <ToastContext.Provider value={contextValue}>
      {children}

      {/* Toast container with responsive positioning */}
      <div
        className={`fixed z-50 flex gap-2 p-4 pointer-events-none ${containerClasses}
          sm:pointer-events-auto`}
        style={{ maxWidth: '400px' }}
      >
        <AnimatePresence mode="popLayout">
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              layout
              className="pointer-events-auto w-full"
              initial={{ opacity: 0, scale: 0.9, x: 100 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.9, x: 100 }}
              transition={{
                type: 'spring',
                stiffness: 300,
                damping: 30,
                opacity: { duration: 0.2 },
              }}
            >
              <Toast
                message={toast.message}
                type={toast.type}
                onClose={() => removeToast(toast.id)}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}
