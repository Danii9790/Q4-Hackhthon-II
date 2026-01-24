/**
 * Root layout component for Todo Application.
 *
 * This layout wraps all pages in the application and provides:
 * - HTML structure with proper meta tags
 * - Font loading (Inter)
 * - Tailwind CSS integration
 * - Better Auth session provider
 * - Global error boundary for error handling
 */
import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import ErrorBoundary from '@/components/ErrorBoundary';
import { ToastProvider } from '@/components/ui/ToastContainer';

const inter = Inter({ subsets: ['latin'] });

/**
 * Application metadata.
 */
export const metadata: Metadata = {
  title: 'Todo App',
  description: 'Multi-user task management application',
};

/**
 * Viewport configuration for Next.js 15.
 */
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
};

/**
 * Root layout component.
 *
 * This component is rendered for every page in the application.
 * It provides the basic HTML structure and includes the Better Auth
 * session provider for client components.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ErrorBoundary>
          <ToastProvider>
            {/* Better Auth Session Provider will be added here in Phase 3 */}
            <div className="min-h-screen bg-gray-50">
              {children}
            </div>
          </ToastProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
