import pytest
from typing import Any

from libs.dashboard import KeyboardNavigationManager, ThemeManager, ThemeMode
from libs.dashboard.keyboard_navigation import KeyModifier


class TestKeyboardThemeIntegration:
    """Tests for keyboard navigation with theme switching."""

    @pytest.fixture
    def keyboard_manager(self):
        """Create KeyboardNavigationManager instance."""
        manager = KeyboardNavigationManager()
        yield manager
        # Cleanup
        manager.actions.clear()
        manager.bindings.clear()

    @pytest.fixture
    def theme_manager(self):
        """Create ThemeManager instance."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            yield ThemeManager(config_dir=Path(temp_dir))

    def test_keyboard_theme_integration(self, keyboard_manager: Any, theme_manager: Any) -> None:
        """Test 10: Keyboard navigation with theme switching."""

        # Register theme switching action
        def switch_to_dark() -> None:
            theme_manager.set_mode(ThemeMode.DARK)

        keyboard_manager.register_action("switch_theme_dark", switch_to_dark)

        keyboard_manager.register_binding(
            "d",
            [KeyModifier.CTRL],
            "switch_theme_dark",
            "Switch to dark theme",
        )

        # Test theme switching via keyboard
        initial_theme = theme_manager.current_theme.name
        keyboard_manager.handle_key_event("d", [KeyModifier.CTRL])

        # Verify theme changed
        assert theme_manager.current_theme.name != initial_theme
        assert theme_manager.current_theme.mode == ThemeMode.DARK
