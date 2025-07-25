# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Web Renderer HTML/JavaScript generator for dashboard widgets."""

import html
import json
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from .base_renderer import BaseRenderer, RenderFormat, WidgetType
from .widget_models import (
    ActivityData,
    ChartData,
    HealthData,
    HealthLevel,
    MetricCardData,
    ProgressData,
    ProgressPhase,
    SessionData,
    StatusIndicatorData,
)


class WebRenderer(BaseRenderer):
    """Web renderer for generating HTML/CSS/JavaScript output.

    Generates responsive HTML components with Tailwind CSS classes and
    JavaScript data binding for interactive dashboard widgets.
    """

    def __init__(self, theme: dict[str, Any] | None = None) -> None:
        """Initialize web renderer.

        Args:
            theme: Theme configuration for styling
        """
        super().__init__(RenderFormat.WEB, theme)
        self.component_id_counter = 0

        # Tailwind CSS class mappings
        self._color_classes = {
            "success": "text-green-600 bg-green-50 border-green-200",
            "warning": "text-yellow-600 bg-yellow-50 border-yellow-200",
            "error": "text-red-600 bg-red-50 border-red-200",
            "info": "text-blue-600 bg-blue-50 border-blue-200",
            "neutral": "text-gray-600 bg-gray-50 border-gray-200",
            "primary": "text-blue-600 bg-blue-50 border-blue-200",
            "secondary": "text-purple-600 bg-purple-50 border-purple-200",
        }

        self._status_classes = {
            "active": "bg-green-100 text-green-800",
            "idle": "bg-yellow-100 text-yellow-800",
            "error": "bg-red-100 text-red-800",
            "loading": "bg-blue-100 text-blue-800",
            "stopped": "bg-gray-100 text-gray-800",
        }

    def render_widget(
        self,
        widget_type: WidgetType,
        data: Any,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Render a single widget as HTML.

        Args:
            widget_type: Type of widget to render
            data: Widget data (should be appropriate model instance)
            options: Rendering options

        Returns:
            HTML string with embedded JavaScript
        """
        options = options or {}
        component_id = self._generate_component_id()

        # Route to specific widget renderer
        if widget_type == WidgetType.SESSION_BROWSER:
            return self._render_session_browser(cast("SessionData | list[SessionData]", data), options, component_id)
        if widget_type == WidgetType.HEALTH_METER:
            return self._render_health_meter(cast("HealthData", data), options, component_id)
        if widget_type == WidgetType.ACTIVITY_HEATMAP:
            return self._render_activity_heatmap(cast("ActivityData", data), options, component_id)
        if widget_type == WidgetType.PROGRESS_TRACKER:
            return self._render_progress_tracker(cast("ProgressData", data), options, component_id)
        if widget_type == WidgetType.LOG_VIEWER:
            return self._render_log_viewer(cast("dict[str, Any]", data), options, component_id)
        if widget_type == WidgetType.METRIC_CARD:
            return self._render_metric_card(cast("MetricCardData", data), options, component_id)
        if widget_type == WidgetType.STATUS_INDICATOR:
            return self._render_status_indicator(cast("StatusIndicatorData", data), options, component_id)
        if widget_type == WidgetType.CHART:
            return self._render_chart(cast("ChartData", data), options, component_id)
        if widget_type == WidgetType.TABLE:
            return self._render_table(cast("dict[str, Any]", data), options, component_id)
        return WebRenderer._render_generic_widget(widget_type, data, options, component_id)

    def render_layout(
        self,
        widgets: list[dict[str, Any]],
        layout_config: dict[str, Any] | None = None,
    ) -> str:
        """Render a layout containing multiple widgets.

        Args:
            widgets: List of widget configurations
            layout_config: Layout configuration

        Returns:
            HTML layout string
        """
        layout_config = layout_config or {}
        layout_type = layout_config.get("type", "vertical")

        # Render individual widgets
        rendered_widgets = []
        for widget in widgets:
            widget_type = widget.get("type", WidgetType.METRIC_CARD)
            widget_data = widget.get("data", {})
            widget_options = widget.get("options", {})

            rendered = self.render_widget(widget_type, widget_data, widget_options)
            rendered_widgets.append(rendered)

        # Apply layout
        if layout_type == "grid":
            return self._render_grid_layout(rendered_widgets, layout_config)
        if layout_type == "flex":
            return self._render_flex_layout(rendered_widgets, layout_config)
        return self._render_vertical_layout(rendered_widgets, layout_config)

    def render_container(self, content: str, container_config: dict[str, Any] | None = None) -> str:
        """Render a container wrapping content.

        Args:
            content: Content to wrap
            container_config: Container configuration

        Returns:
            HTML container string
        """
        container_config = container_config or {}

        title = container_config.get("title", "")
        border = container_config.get("border", True)
        style = container_config.get("style", "")
        padding = container_config.get("padding", "p-4")

        css_classes = ["dashboard-container"]

        if border:
            css_classes.extend(["border", "rounded-lg"])
            if style:
                css_classes.append(self._color_classes.get(style, "border-gray-200"))
            else:
                css_classes.append("border-gray-200")

        if padding:
            css_classes.append(padding)

        # Build container HTML
        html_parts = [f'<div class="{" ".join(css_classes)}">']

        if title:
            html_parts.append(f'<h3 class="text-lg font-semibold mb-3 text-gray-800">{html.escape(title)}</h3>')

        html_parts.extend((content, "</div>"))

        return "\\n".join(html_parts)

    # Widget-specific renderers

    def _render_session_browser(
        self,
        data: SessionData | list[SessionData],
        options: dict[str, Any],
        component_id: str,
    ) -> str:
        """Render session browser widget."""
        view_mode = options.get("view_mode", "table")

        if isinstance(data, SessionData):
            sessions = [data]
        elif isinstance(data, list):
            sessions = data
        else:
            # Handle raw data
            sessions = data.get("sessions", []) if isinstance(data, dict) else []

        if view_mode == "cards":
            return self._render_session_cards(sessions, options, component_id)
        if view_mode == "list":
            return self._render_session_list(sessions, options, component_id)
        return self._render_session_table(sessions, options, component_id)

    def _render_session_table(self, sessions: list[SessionData], options: dict[str, Any], component_id: str) -> str:
        """Render sessions as table."""
        html_parts = [
            f'<div id="{component_id}" class="session-browser-table overflow-hidden">',
            '<div class="bg-white shadow rounded-lg">',
            '<div class="px-4 py-5 sm:p-6">',
            '<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Active Sessions</h3>',
            '<div class="overflow-x-auto">',
            '<table class="min-w-full divide-y divide-gray-200">',
            '<thead class="bg-gray-50">',
            "<tr>",
            '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>',
            '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>',
            '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Windows</th>',
            '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Panes</th>',
            '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Claude</th>',
            '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Activity</th>',
            "</tr>",
            "</thead>",
            '<tbody class="bg-white divide-y divide-gray-200">',
        ]

        for session in sessions:
            if not isinstance(session, SessionData):
                continue

            # Status badge
            status_class = self._status_classes.get(session.status.value, "bg-gray-100 text-gray-800")

            # Claude status
            claude_status = "🤖 Active" if session.claude_active else "💤 Inactive"
            claude_class = "text-green-600" if session.claude_active else "text-gray-400"

            # Activity time
            if session.last_activity:
                time_diff = datetime.now(UTC) - session.last_activity
                if time_diff.total_seconds() < 60:
                    activity = "Just now"
                elif time_diff.total_seconds() < 3600:
                    activity = f"{int(time_diff.total_seconds() // 60)}m ago"
                else:
                    activity = f"{int(time_diff.total_seconds() // 3600)}h ago"
            else:
                activity = "Unknown"

            html_parts.extend(
                [
                    '<tr class="hover:bg-gray-50">',
                    f'<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{html.escape(session.name)}</td>',
                    (
                        f'<td class="px-6 py-4 whitespace-nowrap"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_class}">'
                        f"{session.status.value.upper()}</span></td>"
                    ),
                    f'<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{len(session.windows)}</td>',
                    f'<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{session.panes}</td>',
                    f'<td class="px-6 py-4 whitespace-nowrap text-sm {claude_class}">{claude_status}</td>',
                    f'<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{activity}</td>',
                    "</tr>",
                ]
            )

        html_parts.extend(
            [
                "</tbody>",
                "</table>",
                "</div>",
                "</div>",
                "</div>",
                "</div>",
            ]
        )

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "session_browser",
                    "sessions": [s.to_dict() if hasattr(s, "to_dict") else s for s in sessions],
                    "view_mode": "table",
                },
            )
        )

        return "\\n".join(html_parts)

    def _render_session_cards(self, sessions: list[SessionData], options: dict[str, Any], component_id: str) -> str:
        """Render sessions as cards."""
        html_parts = [
            f'<div id="{component_id}" class="session-browser-cards">',
            '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">',
        ]

        for session in sessions:
            if not isinstance(session, SessionData):
                continue

            status_class = self._status_classes.get(session.status.value, "bg-gray-100 text-gray-800")

            html_parts.extend(
                [
                    '<div class="bg-white overflow-hidden shadow rounded-lg">',
                    '<div class="p-5">',
                    '<div class="flex items-center">',
                    '<div class="flex-shrink-0">',
                    '<div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">',
                    '<span class="text-sm font-medium text-blue-600">📋</span>',
                    "</div>",
                    "</div>",
                    '<div class="ml-5 w-0 flex-1">',
                    '<dl><dt class="text-sm font-medium text-gray-500 truncate">Session</dt>',
                    f'<dd class="text-lg font-medium text-gray-900">{html.escape(session.name)}</dd></dl>',
                    "</div>",
                    "</div>",
                    '<div class="mt-5">',
                    '<div class="flex items-center justify-between">',
                    f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_class}">{session.status.value.upper()}</span>',
                    f'<span class="text-sm text-gray-500">{"🤖" if session.claude_active else "💤"}</span>',
                    "</div>",
                    '<div class="mt-3 grid grid-cols-2 gap-4 text-sm text-gray-500">',
                    f'<div><span class="font-medium">Windows:</span> {len(session.windows)}</div>',
                    f'<div><span class="font-medium">Panes:</span> {session.panes}</div>',
                    "</div>",
                    "</div>",
                    "</div>",
                    "</div>",
                ]
            )

        html_parts.extend(
            [
                "</div>",
                "</div>",
            ]
        )

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "session_browser",
                    "sessions": [s.to_dict() if hasattr(s, "to_dict") else s for s in sessions],
                    "view_mode": "cards",
                },
            )
        )

        return "\\n".join(html_parts)

    def _render_session_list(self, sessions: list[SessionData], options: dict[str, Any], component_id: str) -> str:
        """Render sessions as list."""
        html_parts = [
            f'<div id="{component_id}" class="session-browser-list">',
            '<div class="bg-white shadow overflow-hidden sm:rounded-md">',
            '<ul class="divide-y divide-gray-200">',
        ]

        for session in sessions:
            if not isinstance(session, SessionData):
                continue

            status_class = self._status_classes.get(session.status.value, "bg-gray-100 text-gray-800")

            html_parts.extend(
                [
                    '<li class="px-6 py-4 hover:bg-gray-50">',
                    '<div class="flex items-center justify-between">',
                    '<div class="flex items-center">',
                    '<div class="flex-shrink-0 h-10 w-10">',
                    '<div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">',
                    '<span class="text-sm font-medium text-blue-600">📋</span>',
                    "</div>",
                    "</div>",
                    '<div class="ml-4">',
                    f'<div class="text-sm font-medium text-gray-900">{html.escape(session.name)}</div>',
                    f'<div class="text-sm text-gray-500">{len(session.windows)} windows, {session.panes} panes</div>',
                    "</div>",
                    "</div>",
                    '<div class="flex items-center space-x-2">',
                    f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_class}">{session.status.value.upper()}</span>',
                    f'<span class="text-lg">{"🤖" if session.claude_active else "💤"}</span>',
                    "</div>",
                    "</div>",
                    "</li>",
                ]
            )

        html_parts.extend(
            [
                "</ul>",
                "</div>",
                "</div>",
            ]
        )

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "session_browser",
                    "sessions": [s.to_dict() if hasattr(s, "to_dict") else s for s in sessions],
                    "view_mode": "list",
                },
            )
        )

        return "\\n".join(html_parts)

    def _render_health_meter(self, data: HealthData, options: dict[str, Any], component_id: str) -> str:
        """Render health meter widget."""
        if not isinstance(data, HealthData):
            return self._render_error_widget("Invalid health data", component_id)

        # Health color based on level
        health_color = self._get_health_color_class(data.overall_level)

        html_parts = [
            f'<div id="{component_id}" class="health-meter bg-white shadow rounded-lg p-6">',
            f'<h3 class="text-lg font-semibold text-gray-900 mb-4">{data.overall_level.emoji} Project Health</h3>',
            '<div class="space-y-4">',
            # Overall score progress bar
            "<div>",
            '<div class="flex justify-between text-sm font-medium text-gray-700 mb-1">',
            "<span>Overall Score</span>",
            f"<span>{data.overall_score}%</span>",
            "</div>",
            '<div class="w-full bg-gray-200 rounded-full h-2">',
            f'<div class="bg-{health_color} h-2 rounded-full transition-all duration-300" style="width: {data.overall_score}%"></div>',
            "</div>",
            "</div>",
            # Categories breakdown
            '<div class="space-y-2">',
        ]

        for category in data.categories:
            self._get_health_color_class(category.level)
            html_parts.extend(
                [
                    '<div class="flex items-center justify-between py-2">',
                    f'<span class="text-sm font-medium text-gray-700 capitalize">{category.category}</span>',
                    '<div class="flex items-center space-x-2">',
                    f'<span class="text-sm text-gray-500">{category.score}%</span>',
                    f'<span class="text-lg">{category.level.emoji}</span>',
                    "</div>",
                    "</div>",
                ]
            )

        html_parts.extend(
            [
                "</div>",
                "</div>",
                "</div>",
            ]
        )

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "health_meter",
                    "data": data.to_dict() if hasattr(data, "to_dict") else data,
                },
            )
        )

        return "\\n".join(html_parts)

    def _render_activity_heatmap(self, data: ActivityData, options: dict[str, Any], component_id: str) -> str:
        """Render activity heatmap widget."""
        if not isinstance(data, ActivityData):
            return self._render_error_widget("Invalid activity data", component_id)

        # Activity level indicators
        if data.activity_rate > 80:
            heat_level = "🔥🔥🔥"
            color_class = "text-red-600"
        elif data.activity_rate > 60:
            heat_level = "🔥🔥"
            color_class = "text-orange-600"
        elif data.activity_rate > 40:
            heat_level = "🔥"
            color_class = "text-yellow-600"
        else:
            heat_level = "❄️"
            color_class = "text-blue-600"

        html_parts = [
            f'<div id="{component_id}" class="activity-heatmap bg-white shadow rounded-lg p-6">',
            '<h3 class="text-lg font-semibold text-gray-900 mb-4">📊 Activity Overview</h3>',
            '<div class="space-y-4">',
            # Activity stats
            '<div class="grid grid-cols-2 gap-4 text-sm">',
            f'<div><span class="font-medium text-gray-700">Total Activities:</span> <span class="text-gray-900">{data.total_activities}</span></div>',
            f'<div><span class="font-medium text-gray-700">Active Days:</span> <span class="text-gray-900">{data.active_days}</span></div>',
            f'<div><span class="font-medium text-gray-700">Current Streak:</span> <span class="text-gray-900">{data.current_streak} days</span></div>',
            f'<div><span class="font-medium text-gray-700">Longest Streak:</span> <span class="text-gray-900">{data.longest_streak} days</span></div>',
            "</div>",
            # Activity level
            '<div class="border-t pt-4">',
            '<div class="flex items-center justify-between">',
            '<span class="text-sm font-medium text-gray-700">Activity Level:</span>',
            f'<div class="flex items-center space-x-2"><span class="{color_class} text-lg">{heat_level}</span><span class="text-sm font-medium {color_class}">{data.activity_rate:.1f}%</span></div>',
            "</div>",
            "</div>",
            "</div>",
            "</div>",
        ]

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "activity_heatmap",
                    "data": data.to_dict() if hasattr(data, "to_dict") else data,
                },
            )
        )

        return "\\n".join(html_parts)

    def _render_progress_tracker(self, data: ProgressData, options: dict[str, Any], component_id: str) -> str:
        """Render progress tracker widget."""
        if not isinstance(data, ProgressData):
            return self._render_error_widget("Invalid progress data", component_id)

        # Phase emoji
        phase_emojis = {
            ProgressPhase.STARTING: "🚀",
            ProgressPhase.ANALYZING: "🔍",
            ProgressPhase.IMPLEMENTING: "⚙️",
            ProgressPhase.TESTING: "🧪",
            ProgressPhase.COMPLETING: "✅",
            ProgressPhase.COMPLETED: "🎉",
            ProgressPhase.IDLE: "💤",
            ProgressPhase.ERROR: "❌",
        }
        phase_emoji = phase_emojis.get(data.phase, "❓")

        html_parts = [
            f'<div id="{component_id}" class="progress-tracker bg-white shadow rounded-lg p-6">',
            f'<h3 class="text-lg font-semibold text-gray-900 mb-4">{phase_emoji} Progress Tracker</h3>',
            '<div class="space-y-4">',
            # Overall progress
            "<div>",
            '<div class="flex justify-between text-sm font-medium text-gray-700 mb-1">',
            "<span>Overall Progress</span>",
            f"<span>{data.overall_progress:.0f}%</span>",
            "</div>",
            '<div class="w-full bg-gray-200 rounded-full h-2">',
            f'<div class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: {data.overall_progress}%"></div>',
            "</div>",
            "</div>",
            # Phase progress
            "<div>",
            '<div class="flex justify-between text-sm font-medium text-gray-700 mb-1">',
            f"<span>{data.phase.value.title()} Phase</span>",
            f"<span>{data.phase_progress:.0f}%</span>",
            "</div>",
            '<div class="w-full bg-gray-200 rounded-full h-2">',
            f'<div class="bg-green-600 h-2 rounded-full transition-all duration-300" style="width: {data.phase_progress}%"></div>',
            "</div>",
            "</div>",
            # Stats
            '<div class="border-t pt-4">',
            '<div class="grid grid-cols-2 gap-4 text-sm">',
            f'<div><span class="font-medium text-gray-700">Files Created:</span> <span class="text-gray-900">{data.files_created}</span></div>',
            f'<div><span class="font-medium text-gray-700">Files Modified:</span> <span class="text-gray-900">{data.files_modified}</span></div>',
            f'<div><span class="font-medium text-gray-700">Commands:</span> <span class="text-gray-900">{data.commands_executed}</span></div>',
            f'<div><span class="font-medium text-gray-700">TODOs:</span> <span class="text-gray-900">{data.todos_completed}/{data.todos_identified}</span></div>',
            "</div>",
            "</div>",
            "</div>",
            "</div>",
        ]

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "progress_tracker",
                    "data": data.to_dict() if hasattr(data, "to_dict") else data,
                },
            )
        )

        return "\\n".join(html_parts)

    def _render_log_viewer(self, data: dict[str, Any], options: dict[str, Any], component_id: str) -> str:
        """Render log viewer widget."""
        logs = data.get("logs", []) if isinstance(data, dict) else []
        max_lines = options.get("max_lines", 10)

        # Log level colors
        level_colors = {
            "ERROR": "text-red-600 bg-red-50",
            "WARNING": "text-yellow-600 bg-yellow-50",
            "INFO": "text-blue-600 bg-blue-50",
            "DEBUG": "text-gray-600 bg-gray-50",
        }

        html_parts = [
            f'<div id="{component_id}" class="log-viewer bg-white shadow rounded-lg">',
            '<div class="px-4 py-5 sm:p-6">',
            '<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">📜 Recent Logs</h3>',
            '<div class="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">',
            '<div class="space-y-2 font-mono text-sm">',
        ]

        for log_entry in logs[-max_lines:]:
            if isinstance(log_entry, dict):
                timestamp = log_entry.get("timestamp", "")
                level = log_entry.get("level", "INFO")
                message = log_entry.get("message", str(log_entry))

                level_class = level_colors.get(level.upper(), "text-gray-600 bg-gray-50")

                html_parts.extend(
                    [
                        '<div class="flex items-start space-x-2">',
                        f'<span class="text-xs text-gray-500 mt-0.5">[{html.escape(timestamp)}]</span>',
                        f'<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {level_class}">{level}</span>',
                        f'<span class="flex-1 text-gray-900">{html.escape(message)}</span>',
                        "</div>",
                    ]
                )
            else:
                html_parts.append(f'<div class="text-gray-900">{html.escape(str(log_entry))}</div>')

        html_parts.extend(
            [
                "</div>",
                "</div>",
                "</div>",
                "</div>",
            ]
        )

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "log_viewer",
                    "data": data,
                    "options": options,
                },
            )
        )

        return "\\n".join(html_parts)

    def _render_metric_card(self, data: MetricCardData, options: dict[str, Any], component_id: str) -> str:
        """Render metric card widget."""
        if not isinstance(data, MetricCardData):
            return self._render_error_widget("Invalid metric data", component_id)

        # Format value
        formatted_value = self.format_number(data.value) + data.suffix if isinstance(data.value, int | float) else str(data.value) + data.suffix

        # Trend indicator
        trend_html = ""
        if data.trend is not None:
            if data.trend > 0:
                trend_html = f'<span class="text-green-600">↗️ +{data.trend}</span>'
            elif data.trend < 0:
                trend_html = f'<span class="text-red-600">↘️ {data.trend}</span>'
            else:
                trend_html = '<span class="text-gray-600">➡️ 0</span>'

        color_class = self._color_classes.get(data.color, "text-gray-600 bg-gray-50 border-gray-200")

        html_parts = [
            f'<div id="{component_id}" class="metric-card bg-white shadow rounded-lg border {color_class}">',
            '<div class="p-5">',
            '<div class="flex items-center">',
            '<div class="flex-shrink-0">',
        ]

        if data.icon:
            html_parts.extend(
                [
                    '<div class="w-8 h-8 flex items-center justify-center">',
                    f'<span class="text-2xl">{data.icon}</span>',
                    "</div>",
                ]
            )

        html_parts.extend(
            [
                "</div>",
                '<div class="ml-5 w-0 flex-1">',
                f'<dl><dt class="text-sm font-medium text-gray-500 truncate">{html.escape(data.title)}</dt>',
                f'<dd class="text-2xl font-bold text-gray-900">{formatted_value}</dd></dl>',
                "</div>",
                "</div>",
            ]
        )

        if trend_html or data.comparison:
            html_parts.extend(
                [
                    '<div class="mt-4 border-t pt-4">',
                    '<div class="flex items-center justify-between text-sm">',
                ]
            )

            if data.comparison:
                html_parts.append(f'<span class="text-gray-500">{html.escape(data.comparison)}</span>')

            if trend_html:
                html_parts.append(trend_html)

            html_parts.extend(
                [
                    "</div>",
                    "</div>",
                ]
            )

        html_parts.extend(
            [
                "</div>",
                "</div>",
            ]
        )

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "metric_card",
                    "data": data.to_dict() if hasattr(data, "to_dict") else data,
                },
            )
        )

        return "\\n".join(html_parts)

    def _render_status_indicator(self, data: StatusIndicatorData, options: dict[str, Any], component_id: str) -> str:
        """Render status indicator widget."""
        if not isinstance(data, StatusIndicatorData):
            return self._render_error_widget("Invalid status data", component_id)

        color_class = self._color_classes.get(data.color, "text-gray-600 bg-gray-50 border-gray-200")
        pulse_class = "animate-pulse" if data.pulse else ""

        html_parts = [
            f'<div id="{component_id}" class="status-indicator">',
            f'<div class="inline-flex items-center space-x-2 px-3 py-2 rounded-full border {color_class} {pulse_class}">',
        ]

        if data.icon:
            html_parts.append(f'<span class="text-lg">{data.icon}</span>')

        html_parts.extend(
            [
                f'<span class="font-medium text-sm uppercase tracking-wide">{html.escape(data.status)}</span>',
                "</div>",
            ]
        )

        if data.label:
            html_parts.append(f'<div class="mt-1 text-xs text-gray-500 text-center">{html.escape(data.label)}</div>')

        html_parts.append("</div>")

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "status_indicator",
                    "data": data.to_dict() if hasattr(data, "to_dict") else data,
                },
            )
        )

        return "\\n".join(html_parts)

    def _render_chart(self, data: ChartData, options: dict[str, Any], component_id: str) -> str:
        """Render chart widget."""
        if not isinstance(data, ChartData):
            return self._render_error_widget("Invalid chart data", component_id)

        html_parts = [
            f'<div id="{component_id}" class="chart-widget bg-white shadow rounded-lg p-6">',
            f'<h3 class="text-lg font-semibold text-gray-900 mb-4">📈 {html.escape(data.title)}</h3>',
            '<div class="chart-container h-64">',
            "<!-- Chart will be rendered here by JavaScript -->",
            '<div class="flex items-center justify-center h-full text-gray-500">',
            "<span>Chart data loading...</span>",
            "</div>",
            "</div>",
            "</div>",
        ]

        # Add JavaScript data with chart configuration
        chart_config = {
            "type": "chart",
            "data": data.to_dict() if hasattr(data, "to_dict") else data,
            "chart_type": data.chart_type,
            "title": data.title,
        }

        html_parts.append(self._embed_widget_data(component_id, chart_config))

        return "\\n".join(html_parts)

    def _render_table(self, data: dict[str, Any], options: dict[str, Any], component_id: str) -> str:
        """Render generic table."""
        rows = data.get("rows", []) if isinstance(data, dict) else []
        headers = data.get("headers", []) if isinstance(data, dict) else []

        html_parts = [
            f'<div id="{component_id}" class="table-widget bg-white shadow rounded-lg overflow-hidden">',
            '<div class="overflow-x-auto">',
            '<table class="min-w-full divide-y divide-gray-200">',
        ]

        # Headers
        if headers:
            html_parts.extend(
                [
                    '<thead class="bg-gray-50">',
                    "<tr>",
                ]
            )

            html_parts.extend(f'<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{html.escape(str(header))}</th>' for header in headers)

            html_parts.extend(
                [
                    "</tr>",
                    "</thead>",
                ]
            )

        # Body
        html_parts.append('<tbody class="bg-white divide-y divide-gray-200">')

        for row in rows:
            html_parts.append('<tr class="hover:bg-gray-50">')

            if isinstance(row, list | tuple):
                html_parts.extend(f'<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{html.escape(str(cell))}</td>' for cell in row)
            elif isinstance(row, dict):
                for header in headers:
                    cell_value = row.get(header, "")
                    html_parts.append(f'<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{html.escape(str(cell_value))}</td>')

            html_parts.append("</tr>")

        html_parts.extend(
            [
                "</tbody>",
                "</table>",
                "</div>",
                "</div>",
            ]
        )

        # Add JavaScript data
        html_parts.append(
            self._embed_widget_data(
                component_id,
                {
                    "type": "table",
                    "data": data,
                },
            )
        )

        return "\\n".join(html_parts)

    @staticmethod
    def _render_generic_widget(
        widget_type: WidgetType,
        data: object,
        options: dict[str, Any],
        component_id: str,
    ) -> str:
        """Render generic widget fallback."""
        html_parts = [
            f'<div id="{component_id}" class="generic-widget bg-yellow-50 border border-yellow-200 rounded-lg p-4">',
            f'<h4 class="text-lg font-medium text-yellow-800">🔧 {widget_type.value.replace("_", " ").title()}</h4>',
            '<p class="text-sm text-yellow-700 mt-2">Widget renderer not implemented</p>',
            f'<pre class="text-xs text-yellow-600 mt-2 overflow-auto">{html.escape(str(data)[:200])}</pre>',
            "</div>",
        ]

        return "\\n".join(html_parts)

    @staticmethod
    def _render_error_widget(error_message: str, component_id: str) -> str:
        """Render error widget."""
        return f"""
        <div id="{component_id}" class="error-widget bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <span class="text-red-400 text-xl">❌</span>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Rendering Error</h3>
                    <p class="text-sm text-red-700 mt-1">{html.escape(error_message)}</p>
                </div>
            </div>
        </div>
        """

    # Layout renderers

    @staticmethod
    def _render_vertical_layout(widgets: list[str], config: dict[str, Any]) -> str:
        """Render widgets in vertical layout."""
        spacing = config.get("spacing", "space-y-4")
        css_classes = ["dashboard-layout-vertical", spacing]

        html_parts = [f'<div class="{" ".join(css_classes)}">']
        html_parts.extend(widgets)
        html_parts.append("</div>")

        return "\\n".join(html_parts)

    @staticmethod
    def _render_flex_layout(widgets: list[str], config: dict[str, Any]) -> str:
        """Render widgets in flex layout."""
        direction = config.get("direction", "row")
        gap = config.get("gap", "gap-4")

        flex_class = "flex-row" if direction == "row" else "flex-col"
        css_classes = ["dashboard-layout-flex", "flex", flex_class, gap]

        html_parts = [f'<div class="{" ".join(css_classes)}">']

        html_parts.extend(f'<div class="flex-1">{widget}</div>' for widget in widgets)

        html_parts.append("</div>")

        return "\\n".join(html_parts)

    @staticmethod
    def _render_grid_layout(widgets: list[str], config: dict[str, Any]) -> str:
        """Render widgets in grid layout."""
        columns = config.get("columns", 2)
        gap = config.get("gap", "gap-4")

        grid_cols = f"grid-cols-1 md:grid-cols-{columns}"
        css_classes = ["dashboard-layout-grid", "grid", grid_cols, gap]

        html_parts = [f'<div class="{" ".join(css_classes)}">']
        html_parts.extend(widgets)
        html_parts.append("</div>")

        return "\\n".join(html_parts)

    # Helper methods

    def _generate_component_id(self) -> str:
        """Generate unique component ID."""
        self.component_id_counter += 1
        return f"widget-{self.component_id_counter}-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _get_health_color_class(health_level: HealthLevel) -> str:
        """Get Tailwind color class for health level."""
        color_mapping = {
            HealthLevel.EXCELLENT: "green-600",
            HealthLevel.GOOD: "blue-600",
            HealthLevel.WARNING: "yellow-600",
            HealthLevel.CRITICAL: "red-600",
            HealthLevel.UNKNOWN: "gray-600",
        }
        return color_mapping.get(health_level, "gray-600")

    @staticmethod
    def _embed_widget_data(component_id: str, data: dict[str, Any]) -> str:
        """Embed JavaScript data for widget."""
        json_data = json.dumps(data, default=str, ensure_ascii=False)

        return f"""
<script>
(function() {{
    if (typeof window.widgetData === 'undefined') {{
        window.widgetData = {{}};
    }}
    window.widgetData['{component_id}'] = {json_data};
}})();
</script>
        """

    @staticmethod
    def supports_feature(feature: str) -> bool:
        """Check if feature is supported."""
        features = {
            "html": True,
            "css": True,
            "javascript": True,
            "interactive": True,
            "responsive": True,
            "themes": True,
            "animations": True,
        }
        return features.get(feature, False)
