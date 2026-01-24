'use client'

/**
 * LogoutButton component for user sign out.
 *
 * This component provides a button to sign out the current user.
 * It clears the session and redirects to the home page.
 *
 * Example usage:
 * ```tsx
 * <LogoutButton />
 * ```
 */
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { auth } from '@/lib/auth';

export default function LogoutButton() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleLogout = async () => {
    setIsLoading(true);

    try {
      // Clear session using auth utilities
      await auth.signOut();

      // Redirect to home page
      router.push('/');
    } catch (error) {
      console.error('Logout failed:', error);
      // Even if logout fails, clear local session and redirect
      setIsLoading(false);
    }
  };

  return (
    <motion.button
      onClick={handleLogout}
      disabled={isLoading}
      whileHover={!isLoading ? { scale: 1.02 } : {}}
      whileTap={!isLoading ? { scale: 0.98 } : {}}
      className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isLoading ? (
        <>
          <svg
            className="w-4 h-4 animate-spin"
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
          </svg>
          Signing out...
        </>
      ) : (
        <>
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>
          Sign Out
        </>
      )}
    </motion.button>
  );
}
