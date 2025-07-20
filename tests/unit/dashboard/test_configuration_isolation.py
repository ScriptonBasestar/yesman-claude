import tempfile
from pathlib import Path

from libs.dashboard import ThemeManager
from libs.dashboard.theme_system import ColorPalette, Theme, ThemeMode


class TestConfigurationIsolation:
    """Tests for configuration isolation between instances."""

    def test_configuration_isolation(self) -> None:
        """Test configuration isolation between instances."""
        with (
            tempfile.TemporaryDirectory() as temp_dir1,
            tempfile.TemporaryDirectory() as temp_dir2,
        ):
            theme_manager1 = ThemeManager(config_dir=Path(temp_dir1))
            theme_manager2 = ThemeManager(config_dir=Path(temp_dir2))

            # Create custom theme in first manager
            custom_theme = Theme(
                name="Custom Test",
                mode=ThemeMode.CUSTOM,
                colors=ColorPalette(primary="#ff0000"),
            )

            theme_manager1.save_theme("custom", custom_theme)

            # Verify isolation
            theme1_themes = theme_manager1.get_all_themes()
            theme2_themes = theme_manager2.get_all_themes()

            assert "custom" in theme1_themes
            assert "custom" not in theme2_themes
