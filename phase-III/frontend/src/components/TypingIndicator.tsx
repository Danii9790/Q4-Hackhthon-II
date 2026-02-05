/**
 * TypingIndicator Component
 *
 * Animated indicator shown while the AI agent is processing a request.
 * Provides visual feedback to users that the system is working.
 *
 * Features:
 * - Animated bouncing dots with staggered delays
 * - Accessible ARIA labels for screen readers
 * - Smooth CSS animations
 * - Customizable message text
 * - Dark mode support
 */

'use client'

import React from 'react'

export interface TypingIndicatorProps {
  /** Whether the indicator should be visible */
  isVisible?: boolean
  /** Custom message to display (defaults to "Thinking...") */
  message?: string
  /** Optional CSS class name for styling */
  className?: string
}

/**
 * TypingIndicator component
 *
 * Shows an animated "thinking" indicator when the AI is processing.
 * Hidden by default unless isVisible is true.
 *
 * @example
 * ```tsx
 * <TypingIndicator isVisible={isLoading} />
 *
 * <TypingIndicator
 *   isVisible={true}
 *   message="The assistant is typing..."
 * />
 * ```
 */
export function TypingIndicator({
  isVisible = false,
  message = 'Thinking...',
  className = '',
}: TypingIndicatorProps) {
  // Don't render anything if not visible
  if (!isVisible) {
    return null
  }

  return (
    <div
      className={`flex justify-start ${className}`}
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <div className="bg-gray-100 dark:bg-gray-800 rounded-lg rounded-bl-sm px-4 py-3">
        <div className="flex items-center gap-2">
          {/* Animated bouncing dots */}
          <div className="flex gap-1" aria-hidden="true">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
          </div>

          {/* Text label */}
          <span className="text-xs text-gray-600 dark:text-gray-400">
            {message}
          </span>
        </div>
      </div>
    </div>
  )
}
