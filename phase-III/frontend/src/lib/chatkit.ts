/**
 * ChatKit Configuration for Todo AI Chatbot
 *
 * This module configures the OpenAI ChatKit library with:
 * - REST adapter pointing to the FastAPI backend
 * - Domain allowlist for task management tools only
 * - Comprehensive error handling and retry logic
 *
 * @module chatkit
 */

import { ChatKit, RESTAdapter } from '@openai/chatkit';

/**
 * Environment configuration for API endpoints
 */
const API_URL = import.meta.env.VITE_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Chat endpoint path relative to API_URL
 */
const CHAT_ENDPOINT = '/api';

/**
 * Timeout configuration for API requests (in milliseconds)
 */
const REQUEST_TIMEOUT = 30000; // 30 seconds

/**
 * Maximum number of retry attempts for failed requests
 */
const MAX_RETRIES = 3;

/**
 * Base delay between retry attempts (in milliseconds)
 * Uses exponential backoff: delay * 2^attempt
 */
const RETRY_BASE_DELAY = 1000; // 1 second

/**
 * Domain allowlist for security
 * Only task management tools are permitted in the AI agent
 */
const ALLOWED_TOOLS = [
  'add_task',
  'list_tasks',
  'complete_task',
  'update_task',
  'delete_task',
] as const;

/**
 * Error types for better error handling
 */
export enum ChatKitErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  API_ERROR = 'API_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

/**
 * Custom error class for ChatKit-specific errors
 */
export class ChatKitError extends Error {
  constructor(
    public type: ChatKitErrorType,
    message: string,
    public originalError?: unknown,
    public statusCode?: number
  ) {
    super(message);
    this.name = 'ChatKitError';
  }
}

/**
 * Delay utility for retry logic
 * @param ms - Milliseconds to delay
 */
const delay = (ms: number): Promise<void> =>
  new Promise(resolve => setTimeout(resolve, ms));

/**
 * Validate tool name against domain allowlist
 * @param toolName - Name of the tool to validate
 * @returns true if tool is allowed, false otherwise
 */
function isToolAllowed(toolName: string): boolean {
  return ALLOWED_TOOLS.includes(toolName as typeof ALLOWED_TOOLS[number]);
}

/**
 * Enhanced fetch wrapper with timeout, retry logic, and error handling
 * @param url - Request URL
 * @param options - Fetch options
 * @param retries - Current retry attempt
 * @returns Fetch response
 */
async function enhancedFetch(
  url: string,
  options: RequestInit,
  retries = 0
): Promise<Response> {
  try {
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    // Add abort signal to fetch options
    const fetchOptions: RequestInit = {
      ...options,
      signal: controller.signal,
    };

    const response = await fetch(url, fetchOptions);
    clearTimeout(timeoutId);

    // Handle non-OK responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      throw new ChatKitError(
        ChatKitErrorType.API_ERROR,
        errorData.detail || errorData.message || `API error: ${response.statusText}`,
        errorData,
        response.status
      );
    }

    return response;
  } catch (error) {
    // Handle abort/timeout
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ChatKitError(
        ChatKitErrorType.TIMEOUT_ERROR,
        `Request timeout after ${REQUEST_TIMEOUT}ms`,
        error
      );
    }

    // Handle already-wrapped ChatKitErrors
    if (error instanceof ChatKitError) {
      throw error;
    }

    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      if (retries < MAX_RETRIES) {
        const delayTime = RETRY_BASE_DELAY * Math.pow(2, retries);
        console.warn(`Network error, retrying in ${delayTime}ms (attempt ${retries + 1}/${MAX_RETRIES})`);
        await delay(delayTime);
        return enhancedFetch(url, options, retries + 1);
      }

      throw new ChatKitError(
        ChatKitErrorType.NETWORK_ERROR,
        'Network error: Failed to connect to API server',
        error
      );
    }

    // Unknown errors
    throw new ChatKitError(
      ChatKitErrorType.UNKNOWN_ERROR,
      `Unknown error: ${error instanceof Error ? error.message : String(error)}`,
      error
    );
  }
}

/**
 * Domain-restricted REST Adapter with enhanced error handling
 *
 * Wraps the standard ChatKit REST adapter to:
 * - Validate tool names against allowlist
 * - Add timeout and retry logic
 * - Provide consistent error handling
 */
class DomainRestrictedRESTAdapter extends RESTAdapter {
  private baseUrl: string;

  constructor(baseUrl: string) {
    super();
    this.baseUrl = baseUrl;
  }

  /**
   * Send chat request to backend API
   * @param userId - User ID for routing
   * @param messages - Conversation messages
   * @param options - Additional options
   * @returns API response
   */
  async chat(
    userId: string,
    messages: Array<{ role: string; content: string }>,
    options?: Record<string, unknown>
  ): Promise<unknown> {
    // Validate userId
    if (!userId || typeof userId !== 'string') {
      throw new ChatKitError(
        ChatKitErrorType.VALIDATION_ERROR,
        'Invalid userId: must be a non-empty string'
      );
    }

    // Validate messages
    if (!Array.isArray(messages) || messages.length === 0) {
      throw new ChatKitError(
        ChatKitErrorType.VALIDATION_ERROR,
        'Invalid messages: must be a non-empty array'
      );
    }

    // Validate each message
    for (const msg of messages) {
      if (!msg.role || !msg.content) {
        throw new ChatKitError(
          ChatKitErrorType.VALIDATION_ERROR,
          'Invalid message: each message must have role and content'
        );
      }
    }

    // Construct URL
    const url = `${this.baseUrl}${CHAT_ENDPOINT}/${encodeURIComponent(userId)}/chat`;

    try {
      const response = await enhancedFetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages,
          ...options,
        }),
      });

      return await response.json();
    } catch (error) {
      // Re-throw ChatKitErrors as-is
      if (error instanceof ChatKitError) {
        throw error;
      }

      // Wrap other errors
      throw new ChatKitError(
        ChatKitErrorType.UNKNOWN_ERROR,
        `Failed to send chat request: ${error instanceof Error ? error.message : String(error)}`,
        error
      );
    }
  }

  /**
   * Validate tool calls against domain allowlist
   * @param toolName - Name of the tool being called
   * @returns true if tool is allowed
   */
  validateToolCall(toolName: string): boolean {
    const allowed = isToolAllowed(toolName);

    if (!allowed) {
      console.warn(`Tool "${toolName}" is not in the allowlist and will be blocked`);
    }

    return allowed;
  }
}

/**
 * Configure and create ChatKit instance
 *
 * Creates a singleton ChatKit instance configured for the Todo AI Chatbot:
 * - Uses REST adapter pointing to FastAPI backend
 * - Domain-restricted to task management tools
 * - Enhanced error handling with timeouts and retries
 *
 * @example
 * ```ts
 * import { chatKit } from '@/lib/chatkit';
 *
 * const response = await chatKit.chat(userId, messages);
 * ```
 */
const adapter = new DomainRestrictedRESTAdapter(API_URL);

export const chatKit = new ChatKit({
  adapter,

  // Domain restrictions
  domain: {
    name: 'task_management',
    description: 'Todo and task management operations',
    allowedTools: ALLOWED_TOOLS,
    validateToolCall: (toolName: string) => adapter.validateToolCall(toolName),
  },

  // Error handling
  errorHandler: (error: unknown) => {
    if (error instanceof ChatKitError) {
      console.error(`[${error.type}] ${error.message}`, error.originalError);
      return error;
    }

    console.error('Unexpected ChatKit error:', error);
    return new ChatKitError(
      ChatKitErrorType.UNKNOWN_ERROR,
      'Unexpected error occurred',
      error
    );
  },

  // Request configuration
  config: {
    timeout: REQUEST_TIMEOUT,
    retries: MAX_RETRIES,
  },
});

/**
 * Export types and utilities for external use
 */
export type { ChatKit };
export { ALLOWED_TOOLS, API_URL, CHAT_ENDPOINT };
export default chatKit;
