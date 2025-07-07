"""Dashboard widgets for session visualization and interaction"""

from .session_browser import SessionBrowser
from .activity_heatmap import ActivityHeatmap
from .project_health import ProjectHealthWidget
from .git_activity import GitActivityWidget
from .progress_tracker import ProgressTracker

__all__ = [
    'SessionBrowser',
    'ActivityHeatmap',
    'ProjectHealthWidget',
    'GitActivityWidget',
    'ProgressTracker'
]