# Copyright notice.

import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Base Renderer Interface
Abstract base class for all dashboard renderers.
"""


class RenderFormat(Enum):
    """Supported rendering formats."""

    TUI = "tui"
    WEB = "web"
    TAURI = "tauri"
    JSON = "json"
    MARKDOWN = "markdown"


class WidgetType(Enum):
    """Available widget types."""

    SESSION_BROWSER = "session_browser"
    HEALTH_METER = "health_meter"
    ACTIVITY_HEATMAP = "activity_heatmap"
    PROJECT_HEALTH = "project_health"
    GIT_ACTIVITY = "git_activity"
    PROGRESS_TRACKER = "progress_tracker"
    SESSION_PROGRESS = "session_progress"
    LOG_VIEWER = "log_viewer"
    METRIC_CARD = "metric_card"
    STATUS_INDICATOR = "status_indicator"
    CHART = "chart"
    TABLE = "table"
    GRID = "grid"
    LIST = "list"
    TREE = "tree"


class ThemeColor(Enum):
    """Theme color palette."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    NEUTRAL = "neutral"
    ACCENT = "accent"


class BaseRenderer(ABC):
    """Abstract base class for all dashboard renderers.

    Provides common functionality and enforces consistent interface
    across different rendering formats (TUI, Web, Tauri, etc.)
    """

    def __init__(
        self, format_type: RenderFormat, theme: dict[str, Any] | None = None
    ) -> None:
        """Initialize base renderer.

        Args:
            format_type: The rendering format this renderer supports
            theme: Optional theme configuration

        """
        self.format_type = format_type
        self.theme = theme or self._get_default_theme()
        self._cache: dict[str, Any] = {}

    @abstractmethod
    def render_widget(
        self,
        widget_type: WidgetType,
        data: object,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Render a single widget.

        Args:
            widget_type: Type of widget to render
            data: Data to display in the widget
            options: Optional rendering options

        """

    @abstractmethod
    def render_layout(
        self,
        widgets: list[dict[str, Any]],
        layout_config: dict[str, Any] | None = None,
    ) -> str:
        """Render a layout containing multiple widgets.

        Args:
            widgets: List of widget configurations
            layout_config: Optional layout configuration

        Returns:
            Rendered layout as string
        """

    @abstractmethod
    def render_container(
        self, content: str, container_config: dict[str, Any] | None = None
    ) -> str:
        """Render a container wrapping content.

        Args:
            content: Content to wrap
            container_config: Optional container configuration

        Returns:
            Rendered container as string
        """

    # Common utility methods

    @staticmethod
    def format_number(value: float, precision: int = 2, suffix: str = "") -> str:
        """Format a number with optional precision and suffix.

        Args:
            value: Number to format
            precision: Decimal precision
            suffix: Optional suffix (e.g., '%', 'MB')

        Returns:
            Formatted number string
        """
        if value is None:
            return "N/A"

        if isinstance(value, int) or value.is_integer():
            return f"{int(value):,}{suffix}"

        return f"{value:,.{precision}f}{suffix}"

    @staticmethod
    def format_date(date: datetime | str, format_str: str = "%Y-%m-%d %H:%M") -> str:
        """Format a date/datetime object.

        Args:
            date: Date to format
            format_str: Format string

        Returns:
            Formatted date string
        """
        if date is None:
            return "N/A"

        if isinstance(date, str):
            # Try to parse common date formats
            parsed_date = None
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    parsed_date = datetime.strptime(date, fmt)
                    break
                except ValueError:
                    continue

            if parsed_date is not None:
                date = parsed_date
            else:
                return date  # Return as-is if parsing fails

        if isinstance(date, datetime):
            return date.strftime(format_str)

        return str(date)

    @staticmethod
    def format_percentage(value: float, precision: int = 1) -> str:
        """Format a percentage value.

        Args:
            value: Percentage value (0-100)
            precision: Decimal precision

        Returns:
            Formatted percentage string
        """
        if value is None:
            return "N/A"

        return f"{value:.{precision}f}%"

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes into human-readable format.

        Args:
            bytes_value: Size in bytes

        Returns:
            Formatted size string
        """
        if bytes_value is None:
            return "N/A"

        bytes_float = float(bytes_value)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_float < 1024.0:
                return f"{bytes_float:.1f} {unit}"
            bytes_float /= 1024.0

        return f"{bytes_float:.1f} PB"

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        if seconds is None:
            return "N/A"

        if seconds < 60:
            return f"{seconds:.1f}s"
        if seconds < 3600:
            return f"{seconds // 60:.0f}m {seconds % 60:.0f}s"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"

    def get_color(self, color_type: ThemeColor, variant: str = "default") -> str:
        """Get color value from theme.

        Args:
            color_type: Type of color to retrieve
            variant: Color variant (default, light, dark)

        Returns:
            Color value as string
        """
        color_map = self.theme.get("colors", {})
        color_config = color_map.get(color_type.value, {})

        if isinstance(color_config, dict):
            result = color_config.get(variant, color_config.get("default", "#000000"))
            return str(result)  # Ensure we always return a string

        return str(color_config)

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add when truncated

        Returns:
            Truncated text
        """
        if text is None:
            return ""

        if len(text) <= max_length:
            return text

        return text[: max_length - len(suffix)] + suffix

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text for safe rendering.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        if text is None:
            return ""

        # Remove control characters except newline and tab
        return re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", text)

    @staticmethod
    def get_status_color(status: str) -> ThemeColor:
        """Get appropriate color for status.

        Args:
            status: Status string

        Returns:
            Appropriate theme color
        """
        status_lower = status.lower()

        if status_lower in {"active", "running", "healthy", "online", "connected"}:
            return ThemeColor.SUCCESS
        if status_lower in {"warning", "degraded", "slow"}:
            return ThemeColor.WARNING
        if status_lower in {"error", "failed", "stopped", "offline", "disconnected"}:
            return ThemeColor.ERROR
        if status_lower in {"loading", "pending", "connecting"}:
            return ThemeColor.INFO
        return ThemeColor.NEUTRAL

    @staticmethod
    def calculate_health_score(metrics: dict[str, int | float]) -> float:
        """Calculate overall health score from metrics.

        Args:
            metrics: Dictionary of metric values

        Returns:
            Health score (0-100)
        """
        if not metrics:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        # Default weights for common metrics
        weights = {
            "cpu_usage": 0.2,
            "memory_usage": 0.2,
            "disk_usage": 0.15,
            "network_usage": 0.1,
            "error_rate": 0.2,
            "response_time": 0.15,
        }

        for metric, value in metrics.items():
            weight = weights.get(metric, 0.1)

            # Convert to health score (higher is better)
            if metric in {"cpu_usage", "memory_usage", "disk_usage", "error_rate"}:
                # For usage metrics, lower is better
                score = max(0, 100 - value)
            else:
                # For other metrics, assume higher is better
                score = min(100, value)

            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def _get_default_theme() -> dict[str, Any]:
        """Get default theme configuration.

        Returns:
            Default theme dictionary
        """
        return {
            "colors": {
                "primary": {
                    "default": "#3B82F6",
                    "light": "#93C5FD",
                    "dark": "#1E40AF",
                },
                "secondary": {
                    "default": "#6B7280",
                    "light": "#D1D5DB",
                    "dark": "#374151",
                },
                "success": {
                    "default": "#10B981",
                    "light": "#86EFAC",
                    "dark": "#047857",
                },
                "warning": {
                    "default": "#F59E0B",
                    "light": "#FCD34D",
                    "dark": "#D97706",
                },
                "error": {"default": "#EF4444", "light": "#FCA5A5", "dark": "#DC2626"},
                "info": {"default": "#06B6D4", "light": "#67E8F9", "dark": "#0891B2"},
                "neutral": {
                    "default": "#6B7280",
                    "light": "#F3F4F6",
                    "dark": "#1F2937",
                },
                "accent": {"default": "#8B5CF6", "light": "#C4B5FD", "dark": "#7C3AED"},
            },
            "spacing": {
                "xs": "0.25rem",
                "sm": "0.5rem",
                "md": "1rem",
                "lg": "1.5rem",
                "xl": "2rem",
            },
            "typography": {
                "font_family": "monospace",
                "font_size": {
                    "xs": "0.75rem",
                    "sm": "0.875rem",
                    "md": "1rem",
                    "lg": "1.125rem",
                    "xl": "1.25rem",
                },
            },
        }

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._cache.clear()

    def set_theme(self, theme: dict[str, Any]) -> None:
        """Set new theme configuration.

        Args:
            theme: New theme configuration

        """
        self.theme = theme
        self.clear_cache()
