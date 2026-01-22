/**
 * SkeletonLoader Component
 *
 * Provides animated skeleton loading states for better UX during data fetching.
 * Uses shimmer animation from the animation utilities.
 */

import { motion } from 'framer-motion'
import { shimmer } from '@/lib/animations'
import { colors } from '@/styles/tokens'

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string | number
  height?: string | number
}

/**
 * Individual skeleton element
 */
export function Skeleton({
  className = '',
  variant = 'text',
  width,
  height,
}: SkeletonProps) {
  const baseClasses = 'rounded-lg animate-pulse'
  const variantClasses = {
    text: 'h-4 rounded-md',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  }

  const style = {
    width: width || (variant === 'text' ? '100%' : '40px'),
    height: height || (variant === 'text' ? '1rem' : '40px'),
    backgroundColor: colors.neutral[200],
  }

  return (
    <motion.div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
      animate={{
        backgroundPosition: ['200% 0', '-200% 0'],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: 'linear' as const,
      }}
    />
  )
}

/**
 * Task skeleton item - mimics the TaskItem component
 */
export function TaskSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 space-y-4">
      <div className="flex items-start gap-4">
        {/* Checkbox skeleton */}
        <Skeleton variant="rectangular" width={24} height={24} />

        {/* Content skeleton */}
        <div className="flex-1 space-y-3">
          {/* Title skeleton */}
          <Skeleton width="70%" height={20} />

          {/* Description skeleton */}
          <div className="space-y-2">
            <Skeleton width="100%" />
            <Skeleton width="80%" />
          </div>

          {/* Tags/Status skeleton */}
          <div className="flex items-center gap-2">
            <Skeleton width={60} height={24} className="rounded-full" />
            <Skeleton width={80} height={24} className="rounded-full" />
          </div>
        </div>

        {/* Action buttons skeleton */}
        <div className="flex items-center gap-2">
          <Skeleton variant="circular" width={36} height={36} />
          <Skeleton variant="circular" width={36} height={36} />
          <Skeleton variant="circular" width={36} height={36} />
        </div>
      </div>
    </div>
  )
}

/**
 * Form skeleton - mimics the CreateTaskForm component
 */
export function FormSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 space-y-5">
      <div className="space-y-2">
        <Skeleton width={120} height={24} />
        <Skeleton width="60%" height={16} />
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Skeleton width={80} height={16} />
          <Skeleton height={48} className="rounded-lg" />
        </div>

        <div className="space-y-2">
          <Skeleton width={100} height={16} />
          <Skeleton height={120} className="rounded-lg" />
        </div>

        <div className="space-y-2">
          <Skeleton width={90} height={16} />
          <Skeleton height={48} className="rounded-lg" />
        </div>

        <Skeleton width={150} height={48} className="rounded-lg mt-4" />
      </div>
    </div>
  )
}

/**
 * Loading spinner with modern design
 */
export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-5 h-5',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  return (
    <div className="relative inline-flex items-center justify-center">
      <motion.div
        className={`${sizeClasses[size]} border-4 border-indigo-200 rounded-full`}
        style={{ borderTopColor: colors.primary[500] }}
        animate={{ rotate: 360 }}
        transition={{
          duration: 1,
          repeat: Infinity,
          ease: 'linear',
        }}
      />
    </div>
  )
}

/**
 * Full page loader
 */
export function FullPageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="text-center space-y-6">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          <LoadingSpinner size="lg" />
        </motion.div>
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-gray-600 font-medium text-lg"
        >
          Loading...
        </motion.p>
      </div>
    </div>
  )
}

/**
 * Skeleton list for multiple items
 */
export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, index) => (
        <TaskSkeleton key={index} />
      ))}
    </div>
  )
}

export default Skeleton
