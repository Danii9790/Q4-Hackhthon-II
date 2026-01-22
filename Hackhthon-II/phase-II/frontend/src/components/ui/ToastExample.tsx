'use client'

/**
 * Toast example component demonstrating all toast types
 *
 * This component showcases the enhanced toast notification system with:
 * - Success, error, warning, and info variants
 * - Hover to pause functionality
 * - Progress bar animations
 * - Smooth enter/exit animations
 */

import { useToast } from './ToastContainer'
import { motion } from 'framer-motion'
import { colors, borderRadius, spacing } from '@/styles/tokens'

export default function ToastExample() {
  const { showSuccess, showError, showWarning, showInfo } = useToast()

  return (
    <div className="flex flex-wrap gap-3">
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => showSuccess('Task created successfully!')}
        className="px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors hover:bg-success-600"
        style={{
          backgroundColor: colors.success[500],
        }}
      >
        Success Toast
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => showError('Failed to create task. Please try again.')}
        className="px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors"
        style={{
          backgroundColor: colors.error[500],
        }}
      >
        Error Toast
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => showWarning('Your session will expire in 5 minutes.')}
        className="px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors"
        style={{
          backgroundColor: colors.warning[500],
        }}
      >
        Warning Toast
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => showInfo('New features available! Check out the updates.')}
        className="px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors"
        style={{
          backgroundColor: colors.primary[500],
        }}
      >
        Info Toast
      </motion.button>
    </div>
  )
}
