"""Data models for dashboard"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskPhase(Enum):
    """Phases of a Claude task execution"""

    STARTING = "starting"
    ANALYZING = "analyzing"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    COMPLETING = "completing"
    COMPLETED = "completed"
    IDLE = "idle"


@dataclass
class TaskProgress:
    """Progress tracking for a Claude task"""

    phase: TaskPhase = TaskPhase.IDLE
    phase_progress: float = 0.0  # 0-100% progress within current phase
    overall_progress: float = 0.0  # 0-100% overall task progress

    # Activity metrics
    files_created: int = 0
    files_modified: int = 0
    lines_added: int = 0
    lines_removed: int = 0

    # Command execution metrics
    commands_executed: int = 0
    commands_succeeded: int = 0
    commands_failed: int = 0

    # Time metrics
    start_time: datetime | None = None
    phase_start_time: datetime | None = None
    active_duration: float = 0.0  # seconds of active work
    idle_duration: float = 0.0  # seconds of idle time

    # TODO tracking
    todos_identified: int = 0
    todos_completed: int = 0

    def update_phase(self, new_phase: TaskPhase):
        """Update to a new phase"""
        self.phase = new_phase
        self.phase_start_time = datetime.now()
        self.phase_progress = 0.0
        self._recalculate_overall_progress()

    def _recalculate_overall_progress(self):
        """Recalculate overall progress based on phase"""
        phase_weights = {
            TaskPhase.STARTING: 0.1,
            TaskPhase.ANALYZING: 0.2,
            TaskPhase.IMPLEMENTING: 0.5,
            TaskPhase.TESTING: 0.15,
            TaskPhase.COMPLETING: 0.05,
            TaskPhase.COMPLETED: 1.0,
            TaskPhase.IDLE: 0.0,
        }

        base_progress = 0.0
        phase_list = list(TaskPhase)
        current_phase_index = phase_list.index(self.phase)

        for phase, weight in phase_weights.items():
            phase_index = phase_list.index(phase)
            if phase_index < current_phase_index:
                base_progress += weight
            elif phase_index == current_phase_index:
                base_progress += weight * (self.phase_progress / 100.0)
                break

        self.overall_progress = round(min(100.0, base_progress * 100), 1)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "phase": self.phase.value,
            "phase_progress": self.phase_progress,
            "overall_progress": self.overall_progress,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "commands_executed": self.commands_executed,
            "commands_succeeded": self.commands_succeeded,
            "commands_failed": self.commands_failed,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "active_duration": self.active_duration,
            "idle_duration": self.idle_duration,
            "todos_identified": self.todos_identified,
            "todos_completed": self.todos_completed,
        }


@dataclass
class SessionProgress:
    """Overall progress tracking for a session"""

    session_name: str
    tasks: list[TaskProgress] = field(default_factory=list)
    current_task_index: int = 0

    # Aggregate metrics
    total_files_changed: int = 0
    total_commands: int = 0
    total_todos_completed: int = 0
    session_start_time: datetime | None = None
    last_update_time: datetime | None = None

    def get_current_task(self) -> TaskProgress | None:
        """Get the current task progress"""
        if 0 <= self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None

    def add_task(self) -> TaskProgress:
        """Add a new task and make it current"""
        task = TaskProgress()
        task.start_time = datetime.now()
        self.tasks.append(task)
        self.current_task_index = len(self.tasks) - 1
        if not self.session_start_time:
            self.session_start_time = datetime.now()
        return task

    def calculate_overall_progress(self) -> float:
        """Calculate overall session progress"""
        if not self.tasks:
            return 0.0

        total_progress = sum(task.overall_progress for task in self.tasks)
        return total_progress / len(self.tasks)

    def update_aggregates(self):
        """Update aggregate metrics from all tasks"""
        self.total_files_changed = sum(task.files_created + task.files_modified for task in self.tasks)
        self.total_commands = sum(task.commands_executed for task in self.tasks)
        self.total_todos_completed = sum(task.todos_completed for task in self.tasks)
        self.last_update_time = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_name": self.session_name,
            "current_task_index": self.current_task_index,
            "tasks": [task.to_dict() for task in self.tasks],
            "overall_progress": self.calculate_overall_progress(),
            "total_files_changed": self.total_files_changed,
            "total_commands": self.total_commands,
            "total_todos_completed": self.total_todos_completed,
            "session_start_time": (self.session_start_time.isoformat() if self.session_start_time else None),
            "last_update_time": (self.last_update_time.isoformat() if self.last_update_time else None),
        }


@dataclass
class PaneInfo:
    """Information about a tmux pane with detailed metrics"""

    id: str
    command: str
    is_claude: bool = False
    is_controller: bool = False

    # Extended pane information
    current_task: str | None = None
    idle_time: float = 0.0  # seconds since last activity
    last_activity: datetime | None = None
    cpu_usage: float = 0.0  # percentage
    memory_usage: float = 0.0  # MB
    pid: int | None = None
    running_time: float = 0.0  # seconds since pane started
    status: str = "unknown"  # active, idle, sleeping, etc.

    # Activity tracking
    activity_score: float = 0.0  # 0-100 based on recent activity
    last_output: str | None = None
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
    panes: list[PaneInfo]


@dataclass
class SessionInfo:
    """Information about a tmux session"""

    project_name: str
    session_name: str
    template: str
    exists: bool
    status: str  # 'running' or 'stopped'
    windows: list[WindowInfo]
    controller_status: str  # 'running', 'not running', 'unknown'
    progress: SessionProgress | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for compatibility"""
        return {
            "project_name": self.project_name,
            "session_name": self.session_name,
            "template": self.template,
            "exists": self.exists,
            "status": self.status,
            "windows": [
                {
                    "name": w.name,
                    "index": w.index,
                    "panes": [
                        {
                            "id": p.id,
                            "command": p.command,
                            "is_claude": p.is_claude,
                            "is_controller": p.is_controller,
                            "current_task": p.current_task,
                            "idle_time": p.idle_time,
                            "last_activity": (p.last_activity.isoformat() if p.last_activity else None),
                            "cpu_usage": p.cpu_usage,
                            "memory_usage": p.memory_usage,
                            "pid": p.pid,
                            "running_time": p.running_time,
                            "status": p.status,
                            "activity_score": p.activity_score,
                            "last_output": p.last_output,
                            "output_lines": p.output_lines,
                        }
                        for p in w.panes
                    ],
                }
                for w in self.windows
            ],
            "controller_status": self.controller_status,
            "progress": self.progress.to_dict() if self.progress else None,
        }


@dataclass
class DashboardStats:
    """Dashboard statistics"""

    total_sessions: int
    running_sessions: int
    active_controllers: int

    @classmethod
    def from_sessions(cls, sessions: list[SessionInfo]) -> "DashboardStats":
        """Create stats from session list"""
        total = len(sessions)
        running = sum(1 for s in sessions if s.status == "running")
        controllers = sum(1 for s in sessions if s.controller_status == "running")
        return cls(total, running, controllers)
