"""Widget Data Models
Common data models used across all renderers for consistent data representation.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SessionStatus(Enum):
    """Session status enumeration."""

    ACTIVE = "active"
    IDLE = "idle"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class HealthLevel(Enum):
    """Health level enumeration with score ranges."""

    EXCELLENT = (90, 100, "excellent", "🟢")
    GOOD = (70, 89, "good", "🟡")
    WARNING = (50, 69, "warning", "🟠")
    CRITICAL = (0, 49, "critical", "🔴")
    UNKNOWN = (-1, -1, "unknown", "⚪")

    def __init__(self, min_score: int, max_score: int, label: str, emoji: str):
        self.min_score = min_score
        self.max_score = max_score
        self.label = label
        self.emoji = emoji

    @classmethod
    def from_score(cls, score: int) -> "HealthLevel":
        """Get health level from numeric score."""
        if score < 0:
            return cls.UNKNOWN
        for level in [cls.EXCELLENT, cls.GOOD, cls.WARNING, cls.CRITICAL]:
            if level.min_score <= score <= level.max_score:
                return level
        return cls.UNKNOWN


class ActivityType(Enum):
    """Activity type enumeration."""

    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    COMMAND_EXECUTED = "command_executed"
    TEST_RUN = "test_run"
    BUILD = "build"
    COMMIT = "commit"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


class ProgressPhase(Enum):
    """Progress phase enumeration."""

    STARTING = "starting"
    ANALYZING = "analyzing"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    COMPLETING = "completing"
    COMPLETED = "completed"
    IDLE = "idle"
    ERROR = "error"


@dataclass
class WindowData:
    """Window information within a session."""

    id: str
    name: str
    active: bool = False
    panes: int = 0
    layout: str = "even-horizontal"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionData:
    """Session information model."""

    name: str
    id: str
    status: SessionStatus
    created_at: datetime
    last_activity: datetime | None = None
    windows: list[WindowData] = field(default_factory=list)
    panes: int = 0
    claude_active: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["last_activity"] = self.last_activity.isoformat() if self.last_activity else None

        # Convert windows
        data["windows"] = [
            {
                **window,
                "metadata": window.get("metadata", {}),
            }
            for window in data["windows"]
        ]

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionData":
        """Create from dictionary."""
        # Parse datetime fields
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

        last_activity = None
        if data.get("last_activity"):
            last_activity = datetime.fromisoformat(data["last_activity"].replace("Z", "+00:00"))

        # Parse status
        status = SessionStatus(data.get("status", SessionStatus.IDLE.value))

        # Parse windows
        windows = []
        for window_data in data.get("windows", []):
            windows.append(
                WindowData(
                    id=window_data.get("id", ""),
                    name=window_data.get("name", ""),
                    active=window_data.get("active", False),
                    panes=window_data.get("panes", 0),
                    layout=window_data.get("layout", "even-horizontal"),
                    metadata=window_data.get("metadata", {}),
                )
            )

        return cls(
            name=data["name"],
            id=data["id"],
            status=status,
            created_at=created_at,
            last_activity=last_activity,
            windows=windows,
            panes=data.get("panes", 0),
            claude_active=data.get("claude_active", False),
            metadata=data.get("metadata", {}),
            cpu_usage=data.get("cpu_usage", 0.0),
            memory_usage=data.get("memory_usage", 0.0),
        )


@dataclass
class HealthCategoryData:
    """Health data for a specific category."""

    category: str
    score: int
    level: HealthLevel
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    last_checked: datetime | None = None


@dataclass
class HealthData:
    """Health information model."""

    overall_score: int
    overall_level: HealthLevel
    categories: list[HealthCategoryData] = field(default_factory=list)
    last_updated: datetime | None = None
    project_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["overall_level"] = {
            "label": self.overall_level.label,
            "emoji": self.overall_level.emoji,
            "min_score": self.overall_level.min_score,
            "max_score": self.overall_level.max_score,
        }
        data["last_updated"] = self.last_updated.isoformat() if self.last_updated else None

        # Convert categories
        data["categories"] = []
        for cat in self.categories:
            cat_data = asdict(cat)
            cat_data["level"] = {
                "label": cat.level.label,
                "emoji": cat.level.emoji,
                "min_score": cat.level.min_score,
                "max_score": cat.level.max_score,
            }
            cat_data["last_checked"] = cat.last_checked.isoformat() if cat.last_checked else None
            data["categories"].append(cat_data)

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthData":
        """Create from dictionary."""
        # Parse datetime
        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))

        # Parse overall level
        overall_level = HealthLevel.from_score(data.get("overall_score", 0))

        # Parse categories
        categories = []
        for cat_data in data.get("categories", []):
            last_checked = None
            if cat_data.get("last_checked"):
                last_checked = datetime.fromisoformat(cat_data["last_checked"].replace("Z", "+00:00"))

            level = HealthLevel.from_score(cat_data.get("score", 0))

            categories.append(
                HealthCategoryData(
                    category=cat_data.get("category", ""),
                    score=cat_data.get("score", 0),
                    level=level,
                    message=cat_data.get("message", ""),
                    details=cat_data.get("details", {}),
                    last_checked=last_checked,
                )
            )

        return cls(
            overall_score=data.get("overall_score", 0),
            overall_level=overall_level,
            categories=categories,
            last_updated=last_updated,
            project_path=data.get("project_path", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ActivityEntry:
    """Single activity entry."""

    timestamp: datetime
    activity_type: ActivityType
    description: str
    details: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActivityData:
    """Activity information model."""

    entries: list[ActivityEntry] = field(default_factory=list)
    total_activities: int = 0
    active_days: int = 0
    activity_rate: float = 0.0
    current_streak: int = 0
    longest_streak: int = 0
    avg_per_day: float = 0.0
    date_range: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)

        # Convert entries
        data["entries"] = []
        for entry in self.entries:
            entry_data = asdict(entry)
            entry_data["timestamp"] = entry.timestamp.isoformat()
            entry_data["activity_type"] = entry.activity_type.value
            data["entries"].append(entry_data)

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActivityData":
        """Create from dictionary."""
        # Parse entries
        entries = []
        for entry_data in data.get("entries", []):
            timestamp = datetime.fromisoformat(entry_data["timestamp"].replace("Z", "+00:00"))
            activity_type = ActivityType(entry_data.get("activity_type", ActivityType.FILE_MODIFIED.value))

            entries.append(
                ActivityEntry(
                    timestamp=timestamp,
                    activity_type=activity_type,
                    description=entry_data.get("description", ""),
                    details=entry_data.get("details", {}),
                    metadata=entry_data.get("metadata", {}),
                )
            )

        return cls(
            entries=entries,
            total_activities=data.get("total_activities", 0),
            active_days=data.get("active_days", 0),
            activity_rate=data.get("activity_rate", 0.0),
            current_streak=data.get("current_streak", 0),
            longest_streak=data.get("longest_streak", 0),
            avg_per_day=data.get("avg_per_day", 0.0),
            date_range=data.get("date_range", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ProgressData:
    """Progress information model."""

    phase: ProgressPhase
    phase_progress: float = 0.0  # 0-100% progress within current phase
    overall_progress: float = 0.0  # 0-100% overall progress

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

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["phase"] = self.phase.value
        data["start_time"] = self.start_time.isoformat() if self.start_time else None
        data["phase_start_time"] = self.phase_start_time.isoformat() if self.phase_start_time else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProgressData":
        """Create from dictionary."""
        # Parse datetime fields
        start_time = None
        if data.get("start_time"):
            start_time = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))

        phase_start_time = None
        if data.get("phase_start_time"):
            phase_start_time = datetime.fromisoformat(data["phase_start_time"].replace("Z", "+00:00"))

        # Parse phase
        phase = ProgressPhase(data.get("phase", ProgressPhase.IDLE.value))

        return cls(
            phase=phase,
            phase_progress=data.get("phase_progress", 0.0),
            overall_progress=data.get("overall_progress", 0.0),
            files_created=data.get("files_created", 0),
            files_modified=data.get("files_modified", 0),
            lines_added=data.get("lines_added", 0),
            lines_removed=data.get("lines_removed", 0),
            commands_executed=data.get("commands_executed", 0),
            commands_succeeded=data.get("commands_succeeded", 0),
            commands_failed=data.get("commands_failed", 0),
            start_time=start_time,
            phase_start_time=phase_start_time,
            active_duration=data.get("active_duration", 0.0),
            idle_duration=data.get("idle_duration", 0.0),
            todos_identified=data.get("todos_identified", 0),
            todos_completed=data.get("todos_completed", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MetricCardData:
    """Metric card display data."""

    title: str
    value: str | int | float
    suffix: str = ""
    trend: float | None = None  # positive/negative trend
    comparison: str | None = None  # comparison text
    color: str = "neutral"
    icon: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetricCardData":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class StatusIndicatorData:
    """Status indicator display data."""

    status: str
    label: str = ""
    color: str = "neutral"
    icon: str = ""
    pulse: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StatusIndicatorData":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ChartDataPoint:
    """Single chart data point."""

    x: str | int | float | datetime
    y: int | float
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartData:
    """Chart display data."""

    title: str
    chart_type: str = "line"  # line, bar, pie, area
    data_points: list[ChartDataPoint] = field(default_factory=list)
    x_label: str = ""
    y_label: str = ""
    colors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)

        # Convert data points
        data["data_points"] = []
        for point in self.data_points:
            point_data = asdict(point)
            if isinstance(point.x, datetime):
                point_data["x"] = point.x.isoformat()
            data["data_points"].append(point_data)

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChartData":
        """Create from dictionary."""
        # Parse data points
        data_points = []
        for point_data in data.get("data_points", []):
            x_value = point_data.get("x")
            # Try to parse datetime if it's a string
            if isinstance(x_value, str):
                try:
                    x_value = datetime.fromisoformat(x_value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass  # Keep as string

            data_points.append(
                ChartDataPoint(
                    x=x_value,
                    y=point_data.get("y", 0),
                    label=point_data.get("label"),
                    metadata=point_data.get("metadata", {}),
                )
            )

        return cls(
            title=data.get("title", ""),
            chart_type=data.get("chart_type", "line"),
            data_points=data_points,
            x_label=data.get("x_label", ""),
            y_label=data.get("y_label", ""),
            colors=data.get("colors", []),
            metadata=data.get("metadata", {}),
        )
