'use client'

/**
 * TaskList component for displaying a list of tasks.
 *
 * This component provides:
 * - Display of multiple tasks using TaskItem components
 * - Empty state message when no tasks exist
 * - Loading state with skeleton animation
 * - Optional callback for toggling task completion
 * - Staggered list animations
 * - Modern, responsive design
 */
import { motion, AnimatePresence } from 'framer-motion'
import type { Task } from '@/types/task'
import TaskItem from './TaskItem'
import { colors, borderRadius } from '@/styles/tokens'
import { staggerContainer, fadeIn, scaleIn, loadingPulse } from '@/lib/animations'

interface TaskListProps {
  tasks: Task[]
  isLoading?: boolean
  onToggleComplete?: (task: Task) => void
  onEdit?: (task: Task) => void
  onDelete?: (task: Task) => void
}

export default function TaskList({
  tasks,
  isLoading = false,
  onToggleComplete,
  onEdit,
  onDelete,
}: TaskListProps) {
  // Loading state with skeleton animation
  if (isLoading) {
    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={fadeIn}
        className="bg-white rounded-2xl shadow-lg border-2 border-gray-200 overflow-hidden"
      >
        <div className="p-8 sm:p-12">
          <div className="flex flex-col items-center justify-center">
            {/* Animated loading spinner */}
            <motion.div
              className="relative mb-6"
              animate={{ rotate: 360 }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: 'linear',
              }}
            >
              <div
                className="w-16 h-16 rounded-full border-4 border-gray-200"
                style={{ borderTopColor: colors.primary[500] }}
              />
            </motion.div>

            {/* Loading text with pulse */}
            <motion.div
              className="text-center"
              animate={loadingPulse}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <p
                className="text-base font-semibold"
                style={{ color: colors.neutral[900] }}
              >
                Loading your tasks...
              </p>
              <p className="text-sm mt-1" style={{ color: colors.neutral[500] }}>
                Please wait a moment
              </p>
            </motion.div>
          </div>
        </div>
      </motion.div>
    )
  }

  // Empty state with modern design and animations
  if (tasks.length === 0) {
    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={scaleIn}
        className="bg-white rounded-2xl shadow-md border-2 border-dashed overflow-hidden"
        style={{
          borderColor: colors.neutral[300],
          backgroundColor: 'linear-gradient(135deg, #fafafa 0%, #ffffff 100%)',
        }}
      >
        <div className="p-8 sm:p-12">
          <div className="flex flex-col items-center justify-center text-center">
            {/* Animated empty state illustration */}
            <motion.div
              className="relative mb-6"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{
                type: 'spring',
                stiffness: 200,
                damping: 15,
                delay: 0.2,
              }}
            >
              {/* Outer ring */}
              <motion.div
                className="absolute inset-0 rounded-full opacity-20"
                style={{ backgroundColor: colors.primary[500] }}
                animate={{
                  scale: [1, 1.2, 1],
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
                  backgroundColor: colors.primary[100],
                }}
              >
                <svg
                  className="w-10 h-10"
                  style={{ color: colors.primary[600] }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <motion.path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 1, delay: 0.5, ease: 'easeInOut' }}
                  />
                </svg>
              </div>
            </motion.div>

            {/* Empty state text */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <h3
                className="text-xl sm:text-2xl font-bold mb-3"
                style={{ color: colors.neutral[900] }}
              >
                No tasks yet
              </h3>
              <p
                className="text-base max-w-sm mx-auto leading-relaxed"
                style={{ color: colors.neutral[600] }}
              >
                Get started by creating your first task. Use the form above to add tasks to your todo list.
              </p>
            </motion.div>

            {/* Animated arrow pointing to form */}
            <motion.div
              className="mt-6"
              animate={{
                y: [0, -8, 0],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              <svg
                className="w-6 h-6 mx-auto"
                style={{ color: colors.primary[500] }}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 15l7-7 7 7"
                />
              </svg>
            </motion.div>
          </div>
        </div>
      </motion.div>
    )
  }

  // Task count summary
  const completedCount = tasks.filter((t) => t.completed).length
  const totalCount = tasks.length
  const progressPercentage = (completedCount / totalCount) * 100

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      exit="exit"
      variants={staggerContainer}
      className="space-y-4"
    >
      {/* Task count summary with progress bar */}
      <motion.div
        variants={fadeIn}
        className="bg-white rounded-xl shadow-md border-2 p-4 sm:p-5 mb-6"
        style={{ borderColor: colors.neutral[200] }}
      >
        <div className="flex items-center justify-between mb-3">
          <h2
            className="text-lg sm:text-xl font-bold"
            style={{ color: colors.neutral[900] }}
          >
            Your Tasks{' '}
            <span
              className="font-normal"
              style={{ color: colors.neutral[500] }}
            >
              ({totalCount})
            </span>
          </h2>
          <div
            className="text-sm font-semibold px-3 py-1 rounded-full"
            style={{
              backgroundColor: colors.primary[100],
              color: colors.primary[700],
            }}
          >
            {completedCount} of {totalCount} completed
          </div>
        </div>

        {/* Progress bar */}
        <div className="relative h-2 rounded-full overflow-hidden" style={{ backgroundColor: colors.neutral[200] }}>
          <motion.div
            className="absolute inset-y-0 left-0 rounded-full"
            style={{
              background: 'linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%)',
            }}
            initial={{ width: 0 }}
            animate={{ width: `${progressPercentage}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>
      </motion.div>

      {/* Task items with AnimatePresence for smooth add/remove */}
      <AnimatePresence mode="popLayout">
        {tasks.map((task) => (
          <TaskItem
            key={task.id}
            task={task}
            onToggleComplete={onToggleComplete}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </AnimatePresence>
    </motion.div>
  )
}
