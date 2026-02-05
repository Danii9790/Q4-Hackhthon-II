/**
 * Chat Service for Todo AI Chatbot
 *
 * Handles API communication with the backend chat endpoint.
 * Provides authentication, error handling, and toast notifications.
 *
 * Tasks: T072, T073, T074
 */

import toast from 'react-hot-toast';
import { authClient } from '@/lib/auth';

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Tool call detail from the AI agent response
 */
export interface ToolCallDetail {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: unknown;
}

/**
 * Chat response from the backend API
 */
export interface ChatResponse {
  conversation_id: string;
  assistant_message: string;
  tool_calls: ToolCallDetail[];
  timestamp: string;
}

/**
 * Chat request payload
 */
export interface ChatRequest {
  message: string;
  conversation_id: string | null;
}

/**
 * Error response from the API
 */
interface ErrorResponse {
  detail: string;
}

/**
 * Custom error class for chat API errors
 */
export class ChatApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public detail: string
  ) {
    super(message);
    this.name = 'ChatApiError';
  }
}

// ============================================================================
// Configuration
// ============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const CHAT_ENDPOINT = '/api';

// ============================================================================
// Authentication Helpers
// ============================================================================

/**
 * Extract JWT token from Better Auth session
 *
 * Gets the current session and extracts the JWT token from localStorage.
 * Better Auth stores the session token in localStorage with key format:
 * - better-auth.session_token (for the main session)
 * - better-auth.user.session_token (alternative format)
 *
 * @returns JWT token or null if not authenticated
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    // Get session from Better Auth client
    const sessionData = await authClient.getSession();

    // Better Auth returns a Data or Error object
    if (!sessionData || !('data' in sessionData)) {
      return null;
    }

    const session = sessionData.data;
    if (!session || !session.user) {
      return null;
    }

    // Better Auth stores tokens in localStorage
    // Try different possible keys
    const possibleKeys = [
      'better-auth.session_token',
      'better-auth.user.session_token',
      `better-auth.session_${session.user.id}`,
    ];

    for (const key of possibleKeys) {
      const token = localStorage.getItem(key);
      if (token) {
        return token;
      }
    }

    // Alternative: try to get from the session data directly
    // @ts-ignore - Better Auth session may contain token
    if (session.token) {
      // @ts-ignore
      return session.token;
    }

    return null;
  } catch (error) {
    console.error('Error getting auth token:', error);
    return null;
  }
}

/**
 * Check if user is authenticated
 *
 * @returns true if user has valid session
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const sessionData = await authClient.getSession();

    // Better Auth returns a Data or Error object
    if (!sessionData || !('data' in sessionData)) {
      return false;
    }

    const session = sessionData.data;
    return session !== null && session.user !== null;
  } catch {
    return false;
  }
}

/**
 * Redirect to login page
 *
 * Uses Next.js router to redirect to the login page
 */
export function redirectToLogin(): void {
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Display user-friendly error toast message
 *
 * Maps HTTP status codes to user-friendly messages
 *
 * @param statusCode - HTTP status code
 * @param detail - Error detail from API
 */
export function showErrorToast(statusCode: number, detail: string): void {
  let message = 'An error occurred. Please try again.';

  switch (statusCode) {
    case 400:
      message = detail || 'Invalid request. Please check your input.';
      break;
    case 401:
      message = 'You need to sign in to continue.';
      break;
    case 403:
      message = 'You do not have permission to perform this action.';
      break;
    case 404:
      message = detail || 'The requested resource was not found.';
      break;
    case 429:
      message = 'Too many requests. Please try again in a moment.';
      break;
    case 500:
    case 502:
    case 503:
      message = detail || 'Server error. Please try again later.';
      break;
    default:
      if (detail) {
        message = detail;
      }
  }

  toast.error(message);
}

/**
 * Show network error toast
 *
 * Used when the API cannot be reached
 */
export function showNetworkErrorToast(): void {
  toast.error('Network error. Please check your connection and try again.');
}

/**
 * Show generic error toast
 *
 * @param message - Custom error message
 */
export function showGenericErrorToast(message: string): void {
  toast.error(message);
}

/**
 * Show success toast
 *
 * @param message - Success message
 */
export function showSuccessToast(message: string): void {
  toast.success(message);
}

// ============================================================================
// API Communication
// ============================================================================

/**
 * Send a chat message to the backend API
 *
 * This is the main function for sending messages to the AI agent.
 * It handles:
 * - Authentication (adds JWT token to headers)
 * - Request formatting
 * - Response parsing
 * - Error handling with toast notifications
 * - Automatic redirect to login on 401
 *
 * @param userId - User UUID from path parameter
 * @param request - Chat request with message and optional conversation_id
 * @returns Promise resolving to ChatResponse
 * @throws ChatApiError if the request fails
 *
 * @example
 * ```ts
 * const response = await sendMessage(userId, {
 *   message: "Add a task to buy groceries",
 *   conversation_id: null
 * });
 * console.log(response.assistant_message);
 * ```
 */
export async function sendMessage(
  userId: string,
  request: ChatRequest
): Promise<ChatResponse> {
  // Validate input
  if (!request.message || request.message.trim().length === 0) {
    showGenericErrorToast('Message cannot be empty');
    throw new ChatApiError('Message cannot be empty', 400, 'Empty message');
  }

  if (request.message.length > 10000) {
    showGenericErrorToast('Message is too long (max 10,000 characters)');
    throw new ChatApiError(
      'Message is too long',
      400,
      'Message exceeds maximum length'
    );
  }

  // Check authentication
  const token = await getAuthToken();
  if (!token) {
    showGenericErrorToast('You need to sign in to continue');
    redirectToLogin();
    throw new ChatApiError(
      'Not authenticated',
      401,
      'No authentication token found'
    );
  }

  try {
    // Build request URL
    const url = `${API_URL}${CHAT_ENDPOINT}/${userId}/chat`;

    // Build request headers
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    // Build request body
    const body: ChatRequest = {
      message: request.message.trim(),
      conversation_id: request.conversation_id,
    };

    // Send POST request
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    // Handle non-OK responses
    if (!response.ok) {
      const statusCode = response.status;

      // Parse error response
      let detail = 'An error occurred';
      try {
        const errorData: ErrorResponse = await response.json();
        detail = errorData.detail || detail;
      } catch {
        // If parsing fails, use status text
        detail = response.statusText || detail;
      }

      // Handle 401 Unauthorized - redirect to login
      if (statusCode === 401) {
        showErrorToast(statusCode, detail);
        redirectToLogin();
        throw new ChatApiError('Unauthorized', statusCode, detail);
      }

      // Show error toast for other status codes
      showErrorToast(statusCode, detail);
      throw new ChatApiError(
        `API request failed: ${detail}`,
        statusCode,
        detail
      );
    }

    // Parse successful response
    const data: ChatResponse = await response.json();

    // Validate response structure
    if (!data.conversation_id || !data.assistant_message) {
      throw new ChatApiError(
        'Invalid response format',
        500,
        'Response missing required fields'
      );
    }

    return data;

  } catch (error) {
    // Handle network errors
    if (error instanceof ChatApiError) {
      // Re-throw our custom errors
      throw error;
    }

    // Handle fetch/network errors
    if (error instanceof TypeError) {
      showNetworkErrorToast();
      throw new ChatApiError(
        'Network error',
        0,
        'Failed to connect to the server'
      );
    }

    // Handle unknown errors
    console.error('Unexpected error in sendMessage:', error);
    showGenericErrorToast('An unexpected error occurred');
    throw new ChatApiError(
      'Unexpected error',
      0,
      'An unexpected error occurred'
    );
  }
}

// ============================================================================
// Exports
// ============================================================================

export default {
  sendMessage,
  getAuthToken,
  isAuthenticated,
  redirectToLogin,
  showErrorToast,
  showNetworkErrorToast,
  showGenericErrorToast,
  showSuccessToast,
};
