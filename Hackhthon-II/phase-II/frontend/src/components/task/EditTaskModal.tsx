'use client'

/**
 * EditTaskModal component for editing existing tasks.
 *
 * This component provides:
 * - Modal with pre-filled form for editing task data
 * - Title and description input fields with validation
 * - Form submission to update task API endpoint
 * - Error handling and display
 * - Callback when task is successfully updated
 * - Smooth animations for open/close
 * - Keyboard (ESC) and backdrop click to close
 * - Modern gradient design
 */
import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { taskApi } from '@/lib/api'
import type { Task, TaskUpdateRequest } from '@/types/task'
import { colors, borderRadius, shadows } from '@/styles/tokens'
import { modalOverlay, modalContent, buttonHover, buttonTap } from '@/lib/animations'

interface EditTaskModalProps {
  task: Task
  isOpen: boolean
  onClose: () => void
  onUpdate: (task: Task) => void
  showSuccessToast?: (message: string) => void
  showErrorToast?: (message: string) => void
}

interface FormErrors {
  title?: string
  description?: string
  general?: string
}

interface FormData {
  title: string
  description: string
}

export default function EditTaskModal({
  task,
  isOpen,
  onClose,
  onUpdate,
  showSuccessToast,
  showErrorToast,
}: EditTaskModalProps) {
  const [formData, setFormData] = useState<FormData>({
    title: task.title,
    description: task.description || '',
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)
  const [isFocused, setIsFocused] = useState<'title' | 'description' | null>(null)

  /**
   * Reset form when task changes or modal opens.
   */
  useEffect(() => {
    if (isOpen) {
      setFormData({
        title: task.title,
        description: task.description || '',
      })
      setErrors({})
      setIsFocused(null)
    }
  }, [task, isOpen])

  /**
   * Handle ESC key press to close modal.
   */
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && isOpen && !isLoading) {
      onClose()
    }
  }, [isOpen, isLoading, onClose])

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    } else {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, handleKeyDown])

  /**
   * Validate form fields.
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Title validation (required, 1-200 characters)
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required'
    } else if (formData.title.length < 1) {
      newErrors.title = 'Title must be at least 1 character'
    } else if (formData.title.length > 200) {
      newErrors.title = 'Title must be less than 200 characters'
    }

    // Description validation (optional, 0-1000 characters)
    if (formData.description.length > 1000) {
      newErrors.description = 'Description must be less than 1000 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Clear previous errors
    setErrors({})

    // Validate form
    if (!validateForm()) {
      return
    }

    setIsLoading(true)

    try {
      // Prepare task update request
      const taskData: TaskUpdateRequest = {
        title: formData.title,
        description: formData.description || undefined,
      }

      // Call update task API
      const updatedTask = await taskApi.updateTask(task.id, taskData)

      // Call callback with updated task
      onUpdate(updatedTask)

      // Show success toast if callback provided
      if (showSuccessToast) {
        showSuccessToast('Task updated successfully')
      }

      // Close modal on success
      onClose()
    } catch (error) {
      // Show error toast if callback provided
      if (showErrorToast) {
        showErrorToast('Failed to update task. Please try again.')
      }
      // Don't close modal on error - let user fix it
      if (error instanceof Error) {
        setErrors({
          general: error.message || 'Failed to update task. Please try again.',
        })
      } else {
        setErrors({
          general: 'An unexpected error occurred. Please try again.',
        })
      }
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Handle input field changes.
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))

    // Clear field-specific error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }

    // Clear general error when user makes changes
    if (errors.general) {
      setErrors((prev) => ({ ...prev, general: undefined }))
    }
  }

  /**
   * Handle backdrop click.
   */
  const handleBackdropClick = () => {
    if (!isLoading) {
      onClose()
    }
  }

  // Calculate character counts
  const titleCount = formData.title.length
  const titleProgress = (titleCount / 200) * 100
  const descriptionCount = formData.description.length
  const descriptionProgress = (descriptionCount / 1000) * 100

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={modalOverlay}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={handleBackdropClick}
            className="fixed inset-0 z-50"
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
            }}
          >
            {/* Blur overlay */}
            <div className="absolute inset-0 backdrop-blur-sm" />
          </motion.div>

          {/* Modal panel */}
          <div
            className="fixed inset-0 z-50 overflow-y-auto"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
          >
            <div className="flex min-h-full items-center justify-center p-4 sm:p-6">
              <motion.div
                variants={modalContent}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="relative w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Modal header with gradient */}
                <div
                  className="px-6 py-5 sm:px-8 sm:py-6 border-b-2"
                  style={{
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                    borderColor: colors.primary[200],
                  }}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-xl"
                      style={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }}
                    >
                      <svg
                        className="w-6 h-6 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3
                        className="text-xl sm:text-2xl font-bold text-white"
                        id="modal-title"
                      >
                        Edit Task
                      </h3>
                      <p className="text-sm text-white/90 mt-1">
                        Make changes to your task below
                      </p>
                    </div>
                  </div>
                </div>

                {/* Modal body */}
                <div className="px-6 py-6 sm:px-8 sm:py-7">
                  <form onSubmit={handleSubmit} className="space-y-5">
                    {/* General error message */}
                    <AnimatePresence>
                      {errors.general && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="rounded-xl p-4 flex items-start gap-3"
                          style={{
                            backgroundColor: colors.error[50],
                            border: `1px solid ${colors.error[200]}`,
                          }}
                        >
                          <div className="flex-shrink-0">
                            <svg
                              className="w-5 h-5"
                              style={{ color: colors.error[500] }}
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </div>
                          <p
                            className="text-sm font-medium flex-1"
                            style={{ color: colors.error[800] }}
                          >
                            {errors.general}
                          </p>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Title field */}
                    <motion.div
                      className="space-y-2"
                      animate={{
                        scale: isFocused === 'title' ? 1.01 : 1,
                      }}
                      transition={{ duration: 0.2 }}
                    >
                      <label
                        htmlFor="edit-title"
                        className="block text-sm font-semibold"
                        style={{ color: colors.neutral[700] }}
                      >
                        Title <span style={{ color: colors.error[500] }}>*</span>
                      </label>
                      <div className="relative">
                        <input
                          id="edit-title"
                          name="title"
                          type="text"
                          required
                          maxLength={200}
                          className="w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2"
                          style={{
                            borderColor: errors.title
                              ? colors.error[400]
                              : isFocused === 'title'
                              ? colors.primary[400]
                              : colors.neutral[300],
                            backgroundColor: colors.white,
                            color: colors.neutral[900],
                            fontSize: '0.9375rem',
                          }}
                          placeholder="Enter task title"
                          value={formData.title}
                          onChange={handleChange}
                          onFocus={() => setIsFocused('title')}
                          onBlur={() => setIsFocused(null)}
                          disabled={isLoading}
                          autoFocus
                        />
                        {isFocused === 'title' && (
                          <motion.div
                            className="absolute inset-0 -z-10 rounded-xl"
                            style={{
                              backgroundColor: colors.primary[50],
                            }}
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            transition={{ duration: 0.2 }}
                          />
                        )}
                      </div>
                      <div className="flex items-center justify-between">
                        {errors.title ? (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-sm"
                            style={{ color: colors.error[600] }}
                          >
                            {errors.title}
                          </motion.p>
                        ) : (
                          <div />
                        )}
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: colors.neutral[200] }}>
                            <motion.div
                              className="h-full rounded-full"
                              style={{
                                backgroundColor: titleProgress > 90 ? colors.error[500] : colors.primary[500],
                              }}
                              initial={{ width: 0 }}
                              animate={{ width: `${titleProgress}%` }}
                              transition={{ duration: 0.3 }}
                            />
                          </div>
                          <span
                            className="text-xs font-medium"
                            style={{
                              color: titleProgress > 90 ? colors.error[600] : colors.neutral[500],
                            }}
                          >
                            {titleCount}/200
                          </span>
                        </div>
                      </div>
                    </motion.div>

                    {/* Description field */}
                    <motion.div
                      className="space-y-2"
                      animate={{
                        scale: isFocused === 'description' ? 1.01 : 1,
                      }}
                      transition={{ duration: 0.2 }}
                    >
                      <label
                        htmlFor="edit-description"
                        className="block text-sm font-semibold"
                        style={{ color: colors.neutral[700] }}
                      >
                        Description <span style={{ color: colors.neutral[400] }}>(optional)</span>
                      </label>
                      <div className="relative">
                        <textarea
                          id="edit-description"
                          name="description"
                          rows={4}
                          maxLength={1000}
                          className="w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2 resize-none"
                          style={{
                            borderColor: errors.description
                              ? colors.error[400]
                              : isFocused === 'description'
                              ? colors.primary[400]
                              : colors.neutral[300],
                            backgroundColor: colors.white,
                            color: colors.neutral[900],
                            fontSize: '0.9375rem',
                          }}
                          placeholder="Enter task description (optional)"
                          value={formData.description}
                          onChange={handleChange}
                          onFocus={() => setIsFocused('description')}
                          onBlur={() => setIsFocused(null)}
                          disabled={isLoading}
                        />
                        {isFocused === 'description' && (
                          <motion.div
                            className="absolute inset-0 -z-10 rounded-xl"
                            style={{
                              backgroundColor: colors.primary[50],
                            }}
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            transition={{ duration: 0.2 }}
                          />
                        )}
                      </div>
                      <div className="flex items-center justify-between">
                        {errors.description ? (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-sm"
                            style={{ color: colors.error[600] }}
                          >
                            {errors.description}
                          </motion.p>
                        ) : (
                          <div />
                        )}
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: colors.neutral[200] }}>
                            <motion.div
                              className="h-full rounded-full"
                              style={{
                                backgroundColor: descriptionProgress > 90 ? colors.error[500] : colors.primary[500],
                              }}
                              initial={{ width: 0 }}
                              animate={{ width: `${descriptionProgress}%` }}
                              transition={{ duration: 0.3 }}
                            />
                          </div>
                          <span
                            className="text-xs font-medium"
                            style={{
                              color: descriptionProgress > 90 ? colors.error[600] : colors.neutral[500],
                            }}
                          >
                            {descriptionCount}/1000
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  </form>
                </div>

                {/* Modal footer */}
                <div
                  className="px-6 py-4 sm:px-8 sm:py-5 flex flex-col-reverse sm:flex-row gap-3 justify-end"
                  style={{
                    backgroundColor: colors.neutral[50],
                    borderTop: `1px solid ${colors.neutral[200]}`,
                  }}
                >
                  {/* Cancel button */}
                  <motion.button
                    type="button"
                    onClick={onClose}
                    disabled={isLoading}
                    className="px-6 py-3 rounded-xl border-2 font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed min-h-[48px] sm:min-h-0 flex items-center justify-center gap-2"
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
                    Cancel
                  </motion.button>

                  {/* Save button with gradient */}
                  <motion.button
                    type="button"
                    onClick={handleSubmit}
                    disabled={isLoading}
                    className="px-6 py-3 rounded-xl text-white font-semibold shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed min-h-[48px] sm:min-h-0 flex items-center justify-center gap-2"
                    style={{
                      background: isLoading
                        ? colors.neutral[400]
                        : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      boxShadow: isLoading ? 'none' : shadows['primary-md'],
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
                        Saving...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                        Save Changes
                      </>
                    )}
                  </motion.button>
                </div>
              </motion.div>
            </div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
