"""Dashboard widgets for session visualization and interaction."""

from .activity_heatmap import ActivityHeatmapGenerator
from .agent_monitor import AgentMonitor
from .git_activity import GitActivityWidget
from .progress_tracker import ProgressTracker
from .project_health import ProjectHealth
from .session_browser import SessionBrowser

__all__ = [
    "SessionBrowser",
    "ActivityHeatmapGenerator",
    "ProjectHealth",
    "GitActivityWidget",
    "ProgressTracker",
    "AgentMonitor",
]
