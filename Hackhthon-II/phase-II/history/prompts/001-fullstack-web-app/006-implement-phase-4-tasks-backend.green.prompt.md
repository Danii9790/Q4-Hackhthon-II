---
id: 006
title: Implement Phase 4 Tasks Backend
stage: green
date: 2026-01-22
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-fullstack-web-app
branch: 001-fullstack-web-app
user: xdev
command: Implement backend for Phase 4: Create and View Tasks
labels: ["backend","fastapi","tasks","implementation"]
links:
  spec: /home/xdev/specs/001-fullstack-web-app/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/services/task.py
  - backend/src/api/routes/tasks.py
  - backend/src/main.py
tests:
  - Syntax validation with py_compile (all files pass)
  - Import structure verification
---

## Prompt

You are implementing the backend for Phase 4: Create and View Tasks feature of the Todo application.

Your task is to:

1. **Create `backend/src/services/task.py`** with:
   - `create_task(title: str, description: Optional[str], user_id: str, session: Session)` function
     - Validate title (1-200 chars) and description (0-1000 chars)
     - Create task with completed=False and current timestamps
     - Return the created Task model
   - `list_tasks(user_id: str, offset: int = 0, limit: int = 50, session: Session)` function
     - Query tasks filtered by user_id
     - Order by created_at DESC (most recent first)
     - Apply pagination with offset/limit
     - Return tuple of (tasks, total_count)
   - `get_task(task_id: int, user_id: str, session: Session)` function
     - Get task by ID with user ownership check
     - Raise 404 if not found or doesn't belong to user
     - Return Task model

2. **Create `backend/src/api/routes/tasks.py`** with:
   - GET /api/users/{user_id}/tasks endpoint
     - Use get_current_user dependency to verify JWT
     - Verify user_id matches authenticated user (403 if not)
     - Accept offset and limit query params (default 0, 50, max 100)
     - Call list_tasks service function
     - Return TaskListResponse with tasks, total, offset, limit
   - POST /api/users/{user_id}/tasks endpoint
     - Use get_current_user dependency
     - Verify user_id matches authenticated user
     - Accept TaskCreateRequest (title, description optional)
     - Validate with Pydantic (title min_length=1, max_length=200)
     - Call create_task service function
     - Return created Task with 201 status
   - GET /api/users/{user_id}/tasks/{task_id} endpoint
     - Use get_current_user dependency
     - Verify user_id matches authenticated user
     - Call get_task service function
     - Return Task or 404

3. **Update `backend/src/main.py`**:
   - Import and include the tasks router: `from src.api.routes import tasks`
   - Add: `app.include_router(tasks.router)`

**Important constraints**:
- All endpoints must use `get_current_user` dependency for JWT verification
- All endpoints must verify user_id matches authenticated user (return 403 if not)
- Use proper HTTP status codes: 200, 201, 400, 401, 403, 404, 500
- Use the existing User and Task models from `backend/src/models/`
- Use the existing get_session dependency from `backend/src/db.py`
- Return consistent error responses with {error: {code, message}} structure

**References**:
- See `backend/src/models/task.py` for Task model structure
- See `backend/src/api/dependencies.py` for get_current_user
- See `backend/src/services/auth.py` for service pattern
- See `backend/src/api/routes/auth.py` for endpoint pattern

Create all files with complete implementation.

## Response snapshot

Successfully implemented the backend for Phase 4: Create and View Tasks feature.

**Files Created/Modified:**

1. **`backend/src/services/task.py`** - Task service layer with:
   - `create_task()`: Validates title (1-200 chars) and description (0-1000 chars), creates task with completed=False and current timestamps
   - `list_tasks()`: Queries tasks by user_id, orders by created_at DESC, applies pagination, returns (tasks, total_count)
   - `get_task()`: Retrieves task by ID with user ownership check, raises 404 if not found or doesn't belong to user
   - All functions include proper error handling with HTTPException and consistent error responses

2. **`backend/src/api/routes/tasks.py`** - Task routes with three endpoints:
   - **GET /api/users/{user_id}/tasks**: List user's tasks with pagination (offset/limit, max 100)
   - **POST /api/users/{user_id}/tasks**: Create new task (title required, description optional)
   - **GET /api/users/{user_id}/tasks/{task_id}**: Get specific task by ID
   - All endpoints use `get_current_user` dependency for JWT verification
   - All endpoints verify user_id matches authenticated user (403 if not)
   - Proper Pydantic request/response schemas with validation
   - Comprehensive error responses with {error: {code, message}} structure
   - Full OpenAPI documentation with status codes

3. **`backend/src/main.py`** - Updated to include tasks router

**Implementation Highlights:**
- Service layer separates business logic from route handlers
- Consistent error handling across all endpoints
- User ownership verification prevents cross-user access
- Pagination supports efficient large dataset retrieval
- All code follows existing patterns from auth.py
- Type hints throughout for better IDE support
- Comprehensive docstrings for all functions

**Validation Complete:**
- All files pass py_compile syntax validation
- Import structure verified
- Code follows established patterns from auth routes

## Outcome

- ✅ Impact: Complete backend implementation for Phase 4 task management features (create, list, get tasks)
- 🧪 Tests: Syntax validation passed for all Python files (py_compile)
- 📁 Files: Created 2 new files (task service, task routes), modified 1 file (main.py)
- 🔁 Next prompts: Consider implementing Phase 5 frontend integration, or writing integration tests for task endpoints
- 🧠 Reflection: Service layer pattern provides clean separation of concerns. User ownership checks at both service and route layers provide defense in depth. Pagination prevents performance issues with large datasets.

## Evaluation notes (flywheel)

- Failure modes observed: None during implementation
- Graders run and results (PASS/FAIL): Syntax validation PASS (all files compile successfully)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Consider adding unit tests for task service layer before frontend integration
