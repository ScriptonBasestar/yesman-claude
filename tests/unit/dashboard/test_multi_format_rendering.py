from libs.dashboard.renderers import RendererFactory, RenderFormat, WidgetType
from libs.dashboard.renderers.widget_models import HealthData, SessionData, SessionStatus


class TestMultiFormatRendering:
    """Tests for multi-format rendering across all interfaces"""

    def test_multi_format_rendering(self):
        """Test 2: Multi-format rendering across all interfaces"""
        factory = RendererFactory()

        # Test data
        session_data = SessionData(
            name="test-session",
            status=SessionStatus.ACTIVE,
            uptime=3600,
            windows=2,
        )

        health_data = HealthData(
            overall_score=85,
            overall_level=HealthData.HealthLevel.GOOD,
            categories={"build": 90, "tests": 80},
        )

        # Test all formats
        formats = [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]
        widgets = [WidgetType.SESSION_BROWSER, WidgetType.PROJECT_HEALTH]

        for format_type in formats:
            renderer = factory.create_renderer(format_type)
            assert renderer is not None

            for widget_type in widgets:
                if widget_type == WidgetType.SESSION_BROWSER:
                    result = renderer.render_widget(widget_type, [session_data])
                else:
                    result = renderer.render_widget(widget_type, health_data)

                assert result is not None
                assert isinstance(result, dict)
                assert "content" in result or "data" in result
