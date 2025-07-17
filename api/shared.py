"""Shared instances for API routers to ensure singleton behavior."""

from libs.core.claude_manager import ClaudeManager

# Shared ClaudeManager instance to ensure consistency across all API endpoints
# This ensures that controller state is maintained properly across different routers
claude_manager = ClaudeManager()
