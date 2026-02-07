"""
API Dependencies for Todo Application.

This module re-exports authentication dependencies from the dependencies package
for backward compatibility with existing imports.
"""

from src.api.dependencies.auth import get_current_user_id

__all__ = [
    "get_current_user_id",
]
