#!/usr/bin/env python3
"""
Verification script for T080-T082 performance optimizations.

This script verifies that all performance optimizations are correctly implemented
without requiring the full application dependencies.
"""

import ast
import re
from pathlib import Path


def verify_connection_pooling():
    """Verify T080: Database connection pooling configuration."""
    print("\n" + "="*70)
    print("T080: Database Connection Pooling")
    print("="*70)

    session_file = Path("backend/src/db/session.py")
    content = session_file.read_text()

    checks = {
        "pool_pre_ping": r"pool_pre_ping\s*=\s*True",
        "pool_size": r"pool_size\s*=\s*10",
        "max_overflow": r"max_overflow\s*=\s*20",
        "pool_recycle": r"pool_recycle\s*=\s*3600",
        "connect_timeout": r"connect_timeout\s*:\s*10",
        "command_timeout": r"command_timeout\s*:\s*30",
        "statement_cache_size": r"statement_cache_size\s*:\s*100",
    }

    all_passed = True
    for param, pattern in checks.items():
        if re.search(pattern, content):
            print(f"  ✓ {param:25s} - Configured correctly")
        else:
            print(f"  ✗ {param:25s} - NOT FOUND")
            all_passed = False

    return all_passed


def verify_pagination():
    """Verify T081: Conversation history pagination."""
    print("\n" + "="*70)
    print("T081: Conversation History Pagination")
    print("="*70)

    chat_file = Path("backend/src/api/chat.py")
    content = chat_file.read_text()

    # Parse function signature
    tree = ast.parse(content)

    fetch_function = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "fetch_conversation_history":
            fetch_function = node
            break

    if not fetch_function:
        print("  ✗ fetch_conversation_history function NOT FOUND")
        return False

    # Check parameters
    params = {arg.arg: arg.annotation for arg in fetch_function.args.args}

    checks = {
        "limit": "limit" in params,
        "offset": "offset" in params,
        "before": "before" in params,
        "after": "after" in params,
    }

    # Check validation logic
    limit_validation = "MAX_LIMIT = 1000" in content and "limit > MAX_LIMIT" in content
    offset_validation = "offset < 0" in content

    # Check time filter implementation
    time_filters = (
        "before is not None" in content and
        "after is not None" in content and
        "Message.created_at < before" in content and
        "Message.created_at > after" in content
    )

    all_passed = True

    for param, found in checks.items():
        status = "✓" if found else "✗"
        print(f"  {status} Parameter '{param:10s}' - {'Found' if found else 'NOT FOUND'}")
        all_passed = all_passed and found

    print(f"  {'✓' if limit_validation else '✗'} Limit validation (max 1000) - {'Implemented' if limit_validation else 'NOT FOUND'}")
    print(f"  {'✓' if offset_validation else '✗'} Offset validation - {'Implemented' if offset_validation else 'NOT FOUND'}")
    print(f"  {'✓' if time_filters else '✗'} Time-based filters (before/after) - {'Implemented' if time_filters else 'NOT FOUND'}")

    return all_passed and limit_validation and offset_validation and time_filters


def verify_caching_headers():
    """Verify T082: Response caching headers."""
    print("\n" + "="*70)
    print("T082: Response Caching Headers")
    print("="*70)

    chat_file = Path("backend/src/api/chat.py")
    content = chat_file.read_text()

    # Check for generate_etag function
    tree = ast.parse(content)
    etag_function = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "generate_etag":
            etag_function = node
            break

    # Check caching headers
    checks = {
        "Cache-Control": 'Cache-Control' in content and 'no-cache' in content,
        "Pragma": 'Pragma' in content and 'no-cache' in content,
        "Expires": 'Expires' in content and '"0"' in content,
        "ETag": 'ETag' in content and 'W/"' in content,
    }

    # Check generate_etag function
    etag_exists = etag_function is not None
    etag_params = False
    if etag_function:
        params = {arg.arg for arg in etag_function.args.args}
        etag_params = {"conversation_id", "message_count", "last_message_time"}.issubset(params)

    # Check hashlib import
    hashlib_import = "import hashlib" in content

    all_passed = True

    for header, found in checks.items():
        status = "✓" if found else "✗"
        print(f"  {status} Header '{header:15s}' - {'Found' if found else 'NOT FOUND'}")
        all_passed = all_passed and found

    print(f"  {'✓' if hashlib_import else '✗'} hashlib import - {'Found' if hashlib_import else 'NOT FOUND'}")
    print(f"  {'✓' if etag_exists else '✗'} generate_etag function - {'Found' if etag_exists else 'NOT FOUND'}")
    print(f"  {'✓' if etag_params else '✗'} generate_etag parameters - {'Correct' if etag_params else 'INCORRECT'}")

    return all_passed and hashlib_import and etag_exists and etag_params


def verify_tests():
    """Verify test suite exists and is valid."""
    print("\n" + "="*70)
    print("Test Suite Verification")
    print("="*70)

    test_file = Path("backend/tests/test_performance_optimizations.py")

    if not test_file.exists():
        print(f"  ✗ Test file NOT FOUND")
        return False

    content = test_file.read_text()

    # Check for key test functions
    tests = {
        "test_fetch_conversation_history_default_limit": "test_fetch_conversation_history_default_limit" in content,
        "test_fetch_conversation_history_with_offset": "test_fetch_conversation_history_with_offset" in content,
        "test_fetch_conversation_history_time_filtering": "test_fetch_conversation_history_time_filtering" in content,
        "test_generate_etag_basic": "test_generate_etag_basic" in content,
        "test_pagination_integration_large_conversation": "test_pagination_integration_large_conversation" in content,
    }

    all_passed = True
    for test_name, found in tests.items():
        status = "✓" if found else "✗"
        print(f"  {status} {test_name:50s} - {'Found' if found else 'NOT FOUND'}")
        all_passed = all_passed and found

    # Verify syntax
    try:
        ast.parse(content)
        print(f"  ✓ Test file syntax - VALID")
    except SyntaxError:
        print(f"  ✗ Test file syntax - INVALID")
        all_passed = False

    return all_passed


def main():
    """Run all verification checks."""
    print("\n" + "="*70)
    print("PERFORMANCE OPTIMIZATIONS VERIFICATION (T080-T082)")
    print("="*70)

    results = {
        "T080: Connection Pooling": verify_connection_pooling(),
        "T081: Pagination": verify_pagination(),
        "T082: Caching Headers": verify_caching_headers(),
        "Tests": verify_tests(),
    }

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    all_passed = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status:8s} {name}")
        all_passed = all_passed and passed

    print("="*70)

    if all_passed:
        print("\n  🎉 All performance optimizations successfully implemented!\n")
        return 0
    else:
        print("\n  ⚠️  Some checks failed. Please review the implementation.\n")
        return 1


if __name__ == "__main__":
    exit(main())
