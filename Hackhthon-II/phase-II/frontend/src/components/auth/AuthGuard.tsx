'use client'

/**
 * AuthGuard component for protecting client-side routes.
 *
 * This component checks if a user is authenticated before rendering children.
 * If not authenticated, redirects to the login page.
 *
 * Use this component to wrap pages or sections that require authentication.
 *
 * Example:
 * ```tsx
 * <AuthGuard>
 *   <DashboardPage />
 * </AuthGuard>
 * ```
 */
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * AuthGuard component to protect routes.
 *
 * @param children - Content to render if authenticated
 * @param fallback - Optional content to render while checking auth
 * @returns Protected content or redirects to login
 */
export default function AuthGuard({ children, fallback }: AuthGuardProps) {
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      // Redirect to login with return URL
      const currentPath = window.location.pathname;
      router.push(`/login?redirect=${encodeURIComponent(currentPath)}`);
    }
  }, [router]);

  // Show fallback while checking authentication
  if (!isAuthenticated()) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-secondary-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Render protected content if authenticated
  return <>{children}</>;
}

/**
 * Higher-order component to wrap pages with AuthGuard.
 *
 * Example:
 * ```tsx
 * export default withAuthGuard(DashboardPage);
 * ```
 */
export function withAuthGuard<P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P> {
  return function AuthGuardedComponent(props: P) {
    return (
      <AuthGuard>
        <Component {...props} />
      </AuthGuard>
    );
  };
}
