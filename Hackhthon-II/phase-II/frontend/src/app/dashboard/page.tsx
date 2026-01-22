/**
 * Dashboard page for Todo Application.
 *
 * This page displays the user's task list and allows creating new tasks.
 * It's protected - users must be authenticated to access it.
 *
 * Features:
 * - Displays list of user's tasks
 * - Allows creating new tasks
 * - Shows loading and empty states
 * - Handles authentication and redirects
 * - Modern UI with Framer Motion animations
 * - Gradient effects and smooth transitions
 * - Responsive design
 */
'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { taskApi } from '@/lib/api'
import { useToast } from '@/components/ui/ToastContainer'
import CreateTaskForm from '@/components/task/CreateTaskForm'
import TaskList from '@/components/task/TaskList'
import EditTaskModal from '@/components/task/EditTaskModal'
import ConfirmDeleteDialog from '@/components/task/ConfirmDeleteDialog'
import type { Task } from '@/types/task'
import { fadeInUp, staggerContainer, buttonHover, buttonTap, shimmer, getMotionProps } from '@/lib/animations'
import { gradients, colors, shadows } from '@/styles/tokens'

interface UserData {
  id: string
  email: string
  name?: string
}

export default function DashboardPage() {
  const router = useRouter()
  const toast = useToast()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [tasks, setTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<UserData | null>(null)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [deletingTask, setDeletingTask] = useState<Task | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  /**
   * Fetch tasks from the API.
   */
  const fetchTasks = useCallback(async () => {
    try {
      setIsLoading(true)
      const response = await taskApi.getTasks(0, 50)
      setTasks(response.tasks)
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
      // API interceptor will handle 401 and redirect to login
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Handle task creation callback.
   */
  const handleTaskCreated = useCallback((task: Task) => {
    setTasks((prev) => [task, ...prev])
  }, [])

  /**
   * Handle task toggle complete callback.
   */
  const handleToggleComplete = useCallback(async (task: Task) => {
    try {
      let updatedTask: Task
      if (task.completed) {
        updatedTask = await taskApi.uncompleteTask(task.id)
      } else {
        updatedTask = await taskApi.completeTask(task.id)
      }

      // Update the task in the list
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? updatedTask : t))
      )

      // Show success toast
      toast.showSuccess(
        task.completed ? 'Task marked as incomplete' : 'Task completed'
      )
    } catch (error) {
      console.error('Failed to toggle task completion:', error)
      toast.showError('Failed to update task. Please try again.')
    }
  }, [toast])

  /**
   * Handle opening edit modal for a task.
   */
  const handleOpenEdit = useCallback((task: Task) => {
    setEditingTask(task)
  }, [])

  /**
   * Handle closing edit modal.
   */
  const handleCloseEdit = useCallback(() => {
    setEditingTask(null)
  }, [])

  /**
   * Handle successful task update.
   */
  const handleUpdateTask = useCallback((updatedTask: Task) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === updatedTask.id ? updatedTask : t))
    )
  }, [])

  /**
   * Handle delete button click - opens confirmation dialog.
   */
  const handleDeleteClick = useCallback((task: Task) => {
    setDeletingTask(task)
  }, [])

  /**
   * Handle cancel delete - closes confirmation dialog.
   */
  const handleCancelDelete = useCallback(() => {
    setDeletingTask(null)
  }, [])

  /**
   * Handle confirm delete - performs deletion and closes dialog.
   */
  const handleConfirmDelete = useCallback(async () => {
    if (!deletingTask) return

    setIsDeleting(true)

    try {
      await taskApi.deleteTask(deletingTask.id)

      // Remove the deleted task from state
      setTasks((prev) => prev.filter((t) => t.id !== deletingTask.id))

      // Close the dialog
      setDeletingTask(null)

      // Show success toast
      toast.showSuccess('Task deleted successfully')
    } catch (error) {
      console.error('Failed to delete task:', error)
      toast.showError('Failed to delete task. Please try again.')
      // Keep dialog open on error so user can retry or cancel
    } finally {
      setIsDeleting(false)
    }
  }, [deletingTask, toast])

  /**
   * Handle sign out.
   */
  const handleSignOut = useCallback(async () => {
    try {
      const { authClient } = await import('@/lib/auth')
      await authClient.signOut()
    } catch (error) {
      console.error('Failed to sign out:', error)
    }

    // Clear localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_data')
    }

    router.push('/login')
  }, [router])

  /**
   * Check authentication status on mount.
   */
  useEffect(() => {
    const checkAuth = () => {
      if (typeof window === 'undefined') return

      const token = localStorage.getItem('auth_token')
      const userDataStr = localStorage.getItem('user_data')

      if (!token) {
        router.push('/login')
        return
      }

      if (userDataStr) {
        try {
          const userData = JSON.parse(userDataStr)
          setUser(userData)
        } catch (error) {
          console.error('Failed to parse user data:', error)
        }
      }

      setIsAuthenticated(true)
    }

    checkAuth()
  }, [router])

  /**
   * Fetch tasks when authenticated.
   */
  useEffect(() => {
    if (isAuthenticated) {
      fetchTasks()
    }
  }, [isAuthenticated, fetchTasks])

  // Show loading while checking authentication
  if (!isAuthenticated) {
    return (
      <motion.main
        {...getMotionProps({
          variants: fadeInUp,
          initial: 'hidden',
          animate: 'visible',
        })}
        className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center"
      >
        <div className="text-center">
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              rotate: [0, 360],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            className="w-16 h-16 mx-auto mb-6 relative"
          >
            <div
              className="absolute inset-0 rounded-full"
              style={{
                background: gradients.primary,
                filter: 'blur(8px)',
              }}
            />
            <div
              className="absolute inset-1 rounded-full flex items-center justify-center"
              style={{ background: gradients.primary }}
            >
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </div>
          </motion.div>
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-gray-600 font-medium"
          >
            Loading your workspace...
          </motion.p>
        </div>
      </motion.main>
    )
  }

  return (
    <motion.main
      {...getMotionProps({
        variants: fadeInUp,
        initial: 'hidden',
        animate: 'visible',
      })}
      className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50"
    >
      {/* Animated Header */}
      <header
        className="relative overflow-hidden border-b border-indigo-100"
        style={{
          background: `linear-gradient(135deg, ${colors.primary[50]} 0%, ${colors.secondary[50]} 50%, ${colors.accent[50]} 100%)`,
        }}
      >
        {/* Animated background shapes */}
        <div className="absolute inset-0 overflow-hidden">
          <motion.div
            animate={{
              x: [0, 100, 0],
              y: [0, -100, 0],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: 'linear',
            }}
            className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-20"
            style={{
              background: gradients.primary,
              filter: 'blur(80px)',
            }}
          />
          <motion.div
            animate={{
              x: [0, -100, 0],
              y: [0, 100, 0],
            }}
            transition={{
              duration: 25,
              repeat: Infinity,
              ease: 'linear',
            }}
            className="absolute bottom-0 left-0 w-96 h-96 rounded-full opacity-20"
            style={{
              background: gradients.secondary,
              filter: 'blur(80px)',
            }}
          />
        </div>

        <div className="relative max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
          >
            <div>
              <motion.h1
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="text-4xl sm:text-5xl font-bold mb-2"
                style={{
                  background: gradients.primary,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                Dashboard
              </motion.h1>
              <AnimatePresence mode="wait">
                {user && (
                  <motion.p
                    key="welcome"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.4, delay: 0.2 }}
                    className="text-base text-gray-600 font-medium"
                  >
                    {user.name ? `Welcome back, ${user.name}` : `Welcome back, ${user.email}`}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex items-center gap-3 w-full sm:w-auto"
            >
              <motion.button
                whileHover={buttonHover}
                whileTap={buttonTap}
                onClick={fetchTasks}
                disabled={isLoading}
                className="flex-1 sm:flex-none px-5 py-2.5 text-sm font-semibold text-white rounded-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all duration-200 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                style={{
                  background: gradients.primary,
                  boxShadow: shadows['primary-md'],
                }}
              >
                <motion.svg
                  animate={isLoading ? { rotate: 360 } : {}}
                  transition={isLoading ? { duration: 1, repeat: Infinity, ease: 'linear' } : {}}
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </motion.svg>
                Refresh
              </motion.button>

              <motion.button
                whileHover={buttonHover}
                whileTap={buttonTap}
                onClick={handleSignOut}
                className="flex-1 sm:flex-none px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-red-500 to-red-600 rounded-lg shadow-lg hover:from-red-600 hover:to-red-700 transition-all duration-200 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                style={{
                  boxShadow: shadows['error-sm'],
                }}
              >
                Sign Out
              </motion.button>
            </motion.div>
          </motion.div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-4xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-8"
        >
          {/* Create Task Form */}
          <motion.div variants={fadeInUp}>
            <CreateTaskForm
              onTaskCreated={handleTaskCreated}
              showSuccessToast={toast.showSuccess}
              showErrorToast={toast.showError}
            />
          </motion.div>

          {/* Task List */}
          <motion.div variants={fadeInUp}>
            <TaskList
              tasks={tasks}
              isLoading={isLoading}
              onToggleComplete={handleToggleComplete}
              onEdit={handleOpenEdit}
              onDelete={handleDeleteClick}
            />
          </motion.div>
        </motion.div>
      </div>

      {/* Edit Task Modal */}
      <AnimatePresence mode="wait">
        {editingTask && (
          <EditTaskModal
            task={editingTask}
            isOpen={!!editingTask}
            onClose={handleCloseEdit}
            onUpdate={handleUpdateTask}
            showSuccessToast={toast.showSuccess}
            showErrorToast={toast.showError}
          />
        )}
      </AnimatePresence>

      {/* Delete Confirmation Dialog */}
      <AnimatePresence mode="wait">
        {deletingTask && (
          <ConfirmDeleteDialog
            isOpen={!!deletingTask}
            taskTitle={deletingTask.title}
            onConfirm={handleConfirmDelete}
            onCancel={handleCancelDelete}
            isLoading={isDeleting}
          />
        )}
      </AnimatePresence>
    </motion.main>
  )
}
