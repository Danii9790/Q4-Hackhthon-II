/**
 * AnimatedCard Component
 *
 * A modern card component with smooth hover effects and entrance animations.
 * Perfect for displaying tasks, features, or any content cards.
 */

'use client';

import { motion, HTMLMotionProps } from 'framer-motion';
import { scaleIn, cardHover, cardTap } from '@/lib/animations';
import { getMotionProps } from '@/lib/animations';
import { ReactNode } from 'react';

interface AnimatedCardProps extends HTMLMotionProps<'div'> {
  children: ReactNode;
  hover?: boolean;
  className?: string;
  delay?: number;
}

export default function AnimatedCard({
  children,
  hover = true,
  className = '',
  delay = 0,
  ...props
}: AnimatedCardProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      whileHover={hover ? 'hover' : undefined}
      whileTap={hover ? 'tap' : undefined}
      variants={{
        hidden: { scale: 0.9, opacity: 0 },
        visible: {
          scale: 1,
          opacity: 1,
          transition: {
            duration: 0.4,
            ease: [0.25, 0.46, 0.45, 0.94],
            delay,
          },
        },
        hover: {
          scale: 1.02,
          transition: { duration: 0.2, ease: 'easeInOut' as const },
        },
        tap: {
          scale: 0.98,
          transition: { duration: 0.1 },
        },
      }}
      className={`
        bg-white rounded-xl shadow-sm border border-gray-100
        hover:shadow-lg hover:border-primary-200
        ${hover ? 'cursor-pointer' : ''}
        ${className}
      `}
      {...props}
    >
      {children}
    </motion.div>
  );
}
