"""
Shared pytest configuration and fixtures for all test suites.

This file provides common configuration for unit, integration, and contract tests.
"""

import pytest
import sys
import os

# Add backend src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "contract: marks tests as contract tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
