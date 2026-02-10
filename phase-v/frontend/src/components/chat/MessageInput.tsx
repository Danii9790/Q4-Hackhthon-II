'use client'

/**
 * MessageInput component for chat interface.
 *
 * This component provides the input field and send button for users
 * to submit messages to the AI assistant.
 *
 * Features:
 * - Text input with auto-resize textarea
 * - Send button with keyboard shortcut (Enter)
 * - Disabled state during loading
 * - Character limit indicator
 * - Focus management
 * - Accessibility support
 */
import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { motion } from 'framer-motion'
import { colors, borderRadius, shadows, gradients } from '@/styles/tokens'
import { buttonHover, buttonTap } from '@/lib/animations'

interface MessageInputProps {
  /**
   * Callback when message is submitted
   * @param message - The message text to send
   */
  onSendMessage: (message: string) => void

  /**
   * Whether the input should be disabled (during AI response)
   * @default false
   */
  disabled?: boolean

  /**
   * Maximum character length for messages
   * @default 2000
   */
  maxLength?: number

  /**
   * Placeholder text for the input field
   * @default "Ask me anything about your tasks..."
   */
  placeholder?: string
}

const MAX_HEIGHT = 200 // Maximum height in pixels before scrolling

/**
 * MessageInput component.
 *
 * Handles message input with auto-resize and keyboard interactions.
 */
export default function MessageInput({
  onSendMessage,
  disabled = false,
  maxLength = 2000,
  placeholder = 'Ask me anything about your tasks...',
}: MessageInputProps) {
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  /**
   * Auto-resize textarea based on content.
   */
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto'

    // Calculate new height, capped at MAX_HEIGHT
    const newHeight = Math.min(textarea.scrollHeight, MAX_HEIGHT)
    textarea.style.height = `${newHeight}px`
  }, [message])

  /**
   * Handle sending the message with deduplication.
   */
  const handleSend = () => {
    const trimmedMessage = message.trim()
    if (!trimmedMessage || disabled || isSubmitting) return

    setIsSubmitting(true)
    onSendMessage(trimmedMessage)
    setMessage('')

    // Reset submitting state after a short delay to prevent double-submits
    setTimeout(() => {
      setIsSubmitting(false)
    }, 500)

    // Reset textarea height after clearing
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    // Refocus the textarea for the next message
    setTimeout(() => {
      textareaRef.current?.focus()
    }, 100)
  }

  /**
   * Handle keyboard shortcuts.
   * - Enter: Send message
   * - Shift+Enter: Insert newline
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const characterCount = message.length
  const isNearLimit = characterCount > maxLength * 0.9
  const isAtLimit = characterCount >= maxLength
  const canSend = message.trim().length > 0 && !disabled && !isSubmitting && !isAtLimit

  return (
    <div className="border-t-2 bg-white p-4 sm:p-6" style={{ borderColor: colors.neutral[200] }}>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-end gap-3">
          {/* Text input field */}
          <div className="flex-1 relative">
            <motion.textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              placeholder={placeholder}
              rows={1}
              maxLength={maxLength}
              className="w-full px-4 py-3 pr-16 resize-none overflow-y-auto border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                borderColor: disabled ? colors.neutral[300] : colors.primary[300],
                backgroundColor: disabled ? colors.neutral[50] : colors.white,
                borderRadius: borderRadius.xl,
                color: colors.neutral[900],
                fontSize: '0.9375rem', // 15px
                lineHeight: '1.5',
                maxHeight: `${MAX_HEIGHT}px`,
              }}
              whileFocus={{
                borderColor: colors.primary[500],
                boxShadow: `0 0 0 3px ${colors.primary[100]}`,
              }}
              aria-label="Type your message"
              aria-describedby="message-character-count"
            />

            {/* Character count indicator */}
            <div
              id="message-character-count"
              className="absolute bottom-3 right-3 text-xs font-medium transition-colors"
              style={{
                color: isAtLimit ? colors.error[600] : isNearLimit ? colors.warning[600] : colors.neutral[400],
              }}
            >
              {characterCount} / {maxLength}
            </div>
          </div>

          {/* Send button */}
          <motion.button
            onClick={handleSend}
            disabled={!canSend}
            whileHover={canSend ? buttonHover : {}}
            whileTap={canSend ? buttonTap : {}}
            className="flex-shrink-0 p-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            style={{
              background: canSend ? gradients?.primary || colors.primary[500] : colors.neutral[300],
              boxShadow: canSend ? shadows['primary-md'] : 'none',
            }}
            aria-label="Send message"
            title={disabled ? 'Please wait for response' : 'Send message (Enter)'}
          >
            <svg
              className="w-6 h-6"
              style={{ color: canSend ? colors.white : colors.neutral[500] }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </motion.button>
        </div>

        {/* Help text */}
        <p className="mt-2 text-xs text-center" style={{ color: colors.neutral[500] }}>
          Press <kbd className="px-1.5 py-0.5 rounded font-mono text-xs" style={{
            backgroundColor: colors.neutral[100],
            color: colors.neutral[700],
          }}>Enter</kbd> to send, <kbd className="px-1.5 py-0.5 rounded font-mono text-xs ml-1" style={{
            backgroundColor: colors.neutral[100],
            color: colors.neutral[700],
          }}>Shift + Enter</kbd> for new line
        </p>
      </div>
    </div>
  )
}
