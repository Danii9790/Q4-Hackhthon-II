# Todo API Documentation

**Phase V: Advanced Cloud Deployment**

Version: 1.0.0
Base URL: `http://localhost:8000` (local) or `https://api.todo.example.com` (production)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Tasks](#tasks)
3. [Recurring Tasks](#recurring-tasks)
4. [Audit Trail](#audit-trail)
5. [Real-Time Updates](#real-time-updates)
6. [WebSocket](#websocket)
7. [Error Responses](#error-responses)
8. [Rate Limiting](#rate-limiting)

---

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Signup

**POST** `/api/auth/signup`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword123"
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2026-02-10T10:00:00Z"
}
```

### Login

**POST** `/api/auth/login`

Authenticate and receive a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

---

## Tasks

### List Tasks

**GET** `/api/users/{user_id}/tasks`

Get all tasks for a user with pagination.

**Parameters:**
- `user_id` (path): User ID
- `limit` (query, optional): Number of tasks to return (default: 10, max: 100)
- `offset` (query, optional): Number of tasks to skip (default: 0)

**Response (200):**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Complete project",
      "description": "Finish Phase V implementation",
      "completed": false,
      "priority": "high",
      "tags": ["work", "important"],
      "due_date": "2026-02-15T00:00:00Z",
      "created_at": "2026-02-10T10:00:00Z",
      "updated_at": "2026-02-10T10:00:00Z"
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

### Create Task

**POST** `/api/users/{user_id}/tasks`

Create a new task.

**Request Body:**
```json
{
  "title": "Complete project",
  "description": "Finish Phase V implementation",
  "due_date": "2026-02-15T00:00:00Z",
  "priority": "high",
  "tags": ["work", "important"]
}
```

**Response (201):**
```json
{
  "id": 1,
  "title": "Complete project",
  "description": "Finish Phase V implementation",
  "completed": false,
  "priority": "high",
  "tags": ["work", "important"],
  "due_date": "2026-02-15T00:00:00Z",
  "created_at": "2026-02-10T10:00:00Z",
  "updated_at": "2026-02-10T10:00:00Z"
}
```

### Get Task

**GET** `/api/tasks/{task_id}`

Get a specific task by ID.

**Response (200):**
```json
{
  "id": 1,
  "title": "Complete project",
  "description": "Finish Phase V implementation",
  "completed": false,
  "priority": "high",
  "tags": ["work", "important"],
  "created_at": "2026-02-10T10:00:00Z",
  "updated_at": "2026-02-10T10:00:00Z"
}
```

### Update Task

**PATCH** `/api/tasks/{task_id}`

Update a task.

**Request Body:**
```json
{
  "title": "Complete Phase V",
  "priority": "urgent"
}
```

**Response (200):**
```json
{
  "id": 1,
  "title": "Complete Phase V",
  "description": "Finish Phase V implementation",
  "completed": false,
  "priority": "urgent",
  "tags": ["work", "important"],
  "updated_at": "2026-02-10T11:00:00Z"
}
```

### Complete Task

**PATCH** `/api/tasks/{task_id}/complete`

Mark a task as completed.

**Response (200):**
```json
{
  "id": 1,
  "title": "Complete Phase V",
  "completed": true,
  "completed_at": "2026-02-10T11:30:00Z"
}
```

### Delete Task

**DELETE** `/api/tasks/{task_id}`

Delete a task.

**Response (204):** No content

---

## Recurring Tasks

### Create Recurring Task

**POST** `/api/users/{user_id}/recurring-tasks`

Create a recurring task with automation rules.

**Request Body:**
```json
{
  "title": "Weekly team meeting",
  "description": "Team sync every Monday",
  "frequency": "weekly",
  "interval": 1,
  "days_of_week": [1],
  "end_date": "2026-12-31T00:00:00Z"
}
```

**Response (201):**
```json
{
  "id": 1,
  "title": "Weekly team meeting",
  "frequency": "weekly",
  "interval": 1,
  "days_of_week": [1],
  "next_due_date": "2026-02-17T00:00:00Z",
  "created_at": "2026-02-10T10:00:00Z"
}
```

### List Recurring Tasks

**GET** `/api/users/{user_id}/recurring-tasks`

Get all recurring tasks for a user.

**Response (200):**
```json
{
  "recurring_tasks": [
    {
      "id": 1,
      "title": "Weekly team meeting",
      "frequency": "weekly",
      "active": true,
      "next_due_date": "2026-02-17T00:00:00Z"
    }
  ]
}
```

---

## Audit Trail

### Get Task Audit History

**GET** `/api/tasks/{task_id}/audit`

Get the complete audit trail for a specific task.

**Parameters:**
- `task_id` (path): Task ID
- `limit` (query, optional): Maximum events to return (default: 100, max: 1000)

**Response (200):**
```json
{
  "events": [
    {
      "id": "event-uuid-1",
      "event_type": "created",
      "task_id": 1,
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "event_data": {
        "timestamp": "2026-02-10T10:00:00Z",
        "before": null,
        "after": {"title": "Complete project"},
        "changes": ["created"]
      },
      "timestamp": "2026-02-10T10:00:00Z"
    },
    {
      "id": "event-uuid-2",
      "event_type": "updated",
      "task_id": 1,
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "event_data": {
        "timestamp": "2026-02-10T11:00:00Z",
        "before": {"priority": "high"},
        "after": {"priority": "urgent"},
        "changes": ["priority"]
      },
      "timestamp": "2026-02-10T11:00:00Z"
    }
  ],
  "count": 2
}
```

### Get User Audit Activity

**GET** `/api/users/{user_id}/audit`

Get all audit events for a user across all tasks.

**Response (200):**
```json
{
  "events": [
    {
      "id": "event-uuid-1",
      "event_type": "created",
      "task_id": 1,
      "timestamp": "2026-02-10T10:00:00Z"
    }
  ],
  "count": 1
}
```

---

## Real-Time Updates

### WebSocket Connection

**WS** `/api/users/{user_id}/ws`

Connect to WebSocket for real-time task updates.

**Message Format:**
```json
{
  "type": "task_created" | "task_updated" | "task_completed" | "task_deleted",
  "task_id": 1,
  "data": {
    "id": 1,
    "title": "Complete project",
    "completed": false
  },
  "timestamp": "2026-02-10T10:00:00Z"
}
```

**Ping/Pong:**
- Client sends: `{"type": "ping"}`
- Server responds: `{"type": "pong"}`

---

## Error Responses

All errors follow this format:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "request_id": "uuid-for-tracking"
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `TASK_NOT_FOUND` | 404 | Task does not exist |
| `FORBIDDEN` | 403 | User doesn't own the task |
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Rate Limiting

**T176**: API endpoints are rate-limited to prevent abuse:

- **Unauthenticated**: 10 requests per minute
- **Authenticated**: 100 requests per minute
- **WebSocket**: 1 connection per user per device

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1644480000
```

---

## Performance

**T180**: API performance targets:

- **P50 latency**: < 100ms
- **P95 latency**: < 500ms
- **P99 latency**: < 1000ms
- **Throughput**: 1000 requests/second

---

## Monitoring

Metrics are exposed at `/metrics` in Prometheus format:

- `http_requests_total` - Total HTTP requests by endpoint, method, status
- `http_request_duration_seconds` - Request latency histogram
- `kafka_messages_published_total` - Kafka messages published
- `db_query_duration_seconds` - Database query latency
- `tasks_total` - Task count by user and status
