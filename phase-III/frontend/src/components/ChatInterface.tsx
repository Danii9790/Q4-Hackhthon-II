/**
 * ChatInterface Component
 *
 * Main chat interface container that integrates the message list and input.
 * Handles the overall layout and error display.
 */

'use client'

import React from 'react'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { useChat } from '@/hooks/useChat'

interface ChatInterfaceProps {
  userId: string
  initialConversationId?: string
}

/**
 * ChatInterface component
 */
export function ChatInterface({
  userId,
  initialConversationId,
}: ChatInterfaceProps) {
  const { messages, isLoading, error, sendMessage, clearError } = useChat(
    userId,
    initialConversationId
  )

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-950">
      {/* Error banner */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 px-4 py-3">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg
                className="h-5 w-5 text-red-600 dark:text-red-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-sm text-red-800 dark:text-red-200">
                {error}
              </span>
            </div>
            <button
              onClick={clearError}
              className="text-sm text-red-700 dark:text-red-300 hover:text-red-900 dark:hover:text-red-100 underline"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Messages area */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Input area */}
      <MessageInput
        onSendMessage={sendMessage}
        isLoading={isLoading}
        disabled={isLoading}
        placeholder="Ask me anything about your tasks..."
      />
    </div>
  )
}
