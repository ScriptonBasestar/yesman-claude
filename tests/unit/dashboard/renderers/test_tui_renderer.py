# Copyright notice.

from datetime import UTC, datetime
from io import StringIO

from rich.console import Console

from libs.dashboard.renderers.base_renderer import RenderFormat, WidgetType
from libs.dashboard.renderers.tui_renderer import TUIRenderer
from libs.dashboard.renderers.widget_models import (
    ActivityData,
    ActivityEntry,
    ActivityType,
    ChartData,
    ChartDataPoint,
    HealthCategoryData,
    HealthData,
    HealthLevel,
    MetricCardData,
    ProgressData,
    ProgressPhase,
    SessionData,
    SessionStatus,
    StatusIndicatorData,
    WindowData,
)

"""Tests for TUI Renderer."""


class TestTUIRenderer:
    """Test cases for TUI renderer."""

    def setup_method(self) -> None:
        """Setup test renderer."""
        # Use StringIO to capture output for testing
        self.string_io = StringIO()
        self.console = Console(file=self.string_io, width=80, height=24, force_terminal=True)
        self.renderer = TUIRenderer(console=self.console)

    def test_renderer_initialization(self) -> None:
        """Test TUI renderer initialization."""
        assert self.renderer.format_type == RenderFormat.TUI
        assert self.renderer.console is not None
        assert self.renderer.supports_color
        assert self.renderer.terminal_width == 80
        assert self.renderer.terminal_height == 24

    def test_color_mapping(self) -> None:
        """Test color mapping functionality."""
        assert self.renderer._color_map["success"] == "green"
        assert self.renderer._color_map["warning"] == "yellow"
        assert self.renderer._color_map["error"] == "red"
        assert self.renderer._color_map["info"] == "blue"

    def test_get_status_color(self) -> None:
        """Test status color retrieval."""
        color = self.renderer._get_status_color("active")
        assert color in {"green", "blue", "cyan", "white"}  # Valid color options

        color = self.renderer._get_status_color("error")
        assert color in {"red", "yellow", "white"}

    def test_get_health_color(self) -> None:
        """Test health level color mapping."""
        assert self.renderer._get_health_color(HealthLevel.EXCELLENT) == "green"
        assert self.renderer._get_health_color(HealthLevel.GOOD) == "blue"
        assert self.renderer._get_health_color(HealthLevel.WARNING) == "yellow"
        assert self.renderer._get_health_color(HealthLevel.CRITICAL) == "red"
        assert self.renderer._get_health_color(HealthLevel.UNKNOWN) == "dim"

    def test_supports_feature(self) -> None:
        """Test feature support checking."""
        assert self.renderer.supports_feature("color") is True
        assert self.renderer.supports_feature("unicode") is True
        assert self.renderer.supports_feature("progress") is True
        assert self.renderer.supports_feature("tables") is True
        assert self.renderer.supports_feature("trees") is True
        assert self.renderer.supports_feature("panels") is True
        assert self.renderer.supports_feature("nonexistent") is False

    def test_render_session_browser_table(self) -> None:
        """Test session browser table view rendering."""
        now = datetime.now(UTC)
        window = WindowData(id="1", name="test-window", active=True, panes=2)

        session = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            windows=[window],
            panes=2,
            claude_active=True,
            last_activity=now,
        )

        result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            [session],
            {"view_mode": "table"},
        )

        assert isinstance(result, str)
        assert "test-session" in result
        assert "ACTIVE" in result
        assert "🤖" in result  # Claude active indicator

    def test_render_session_browser_tree(self) -> None:
        """Test session browser tree view rendering."""
        now = datetime.now(UTC)
        window = WindowData(id="1", name="test-window", active=True, panes=2)

        session = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            windows=[window],
            panes=2,
            claude_active=True,
        )

        result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            [session],
            {"view_mode": "tree"},
        )

        assert isinstance(result, str)
        assert "Sessions" in result
        assert "test-session" in result
        assert "🟢" in result  # Active status emoji

    def test_render_session_browser_cards(self) -> None:
        """Test session browser cards view rendering."""
        now = datetime.now(UTC)
        window = WindowData(id="1", name="test-window", active=True, panes=2)

        session = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            windows=[window],
            panes=2,
            claude_active=True,
        )

        result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            [session],
            {"view_mode": "cards"},
        )

        assert isinstance(result, str)
        assert "test-session" in result
        assert "Status:" in result
        assert "Windows:" in result
        assert "Claude:" in result

    def test_render_health_meter(self) -> None:
        """Test health meter rendering."""
        now = datetime.now(UTC)
        category = HealthCategoryData(
            category="build",
            score=85,
            level=HealthLevel.GOOD,
            message="Build successful",
        )

        health = HealthData(
            overall_score=85,
            overall_level=HealthLevel.GOOD,
            categories=[category],
            last_updated=now,
        )

        result = self.renderer.render_widget(
            WidgetType.HEALTH_METER,
            health,
            {},
        )

        assert isinstance(result, str)
        assert "Project Health" in result
        assert "85%" in result
        assert "Build:" in result

    def test_render_activity_heatmap(self) -> None:
        """Test activity heatmap rendering."""
        now = datetime.now(UTC)
        entry = ActivityEntry(
            timestamp=now,
            activity_type=ActivityType.FILE_CREATED,
            description="Created new file",
        )

        activity = ActivityData(
            entries=[entry],
            total_activities=10,
            active_days=5,
            activity_rate=75.0,
            current_streak=3,
            longest_streak=7,
            avg_per_day=2.0,
        )

        result = self.renderer.render_widget(
            WidgetType.ACTIVITY_HEATMAP,
            activity,
            {},
        )

        assert isinstance(result, str)
        assert "Activity Overview" in result
        assert "Total Activities: 10" in result
        assert "Active Days: 5" in result
        assert "75.0%" in result
        assert "🔥" in result  # Heat indicator

    def test_render_progress_tracker(self) -> None:
        """Test progress tracker rendering."""
        now = datetime.now(UTC)

        progress = ProgressData(
            phase=ProgressPhase.IMPLEMENTING,
            phase_progress=75.0,
            overall_progress=50.0,
            files_created=5,
            files_modified=10,
            commands_executed=20,
            commands_succeeded=18,
            commands_failed=2,
            start_time=now,
            active_duration=3600.0,
            todos_identified=10,
            todos_completed=7,
        )

        result = self.renderer.render_widget(
            WidgetType.PROGRESS_TRACKER,
            progress,
            {},
        )

        assert isinstance(result, str)
        assert "Progress Tracker" in result
        assert "⚙️" in result  # Implementing phase emoji
        assert "Overall Progress" in result
        assert "Files Created: 5" in result
        assert "Commands: 20" in result

    def test_render_log_viewer(self) -> None:
        """Test log viewer rendering."""
        logs = [
            {
                "timestamp": "2023-01-01T10:00:00",
                "level": "INFO",
                "message": "Application started",
            },
            {
                "timestamp": "2023-01-01T10:01:00",
                "level": "WARNING",
                "message": "Configuration missing",
            },
            {
                "timestamp": "2023-01-01T10:02:00",
                "level": "ERROR",
                "message": "Connection failed",
            },
        ]

        result = self.renderer.render_widget(
            WidgetType.LOG_VIEWER,
            {"logs": logs},
            {"max_lines": 5},
        )

        assert isinstance(result, str)
        assert "Recent Logs" in result
        assert "Application started" in result
        assert "Configuration missing" in result
        assert "Connection failed" in result
        assert "INFO:" in result
        assert "WARNING:" in result
        assert "ERROR:" in result

    def test_render_metric_card(self) -> None:
        """Test metric card rendering."""
        metric = MetricCardData(
            title="CPU Usage",
            value=75.5,
            suffix="%",
            trend=5.2,
            color="warning",
            icon="🖥️",
            comparison="vs last hour",
        )

        result = self.renderer.render_widget(
            WidgetType.METRIC_CARD,
            metric,
            {},
        )

        assert isinstance(result, str)
        assert "CPU Usage" in result
        assert "75.50%" in result  # format_number adds precision
        assert "🖥️" in result
        assert "↗️ +5.2" in result
        assert "vs last hour" in result

    def test_render_status_indicator(self) -> None:
        """Test status indicator rendering."""
        status = StatusIndicatorData(
            status="running",
            label="Service Active",
            color="success",
            icon="✅",
            pulse=True,
        )

        result = self.renderer.render_widget(
            WidgetType.STATUS_INDICATOR,
            status,
            {},
        )

        assert isinstance(result, str)
        assert "RUNNING" in result
        assert "Service Active" in result
        assert "✅" in result
        assert "⟳" in result  # Pulse indicator

    def test_render_chart(self) -> None:
        """Test chart rendering."""
        now = datetime.now(UTC)
        points = [
            ChartDataPoint(x=now, y=10),
            ChartDataPoint(x="2023-01-02", y=20),
            ChartDataPoint(x=3, y=30),
        ]

        chart = ChartData(
            title="Test Chart",
            chart_type="line",
            data_points=points,
            x_label="Time",
            y_label="Value",
        )

        result = self.renderer.render_widget(
            WidgetType.CHART,
            chart,
            {},
        )

        assert isinstance(result, str)
        assert "Test Chart" in result
        assert "Max: 30, Min: 10" in result
        assert "█" in result  # Bar character
        assert "░" in result  # Empty bar character

    def test_render_table(self) -> None:
        """Test generic table rendering."""
        table_data = {
            "headers": ["Name", "Status", "Count"],
            "rows": [
                ["Session 1", "Active", "5"],
                ["Session 2", "Idle", "3"],
                {"Name": "Session 3", "Status": "Error", "Count": "0"},
            ],
        }

        result = self.renderer.render_widget(
            WidgetType.TABLE,
            table_data,
            {},
        )

        assert isinstance(result, str)
        assert "Name" in result
        assert "Status" in result
        assert "Count" in result
        assert "Session 1" in result
        assert "Active" in result

    def test_render_generic_widget(self) -> None:
        """Test generic widget fallback rendering."""
        result = self.renderer._render_generic_widget(
            WidgetType.METRIC_CARD,
            {"test": "data"},
            {},
        )

        assert isinstance(result, str)
        assert "Widget Type: metric_card" in result
        assert "Data:" in result

    def test_render_layout_vertical(self) -> None:
        """Test vertical layout rendering."""
        widgets = [
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test 1", value=10),
            },
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test 2", value=20),
            },
        ]

        result = self.renderer.render_layout(widgets, {"type": "vertical", "spacing": 2})

        assert isinstance(result, str)
        assert "Test 1" in result
        assert "Test 2" in result

    def test_render_layout_horizontal(self) -> None:
        """Test horizontal layout rendering."""
        widgets = [
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test 1", value=10),
            },
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test 2", value=20),
            },
        ]

        result = self.renderer.render_layout(widgets, {"type": "horizontal"})

        assert isinstance(result, str)
        assert "Test 1" in result
        assert "Test 2" in result

    def test_render_layout_grid(self) -> None:
        """Test grid layout rendering."""
        widgets = [
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test 1", value=10),
            },
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test 2", value=20),
            },
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test 3", value=30),
            },
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test 4", value=40),
            },
        ]

        result = self.renderer.render_layout(widgets, {"type": "grid", "columns": 2})

        assert isinstance(result, str)
        assert "Test 1" in result
        assert "Test 4" in result

    def test_render_container_with_border(self) -> None:
        """Test container rendering with border."""
        content = "Test content"

        result = self.renderer.render_container(
            content,
            {
                "title": "Test Container",
                "border": True,
                "style": "blue",
                "rounded": True,
                "padding": (1, 2),
            },
        )

        assert isinstance(result, str)
        assert "Test content" in result

    def test_render_container_without_border(self) -> None:
        """Test container rendering without border."""
        content = "Test content"

        result = self.renderer.render_container(
            content,
            {"border": False},
        )

        assert result == content

    def test_error_handling_invalid_data(self) -> None:
        """Test error handling with invalid data."""
        # Test with invalid health data
        result = self.renderer.render_widget(
            WidgetType.HEALTH_METER,
            "invalid_data",
            {},
        )

        assert result == "Invalid health data"

        # Test with invalid session data
        result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            None,
            {},
        )

        assert isinstance(result, str)

    def test_empty_session_list(self) -> None:
        """Test rendering empty session list."""
        result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            [],
            {"view_mode": "cards"},
        )

        assert result == "No sessions found"

    def test_activity_heatmap_heat_levels(self) -> None:
        """Test different activity heat levels."""
        # High activity
        high_activity = ActivityData(
            entries=[],
            total_activities=100,
            active_days=10,
            activity_rate=85.0,
            current_streak=5,
        )

        result = self.renderer._render_activity_heatmap(high_activity, {})
        assert "🔥🔥🔥" in result

        # Medium activity
        medium_activity = ActivityData(
            entries=[],
            total_activities=50,
            active_days=5,
            activity_rate=65.0,
            current_streak=3,
        )

        result = self.renderer._render_activity_heatmap(medium_activity, {})
        assert "🔥🔥" in result

        # Low activity
        low_activity = ActivityData(
            entries=[],
            total_activities=10,
            active_days=2,
            activity_rate=45.0,
            current_streak=1,
        )

        result = self.renderer._render_activity_heatmap(low_activity, {})
        assert "🔥" in result

        # Very low activity
        very_low_activity = ActivityData(
            entries=[],
            total_activities=5,
            active_days=1,
            activity_rate=25.0,
            current_streak=0,
        )

        result = self.renderer._render_activity_heatmap(very_low_activity, {})
        assert "❄️" in result

    def test_progress_phase_emojis(self) -> None:
        """Test different progress phase emojis."""
        phases_and_emojis = [
            (ProgressPhase.STARTING, "🚀"),
            (ProgressPhase.ANALYZING, "🔍"),
            (ProgressPhase.IMPLEMENTING, "⚙️"),
            (ProgressPhase.TESTING, "🧪"),
            (ProgressPhase.COMPLETING, "✅"),
            (ProgressPhase.COMPLETED, "🎉"),
            (ProgressPhase.IDLE, "💤"),
            (ProgressPhase.ERROR, "❌"),
        ]

        for phase, emoji in phases_and_emojis:
            progress = ProgressData(
                phase=phase,
                phase_progress=50.0,
                overall_progress=25.0,
            )

            result = self.renderer._render_progress_tracker(progress, {})
            assert emoji in result

    def test_metric_card_trend_indicators(self) -> None:
        """Test metric card trend indicators."""
        # Positive trend
        positive_metric = MetricCardData(
            title="Test",
            value=100,
            trend=5.2,
        )
        result = self.renderer._render_metric_card(positive_metric, {})
        assert "↗️ +5.2" in result

        # Negative trend
        negative_metric = MetricCardData(
            title="Test",
            value=100,
            trend=-3.1,
        )
        result = self.renderer._render_metric_card(negative_metric, {})
        assert "↘️ -3.1" in result

        # No trend
        no_trend_metric = MetricCardData(
            title="Test",
            value=100,
            trend=0,
        )
        result = self.renderer._render_metric_card(no_trend_metric, {})
        assert "➡️ 0" in result

        # No trend data
        no_trend_data_metric = MetricCardData(
            title="Test",
            value=100,
            trend=None,
        )
        result = self.renderer._render_metric_card(no_trend_data_metric, {})
        assert "↗️" not in result
        assert "↘️" not in result
        assert "➡️" not in result


class TestTUIRendererIntegration:
    """Integration tests for TUI renderer."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.console = Console(width=120, height=30, force_terminal=True)
        self.renderer = TUIRenderer(console=self.console)

    def test_full_dashboard_rendering(self) -> None:
        """Test rendering a complete dashboard."""
        now = datetime.now(UTC)

        # Create sample data
        session = SessionData(
            name="main-session",
            id="session-1",
            status=SessionStatus.ACTIVE,
            created_at=now,
            windows=[WindowData(id="1", name="editor", active=True, panes=3)],
            panes=3,
            claude_active=True,
            cpu_usage=25.5,
            memory_usage=45.2,
        )

        health = HealthData(
            overall_score=82,
            overall_level=HealthLevel.GOOD,
            categories=[
                HealthCategoryData(
                    category="build",
                    score=90,
                    level=HealthLevel.EXCELLENT,
                    message="All tests passing",
                ),
            ],
            last_updated=now,
        )

        progress = ProgressData(
            phase=ProgressPhase.IMPLEMENTING,
            phase_progress=65.0,
            overall_progress=40.0,
            files_created=8,
            files_modified=15,
            commands_executed=25,
            commands_succeeded=23,
            commands_failed=2,
        )

        # Render widgets
        session_result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            [session],
            {"view_mode": "table"},
        )

        health_result = self.renderer.render_widget(
            WidgetType.HEALTH_METER,
            health,
            {},
        )

        progress_result = self.renderer.render_widget(
            WidgetType.PROGRESS_TRACKER,
            progress,
            {},
        )

        # All should be valid strings
        assert isinstance(session_result, str)
        assert len(session_result) > 0
        assert isinstance(health_result, str)
        assert len(health_result) > 0
        assert isinstance(progress_result, str)
        assert len(progress_result) > 0

        # Should contain expected content
        assert "main-session" in session_result
        assert "82%" in health_result
        assert "65%" in progress_result  # Progress shows as integer percentage
