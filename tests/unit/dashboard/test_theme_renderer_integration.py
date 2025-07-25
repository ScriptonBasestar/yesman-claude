# Copyright notice.

import tempfile
from pathlib import Path

import pytest

from libs.dashboard import ThemeManager, ThemeMode
from libs.dashboard.renderers import RendererFactory, RenderFormat, WidgetType
from libs.dashboard.renderers.widget_models import HealthData, HealthLevel

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


class TestThemeRendererIntegration:
    """Tests for theme and renderer integration."""

    @pytest.fixture
    @staticmethod
    def theme_manager() -> object:
        """Create ThemeManager instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ThemeManager(config_dir=Path(temp_dir))

    @staticmethod
    def test_theme_renderer_integration(theme_manager: object) -> None:
        """Test 8: Theme and renderer integration."""
        factory = RendererFactory()

        # Test theme switching affects renderers
        theme_manager.set_mode(ThemeMode.DARK)
        dark_theme = theme_manager.current_theme

        # Create renderer with dark theme
        renderer = factory.create_renderer(
            RenderFormat.TUI, theme=dark_theme.colors.to_dict()
        )

        # Test rendering with theme
        health_data = HealthData(
            overall_score=75,
            overall_level=HealthLevel.GOOD,
            categories={"security": 80},
        )

        result = renderer.render_widget(WidgetType.PROJECT_HEALTH, health_data)
        assert result is not None

        # Switch to light theme
        theme_manager.set_mode(ThemeMode.LIGHT)
        light_theme = theme_manager.current_theme

        # Verify theme changed
        assert light_theme.name != dark_theme.name
