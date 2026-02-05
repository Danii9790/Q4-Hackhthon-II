# Chat Service

The chat service handles all API communication with the backend chat endpoint for the Todo AI Chatbot.

## Features

- **T072**: Fetch wrapper for `/api/{user_id}/chat` endpoint
- **T073**: JWT token authentication with Better Auth
- **T074**: Toast notifications for error handling

## Installation

The service requires `react-hot-toast` for notifications:

```bash
npm install react-hot-toast
```

## Setup

Add the `Toaster` component to your app root (e.g., in `pages/_app.tsx` or `app/layout.tsx`):

```tsx
import { Toaster } from 'react-hot-toast';

export default function App({ Component, pageProps }) {
  return (
    <>
      <Component {...pageProps} />
      <Toaster position="top-center" />
    </>
  );
}
```

## Usage

### Basic Example

```tsx
import { sendMessage } from '@/services';

async function handleSendMessage() {
  try {
    const response = await sendMessage(userId, {
      message: 'Add a task to buy groceries',
      conversation_id: null,
    });

    console.log('Assistant:', response.assistant_message);
    console.log 'Tool calls:', response.tool_calls);
  } catch (error) {
    // Error toast is automatically shown
    console.error('Failed to send message:', error);
  }
}
```

### Continue Conversation

```tsx
const response = await sendMessage(userId, {
  message: 'Show me all my tasks',
  conversation_id: 'existing-conversation-id',
});
```

### Check Authentication

```tsx
import { isAuthenticated, getAuthToken } from '@/services';

const authenticated = await isAuthenticated();
const token = await getAuthToken();
```

## API Reference

### `sendMessage(userId, request)`

Send a message to the AI chatbot.

**Parameters:**
- `userId` (string): User UUID
- `request` (ChatRequest):
  - `message` (string): User message (1-10,000 characters)
  - `conversation_id` (string | null): Conversation ID to continue, or null for new

**Returns:** `Promise<ChatResponse>`

**Throws:** `ChatApiError` on failure

**Example Response:**
```typescript
{
  conversation_id: "123e4567-e89b-12d3-a456-426614174000",
  assistant_message: "I've added that task for you!",
  tool_calls: [
    {
      tool_name: "add_task",
      arguments: { title: "Buy groceries" },
      result: { success: true, data: { id: 1 } }
    }
  ],
  timestamp: "2025-01-19T12:00:00Z"
}
```

### `getAuthToken()`

Extract JWT token from Better Auth session.

**Returns:** `Promise<string | null>`

### `isAuthenticated()`

Check if user has valid session.

**Returns:** `Promise<boolean>`

### `redirectToLogin()`

Redirect to login page.

## Error Handling

The service automatically shows toast notifications for errors:

- **400**: Validation error
- **401**: Unauthorized (redirects to login)
- **403**: Forbidden
- **404**: Not found
- **429**: Rate limit
- **500/502/503**: Server error
- **Network error**: Connection failed

Custom errors can be shown using:

```tsx
import { showGenericErrorToast, showSuccessToast } from '@/services';

showSuccessToast('Message sent successfully!');
showGenericErrorToast('Custom error message');
```

## Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000
```

## Type Definitions

```typescript
interface ChatRequest {
  message: string;
  conversation_id: string | null;
}

interface ChatResponse {
  conversation_id: string;
  assistant_message: string;
  tool_calls: ToolCallDetail[];
  timestamp: string;
}

interface ToolCallDetail {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: unknown;
}

class ChatApiError extends Error {
  statusCode: number;
  detail: string;
}
```

## Tasks Completed

- ✅ **T072**: Implemented fetch wrapper for chat endpoint
- ✅ **T073**: Added JWT token handling with Better Auth
- ✅ **T074**: Implemented toast notifications for errors
