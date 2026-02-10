'use client'

/**
 * RecurringTaskForm component for creating recurring task templates.
 *
 * T073: This component provides:
 * - Title and description input fields with validation
 * - Frequency selector (DAILY, WEEKLY, MONTHLY)
 * - Start date picker
 * - Optional end date picker
 * - Form submission to create recurring task API endpoint
 * - Error handling and display
 * - Callback when recurring task is successfully created
 * - Clear form after successful creation
 * - Modern gradient buttons and animations
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useToast } from '@/components/ui/ToastContainer'
import { colors } from '@/styles/tokens'
import { fadeIn, buttonHover, buttonTap } from '@/lib/animations'

interface RecurringTaskFormProps {
  onRecurringTaskCreated: (recurringTask: any) => void
  onCancel: () => void
  showSuccessToast?: (message: string) => void
  showErrorToast?: (message: string) => void
}

interface FormErrors {
  title?: string
  description?: string
  frequency?: string
  start_date?: string
  end_date?: string
  general?: string
}

interface FormData {
  title: string
  description: string
  frequency: 'DAILY' | 'WEEKLY' | 'MONTHLY'
  start_date: string
  end_date: string
}

export default function RecurringTaskForm({
  onRecurringTaskCreated,
  onCancel,
  showSuccessToast,
  showErrorToast,
}: RecurringTaskFormProps) {
  const [formData, setFormData] = useState<FormData>({
    title: '',
    description: '',
    frequency: 'WEEKLY',
    start_date: new Date().toISOString().split('T')[0], // Today's date
    end_date: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)

  const { showSuccessToast: defaultSuccess, showErrorToast: defaultError } = useToast()

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

    // Frequency validation
    if (!formData.frequency) {
      newErrors.frequency = 'Frequency is required'
    }

    // Start date validation
    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required'
    }

    // End date validation (must be after start date)
    if (formData.end_date && formData.start_date) {
      const startDate = new Date(formData.start_date)
      const endDate = new Date(formData.end_date)
      if (endDate <= startDate) {
        newErrors.end_date = 'End date must be after start date'
      }
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
      // Prepare recurring task creation request
      const recurringTaskData = {
        title: formData.title,
        description: formData.description || undefined,
        frequency: formData.frequency,
        start_date: formData.start_date ? new Date(formData.start_date).toISOString() : undefined,
        end_date: formData.end_date ? new Date(formData.end_date).toISOString() : undefined,
      }

      // Call create recurring task API
      const response = await fetch('/api/recurring-tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(recurringTaskData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.message || 'Failed to create recurring task')
      }

      const createdRecurringTask = await response.json()

      // Call callback with created recurring task
      onRecurringTaskCreated(createdRecurringTask)

      // Show success toast
      if (showSuccessToast) {
        showSuccessToast('Recurring task created successfully')
      } else {
        defaultSuccess('Recurring task created successfully')
      }

      // Clear form
      setFormData({
        title: '',
        description: '',
        frequency: 'WEEKLY',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
      })
    } catch (error) {
      // Show error toast
      if (showErrorToast) {
        showErrorToast('Failed to create recurring task. Please try again.')
      } else {
        defaultError('Failed to create recurring task. Please try again.')
      }

      if (error instanceof Error) {
        setErrors({
          general: error.message || 'Failed to create recurring task. Please try again.',
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
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))

    // Clear field-specific error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

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
          background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
        }}
      >
        <h2 className="text-xl sm:text-2xl font-bold text-white">
          Create Recurring Task
        </h2>
        <p className="text-sm text-white/80 mt-1">
          Set up a task that repeats automatically
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
          <div className="space-y-2">
            <label
              htmlFor="title"
              className="block text-sm font-semibold"
              style={{ color: colors.neutral[700] }}
            >
              Title <span style={{ color: colors.error[500] }}>*</span>
            </label>
            <input
              id="title"
              name="title"
              type="text"
              required
              maxLength={200}
              className="w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2"
              style={{
                borderColor: errors.title ? colors.error[400] : colors.neutral[300],
                backgroundColor: colors.white,
                color: colors.neutral[900],
                fontSize: '0.9375rem',
              }}
              placeholder="e.g., Weekly team standup"
              value={formData.title}
              onChange={handleChange}
              disabled={isLoading}
            />
            {errors.title && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-sm"
                style={{ color: colors.error[600] }}
              >
                {errors.title}
              </motion.p>
            )}
          </div>

          {/* Description field */}
          <div className="space-y-2">
            <label
              htmlFor="description"
              className="block text-sm font-semibold"
              style={{ color: colors.neutral[700] }}
            >
              Description <span style={{ color: colors.neutral[400] }}>(optional)</span>
            </label>
            <textarea
              id="description"
              name="description"
              rows={3}
              maxLength={1000}
              className="w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2 resize-none"
              style={{
                borderColor: errors.description ? colors.error[400] : colors.neutral[300],
                backgroundColor: colors.white,
                color: colors.neutral[900],
                fontSize: '0.9375rem',
              }}
              placeholder="Enter task description (optional)"
              value={formData.description}
              onChange={handleChange}
              disabled={isLoading}
            />
            {errors.description && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-sm"
                style={{ color: colors.error[600] }}
              >
                {errors.description}
              </motion.p>
            )}
          </div>

          {/* Frequency field */}
          <div className="space-y-2">
            <label
              htmlFor="frequency"
              className="block text-sm font-semibold"
              style={{ color: colors.neutral[700] }}
            >
              Frequency <span style={{ color: colors.error[500] }}>*</span>
            </label>
            <select
              id="frequency"
              name="frequency"
              required
              className="w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2"
              style={{
                borderColor: errors.frequency ? colors.error[400] : colors.neutral[300],
                backgroundColor: colors.white,
                color: colors.neutral[900],
                fontSize: '0.9375rem',
              }}
              value={formData.frequency}
              onChange={handleChange}
              disabled={isLoading}
            >
              <option value="DAILY">Daily</option>
              <option value="WEEKLY">Weekly</option>
              <option value="MONTHLY">Monthly</option>
            </select>
            {errors.frequency && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-sm"
                style={{ color: colors.error[600] }}
              >
                {errors.frequency}
              </motion.p>
            )}
          </div>

          {/* Start date field */}
          <div className="space-y-2">
            <label
              htmlFor="start_date"
              className="block text-sm font-semibold"
              style={{ color: colors.neutral[700] }}
            >
              Start Date <span style={{ color: colors.error[500] }}>*</span>
            </label>
            <input
              id="start_date"
              name="start_date"
              type="date"
              required
              className="w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2"
              style={{
                borderColor: errors.start_date ? colors.error[400] : colors.neutral[300],
                backgroundColor: colors.white,
                color: colors.neutral[900],
                fontSize: '0.9375rem',
              }}
              value={formData.start_date}
              onChange={handleChange}
              disabled={isLoading}
            />
            {errors.start_date && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-sm"
                style={{ color: colors.error[600] }}
              >
                {errors.start_date}
              </motion.p>
            )}
          </div>

          {/* End date field */}
          <div className="space-y-2">
            <label
              htmlFor="end_date"
              className="block text-sm font-semibold"
              style={{ color: colors.neutral[700] }}
            >
              End Date <span style={{ color: colors.neutral[400] }}>(optional)</span>
            </label>
            <input
              id="end_date"
              name="end_date"
              type="date"
              className="w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2"
              style={{
                borderColor: errors.end_date ? colors.error[400] : colors.neutral[300],
                backgroundColor: colors.white,
                color: colors.neutral[900],
                fontSize: '0.9375rem',
              }}
              value={formData.end_date}
              onChange={handleChange}
              disabled={isLoading}
              min={formData.start_date}
            />
            <p className="text-xs" style={{ color: colors.neutral[500] }}>
              Leave empty for infinite recurrence
            </p>
            {errors.end_date && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-sm"
                style={{ color: colors.error[600] }}
              >
                {errors.end_date}
              </motion.p>
            )}
          </div>

          {/* Submit and Cancel buttons */}
          <div className="flex gap-3">
            <motion.button
              type="submit"
              disabled={isLoading}
              className="flex-1 py-4 px-6 rounded-xl text-white font-semibold shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed min-h-[56px] flex items-center justify-center gap-2"
              style={{
                background: isLoading
                  ? colors.neutral[400]
                  : 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
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
                  Creating...
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
                  Create Recurring Task
                </>
              )}
            </motion.button>

            <motion.button
              type="button"
              onClick={onCancel}
              disabled={isLoading}
              className="px-6 py-4 rounded-xl font-semibold border-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed min-h-[56px]"
              style={{
                borderColor: colors.neutral[300],
                backgroundColor: colors.white,
                color: colors.neutral[700],
              }}
              whileHover={{
                scale: 1.02,
                backgroundColor: colors.neutral[50],
              }}
              whileTap={{ scale: 0.98 }}
            >
              Cancel
            </motion.button>
          </div>
        </form>
      </div>
    </motion.div>
  )
}
