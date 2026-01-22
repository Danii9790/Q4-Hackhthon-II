/**
 * MotionContainer Component
 *
 * A wrapper component that provides consistent animations to its children.
 * Supports various animation variants and respects reduced motion preferences.
 */

'use client';

import { motion, HTMLMotionProps } from 'framer-motion';
import { fadeIn, fadeInUp, getMotionProps } from '@/lib/animations';

type AnimationType = 'fadeIn' | 'fadeInUp' | 'none';

interface MotionContainerProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode;
  animationType?: AnimationType;
  delay?: number;
  className?: string;
}

const animationVariants = {
  fadeIn,
  fadeInUp,
  none: {
    hidden: {},
    visible: {},
    exit: {},
  },
};

export default function MotionContainer({
  children,
  animationType = 'fadeInUp',
  delay = 0,
  className = '',
  ...props
}: MotionContainerProps) {
  const selectedVariant = animationVariants[animationType];

  const motionProps = getMotionProps({
    initial: 'hidden',
    animate: 'visible',
    exit: 'exit',
    variants: selectedVariant,
    transition: { delay },
    className,
    ...props,
  });

  return <motion.div {...motionProps}>{children}</motion.div>;
}
