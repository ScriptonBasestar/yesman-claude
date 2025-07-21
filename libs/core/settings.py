#!/usr/bin/env python3

# Copyright notice.

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Central settings and configuration management."""


@dataclass
class CacheSettings:
    """Cache configuration settings."""

    ttl: float = 5.0
    max_entries: int = 100
    enable_compression: bool = True
    cleanup_interval: int = 300  # 5 minutes


@dataclass
class LoggingSettings:
    """Logging configuration settings."""

    level: str = "INFO"
    default_path: str = "~/.scripton/yesman/logs/"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class PathSettings:
    """Path configuration settings."""

    home_dir: str = "~/.scripton/yesman"
    templates_dir: str = "~/.scripton/yesman/templates"
    logs_dir: str = "~/.scripton/yesman/logs"
    cache_dir: str = "~/.scripton/yesman/cache"
    projects_file: str = "~/.scripton/yesman/projects.yaml"
    config_file: str = "~/.scripton/yesman/yesman.yaml"


@dataclass
class SessionSettings:
    """Session management settings."""

    default_timeout: int = 30
    max_windows_per_session: int = 10
    max_panes_per_window: int = 4
    session_name_max_length: int = 64
    auto_cleanup_enabled: bool = True


@dataclass
class MonitoringSettings:
    """Monitoring and health check settings."""

    health_check_interval: int = 60  # seconds
    max_response_time: float = 1.0  # seconds
    memory_threshold_mb: int = 500
    cpu_threshold_percent: float = 80.0
    disk_threshold_percent: float = 85.0


@dataclass
class APISettings:
    """API server settings."""

    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    cors_origins: list = None
    request_timeout: int = 30
    max_request_size: int = 1024 * 1024  # 1MB


@dataclass
class SecuritySettings:
    """Security configuration."""

    enable_auth: bool = False
    session_secret: str | None = None
    token_expiry_hours: int = 24
    max_login_attempts: int = 5
    rate_limit_per_minute: int = 60


class AppSettings:
    """Central application settings."""

    def __init__(self) -> None:
        self.cache = CacheSettings()
        self.logging = LoggingSettings()
        self.paths = PathSettings()
        self.sessions = SessionSettings()
        self.monitoring = MonitoringSettings()
        self.api = APISettings()
        self.security = SecuritySettings()

        # Load from environment variables
        self._load_from_env()

        # Expand paths
        self._expand_paths()

    def _load_from_env(self) -> None:
        """Load settings from environment variables."""
        # Cache settings
        self.cache.ttl = float(os.getenv("YESMAN_CACHE_TTL", self.cache.ttl))
        self.cache.max_entries = int(os.getenv("YESMAN_CACHE_MAX_ENTRIES", self.cache.max_entries))

        # Logging settings
        self.logging.level = os.getenv("YESMAN_LOG_LEVEL", self.logging.level)
        self.logging.default_path = os.getenv("YESMAN_LOG_PATH", self.logging.default_path)

        # Path settings
        self.paths.home_dir = os.getenv("YESMAN_HOME_DIR", self.paths.home_dir)
        self.paths.templates_dir = os.getenv("YESMAN_TEMPLATES_DIR", self.paths.templates_dir)

        # Session settings
        self.sessions.default_timeout = int(os.getenv("YESMAN_SESSION_TIMEOUT", self.sessions.default_timeout))

        # API settings
        self.api.host = os.getenv("YESMAN_API_HOST", self.api.host)
        self.api.port = int(os.getenv("YESMAN_API_PORT", self.api.port))
        self.api.debug = os.getenv("YESMAN_API_DEBUG", "false").lower() == "true"

    def _expand_paths(self) -> None:
        """Expand user paths (~) to absolute paths."""
        self.paths.home_dir = os.path.expanduser(self.paths.home_dir)
        self.paths.templates_dir = os.path.expanduser(self.paths.templates_dir)
        self.paths.logs_dir = os.path.expanduser(self.paths.logs_dir)
        self.paths.cache_dir = os.path.expanduser(self.paths.cache_dir)
        self.paths.projects_file = os.path.expanduser(self.paths.projects_file)
        self.paths.config_file = os.path.expanduser(self.paths.config_file)
        self.logging.default_path = os.path.expanduser(self.logging.default_path)

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.paths.home_dir,
            self.paths.templates_dir,
            self.paths.logs_dir,
            self.paths.cache_dir,
            self.logging.default_path,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict[str, object]:
        """Convert settings to dictionary for serialization.

        Returns:
        object: Description of return value.
        """
        return {
            "cache": {
                "ttl": self.cache.ttl,
                "max_entries": self.cache.max_entries,
                "enable_compression": self.cache.enable_compression,
                "cleanup_interval": self.cache.cleanup_interval,
            },
            "logging": {
                "level": self.logging.level,
                "default_path": self.logging.default_path,
                "max_file_size": self.logging.max_file_size,
                "backup_count": self.logging.backup_count,
                "format": self.logging.format,
            },
            "paths": {
                "home_dir": self.paths.home_dir,
                "templates_dir": self.paths.templates_dir,
                "logs_dir": self.paths.logs_dir,
                "cache_dir": self.paths.cache_dir,
                "projects_file": self.paths.projects_file,
                "config_file": self.paths.config_file,
            },
            "sessions": {
                "default_timeout": self.sessions.default_timeout,
                "max_windows_per_session": self.sessions.max_windows_per_session,
                "max_panes_per_window": self.sessions.max_panes_per_window,
                "session_name_max_length": self.sessions.session_name_max_length,
                "auto_cleanup_enabled": self.sessions.auto_cleanup_enabled,
            },
            "monitoring": {
                "health_check_interval": self.monitoring.health_check_interval,
                "max_response_time": self.monitoring.max_response_time,
                "memory_threshold_mb": self.monitoring.memory_threshold_mb,
                "cpu_threshold_percent": self.monitoring.cpu_threshold_percent,
                "disk_threshold_percent": self.monitoring.disk_threshold_percent,
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "debug": self.api.debug,
                "cors_origins": self.api.cors_origins,
                "request_timeout": self.api.request_timeout,
                "max_request_size": self.api.max_request_size,
            },
            "security": {
                "enable_auth": self.security.enable_auth,
                "token_expiry_hours": self.security.token_expiry_hours,
                "max_login_attempts": self.security.max_login_attempts,
                "rate_limit_per_minute": self.security.rate_limit_per_minute,
            },
        }


# Global settings instance
settings = AppSettings()


# Status constants
class SessionStatus:
    """Session status constants."""

    RUNNING = "running"
    STOPPED = "stopped"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"


class ControllerStatus:
    """Controller status constants."""

    IDLE = "idle"
    MONITORING = "monitoring"
    RESPONDING = "responding"
    ERROR = "error"
    DISABLED = "disabled"


class LogLevel:
    """Log level constants."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CacheKeys:
    """Cache key prefixes."""

    SESSION_INFO = "session_info"
    SESSION_LIST = "session_list"
    HEALTH_SCORE = "health_score"
    PROMPT_PATTERNS = "prompt_patterns"
    USER_PREFERENCES = "user_prefs"


# Content limits
class ContentLimits:
    """Content size and line limits."""

    MAX_PANE_LINES = 2000
    MAX_LOG_LINES = 50
    MAX_OUTPUT_CHARS = 30000
    MAX_SESSION_NAME_LENGTH = 64
    MAX_WINDOW_NAME_LENGTH = 32
    MAX_COMMAND_LENGTH = 1024
    MAX_WINDOWS_PER_SESSION = 10
    MAX_PANES_PER_WINDOW = 4


# Validation patterns
class ValidationPatterns:
    """Common validation regex patterns."""

    SESSION_NAME = r"^[a-zA-Z0-9_-]+$"
    WINDOW_NAME = r"^[a-zA-Z0-9_\-\s]+$"
    PORT_NUMBER = r"^[0-9]{1,5}$"
    LOG_LEVEL = r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
