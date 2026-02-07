'use client'

/**
 * TypingIndicator component for chat interface.
 *
 * This component displays an animated indicator showing that the AI
 * is processing a message or generating a response.
 *
 * Features:
 * - Animated bouncing dots
 * - "AI is thinking..." text
 * - Smooth fade-in/out animations
 * - Accessible for screen readers
 */
import { motion } from 'framer-motion'
import { colors } from '@/styles/tokens'
import { fadeIn, loadingPulse } from '@/lib/animations'

interface TypingIndicatorProps {
  /**
   * Optional custom text to display
   * @default "AI is thinking..."
   */
  text?: string
}

/**
 * TypingIndicator component.
 *
 * Shows an animated loading indicator during AI response generation.
 */
export default function TypingIndicator({ text = 'AI is thinking...' }: TypingIndicatorProps) {
  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      exit="exit"
      className="flex items-center gap-3 px-4 py-3"
      role="status"
      aria-live="polite"
      aria-label="AI is typing a response"
    >
      {/* Animated dots */}
      <div className="flex items-center gap-1.5">
        {[0, 1, 2].map((index) => (
          <motion.div
            key={index}
            className="w-2 h-2 rounded-full"
            style={{
              backgroundColor: colors.primary[500],
            }}
            animate={{
              y: [0, -8, 0],
            }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: index * 0.15,
            }}
          />
        ))}
      </div>

      {/* Animated text */}
      <motion.span
        className="text-sm font-medium"
        style={{ color: colors.neutral[600] }}
        animate={loadingPulse}
        transition={{
          duration: 1.5,
          repeat: Infinity,
        }}
      >
        {text}
      </motion.span>
    </motion.div>
  )
}
