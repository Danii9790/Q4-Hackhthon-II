'use client'

/**
 * MessageList component for chat interface.
 *
 * This component displays the list of chat messages between the user and AI.
 *
 * Features:
 * - Role-based message styling (user vs assistant)
 * - Tool calls display with success indicators
 * - Auto-scroll to latest message
 * - Timestamp display
 * - Smooth animations
 * - Responsive design
 */
import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { colors, borderRadius } from '@/styles/tokens'
import { staggerContainer, fadeIn, scaleIn } from '@/lib/animations'
import type { ChatMessage } from '@/types/chat'

interface MessageListProps {
  /**
   * Array of chat messages to display
   */
  messages: ChatMessage[]

  /**
   * Optional callback to get reference to messages end element
   */
  onScrollToEnd?: () => void
}

/**
 * MessageList component.
 *
 * Displays messages with role-based styling and auto-scrolls to bottom.
 */
export default function MessageList({ messages, onScrollToEnd }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  /**
   * Auto-scroll to bottom when new messages arrive.
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    onScrollToEnd?.()
  }, [messages, onScrollToEnd])

  /**
   * Format timestamp for display.
   */
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp)
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()

    if (isToday) {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      })
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      })
    }
  }

  /**
   * Render tool calls with success indicators.
   */
  const renderToolCalls = (toolCalls: ChatMessage['tool_calls']) => {
    if (!toolCalls || toolCalls.length === 0) return null

    return (
      <div className="mt-3 space-y-2">
        {toolCalls.map((toolCall, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1, duration: 0.3 }}
            className="flex items-start gap-2 px-3 py-2 rounded-lg border"
            style={{
              backgroundColor: toolCall.result.success
                ? colors.success[50]
                : colors.error[50],
              borderColor: toolCall.result.success
                ? colors.success[200]
                : colors.error[200],
            }}
          >
            {/* Success/Failure Icon */}
            <div className="flex-shrink-0 mt-0.5">
              {toolCall.result.success ? (
                <svg
                  className="w-4 h-4"
                  style={{ color: colors.success[600] }}
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg
                  className="w-4 h-4"
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
              )}
            </div>

            {/* Tool call details */}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold" style={{ color: colors.neutral[700] }}>
                {toolCall.tool_name.replace(/_/g, ' ')}
              </p>
              <p className="text-xs mt-1" style={{ color: colors.neutral[600] }}>
                {toolCall.result.success
                  ? 'Successfully completed'
                  : 'Failed to complete'}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    )
  }

  if (messages.length === 0) {
    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={scaleIn}
        className="flex-1 flex items-center justify-center p-8"
      >
        <div className="text-center max-w-md">
          {/* Empty state illustration */}
          <motion.div
            className="relative mb-6 mx-auto w-24 h-24"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{
              type: 'spring',
              stiffness: 200,
              damping: 15,
              delay: 0.2,
            }}
          >
            {/* Animated background rings */}
            <motion.div
              className="absolute inset-0 rounded-full opacity-20"
              style={{ backgroundColor: colors.primary[500] }}
              animate={{
                scale: [1, 1.3, 1],
                opacity: [0.2, 0.1, 0.2],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
            <motion.div
              className="absolute inset-2 rounded-full opacity-20"
              style={{ backgroundColor: colors.secondary[500] }}
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.2, 0.1, 0.2],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: 0.5,
              }}
            />

            {/* Chat icon */}
            <div
              className="relative w-full h-full rounded-full flex items-center justify-center"
              style={{ backgroundColor: colors.primary[100] }}
            >
              <svg
                className="w-12 h-12"
                style={{ color: colors.primary[600] }}
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
          </motion.div>

          {/* Empty state text */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <h3
              className="text-2xl font-bold mb-3"
              style={{ color: colors.neutral[900] }}
            >
              Start a conversation
            </h3>
            <p
              className="text-base leading-relaxed"
              style={{ color: colors.neutral[600] }}
            >
              Ask me anything about your tasks. I can help you create, complete,
              update, or delete tasks using natural language.
            </p>

            {/* Example prompts */}
            <div className="mt-6 space-y-2 text-left">
              <p
                className="text-xs font-semibold uppercase tracking-wide"
                style={{ color: colors.neutral[500] }}
              >
                Try asking:
              </p>
              <div className="space-y-2">
                {[
                  'Add a task to buy groceries',
                  'Show me my incomplete tasks',
                  'Mark the "Buy groceries" task as complete',
                ].map((example, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    className="px-4 py-2 rounded-lg text-sm cursor-pointer hover:shadow-md transition-shadow"
                    style={{
                      backgroundColor: colors.neutral[50],
                      border: `1px solid ${colors.neutral[200]}`,
                      color: colors.neutral[700],
                    }}
                  >
                    "{example}"
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="flex-1 overflow-y-auto px-4 py-6 space-y-6"
      style={{ scrollBehavior: 'smooth' }}
    >
      <AnimatePresence mode="popLayout">
        {messages.map((message, index) => (
          <motion.div
            key={message.id}
            layout
            variants={fadeIn}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{
              layout: { duration: 0.3 },
              opacity: { duration: 0.2 },
            }}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`flex max-w-[85%] sm:max-w-[75%] ${
                message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              } gap-3`}
            >
              {/* Avatar */}
              <div
                className={`flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center ${
                  message.role === 'user' ? 'ml-2' : 'mr-2'
                }`}
                style={{
                  backgroundColor:
                    message.role === 'user'
                      ? colors.primary[500]
                      : colors.secondary[500],
                }}
              >
                {message.role === 'user' ? (
                  // User icon
                  <svg
                    className="w-5 h-5 sm:w-6 sm:h-6"
                    style={{ color: colors.white }}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  // AI icon
                  <svg
                    className="w-5 h-5 sm:w-6 sm:h-6"
                    style={{ color: colors.white }}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v7.333l-2-2V6a1 1 0 00-1-1 1 1 0 00-1 1v.333zM13 4a1 1 0 011-1 2 2 0 012 2v6.5a1 1 0 01-1 1H13V4z" />
                  </svg>
                )}
              </div>

              {/* Message content */}
              <div
                className={`flex-1 px-4 py-3 rounded-2xl ${
                  message.role === 'user'
                    ? 'rounded-tr-sm'
                    : 'rounded-tl-sm'
                } shadow-sm`}
                style={{
                  backgroundColor:
                    message.role === 'user'
                      ? colors.primary[500]
                      : colors.white,
                  color: message.role === 'user'
                    ? colors.white
                    : colors.neutral[900],
                  border:
                    message.role === 'assistant'
                      ? `2px solid ${colors.neutral[200]}`
                      : 'none',
                }}
              >
                {/* Message text */}
                <p className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap break-words">
                  {message.content}
                </p>

                {/* Tool calls (for assistant messages only) */}
                {message.role === 'assistant' &&
                  renderToolCalls(message.tool_calls)}

                {/* Timestamp */}
                <div
                  className={`mt-2 text-xs opacity-75 ${
                    message.role === 'user' ? 'text-right' : 'text-left'
                  }`}
                  style={{
                    color:
                      message.role === 'user'
                        ? 'rgba(255, 255, 255, 0.8)'
                        : colors.neutral[500],
                  }}
                >
                  {formatTimestamp(message.created_at)}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Invisible element for auto-scroll */}
      <div ref={messagesEndRef} />
    </motion.div>
  )
}
