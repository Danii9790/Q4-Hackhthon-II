/**
 * Chat page for Todo AI Chatbot.
 *
 * This page provides the main chat interface where users can interact
 * with the AI assistant to manage their tasks using natural language.
 *
 * Features:
 * - Protected by authentication (AuthGuard)
 * - Full-screen chat interface
 * - Message history display
 * - Real-time AI responses
 * - Tool execution confirmation
 * - Modern, responsive design
 *
 * Route: /chat
 */
'use client'

import AuthGuard from '@/components/auth/AuthGuard'
import ChatInterface from '@/components/chat/ChatInterface'

/**
 * Chat page component.
 *
 * Renders the chat interface protected by authentication.
 */
export default function ChatPage() {
  return (
    <AuthGuard>
      <ChatInterface />
    </AuthGuard>
  )
}
