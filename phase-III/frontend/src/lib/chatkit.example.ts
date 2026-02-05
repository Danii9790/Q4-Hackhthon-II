/**
 * ChatKit Usage Examples
 *
 * This file demonstrates how to use the configured ChatKit instance
 * for the Todo AI Chatbot application.
 *
 * @example
 * Basic chat interaction
 */

import { chatKit, ChatKitError, ChatKitErrorType } from './chatkit';

/**
 * Example 1: Basic Chat Request
 *
 * Send a simple message to the AI chatbot and receive a response.
 */
export async function basicChatExample(userId: string, userMessage: string) {
  try {
    const response = await chatKit.chat(userId, [
      {
        role: 'user',
        content: userMessage,
      },
    ]);

    console.log('AI Response:', response);
    return response;
  } catch (error) {
    if (error instanceof ChatKitError) {
      console.error(`ChatKit Error [${error.type}]:`, error.message);

      // Handle specific error types
      switch (error.type) {
        case ChatKitErrorType.NETWORK_ERROR:
          console.error('Network connection failed. Please check your internet.');
          break;
        case ChatKitErrorType.TIMEOUT_ERROR:
          console.error('Request timed out. Please try again.');
          break;
        case ChatKitErrorType.API_ERROR:
          console.error(`API returned error: ${error.statusCode}`, error.originalError);
          break;
        case ChatKitErrorType.VALIDATION_ERROR:
          console.error('Invalid request:', error.message);
          break;
        default:
          console.error('Unknown error occurred');
      }
    }

    throw error;
  }
}

/**
 * Example 2: Multi-turn Conversation
 *
 * Send conversation history to maintain context across turns.
 */
export async function conversationExample(userId: string) {
  const conversationHistory = [
    {
      role: 'user' as const,
      content: 'Add a task to buy groceries',
    },
    {
      role: 'assistant' as const,
      content: 'I\'ve added the task "Buy groceries" to your list.',
    },
    {
      role: 'user' as const,
      content: 'Now add a task to call mom',
    },
  ];

  try {
    const response = await chatKit.chat(userId, conversationHistory);
    console.log('Conversation Response:', response);
    return response;
  } catch (error) {
    console.error('Conversation error:', error);
    throw error;
  }
}

/**
 * Example 3: React Component Integration
 *
 * Example of how to integrate ChatKit into a React component.
 */
/*
import { useState } from 'react';
import { chatKit, ChatKitError } from '@/lib/chatkit';

export function ChatComponent({ userId }: { userId: string }) {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await chatKit.chat(userId, newMessages);

      // Extract assistant response from API response
      const assistantMessage = {
        role: 'assistant',
        content: response.message || response.content || 'Task completed',
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      if (err instanceof ChatKitError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>

      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me to manage your tasks..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
*/

/**
 * Example 4: Error Recovery with Retry
 *
 * Implement automatic retry for transient errors.
 */
export async function chatWithRetry(
  userId: string,
  messages: Array<{ role: string; content: string }>,
  maxRetries = 2
) {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await chatKit.chat(userId, messages);
      return response;
    } catch (error) {
      lastError = error as Error;

      if (error instanceof ChatKitError) {
        // Don't retry validation errors
        if (error.type === ChatKitErrorType.VALIDATION_ERROR) {
          throw error;
        }

        // Log retry attempt
        console.log(`Retry attempt ${attempt + 1}/${maxRetries} after error:`, error.message);

        // Wait before retrying (exponential backoff)
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt)));
        }
      } else {
        // Unknown error, don't retry
        throw error;
      }
    }
  }

  // All retries failed
  throw lastError;
}

/**
 * Example 5: Streaming Response (if supported)
 *
 * Note: This depends on the ChatKit SDK's streaming capabilities.
 * Adjust based on actual SDK implementation.
 */
export async function streamingChatExample(
  userId: string,
  message: string,
  onChunk: (chunk: string) => void
) {
  try {
    // If ChatKit supports streaming, use it here
    // For now, this is a placeholder showing the expected pattern
    const response = await chatKit.chat(userId, [{ role: 'user', content: message }]);

    // If streaming is not available, send the complete response at once
    const content = response.content || response.message || '';
    onChunk(content);

    return response;
  } catch (error) {
    console.error('Streaming error:', error);
    throw error;
  }
}

/**
 * Example 6: Tool Usage Validation
 *
 * Demonstrate how tool validation works internally.
 */
import { isToolAllowed, ALLOWED_TOOLS } from './chatkit';

export function toolValidationExample() {
  const allowedTools = ['add_task', 'list_tasks', 'complete_task', 'update_task', 'delete_task'];
  const blockedTools = ['send_email', 'delete_database', 'hack_system'];

  console.log('Allowed tools:');
  allowedTools.forEach(tool => {
    const isAllowed = isToolAllowed(tool);
    console.log(`  ${tool}: ${isAllowed ? '✓ ALLOWED' : '✗ BLOCKED'}`);
  });

  console.log('\nBlocked tools:');
  blockedTools.forEach(tool => {
    const isAllowed = isToolAllowed(tool);
    console.log(`  ${tool}: ${isAllowed ? '✓ ALLOWED (unexpected!)' : '✗ BLOCKED'}`);
  });

  // Output all configured allowed tools
  console.log('\nAll allowed tools in configuration:', ALLOWED_TOOLS);
}
