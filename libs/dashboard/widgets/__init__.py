"""Dashboard widgets for session visualization and interaction"""

from .session_browser import SessionBrowser
from .activity_heatmap import ActivityHeatmapGenerator
from .project_health import ProjectHealth
from .git_activity import GitActivityWidget
from .progress_tracker import ProgressTracker
from .agent_monitor import AgentMonitor

__all__ = [
    'SessionBrowser',
    'ActivityHeatmapGenerator',
    'ProjectHealth',
    'GitActivityWidget',
    'ProgressTracker',
    'AgentMonitor'
]