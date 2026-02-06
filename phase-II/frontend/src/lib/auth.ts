/**
 * Authentication utilities for Todo Application.
 *
 * This module provides authentication functions that integrate with the FastAPI backend
 * while using Better Auth for session management on the frontend.
 *
 * Flow:
 * 1. User signs in/up via FastAPI endpoints
 * 2. FastAPI returns JWT token
 * 3. Better Auth stores session data including JWT token
 * 4. JWT token is attached to all API requests
 */
import axios, { AxiosError } from 'axios';
import { AUTH_ENDPOINTS, SESSION_KEYS } from './auth.config';

/**
 * Get the backend API URL from environment variables.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Authentication response from FastAPI backend.
 */
interface AuthResponse {
  token: string;
  user: {
    id: string;
    email: string;
    name?: string;
    created_at: string;
  };
}

/**
 * Authentication error structure.
 */
interface AuthError {
  response?: {
    data?: {
      detail?: {
        message?: string;
        code?: string;
      };
    };
    status?: number;
  };
}

/**
 * Save session data to localStorage and cookie.
 *
 * This stores both the JWT token and user data for use by the API client.
 * The token is also stored as a cookie for Next.js middleware to access.
 *
 * @param token - JWT bearer token from FastAPI
 * @param user - User object with id, email, name
 */
function saveSession(token: string, user: AuthResponse['user']): void {
  if (typeof window === 'undefined') return;

  // Store JWT token for API requests
  localStorage.setItem(SESSION_KEYS.TOKEN, token);

  // Store user data for app usage
  localStorage.setItem(SESSION_KEYS.USER, JSON.stringify(user));

  // Also store token as cookie for Next.js middleware access
  // Set with appropriate security flags
  document.cookie = `${SESSION_KEYS.TOKEN}=${token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
}

/**
 * Clear session data from localStorage and cookies.
 *
 * This is called on sign out or when token expires.
 */
function clearSession(): void {
  if (typeof window === 'undefined') return;

  localStorage.removeItem(SESSION_KEYS.TOKEN);
  localStorage.removeItem(SESSION_KEYS.USER);

  // Also clear the cookie
  document.cookie = `${SESSION_KEYS.TOKEN}=; path=/; max-age=0; SameSite=Lax`;
}

/**
 * Get the current JWT token from localStorage.
 *
 * @returns JWT token or null if not authenticated
 */

/**
 * Export clearSession for use in API client
 */
export { clearSession };
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(SESSION_KEYS.TOKEN);
}

/**
 * Get the current user data from localStorage.
 *
 * @returns User object or null if not authenticated
 */
export function getCurrentUser(): AuthResponse['user'] | null {
  if (typeof window === 'undefined') return null;

  try {
    const userData = localStorage.getItem(SESSION_KEYS.USER);
    if (!userData) return null;
    return JSON.parse(userData);
  } catch (error) {
    console.error('Failed to parse user data from localStorage:', error);
    return null;
  }
}

/**
 * Check if user is authenticated.
 *
 * @returns true if user has valid session
 */
export function isAuthenticated(): boolean {
  const token = getAuthToken();
  const user = getCurrentUser();
  return !!(token && user);
}

/**
 * Sign in with email and password.
 *
 * Calls FastAPI signin endpoint and stores JWT token in session.
 *
 * @param email - User email address
 * @param password - User password
 * @returns User object if successful
 * @throws Error with message from backend if authentication fails
 */
export async function signIn(email: string, password: string): Promise<AuthResponse['user']> {
  try {
    const response = await axios.post<AuthResponse>(AUTH_ENDPOINTS.signin, {
      email,
      password,
    });

    const { token, user } = response.data;
    saveSession(token, user);

    return user;
  } catch (error) {
    const authError = error as AuthError;

    // Extract error message from backend response
    const message = authError.response?.data?.detail?.message || 'Invalid email or password';

    throw new Error(message);
  }
}

/**
 * Sign up a new user with email and password.
 *
 * Calls FastAPI signup endpoint and stores JWT token in session.
 *
 * @param email - User email address
 * @param password - User password (min 8 characters)
 * @param name - Optional display name
 * @returns User object if successful
 * @throws Error with message from backend if signup fails
 */
export async function signUp(
  email: string,
  password: string,
  name?: string
): Promise<AuthResponse['user']> {
  try {
    const response = await axios.post<AuthResponse>(AUTH_ENDPOINTS.signup, {
      email,
      password,
      name: name || undefined,
    });

    const { token, user } = response.data;
    saveSession(token, user);

    return user;
  } catch (error) {
    const authError = error as AuthError;

    // Extract error message from backend response
    const message = authError.response?.data?.detail?.message || 'Failed to create account';

    throw new Error(message);
  }
}

/**
 * Sign out the current user and clear session.
 *
 * This clears the local session. If the backend has a signout endpoint,
 * it should be called here to invalidate the token server-side.
 */
export async function signOut(): Promise<void> {
  // Clear local session
  clearSession();

  // If backend has a signout endpoint, call it:
  // try {
  //   await axios.post(AUTH_ENDPOINTS.signout);
  // } catch (error) {
  //   console.error('Signout request failed:', error);
  // }
}

/**
 * Request a password reset email.
 *
 * Calls FastAPI forgot-password endpoint to generate a reset token.
 * In production, this would send an email with the reset link.
 *
 * @param email - User email address
 * @returns Reset link (for development only)
 * @throws Error with message from backend if request fails
 */
export async function forgotPassword(email: string): Promise<string> {
  try {
    const response = await axios.post<{ reset_link: string }>(AUTH_ENDPOINTS.forgotPassword, {
      email,
    });

    return response.data.reset_link;
  } catch (error) {
    const authError = error as AuthError;

    // Extract error message from backend response
    const message = authError.response?.data?.detail?.message || 'Failed to request password reset';

    throw new Error(message);
  }
}

/**
 * Reset password with a token.
 *
 * Calls FastAPI reset-password endpoint to update the password.
 *
 * @param token - Password reset token from email
 * @param newPassword - New password (min 8 characters)
 * @throws Error with message from backend if reset fails
 */
export async function resetPassword(token: string, newPassword: string): Promise<void> {
  try {
    await axios.post(AUTH_ENDPOINTS.resetPassword, {
      token,
      new_password: newPassword,
    });
  } catch (error) {
    const authError = error as AuthError;

    // Extract error message from backend response
    const message = authError.response?.data?.detail?.message || 'Failed to reset password';

    throw new Error(message);
  }
}

/**
 * React hook to access authentication state.
 *
 * This hook provides the current user data and authentication status.
 * It can be used in components to conditionally render content based on auth state.
 *
 * @returns Object with user, loading state, and helper functions
 */
export function useAuth() {
  // For SSR safety, check if we're on the client
  const user = typeof window !== 'undefined' ? getCurrentUser() : null;
  const authenticated = isAuthenticated();

  return {
    user,
    isAuthenticated: authenticated,
    isLoading: false, // Since we read from localStorage, it's synchronous
    signIn,
    signUp,
    signOut,
    forgotPassword,
    resetPassword,
  };
}

/**
 * Export authentication utilities.
 */
export const auth = {
  signIn,
  signUp,
  signOut,
  forgotPassword,
  resetPassword,
  getSession: getCurrentUser,
  useAuth,
  isAuthenticated,
  getAuthToken,
  getCurrentUser,
};

export default auth;
