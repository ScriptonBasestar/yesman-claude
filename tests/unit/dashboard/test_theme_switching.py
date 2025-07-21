"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

import pytest

from libs.dashboard import ThemeManager, ThemeMode


class TestThemeSwitching:
    """Tests for theme switching and CSS generation."""

    @pytest.fixture
    @staticmethod
    def theme_manager() -> ThemeManager:
        """Create ThemeManager instance."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            yield ThemeManager(config_dir=Path(temp_dir))

    @staticmethod
    def test_theme_switching(theme_manager: ThemeManager) -> None:
        """Test 3: Theme switching and CSS generation."""
        # Test built-in themes
        themes = theme_manager.get_all_themes()
        assert len(themes) >= 3

        # Test theme switching
        assert theme_manager.set_theme("default_dark") is True
        assert theme_manager.current_theme.name == "Default Dark"

        assert theme_manager.set_mode(ThemeMode.LIGHT) is True
        assert theme_manager.current_theme.name == "Default Light"

        # Test CSS export
        css = theme_manager.export_css()
        assert ":root {" in css
        assert "--color-primary:" in css
        assert "--font-family-primary:" in css

        # Test Rich theme export
        rich_theme = theme_manager.export_rich_theme()
        assert isinstance(rich_theme, dict)
        assert "primary" in rich_theme
        assert "background" in rich_theme

        # Test Textual CSS export
        textual_css = theme_manager.export_textual_css()
        assert "App {" in textual_css
        assert "background:" in textual_css
