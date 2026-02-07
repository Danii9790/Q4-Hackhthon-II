'use client'

/**
 * TaskItem component for displaying a single task.
 *
 * This component provides:
 * - Display of task title and description
 * - Visual indication of completion status
 * - Formatted creation date
 * - Optional toggle complete callback
 * - Smooth animations and modern card design
 * - Hover effects and micro-interactions
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import type { Task } from '@/types/task'
import { colors, borderRadius, shadows, spacing } from '@/styles/tokens'
import { cardHover, cardTap, staggerItem } from '@/lib/animations'

interface TaskItemProps {
  task: Task
  onToggleComplete?: (task: Task) => void
  onEdit?: (task: Task) => void
  onDelete?: (task: Task) => void
}

/**
 * Format date for display.
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) {
    return 'Just now'
  } else if (diffMins < 60) {
    return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  } else if (diffDays < 7) {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  } else {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    })
  }
}

export default function TaskItem({ task, onToggleComplete, onEdit, onDelete }: TaskItemProps) {
  const [isHovered, setIsHovered] = useState(false)
  const hasDescription = task.description && task.description.trim().length > 0

  const cardStyles = task.completed
    ? {
        background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
        border: `2px solid ${colors.success[200]}`,
      }
    : {
        background: colors.white,
        border: `2px solid ${isHovered ? colors.primary[300] : colors.neutral[200]}`,
      }

  const checkboxVariants = {
    unchecked: {
      scale: 1,
      borderColor: colors.neutral[300],
      backgroundColor: colors.white,
    },
    checked: {
      scale: 1,
      borderColor: colors.success[500],
      backgroundColor: colors.success[500],
    },
    hover: {
      scale: 1.05,
      borderColor: task.completed ? colors.success[500] : colors.success[400],
    },
  }

  const checkmarkVariants = {
    unchecked: {
      pathLength: 0,
      opacity: 0,
      transition: { duration: 0.2 },
    },
    checked: {
      pathLength: 1,
      opacity: 1,
      transition: { duration: 0.3 },
    },
  }

  return (
    <motion.div
      variants={staggerItem}
      initial="hidden"
      animate="visible"
      exit="exit"
      whileHover="hover"
      whileTap="tap"
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className="relative overflow-hidden rounded-xl shadow-sm transition-all duration-300"
      style={{
        ...cardStyles,
        boxShadow: isHovered && !task.completed ? shadows.md : shadows.sm,
      }}
    >
      {/* Gradient overlay for hover effect */}
      {!task.completed && (
        <motion.div
          className="absolute inset-0 opacity-0 pointer-events-none"
          animate={{
            opacity: isHovered ? 0.03 : 0,
          }}
          style={{
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          }}
          transition={{ duration: 0.3 }}
        />
      )}

      <div className="relative p-4 sm:p-5">
        <div className="flex items-start gap-3 sm:gap-4">
          {/* Animated completion checkbox */}
          <div className="flex-shrink-0 pt-1">
            {onToggleComplete ? (
              <motion.button
                onClick={() => onToggleComplete(task)}
                className="w-7 h-7 sm:w-6 sm:h-6 rounded-lg flex items-center justify-center touch-manipulation focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-success-500"
                style={{
                  borderRadius: borderRadius.lg,
                  border: `2px solid ${task.completed ? colors.success[500] : colors.neutral[300]}`,
                  backgroundColor: task.completed ? colors.success[500] : colors.white,
                }}
                variants={checkboxVariants}
                initial={task.completed ? 'checked' : 'unchecked'}
                    animate={task.completed ? 'checked' : 'unchecked'}
                whileHover="hover"
                whileTap={{ scale: 0.9 }}
                aria-label={task.completed ? 'Mark as incomplete' : 'Mark as complete'}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <motion.path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M5 13l4 4L19 7"
                    variants={checkmarkVariants}
                    initial={task.completed ? 'checked' : 'unchecked'}
                    animate={task.completed ? 'checked' : 'unchecked'}
                  />
                </svg>
              </motion.button>
            ) : (
              <div
                className="w-7 h-7 sm:w-6 sm:h-6 rounded-lg flex items-center justify-center"
                style={{
                  borderRadius: borderRadius.lg,
                  border: `2px solid ${task.completed ? colors.success[500] : colors.neutral[300]}`,
                  backgroundColor: task.completed ? colors.success[500] : colors.white,
                }}
              >
                {task.completed && (
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                )}
              </div>
            )}
          </div>

          {/* Task content */}
          <div className="flex-1 min-w-0">
            {/* Title with strikethrough animation */}
            <motion.h3
              className="text-base sm:text-lg font-semibold"
              animate={{
                color: task.completed ? colors.neutral[500] : colors.neutral[900],
                textDecoration: task.completed ? 'line-through' : 'none',
              }}
              transition={{ duration: 0.3 }}
            >
              {task.title}
            </motion.h3>

            {/* Description with fade animation */}
            {hasDescription && (
              <motion.p
                className="mt-1 text-sm"
                animate={{
                  color: task.completed ? colors.neutral[400] : colors.neutral[600],
                  textDecoration: task.completed ? 'line-through' : 'none',
                }}
                transition={{ duration: 0.3 }}
              >
                {task.description}
              </motion.p>
            )}

            {/* Metadata */}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {/* Completion status badge */}
              <motion.span
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold"
                style={{
                  backgroundColor: task.completed ? colors.success[100] : colors.primary[100],
                  color: task.completed ? colors.success[700] : colors.primary[700],
                }}
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
                {task.completed ? 'Completed' : 'In Progress'}
              </motion.span>

              {/* Created date */}
              <span
                className="text-xs font-medium"
                style={{ color: colors.neutral[500] }}
              >
                Created {formatDate(task.created_at)}
              </span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Edit button */}
            {onEdit && (
              <motion.button
                onClick={() => onEdit(task)}
                className="inline-flex items-center justify-center p-2.5 sm:p-2 border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 touch-manipulation min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0"
                style={{
                  borderColor: colors.neutral[300],
                  color: colors.neutral[700],
                  backgroundColor: colors.white,
                  borderRadius: borderRadius.md,
                }}
                whileHover={{
                  borderColor: colors.primary[300],
                  backgroundColor: colors.primary[50],
                  color: colors.primary[600],
                }}
                whileTap={{ scale: 0.95 }}
                aria-label="Edit task"
                title="Edit task"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </motion.button>
            )}

            {/* Delete button */}
            {onDelete && (
              <motion.button
                onClick={() => onDelete(task)}
                className="inline-flex items-center justify-center p-2.5 sm:p-2 border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-error-500 touch-manipulation min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0"
                style={{
                  borderColor: colors.neutral[300],
                  color: colors.neutral[700],
                  backgroundColor: colors.white,
                  borderRadius: borderRadius.md,
                }}
                whileHover={{
                  borderColor: colors.error[300],
                  backgroundColor: colors.error[50],
                  color: colors.error[600],
                }}
                whileTap={{ scale: 0.95 }}
                aria-label="Delete task"
                title="Delete task"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </motion.button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
