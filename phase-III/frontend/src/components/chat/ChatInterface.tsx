'use client'

/**
 * ChatInterface component for Todo AI Chatbot.
 *
 * This is the main container component that manages the chat interface state
 * and handles communication with the backend API.
 *
 * Features:
 * - Message state management
 * - Loading and error states
 * - Message submission to chat API
 * - Auto-scroll to latest message
 * - Typing indicator during API requests
 * - Toast notifications for errors
 * - Responsive design
 */
import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { chatApi } from '@/lib/api'
import { useToast } from '@/components/ui/ToastContainer'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import TypingIndicator from './TypingIndicator'
import { fadeInUp } from '@/lib/animations'
import { colors } from '@/styles/tokens'
import type { ChatMessage } from '@/types/chat'

interface ChatInterfaceProps {
  /**
   * Optional initial messages to display
   */
  initialMessages?: ChatMessage[]
}

/**
 * ChatInterface component.
 *
 * Manages chat state and API communication.
 */
export default function ChatInterface({ initialMessages = [] }: ChatInterfaceProps) {
  const toast = useToast()
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Handle sending a new message.
   */
  const handleSendMessage = useCallback(async (messageText: string) => {
    if (!messageText.trim() || isLoading) return

    // Create user message
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: messageText.trim(),
      created_at: new Date().toISOString(),
    }

    // Add user message to state
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      // Send message to API
      const response = await chatApi.sendMessage(messageText.trim())

      // Create assistant message
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: response.response,
        tool_calls: response.tool_calls,
        created_at: new Date().toISOString(),
      }

      // Add assistant message to state
      setMessages((prev) => [...prev, assistantMessage])

      // Show success toast if tool calls were made
      if (response.tool_calls.length > 0) {
        const successCount = response.tool_calls.filter(
          (tc) => tc.result.success
        ).length
        if (successCount > 0) {
          toast.showSuccess(
            `Completed ${successCount} task${successCount > 1 ? 's' : ''}`
          )
        }
      }
    } catch (err) {
      console.error('Failed to send message:', err)

      const errorMessage =
        err instanceof Error ? err.message : 'Failed to send message'

      setError(errorMessage)

      // Show error toast
      toast.showError(errorMessage)

      // Remove the user message if the request failed
      setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id))
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, toast])

  /**
   * Clear all messages.
   */
  const handleClearMessages = useCallback(() => {
    setMessages([])
    setError(null)
    toast.showSuccess('Conversation cleared')
  }, [toast])

  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      className="flex flex-col h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50"
    >
      {/* Header */}
      <header
        className="flex-shrink-0 border-b-2 px-6 py-4 bg-white shadow-sm"
        style={{ borderColor: colors.neutral[200] }}
      >
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          {/* Title and subtitle */}
          <div>
            <h1
              className="text-2xl sm:text-3xl font-bold"
              style={{
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              AI Task Assistant
            </h1>
            <p className="text-sm mt-1" style={{ color: colors.neutral[600] }}>
              Ask me anything about your tasks
            </p>
          </div>

          {/* Clear button */}
          {messages.length > 0 && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleClearMessages}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-semibold rounded-lg border-2 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              style={{
                borderColor: colors.neutral[300],
                color: colors.neutral[700],
                backgroundColor: colors.white,
              }}
              aria-label="Clear conversation"
            >
              Clear Chat
            </motion.button>
          )}
        </div>
      </header>

      {/* Messages list */}
      <div className="flex-1 overflow-hidden">
        <MessageList messages={messages} />
      </div>

      {/* Typing indicator */}
      <AnimatePresence mode="wait">
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="px-6 py-4 bg-white"
          >
            <div className="max-w-5xl mx-auto">
              <TypingIndicator text="AI is thinking..." />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Message input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={isLoading}
        placeholder="Ask me anything about your tasks..."
      />

      {/* Error display */}
      <AnimatePresence mode="wait">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="px-6 py-3 bg-white border-t-2"
            style={{ borderColor: colors.error[200] }}
          >
            <div className="max-w-5xl mx-auto flex items-center gap-3">
              <svg
                className="w-5 h-5 flex-shrink-0"
                style={{ color: colors.error[600] }}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="text-sm font-medium" style={{ color: colors.error[700] }}>
                {error}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
