# Copyright notice.

from .activity_heatmap import ActivityHeatmapGenerator
from .agent_monitor import AgentMonitor
from .git_activity import GitActivityWidget
from .progress_tracker import ProgressTracker
from .project_health import ProjectHealth
from .session_browser import SessionBrowser

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Dashboard widgets for session visualization and interaction."""


__all__ = [
    "ActivityHeatmapGenerator",
    "AgentMonitor",
    "GitActivityWidget",
    "ProgressTracker",
    "ProjectHealth",
    "SessionBrowser",
]
