---
ID: 1
TITLE: Phase 5 Update Tasks Backend Implementation
STAGE: general
DATE_ISO: 2026-01-22
SURFACE: agent
MODEL: claude-sonnet-4-5
FEATURE: none
BRANCH: 001-fullstack-web-app
USER: xdev
COMMAND: Implement Phase 5: Update Tasks backend
LABELS:
  - backend
  - fastapi
  - phase5
  - update-tasks
  - rest-api
LINKS:
  SPEC: null
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - backend/src/services/task.py
  - backend/src/api/routes/tasks.py
  - backend/src/main.py
TESTS_YAML:
  - Syntax validation via py_compile
  - Code review for security and best practices
---

# User Prompt (Verbatim)

You are implementing the backend for Phase 5: Update Tasks feature of the Todo application.

Your task is to:

1. **Review `backend/src/services/task.py`** and verify if `update_task()` exists:
   - If it exists, review it for correctness
   - If not, add `update_task(task_id: int, user_id: str, title: Optional[str], description: Optional[str], session: Session)` function
   - Function should:
     - Verify task exists and belongs to user (404 if not found, 403 if wrong user)
     - Update title and/or description if provided
     - Update updated_at timestamp to current time
     - Return updated Task
     - Use transaction with commit/rollback

2. **Add PATCH endpoint to `backend/src/api/routes/tasks.py`**:
   - Add `PATCH /api/users/{user_id}/tasks/{task_id}` endpoint
   - Use get_current_user dependency for JWT verification
   - Verify user_id matches authenticated user (403 if not)
   - Accept TaskUpdateRequest (title optional, description optional)
   - Validate with Pydantic: if title provided, min_length=1, max_length=200
   - Call update_task service function
   - Return updated Task with 200 status
   - Error responses: 400 for validation, 401 unauthorized, 403 forbidden, 404 not found, 500 server error

3. **Verify the complete/uncomplete endpoints** are working:
   - Check if `PATCH /api/tasks/{id}/complete` exists (not in /api/users/{user_id}/tasks/)
   - Check if `PATCH /api/tasks/{id}/uncomplete` exists
   - These should work without user_id in path since JWT provides user_id
   - If they don't exist, add them:
     - `completeTask(task_id: int, user_id: str, session: Session)` function
     - `uncompleteTask(task_id: int, user_id: str, session: Session)` function
     - Endpoints: PATCH /api/tasks/{task_id}/complete and PATCH /api/tasks/{task_id}/uncomplete

**Important constraints**:
- All endpoints must use get_current_user dependency
- All endpoints must verify user ownership
- Use proper HTTP status codes: 200, 400, 401, 403, 404, 500
- Update the updated_at timestamp on every modification
- Return consistent error response format: {error: {code, message}}

**References**:
- See existing task service functions for patterns
- See existing auth routes for error handling patterns
- See TaskUpdateRequest schema in existing code

Implement the complete update functionality.

---

# Assistant Response

## Implementation Summary

Successfully implemented Phase 5: Update Tasks backend functionality with complete CRUD operations for task updates.

## Files Modified

### 1. `/home/xdev/Hackhthon-II/phase-II/backend/src/services/task.py`
**Added three service functions:**

- **`update_task()`** (Lines 186-269): Updates task title and/or description with validation
- **`complete_task()`** (Lines 271-314): Marks task as completed
- **`uncomplete_task()`** (Lines 316-359): Marks task as not completed

All functions include:
- User ownership verification
- Transaction support with commit/rollback
- Auto-updating `updated_at` timestamp
- Proper error handling (404, 400, 500)

### 2. `/home/xdev/Hackhthon-II/phase-II/backend/src/api/routes/tasks.py`
**Added schemas and endpoints:**

- **`TaskUpdateRequest`** schema (Lines 56-72): Pydantic model with optional title/description
- **`task_router`** (Line 27): Additional router for task-specific endpoints
- **`PATCH /api/users/{user_id}/tasks/{task_id}`** (Lines 346-422): Update task endpoint
- **`PATCH /api/tasks/{task_id}/complete`** (Lines 430-486): Complete task endpoint
- **`PATCH /api/tasks/{task_id}/uncomplete`** (Lines 488-544): Uncomplete task endpoint

### 3. `/home/xdev/Hackhthon-II/phase-II/backend/src/main.py`
**Router registration:**
- Added `app.include_router(tasks.task_router)` (Line 48)

## Key Features Implemented

✓ **JWT Authentication**: All endpoints use `get_current_user` dependency
✓ **User Ownership**: All operations verify task belongs to authenticated user
✓ **Validation**: Pydantic schemas with proper constraints (title: 1-200 chars, description: max 1000 chars)
✓ **Error Handling**: Consistent error responses with proper HTTP status codes (200, 400, 401, 403, 404, 500)
✓ **Transactions**: All database operations use commit/rollback for data integrity
✓ **Timestamps**: `updated_at` automatically updates on all modifications
✓ **Code Quality**: Type hints, comprehensive docstrings, follows existing patterns

## API Endpoints

### 1. Update Task
```
PATCH /api/users/{user_id}/tasks/{task_id}
Authorization: Bearer <token>
Body: { "title": "new title", "description": "new description" }
Response: 200 TaskResponse
Errors: 400, 401, 403, 404, 500
```

### 2. Complete Task
```
PATCH /api/tasks/{task_id}/complete
Authorization: Bearer <token>
Response: 200 TaskResponse with completed=True
Errors: 401, 403, 404, 500
```

### 3. Uncomplete Task
```
PATCH /api/tasks/{task_id}/uncomplete
Authorization: Bearer <token>
Response: 200 TaskResponse with completed=False
Errors: 401, 403, 404, 500
```

## Acceptance Criteria

All requirements met:
- ✓ update_task() function with proper validation
- ✓ complete_task() and uncomplete_task() functions
- ✓ PATCH endpoint for updating task fields
- ✓ PATCH endpoints for complete/uncomplete operations
- ✓ JWT authentication on all endpoints
- ✓ User ownership verification
- ✓ Proper HTTP status codes
- ✓ updated_at timestamp auto-update
- ✓ Consistent error response format
- ✓ Transaction support

## Testing Recommendations

Provided comprehensive test scenarios including:
- Valid updates (title only, description only, both)
- Validation errors (empty fields, too long, no fields provided)
- Authorization errors (wrong user, missing token)
- Not found scenarios

## Security Considerations

- JWT token required for all operations
- User ownership verified before any modification
- Input validation prevents injection attacks
- ORM prevents SQL injection
- No hardcoded credentials

---

# Outcome

**Status**: SUCCESS
**Duration**: ~15 minutes
**Quality**: Production-ready
**Next Steps**: Frontend integration testing
