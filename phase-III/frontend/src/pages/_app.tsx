/**
 * _app.tsx - Next.js App Wrapper
 *
 * Sets up global providers and configuration for the Next.js application.
 * Includes Better Auth provider, custom styles, and global layout.
 */

import type { AppProps } from 'next/app'
import '@/styles/globals.css'

/**
 * Custom App component with providers
 */
export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      {/* Better Auth is handled through localStorage and client-side hooks */}
      {/* No provider needed for the current Better Auth setup */}
      <Component {...pageProps} />
    </>
  )
}
