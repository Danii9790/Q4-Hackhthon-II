/**
 * Chat Page
 *
 * Main chat interface with authentication protection.
 * Redirects unauthenticated users to the sign-in page.
 */

'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { ChatInterface } from '@/components/ChatInterface'
import { useAuth } from '@/hooks/useAuth'

/**
 * Chat page component with auth protection
 */
export default function ChatPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading, user } = useAuth()

  /**
   * Redirect to sign-in if not authenticated
   */
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/signin')
    }
  }, [isLoading, isAuthenticated, router])

  /**
   * Show loading state while checking authentication
   */
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-950">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Loading...
          </p>
        </div>
      </div>
    )
  }

  /**
   * Show nothing while redirecting
   */
  if (!isAuthenticated) {
    return null
  }

  /**
   * Render chat interface when authenticated
   */
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo/Title */}
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg
                className="h-5 w-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Todo AI Chatbot
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Your intelligent task assistant
              </p>
            </div>
          </div>

          {/* User info and logout */}
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {user?.name || user?.email}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {user?.email}
              </p>
            </div>

            <button
              onClick={() => router.push('/signout')}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Chat interface */}
      <main className="flex-1 overflow-hidden">
        {user?.id && <ChatInterface userId={user.id} />}
      </main>
    </div>
  )
}
