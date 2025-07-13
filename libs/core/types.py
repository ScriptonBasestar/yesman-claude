#!/usr/bin/env python3
"""
Type definitions and type hints for Yesman-Claude
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from typing_extensions import Literal, TypedDict

# Session-related types
SessionName = str
WindowName = str
PaneName = str
CommandString = str
DirectoryPath = str

# Status types
SessionStatusType = Literal["running", "stopped", "unknown", "starting", "stopping"]
ControllerStatusType = Literal["idle", "monitoring", "responding", "error", "disabled"]
HealthStatusType = Literal["healthy", "warning", "critical", "unknown"]


# Configuration types
class WindowConfig(TypedDict, total=False):
    """Window configuration structure"""

    window_name: str
    layout: Optional[str]
    start_directory: Optional[str]
    panes: List["PaneConfig"]


class PaneConfig(TypedDict, total=False):
    """Pane configuration structure"""

    shell_command: List[str]
    start_directory: Optional[str]
    focus: Optional[bool]


class SessionConfig(TypedDict, total=False):
    """Complete session configuration structure"""

    session_name: str
    start_directory: Optional[str]
    windows: List[WindowConfig]
    before_script: Optional[str]
    after_script: Optional[str]


class ProjectConfig(TypedDict, total=False):
    """Project configuration structure"""

    template_name: Optional[str]
    override: SessionConfig


class ProjectsConfig(TypedDict):
    """Projects configuration file structure"""

    sessions: Dict[str, ProjectConfig]


# Runtime data types
@dataclass
class SessionInfo:
    """Runtime session information"""

    session_name: str
    status: SessionStatusType
    windows: List["WindowInfo"]
    created_at: Optional[float] = None
    last_activity: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_activity is None:
            self.last_activity = time.time()


@dataclass
class WindowInfo:
    """Runtime window information"""

    window_name: str
    window_index: int
    active: bool = False
    panes: List["PaneInfo"] = None

    def __post_init__(self):
        if self.panes is None:
            self.panes = []


@dataclass
class PaneInfo:
    """Runtime pane information"""

    pane_id: str
    pane_index: int
    active: bool = False
    current_path: Optional[str] = None
    current_command: Optional[str] = None


# Controller and monitoring types
@dataclass
class ControllerState:
    """Controller state information"""

    session_name: str
    status: ControllerStatusType
    auto_next_enabled: bool = True
    last_activity: Optional[float] = None
    response_count: int = 0
    error_count: int = 0

    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = time.time()


@dataclass
class PromptDetection:
    """Detected prompt information"""

    prompt_type: str
    confidence: float
    matched_pattern: str
    suggested_response: Optional[str] = None
    context: Optional[str] = None


@dataclass
class AutoResponse:
    """Auto-response action"""

    response_text: str
    confidence: float
    pattern_used: str
    timestamp: float
    success: bool = False

    def __post_init__(self):
        if hasattr(self, "timestamp") and self.timestamp is None:
            self.timestamp = time.time()


# Health monitoring types
class HealthCategory(Enum):
    """Health check categories"""

    BUILD = "build"
    TESTS = "tests"
    DEPENDENCIES = "dependencies"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    GIT = "git"
    DOCUMENTATION = "documentation"


@dataclass
class HealthScore:
    """Health score for a category"""

    category: HealthCategory
    score: float  # 0-100
    status: HealthStatusType
    details: Dict[str, Any]
    last_checked: float

    def __post_init__(self):
        if hasattr(self, "last_checked") and self.last_checked is None:
            self.last_checked = time.time()


@dataclass
class ProjectHealth:
    """Overall project health"""

    project_path: str
    overall_score: float
    category_scores: Dict[HealthCategory, HealthScore]
    last_updated: float
    trends: List["HealthTrend"]

    def __post_init__(self):
        if hasattr(self, "last_updated") and self.last_updated is None:
            self.last_updated = time.time()
        if not hasattr(self, "trends") or self.trends is None:
            self.trends = []


@dataclass
class HealthTrend:
    """Health trend data point"""

    timestamp: float
    score: float
    category: Optional[HealthCategory] = None


# Cache types
CacheKey = str
CacheValue = Any
CacheTTL = float


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    key: CacheKey
    value: CacheValue
    created_at: float
    ttl: CacheTTL
    access_count: int = 0
    last_accessed: Optional[float] = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return time.time() > (self.created_at + self.ttl)

    def touch(self) -> None:
        """Update access information"""
        self.access_count += 1
        self.last_accessed = time.time()


# API types
class APIResponse(TypedDict):
    """Standard API response structure"""

    success: bool
    data: Optional[Any]
    error: Optional[str]
    timestamp: float


class SessionAPIData(TypedDict):
    """Session data for API responses"""

    session_name: str
    status: SessionStatusType
    windows: List[Dict[str, Any]]
    created_at: Optional[float]
    last_activity: Optional[float]


class ControllerAPIData(TypedDict):
    """Controller data for API responses"""

    session_name: str
    status: ControllerStatusType
    auto_next_enabled: bool
    last_activity: Optional[float]
    response_count: int
    error_count: int


# Callback and handler types
EventCallback = Callable[[str, Dict[str, Any]], None]
ErrorHandler = Callable[[Exception], None]
ValidationFunction = Callable[[Any], bool]
TransformFunction = Callable[[Any], Any]

# Logging types
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogEntry = Dict[str, Any]

# File system types
FilePath = str
DirectoryPath = str
FileName = str
FileExtension = str

# Network types
HostAddress = str
PortNumber = int
URL = str
HTTPMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]

# Template types
TemplateName = str
TemplateVariable = str
TemplateValue = Union[str, int, float, bool]
TemplateContext = Dict[TemplateVariable, TemplateValue]

# Validation types
ValidationResult = Tuple[bool, Optional[str]]  # (is_valid, error_message)
ValidationRules = Dict[str, ValidationFunction]

# Configuration merge strategies
MergeStrategy = Literal["override", "merge", "append"]

# Command execution types
CommandResult = Tuple[int, str, str]  # (return_code, stdout, stderr)
CommandTimeout = Optional[float]


# Statistics and metrics types
@dataclass
class PerformanceMetrics:
    """Performance metrics data"""

    operation_name: str
    start_time: float
    end_time: float
    success: bool
    error_message: Optional[str] = None

    @property
    def duration(self) -> float:
        """Get operation duration in seconds"""
        return self.end_time - self.start_time


@dataclass
class UsageStatistics:
    """Usage statistics data"""

    total_sessions_created: int = 0
    total_commands_executed: int = 0
    total_responses_automated: int = 0
    total_errors: int = 0
    uptime_seconds: float = 0
    last_reset: float = 0

    def __post_init__(self):
        if self.last_reset == 0:
            self.last_reset = time.time()


# Update forward references
WindowConfig.__annotations__["panes"] = List[PaneConfig]
ProjectHealth.__annotations__["trends"] = List[HealthTrend]
