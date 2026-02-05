/**
 * Central API client for Todo AI Chatbot frontend.
 *
 * Provides a single, consistent interface for all backend communication.
 * All API calls should route through this client - never make fetch calls directly in components.
 *
 * Features:
 * - JWT token management via Better Auth
 * - Automatic error handling with user-friendly messages
 * - Type-safe request/response handling
 * - Centralized configuration
 */

import { ChatRequest, ChatResponse, ToolCall } from '@/types/chat';

/**
 * API error class for structured error handling.
 */
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Get the JWT token from Better Auth localStorage.
 *
 * Better Auth stores tokens under specific keys in localStorage.
 * This function retrieves the session token for authenticated requests.
 *
 * @returns The JWT token or null if not found
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;

  // Better Auth uses specific localStorage keys
  const SESSION_KEY = 'better-auth.session_token';
  const token = localStorage.getItem(SESSION_KEY);

  return token;
}

/**
 * Get the base URL for API requests from environment variables.
 *
 * Falls back to relative URL if not configured (useful for same-origin deployments).
 *
 * @returns The API base URL
 */
function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    // Client-side: use environment variable or fallback
    return process.env.NEXT_PUBLIC_API_URL || '';
  }
  // Server-side: use environment variable
  return process.env.NEXT_PUBLIC_API_URL || '';
}

/**
 * Make an authenticated API request with automatic token injection.
 *
 * Handles:
 * - JWT token injection from Better Auth
 * - JSON serialization
 * - Error parsing and transformation
 * - Network error handling
 *
 * @param endpoint - API endpoint path (e.g., '/api/123e4567-e89b-12d3-a456-426614174000/chat')
 * @param options - Fetch options (method, body, etc.)
 * @returns Parsed JSON response
 * @throws ApiError with structured error information
 */
async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const token = getAuthToken();
  const url = `${baseUrl}${endpoint}`;

  // Prepare headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  // Add authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle non-JSON responses (e.g., 204 No Content)
    if (response.status === 204) {
      return undefined as T;
    }

    // Parse JSON response
    const data = await response.json();

    // Handle error responses
    if (!response.ok) {
      throw new ApiError(
        response.status,
        data.code || 'UNKNOWN_ERROR',
        data.detail || data.message || 'An unexpected error occurred'
      );
    }

    return data;

  } catch (error) {
    // Re-throw ApiError as-is
    if (error instanceof ApiError) {
      throw error;
    }

    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        0,
        'NETWORK_ERROR',
        'Unable to connect to the server. Please check your internet connection.'
      );
    }

    // Handle other errors
    throw new ApiError(
      0,
      'UNKNOWN_ERROR',
      error instanceof Error ? error.message : 'An unexpected error occurred'
    );
  }
}

/**
 * Send a chat message to the AI agent.
 *
 * Makes a POST request to the chat endpoint with the user's message
 * and optional conversation ID. Returns the AI's response with any
 * tool calls that were executed.
 *
 * @param userId - The user's UUID (from Better Auth session)
 * @param request - Chat request with message and optional conversation_id
 * @returns Chat response with assistant message and tool calls
 * @throws ApiError if the request fails
 *
 * @example
 * ```typescript
 * const response = await sendChatMessage(userUuid, {
 *   message: "Add a task to buy groceries",
 *   conversation_id: null
 * });
 * console.log(response.assistant_message);
 * ```
 */
export async function sendChatMessage(
  userId: string,
  request: ChatRequest
): Promise<ChatResponse> {
  if (!userId) {
    throw new ApiError(400, 'INVALID_USER', 'User ID is required');
  }

  if (!request.message || request.message.trim().length === 0) {
    throw new ApiError(400, 'INVALID_MESSAGE', 'Message cannot be empty');
  }

  if (request.message.length > 10000) {
    throw new ApiError(
      400,
      'MESSAGE_TOO_LONG',
      'Message cannot exceed 10,000 characters'
    );
  }

  const endpoint = `/api/${userId}/chat`;

  return fetchWithAuth<ChatResponse>(endpoint, {
    method: 'POST',
    body: JSON.stringify({
      message: request.message.trim(),
      conversation_id: request.conversation_id,
    }),
  });
}

/**
 * Convert API error codes to user-friendly messages.
 *
 * Maps backend error codes to localized, user-friendly error messages.
 * Used by components to display appropriate error feedback.
 *
 * @param error - The ApiError to translate
 * @returns User-friendly error message
 */
export function getErrorMessage(error: ApiError): string {
  // Error code to message mapping
  const errorMessages: Record<string, string> = {
    NETWORK_ERROR: 'Unable to connect to the server. Please check your internet connection.',
    UNAUTHORIZED: 'You need to sign in to perform this action.',
    FORBIDDEN: 'You do not have permission to perform this action.',
    NOT_FOUND: 'The requested resource was not found.',
    INVALID_USER: 'Invalid user ID. Please sign in again.',
    INVALID_MESSAGE: 'Please enter a valid message.',
    MESSAGE_TOO_LONG: 'Your message is too long. Please keep it under 10,000 characters.',
    AGENT_TIMEOUT: 'The assistant is taking too long to respond. Please try again.',
    RATE_LIMITED: 'You are sending messages too quickly. Please wait a moment.',
    INTERNAL_ERROR: 'Something went wrong. Please try again.',
  };

  // Return mapped message or fallback to the error's message
  return errorMessages[error.code] || error.message || 'An unexpected error occurred.';
}

/**
 * Export the API client object for convenience.
 *
 * Components can import individual functions or the entire client object.
 *
 * @example
 * ```typescript
 * import { api } from '@/services/api';
 * const response = await api.sendChatMessage(userId, request);
 * ```
 */
export const api = {
  sendChatMessage,
  getErrorMessage,
};

/**
 * Export types for use in components.
 * Note: ApiError is already exported above.
 */
export type { ChatRequest, ChatResponse, ToolCall };
