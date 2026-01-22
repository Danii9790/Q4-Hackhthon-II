/**
 * Better Auth client configuration for Todo Application.
 *
 * This module configures the Better Auth client to handle authentication
 * using the shared JWT secret with the backend.
 */
import { createAuthClient } from 'better-auth/react';

/**
 * Get the Better Auth API URL from environment variables.
 *
 * This should be the URL where the Better Auth server is running.
 * For local development, this is typically the Next.js dev server.
 */
const BETTER_AUTH_URL = process.env.NEXT_PUBLIC_BETTER_AUTH_URL || 'http://localhost:3000';

/**
 * Better Auth client instance.
 *
 * This client provides authentication methods including:
 * - signIn: Email/password authentication
 * - signOut: Logout and clear session
 * - signUp: User registration
 * - getSession: Retrieve current session with JWT token
 * - useSession: React hook for session state
 */
export const authClient = createAuthClient({
  baseURL: BETTER_AUTH_URL,
});

/**
 * Authentication helper functions.
 */
export const auth = {
  /**
   * Sign in with email and password.
   *
   * @param email - User email address
   * @param password - User password
   * @returns Session data with JWT token
   */
  async signIn(email: string, password: string) {
    return await authClient.signIn.email({
      email,
      password,
    });
  },

  /**
   * Sign out the current user and clear session.
   */
  async signOut() {
    return await authClient.signOut();
  },

  /**
   * Sign up a new user with email and password.
   *
   * @param email - User email address
   * @param password - User password
   * @param name - Optional user display name
   * @returns Session data with JWT token
   */
  async signUp(email: string, password: string, name?: string) {
    return await authClient.signUp.email({
      email,
      password,
      name: name ?? '',
    });
  },

  /**
   * Get the current session.
   *
   * @returns Session data with JWT token, or null if not authenticated
   */
  async getSession() {
    const session = await authClient.getSession();
    return session.data;
  },

  /**
   * React hook to access session state in components.
   *
   * @returns Session data with loading state
   */
  useSession() {
    return authClient.useSession();
  },
};

/**
 * Export the auth client for direct access to Better Auth methods.
 */
export default authClient;
