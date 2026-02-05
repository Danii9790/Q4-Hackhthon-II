/**
 * TypeScript type definitions for Todo AI Chatbot frontend.
 *
 * Provides type safety for chat components, API responses, and application state.
 * Aligned with backend Pydantic schemas in backend/src/schemas.py.
 */

/**
 * Represents a single tool call made by the AI agent.
 *
 * Corresponds to backend ToolCallDetail schema.
 */
export interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: unknown;
}

/**
 * Chat message role type.
 */
export type MessageRole = 'user' | 'assistant' | 'system';

/**
 * Represents a chat message in the conversation.
 */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  tool_calls?: ToolCall[];
}

/**
 * Response from the chat API endpoint.
 *
 * Corresponds to backend ChatResponse schema.
 */
export interface ChatResponse {
  conversation_id: string;
  assistant_message: string;
  tool_calls: ToolCall[];
  timestamp: string;
}

/**
 * Request payload for sending a chat message.
 */
export interface ChatRequest {
  message: string;
  conversation_id?: string | null;
}

/**
 * State for the chat interface.
 */
export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  conversationId: string | null;
}

/**
 * Props for ChatInterface component.
 */
export interface ChatInterfaceProps {
  apiBaseUrl?: string;
  userId?: string;
  initialConversationId?: string | null;
  onError?: (error: string) => void;
}

/**
 * Props for MessageList component.
 */
export interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
}

/**
 * Props for MessageInput component.
 */
export interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Props for TypingIndicator component.
 */
export interface TypingIndicatorProps {
  isVisible?: boolean;
  message?: string;
}
