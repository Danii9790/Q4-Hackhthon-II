# Quick Start: Running T025 Integration Tests

## Overview

This guide provides quick commands to run the T025 stateless conversation reconstruction tests.

## Prerequisites

```bash
# Navigate to backend directory
cd /home/xdev/Hackhthon-II/phase-III/backend

# Install dev dependencies (includes pytest, pytest-asyncio, aiosqlite)
pip install -e ".[dev]"
```

## Run Tests

### Run All T025 Tests

```bash
pytest tests/integration/test_conversation_state.py -v
```

### Run Specific Test Categories

```bash
# Conversation creation tests
pytest tests/integration/test_conversation_state.py::TestConversationCreation -v

# Message persistence tests
pytest tests/integration/test_conversation_state.py::TestMessagePersistence -v

# Context retrieval tests
pytest tests/integration/test_conversation_state.py::TestContextRetrieval -v

# ⭐ CRITICAL: Stateless reconstruction tests
pytest tests/integration/test_conversation_state.py::TestStatelessReconstruction -v

# User isolation tests
pytest tests/integration/test_conversation_state.py::TestUserIsolation -v

# Edge case tests
pytest tests/integration/test_conversation_state.py::TestEdgeCases -v
```

### Run Individual Tests

```bash
# Most critical test - verifies stateless architecture
pytest tests/integration/test_conversation_state.py::TestStatelessReconstruction::test_conversation_persists_across_sessions -v

# Test with extended conversation (10+ messages)
pytest tests/integration/test_conversation_state.py::TestStatelessReconstruction::test_extended_conversation_reconstruction -v

# Test conversation continuation after restart
pytest tests/integration/test_conversation_state.py::TestStatelessReconstruction::test_conversation_continuation_after_restart -v
```

### Run with Coverage

```bash
# Coverage for chat.py module
pytest tests/integration/test_conversation_state.py -v --cov=src.api.chat --cov-report=term-missing

# Coverage with HTML report
pytest tests/integration/test_conversation_state.py -v --cov=src.api.chat --cov-report=html
# Open htmlcov/index.html in browser to view
```

### Run All Integration Tests

```bash
pytest tests/integration/ -v
```

### Run All Tests (Unit + Integration)

```bash
pytest tests/ -v
```

## Expected Output

When all tests pass, you should see:

```
tests/integration/test_conversation_state.py::TestConversationCreation::test_create_new_conversation_generates_valid_id PASSED
tests/integration/test_conversation_state.py::TestConversationCreation::test_multiple_conversations_per_user PASSED
tests/integration/test_conversation_state.py::TestMessagePersistence::test_user_message_persistence PASSED
tests/integration/test_conversation_state.py::TestMessagePersistence::test_assistant_message_persistence PASSED
tests/integration/test_conversation_state.py::TestMessagePersistence::test_message_order_preservation PASSED
tests/integration/test_conversation_state.py::TestContextRetrieval::test_fetch_conversation_history_returns_all_messages PASSED
tests/integration/test_conversation_state.py::TestContextRetrieval::test_history_with_mixed_roles PASSED
tests/integration/test_conversation_state.py::TestContextRetrieval::test_empty_conversation_returns_empty_list PASSED
tests/integration/test_conversation_state.py::TestStatelessReconstruction::test_conversation_persists_across_sessions PASSED
tests/integration/test_conversation_state.py::TestStatelessReconstruction::test_extended_conversation_reconstruction PASSED
tests/integration/test_conversation_state.py::TestStatelessReconstruction::test_conversation_continuation_after_restart PASSED
tests/integration/test_conversation_state.py::TestStatelessReconstruction::test_multiple_conversations_survive_restart PASSED
tests/integration/test_conversation_state.py::TestUserIsolation::test_user_cannot_access_other_user_conversation PASSED
tests/integration/test_conversation_state.py::TestUserIsolation::test_messages_scoped_by_user_id PASSED
tests/integration/test_conversation_state.py::TestUserIsolation::test_conversation_list_isolation PASSED
tests/integration/test_conversation_state.py::TestUserIsolation::test_cascade_delete_isolates_user_data PASSED
tests/integration/test_conversation_state.py::TestEdgeCases::test_retrieving_nonexistent_conversation PASSED
tests/integration/test_conversation_state.py::TestEdgeCases::test_message_with_empty_content PASSED
tests/integration/test_conversation_state.py::TestEdgeCases::test_long_message_content PASSED
tests/integration/test_conversation_state.py::TestEdgeCases::test_conversation_with_many_messages PASSED

==== 24 passed in 2.34s ====
```

## Test Statistics

- **Total Tests**: 24
- **Test Classes**: 6
- **Expected Duration**: ~2-3 seconds
- **Database**: In-memory SQLite (fast, no external deps)

## What These Tests Verify

✅ **Conversation Creation**: Valid UUIDs generated, database persistence
✅ **Message Persistence**: User/assistant messages saved correctly
✅ **Context Retrieval**: History fetched in chronological order
✅ **Stateless Reconstruction**: ⭐ Conversation survives server restarts
✅ **User Isolation**: Users can't access other users' data
✅ **Edge Cases**: Empty content, long messages, many messages

## Troubleshooting

### Import Errors

```bash
# Ensure you're in the backend directory
cd /home/xdev/Hackhthon-II/phase-III/backend

# Install dependencies
pip install -e ".[dev]"
```

### ModuleNotFoundError: No module named 'pytest'

```bash
pip install pytest pytest-asyncio aiosqlite
```

### Tests Run Slowly

This is normal for the first run. Subsequent runs should be fast (~2-3 seconds).

### AsyncIO Mode Warnings

The pyproject.toml is configured with `asyncio_mode = "auto"`, so no warnings should appear. If you see warnings, ensure pytest-asyncio is installed:

```bash
pip install pytest-asyncio>=0.21.0
```

## Related Documentation

- **Full Documentation**: `tests/integration/README.md`
- **Task Summary**: `T025_COMPLETION_SUMMARY.md`
- **Source Code**: `src/api/chat.py`

## Next Steps

1. ✅ Run all tests and verify they pass
2. ✅ Check test coverage with `--cov` flag
3. ✅ Review test code to understand stateless architecture
4. ✅ Integrate into CI/CD pipeline

---

**Success Criteria**: All 24 tests pass, confirming stateless conversation architecture works correctly. 🎯
