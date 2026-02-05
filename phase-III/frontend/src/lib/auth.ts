import { createAuthClient } from 'better-auth/react'

const authUrl = process.env.NEXT_PUBLIC_BETTER_AUTH_URL || 'http://localhost:3000'

/**
 * Better Auth client instance
 *
 * Provides authentication methods for signin, signup, signout, and session management.
 * Configured to work with the Better Auth backend.
 */
export const authClient = createAuthClient({
  baseURL: authUrl,
})

/**
 * Type definitions for Better Auth session
 */
export interface Session {
  user: {
    id: string
    email: string
    name?: string
  }
  expiresAt: Date
}

/**
 * Type definitions for Better Auth user
 */
export interface User {
  id: string
  email: string
  name?: string
}
