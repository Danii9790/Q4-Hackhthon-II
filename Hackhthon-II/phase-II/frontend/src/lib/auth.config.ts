/**
 * Better Auth Configuration for Todo Application.
 *
 * This configuration sets up Better Auth to work with the FastAPI backend.
 * Better Auth handles session management on the frontend while using JWT tokens
 * issued by the FastAPI backend.
 */

import { createAuthClient } from 'better-auth/react';

/**
 * Get the Better Auth base URL from environment variables.
 *
 * For local development, this points to the Next.js dev server.
 * For production, this should be the frontend URL.
 */
const BASE_URL = process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:3000';

/**
 * Get the backend API URL from environment variables.
 *
 * This is where the FastAPI authentication endpoints are located.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Better Auth client instance.
 *
 * Configuration:
 * - baseURL: The frontend URL for session management
 * - baseURL is used for cookie storage and session APIs
 *
 * Note: Better Auth will store session data including JWT tokens
 * that are issued by the FastAPI backend.
 */
export const authClient = createAuthClient({
  baseURL: BASE_URL,
});

/**
 * Authentication endpoints on the FastAPI backend.
 *
 * These endpoints return JWT tokens that Better Auth will store
 * as part of the session data.
 */
export const AUTH_ENDPOINTS = {
  signup: `${API_URL}/api/auth/signup`,
  signin: `${API_URL}/api/auth/signin`,
  signout: `${API_URL}/api/auth/signout`,
  forgotPassword: `${API_URL}/api/auth/forgot-password`,
  resetPassword: `${API_URL}/api/auth/reset-password`,
} as const;

/**
 * Session storage keys.
 *
 * Better Auth stores session data including JWT tokens in localStorage
 * with these keys for client-side access.
 */
export const SESSION_KEYS = {
  TOKEN: 'better-auth.session_token',
  USER: 'better-auth.user_data',
} as const;
