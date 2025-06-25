"""Dashboard module for Yesman Claude

This module provides a TUI dashboard for monitoring tmux sessions and controllers.
"""

from .app import DashboardApp
from .runner import run_dashboard

__all__ = ['DashboardApp', 'run_dashboard']