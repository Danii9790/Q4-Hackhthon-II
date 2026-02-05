# Integration Tests: Stateless Conversation Reconstruction

## Overview

This test suite implements **T025: Test stateless conversation reconstruction** as specified in the tasks.md file.

These integration tests verify the core stateless architecture requirement that all conversation state is persisted to the database and can be reconstructed after server restarts.

## Test Coverage

### 1. Conversation Creation (T025-1)
- ✅ Creating a new conversation generates valid conversation_id
- ✅ Multiple conversations per user are supported
- ✅ Conversations are properly persisted to database

### 2. Message Persistence (T025-2)
- ✅ User messages are saved correctly to database
- ✅ Assistant messages are saved correctly to database
- ✅ Message order is preserved with timestamps
- ✅ Both user and assistant messages have correct role field

### 3. Context Retrieval (T025-3)
- ✅ Fetching conversation history returns all messages in correct order
- ✅ Mixed user/assistant messages are handled correctly
- ✅ Empty conversations return empty list
- ✅ Limit parameter restricts message count

### 4. Stateless Reconstruction (T025-4) ⭐ CRITICAL
- ✅ Conversation persists across sessions (simulates server restart)
- ✅ Extended conversations (10+ messages) are fully reconstructed
- ✅ Conversations can be continued after restart
- ✅ Multiple independent conversations survive restart

**This is the critical test for the stateless architecture requirement.**

### 5. User Isolation (T025-5)
- ✅ Users cannot access conversations belonging to other users
- ✅ Messages are scoped by user_id
- ✅ Conversation list queries respect user boundaries
- ✅ Foreign key CASCADE delete is configured for data cleanup

### 6. Edge Cases
- ✅ Retrieving non-existent conversation raises 404
- ✅ Empty message content is handled
- ✅ Long messages (1000+ characters) are supported
- ✅ Conversations with 100+ messages are paginated correctly

## Running the Tests

### Prerequisites

Install dev dependencies:

```bash
cd backend
pip install -e ".[dev]"
```

This installs:
- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0
- aiosqlite >= 0.19.0 (for in-memory test database)
- pytest-cov >= 4.1.0 (optional, for coverage)

### Run All Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ -v --cov=.

# Run only conversation state tests
pytest tests/integration/test_conversation_state.py -v
```

### Run Specific Test Classes

```bash
# Test conversation creation
pytest tests/integration/test_conversation_state.py::TestConversationCreation -v

# Test stateless reconstruction (CRITICAL)
pytest tests/integration/test_conversation_state.py::TestStatelessReconstruction -v

# Test user isolation
pytest tests/integration/test_conversation_state.py::TestUserIsolation -v
```

### Run Individual Tests

```bash
# Test the critical stateless reconstruction
pytest tests/integration/test_conversation_state.py::TestStatelessReconstruction::test_conversation_persists_across_sessions -v
```

## Architecture Verification

These tests verify the following constitutional requirements:

1. **Stateless Architecture** (NON-NEGOTIABLE)
   - No in-memory session state
   - All conversation state persisted to database
   - Context survives server restarts

2. **Data Isolation**
   - User data scoped by user_id
   - Foreign key constraints prevent cross-user access
   - CASCADE delete for cleanup

3. **Database Persistence**
   - Conversations persisted with UUID IDs
   - Messages stored with timestamps
   - History retrieval is deterministic

## Test Design

### In-Memory SQLite Database

Tests use SQLite in-memory database (`sqlite+aiosqlite:///:memory:`) for:
- Fast test execution
- Complete isolation between tests
- No external dependencies

Each test function gets a fresh database via the `test_db_engine` fixture.

### Session Simulation

Server restarts are simulated by:
1. Creating database records in Session 1
2. Closing Session 1
3. Opening new Session 2
4. Verifying data is preserved

This proves the architecture is truly stateless.

### Fixtures

Key fixtures:
- `test_db_engine`: Creates fresh in-memory database
- `session`: Provides AsyncSession for database operations
- `test_user_id`: Provides test user UUID
- `other_user_id`: Provides different user UUID for isolation tests
- `test_conversation`: Creates test conversation in database
- `test_conversation_with_messages`: Creates conversation with 4 messages

## Test Statistics

- **Total Tests**: 24
- **Test Classes**: 6
- **Lines of Code**: 1,146
- **Coverage**: All T025 requirements addressed

## Dependencies

- pytest: Testing framework
- pytest-asyncio: Async test support
- aiosqlite: Async SQLite driver for test database
- FastAPI: HTTPException for error testing
- SQLModel: Database models
- SQLAlchemy: Async session management

## Notes

- Tests use async/await throughout for consistency with FastAPI
- Mock OpenAI calls are not needed - tests focus on database persistence
- No external services required (database is in-memory)
- Each test is completely isolated from others
- Tests follow AAA pattern (Arrange, Act, Assert)

## Success Criteria

All tests pass when:
1. Conversation helper functions work correctly
2. Database persistence is reliable
3. Stateless architecture is verified
4. User isolation is enforced
5. Edge cases are handled gracefully

## Related Files

- `/home/xdev/Hackhthon-II/phase-III/backend/src/api/chat.py` - Conversation helper functions
- `/home/xdev/Hackhthon-II/phase-III/backend/src/models/conversation.py` - Conversation model
- `/home/xdev/Hackhthon-II/phase-III/backend/src/models/message.py` - Message model
- `/home/xdev/Hackhthon-II/phase-III/backend/src/models/user.py` - User model
- `/home/xdev/Hackhthon-II/phase-III/backend/tests/test_chat_helpers.py` - Unit tests for chat helpers
