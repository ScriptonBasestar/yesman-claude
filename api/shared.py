# Copyright notice.

from libs.core.claude_manager import ClaudeManager

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Shared instances for API routers to ensure singleton behavior."""


# Shared ClaudeManager instance to ensure consistency across all API endpoints
# This ensures that controller state is maintained properly across different routers
claude_manager = ClaudeManager()
