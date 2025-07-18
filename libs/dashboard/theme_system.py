"""Theme System.

Unified theme management system for all dashboard interfaces
providing consistent colors, typography, spacing, and visual design.
"""

import json
import logging
import os
import platform
import subprocess
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    """Theme mode enumeration."""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system preference
    HIGH_CONTRAST = "high_contrast"
    CUSTOM = "custom"


@dataclass
class ColorPalette:
    """Color palette definition for themes."""

    # Primary colors
    primary: str = "#3b82f6"  # Blue
    primary_dark: str = "#1d4ed8"  # Darker blue
    primary_light: str = "#93c5fd"  # Lighter blue

    # Secondary colors
    secondary: str = "#64748b"  # Slate
    secondary_dark: str = "#334155"  # Dark slate
    secondary_light: str = "#cbd5e1"  # Light slate

    # Status colors
    success: str = "#10b981"  # Green
    warning: str = "#f59e0b"  # Yellow
    error: str = "#ef4444"  # Red
    info: str = "#06b6d4"  # Cyan

    # Neutral colors
    background: str = "#ffffff"  # White
    surface: str = "#f8fafc"  # Very light gray
    panel: str = "#f1f5f9"  # Light gray
    border: str = "#e2e8f0"  # Light border

    # Text colors
    text: str = "#0f172a"  # Almost black
    text_muted: str = "#64748b"  # Muted text
    text_inverse: str = "#ffffff"  # White text

    # Accent colors
    accent: str = "#8b5cf6"  # Purple
    highlight: str = "#fbbf24"  # Amber

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "ColorPalette":
        """Create from dictionary."""
        return cls(**data)

    def adjust_opacity(self, color: str, opacity: float) -> str:
        """Add opacity to a color (simplified - would need color parsing in production)."""
        if color.startswith("#") and len(color) == 7:
            # Convert hex to RGB and add alpha
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return f"rgba({r}, {g}, {b}, {opacity})"
        return color


@dataclass
class Typography:
    """Typography settings for themes."""

    # Font families
    font_family_primary: str = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    font_family_mono: str = "'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace"

    # Font sizes (in rem)
    font_size_xs: str = "0.75rem"  # 12px
    font_size_sm: str = "0.875rem"  # 14px
    font_size_base: str = "1rem"  # 16px
    font_size_lg: str = "1.125rem"  # 18px
    font_size_xl: str = "1.25rem"  # 20px
    font_size_2xl: str = "1.5rem"  # 24px
    font_size_3xl: str = "1.875rem"  # 30px
    font_size_4xl: str = "2.25rem"  # 36px

    # Font weights
    font_weight_light: str = "300"
    font_weight_normal: str = "400"
    font_weight_medium: str = "500"
    font_weight_semibold: str = "600"
    font_weight_bold: str = "700"

    # Line heights
    line_height_tight: str = "1.25"
    line_height_normal: str = "1.5"
    line_height_relaxed: str = "1.75"

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Typography":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Spacing:
    """Spacing settings for themes."""

    # Base spacing unit (in rem)
    base_unit: str = "0.25rem"  # 4px

    # Spacing scale
    space_0: str = "0"
    space_1: str = "0.25rem"  # 4px
    space_2: str = "0.5rem"  # 8px
    space_3: str = "0.75rem"  # 12px
    space_4: str = "1rem"  # 16px
    space_5: str = "1.25rem"  # 20px
    space_6: str = "1.5rem"  # 24px
    space_8: str = "2rem"  # 32px
    space_10: str = "2.5rem"  # 40px
    space_12: str = "3rem"  # 48px
    space_16: str = "4rem"  # 64px
    space_20: str = "5rem"  # 80px
    space_24: str = "6rem"  # 96px
    space_32: str = "8rem"  # 128px

    # Border radius
    radius_none: str = "0"
    radius_sm: str = "0.125rem"  # 2px
    radius_base: str = "0.25rem"  # 4px
    radius_md: str = "0.375rem"  # 6px
    radius_lg: str = "0.5rem"  # 8px
    radius_xl: str = "0.75rem"  # 12px
    radius_2xl: str = "1rem"  # 16px
    radius_full: str = "9999px"

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Spacing":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Theme:
    """Complete theme definition."""

    name: str
    mode: ThemeMode
    colors: ColorPalette = field(default_factory=ColorPalette)
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    custom_css: str = ""
    description: str = ""
    author: str = ""
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "mode": self.mode.value,
            "colors": self.colors.to_dict(),
            "typography": self.typography.to_dict(),
            "spacing": self.spacing.to_dict(),
            "custom_css": self.custom_css,
            "description": self.description,
            "author": self.author,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Theme":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            mode=ThemeMode(data["mode"]),
            colors=ColorPalette.from_dict(data.get("colors", {})),
            typography=Typography.from_dict(data.get("typography", {})),
            spacing=Spacing.from_dict(data.get("spacing", {})),
            custom_css=data.get("custom_css", ""),
            description=data.get("description", ""),
            author=data.get("author", ""),
            version=data.get("version", "1.0.0"),
        )


class SystemThemeDetector:
    """Detects system theme preferences across platforms."""

    @staticmethod
    def get_system_theme() -> ThemeMode:
        """Get system theme preference."""
        try:
            system = platform.system()

            if system == "Darwin":  # macOS
                return SystemThemeDetector._get_macos_theme()
            elif system == "Windows":
                return SystemThemeDetector._get_windows_theme()
            elif system == "Linux":
                return SystemThemeDetector._get_linux_theme()
            else:
                logger.warning(f"Unknown system: {system}")
                return ThemeMode.LIGHT

        except Exception as e:
            logger.error(f"Error detecting system theme: {e}")
            return ThemeMode.LIGHT

    @staticmethod
    def _get_macos_theme() -> ThemeMode:
        """Get macOS theme preference."""
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and "Dark" in result.stdout:
                return ThemeMode.DARK
            else:
                return ThemeMode.LIGHT

        except subprocess.TimeoutExpired:
            logger.warning("macOS theme detection timed out")
            return ThemeMode.LIGHT
        except Exception as e:
            logger.warning(f"macOS theme detection failed: {e}")
            return ThemeMode.LIGHT

    @staticmethod
    def _get_windows_theme() -> ThemeMode:
        """Get Windows theme preference."""
        try:
            import winreg

            # Check Windows registry for theme preference
            key = winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_CURRENT_USER,  # type: ignore[attr-defined]
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )

            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")  # type: ignore[attr-defined]
            winreg.CloseKey(key)  # type: ignore[attr-defined]

            return ThemeMode.LIGHT if value else ThemeMode.DARK

        except ImportError:
            logger.warning("winreg not available")
            return ThemeMode.LIGHT
        except Exception as e:
            logger.warning(f"Windows theme detection failed: {e}")
            return ThemeMode.LIGHT

    @staticmethod
    def _get_linux_theme() -> ThemeMode:
        """Get Linux theme preference."""
        try:
            # Check various Linux desktop environment settings

            # GNOME
            if os.environ.get("XDG_CURRENT_DESKTOP") == "GNOME":
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0 and "dark" in result.stdout.lower():
                    return ThemeMode.DARK

            # KDE
            elif os.environ.get("XDG_CURRENT_DESKTOP") == "KDE":
                # Check KDE color scheme
                kde_config = Path.home() / ".config" / "kdeglobals"
                if kde_config.exists():
                    with open(kde_config) as f:
                        content = f.read()
                        if "ColorScheme=Breeze Dark" in content:
                            return ThemeMode.DARK

            # Check environment variables
            if os.environ.get("GTK_THEME", "").lower().find("dark") != -1:
                return ThemeMode.DARK

            return ThemeMode.LIGHT

        except Exception as e:
            logger.warning(f"Linux theme detection failed: {e}")
            return ThemeMode.LIGHT


class ThemeManager:
    """Manages all themes for the dashboard."""

    _instance: Optional["ThemeManager"] = None

    @classmethod
    def get_instance(cls, config_dir: Path | None = None) -> "ThemeManager":
        """Get the singleton instance of the theme manager."""
        if cls._instance is None:
            cls._instance = cls(config_dir=config_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance."""
        cls._instance = None

    def __init__(self, config_dir: Path | None = None):
        """Initialize the theme manager.

        Args:
            config_dir: Directory for storing user themes
        """
        if ThemeManager._instance is not None:
            raise RuntimeError("ThemeManager is a singleton, use get_instance()")

        # Paths
        self.config_dir = config_dir or Path.home() / ".config" / "yesman" / "themes"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Built-in themes
        self.built_in_themes = self._create_builtin_themes()

        # Current theme
        self.current_theme = self.built_in_themes["default_light"]
        self.current_mode = ThemeMode.LIGHT

        # User themes
        self.user_themes: dict[str, Theme] = {}
        self.load_user_themes()

        # Auto-detect system theme
        self.auto_theme_enabled = True
        self.update_from_system()

    def _create_builtin_themes(self) -> dict[str, Theme]:
        """Create built-in themes."""
        themes = {}

        # Default Light Theme
        light_colors = ColorPalette()
        themes["default_light"] = Theme(
            name="Default Light",
            mode=ThemeMode.LIGHT,
            colors=light_colors,
            description="Clean and modern light theme",
            author="Yesman-Claude",
        )

        # Default Dark Theme
        dark_colors = ColorPalette(
            primary="#60a5fa",  # Lighter blue for dark mode
            primary_dark="#2563eb",
            primary_light="#3b82f6",
            secondary="#94a3b8",  # Lighter slate
            secondary_dark="#64748b",
            secondary_light="#cbd5e1",
            background="#0f172a",  # Dark background
            surface="#1e293b",  # Dark surface
            panel="#334155",  # Dark panel
            border="#475569",  # Dark border
            text="#f8fafc",  # Light text
            text_muted="#94a3b8",  # Muted light text
            text_inverse="#0f172a",  # Dark text
        )

        themes["default_dark"] = Theme(
            name="Default Dark",
            mode=ThemeMode.DARK,
            colors=dark_colors,
            description="Elegant dark theme for reduced eye strain",
            author="Yesman-Claude",
        )

        # High Contrast Theme
        high_contrast_colors = ColorPalette(
            primary="#000000",
            primary_dark="#000000",
            primary_light="#333333",
            secondary="#666666",
            secondary_dark="#333333",
            secondary_light="#999999",
            success="#00ff00",
            warning="#ffff00",
            error="#ff0000",
            info="#00ffff",
            background="#ffffff",
            surface="#ffffff",
            panel="#f0f0f0",
            border="#000000",
            text="#000000",
            text_muted="#333333",
            text_inverse="#ffffff",
            accent="#ff00ff",
            highlight="#ffff00",
        )

        themes["high_contrast"] = Theme(
            name="High Contrast",
            mode=ThemeMode.HIGH_CONTRAST,
            colors=high_contrast_colors,
            description="High contrast theme for accessibility",
            author="Yesman-Claude",
        )

        return themes

    def get_all_themes(self) -> dict[str, Theme]:
        """Get all available themes (built-in + user)."""
        all_themes = self.built_in_themes.copy()
        all_themes.update(self.user_themes)
        return all_themes

    def get_theme(self, name: str) -> Theme | None:
        """Get theme by name."""
        all_themes = self.get_all_themes()
        return all_themes.get(name)

    def set_theme(self, theme: str | Theme) -> bool:
        """Set current theme.

        Args:
            theme: Theme name or Theme object

        Returns:
            True if theme was set successfully
        """
        if isinstance(theme, str):
            theme_obj = self.get_theme(theme)
            if theme_obj is None:
                logger.error(f"Theme not found: {theme}")
                return False
            theme = theme_obj

        self.current_theme = theme
        self.current_mode = theme.mode

        logger.info(f"Theme changed to: {theme.name}")
        return True

    def set_mode(self, mode: ThemeMode) -> bool:
        """Set theme mode (auto-selects appropriate theme).

        Args:
            mode: Theme mode to set

        Returns:
            True if mode was set successfully
        """
        self.current_mode = mode

        if mode == ThemeMode.AUTO:
            self.auto_theme_enabled = True
            return self.update_from_system()
        else:
            self.auto_theme_enabled = False

            # Select appropriate built-in theme
            if mode == ThemeMode.LIGHT:
                return self.set_theme("default_light")
            elif mode == ThemeMode.DARK:
                return self.set_theme("default_dark")
            elif mode == ThemeMode.HIGH_CONTRAST:
                return self.set_theme("high_contrast")

        return False

    def update_from_system(self) -> bool:
        """Update theme from system preference."""
        if not self.auto_theme_enabled:
            return False

        system_mode = SystemThemeDetector.get_system_theme()

        if system_mode == ThemeMode.DARK:
            return self.set_theme("default_dark")
        else:
            return self.set_theme("default_light")

    def save_theme(self, name: str, theme: Theme) -> bool:
        """Save user theme to disk.

        Args:
            name: Theme name (used as filename)
            theme: Theme to save

        Returns:
            True if theme was saved successfully
        """
        try:
            theme_file = self.config_dir / f"{name}.json"

            with open(theme_file, "w", encoding="utf-8") as f:
                json.dump(theme.to_dict(), f, indent=2, ensure_ascii=False)

            self.user_themes[name] = theme
            logger.info(f"Theme saved: {name}")
            return True

        except Exception as e:
            logger.error(f"Error saving theme {name}: {e}")
            return False

    def load_theme(self, name: str) -> Theme | None:
        """Load user theme from disk.

        Args:
            name: Theme name to load

        Returns:
            Loaded theme or None if failed
        """
        try:
            theme_file = self.config_dir / f"{name}.json"

            if not theme_file.exists():
                return None

            with open(theme_file, encoding="utf-8") as f:
                data = json.load(f)

            theme = Theme.from_dict(data)
            self.user_themes[name] = theme
            logger.info(f"Theme loaded: {name}")
            return theme

        except Exception as e:
            logger.error(f"Error loading theme {name}: {e}")
            return None

    def load_user_themes(self) -> None:
        """Load all user themes from config directory."""
        try:
            for theme_file in self.config_dir.glob("*.json"):
                theme_name = theme_file.stem
                self.load_theme(theme_name)

        except Exception as e:
            logger.error(f"Error loading user themes: {e}")

    def delete_theme(self, name: str) -> bool:
        """Delete user theme.

        Args:
            name: Theme name to delete

        Returns:
            True if theme was deleted successfully
        """
        try:
            # Don't allow deleting built-in themes
            if name in self.built_in_themes:
                logger.error(f"Cannot delete built-in theme: {name}")
                return False

            theme_file = self.config_dir / f"{name}.json"

            if theme_file.exists():
                theme_file.unlink()

            if name in self.user_themes:
                del self.user_themes[name]

            logger.info(f"Theme deleted: {name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting theme {name}: {e}")
            return False

    def export_css(self, theme: Theme | None = None) -> str:
        """Export theme as CSS variables.

        Args:
            theme: Theme to export (uses current if None)

        Returns:
            CSS string with theme variables
        """
        if theme is None:
            theme = self.current_theme

        css_lines = [
            ":root {",
            f"  /* Theme: {theme.name} */",
        ]

        # Color variables
        css_lines.append("  /* Colors */")
        for key, value in theme.colors.to_dict().items():
            css_var = key.replace("_", "-")
            css_lines.append(f"  --color-{css_var}: {value};")

        # Typography variables
        css_lines.append("\n  /* Typography */")
        for key, value in theme.typography.to_dict().items():
            css_var = key.replace("_", "-")
            css_lines.append(f"  --{css_var}: {value};")

        # Spacing variables
        css_lines.append("\n  /* Spacing */")
        for key, value in theme.spacing.to_dict().items():
            css_var = key.replace("_", "-")
            css_lines.append(f"  --{css_var}: {value};")

        css_lines.append("}")

        # Add custom CSS
        if theme.custom_css:
            css_lines.append("\n/* Custom CSS */")
            css_lines.append(theme.custom_css)

        return "\n".join(css_lines)

    def export_rich_theme(self, theme: Theme | None = None) -> dict[str, str]:
        """Export theme for Rich library.

        Args:
            theme: Theme to export (uses current if None)

        Returns:
            Dictionary of Rich style mappings
        """
        if theme is None:
            theme = self.current_theme

        colors = theme.colors

        return {
            "primary": colors.primary,
            "secondary": colors.secondary,
            "success": colors.success,
            "warning": colors.warning,
            "error": colors.error,
            "info": colors.info,
            "background": colors.background,
            "surface": colors.surface,
            "panel": colors.panel,
            "text": colors.text,
            "text-muted": colors.text_muted,
            "accent": colors.accent,
            "highlight": colors.highlight,
            # Rich-specific styles
            "prompt": colors.primary,
            "prompt.choices": colors.secondary,
            "prompt.default": colors.text_muted,
            "progress.bar": colors.primary,
            "progress.complete": colors.success,
            "status.spinner": colors.primary,
            "log.level.debug": colors.text_muted,
            "log.level.info": colors.info,
            "log.level.warning": colors.warning,
            "log.level.error": colors.error,
            "table.header": colors.primary,
            "table.row": colors.text,
            "tree.guide": colors.secondary,
        }

    def export_textual_css(self, theme: Theme | None = None) -> str:
        """Export theme as CSS for Textual TUI framework."""
        theme = theme or self.current_theme
        if not theme:
            return ""

        # Generate CSS variables
        css_vars = [
            f"  --primary: {theme.colors.primary};",
            f"  --secondary: {theme.colors.secondary};",
            f"  --background: {theme.colors.background};",
            f"  --surface: {theme.colors.surface};",
            f"  --panel: {theme.colors.panel};",
            f"  --text: {theme.colors.text};",
            f"  --text-muted: {theme.colors.text_muted};",
            f"  --success: {theme.colors.success};",
            f"  --warning: {theme.colors.warning};",
            f"  --error: {theme.colors.error};",
            f"  --info: {theme.colors.info};",
        ]

        return f""":root {{\n{os.linesep.join(css_vars)}\n}}"""


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    return ThemeManager.get_instance()


def reset_theme_manager() -> None:
    """Reset the global theme manager."""
    ThemeManager.reset_instance()
