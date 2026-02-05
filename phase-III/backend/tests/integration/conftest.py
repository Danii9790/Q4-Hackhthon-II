"""
Pytest configuration for integration tests.

This file ensures pytest can properly discover and run integration tests.
"""

import pytest

# Configure pytest markers for integration tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
