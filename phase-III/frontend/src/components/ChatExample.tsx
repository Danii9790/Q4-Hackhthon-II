/**
 * Chat Example Component
 *
 * Demonstrates how to use the chat service in a React component.
 * This example shows:
 * - Authentication check
 * - Sending messages
 * - Handling responses
 * - Error handling
 * - Tool call display
 */

'use client';

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { sendMessage } from '@/services';
import type { ChatResponse } from '@/services';

export function ChatExample() {
  const { user, isAuthenticated: isAuth } = useAuth();
  const [message, setMessage] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Handle message send
   */
  const handleSend = async () => {
    if (!message.trim() || !user) {
      return;
    }

    setIsLoading(true);
    setResponse(null);

    try {
      const result = await sendMessage(user.id, {
        message: message.trim(),
        conversation_id: conversationId,
      });

      // Update conversation ID for next message
      setConversationId(result.conversation_id);
      setResponse(result);
      setMessage(''); // Clear input on success

    } catch (error) {
      // Error toast is automatically shown by the service
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Show login message if not authenticated
   */
  if (!isAuth) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-gray-600">Please sign in to use the chat.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 p-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold">Todo AI Chatbot</h2>

      {/* Response Display */}
      {response && (
        <div className="p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold mb-2">Assistant:</h3>
          <p className="text-gray-800">{response.assistant_message}</p>

          {/* Tool Calls */}
          {response.tool_calls.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold text-sm text-gray-600 mb-2">
                Actions taken:
              </h4>
              <ul className="space-y-2">
                {response.tool_calls.map((tool, index) => (
                  <li key={index} className="text-sm">
                    <span className="font-mono bg-gray-200 px-2 py-1 rounded">
                      {tool.tool_name}
                    </span>
                    <pre className="mt-1 text-xs bg-gray-100 p-2 rounded">
                      {JSON.stringify(tool.arguments, null, 2)}
                    </pre>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Input Form */}
      <div className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask me to manage your tasks..."
          disabled={isLoading}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !message.trim()}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>

      {/* Conversation Info */}
      {conversationId && (
        <p className="text-xs text-gray-500">
          Conversation ID: {conversationId}
        </p>
      )}
    </div>
  );
}
