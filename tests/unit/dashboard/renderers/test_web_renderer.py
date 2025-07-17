"""Tests for Web Renderer."""

import json
from datetime import datetime

import pytest

from libs.dashboard.renderers.base_renderer import RenderFormat, WidgetType
from libs.dashboard.renderers.web_renderer import WebRenderer
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


class TestWebRenderer:
    """Test cases for Web renderer."""

    def setup_method(self):
        """Setup test renderer."""
        self.renderer = WebRenderer()

    def test_renderer_initialization(self):
        """Test Web renderer initialization."""
        assert self.renderer.format_type == RenderFormat.WEB
        assert self.renderer.component_id_counter == 0
        assert "success" in self.renderer._color_classes
        assert "active" in self.renderer._status_classes

    def test_component_id_generation(self):
        """Test unique component ID generation."""
        id1 = self.renderer._generate_component_id()
        id2 = self.renderer._generate_component_id()

        assert id1 != id2
        assert id1.startswith("widget-1-")
        assert id2.startswith("widget-2-")
        assert self.renderer.component_id_counter == 2

    def test_health_color_class_mapping(self):
        """Test health level to CSS class mapping."""
        assert self.renderer._get_health_color_class(HealthLevel.EXCELLENT) == "green-600"
        assert self.renderer._get_health_color_class(HealthLevel.GOOD) == "blue-600"
        assert self.renderer._get_health_color_class(HealthLevel.WARNING) == "yellow-600"
        assert self.renderer._get_health_color_class(HealthLevel.CRITICAL) == "red-600"
        assert self.renderer._get_health_color_class(HealthLevel.UNKNOWN) == "gray-600"

    def test_supports_feature(self):
        """Test feature support checking."""
        assert self.renderer.supports_feature("html") is True
        assert self.renderer.supports_feature("css") is True
        assert self.renderer.supports_feature("javascript") is True
        assert self.renderer.supports_feature("interactive") is True
        assert self.renderer.supports_feature("responsive") is True
        assert self.renderer.supports_feature("themes") is True
        assert self.renderer.supports_feature("animations") is True
        assert self.renderer.supports_feature("nonexistent") is False

    def test_embed_widget_data(self):
        """Test JavaScript data embedding."""
        component_id = "test-widget-123"
        test_data = {"type": "test", "value": 42, "name": "test widget"}

        result = self.renderer._embed_widget_data(component_id, test_data)

        assert isinstance(result, str)
        assert component_id in result
        assert "window.widgetData" in result
        assert '"type": "test"' in result
        assert '"value": 42' in result
        assert "<script>" in result
        assert "</script>" in result

    def test_render_session_browser_table(self):
        """Test session browser table view rendering."""
        now = datetime.now()
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
        assert "session-browser-table" in result
        assert "test-session" in result
        assert "ACTIVE" in result
        assert "🤖 Active" in result
        assert "table" in result
        assert "thead" in result
        assert "tbody" in result
        assert "window.widgetData" in result

    def test_render_session_browser_cards(self):
        """Test session browser cards view rendering."""
        now = datetime.now()
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
        assert "session-browser-cards" in result
        assert "test-session" in result
        assert "grid" in result
        assert "📋" in result
        assert "window.widgetData" in result

    def test_render_session_browser_list(self):
        """Test session browser list view rendering."""
        now = datetime.now()
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
            {"view_mode": "list"},
        )

        assert isinstance(result, str)
        assert "session-browser-list" in result
        assert "test-session" in result
        assert "📋" in result
        assert "<ul" in result
        assert "<li" in result
        assert "window.widgetData" in result

    def test_render_health_meter(self):
        """Test health meter rendering."""
        now = datetime.now()
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
        assert "health-meter" in result
        assert "Project Health" in result
        assert "85%" in result
        assert "Build" in result
        assert "progress" in result or "bg-blue-600" in result
        assert "window.widgetData" in result

    def test_render_activity_heatmap(self):
        """Test activity heatmap rendering."""
        now = datetime.now()
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
        assert "activity-heatmap" in result
        assert "Activity Overview" in result
        assert "Total Activities:" in result and ">10<" in result
        assert "Active Days:" in result and ">5<" in result
        assert "75.0%" in result
        assert "🔥" in result or "🔥🔥" in result
        assert "window.widgetData" in result

    def test_render_progress_tracker(self):
        """Test progress tracker rendering."""
        now = datetime.now()

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
        assert "progress-tracker" in result
        assert "Progress Tracker" in result
        assert "⚙️" in result
        assert "50%" in result  # overall progress
        assert "75%" in result  # phase progress
        assert "Files Created:" in result and ">5<" in result
        assert "Commands:" in result and ">20<" in result
        assert "window.widgetData" in result

    def test_render_log_viewer(self):
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
        assert "log-viewer" in result
        assert "Recent Logs" in result
        assert "Application started" in result
        assert "Configuration missing" in result
        assert "Connection failed" in result
        assert "INFO" in result
        assert "WARNING" in result
        assert "ERROR" in result
        assert "window.widgetData" in result

    def test_render_metric_card(self):
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
        assert "metric-card" in result
        assert "CPU Usage" in result
        assert "75.50%" in result  # formatted number
        assert "🖥️" in result
        assert "↗️ +5.2" in result
        assert "vs last hour" in result
        assert "window.widgetData" in result

    def test_render_status_indicator(self):
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
        assert "status-indicator" in result
        assert "running" in result  # Status is lowercase in web renderer
        assert "Service Active" in result
        assert "✅" in result
        assert "animate-pulse" in result
        assert "window.widgetData" in result

    def test_render_chart(self):
        """Test chart rendering."""
        now = datetime.now()
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
        assert "chart-widget" in result
        assert "Test Chart" in result
        assert "chart-container" in result
        assert "Chart data loading..." in result
        assert "window.widgetData" in result

    def test_render_table(self):
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
        assert "table-widget" in result
        assert "Name" in result
        assert "Status" in result
        assert "Count" in result
        assert "Session 1" in result
        assert "Active" in result
        assert "<table" in result
        assert "<thead" in result
        assert "<tbody" in result
        assert "window.widgetData" in result

    def test_render_generic_widget(self):
        """Test generic widget fallback rendering."""
        result = self.renderer._render_generic_widget(
            WidgetType.METRIC_CARD,
            {"test": "data"},
            {},
            "test-component-123",
        )

        assert isinstance(result, str)
        assert "generic-widget" in result
        assert "Metric Card" in result
        assert "Widget renderer not implemented" in result
        assert "test-component-123" in result

    def test_render_error_widget(self):
        """Test error widget rendering."""
        result = self.renderer._render_error_widget(
            "Test error message",
            "error-component-123",
        )

        assert isinstance(result, str)
        assert "error-widget" in result
        assert "Rendering Error" in result
        assert "Test error message" in result
        assert "error-component-123" in result
        assert "❌" in result

    def test_render_layout_vertical(self):
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

        result = self.renderer.render_layout(widgets, {"type": "vertical", "spacing": "space-y-6"})

        assert isinstance(result, str)
        assert "dashboard-layout-vertical" in result
        assert "space-y-6" in result
        assert "Test 1" in result
        assert "Test 2" in result

    def test_render_layout_flex(self):
        """Test flex layout rendering."""
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

        result = self.renderer.render_layout(widgets, {"type": "flex", "direction": "row", "gap": "gap-6"})

        assert isinstance(result, str)
        assert "dashboard-layout-flex" in result
        assert "flex-row" in result
        assert "gap-6" in result
        assert "flex-1" in result
        assert "Test 1" in result
        assert "Test 2" in result

    def test_render_layout_grid(self):
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

        result = self.renderer.render_layout(widgets, {"type": "grid", "columns": 2, "gap": "gap-4"})

        assert isinstance(result, str)
        assert "dashboard-layout-grid" in result
        assert "grid-cols-1 md:grid-cols-2" in result
        assert "gap-4" in result
        assert "Test 1" in result
        assert "Test 4" in result

    def test_render_container_with_border(self):
        """Test container rendering with border."""
        content = "<p>Test content</p>"

        result = self.renderer.render_container(
            content,
            {
                "title": "Test Container",
                "border": True,
                "style": "info",
                "padding": "p-6",
            },
        )

        assert isinstance(result, str)
        assert "dashboard-container" in result
        assert "Test Container" in result
        assert "Test content" in result
        assert "border" in result
        assert "rounded-lg" in result
        assert "p-6" in result

    def test_render_container_without_border(self):
        """Test container rendering without border."""
        content = "<p>Test content</p>"

        result = self.renderer.render_container(
            content,
            {"border": False},
        )

        assert isinstance(result, str)
        assert "Test content" in result
        assert "border" not in result

    def test_html_escaping(self):
        """Test HTML escaping for security."""
        malicious_data = MetricCardData(
            title="<script>alert('xss')</script>",
            value=100,
            comparison="<img src=x onerror=alert('xss')>",
        )

        result = self.renderer.render_widget(
            WidgetType.METRIC_CARD,
            malicious_data,
            {},
        )

        # Should be escaped in the content area (not in the embedded script)
        assert "&lt;script&gt;" in result
        assert "&lt;img" in result
        # Check that malicious content is properly escaped in HTML content
        # The title should be escaped in the dt element
        assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in result
        # The comparison should be escaped
        assert "&lt;img src=x onerror=alert(&#x27;xss&#x27;)&gt;" in result

    def test_error_handling_invalid_data(self):
        """Test error handling with invalid data."""
        # Test with invalid health data
        result = self.renderer.render_widget(
            WidgetType.HEALTH_METER,
            "invalid_data",
            {},
        )

        assert "error-widget" in result
        assert "Invalid health data" in result

        # Test with invalid session data produces valid HTML
        result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            None,
            {},
        )

        assert isinstance(result, str)
        assert "session-browser" in result

    def test_activity_heatmap_heat_levels(self):
        """Test different activity heat levels."""
        # High activity
        high_activity = ActivityData(
            entries=[],
            total_activities=100,
            active_days=10,
            activity_rate=85.0,
            current_streak=5,
        )

        result = self.renderer._render_activity_heatmap(high_activity, {}, "test-1")
        assert "🔥🔥🔥" in result
        assert "text-red-600" in result

        # Medium activity
        medium_activity = ActivityData(
            entries=[],
            total_activities=50,
            active_days=5,
            activity_rate=65.0,
            current_streak=3,
        )

        result = self.renderer._render_activity_heatmap(medium_activity, {}, "test-2")
        assert "🔥🔥" in result
        assert "text-orange-600" in result

        # Low activity
        low_activity = ActivityData(
            entries=[],
            total_activities=10,
            active_days=2,
            activity_rate=45.0,
            current_streak=1,
        )

        result = self.renderer._render_activity_heatmap(low_activity, {}, "test-3")
        assert "🔥" in result
        assert "text-yellow-600" in result

        # Very low activity
        very_low_activity = ActivityData(
            entries=[],
            total_activities=5,
            active_days=1,
            activity_rate=25.0,
            current_streak=0,
        )

        result = self.renderer._render_activity_heatmap(very_low_activity, {}, "test-4")
        assert "❄️" in result
        assert "text-blue-600" in result

    def test_metric_card_trend_indicators(self):
        """Test metric card trend indicators."""
        # Positive trend
        positive_metric = MetricCardData(
            title="Test",
            value=100,
            trend=5.2,
        )
        result = self.renderer._render_metric_card(positive_metric, {}, "test-1")
        assert "↗️ +5.2" in result
        assert "text-green-600" in result

        # Negative trend
        negative_metric = MetricCardData(
            title="Test",
            value=100,
            trend=-3.1,
        )
        result = self.renderer._render_metric_card(negative_metric, {}, "test-2")
        assert "↘️ -3.1" in result
        assert "text-red-600" in result

        # No trend
        no_trend_metric = MetricCardData(
            title="Test",
            value=100,
            trend=0,
        )
        result = self.renderer._render_metric_card(no_trend_metric, {}, "test-3")
        assert "➡️ 0" in result
        assert "text-gray-600" in result

        # No trend data
        no_trend_data_metric = MetricCardData(
            title="Test",
            value=100,
            trend=None,
        )
        result = self.renderer._render_metric_card(no_trend_data_metric, {}, "test-4")
        assert "↗️" not in result and "↘️" not in result and "➡️" not in result

    def test_javascript_data_validity(self):
        """Test that embedded JavaScript data is valid JSON."""
        session = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(),
            windows=[],
        )

        result = self.renderer.render_widget(
            WidgetType.SESSION_BROWSER,
            [session],
            {"view_mode": "table"},
        )

        # Check that JavaScript data is embedded properly
        assert "window.widgetData" in result
        assert '"type": "session_browser"' in result
        assert '"view_mode": "table"' in result

        # Extract and validate JSON structure
        import re

        # Find the JSON data using regex
        json_match = re.search(r"window\.widgetData\[\'[^\']+\'\] = ({.*?});", result, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
            try:
                parsed_data = json.loads(json_str)
                assert isinstance(parsed_data, dict)
                assert "type" in parsed_data
                assert "sessions" in parsed_data
            except json.JSONDecodeError:
                pytest.fail("Generated JavaScript data is not valid JSON")
        else:
            pytest.fail("Could not find JavaScript data in output")


class TestWebRendererIntegration:
    """Integration tests for Web renderer."""

    def setup_method(self):
        """Setup test environment."""
        self.renderer = WebRenderer()

    def test_full_dashboard_rendering(self):
        """Test rendering a complete dashboard."""
        now = datetime.now()

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

        # All should be valid HTML strings
        assert isinstance(session_result, str) and len(session_result) > 0
        assert isinstance(health_result, str) and len(health_result) > 0
        assert isinstance(progress_result, str) and len(progress_result) > 0

        # Should contain expected content
        assert "main-session" in session_result
        assert "82%" in health_result
        assert "65%" in progress_result

        # Should have proper HTML structure
        assert session_result.count("<div") == session_result.count("</div>")
        assert health_result.count("<div") == health_result.count("</div>")
        assert progress_result.count("<div") == progress_result.count("</div>")

        # Should contain JavaScript data
        assert "window.widgetData" in session_result
        assert "window.widgetData" in health_result
        assert "window.widgetData" in progress_result

    def test_responsive_layout_rendering(self):
        """Test responsive layout with multiple breakpoints."""
        widgets = [
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="CPU", value=75.5, suffix="%"),
            },
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Memory", value=45.2, suffix="%"),
            },
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Disk", value=60.1, suffix="%"),
            },
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Network", value=12.3, suffix="MB/s"),
            },
        ]

        # Test grid layout
        grid_result = self.renderer.render_layout(
            widgets,
            {"type": "grid", "columns": 2, "gap": "gap-4"},
        )

        assert "grid-cols-1 md:grid-cols-2" in grid_result
        assert "gap-4" in grid_result
        assert "CPU" in grid_result
        assert "Network" in grid_result

        # Test flex layout
        flex_result = self.renderer.render_layout(
            widgets,
            {"type": "flex", "direction": "row", "gap": "gap-6"},
        )

        assert "flex-row" in flex_result
        assert "gap-6" in flex_result
        assert "flex-1" in flex_result

    def test_accessibility_attributes(self):
        """Test that rendered HTML includes accessibility attributes."""
        metric = MetricCardData(
            title="Response Time",
            value=150,
            suffix="ms",
        )

        result = self.renderer.render_widget(
            WidgetType.METRIC_CARD,
            metric,
            {},
        )

        # Should have semantic HTML structure
        assert "<dl>" in result  # Description list for key-value pairs
        assert "<dt" in result  # Term (with attributes)
        assert "<dd" in result  # Description (with attributes)

        # Table should have proper headers
        table_data = {"headers": ["Name", "Value"], "rows": [["Test", "123"]]}
        table_result = self.renderer.render_widget(
            WidgetType.TABLE,
            table_data,
            {},
        )

        assert "<th" in table_result
        assert "text-xs font-medium text-gray-500 uppercase" in table_result  # Proper header styling
