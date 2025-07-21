"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

from libs.dashboard.renderers import RendererFactory, RenderFormat, WidgetType
from libs.dashboard.renderers.widget_models import HealthData, HealthLevel


class TestFactoryIntegration:
    """Tests for renderer factory with all formats."""

    @staticmethod
    def test_factory_integration() -> None:
        """Test 11: Renderer factory with all formats."""
        factory = RendererFactory()

        # Test factory creates all renderer types
        tui_renderer = factory.create_renderer(RenderFormat.TUI)
        web_renderer = factory.create_renderer(RenderFormat.WEB)
        tauri_renderer = factory.create_renderer(RenderFormat.TAURI)

        assert tui_renderer is not None
        assert web_renderer is not None
        assert tauri_renderer is not None

        # Test batch rendering
        data = HealthData(overall_score=90, overall_level=HealthLevel.EXCELLENT)

        results = factory.render_all_formats(WidgetType.PROJECT_HEALTH, data)
        assert len(results) == 3
        assert RenderFormat.TUI in results
        assert RenderFormat.WEB in results
        assert RenderFormat.TAURI in results
