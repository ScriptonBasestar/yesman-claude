"""Core modules for Yesman Claude

This module provides core functionality shared between different dashboard implementations.
"""

from .claude_manager import ClaudeManager
from .content_collector import ClaudeContentCollector
from .models import DashboardStats, SessionInfo
from .prompt_detector import ClaudePromptDetector
from .session_manager import SessionManager

__all__ = [
    "SessionManager",
    "ClaudeManager",
    "SessionInfo",
    "DashboardStats",
    "ClaudeContentCollector",
    "ClaudePromptDetector",
]
