"""
Tests for BaseRenderer and related components
"""

from datetime import datetime

import pytest

from libs.dashboard.renderers.base_renderer import (
    BaseRenderer,
    RenderFormat,
    ThemeColor,
    WidgetType,
)
from libs.dashboard.renderers.registry import RendererRegistry


class TestRenderer(BaseRenderer):
    """Test implementation of BaseRenderer for testing"""

    def render_widget(self, widget_type, data, options=None):
        return f"<widget type='{widget_type.value}' data='{data}' />"

    def render_layout(self, widgets, layout_config=None):
        rendered_widgets = []
        for widget in widgets:
            widget_html = self.render_widget(
                widget.get("type", WidgetType.METRIC_CARD),
                widget.get("data", {}),
                widget.get("options"),
            )
            rendered_widgets.append(widget_html)
        return f"<layout>{' '.join(rendered_widgets)}</layout>"

    def render_container(self, content, container_config=None):
        return f"<container>{content}</container>"


class TestBaseRenderer:
    """Test cases for BaseRenderer abstract class"""

    def setup_method(self):
        """Setup test renderer"""
        self.renderer = TestRenderer(RenderFormat.WEB)

    def test_initialization(self):
        """Test renderer initialization"""
        assert self.renderer.format_type == RenderFormat.WEB
        assert self.renderer.theme is not None
        assert isinstance(self.renderer.theme, dict)
        assert "colors" in self.renderer.theme

    def test_initialization_with_custom_theme(self):
        """Test renderer initialization with custom theme"""
        custom_theme = {
            "colors": {"primary": "#FF0000"},
            "custom_setting": "test",
        }
        renderer = TestRenderer(RenderFormat.TUI, theme=custom_theme)

        assert renderer.theme == custom_theme
        assert renderer.theme["custom_setting"] == "test"

    def test_format_number(self):
        """Test number formatting"""
        # Integer
        assert self.renderer.format_number(1000) == "1,000"
        assert self.renderer.format_number(1000, suffix="%") == "1,000%"

        # Float
        assert self.renderer.format_number(1000.456) == "1,000.46"
        assert self.renderer.format_number(1000.456, precision=1) == "1,000.5"

        # None value
        assert self.renderer.format_number(None) == "N/A"

    def test_format_date(self):
        """Test date formatting"""
        # Datetime object
        dt = datetime(2023, 12, 25, 15, 30, 45)
        assert self.renderer.format_date(dt) == "2023-12-25 15:30"
        assert self.renderer.format_date(dt, "%Y-%m-%d") == "2023-12-25"

        # String date
        assert self.renderer.format_date("2023-12-25 15:30:45") == "2023-12-25 15:30"
        assert self.renderer.format_date("2023-12-25") == "2023-12-25 00:00"

        # None value
        assert self.renderer.format_date(None) == "N/A"

    def test_format_percentage(self):
        """Test percentage formatting"""
        assert self.renderer.format_percentage(85.5) == "85.5%"
        assert self.renderer.format_percentage(85.567, precision=2) == "85.57%"
        assert self.renderer.format_percentage(None) == "N/A"

    def test_format_bytes(self):
        """Test bytes formatting"""
        assert self.renderer.format_bytes(1024) == "1.0 KB"
        assert self.renderer.format_bytes(1024 * 1024) == "1.0 MB"
        assert self.renderer.format_bytes(1024 * 1024 * 1024) == "1.0 GB"
        assert self.renderer.format_bytes(None) == "N/A"

    def test_format_duration(self):
        """Test duration formatting"""
        assert self.renderer.format_duration(30) == "30.0s"
        assert self.renderer.format_duration(90) == "1m 30s"
        assert self.renderer.format_duration(3661) == "1h 1m"
        assert self.renderer.format_duration(None) == "N/A"

    def test_get_color(self):
        """Test color retrieval from theme"""
        color = self.renderer.get_color(ThemeColor.PRIMARY)
        assert color == "#3B82F6"  # Default primary color

        light_color = self.renderer.get_color(ThemeColor.PRIMARY, "light")
        assert light_color == "#93C5FD"

    def test_truncate_text(self):
        """Test text truncation"""
        text = "This is a very long text that should be truncated"

        assert self.renderer.truncate_text(text, 20) == "This is a very lo..."
        assert self.renderer.truncate_text(text, 50) == text  # No truncation needed
        assert self.renderer.truncate_text(None, 20) == ""

        # Custom suffix
        assert self.renderer.truncate_text(text, 20, ">>") == "This is a very lon>>"

    def test_sanitize_text(self):
        """Test text sanitization"""
        # Control characters should be removed
        text_with_controls = "Hello\x00\x01World\x1f"
        assert self.renderer.sanitize_text(text_with_controls) == "HelloWorld"

        # Newlines and tabs should be preserved
        text_with_whitespace = "Hello\nWorld\tTest"
        assert self.renderer.sanitize_text(text_with_whitespace) == "Hello\nWorld\tTest"

        assert self.renderer.sanitize_text(None) == ""

    def test_get_status_color(self):
        """Test status color mapping"""
        assert self.renderer.get_status_color("active") == ThemeColor.SUCCESS
        assert self.renderer.get_status_color("RUNNING") == ThemeColor.SUCCESS
        assert self.renderer.get_status_color("warning") == ThemeColor.WARNING
        assert self.renderer.get_status_color("ERROR") == ThemeColor.ERROR
        assert self.renderer.get_status_color("loading") == ThemeColor.INFO
        assert self.renderer.get_status_color("unknown") == ThemeColor.NEUTRAL

    def test_calculate_health_score(self):
        """Test health score calculation"""
        # Empty metrics
        assert self.renderer.calculate_health_score({}) == 0.0

        # Good metrics (low usage)
        good_metrics = {
            "cpu_usage": 20,
            "memory_usage": 30,
            "error_rate": 5,
        }
        score = self.renderer.calculate_health_score(good_metrics)
        assert score > 70  # Should be high

        # Bad metrics (high usage)
        bad_metrics = {
            "cpu_usage": 90,
            "memory_usage": 95,
            "error_rate": 25,
        }
        score = self.renderer.calculate_health_score(bad_metrics)
        assert score < 30  # Should be low

    def test_set_theme(self):
        """Test theme setting"""
        new_theme = {"colors": {"primary": "#FF0000"}}
        self.renderer.set_theme(new_theme)

        assert self.renderer.theme == new_theme
        assert len(self.renderer._cache) == 0  # Cache should be cleared

    def test_clear_cache(self):
        """Test cache clearing"""
        self.renderer._cache["test"] = "value"
        assert len(self.renderer._cache) == 1

        self.renderer.clear_cache()
        assert len(self.renderer._cache) == 0

    def test_abstract_methods(self):
        """Test that abstract methods are implemented"""
        # These should work without raising NotImplementedError
        result = self.renderer.render_widget(WidgetType.METRIC_CARD, {"value": 100})
        assert "metric_card" in result

        widgets = [{"type": WidgetType.STATUS_INDICATOR, "data": {"status": "ok"}}]
        result = self.renderer.render_layout(widgets)
        assert "status_indicator" in result

        result = self.renderer.render_container("content")
        assert "content" in result


class TestRendererRegistry:
    """Test cases for RendererRegistry"""

    def setup_method(self):
        """Setup test registry"""
        self.registry = RendererRegistry()

    def test_register_renderer(self):
        """Test renderer registration"""
        self.registry.register(RenderFormat.WEB, TestRenderer)

        assert self.registry.is_registered(RenderFormat.WEB)
        assert RenderFormat.WEB in self.registry.get_registered_formats()
        assert self.registry.get_default_format() == RenderFormat.WEB

    def test_register_invalid_renderer(self):
        """Test registration of invalid renderer"""

        class NotARenderer:
            pass

        with pytest.raises(ValueError):
            self.registry.register(RenderFormat.WEB, NotARenderer)

    def test_get_renderer_class(self):
        """Test getting renderer class"""
        self.registry.register(RenderFormat.TUI, TestRenderer)

        renderer_class = self.registry.get_renderer_class(RenderFormat.TUI)
        assert renderer_class == TestRenderer

        assert self.registry.get_renderer_class(RenderFormat.JSON) is None

    def test_get_renderer_instance(self):
        """Test getting renderer instance"""
        self.registry.register(RenderFormat.WEB, TestRenderer)

        renderer = self.registry.get_renderer(RenderFormat.WEB)
        assert isinstance(renderer, TestRenderer)
        assert renderer.format_type == RenderFormat.WEB

        # Should return cached instance
        renderer2 = self.registry.get_renderer(RenderFormat.WEB)
        assert renderer is renderer2

    def test_get_renderer_with_kwargs(self):
        """Test getting renderer with custom arguments"""
        self.registry.register(RenderFormat.WEB, TestRenderer)

        custom_theme = {"colors": {"primary": "#FF0000"}}
        renderer = self.registry.get_renderer(RenderFormat.WEB, theme=custom_theme)

        assert renderer.theme == custom_theme

        # Should not be cached when kwargs provided
        renderer2 = self.registry.get_renderer(RenderFormat.WEB)
        assert renderer is not renderer2

    def test_unregister_renderer(self):
        """Test renderer unregistration"""
        self.registry.register(RenderFormat.WEB, TestRenderer)
        self.registry.register(RenderFormat.TUI, TestRenderer)

        assert self.registry.is_registered(RenderFormat.WEB)

        self.registry.unregister(RenderFormat.WEB)

        assert not self.registry.is_registered(RenderFormat.WEB)
        assert self.registry.get_default_format() == RenderFormat.TUI

    def test_set_default_format(self):
        """Test setting default format"""
        self.registry.register(RenderFormat.WEB, TestRenderer)
        self.registry.register(RenderFormat.TUI, TestRenderer)

        self.registry.set_default_format(RenderFormat.TUI)
        assert self.registry.get_default_format() == RenderFormat.TUI

        with pytest.raises(ValueError):
            self.registry.set_default_format(RenderFormat.JSON)

    def test_get_default_renderer(self):
        """Test getting default renderer"""
        assert self.registry.get_default_renderer() is None

        self.registry.register(RenderFormat.WEB, TestRenderer)
        renderer = self.registry.get_default_renderer()

        assert isinstance(renderer, TestRenderer)
        assert renderer.format_type == RenderFormat.WEB

    def test_registry_methods(self):
        """Test registry utility methods"""
        assert len(self.registry) == 0
        assert RenderFormat.WEB not in self.registry

        self.registry.register(RenderFormat.WEB, TestRenderer)
        self.registry.register(RenderFormat.TUI, TestRenderer)

        assert len(self.registry) == 2
        assert RenderFormat.WEB in self.registry
        assert set(self.registry.get_registered_formats()) == {RenderFormat.WEB, RenderFormat.TUI}

    def test_clear_registry(self):
        """Test clearing registry"""
        self.registry.register(RenderFormat.WEB, TestRenderer)
        self.registry.register(RenderFormat.TUI, TestRenderer)

        assert len(self.registry) == 2

        self.registry.clear()

        assert len(self.registry) == 0
        assert self.registry.get_default_format() is None

    def test_registry_repr(self):
        """Test registry string representation"""
        self.registry.register(RenderFormat.WEB, TestRenderer)
        repr_str = repr(self.registry)

        assert "RendererRegistry" in repr_str
        assert "web" in repr_str
        assert "default=web" in repr_str


class TestEnums:
    """Test cases for enum definitions"""

    def test_render_format_enum(self):
        """Test RenderFormat enum"""
        assert RenderFormat.TUI.value == "tui"
        assert RenderFormat.WEB.value == "web"
        assert RenderFormat.TAURI.value == "tauri"
        assert RenderFormat.JSON.value == "json"
        assert RenderFormat.MARKDOWN.value == "markdown"

    def test_widget_type_enum(self):
        """Test WidgetType enum"""
        assert WidgetType.SESSION_BROWSER.value == "session_browser"
        assert WidgetType.HEALTH_METER.value == "health_meter"
        assert WidgetType.ACTIVITY_HEATMAP.value == "activity_heatmap"

        # Test that all expected widget types exist
        expected_widgets = [
            "SESSION_BROWSER",
            "HEALTH_METER",
            "ACTIVITY_HEATMAP",
            "PROJECT_HEALTH",
            "GIT_ACTIVITY",
            "PROGRESS_TRACKER",
            "SESSION_PROGRESS",
            "LOG_VIEWER",
            "METRIC_CARD",
            "STATUS_INDICATOR",
            "CHART",
            "TABLE",
            "GRID",
            "LIST",
            "TREE",
        ]

        for widget in expected_widgets:
            assert hasattr(WidgetType, widget)

    def test_theme_color_enum(self):
        """Test ThemeColor enum"""
        assert ThemeColor.PRIMARY.value == "primary"
        assert ThemeColor.SUCCESS.value == "success"
        assert ThemeColor.ERROR.value == "error"

        # Test that all expected colors exist
        expected_colors = [
            "PRIMARY",
            "SECONDARY",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "INFO",
            "NEUTRAL",
            "ACCENT",
        ]

        for color in expected_colors:
            assert hasattr(ThemeColor, color)
