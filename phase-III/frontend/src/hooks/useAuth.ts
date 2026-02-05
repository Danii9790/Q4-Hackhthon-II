/**
 * useAuth hook
 *
 * Provides authentication state and methods using Better Auth.
 * Handles session management, sign in, sign out, and authentication state.
 */

'use client'

import { useEffect, useState } from 'react'
import { authClient, type User, type Session } from '@/lib/auth'

interface AuthState {
  user: User | null
  session: Session | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
}

interface AuthReturn extends AuthState {
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, name?: string) => Promise<void>
  signOut: () => Promise<void>
  clearError: () => void
}

/**
 * Custom hook for authentication
 *
 * @returns Authentication state and methods
 */
export function useAuth(): AuthReturn {
  const [state, setState] = useState<AuthState>({
    user: null,
    session: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
  })

  /**
   * Fetch current session on mount
   */
  useEffect(() => {
    async function fetchSession() {
      try {
        const session = await authClient.getSession()

        if (session?.user) {
          setState({
            user: session.user as User,
            session: session as Session,
            isLoading: false,
            isAuthenticated: true,
            error: null,
          })
        } else {
          setState({
            user: null,
            session: null,
            isLoading: false,
            isAuthenticated: false,
            error: null,
          })
        }
      } catch (error) {
        setState({
          user: null,
          session: null,
          isLoading: false,
          isAuthenticated: false,
          error: error instanceof Error ? error.message : 'Failed to fetch session',
        })
      }
    }

    fetchSession()
  }, [])

  /**
   * Sign in with email and password
   */
  const signIn = async (email: string, password: string) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }))

    try {
      const session = await authClient.signIn.email({ email, password })

      if (session?.user) {
        setState({
          user: session.user as User,
          session: session as Session,
          isLoading: false,
          isAuthenticated: true,
          error: null,
        })
      } else {
        throw new Error('Sign in failed')
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Sign in failed'
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }))
      throw error
    }
  }

  /**
   * Sign up with email, password, and optional name
   */
  const signUp = async (email: string, password: string, name?: string) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }))

    try {
      const session = await authClient.signUp.email({ email, password, name })

      if (session?.user) {
        setState({
          user: session.user as User,
          session: session as Session,
          isLoading: false,
          isAuthenticated: true,
          error: null,
        })
      } else {
        throw new Error('Sign up failed')
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Sign up failed'
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }))
      throw error
    }
  }

  /**
   * Sign out current user
   */
  const signOut = async () => {
    setState((prev) => ({ ...prev, isLoading: true }))

    try {
      await authClient.signOut()

      setState({
        user: null,
        session: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
      })
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Sign out failed'
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }))
    }
  }

  /**
   * Clear error state
   */
  const clearError = () => {
    setState((prev) => ({ ...prev, error: null }))
  }

  return {
    ...state,
    signIn,
    signUp,
    signOut,
    clearError,
  }
}
