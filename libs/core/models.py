"""Data models for dashboard"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class PaneInfo:
    """Information about a tmux pane"""
    id: str
    command: str
    is_claude: bool = False
    is_controller: bool = False


@dataclass
class WindowInfo:
    """Information about a tmux window"""
    name: str
    index: str
    panes: List[PaneInfo]


@dataclass
class SessionInfo:
    """Information about a tmux session"""
    project_name: str
    session_name: str
    template: str
    exists: bool
    status: str  # 'running' or 'stopped'
    windows: List[WindowInfo]
    controller_status: str  # 'running', 'not running', 'unknown'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for compatibility"""
        return {
            'project_name': self.project_name,
            'session_name': self.session_name,
            'template': self.template,
            'exists': self.exists,
            'status': self.status,
            'windows': [
                {
                    'name': w.name,
                    'index': w.index,
                    'panes': [
                        {
                            'id': p.id,
                            'command': p.command,
                            'is_claude': p.is_claude,
                            'is_controller': p.is_controller
                        } for p in w.panes
                    ]
                } for w in self.windows
            ],
            'controller_status': self.controller_status
        }


@dataclass
class DashboardStats:
    """Dashboard statistics"""
    total_sessions: int
    running_sessions: int
    active_controllers: int
    
    @classmethod
    def from_sessions(cls, sessions: List[SessionInfo]) -> 'DashboardStats':
        """Create stats from session list"""
        total = len(sessions)
        running = sum(1 for s in sessions if s.status == 'running')
        controllers = sum(1 for s in sessions if s.controller_status == 'running')
        return cls(total, running, controllers)