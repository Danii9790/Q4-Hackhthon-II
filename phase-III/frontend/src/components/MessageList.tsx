/**
 * MessageList Component
 *
 * Displays a list of chat messages with proper styling for user and assistant messages.
 * Supports automatic scrolling to the latest message.
 */

'use client'

import React, { useEffect, useRef } from 'react'
import type { ChatMessage } from '@/types/chat'
import { TypingIndicator } from './TypingIndicator'

interface MessageListProps {
  messages: ChatMessage[]
  isLoading?: boolean
}

/**
 * Formatted timestamp display
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return date.toLocaleDateString()
}

/**
 * MessageList component
 */
export function MessageList({ messages, isLoading }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
            Welcome to Todo AI Chatbot
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Start a conversation by sending a message below. I can help you
            manage tasks, create todos, and answer questions.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          <div
            className={`max-w-[80%] lg:max-w-[70%] rounded-lg px-4 py-3 ${
              message.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-sm'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-sm'
            }`}
          >
            {/* Message header with role */}
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold opacity-90">
                {message.role === 'user' ? 'You' : 'Assistant'}
              </span>
              <span className="text-xs opacity-75">
                {formatTimestamp(message.timestamp)}
              </span>
            </div>

            {/* Message content */}
            <div className="text-sm whitespace-pre-wrap break-words">
              {message.content}
            </div>

            {/* Tool calls display */}
            {message.tool_calls && message.tool_calls.length > 0 && (
              <div className="mt-2 pt-2 border-t border-white/20">
                <div className="text-xs opacity-90">
                  Used tools: {message.tool_calls.map((t) => t.tool_name).join(', ')}
                </div>
              </div>
            )}
          </div>
        </div>
      ))}

      {/* Loading indicator */}
      <TypingIndicator isVisible={isLoading} />

      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  )
}
