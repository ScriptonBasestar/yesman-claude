"""
TUI Dashboard

Textual-based terminal user interface dashboard for Yesman-Claude
Provides comprehensive project monitoring with multiple views and real-time updates.
"""

from datetime import datetime
from typing import Any, List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import (
    Footer,
    Header,
    Label,
    Placeholder,
    RichLog,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)

from .renderers import TUIRenderer, WidgetType
from .renderers.widget_models import (
    ActivityData,
    HealthData,
    HealthLevel,
    SessionData,
    SessionStatus,
)


class DashboardWidget(Static):
    """
    Base dashboard widget component for Textual UI

    Integrates with TUIRenderer to display various widget types
    with real-time data updates and rich formatting.
    """

    def __init__(
        self,
        widget_type: WidgetType,
        title: str = "",
        update_interval: float = 2.0,
        **kwargs,
    ):
        """
        Initialize dashboard widget

        Args:
            widget_type: Type of widget to render
            title: Widget title for display
            update_interval: Auto-update interval in seconds
        """
        super().__init__(**kwargs)
        self.widget_type = widget_type
        self.title = title
        self.update_interval = update_interval
        self.renderer = TUIRenderer()
        self._timer: Optional[Timer] = None
        self._last_data: Optional[Any] = None

    def compose(self) -> ComposeResult:
        """Compose the widget structure"""
        if self.title:
            yield Label(self.title, classes="widget-title")
        yield Container(id="widget-content")

    def on_mount(self) -> None:
        """Start auto-update timer when widget is mounted"""
        if self.update_interval > 0:
            self._timer = self.set_interval(self.update_interval, self.auto_update)

    def on_unmount(self) -> None:
        """Clean up timer when widget is unmounted"""
        if self._timer:
            self._timer.stop()

    async def update_data(self, data: Any) -> None:
        """
        Update widget with new data

        Args:
            data: Widget-specific data to display
        """
        self._last_data = data

        try:
            # Render data using TUIRenderer
            rendered_content = self.renderer.render_widget(self.widget_type, data)

            # Update the content container
            content_container = self.query_one("#widget-content", Container)
            await content_container.update(rendered_content.get("content", ""))

        except Exception as e:
            # Show error state
            error_msg = f"Error rendering {self.widget_type.value}: {str(e)}"
            content_container = self.query_one("#widget-content", Container)
            await content_container.update(f"[red]{error_msg}[/red]")

    async def auto_update(self) -> None:
        """Auto-update callback - override in subclasses for custom data fetching"""
        if self._last_data is not None:
            await self.update_data(self._last_data)


class SessionsView(DashboardWidget):
    """Sessions monitoring view"""

    def __init__(self, **kwargs):
        super().__init__(
            widget_type=WidgetType.SESSION_BROWSER,
            title="Active Sessions",
            update_interval=3.0,
            **kwargs,
        )

    async def auto_update(self) -> None:
        """Fetch and update session data"""
        # Mock session data - replace with actual data fetching
        mock_sessions = [
            SessionData(
                name="yesman-dev",
                status=SessionStatus.ACTIVE,
                uptime=7200,  # 2 hours
                windows=3,
                last_activity=datetime.now(),
            ),
            SessionData(
                name="claude-test",
                status=SessionStatus.IDLE,
                uptime=1800,  # 30 minutes
                windows=2,
                last_activity=datetime.now(),
            ),
        ]
        await self.update_data(mock_sessions)


class HealthView(DashboardWidget):
    """Project health monitoring view"""

    def __init__(self, **kwargs):
        super().__init__(
            widget_type=WidgetType.PROJECT_HEALTH,
            title="Project Health",
            update_interval=5.0,
            **kwargs,
        )

    async def auto_update(self) -> None:
        """Fetch and update health data"""
        # Mock health data
        mock_health = HealthData(
            overall_score=85,
            overall_level=HealthLevel.GOOD,
            categories={
                "build": 90,
                "tests": 85,
                "dependencies": 95,
                "security": 80,
                "performance": 85,
                "code_quality": 75,
                "git": 88,
                "documentation": 70,
            },
            last_updated=datetime.now(),
        )
        await self.update_data(mock_health)


class ActivityView(DashboardWidget):
    """Activity monitoring view"""

    def __init__(self, **kwargs):
        super().__init__(
            widget_type=WidgetType.ACTIVITY_HEATMAP,
            title="Activity Heatmap",
            update_interval=10.0,
            **kwargs,
        )

    async def auto_update(self) -> None:
        """Fetch and update activity data"""
        # Mock activity data
        mock_activity = ActivityData(
            hourly_stats={f"{i:02d}:00": i * 10 for i in range(24)},
            daily_stats={"Mon": 120, "Tue": 95, "Wed": 110, "Thu": 85, "Fri": 130},
            peak_hours=["09:00", "14:00", "16:00"],
            total_sessions=15,
            avg_session_time=45.5,
        )
        await self.update_data(mock_activity)


class LogsView(Static):
    """Logs monitoring view"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_buffer: List[str] = []
        self.max_logs = 100

    def compose(self) -> ComposeResult:
        """Compose logs view"""
        yield Label("System Logs", classes="widget-title")
        yield RichLog(id="logs-content", highlight=True, markup=True)

    def on_mount(self) -> None:
        """Initialize logs view with sample data"""
        self.add_log("INFO", "TUI Dashboard started")
        self.add_log("DEBUG", "Initializing widget components")
        self.add_log("INFO", "Auto-refresh enabled for all views")

    def add_log(self, level: str, message: str) -> None:
        """Add a log entry"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color-code log levels
        color_map = {
            "ERROR": "red",
            "WARNING": "yellow",
            "INFO": "green",
            "DEBUG": "blue",
        }
        color = color_map.get(level, "white")

        formatted_log = f"[dim]{timestamp}[/dim] [{color}]{level}[/{color}] {message}"

        # Add to buffer
        self.log_buffer.append(formatted_log)
        if len(self.log_buffer) > self.max_logs:
            self.log_buffer.pop(0)

        # Update display
        logs_widget = self.query_one("#logs-content", RichLog)
        logs_widget.write(formatted_log)


class SettingsView(Static):
    """Settings and configuration view"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = {
            "auto_refresh": True,
            "refresh_interval": 3.0,
            "dark_mode": True,
            "show_timestamps": True,
        }

    def compose(self) -> ComposeResult:
        """Compose settings view"""
        yield Label("Dashboard Settings", classes="widget-title")
        yield Vertical(
            Horizontal(
                Label("Auto Refresh: "),
                Switch(value=self.settings["auto_refresh"], id="auto-refresh-switch"),
                classes="setting-row",
            ),
            Horizontal(
                Label("Dark Mode: "),
                Switch(value=self.settings["dark_mode"], id="dark-mode-switch"),
                classes="setting-row",
            ),
            Horizontal(
                Label("Show Timestamps: "),
                Switch(value=self.settings["show_timestamps"], id="timestamps-switch"),
                classes="setting-row",
            ),
            classes="settings-container",
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle settings changes"""
        if event.switch.id == "auto-refresh-switch":
            self.settings["auto_refresh"] = event.value
            self.post_message(self.SettingChanged("auto_refresh", event.value))
        elif event.switch.id == "dark-mode-switch":
            self.settings["dark_mode"] = event.value
            self.post_message(self.SettingChanged("dark_mode", event.value))
        elif event.switch.id == "timestamps-switch":
            self.settings["show_timestamps"] = event.value
            self.post_message(self.SettingChanged("show_timestamps", event.value))

    class SettingChanged(Message):
        """Setting changed message"""

        def __init__(self, setting: str, value: Any) -> None:
            self.setting = setting
            self.value = value
            super().__init__()


class TUIDashboard(App):
    """
    Textual-based TUI Dashboard for Yesman-Claude

    Provides comprehensive project monitoring with multiple views,
    keyboard shortcuts, auto-refresh, and customizable settings.
    """

    CSS_PATH = "tui_dashboard.css"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "toggle_dark", "Dark Mode", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("1", "view_sessions", "Sessions", show=True),
        Binding("2", "view_health", "Health", show=True),
        Binding("3", "view_activity", "Activity", show=True),
        Binding("4", "view_logs", "Logs", show=True),
        Binding("5", "view_settings", "Settings", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    # Reactive attributes
    current_view = reactive("sessions")
    auto_refresh_enabled = reactive(True)
    refresh_interval = reactive(3.0)

    def __init__(self, **kwargs):
        """Initialize TUI Dashboard"""
        super().__init__(**kwargs)
        self.title = "Yesman-Claude TUI Dashboard"
        self.sub_title = "Real-time Project Monitoring"

        # View components
        self.sessions_view: Optional[SessionsView] = None
        self.health_view: Optional[HealthView] = None
        self.activity_view: Optional[ActivityView] = None
        self.logs_view: Optional[LogsView] = None
        self.settings_view: Optional[SettingsView] = None

        # Refresh timer
        self._refresh_timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        """Compose the main dashboard layout"""
        yield Header(show_clock=True)

        with TabbedContent():
            with TabPane("Sessions", id="sessions-tab"):
                yield Placeholder("Loading sessions...", id="sessions-content")

            with TabPane("Health", id="health-tab"):
                yield Placeholder("Loading health data...", id="health-content")

            with TabPane("Activity", id="activity-tab"):
                yield Placeholder("Loading activity data...", id="activity-content")

            with TabPane("Logs", id="logs-tab"):
                yield Placeholder("Loading logs...", id="logs-content")

            with TabPane("Settings", id="settings-tab"):
                yield Placeholder("Loading settings...", id="settings-content")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize dashboard after mounting"""
        self.call_after_refresh(self.initialize_views)
        self.start_auto_refresh()

    async def initialize_views(self) -> None:
        """Initialize all view components"""
        # Initialize views
        self.sessions_view = SessionsView()
        self.health_view = HealthView()
        self.activity_view = ActivityView()
        self.logs_view = LogsView()
        self.settings_view = SettingsView()

        # Mount views to their respective containers
        sessions_container = self.query_one("#sessions-content")
        await sessions_container.remove()
        await self.query_one("#sessions-tab").mount(self.sessions_view)

        health_container = self.query_one("#health-content")
        await health_container.remove()
        await self.query_one("#health-tab").mount(self.health_view)

        activity_container = self.query_one("#activity-content")
        await activity_container.remove()
        await self.query_one("#activity-tab").mount(self.activity_view)

        logs_container = self.query_one("#logs-content")
        await logs_container.remove()
        await self.query_one("#logs-tab").mount(self.logs_view)

        settings_container = self.query_one("#settings-content")
        await settings_container.remove()
        await self.query_one("#settings-tab").mount(self.settings_view)

        # Log initialization
        if self.logs_view:
            self.logs_view.add_log("INFO", "All dashboard views initialized")

    def start_auto_refresh(self) -> None:
        """Start auto-refresh timer"""
        if self.auto_refresh_enabled and self._refresh_timer is None:
            self._refresh_timer = self.set_interval(
                self.refresh_interval,
                self.auto_refresh_all_views,
            )

    def stop_auto_refresh(self) -> None:
        """Stop auto-refresh timer"""
        if self._refresh_timer:
            self._refresh_timer.stop()
            self._refresh_timer = None

    async def auto_refresh_all_views(self) -> None:
        """Auto-refresh all active views"""
        try:
            # Refresh only the currently visible view for performance
            current_tab = self.query_one(TabbedContent).active_pane

            if current_tab and current_tab.id == "sessions-tab" and self.sessions_view:
                await self.sessions_view.auto_update()
            elif current_tab and current_tab.id == "health-tab" and self.health_view:
                await self.health_view.auto_update()
            elif current_tab and current_tab.id == "activity-tab" and self.activity_view:
                await self.activity_view.auto_update()

            if self.logs_view:
                self.logs_view.add_log("DEBUG", f"Auto-refreshed {current_tab.id if current_tab else 'unknown'}")

        except Exception as e:
            if self.logs_view:
                self.logs_view.add_log("ERROR", f"Auto-refresh failed: {str(e)}")

    # Action handlers
    def action_quit(self) -> None:
        """Quit the application"""
        self.stop_auto_refresh()
        self.exit()

    def action_toggle_dark(self) -> None:
        """Toggle dark mode"""
        self.dark = not self.dark
        if self.logs_view:
            mode = "dark" if self.dark else "light"
            self.logs_view.add_log("INFO", f"Switched to {mode} mode")

    async def action_refresh(self) -> None:
        """Manual refresh current view"""
        await self.auto_refresh_all_views()
        if self.logs_view:
            self.logs_view.add_log("INFO", "Manual refresh triggered")

    def action_view_sessions(self) -> None:
        """Switch to sessions view"""
        tabs = self.query_one(TabbedContent)
        tabs.active = "sessions-tab"
        self.current_view = "sessions"

    def action_view_health(self) -> None:
        """Switch to health view"""
        tabs = self.query_one(TabbedContent)
        tabs.active = "health-tab"
        self.current_view = "health"

    def action_view_activity(self) -> None:
        """Switch to activity view"""
        tabs = self.query_one(TabbedContent)
        tabs.active = "activity-tab"
        self.current_view = "activity"

    def action_view_logs(self) -> None:
        """Switch to logs view"""
        tabs = self.query_one(TabbedContent)
        tabs.active = "logs-tab"
        self.current_view = "logs"

    def action_view_settings(self) -> None:
        """Switch to settings view"""
        tabs = self.query_one(TabbedContent)
        tabs.active = "settings-tab"
        self.current_view = "settings"

    def on_settings_view_setting_changed(self, message: SettingsView.SettingChanged) -> None:
        """Handle settings changes"""
        if message.setting == "auto_refresh":
            self.auto_refresh_enabled = message.value
            if message.value:
                self.start_auto_refresh()
            else:
                self.stop_auto_refresh()
        elif message.setting == "dark_mode":
            self.dark = message.value

        if self.logs_view:
            self.logs_view.add_log("INFO", f"Setting changed: {message.setting} = {message.value}")


def run_tui_dashboard():
    """Convenience function to run the TUI dashboard"""
    app = TUIDashboard()
    app.run()


if __name__ == "__main__":
    run_tui_dashboard()
