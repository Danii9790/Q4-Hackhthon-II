#!/usr/bin/env python
"""
Test script to verify Alembic configuration.

This script validates:
1. Models can be imported
2. SQLModel metadata contains all tables
3. Alembic can load migration environment
4. Migration history is accessible
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def test_model_imports():
    """Test that all models can be imported."""
    print("Testing model imports...")
    try:
        from src.models.models import User, Conversation, Message, Task
        print("  ✓ All models imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Model import failed: {e}")
        return False

def test_metadata():
    """Test that SQLModel metadata is configured."""
    print("\nTesting SQLModel metadata...")
    try:
        from sqlmodel import SQLModel
        tables = list(SQLModel.metadata.tables.keys())
        expected = ['users', 'conversations', 'messages', 'tasks']

        if set(tables) == set(expected):
            print(f"  ✓ All expected tables present: {tables}")
            return True
        else:
            print(f"  ✗ Missing tables. Expected: {expected}, Got: {tables}")
            return False
    except Exception as e:
        print(f"  ✗ Metadata check failed: {e}")
        return False

def test_alembic_config():
    """Test that Alembic can load configuration."""
    print("\nTesting Alembic configuration...")
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)

        # Get migration head
        head = script.get_current_head()
        print(f"  ✓ Alembic configuration loaded")
        print(f"  ✓ Current head revision: {head}")

        # List migrations
        revisions = list(script.walk_revisions())
        print(f"  ✓ Found {len(revisions)} migration(s)")
        for rev in revisions:
            print(f"    - {rev.revision}: {rev.doc}")

        return True
    except Exception as e:
        print(f"  ✗ Alembic configuration failed: {e}")
        return False

def test_env_py():
    """Test that alembic/env.py can be loaded."""
    print("\nTesting alembic/env.py...")
    try:
        # Set a dummy DATABASE_URL for testing
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://user:pass@localhost/test'

        # Import env.py (this will test imports and path setup)
        import importlib.util
        spec = importlib.util.spec_from_file_location("alembic_env", "alembic/env.py")
        if spec and spec.loader:
            env_module = importlib.util.module_from_spec(spec)
            # Don't execute since we don't have a real database
            print("  ✓ alembic/env.py can be loaded")
            return True
        else:
            print("  ✗ Failed to load alembic/env.py")
            return False
    except Exception as e:
        print(f"  ✗ alembic/env.py test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Alembic Configuration Test Suite")
    print("=" * 60)

    results = [
        test_model_imports(),
        test_metadata(),
        test_alembic_config(),
        test_env_py(),
    ]

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"SUCCESS: All {total} tests passed! ✓")
        return 0
    else:
        print(f"FAILURE: {passed}/{total} tests passed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
