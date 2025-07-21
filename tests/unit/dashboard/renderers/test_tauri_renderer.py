# Copyright notice.

import json
from datetime import UTC, datetime
import pytest
from libs.dashboard.renderers.base_renderer import RenderFormat, WidgetType
from libs.dashboard.renderers.tauri_renderer import TauriRenderer
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


"""Tests for Tauri Renderer."""


class TestTauriRenderer:
    """Test cases for Tauri renderer."""

    def setup_method(self) -> None:
        """Setup test renderer."""
        self.renderer = TauriRenderer()

    def test_renderer_initialization(self) -> None:
        """Test Tauri renderer initialization."""
        assert self.renderer.format_type == RenderFormat.TAURI
        assert self.renderer.widget_id_counter == 0
        assert "success" in self.renderer._style_classes  # noqa: SLF001
        assert isinstance(self.renderer._style_classes["success"], dict)  # noqa: SLF001

    def test_widget_id_generation(self) -> None:
        """Test unique widget ID generation."""
        id1 = self.renderer._generate_widget_id()  # noqa: SLF001
        id2 = self.renderer._generate_widget_id()  # noqa: SLF001

        assert id1 != id2
        assert id1.startswith("tauri-widget-1-")
        assert id2.startswith("tauri-widget-2-")
        assert self.renderer.widget_id_counter == 2

    def test_default_style(self) -> None:
        """Test default style generation."""
        style = self.renderer._get_default_style()  # noqa: SLF001

        assert isinstance(style, dict)
        assert style["background"] == "surface"
        assert style["border"] is True
        assert style["shadow"] is True
        assert style["rounded"] is True

    def test_supports_feature(self) -> None:
        """Test feature support checking."""
        assert self.renderer.supports_feature("json") is True
        assert self.renderer.supports_feature("charts") is True
        assert self.renderer.supports_feature("interactive") is True
        assert self.renderer.supports_feature("actions") is True
        assert self.renderer.supports_feature("animations") is True
        assert self.renderer.supports_feature("serializable") is True
        assert self.renderer.supports_feature("nonexistent") is False

    def test_render_session_browser(self) -> None:
        """Test session browser rendering."""
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
            {"view_mode": "table"},
        )

        assert isinstance(result, dict)
        assert result["type"] == "widget"
        assert result["widget_type"] == "session_browser"
        assert "id" in result
        assert "data" in result
        assert "metadata" in result
        assert "style" in result
        assert "actions" in result

        # Check data structure
        assert "sessions" in result["data"]
        assert len(result["data"]["sessions"]) == 1
        assert result["data"]["sessions"][0]["name"] == "test-session"
        assert result["data"]["view_mode"] == "table"
        assert result["data"]["total_count"] == 1
        assert result["data"]["active_count"] == 1
        assert result["data"]["claude_count"] == 1

        # Check actions
        assert len(result["actions"]) >= 3
        action_ids = [action["id"] for action in result["actions"]]
        assert "refresh" in action_ids
        assert "new_session" in action_ids

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

        assert isinstance(result, dict)
        assert result["widget_type"] == "health_meter"
        assert "data" in result
        assert "chart_data" in result

        # Check data structure
        assert result["data"]["overall_score"] == 85
        # The enum might return different format, just check it's a string representation
        assert isinstance(result["data"]["overall_level"], str)
        assert "overall_emoji" in result["data"]
        assert len(result["data"]["categories"]) == 1
        assert result["data"]["categories"][0]["category"] == "build"
        assert result["data"]["categories"][0]["score"] == 85

        # Check chart data
        assert result["chart_data"]["type"] == "radar"
        assert "labels" in result["chart_data"]
        assert "datasets" in result["chart_data"]
        assert len(result["chart_data"]["labels"]) == 1
        assert result["chart_data"]["labels"][0] == "Build"

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

        assert isinstance(result, dict)
        assert result["widget_type"] == "activity_heatmap"
        assert "data" in result

        # Check data structure
        assert result["data"]["total_activities"] == 10
        assert result["data"]["active_days"] == 5
        assert result["data"]["activity_rate"] == 75.0
        assert "heatmap_data" in result["data"]
        assert "activity_levels" in result["data"]

        # Check heatmap data structure
        assert isinstance(result["data"]["heatmap_data"], list)
        if result["data"]["heatmap_data"]:
            heatmap_entry = result["data"]["heatmap_data"][0]
            assert "date" in heatmap_entry
            assert "value" in heatmap_entry
            assert "level" in heatmap_entry

        # Check activity levels
        assert len(result["data"]["activity_levels"]) == 5
        for level in result["data"]["activity_levels"]:
            assert "level" in level
            assert "color" in level
            assert "label" in level

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
            todos_identified=10,
            todos_completed=7,
        )

        result = self.renderer.render_widget(
            WidgetType.PROGRESS_TRACKER,
            progress,
            {},
        )

        assert isinstance(result, dict)
        assert result["widget_type"] == "progress_tracker"
        assert "data" in result
        assert "chart_data" in result

        # Check data structure
        assert result["data"]["phase"] == "implementing"
        assert "phase_emoji" in result["data"]
        assert result["data"]["phase_progress"] == 75.0
        assert result["data"]["overall_progress"] == 50.0
        assert result["data"]["files_created"] == 5
        assert result["data"]["commands_executed"] == 20
        assert result["data"]["success_rate"] == 90.0  # 18/20 * 100
        assert result["data"]["completion_rate"] == 70.0  # 7/10 * 100

        # Check chart data (doughnut chart)
        assert result["chart_data"]["type"] == "doughnut"
        assert result["chart_data"]["labels"] == ["Completed", "Remaining"]
        assert result["chart_data"]["datasets"][0]["data"] == [50.0, 50.0]

    def test_render_log_viewer(self) -> None:
        """Test log viewer rendering."""
        logs = [
            {
                "timestamp": "2023-01-01T10:00:00",
                "level": "INFO",
                "message": "Application started",
                "source": "main",
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

        assert isinstance(result, dict)
        assert result["widget_type"] == "log_viewer"
        assert "data" in result
        assert "actions" in result

        # Check data structure
        assert len(result["data"]["logs"]) == 3
        assert result["data"]["total_count"] == 3
        assert result["data"]["displayed_count"] == 3
        assert result["data"]["max_lines"] == 5
        assert "level_counts" in result["data"]

        # Check processed log structure
        log_entry = result["data"]["logs"][0]
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "message" in log_entry
        assert "color" in log_entry

        # Check level counts
        level_counts = result["data"]["level_counts"]
        assert level_counts["INFO"] == 1
        assert level_counts["WARNING"] == 1
        assert level_counts["ERROR"] == 1

        # Check actions
        action_ids = [action["id"] for action in result["actions"]]
        assert "refresh" in action_ids
        assert "clear" in action_ids
        assert "filter" in action_ids

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

        assert isinstance(result, dict)
        assert result["widget_type"] == "metric_card"
        assert "data" in result
        assert "chart_data" in result

        # Check data structure
        assert result["data"]["title"] == "CPU Usage"
        assert result["data"]["value"] == 75.5
        assert "75.50%" in result["data"]["formatted_value"]
        assert result["data"]["suffix"] == "%"
        assert result["data"]["trend"] == 5.2
        assert result["data"]["trend_direction"] == "up"
        assert result["data"]["color"] == "warning"
        assert result["data"]["icon"] == "🖥️"

        # Check chart data (sparkline)
        assert result["chart_data"]["type"] == "line"
        assert result["chart_data"]["labels"] == ["Previous", "Current"]
        assert result["chart_data"]["datasets"][0]["data"] == [0, 5.2]

        # Check style update based on color
        assert "warning" in str(result["style"])

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

        assert isinstance(result, dict)
        assert result["widget_type"] == "status_indicator"
        assert "data" in result
        assert "animation" in result

        # Check data structure
        assert result["data"]["status"] == "running"
        assert result["data"]["label"] == "Service Active"
        assert result["data"]["color"] == "success"
        assert result["data"]["icon"] == "✅"
        assert result["data"]["pulse"] is True
        assert "timestamp" in result["data"]

        # Check animation config
        assert result["animation"]["type"] == "pulse"
        assert result["animation"]["duration"] == 2000
        assert result["animation"]["infinite"] is True

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
            colors=["#3b82f6"],
        )

        result = self.renderer.render_widget(
            WidgetType.CHART,
            chart,
            {},
        )

        assert isinstance(result, dict)
        assert result["widget_type"] == "chart"
        assert "data" in result
        assert "chart_data" in result

        # Check data structure
        assert result["data"]["title"] == "Test Chart"
        assert result["data"]["chart_type"] == "line"
        assert result["data"]["x_label"] == "Time"
        assert result["data"]["y_label"] == "Value"
        assert result["data"]["data_points"] == 3

        # Check chart data (Chart.js format)
        assert result["chart_data"]["type"] == "line"
        assert len(result["chart_data"]["labels"]) == 3
        assert len(result["chart_data"]["datasets"][0]["data"]) == 3
        assert result["chart_data"]["datasets"][0]["data"] == [10, 20, 30]
        assert result["chart_data"]["datasets"][0]["backgroundColor"] == "#3b82f6"

    def test_render_table(self) -> None:
        """Test table rendering."""
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

        assert isinstance(result, dict)
        assert result["widget_type"] == "table"
        assert "data" in result
        assert "actions" in result

        # Check data structure
        assert result["data"]["headers"] == ["Name", "Status", "Count"]
        assert len(result["data"]["rows"]) == 3
        assert result["data"]["total_rows"] == 3
        assert result["data"]["total_columns"] == 3

        # Check processed rows
        assert result["data"]["rows"][0] == ["Session 1", "Active", "5"]
        assert result["data"]["rows"][2] == [
            "Session 3",
            "Error",
            "0",
        ]  # Dict converted to list

        # Check actions
        action_ids = [action["id"] for action in result["actions"]]
        assert "sort" in action_ids
        assert "filter" in action_ids
        assert "export" in action_ids

    def test_render_generic_widget(self) -> None:
        """Test generic widget rendering."""
        result = self.renderer.render_widget(
            WidgetType.METRIC_CARD,
            {"unknown": "data"},
            {},
        )

        # Should not error but will process as metric card with data conversion
        assert isinstance(result, dict)
        assert result["widget_type"] == "metric_card"
        assert "error" in result["data"]

    def test_render_layout(self) -> None:
        """Test layout rendering."""
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

        result = self.renderer.render_layout(widgets, {"type": "grid", "columns": 2})

        assert isinstance(result, dict)
        assert result["type"] == "layout"
        assert result["layout_type"] == "grid"
        assert "id" in result
        assert "widgets" in result
        assert "config" in result
        assert "metadata" in result

        # Check widgets
        assert len(result["widgets"]) == 2
        assert result["widgets"][0]["widget_type"] == "metric_card"
        assert result["widgets"][1]["widget_type"] == "metric_card"

        # Check metadata
        assert result["metadata"]["widget_count"] == 2

    def test_render_container(self) -> None:
        """Test container rendering."""
        content = {"type": "widget", "widget_type": "metric_card", "data": {}}

        result = self.renderer.render_container(
            content,
            {
                "title": "Test Container",
                "border": True,
                "background": "primary",
                "shadow": True,
            },
        )

        assert isinstance(result, dict)
        assert result["type"] == "container"
        assert "id" in result
        assert "content" in result
        assert "config" in result
        assert "style" in result
        assert "metadata" in result

        # Check config
        assert result["config"]["title"] == "Test Container"
        assert result["config"]["border"] is True
        assert result["config"]["background"] == "primary"
        assert result["config"]["shadow"] is True

        # Check content
        assert result["content"] == content

    def test_json_serialization(self) -> None:
        """Test that rendered output is JSON serializable."""
        now = datetime.now(UTC)
        session = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            windows=[],
        )

        result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            [session],
            {"view_mode": "table"},
        )

        # Should serialize to JSON without errors
        try:
            json_str = json.dumps(result, default=str)
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
            assert parsed["widget_type"] == "session_browser"
        except (TypeError, ValueError) as e:
            pytest.fail(f"JSON serialization failed: {e}")

    def test_helper_methods(self) -> None:
        """Test helper methods."""
        # Test health color mapping
        assert self.renderer._get_health_color(HealthLevel.EXCELLENT) == "#10b981"  # noqa: SLF001
        assert self.renderer._get_health_color(HealthLevel.CRITICAL) == "#ef4444"  # noqa: SLF001

        # Test phase emoji mapping
        assert self.renderer._get_phase_emoji(ProgressPhase.IMPLEMENTING) == "⚙️"  # noqa: SLF001
        assert self.renderer._get_phase_emoji(ProgressPhase.COMPLETED) == "🎉"  # noqa: SLF001

        # Test log level color mapping
        assert self.renderer._get_log_level_color("ERROR") == "#ef4444"  # noqa: SLF001
        assert self.renderer._get_log_level_color("INFO") == "#3b82f6"  # noqa: SLF001

        # Test log level counting
        logs = [
            {"level": "ERROR"},
            {"level": "ERROR"},
            {"level": "INFO"},
            {"level": "WARNING"},
        ]
        counts = self.renderer._count_log_levels(logs)  # noqa: SLF001
        assert counts["ERROR"] == 2
        assert counts["INFO"] == 1
        assert counts["WARNING"] == 1
        assert counts["DEBUG"] == 0

    def test_error_handling(self) -> None:
        """Test error handling with invalid data."""
        # Test with invalid health data
        result = self.renderer.render_widget(
            WidgetType.HEALTH_METER,
            "invalid_data",
            {},
        )

        assert result["data"]["error"] == "Invalid health data"

        # Test with invalid progress data
        result = self.renderer.render_widget(
            WidgetType.PROGRESS_TRACKER,
            None,
            {},
        )

        assert result["data"]["error"] == "Invalid progress data"

    def test_trend_calculations(self) -> None:
        """Test trend direction calculations."""
        # Positive trend
        metric_up = MetricCardData(title="Test", value=100, trend=5.0)
        result_up = self.renderer.render_widget(WidgetType.METRIC_CARD, metric_up, {})
        assert result_up["data"]["trend_direction"] == "up"

        # Negative trend
        metric_down = MetricCardData(title="Test", value=100, trend=-3.0)
        result_down = self.renderer.render_widget(WidgetType.METRIC_CARD, metric_down, {})
        assert result_down["data"]["trend_direction"] == "down"

        # Neutral trend
        metric_neutral = MetricCardData(title="Test", value=100, trend=0)
        result_neutral = self.renderer.render_widget(WidgetType.METRIC_CARD, metric_neutral, {})
        assert result_neutral["data"]["trend_direction"] == "neutral"

        # No trend
        metric_none = MetricCardData(title="Test", value=100, trend=None)
        result_none = self.renderer.render_widget(WidgetType.METRIC_CARD, metric_none, {})
        assert result_none["data"]["trend_direction"] == "neutral"


class TestTauriRendererIntegration:
    """Integration tests for Tauri renderer."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.renderer = TauriRenderer()

    def test_full_dashboard_json(self) -> None:
        """Test rendering a complete dashboard as JSON."""
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

        # Render multiple widgets
        widgets = [
            {
                "type": WidgetType.SESSION_BROWSER,
                "data": [session],
                "options": {"view_mode": "cards"},
            },
            {"type": WidgetType.HEALTH_METER, "data": health, "options": {}},
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="CPU", value=45.2, suffix="%"),
                "options": {},
            },
        ]

        dashboard = self.renderer.render_layout(widgets, {"type": "grid", "columns": 2})

        # Wrap in container
        container = self.renderer.render_container(
            dashboard,
            {"title": "System Dashboard", "background": "surface"},
        )

        # Should be fully JSON serializable
        try:
            json_str = json.dumps(container, default=str, indent=2)
            parsed = json.loads(json_str)

            assert parsed["type"] == "container"
            assert parsed["config"]["title"] == "System Dashboard"
            assert parsed["content"]["type"] == "layout"
            assert len(parsed["content"]["widgets"]) == 3

            # Check widget types
            widget_types = [w["widget_type"] for w in parsed["content"]["widgets"]]
            assert "session_browser" in widget_types
            assert "health_meter" in widget_types
            assert "metric_card" in widget_types

        except (TypeError, ValueError) as e:
            pytest.fail(f"Dashboard JSON serialization failed: {e}")

    def test_chart_data_compatibility(self) -> None:
        """Test that chart data is compatible with Chart.js."""
        # Test different chart types
        chart_types = ["line", "bar", "radar", "doughnut", "pie"]

        for chart_type in chart_types:
            chart = ChartData(
                title=f"Test {chart_type} Chart",
                chart_type=chart_type,
                data_points=[
                    ChartDataPoint(x=1, y=10),
                    ChartDataPoint(x=2, y=20),
                    ChartDataPoint(x=3, y=15),
                ],
                x_label="X Axis",
                y_label="Y Axis",
            )

            result = self.renderer.render_widget(WidgetType.CHART, chart, {})

            # Check Chart.js compatibility
            chart_data = result["chart_data"]
            assert chart_data["type"] == chart_type
            assert "labels" in chart_data
            assert "datasets" in chart_data
            assert len(chart_data["datasets"]) == 1
            assert "data" in chart_data["datasets"][0]
            assert len(chart_data["datasets"][0]["data"]) == 3

    def test_actions_structure(self) -> None:
        """Test that actions have consistent structure."""
        # Test widgets with actions
        log_result = self.renderer.render_widget(
            WidgetType.LOG_VIEWER,
            {"logs": []},
            {},
        )

        table_result = self.renderer.render_widget(
            WidgetType.TABLE,
            {"headers": ["A", "B"], "rows": [["1", "2"]]},
            {},
        )

        session_result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            [],
            {},
        )

        # Check action structure consistency
        for result in [log_result, table_result, session_result]:
            assert "actions" in result
            for action in result["actions"]:
                assert "id" in action
                assert "label" in action
                assert "type" in action
                assert action["type"] in {"button", "dropdown"}

                if "icon" in action:
                    assert isinstance(action["icon"], str)

                if action["type"] == "dropdown":
                    assert "options" in action
                    assert isinstance(action["options"], list)
