/**
 * useChat hook
 *
 * Manages chat state and operations including:
 * - Sending messages
 * - Loading states
 * - Error handling
 * - Conversation management
 */

import { useState, useCallback } from 'react'
import { sendMessage, type ChatRequest } from '@/services/chat'
import type { ChatMessage } from '@/types/chat'

interface UseChatState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  conversationId: string | null
}

interface UseChatReturn extends UseChatState {
  sendMessage: (content: string) => Promise<void>
  clearError: () => void
  resetConversation: () => void
}

/**
 * Custom hook for chat functionality
 *
 * @param userId - User ID from Better Auth session
 * @param initialConversationId - Optional existing conversation ID
 * @returns Chat state and operations
 */
export function useChat(
  userId: string,
  initialConversationId?: string
): UseChatReturn {
  const [state, setState] = useState<UseChatState>({
    messages: [],
    isLoading: false,
    error: null,
    conversationId: initialConversationId || null,
  })

  /**
   * Send a message to the chat API
   */
  const handleSendMessage = useCallback(
    async (content: string) => {
      // Clear previous errors
      setState((prev) => ({ ...prev, error: null }))

      // Validate input
      if (!content.trim()) {
        setState((prev) => ({
          ...prev,
          error: 'Message cannot be empty',
        }))
        return
      }

      // Add user message immediately for optimistic UI
      const userMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: content.trim(),
        timestamp: new Date().toISOString(),
      }

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: true,
      }))

      try {
        // Prepare request
        const request: ChatRequest = {
          userId,
          message: content.trim(),
          conversationId: state.conversationId,
        }

        // Send to API
        const response = await sendMessage(request)

        // Update state with assistant message
        setState((prev) => ({
          ...prev,
          messages: [...prev.messages, response.message],
          conversationId: response.conversationId,
          isLoading: false,
        }))
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : 'Failed to send message'

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
        }))
      }
    },
    [userId, state.conversationId]
  )

  /**
   * Clear the current error state
   */
  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }))
  }, [])

  /**
   * Reset conversation and start fresh
   */
  const resetConversation = useCallback(async () => {
    setState((prev) => ({
      ...prev,
      messages: [],
      conversationId: null,
      error: null,
    }))
  }, [])

  return {
    ...state,
    sendMessage: handleSendMessage,
    clearError,
    resetConversation,
  }
}
