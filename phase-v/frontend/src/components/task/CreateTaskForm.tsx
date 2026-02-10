'use client'

/**
 * CreateTaskForm component for creating new tasks.
 *
 * This component provides:
 * - Title and description input fields with validation
 * - Form submission to create task API endpoint
 * - Error handling and display
 * - Callback when task is successfully created
 * - Clear form after successful creation
 * - Modern gradient buttons and animations
 * - Enhanced form design with smooth transitions
 */
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { taskApi } from '@/lib/api'
import { useToast } from '@/components/ui/ToastContainer'
import type { Task, TaskCreateRequest } from '@/types/task'
import { colors, borderRadius, shadows, spacing } from '@/styles/tokens'
import { fadeIn, buttonHover, buttonTap } from '@/lib/animations'

interface CreateTaskFormProps {
  onTaskCreated: (task: Task) => void
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

export default function CreateTaskForm({
  onTaskCreated,
  showSuccessToast,
  showErrorToast,
}: CreateTaskFormProps) {
  const [formData, setFormData] = useState<FormData>({
    title: '',
    description: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)
  const [isFocused, setIsFocused] = useState<'title' | 'description' | null>(null)

  /**
   * Validate form fields.
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Title validation (required, 1-200 characters)
    if (!formData.title) {
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
      // Prepare task creation request
      const taskData: TaskCreateRequest = {
        title: formData.title,
        description: formData.description || undefined,
      }

      // Call create task API
      const createdTask = await taskApi.createTask(taskData)

      // Call callback with created task
      onTaskCreated(createdTask)

      // Show success toast if callback provided
      if (showSuccessToast) {
        showSuccessToast('Task created successfully')
      }

      // Clear form
      setFormData({
        title: '',
        description: '',
      })
    } catch (error) {
      // Show error toast if callback provided
      if (showErrorToast) {
        showErrorToast('Failed to create task. Please try again.')
      }
      if (error instanceof Error) {
        setErrors({
          general: error.message || 'Failed to create task. Please try again.',
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
  }

  // Calculate character counts for progress indicators
  const titleCount = formData.title.length
  const titleProgress = (titleCount / 200) * 100
  const descriptionCount = formData.description.length
  const descriptionProgress = (descriptionCount / 1000) * 100

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeIn}
      className="bg-white rounded-2xl shadow-lg overflow-hidden"
      style={{
        border: `2px solid ${colors.neutral[200]}`,
      }}
    >
      {/* Header with gradient accent */}
      <div
        className="px-6 py-4 sm:px-8 sm:py-5"
        style={{
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        }}
      >
        <h2
          className="text-xl sm:text-2xl font-bold text-white"
        >
          Create New Task
        </h2>
        <p className="text-sm text-white/80 mt-1">
          Add a new task to your todo list
        </p>
      </div>

      <div className="p-6 sm:p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
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
              htmlFor="title"
              className="block text-sm font-semibold"
              style={{ color: colors.neutral[700] }}
            >
              Title <span style={{ color: colors.error[500] }}>*</span>
            </label>
            <div className="relative">
              <input
                id="title"
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
                  fontFamily: 'Inter, system-ui, sans-serif',
                }}
                placeholder="Enter task title"
                value={formData.title}
                onChange={handleChange}
                onFocus={() => setIsFocused('title')}
                onBlur={() => setIsFocused(null)}
                disabled={isLoading}
              />
              {/* Focus ring effect */}
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
              htmlFor="description"
              className="block text-sm font-semibold"
              style={{ color: colors.neutral[700] }}
            >
              Description <span style={{ color: colors.neutral[400] }}>(optional)</span>
            </label>
            <div className="relative">
              <textarea
                id="description"
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
                  fontFamily: 'Inter, system-ui, sans-serif',
                }}
                placeholder="Enter task description (optional)"
                value={formData.description}
                onChange={handleChange}
                onFocus={() => setIsFocused('description')}
                onBlur={() => setIsFocused(null)}
                disabled={isLoading}
              />
              {/* Focus ring effect */}
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

          {/* Submit button with gradient */}
          <motion.button
            type="submit"
            disabled={isLoading}
            className="w-full py-4 px-6 rounded-xl text-white font-semibold shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed min-h-[56px] flex items-center justify-center gap-2"
            style={{
              background: isLoading
                ? colors.neutral[400]
                : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              boxShadow: isLoading ? 'none' : shadows['primary-md'],
              fontSize: '1rem',
            }}
            whileHover={!isLoading ? buttonHover : undefined}
            whileTap={!isLoading ? buttonTap : undefined}
          >
            {isLoading ? (
              <>
                <motion.svg
                  className="w-5 h-5"
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
                Creating task...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Create Task
              </>
            )}
          </motion.button>
        </form>
      </div>
    </motion.div>
  )
}
