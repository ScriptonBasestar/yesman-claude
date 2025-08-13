#!/usr/bin/env python3

"""Error handling package for Yesman Claude Agent.

This package provides intelligent error handling capabilities including:
- Context-aware error processing
- User-friendly error messages
- Automated resolution suggestions
- Integration with monitoring systems
"""

from .contextual_error_handler import (
    ContextualErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    UserFriendlyError,
)

__all__ = [
    "ContextualErrorHandler",
    "UserFriendlyError",
    "ErrorSeverity",
    "ErrorCategory",
]
