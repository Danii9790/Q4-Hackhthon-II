/**
 * Chat page layout with metadata.
 *
 * This is a server component that provides metadata for the chat page.
 * The actual chat interface is rendered in the client component page.tsx.
 */
import { Metadata } from 'next'
import React from 'react'

export const metadata: Metadata = {
  title: 'AI Task Assistant | Todo App',
  description:
    'Chat with your AI assistant to manage tasks using natural language. Create, complete, update, and delete tasks with ease.',
  keywords: ['AI', 'chat', 'tasks', 'assistant', 'todo'],
}

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
