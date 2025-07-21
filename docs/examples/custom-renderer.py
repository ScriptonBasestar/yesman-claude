#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Custom Renderer Example.

This example demonstrates how to create custom renderers
for the Yesman-Claude dashboard system.
"""

import json
from datetime import UTC, datetime
from typing import object

from libs.dashboard.renderers import BaseRenderer, RendererFactory, RenderFormat, WidgetType
from libs.dashboard.renderers.widget_models import ActivityData, HealthData, HealthLevel, SessionData, SessionStatus


class ASCIIRenderer(BaseRenderer):
    """Custom renderer that outputs ASCII art representations."""

    def __init__(self, theme: dict[str, object] | None = None):
        """Initialize ASCII renderer.

        Args:
            theme: Optional theme configuration

        """
        super().__init__()
        self.format = RenderFormat.CUSTOM
        self.theme = theme or {}
        self.width = 80  # ASCII art width

    def render_widget(self, widget_type: WidgetType, data: object) -> dict[str, object]:
        """Render widget as ASCII art."""
        if widget_type == WidgetType.SESSION_BROWSER:
            return self._render_session_browser(data)
        elif widget_type == WidgetType.PROJECT_HEALTH:
            return self._render_health_chart(data)
        elif widget_type == WidgetType.ACTIVITY_MONITOR:
            return self._render_activity_graph(data)
        else:
            return {"content": f"Unsupported widget: {widget_type}", "data": data}

    def _render_session_browser(self, sessions: list[SessionData]) -> dict[str, object]:
        """Render sessions as ASCII table."""
        lines = []
        lines.append("=" * self.width)
        lines.append("SESSION BROWSER".center(self.width))
        lines.append("=" * self.width)

        if not sessions:
            lines.append("No sessions found".center(self.width))
            lines.append("=" * self.width)
            return {"content": "\n".join(lines), "format": "ascii"}

        # Header
        header = f"{'NAME':<20} {'STATUS':<10} {'UPTIME':<10} {'WINDOWS':<8} {'CPU%':<6} {'MEM':<8}"
        lines.append(header)
        lines.append("-" * len(header))

        # Sessions
        for session in sessions:
            uptime_str = self._format_uptime(session.uptime)
            cpu_str = f"{session.cpu_usage:.1f}%" if session.cpu_usage else "N/A"
            mem_str = f"{session.memory_usage:.0f}MB" if session.memory_usage else "N/A"

            row = f"{session.name[:19]:<20} {session.status.value.upper():<10} {uptime_str:<10} {session.windows or 0:<8} {cpu_str:<6} {mem_str:<8}"
            lines.append(row)

        lines.append("=" * self.width)

        return {
            "content": "\n".join(lines),
            "format": "ascii",
            "session_count": len(sessions),
        }

    def _render_health_chart(self, health: HealthData) -> dict[str, object]:
        """Render health as ASCII bar chart."""
        lines = []
        lines.append("=" * self.width)
        lines.append("PROJECT HEALTH".center(self.width))
        lines.append("=" * self.width)

        # Overall score
        overall_bar = self._create_progress_bar(health.overall_score, 40)
        lines.append(f"Overall: {health.overall_score:3d}% {overall_bar}")
        lines.append("")

        # Category breakdown
        if health.categories:
            lines.append("Category Breakdown:")
            lines.append("-" * 20)

            for category, score in health.categories.items():
                bar = self._create_progress_bar(score, 30)
                lines.append(f"{category.title():<12}: {score:3d}% {bar}")

        # Health level indicator
        level_indicator = self._get_health_indicator(health.overall_level)
        lines.append("")
        lines.append(f"Status: {level_indicator}")

        lines.append("=" * self.width)

        return {
            "content": "\n".join(lines),
            "format": "ascii",
            "health_score": health.overall_score,
        }

    def _render_activity_graph(self, activities: list[ActivityData]) -> dict[str, object]:
        """Render activity as ASCII graph."""
        lines = []
        lines.append("=" * self.width)
        lines.append("ACTIVITY MONITOR".center(self.width))
        lines.append("=" * self.width)

        if not activities:
            lines.append("No activity data".center(self.width))
            lines.append("=" * self.width)
            return {"content": "\n".join(lines), "format": "ascii"}

        # Group activities by session
        session_activities = {}
        for activity in activities[-20:]:  # Last 20 activities
            session = activity.session_name
            if session not in session_activities:
                session_activities[session] = []
            session_activities[session].append(activity)

        # Render each session's activity
        for session, sess_activities in session_activities.items():
            lines.append(f"\n{session.upper()}:")

            # Create timeline
            timeline = ["."] * 50  # 50 character timeline
            for i, activity in enumerate(sess_activities[-10:]):  # Last 10
                pos = min(49, i * 5)
                symbol = self._get_activity_symbol(activity.activity_type.value)
                timeline[pos] = symbol

            lines.append("  " + "".join(timeline))

            # Recent activity
            if sess_activities:
                recent = sess_activities[-1]
                time_str = recent.timestamp.strftime("%H:%M:%S")
                lines.append(f"  Latest: {recent.activity_type.value} at {time_str}")

        lines.append("\n" + "=" * self.width)

        return {
            "content": "\n".join(lines),
            "format": "ascii",
            "activity_count": len(activities),
        }

    @staticmethod
    def _create_progress_bar( percentage: int, width: int) -> str:
        """Create ASCII progress bar."""
        filled = int(percentage * width / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    @staticmethod
    def _get_health_indicator(level: HealthLevel) -> str:
        """Get ASCII health indicator."""
        indicators = {
            HealthLevel.EXCELLENT: "🟢 EXCELLENT",
            HealthLevel.GOOD: "🟡 GOOD",
            HealthLevel.WARNING: "🟠 WARNING",
            HealthLevel.CRITICAL: "🔴 CRITICAL",
        }
        return indicators.get(level, "❓ UNKNOWN")

    @staticmethod
    def _get_activity_symbol(activity_type: str) -> str:
        """Get symbol for activity type."""
        symbols = {
            "command": "●",
            "file_change": "◆",
            "build": "▲",
            "test": "✓",
            "error": "✗",
            "commit": "↑",
        }
        return symbols.get(activity_type, "○")

    @staticmethod
    def _format_uptime(seconds: int | None) -> str:
        """Format uptime as human-readable string."""
        if not seconds:
            return "N/A"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h{minutes}m"
        else:
            return f"{minutes}m"

    def apply_theme(self, theme: dict[str, object]) -> None:
        """Apply theme to renderer."""
        self.theme.update(theme)

    @staticmethod
    def get_capabilities() -> list[str]:
        """Get renderer capabilities."""
        return [
            "ascii_art",
            "terminal_friendly",
            "monospace_optimized",
            "low_resource",
        ]


class JSONRenderer(BaseRenderer):
    """Custom renderer that outputs structured JSON."""

    def __init__(self, theme: dict[str, object] | None = None):
        """Initialize JSON renderer.

        Args:
            theme: Optional theme configuration

        """
        super().__init__()
        self.format = RenderFormat.CUSTOM
        self.theme = theme or {}
        self.indent = 2

    def render_widget(self, widget_type: WidgetType, data: object) -> dict[str, object]:
        """Render widget as structured JSON."""
        result = {
            "widget_type": widget_type.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": self._serialize_data(data),
            "metadata": {
                "renderer": "JSONRenderer",
                "format": "json",
                "theme": self.theme.get("name", "default"),
            },
        }

        # Add widget-specific processing
        if widget_type == WidgetType.SESSION_BROWSER:
            result["summary"] = self._summarize_sessions(data)
        elif widget_type == WidgetType.PROJECT_HEALTH:
            result["summary"] = self._summarize_health(data)
        elif widget_type == WidgetType.ACTIVITY_MONITOR:
            result["summary"] = self._summarize_activity(data)

        return {
            "content": json.dumps(result, indent=self.indent),
            "data": result,
            "format": "json",
        }

    def _serialize_data(self, data: object) -> Any:
        """Serialize data to JSON-compatible format."""
        if isinstance(data, list):
            return [self._serialize_data(item) for item in data]

        elif hasattr(data, "__dict__"):
            # Handle dataclass or object
            result = {}
            for key, value in data.__dict__.items():
                if not key.startswith("_"):
                    result[key] = self._serialize_data(value)
            return result

        elif isinstance(data, datetime):
            return data.isoformat()

        elif hasattr(data, "value"):
            # Handle enum
            return data.value

        else:
            return data

    @staticmethod
    def _summarize_sessions(sessions: list[SessionData]) -> dict[str, object]:
        """Create session summary."""
        if not sessions:
            return {"total": 0, "active": 0, "inactive": 0}

        active_count = sum(1 for s in sessions if s.status == SessionStatus.ACTIVE)
        total_uptime = sum(s.uptime or 0 for s in sessions)
        avg_cpu = sum(s.cpu_usage or 0 for s in sessions) / len(sessions)

        return {
            "total": len(sessions),
            "active": active_count,
            "inactive": len(sessions) - active_count,
            "total_uptime": total_uptime,
            "average_cpu": round(avg_cpu, 2),
        }

    @staticmethod
    def _summarize_health(health: HealthData) -> dict[str, object]:
        """Create health summary."""
        category_avg = 0
        if health.categories:
            category_avg = sum(health.categories.values()) / len(health.categories)

        return {
            "overall_score": health.overall_score,
            "level": health.overall_level.value,
            "category_average": round(category_avg, 2),
            "category_count": len(health.categories or {}),
        }

    @staticmethod
    def _summarize_activity(activities: list[ActivityData]) -> dict[str, object]:
        """Create activity summary."""
        if not activities:
            return {"total": 0, "sessions": 0, "latest": None}

        sessions = set(a.session_name for a in activities)
        latest = max(activities, key=lambda a: a.timestamp)

        return {
            "total": len(activities),
            "sessions": len(sessions),
            "latest": {
                "session": latest.session_name,
                "type": latest.activity_type.value,
                "timestamp": latest.timestamp.isoformat(),
            },
        }

    def apply_theme(self, theme: dict[str, object]) -> None:
        """Apply theme to renderer."""
        self.theme.update(theme)
        # Adjust indentation based on theme
        if theme.get("compact", False):
            self.indent = None
        else:
            self.indent = 2

    @staticmethod
    def get_capabilities() -> list[str]:
        """Get renderer capabilities."""
        return [
            "structured_output",
            "machine_readable",
            "api_friendly",
            "searchable",
        ]


def demo_custom_renderers():
    """Demonstrate custom renderers."""
    print("🎨 Custom Renderer Demo")
    print("=" * 60)

    # Create sample data
    sessions = [
        SessionData(
            name="web-server",
            status=SessionStatus.ACTIVE,
            uptime=7200,  # 2 hours
            windows=3,
            cpu_usage=15.5,
            memory_usage=256.7,
        ),
        SessionData(
            name="background-worker",
            status=SessionStatus.ACTIVE,
            uptime=3600,  # 1 hour
            windows=1,
            cpu_usage=5.2,
            memory_usage=128.3,
        ),
    ]

    health = HealthData(
        overall_score=85,
        overall_level=HealthLevel.GOOD,
        categories={
            "build": 90,
            "tests": 80,
            "security": 75,
            "performance": 88,
        },
    )

    # Create custom renderers
    ascii_renderer = ASCIIRenderer()
    json_renderer = JSONRenderer()

    # Test ASCII renderer
    print("\n🎯 ASCII Renderer Output:")
    print("-" * 40)

    ascii_result = ascii_renderer.render_widget(WidgetType.SESSION_BROWSER, sessions)
    print(ascii_result["content"])

    ascii_health = ascii_renderer.render_widget(WidgetType.PROJECT_HEALTH, health)
    print("\n" + ascii_health["content"])

    # Test JSON renderer
    print("\n🎯 JSON Renderer Output:")
    print("-" * 40)

    json_result = json_renderer.render_widget(WidgetType.SESSION_BROWSER, sessions)
    print(json_result["content"][:500] + "..." if len(json_result["content"]) > 500 else json_result["content"])

    # Test with factory
    print("\n🏭 Factory Integration:")
    print("-" * 40)

    factory = RendererFactory()

    # Register custom renderers
    factory.register_renderer("ascii", ASCIIRenderer)
    factory.register_renderer("json", JSONRenderer)

    # Use custom renderers
    ascii_renderer = factory.create_renderer("ascii")
    json_renderer = factory.create_renderer("json")

    print("✅ Custom renderers registered and created via factory")

    # Test capabilities
    print(f"ASCII capabilities: {ascii_renderer.get_capabilities()}")
    print(f"JSON capabilities: {json_renderer.get_capabilities()}")


def save_renderer_examples():
    """Save renderer examples to files."""
    from pathlib import Path

    # Create output directory
    output_dir = Path("docs/examples/renderers")
    output_dir.mkdir(exist_ok=True)

    # Save ASCII renderer code
    ascii_code = '''# ASCII Renderer Implementation
# Copy this class to create your own ASCII renderer

class MyASCIIRenderer(BaseRenderer):
    """Custom ASCII art renderer"""

    @staticmethod
    def render_widget(widget_type, data):
        # Your ASCII rendering logic here
        return {"content": "ASCII output", "format": "ascii"}
'''

    with open(output_dir / "ascii_renderer_template.py", "w") as f:
        f.write(ascii_code)

    # Save JSON renderer code
    json_code = '''# JSON Renderer Implementation
# Copy this class to create your own JSON renderer

class MyJSONRenderer(BaseRenderer):
    """Custom JSON data renderer"""

    @staticmethod
    def render_widget(widget_type, data):
        # Your JSON rendering logic here
        result = {"widget_type": widget_type.value, "data": data}
        return {"content": json.dumps(result), "format": "json"}
'''

    with open(output_dir / "json_renderer_template.py", "w") as f:
        f.write(json_code)

    print("💾 Saved renderer templates to docs/examples/renderers/")


if __name__ == "__main__":
    # Run the demo
    demo_custom_renderers()

    # Save examples
    print("\n💾 Saving renderer examples...")
    save_renderer_examples()

    print("\n✨ Custom renderer example completed!")
    print("Check docs/examples/renderers/ for template files.")
