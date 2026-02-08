/**
 * Chat-related TypeScript interfaces and types for Todo AI Chatbot
 */

/**
 * Message role enum
 */
export type MessageRole = 'user' | 'assistant';

/**
 * Tool call information
 */
export interface ToolCall {
  tool_name: 'add_task' | 'list_tasks' | 'complete_task' | 'update_task' | 'delete_task';
  parameters: Record<string, unknown>;
  result: {
    success: boolean;
    [key: string]: unknown;
  };
  timestamp?: string;
}

/**
 * Chat message structure
 */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  tool_calls?: ToolCall[];
  created_at: string;
}

/**
 * Chat API request
 */
export interface ChatRequest {
  message: string;
}

/**
 * Chat API response
 */
export interface ChatResponse {
  response: string;
  tool_calls: ToolCall[];
}

/**
 * Conversation state
 */
export interface ConversationState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}
