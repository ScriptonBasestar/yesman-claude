"""
TUI Renderer
Rich-based terminal user interface renderer for dashboard widgets
"""

from datetime import datetime
from typing import Any

from rich.align import Align
from rich.box import MINIMAL, ROUNDED
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from .base_renderer import BaseRenderer, RenderFormat, WidgetType
from .widget_models import ActivityData, ChartData, HealthData, HealthLevel, MetricCardData, ProgressData, ProgressPhase, SessionData, SessionStatus, StatusIndicatorData


class TUIRenderer(BaseRenderer):
    """
    Terminal User Interface renderer using Rich library

    Provides rich terminal-based rendering of dashboard widgets
    with colors, progress bars, tables, trees, and panels.
    """

    def __init__(self, console: Console | None = None, theme: dict[str, Any] | None = None):
        """
        Initialize TUI renderer

        Args:
            console: Rich Console instance (creates new if None)
            theme: Theme configuration
        """
        super().__init__(RenderFormat.TUI, theme)
        self.console = console or Console()

        # Terminal capabilities
        self.supports_color = self.console.color_system is not None
        self.terminal_width = self.console.width or 80
        self.terminal_height = self.console.height or 24

        # Color mappings for TUI
        self._color_map = {
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "info": "blue",
            "neutral": "white",
            "primary": "cyan",
            "secondary": "magenta",
        }

    def render_widget(
        self,
        widget_type: WidgetType,
        data: Any,
        options: dict[str, Any] | None = None,
    ) -> str:
        """
        Render a single widget using Rich components

        Args:
            widget_type: Type of widget to render
            data: Widget data (should be appropriate model instance)
            options: Rendering options

        Returns:
            Rendered widget as Rich renderable converted to string
        """
        options = options or {}

        # Route to specific widget renderer
        if widget_type == WidgetType.SESSION_BROWSER:
            return self._render_session_browser(data, options)
        elif widget_type == WidgetType.HEALTH_METER:
            return self._render_health_meter(data, options)
        elif widget_type == WidgetType.ACTIVITY_HEATMAP:
            return self._render_activity_heatmap(data, options)
        elif widget_type == WidgetType.PROGRESS_TRACKER:
            return self._render_progress_tracker(data, options)
        elif widget_type == WidgetType.LOG_VIEWER:
            return self._render_log_viewer(data, options)
        elif widget_type == WidgetType.METRIC_CARD:
            return self._render_metric_card(data, options)
        elif widget_type == WidgetType.STATUS_INDICATOR:
            return self._render_status_indicator(data, options)
        elif widget_type == WidgetType.CHART:
            return self._render_chart(data, options)
        elif widget_type == WidgetType.TABLE:
            return self._render_table(data, options)
        else:
            return self._render_generic_widget(widget_type, data, options)

    def render_layout(
        self,
        widgets: list[dict[str, Any]],
        layout_config: dict[str, Any] | None = None,
    ) -> str:
        """
        Render a layout containing multiple widgets

        Args:
            widgets: List of widget configurations
            layout_config: Layout configuration

        Returns:
            Rendered layout as string
        """
        layout_config = layout_config or {}
        layout_type = layout_config.get("type", "vertical")

        rendered_widgets = []
        for widget in widgets:
            widget_type = widget.get("type", WidgetType.METRIC_CARD)
            widget_data = widget.get("data", {})
            widget_options = widget.get("options", {})

            rendered = self.render_widget(widget_type, widget_data, widget_options)
            rendered_widgets.append(rendered)

        if layout_type == "horizontal":
            return self._render_horizontal_layout(rendered_widgets, layout_config)
        elif layout_type == "grid":
            return self._render_grid_layout(rendered_widgets, layout_config)
        else:
            return self._render_vertical_layout(rendered_widgets, layout_config)

    def render_container(self, content: str, container_config: dict[str, Any] | None = None) -> str:
        """
        Render a container wrapping content

        Args:
            content: Content to wrap
            container_config: Container configuration

        Returns:
            Rendered container as string
        """
        container_config = container_config or {}

        title = container_config.get("title", "")
        border = container_config.get("border", True)
        style = container_config.get("style", "")
        padding = container_config.get("padding", (0, 1))

        if border:
            box_style = ROUNDED if container_config.get("rounded", True) else MINIMAL
            panel = Panel(
                content,
                title=title,
                border_style=style,
                box=box_style,
                padding=padding,
            )

            with self.console.capture() as capture:
                self.console.print(panel)
            return capture.get()
        else:
            return content

    # Widget-specific renderers

    def _render_session_browser(self, data: SessionData | list[SessionData], options: dict[str, Any]) -> str:
        """Render session browser widget"""
        view_mode = options.get("view_mode", "table")

        if isinstance(data, SessionData):
            sessions = [data]
        elif isinstance(data, list):
            sessions = data
        else:
            # Handle raw data
            sessions = data.get("sessions", []) if isinstance(data, dict) else []

        if view_mode == "tree":
            return self._render_session_tree(sessions, options)
        elif view_mode == "cards":
            return self._render_session_cards(sessions, options)
        else:
            return self._render_session_table(sessions, options)

    def _render_session_table(self, sessions: list[SessionData], options: dict[str, Any]) -> str:
        """Render sessions as table"""
        table = Table(title="Active Sessions", box=ROUNDED)

        # Add columns
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Windows", justify="right")
        table.add_column("Panes", justify="right")
        table.add_column("Claude", justify="center")
        table.add_column("Activity", style="dim")

        for session in sessions:
            if not isinstance(session, SessionData):
                continue

            # Status with color
            status_color = self._get_status_color(session.status.value)
            status_text = Text(session.status.value.upper(), style=status_color)

            # Claude status
            claude_status = "🤖" if session.claude_active else "💤"

            # Last activity
            if session.last_activity:
                time_diff = datetime.now() - session.last_activity
                if time_diff.total_seconds() < 60:
                    activity = "Just now"
                elif time_diff.total_seconds() < 3600:
                    activity = f"{int(time_diff.total_seconds() // 60)}m ago"
                else:
                    activity = f"{int(time_diff.total_seconds() // 3600)}h ago"
            else:
                activity = "Unknown"

            table.add_row(
                session.name,
                status_text,
                str(len(session.windows)),
                str(session.panes),
                claude_status,
                activity,
            )

        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _render_session_tree(self, sessions: list[SessionData], options: dict[str, Any]) -> str:
        """Render sessions as tree"""
        tree = Tree("📂 Sessions", style="bold blue")

        for session in sessions:
            if not isinstance(session, SessionData):
                continue

            # Session node
            status_emoji = "🟢" if session.status == SessionStatus.ACTIVE else "🟡" if session.status == SessionStatus.IDLE else "🔴"
            claude_emoji = "🤖" if session.claude_active else ""

            session_label = f"{status_emoji} {session.name} {claude_emoji}"
            session_node = tree.add(session_label)

            # Windows
            if session.windows:
                windows_node = session_node.add("📁 Windows")
                for window in session.windows:
                    window_emoji = "⚡" if window.active else "💤"
                    window_label = f"{window_emoji} {window.name} ({window.panes} panes)"
                    windows_node.add(window_label)

            # Metadata
            if session.metadata:
                meta_node = session_node.add("ℹ️ Info")
                meta_node.add(f"CPU: {session.cpu_usage:.1f}%")
                meta_node.add(f"Memory: {session.memory_usage:.1f}%")

        with self.console.capture() as capture:
            self.console.print(tree)
        return capture.get()

    def _render_session_cards(self, sessions: list[SessionData], options: dict[str, Any]) -> str:
        """Render sessions as cards"""
        cards = []

        for session in sessions:
            if not isinstance(session, SessionData):
                continue

            # Card content
            status_color = self._get_status_color(session.status.value)

            content = Text()
            content.append("Status: ", style="bold")
            content.append(f"{session.status.value.upper()}\n", style=status_color)
            content.append(f"Windows: {len(session.windows)}\n")
            content.append(f"Panes: {session.panes}\n")

            if session.claude_active:
                content.append("Claude: 🤖 Active\n", style="green")
            else:
                content.append("Claude: 💤 Inactive\n", style="dim")

            # Create card panel
            card = Panel(
                content,
                title=f"📋 {session.name}",
                border_style=status_color,
                box=ROUNDED,
                padding=(0, 1),
            )
            cards.append(card)

        # Arrange in columns
        if cards:
            columns = Columns(cards, equal=True, expand=True)
            with self.console.capture() as capture:
                self.console.print(columns)
            return capture.get()
        else:
            return "No sessions found"

    def _render_health_meter(self, data: HealthData, options: dict[str, Any]) -> str:
        """Render health meter widget"""
        if not isinstance(data, HealthData):
            return "Invalid health data"

        # Overall health panel
        health_color = self._get_health_color(data.overall_level)
        health_emoji = data.overall_level.emoji

        # Create health bar
        progress = Progress(
            TextColumn("[bold blue]Health Score"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            expand=True,
        )

        task = progress.add_task("health", total=100, completed=data.overall_score)

        # Categories breakdown
        categories_text = Text()
        for category in data.categories:
            cat_color = self._get_health_color(category.level)
            categories_text.append(f"• {category.category.title()}: ", style="bold")
            categories_text.append(f"{category.score}% ", style=cat_color)
            categories_text.append(f"{category.level.emoji}\n")

        # Combine into panel
        content = Layout()
        content.split_column(
            Layout(progress, size=3),
            Layout(categories_text),
        )

        panel = Panel(
            content,
            title=f"{health_emoji} Project Health ({data.overall_score}%)",
            border_style=health_color,
            box=ROUNDED,
        )

        with self.console.capture() as capture:
            self.console.print(panel)
        return capture.get()

    def _render_activity_heatmap(self, data: ActivityData, options: dict[str, Any]) -> str:
        """Render activity heatmap as ASCII art"""
        if not isinstance(data, ActivityData):
            return "Invalid activity data"

        # Simple ASCII heatmap representation
        content = Text()
        content.append("Activity Overview\n\n", style="bold")

        # Stats
        content.append(f"Total Activities: {data.total_activities}\n")
        content.append(f"Active Days: {data.active_days}\n")
        content.append(f"Current Streak: {data.current_streak} days\n")
        content.append(f"Longest Streak: {data.longest_streak} days\n")
        content.append(f"Average/Day: {data.avg_per_day:.1f}\n\n")

        # Simple heat representation
        if data.activity_rate > 80:
            heat_level = "🔥🔥🔥"
            color = "red"
        elif data.activity_rate > 60:
            heat_level = "🔥🔥"
            color = "yellow"
        elif data.activity_rate > 40:
            heat_level = "🔥"
            color = "blue"
        else:
            heat_level = "❄️"
            color = "dim"

        content.append("Activity Level: ", style="bold")
        content.append(f"{heat_level} {data.activity_rate:.1f}%\n", style=color)

        panel = Panel(
            content,
            title="📊 Activity Heatmap",
            border_style="cyan",
            box=ROUNDED,
        )

        with self.console.capture() as capture:
            self.console.print(panel)
        return capture.get()

    def _render_progress_tracker(self, data: ProgressData, options: dict[str, Any]) -> str:
        """Render progress tracker widget"""
        if not isinstance(data, ProgressData):
            return "Invalid progress data"

        # Phase indicator
        phase_emoji = {
            ProgressPhase.STARTING: "🚀",
            ProgressPhase.ANALYZING: "🔍",
            ProgressPhase.IMPLEMENTING: "⚙️",
            ProgressPhase.TESTING: "🧪",
            ProgressPhase.COMPLETING: "✅",
            ProgressPhase.COMPLETED: "🎉",
            ProgressPhase.IDLE: "💤",
            ProgressPhase.ERROR: "❌",
        }.get(data.phase, "❓")

        # Progress bars
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[label]}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            expand=True,
        )

        # Overall progress
        overall_task = progress.add_task(
            "overall",
            total=100,
            completed=data.overall_progress,
            label="Overall Progress",
        )

        # Phase progress
        phase_task = progress.add_task(
            "phase",
            total=100,
            completed=data.phase_progress,
            label=f"{data.phase.value.title()} Phase",
        )

        # Stats
        stats_text = Text()
        stats_text.append("Activity:\n", style="bold")
        stats_text.append(f"• Files Created: {data.files_created}\n")
        stats_text.append(f"• Files Modified: {data.files_modified}\n")
        stats_text.append(f"• Commands: {data.commands_executed} ({data.commands_succeeded} ✅, {data.commands_failed} ❌)\n")
        stats_text.append(f"• TODOs: {data.todos_completed}/{data.todos_identified}\n")

        if data.active_duration > 0:
            stats_text.append(f"• Active Time: {self.format_duration(data.active_duration)}\n")

        # Combine layout
        content = Layout()
        content.split_column(
            Layout(progress, size=5),
            Layout(stats_text),
        )

        panel = Panel(
            content,
            title=f"{phase_emoji} Progress Tracker",
            border_style="green" if data.phase == ProgressPhase.COMPLETED else "blue",
            box=ROUNDED,
        )

        with self.console.capture() as capture:
            self.console.print(panel)
        return capture.get()

    def _render_log_viewer(self, data: dict[str, Any], options: dict[str, Any]) -> str:
        """Render log viewer widget"""
        logs = data.get("logs", []) if isinstance(data, dict) else []
        max_lines = options.get("max_lines", 10)

        content = Text()

        for i, log_entry in enumerate(logs[-max_lines:]):
            if isinstance(log_entry, dict):
                timestamp = log_entry.get("timestamp", "")
                level = log_entry.get("level", "INFO")
                message = log_entry.get("message", str(log_entry))

                # Color by log level
                level_color = {
                    "ERROR": "red",
                    "WARNING": "yellow",
                    "INFO": "blue",
                    "DEBUG": "dim",
                }.get(level.upper(), "white")

                content.append(f"[{timestamp}] ", style="dim")
                content.append(f"{level}: ", style=level_color)
                content.append(f"{message}\n")
            else:
                content.append(f"{log_entry}\n")

        panel = Panel(
            content,
            title="📜 Recent Logs",
            border_style="magenta",
            box=ROUNDED,
        )

        with self.console.capture() as capture:
            self.console.print(panel)
        return capture.get()

    def _render_metric_card(self, data: MetricCardData, options: dict[str, Any]) -> str:
        """Render metric card widget"""
        if not isinstance(data, MetricCardData):
            return "Invalid metric data"

        # Format value
        formatted_value = self.format_number(data.value) + data.suffix if isinstance(data.value, int | float) else str(data.value) + data.suffix

        # Trend indicator
        trend_indicator = ""
        if data.trend is not None:
            if data.trend > 0:
                trend_indicator = f" ↗️ +{data.trend}"
            elif data.trend < 0:
                trend_indicator = f" ↘️ {data.trend}"
            else:
                trend_indicator = " ➡️ 0"

        # Content
        content = Text()
        content.append(f"{data.icon} " if data.icon else "")
        content.append(
            f"{formatted_value}",
            style=f"bold {self._color_map.get(data.color, 'white')}",
        )
        content.append(f"{trend_indicator}\n", style="dim")

        if data.comparison:
            content.append(f"{data.comparison}", style="dim")

        panel = Panel(
            Align.center(content),
            title=data.title,
            border_style=self._color_map.get(data.color, "white"),
            box=ROUNDED,
            padding=(1, 2),
        )

        with self.console.capture() as capture:
            self.console.print(panel)
        return capture.get()

    def _render_status_indicator(self, data: StatusIndicatorData, options: dict[str, Any]) -> str:
        """Render status indicator widget"""
        if not isinstance(data, StatusIndicatorData):
            return "Invalid status data"

        status_color = self._color_map.get(data.color, "white")

        content = Text()
        content.append(f"{data.icon} " if data.icon else "")
        content.append(f"{data.status.upper()}", style=f"bold {status_color}")

        if data.label:
            content.append(f"\n{data.label}", style="dim")

        # Pulse effect (just add a spinner for TUI)
        if data.pulse:
            content.append(" ⟳", style=status_color)

        panel = Panel(
            Align.center(content),
            border_style=status_color,
            box=MINIMAL if options.get("compact") else ROUNDED,
            padding=(0, 1),
        )

        with self.console.capture() as capture:
            self.console.print(panel)
        return capture.get()

    def _render_chart(self, data: ChartData, options: dict[str, Any]) -> str:
        """Render chart as ASCII representation"""
        if not isinstance(data, ChartData):
            return "Invalid chart data"

        content = Text()
        content.append(f"📈 {data.title}\n\n", style="bold")

        if not data.data_points:
            content.append("No data available", style="dim")
        else:
            # Simple ASCII chart
            values = [point.y for point in data.data_points]
            if values:
                max_val = max(values)
                min_val = min(values)

                content.append(f"Max: {max_val}, Min: {min_val}, Avg: {sum(values) / len(values):.1f}\n\n")

                # Simple bar representation
                for i, point in enumerate(data.data_points[-10:]):  # Show last 10 points
                    bar_length = int(point.y / max_val * 20) if max_val > 0 else 0
                    bar = "█" * bar_length + "░" * (20 - bar_length)

                    label = str(point.x)
                    if hasattr(point.x, "strftime"):
                        label = point.x.strftime("%H:%M")

                    content.append(f"{label:>8} │{bar}│ {point.y}\n")

        panel = Panel(
            content,
            title=f"📊 {data.title}",
            border_style="cyan",
            box=ROUNDED,
        )

        with self.console.capture() as capture:
            self.console.print(panel)
        return capture.get()

    def _render_table(self, data: dict[str, Any], options: dict[str, Any]) -> str:
        """Render generic table"""
        rows = data.get("rows", []) if isinstance(data, dict) else []
        headers = data.get("headers", []) if isinstance(data, dict) else []

        table = Table(box=ROUNDED)

        # Add columns
        for header in headers:
            table.add_column(str(header), style="cyan")

        # Add rows
        for row in rows:
            if isinstance(row, list | tuple):
                table.add_row(*[str(cell) for cell in row])
            elif isinstance(row, dict):
                table.add_row(*[str(row.get(header, "")) for header in headers])

        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _render_generic_widget(self, widget_type: WidgetType, data: Any, options: dict[str, Any]) -> str:
        """Render generic widget fallback"""
        content = Text()
        content.append(f"Widget Type: {widget_type.value}\n", style="bold")
        content.append(f"Data: {str(data)[:200]}\n", style="dim")

        panel = Panel(
            content,
            title=f"🔧 {widget_type.value.replace('_', ' ').title()}",
            border_style="yellow",
            box=ROUNDED,
        )

        with self.console.capture() as capture:
            self.console.print(panel)
        return capture.get()

    # Layout renderers

    def _render_vertical_layout(self, widgets: list[str], config: dict[str, Any]) -> str:
        """Render widgets in vertical layout"""
        result = []
        spacing = config.get("spacing", 1)

        for i, widget in enumerate(widgets):
            result.append(widget)
            if i < len(widgets) - 1:
                result.extend(["\n"] * spacing)

        return "".join(result)

    def _render_horizontal_layout(self, widgets: list[str], config: dict[str, Any]) -> str:
        """Render widgets in horizontal layout"""
        if not widgets:
            return ""

        # For horizontal layout, we'll use Rich Columns
        # Convert strings back to renderables (this is a limitation of the current design)
        panels = []
        for widget in widgets:
            panels.append(Panel(widget, box=MINIMAL))

        columns = Columns(panels, equal=True, expand=True)

        with self.console.capture() as capture:
            self.console.print(columns)
        return capture.get()

    def _render_grid_layout(self, widgets: list[str], config: dict[str, Any]) -> str:
        """Render widgets in grid layout"""
        cols = config.get("columns", 2)

        # Group widgets into rows
        rows = []
        for i in range(0, len(widgets), cols):
            row_widgets = widgets[i : i + cols]
            if len(row_widgets) < cols:
                # Pad with empty widgets
                row_widgets.extend([""] * (cols - len(row_widgets)))
            rows.append(row_widgets)

        # Render each row horizontally
        result = []
        for row in rows:
            row_result = self._render_horizontal_layout(row, config)
            result.append(row_result)

        return "\n\n".join(result)

    # Helper methods

    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        color_theme = self.get_status_color(status)
        return self._color_map.get(color_theme.value, "white")

    def _get_health_color(self, health_level: HealthLevel) -> str:
        """Get color for health level"""
        color_mapping = {
            HealthLevel.EXCELLENT: "green",
            HealthLevel.GOOD: "blue",
            HealthLevel.WARNING: "yellow",
            HealthLevel.CRITICAL: "red",
            HealthLevel.UNKNOWN: "dim",
        }
        return color_mapping.get(health_level, "white")

    def supports_feature(self, feature: str) -> bool:
        """Check if feature is supported"""
        features = {
            "color": self.supports_color,
            "unicode": True,  # Rich handles this
            "progress": True,
            "tables": True,
            "trees": True,
            "panels": True,
        }
        return features.get(feature, False)
