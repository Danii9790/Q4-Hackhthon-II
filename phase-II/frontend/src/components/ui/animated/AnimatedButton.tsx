/**
 * AnimatedButton Component
 *
 * A modern button component with smooth animations and multiple variants.
 * Supports loading state, different sizes, and visual styles.
 */

'use client';

import { motion, HTMLMotionProps } from 'framer-motion';
import { buttonHover, buttonTap } from '@/lib/animations';
import { ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
type ButtonSize = 'sm' | 'md' | 'lg';

interface AnimatedButtonProps extends Omit<HTMLMotionProps<'button'>, 'variants'> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
  className?: string;
}

const variantStyles = {
  primary: `
    bg-gradient-to-r from-primary-500 to-primary-600
    text-white
    hover:from-primary-600 hover:to-primary-700
    shadow-md hover:shadow-lg
    border border-transparent
  `,
  secondary: `
    bg-gradient-to-r from-secondary-500 to-secondary-600
    text-white
    hover:from-secondary-600 hover:to-secondary-700
    shadow-md hover:shadow-lg
    border border-transparent
  `,
  ghost: `
    bg-transparent
    text-primary-600
    hover:bg-primary-50
    border border-primary-200
  `,
  danger: `
    bg-gradient-to-r from-error-500 to-error-600
    text-white
    hover:from-error-600 hover:to-error-700
    shadow-md hover:shadow-lg
    border border-transparent
  `,
  success: `
    bg-gradient-to-r from-success-500 to-success-600
    text-white
    hover:from-success-600 hover:to-success-700
    shadow-md hover:shadow-lg
    border border-transparent
  `,
};

const sizeStyles = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-2.5 text-base',
  lg: 'px-8 py-3 text-lg',
};

export default function AnimatedButton({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  className = '',
  disabled,
  ...props
}: AnimatedButtonProps) {
  return (
    <motion.button
      whileHover={!loading && !disabled ? buttonHover : undefined}
      whileTap={!loading && !disabled ? buttonTap : undefined}
      transition={{ duration: 0.2 }}
      disabled={loading || disabled}
      className={`
        inline-flex items-center justify-center gap-2
        font-medium rounded-xl
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-all duration-200
        ${fullWidth ? 'w-full' : ''}
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
      {...props}
    >
      {loading && (
        <motion.svg
          className="w-5 h-5"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </motion.svg>
      )}
      {children}
    </motion.button>
  );
}
