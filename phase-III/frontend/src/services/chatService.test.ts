/**
 * Chat Service Tests
 *
 * Demonstrates usage of the chat service and provides test examples.
 * These are integration tests that would run with a test backend.
 */

import {
  sendMessage,
  getAuthToken,
  isAuthenticated,
  ChatRequest,
  ChatResponse,
} from './chatService';

// ============================================================================
// Usage Examples
// ============================================================================

/**
 * Example 1: Send a message to start a new conversation
 */
export async function example1_StartNewConversation(): Promise<void> {
  const userId = '123e4567-e89b-12d3-a456-426614174000';

  const request: ChatRequest = {
    message: 'Add a task to buy groceries',
    conversation_id: null, // Start new conversation
  };

  try {
    const response: ChatResponse = await sendMessage(userId, request);
    console.log('Assistant:', response.assistant_message);
    console.log('Conversation ID:', response.conversation_id);
    console.log('Tool calls:', response.tool_calls);
  } catch (error) {
    console.error('Error:', error);
  }
}

/**
 * Example 2: Continue an existing conversation
 */
export async function example2_ContinueConversation(): Promise<void> {
  const userId = '123e4567-e89b-12d3-a456-426614174000';
  const conversationId = '123e4567-e89b-12d3-a456-426614174001';

  const request: ChatRequest = {
    message: 'Show me all my tasks',
    conversation_id: conversationId, // Continue existing conversation
  };

  try {
    const response: ChatResponse = await sendMessage(userId, request);
    console.log('Assistant:', response.assistant_message);
  } catch (error) {
    console.error('Error:', error);
  }
}

/**
 * Example 3: Check authentication before sending
 */
export async function example3_CheckAuthFirst(): Promise<void> {
  const authenticated = await isAuthenticated();

  if (!authenticated) {
    console.log('User is not authenticated');
    return;
  }

  const token = await getAuthToken();
  console.log('Auth token:', token ? 'exists' : 'missing');
}

/**
 * Example 4: Handle errors gracefully
 */
export async function example4_ErrorHandling(): Promise<void> {
  const userId = '123e4567-e89b-12d3-a456-426614174000';

  const request: ChatRequest = {
    message: '', // Empty message will trigger validation error
    conversation_id: null,
  };

  try {
    await sendMessage(userId, request);
  } catch (error) {
    if (error instanceof Error) {
      console.error('Caught error:', error.message);
      // Error toast is automatically shown by the service
    }
  }
}

// ============================================================================
// Test Cases (for testing framework)
// ============================================================================

/**
 * Test: Send message successfully
 */
export async function test_SendMessage_Success(): Promise<boolean> {
  try {
    const response = await sendMessage('test-user-id', {
      message: 'Test message',
      conversation_id: null,
    });

    return (
      response.conversation_id !== undefined &&
      response.assistant_message !== undefined &&
      Array.isArray(response.tool_calls)
    );
  } catch {
    return false;
  }
}

/**
 * Test: Reject empty message
 */
export async function test_SendMessage_EmptyMessage(): Promise<boolean> {
  try {
    await sendMessage('test-user-id', {
      message: '',
      conversation_id: null,
    });
    return false; // Should have thrown error
  } catch (error) {
    return error instanceof Error; // Expected to throw
  }
}

/**
 * Test: Reject message exceeding max length
 */
export async function test_SendMessage_TooLong(): Promise<boolean> {
  try {
    const longMessage = 'a'.repeat(10001);
    await sendMessage('test-user-id', {
      message: longMessage,
      conversation_id: null,
    });
    return false; // Should have thrown error
  } catch (error) {
    return error instanceof Error; // Expected to throw
  }
}

/**
 * Test: Handle unauthorized response
 */
export async function test_SendMessage_Unauthorized(): Promise<boolean> {
  try {
    // This will fail if not authenticated
    await sendMessage('invalid-user-id', {
      message: 'Test',
      conversation_id: null,
    });
    return false;
  } catch (error) {
    return error instanceof Error;
  }
}

// ============================================================================
// Mock Tests (for unit testing without backend)
// ============================================================================

/**
 * Mock test: Verify request structure
 */
export function test_MockRequestStructure(): boolean {
  const request: ChatRequest = {
    message: 'Test message',
    conversation_id: null,
  };

  return (
    request.message === 'Test message' &&
    request.conversation_id === null
  );
}

/**
 * Mock test: Verify response structure
 */
export function test_MockResponseStructure(): boolean {
  const mockResponse: ChatResponse = {
    conversation_id: '123e4567-e89b-12d3-a456-426614174000',
    assistant_message: 'I added that task for you!',
    tool_calls: [
      {
        tool_name: 'add_task',
        arguments: { title: 'Buy groceries' },
        result: { success: true, data: { id: 1 } },
      },
    ],
    timestamp: new Date().toISOString(),
  };

  return (
    mockResponse.conversation_id !== undefined &&
    mockResponse.assistant_message !== undefined &&
    Array.isArray(mockResponse.tool_calls) &&
    mockResponse.tool_calls.length === 1 &&
    mockResponse.tool_calls[0].tool_name === 'add_task'
  );
}

// ============================================================================
// Export all examples and tests
// ============================================================================

export const examples = {
  example1_StartNewConversation,
  example2_ContinueConversation,
  example3_CheckAuthFirst,
  example4_ErrorHandling,
};

export const tests = {
  test_SendMessage_Success,
  test_SendMessage_EmptyMessage,
  test_SendMessage_TooLong,
  test_SendMessage_Unauthorized,
  test_MockRequestStructure,
  test_MockResponseStructure,
};
