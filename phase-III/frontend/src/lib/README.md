# ChatKit Configuration

This directory contains the ChatKit configuration for the Todo AI Chatbot frontend application.

## Overview

The ChatKit library is configured to provide AI-powered task management through natural language conversations. The implementation includes:

- **REST Adapter**: Connects to the FastAPI backend at `http://localhost:8000` (configurable via `VITE_API_URL` or `NEXT_PUBLIC_API_URL`)
- **Domain Restrictions**: Only allows task management tools (add_task, list_tasks, complete_task, update_task, delete_task)
- **Error Handling**: Comprehensive error types with timeout and retry logic
- **TypeScript Support**: Fully typed with custom error classes and JSDoc documentation

## Files

### `chatkit.ts`
Main configuration file that exports:
- `chatKit`: Configured ChatKit instance
- `ChatKitError`: Custom error class with error types
- `ChatKitErrorType`: Enum of error types (NETWORK_ERROR, API_ERROR, TIMEOUT_ERROR, etc.)
- `ALLOWED_TOOLS`: Array of permitted tool names
- `API_URL`: Configured backend URL
- `CHAT_ENDPOINT`: Chat endpoint path

### `chatkit.example.ts`
Usage examples demonstrating:
- Basic chat requests
- Multi-turn conversations
- React component integration
- Error recovery with retry
- Tool validation
- Streaming responses (placeholder)

## Configuration

### Environment Variables

Configure the API URL using either:
- `VITE_API_URL` (for Vite)
- `NEXT_PUBLIC_API_URL` (for Next.js)

If neither is set, defaults to `http://localhost:8000`.

### Allowed Tools

The following tools are permitted (all others are blocked):
- `add_task` - Create a new task
- `list_tasks` - List tasks by status
- `complete_task` - Mark a task as complete
- `update_task` - Modify an existing task
- `delete_task` - Remove a task

### Request Configuration

- **Timeout**: 30 seconds (30000ms)
- **Max Retries**: 3 attempts
- **Retry Delay**: Exponential backoff (1s, 2s, 4s)

## Usage

### Basic Usage

```typescript
import { chatKit } from '@/lib/chatkit';

const response = await chatKit.chat(userId, [
  {
    role: 'user',
    content: 'Add a task to buy groceries',
  },
]);
```

### Error Handling

```typescript
import { chatKit, ChatKitError, ChatKitErrorType } from '@/lib/chatkit';

try {
  const response = await chatKit.chat(userId, messages);
} catch (error) {
  if (error instanceof ChatKitError) {
    switch (error.type) {
      case ChatKitErrorType.NETWORK_ERROR:
        // Handle network errors
        break;
      case ChatKitErrorType.TIMEOUT_ERROR:
        // Handle timeouts
        break;
      case ChatKitErrorType.API_ERROR:
        // Handle API errors (check error.statusCode)
        break;
      case ChatKitErrorType.VALIDATION_ERROR:
        // Handle validation errors
        break;
    }
  }
}
```

### React Component Integration

```tsx
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
      {/* Messages display */}
      <form onSubmit={handleSubmit}>
        {/* Input form */}
      </form>
    </div>
  );
}
```

## Error Types

### ChatKitErrorType

| Type | Description | When It Occurs |
|------|-------------|----------------|
| `NETWORK_ERROR` | Failed to connect to API | Server unreachable, CORS issues, DNS failures |
| `API_ERROR` | API returned error response | 4xx/5xx responses, backend errors |
| `TIMEOUT_ERROR` | Request exceeded timeout | Slow server, network congestion |
| `VALIDATION_ERROR` | Invalid request data | Missing userId, malformed messages |
| `UNKNOWN_ERROR` | Unexpected error | Unhandled exceptions |

### ChatKitError Class

```typescript
class ChatKitError extends Error {
  type: ChatKitErrorType;
  message: string;
  originalError?: unknown;
  statusCode?: number;
}
```

## Architecture

### DomainRestrictedRESTAdapter

Custom REST adapter that extends the base `RESTAdapter` class to provide:

1. **Tool Validation**: Checks all tool calls against the allowlist
2. **Request Validation**: Validates userId and message format
3. **Error Handling**: Wraps all errors in `ChatKitError` instances
4. **URL Construction**: Builds proper API endpoint URLs

### Enhanced Fetch

Custom fetch implementation that adds:

1. **Timeout Support**: Uses AbortController to cancel long-running requests
2. **Retry Logic**: Automatically retries failed network requests with exponential backoff
3. **Error Transformation**: Converts fetch errors into ChatKitError instances

### ChatKit Instance

Singleton instance configured with:
- Custom adapter
- Domain restrictions (task_management)
- Error handler
- Request configuration (timeout, retries)

## Security

### Domain Allowlist

All tool calls are validated against the `ALLOWED_TOOLS` array. Tools not in this list are blocked with a console warning:

```typescript
function isToolAllowed(toolName: string): boolean {
  return ALLOWED_TOOLS.includes(toolName as typeof ALLOWED_TOOLS[number]);
}
```

### Input Validation

The adapter validates:
- `userId` must be a non-empty string
- `messages` must be a non-empty array
- Each message must have `role` and `content` fields

### URL Encoding

User IDs are properly encoded in URLs to prevent injection attacks:

```typescript
const url = `${this.baseUrl}${CHAT_ENDPOINT}/${encodeURIComponent(userId)}/chat`;
```

## Testing

### Manual Testing

1. Start the backend server: `cd backend && uvicorn app.main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Open browser console and test:

```javascript
// Test basic chat
import { chatKit } from './src/lib/chatkit';
const response = await chatKit.chat('test-user', [{ role: 'user', content: 'Add a task to test' }]);
console.log(response);

// Test error handling
try {
  await chatKit.chat('', [{ role: 'user', content: 'test' }]);
} catch (error) {
  console.error('Expected validation error:', error);
}
```

### Unit Testing

Create tests for:
- Tool validation logic
- Error type detection
- Retry behavior
- URL construction
- Message validation

## Troubleshooting

### Common Issues

**Issue**: "Network error: Failed to connect to API server"
- **Cause**: Backend server not running or wrong URL
- **Fix**: Ensure backend is running and `VITE_API_URL` is correct

**Issue**: "Request timeout after 30000ms"
- **Cause**: Server taking too long to respond
- **Fix**: Increase `REQUEST_TIMEOUT` or optimize backend

**Issue**: "Tool X is not in the allowlist"
- **Cause**: Attempting to use a non-allowed tool
- **Fix**: Add tool to `ALLOWED_TOOLS` array if appropriate

**Issue**: TypeScript errors about `@openai/chatkit`
- **Cause**: SDK not installed
- **Fix**: Run `npm install @openai/chatkit`

## Dependencies

- `@openai/chatkit`: OpenAI ChatKit SDK (latest)
- TypeScript: 5.7.2+
- React: 18.3.1+ (for React components)

## Related Files

- Backend API: `/backend/app/api/routes/chat.py`
- MCP Tools: `/backend/app/api/tools/`
- Frontend Components: `/frontend/src/components/`
- Environment Config: `/frontend/.env.example`

## Future Enhancements

Potential improvements:
1. **Streaming Support**: Implement real-time streaming responses
2. **Caching**: Add response caching for repeated queries
3. **Metrics**: Track request latency, error rates, retry counts
4. **Analytics**: Log tool usage patterns
5. **Rate Limiting**: Add client-side rate limiting
6. **Offline Support**: Queue requests when offline
7. **WebSocket Support**: Upgrade to WebSocket for real-time updates
