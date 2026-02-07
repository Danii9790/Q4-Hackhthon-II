'use client'

/**
 * Floating Chat Widget Component for Dashboard.
 *
 * Adds an AI chatbot button in the bottom-right corner that opens a small chat interface.
 * Users can interact with the AI to manage tasks through natural language.
 *
 * Features:
 * - Floating button in bottom-right corner
 * - Expandable chat window
 * - Minimize/close functionality
 * - Integration with backend chat API
 * - Smooth animations
 * - MCP tool support for task CRUD
 */
'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { chatApi } from '@/lib/api'
import { useToast } from '@/components/ui/ToastContainer'
import { colors, borderRadius, shadows } from '@/styles/tokens'
import type { ChatMessage } from '@/types/chat'

interface ChatWidgetProps {
  /**
   * Current user ID for chat API
   */
  userId?: string
}

/**
 * ChatWidget Component.
 *
 * Floating chat widget that expands when clicked.
 */
export default function ChatWidget({ userId }: ChatWidgetProps) {
  const toast = useToast()
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  /**
   * Auto-scroll to bottom when new messages arrive.
   */
  useEffect(() => {
    if (isOpen && !isMinimized) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen, isMinimized])

  /**
   * Reset unread count when chat is opened.
   */
  useEffect(() => {
    if (isOpen) {
      setUnreadCount(0)
    }
  }, [isOpen])

  /**
   * Send message to AI assistant.
   */
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !userId) return

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: inputValue.trim(),
      created_at: new Date().toISOString(),
    }

    // Add user message
    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Send to backend chat API
      const response = await chatApi.sendMessage(inputValue.trim())

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: response.response,
        tool_calls: response.tool_calls,
        created_at: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, assistantMessage])

      // Show success if tools were used
      if (response.tool_calls.length > 0) {
        const successCount = response.tool_calls.filter((tc) => tc.result.success).length
        if (successCount > 0) {
          toast.showSuccess(`Completed ${successCount} task${successCount > 1 ? 's' : ''}`)
        }
      }
    } catch (err) {
      console.error('Chat error:', err)
      // Remove user message if failed
      setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id))
      toast.showError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Handle Enter key press.
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  /**
   * Toggle chat open/close.
   */
  const toggleChat = () => {
    setIsOpen((prev) => !prev)
    if (!isOpen) {
      setUnreadCount(0)
    }
  }

  /**
   * Close chat.
   */
  const closeChat = () => {
    setIsOpen(false)
    setIsMinimized(false)
  }

  /**
   * Minimize chat.
   */
  const minimizeChat = () => {
    setIsMinimized(true)
  }

  /**
   * Restore chat from minimized.
   */
  const restoreChat = () => {
    setIsMinimized(false)
  }

  return (
    <>
      {/* Floating Chat Button */}
      <AnimatePresence mode="wait">
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0, rotate: -180 }}
            animate={{ scale: 1, opacity: 1, rotate: 0 }}
            exit={{ scale: 0, opacity: 0, rotate: 180 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleChat}
            className="fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full shadow-2xl flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-300"
            style={{
              background: `linear-gradient(135deg, ${colors.primary[500]} 0%, ${colors.primary[600]} 100%)`,
              boxShadow: shadows['primary-lg'],
            }}
            title="Open AI Assistant"
          >
            {/* Chat icon */}
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 20H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v12a2 2 0 01-2 2h-4l-3 3z"
              />
            </svg>

            {/* Unread badge */}
            {unreadCount > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
              >
                {unreadCount > 9 ? '9+' : unreadCount}
              </motion.span>
            )}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence mode="wait">
        {(isOpen || isMinimized) && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{
              opacity: 1,
              scale: 1,
              y: 0,
              height: isMinimized ? 60 : 'auto',
            }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            transition={{ duration: 0.3 }}
            className="fixed bottom-6 right-6 z-50 w-[calc(100vw-3rem)] sm:w-96 bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden"
            style={{
              maxHeight: isMinimized ? 60 : '600px',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Header */}
            <div
              className="px-4 py-3 border-b border-gray-200 flex items-center justify-between"
              style={{ backgroundColor: colors.primary[50] }}
            >
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: colors.primary[100] }}
                >
                  <svg
                    className="w-5 h-5"
                    style={{ color: colors.primary[600] }}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 20H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v12a2 2 0 01-2 2h-4l-3 3z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-semibold" style={{ color: colors.neutral[900] }}>
                    AI Assistant
                  </h3>
                  {!isMinimized && (
                    <p className="text-xs" style={{ color: colors.neutral[500] }}>
                      Ask me to manage your tasks
                    </p>
                  )}
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-1">
                {isMinimized ? (
                  <button
                    onClick={restoreChat}
                    className="p-1 hover:bg-gray-100 rounded transition-colors"
                    title="Restore"
                  >
                    <svg className="w-5 h-5" style={{ color: colors.neutral[600] }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 16l-4-4m0 0l4 4m4-12v4m0 0h4" />
                    </svg>
                  </button>
                ) : (
                  <>
                    <button
                      onClick={minimizeChat}
                      className="p-1 hover:bg-gray-100 rounded transition-colors"
                      title="Minimize"
                    >
                      <svg className="w-5 h-5" style={{ color: colors.neutral[600] }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                      </svg>
                    </button>
                    <button
                      onClick={closeChat}
                      className="p-1 hover:bg-red-50 rounded transition-colors"
                      title="Close"
                    >
                      <svg className="w-5 h-5" style={{ color: colors.error[600] }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Messages Area (hidden when minimized) */}
            {!isMinimized && (
              <>
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ maxHeight: '400px' }}>
                  {messages.length === 0 ? (
                    // Empty state
                    <div className="text-center py-8">
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2 }}
                        className="w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center"
                        style={{ backgroundColor: colors.primary[100] }}
                      >
                        <svg
                          className="w-6 h-6"
                          style={{ color: colors.primary[600] }}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 10h.01M12 10h.01M16 10h.01M9 20H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v12a2 2 0 01-2 2h-4l-3 3z"
                          />
                        </svg>
                      </motion.div>
                      <p className="text-sm font-medium mb-1" style={{ color: colors.neutral[900] }}>
                        Hi! I'm your AI assistant
                      </p>
                      <p className="text-xs" style={{ color: colors.neutral[500] }}>
                        Ask me to create, complete, or manage tasks!
                      </p>
                      <div className="mt-3 space-y-1 text-left">
                        {['Add task buy groceries', 'Show my tasks', 'Mark task 1 done'].map((example, i) => (
                          <button
                            key={i}
                            onClick={() => setInputValue(example)}
                            className="w-full text-left px-3 py-2 text-xs rounded-lg hover:bg-gray-50 transition-colors"
                            style={{
                              color: colors.neutral[700],
                              border: `1px solid ${colors.neutral[200]}`,
                            }}
                          >
                            "{example}"
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    // Message list
                    messages.map((message) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] px-3 py-2 rounded-lg text-sm ${
                            message.role === 'user'
                              ? 'bg-primary-500 text-white'
                              : 'bg-gray-100 text-gray-900'
                          }`}
                        >
                          {message.content}
                          {message.tool_calls && message.tool_calls.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-gray-300 text-xs">
                              {message.tool_calls.map((tool, i) => (
                                <div
                                  key={i}
                                  className={`flex items-center gap-1 ${tool.result.success ? 'text-green-600' : 'text-red-600'}`}
                                >
                                  <span className="font-medium">
                                    {tool.tool_name.replace(/_/g, ' ')}
                                  </span>
                                  <span>{tool.result.success ? '✓' : '✗'}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))
                  )}

                  {/* Typing indicator */}
                  {isLoading && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex justify-start"
                    >
                      <div className="bg-gray-100 px-4 py-2 rounded-lg">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Invisible element for auto-scroll */}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-3 border-t border-gray-200">
                  <div className="flex gap-2">
                    <textarea
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Ask me anything..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                      rows={1}
                      disabled={isLoading}
                      style={{ maxHeight: '60px' }}
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim() || isLoading}
                      className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                      style={{
                        backgroundColor: !inputValue.trim() || isLoading ? colors.neutral[300] : colors.primary[500],
                      }}
                    >
                      Send
                    </button>
                  </div>
                  <p className="text-xs text-center mt-2" style={{ color: colors.neutral[400] }}>
                    Press Enter to send, Shift+Enter for new line
                  </p>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
