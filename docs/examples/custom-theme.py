from typing import Any
from libs.dashboard import get_theme_manager
from libs.dashboard.theme_system import ColorPalette, Spacing, Theme, ThemeMode, Typography
import json
from pathlib import Path


# !/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Custom Theme Example.

This example demonstrates how to create and use custom themes
in Yesman-Claude dashboard system.
"""


def create_cyberpunk_theme() -> object:
    """Create a cyberpunk-inspired theme with neon colors."""
    return Theme(
        name="Cyberpunk Neon",
        mode=ThemeMode.CUSTOM,
        colors=ColorPalette(
            # Primary neon colors
            primary="#00ff41",  # Matrix green
            secondary="#ff0080",  # Hot pink
            background="#0a0a0a",  # Nearly black
            surface="#1a1a2e",  # Dark blue-gray
            # Text colors
            text="#00ff41",  # Bright green
            text_secondary="#80ff80",  # Dimmer green
            # Status colors
            success="#00ff41",  # Green
            warning="#ffff00",  # Yellow
            error="#ff0040",  # Red
            info="#0080ff",  # Blue
            # Accent colors
            accent="#ff0080",  # Hot pink
            muted="#404040",  # Dark gray
        ),
        typography=Typography(
            primary_font="JetBrains Mono",
            secondary_font="Orbitron",  # Futuristic font
            size_small="11px",
            size_normal="13px",
            size_large="15px",
            size_extra_large="17px",
            weight_normal="400",
            weight_bold="600",
        ),
        spacing=Spacing(
            small="2px",
            medium="6px",
            large="12px",
            extra_large="20px",
        ),
    )


def create_ocean_theme() -> object:
    """Create a calming ocean-inspired theme."""
    return Theme(
        name="Ocean Depths",
        mode=ThemeMode.CUSTOM,
        colors=ColorPalette(
            # Ocean colors
            primary="#2980b9",  # Ocean blue
            secondary="#16a085",  # Teal
            background="#1e3a8a",  # Deep blue
            surface="#1e40af",  # Blue
            # Text colors
            text="#e0f2fe",  # Light blue
            text_secondary="#b3e5fc",  # Lighter blue
            # Status colors
            success="#2dd4bf",  # Teal
            warning="#fbbf24",  # Amber
            error="#ef4444",  # Red
            info="#3b82f6",  # Blue
            # Accent colors
            accent="#0891b2",  # Cyan
            muted="#475569",  # Slate
        ),
        typography=Typography(
            primary_font="Inter",
            secondary_font="Roboto",
            size_small="12px",
            size_normal="14px",
            size_large="16px",
            size_extra_large="18px",
            weight_normal="400",
            weight_bold="500",
        ),
        spacing=Spacing(
            small="4px",
            medium="8px",
            large="16px",
            extra_large="24px",
        ),
    )


def create_minimal_theme() -> object:
    """Create a minimal, clean theme."""
    return Theme(
        name="Minimal Clean",
        mode=ThemeMode.LIGHT,
        colors=ColorPalette(
            # Minimal colors
            primary="#000000",  # Pure black
            secondary="#6b7280",  # Gray
            background="#ffffff",  # Pure white
            surface="#f9fafb",  # Light gray
            # Text colors
            text="#111827",  # Dark gray
            text_secondary="#6b7280",  # Medium gray
            # Status colors
            success="#059669",  # Green
            warning="#d97706",  # Orange
            error="#dc2626",  # Red
            info="#2563eb",  # Blue
            # Accent colors
            accent="#4f46e5",  # Indigo
            muted="#e5e7eb",  # Light gray
        ),
        typography=Typography(
            primary_font="SF Pro Text",
            secondary_font="SF Pro Display",
            size_small="12px",
            size_normal="14px",
            size_large="16px",
            size_extra_large="18px",
            weight_normal="400",
            weight_bold="600",
        ),
        spacing=Spacing(
            small="4px",
            medium="8px",
            large="16px",
            extra_large="24px",
        ),
    )


def demo_theme_operations() -> None:
    """Demonstrate theme operations."""
    print("🎨 Custom Theme Demo")
    print("=" * 50)

    # Get theme manager
    theme_manager = get_theme_manager()

    # Create custom themes
    cyberpunk = create_cyberpunk_theme()
    ocean = create_ocean_theme()
    minimal = create_minimal_theme()

    # Save themes
    theme_manager.save_theme("cyberpunk", cyberpunk)
    theme_manager.save_theme("ocean", ocean)
    theme_manager.save_theme("minimal", minimal)

    print("✅ Created and saved 3 custom themes")

    # List all themes
    all_themes = theme_manager.get_all_themes()
    print(f"\n📋 Available themes ({len(all_themes)}):")
    for theme_id, theme in all_themes.items():
        print(f"  - {theme_id}: {theme.name} ({theme.mode.value})")

    # Switch to cyberpunk theme
    print("\n🔄 Switching to cyberpunk theme...")
    theme_manager.set_theme("cyberpunk")
    current = theme_manager.current_theme
    print(f"✅ Current theme: {current.name}")

    # Export theme as CSS
    print("\n📤 Exporting CSS...")
    css = theme_manager.export_css(cyberpunk)
    print(f"CSS Variables generated: {css.count('--')} variables")

    # Export for Rich library
    print("\n📤 Exporting Rich theme...")
    rich_theme = theme_manager.export_rich_theme(cyberpunk)
    print(f"Rich styles generated: {len(rich_theme)} styles")

    # Export for Textual framework
    print("\n📤 Exporting Textual CSS...")
    textual_css = theme_manager.export_textual_css(cyberpunk)
    print(f"Textual CSS generated: {len(textual_css)} characters")

    # Switch between themes
    themes_to_test = ["ocean", "minimal", "default_dark", "cyberpunk"]
    print("\n🔄 Testing theme switching...")

    for theme_id in themes_to_test:
        try:
            theme_manager.set_theme(theme_id)
            current = theme_manager.current_theme
            print(f"  ✅ {theme_id}: {current.name}")
        except Exception as e:
            print(f"  ❌ {theme_id}: {e}")

    print("\n🎉 Theme demo completed!")


def save_theme_examples() -> None:
    """Save theme examples to files for reference."""

    # Create themes
    themes = {
        "cyberpunk": create_cyberpunk_theme(),
        "ocean": create_ocean_theme(),
        "minimal": create_minimal_theme(),
    }

    # Create output directory
    output_dir = Path("docs/examples/themes")
    output_dir.mkdir(exist_ok=True)

    # Save each theme
    for theme_id, theme in themes.items():
        # Save as JSON
        theme_data = {
            "name": theme.name,
            "mode": theme.mode.value,
            "colors": theme.colors.to_dict(),
            "typography": theme.typography.to_dict(),
            "spacing": theme.spacing.to_dict(),
        }

        with open(output_dir / f"{theme_id}.json", "w", encoding="utf-8") as f:
            json.dump(theme_data, f, indent=2)

        # Save as CSS
        theme_manager = get_theme_manager()
        css = theme_manager.export_css(theme)

        with open(output_dir / f"{theme_id}.css", "w", encoding="utf-8") as f:
            f.write(css)

        print(f"💾 Saved {theme_id} theme (JSON + CSS)")


if __name__ == "__main__":
    # Run the demo
    demo_theme_operations()

    # Save examples
    print("\n💾 Saving theme examples...")
    save_theme_examples()

    print("\n✨ Custom theme example completed!")
    print("Check docs/examples/themes/ for saved theme files.")
