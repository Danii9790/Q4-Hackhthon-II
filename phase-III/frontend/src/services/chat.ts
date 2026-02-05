/**
 * Chat service for managing conversations and messages
 *
 * Handles all chat-related API calls including:
 * - Creating new conversations
 * - Sending messages
 * - Retrieving conversation history
 */

import { sendChatMessage } from '@/services/api'
import type {
  ChatRequest as ApiChatRequest,
  ChatResponse as ApiChatResponse,
  ChatMessage,
} from '@/types/chat'

/**
 * Extended chat request with user ID
 */
export interface ChatRequest {
  userId: string
  message: string
  conversationId?: string | null
}

/**
 * Extended chat response with formatted message
 */
export interface ChatResponse {
  conversationId: string
  message: ChatMessage
}

/**
 * Send a chat message using the centralized API client
 *
 * @param request - Chat request with userId, message, and optional conversationId
 * @returns Chat response with conversationId and assistant message
 */
export async function sendMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const apiRequest: ApiChatRequest = {
    message: request.message,
    conversation_id: request.conversationId,
  }

  const apiResponse: ApiChatResponse = await sendChatMessage(
    request.userId,
    apiRequest
  )

  // Convert API response to our internal format
  return {
    conversationId: apiResponse.conversation_id,
    message: {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: apiResponse.assistant_message,
      timestamp: apiResponse.timestamp,
      tool_calls: apiResponse.tool_calls,
    },
  }
}
