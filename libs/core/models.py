"""Data models for dashboard"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import time


@dataclass
class PaneInfo:
    """Information about a tmux pane with detailed metrics"""
    id: str
    command: str
    is_claude: bool = False
    is_controller: bool = False
    
    # Extended pane information
    current_task: Optional[str] = None
    idle_time: float = 0.0  # seconds since last activity
    last_activity: Optional[datetime] = None
    cpu_usage: float = 0.0  # percentage
    memory_usage: float = 0.0  # MB
    pid: Optional[int] = None
    running_time: float = 0.0  # seconds since pane started
    status: str = "unknown"  # active, idle, sleeping, etc.
    
    # Activity tracking
    activity_score: float = 0.0  # 0-100 based on recent activity
    last_output: Optional[str] = None
    output_lines: int = 0
    
    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.now()
    
    def update_activity(self, new_output: str = None):
        """Update activity tracking"""
        self.last_activity = datetime.now()
        self.idle_time = 0.0
        if new_output:
            self.last_output = new_output
            self.output_lines += 1
    
    def calculate_idle_time(self) -> float:
        """Calculate current idle time in seconds"""
        if self.last_activity:
            self.idle_time = (datetime.now() - self.last_activity).total_seconds()
        return self.idle_time


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
                            'is_controller': p.is_controller,
                            'current_task': p.current_task,
                            'idle_time': p.idle_time,
                            'last_activity': p.last_activity.isoformat() if p.last_activity else None,
                            'cpu_usage': p.cpu_usage,
                            'memory_usage': p.memory_usage,
                            'pid': p.pid,
                            'running_time': p.running_time,
                            'status': p.status,
                            'activity_score': p.activity_score,
                            'last_output': p.last_output,
                            'output_lines': p.output_lines
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