/**
 * Animation utilities and variants for Framer Motion
 *
 * This file provides reusable animation configurations for consistent
 * motion design across the application.
 */

import { Variants, Transition } from 'framer-motion';

// ============================================================================
// FADE ANIMATIONS
// ============================================================================

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
  exit: { opacity: 0 },
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
  exit: {
    opacity: 0,
    y: 20,
    transition: { duration: 0.3, ease: 'easeIn' },
  },
};

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: { duration: 0.3, ease: 'easeIn' },
  },
};

// ============================================================================
// SLIDE ANIMATIONS
// ============================================================================

export const slideInLeft: Variants = {
  hidden: { x: -50, opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
  exit: {
    x: -50,
    opacity: 0,
    transition: { duration: 0.3, ease: 'easeIn' },
  },
};

export const slideInRight: Variants = {
  hidden: { x: 50, opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
  exit: {
    x: 50,
    opacity: 0,
    transition: { duration: 0.3, ease: 'easeIn' },
  },
};

export const slideInUp: Variants = {
  hidden: { y: 100, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] },
  },
  exit: {
    y: 100,
    opacity: 0,
    transition: { duration: 0.4, ease: 'easeIn' },
  },
};

// ============================================================================
// SCALE ANIMATIONS
// ============================================================================

export const scaleIn: Variants = {
  hidden: { scale: 0.9, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      duration: 0.4,
      ease: [0.25, 0.46, 0.45, 0.94],
    },
  },
  exit: {
    scale: 0.9,
    opacity: 0,
    transition: { duration: 0.3, ease: 'easeIn' },
  },
};

export const scaleInBounce: Variants = {
  hidden: { scale: 0 },
  visible: {
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 20,
    },
  },
  exit: {
    scale: 0,
    transition: { duration: 0.2 },
  },
};

// ============================================================================
// STAGGER ANIMATIONS (for lists)
// ============================================================================

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1,
    },
  },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: 'easeOut' },
  },
  exit: {
    opacity: 0,
    y: 20,
    transition: { duration: 0.3, ease: 'easeIn' },
  },
};

// ============================================================================
// MODAL ANIMATIONS
// ============================================================================

export const modalOverlay: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.3 },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.2 },
  },
};

export const modalContent: Variants = {
  hidden: {
    scale: 0.95,
    opacity: 0,
    y: 20,
  },
  visible: {
    scale: 1,
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.25, 0.46, 0.45, 0.94],
    },
  },
  exit: {
    scale: 0.95,
    opacity: 0,
    y: 20,
    transition: { duration: 0.2 },
  },
};

// ============================================================================
// CARD HOVER EFFECTS
// ============================================================================

export const cardHover = {
  scale: 1.02,
  transition: { duration: 0.2, ease: 'easeInOut' },
};

export const cardTap = {
  scale: 0.98,
  transition: { duration: 0.1 },
};

// ============================================================================
// PAGE TRANSITIONS
// ============================================================================

export const pageTransition: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.25, 0.46, 0.45, 0.94],
    },
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: { duration: 0.3 },
  },
};

// ============================================================================
// BUTTON ANIMATIONS
// ============================================================================

export const buttonHover = {
  scale: 1.05,
  transition: { duration: 0.2 },
};

export const buttonTap = {
  scale: 0.95,
  transition: { duration: 0.1 },
};

// ============================================================================
// LOADING STATES
// ============================================================================

export const loadingPulse = {
  scale: [1, 1.05, 1],
  opacity: [1, 0.7, 1],
};

export const shimmer = {
  backgroundPosition: ['200% 0', '-200% 0'],
  transition: {
    duration: 1.5,
    repeat: Infinity,
    ease: 'linear',
  },
};

// ============================================================================
// ACCESSIBILITY
// ============================================================================

// Respect reduced motion preference
export const getMotionProps = (props: {
  variants?: Variants;
  transition?: Transition;
  [key: string]: unknown;
}) => {
  if (typeof window !== 'undefined') {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      return {
        ...props,
        transition: { duration: 0.01 },
      };
    }
  }
  return props;
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Create stagger variants for list items
 */
export const createStaggerVariants = (
  itemCount: number,
  baseDelay: number = 0
): Variants[] => {
  return Array.from({ length: itemCount }, (_, i) => ({
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        delay: baseDelay + i * 0.05,
        duration: 0.4,
        ease: 'easeOut',
      },
    },
  }));
};

/**
 * Spring transition configuration
 */
export const springTransition: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 30,
};

/**
 * Gentle transition configuration
 */
export const gentleTransition: Transition = {
  duration: 0.4,
  ease: [0.25, 0.46, 0.45, 0.94],
};
