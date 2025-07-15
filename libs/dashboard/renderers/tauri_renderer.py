"""
Tauri Renderer
JSON-based renderer for Tauri desktop application integration
"""

import uuid
from datetime import datetime
from typing import Any

from .base_renderer import BaseRenderer, RenderFormat, WidgetType
from .widget_models import ActivityData, ChartData, HealthData, HealthLevel, MetricCardData, ProgressData, ProgressPhase, SessionData, StatusIndicatorData


class TauriRenderer(BaseRenderer):
    """
    Tauri renderer for generating JSON data structures

    Generates JSON objects that the Tauri desktop application can consume
    to render native UI components with chart data and interactive elements.
    """

    def __init__(self, theme: dict[str, Any] | None = None):
        """
        Initialize Tauri renderer

        Args:
            theme: Theme configuration for styling
        """
        super().__init__(RenderFormat.TAURI, theme)
        self.widget_id_counter = 0

        # Tauri style mappings
        self._style_classes = {
            "success": {
                "background": "success",
                "border_color": "success-border",
                "text_color": "success-text",
            },
            "warning": {
                "background": "warning",
                "border_color": "warning-border",
                "text_color": "warning-text",
            },
            "error": {
                "background": "error",
                "border_color": "error-border",
                "text_color": "error-text",
            },
            "info": {
                "background": "info",
                "border_color": "info-border",
                "text_color": "info-text",
            },
            "neutral": {
                "background": "surface",
                "border_color": "border",
                "text_color": "on-surface",
            },
            "primary": {
                "background": "primary",
                "border_color": "primary-border",
                "text_color": "on-primary",
            },
        }

    def render_widget(
        self,
        widget_type: WidgetType,
        data: Any,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Render a single widget as JSON structure

        Args:
            widget_type: Type of widget to render
            data: Widget data (should be appropriate model instance)
            options: Rendering options

        Returns:
            JSON object representing the widget
        """
        options = options or {}
        widget_id = self._generate_widget_id()

        # Base widget structure
        widget_json = {
            "type": "widget",
            "widget_type": widget_type.value,
            "id": widget_id,
            "data": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "format": "tauri",
                "version": "1.0",
            },
            "style": self._get_default_style(),
            "options": options,
        }

        # Route to specific widget processor
        if widget_type == WidgetType.SESSION_BROWSER:
            self._process_session_browser(widget_json, data, options)
        elif widget_type == WidgetType.HEALTH_METER:
            self._process_health_meter(widget_json, data, options)
        elif widget_type == WidgetType.ACTIVITY_HEATMAP:
            self._process_activity_heatmap(widget_json, data, options)
        elif widget_type == WidgetType.PROGRESS_TRACKER:
            self._process_progress_tracker(widget_json, data, options)
        elif widget_type == WidgetType.LOG_VIEWER:
            self._process_log_viewer(widget_json, data, options)
        elif widget_type == WidgetType.METRIC_CARD:
            self._process_metric_card(widget_json, data, options)
        elif widget_type == WidgetType.STATUS_INDICATOR:
            self._process_status_indicator(widget_json, data, options)
        elif widget_type == WidgetType.CHART:
            self._process_chart(widget_json, data, options)
        elif widget_type == WidgetType.TABLE:
            self._process_table(widget_json, data, options)
        else:
            self._process_generic_widget(widget_json, widget_type, data, options)

        return widget_json

    def render_layout(
        self,
        widgets: list[dict[str, Any]],
        layout_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Render a layout containing multiple widgets

        Args:
            widgets: List of widget configurations
            layout_config: Layout configuration

        Returns:
            JSON layout object
        """
        layout_config = layout_config or {}

        # Render individual widgets
        rendered_widgets = []
        for widget in widgets:
            widget_type = widget.get("type", WidgetType.METRIC_CARD)
            widget_data = widget.get("data", {})
            widget_options = widget.get("options", {})

            rendered = self.render_widget(widget_type, widget_data, widget_options)
            rendered_widgets.append(rendered)

        # Create layout structure
        layout_json = {
            "type": "layout",
            "layout_type": layout_config.get("type", "vertical"),
            "id": self._generate_widget_id(),
            "widgets": rendered_widgets,
            "config": layout_config,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "widget_count": len(rendered_widgets),
            },
        }

        return layout_json

    def render_container(
        self,
        content: dict[str, Any] | list[dict[str, Any]],
        container_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Render a container wrapping content

        Args:
            content: Content to wrap (widget or layout)
            container_config: Container configuration

        Returns:
            JSON container object
        """
        container_config = container_config or {}

        container_json = {
            "type": "container",
            "id": self._generate_widget_id(),
            "content": content,
            "config": {
                "title": container_config.get("title", ""),
                "border": container_config.get("border", True),
                "padding": container_config.get("padding", "medium"),
                "background": container_config.get("background", "surface"),
                "shadow": container_config.get("shadow", True),
                "rounded": container_config.get("rounded", True),
            },
            "style": self._get_container_style(container_config),
            "metadata": {
                "created_at": datetime.now().isoformat(),
            },
        }

        return container_json

    # Widget-specific processors

    def _process_session_browser(
        self,
        widget_json: dict[str, Any],
        data: SessionData | list[SessionData],
        options: dict[str, Any],
    ):
        """Process session browser widget"""
        view_mode = options.get("view_mode", "table")

        if isinstance(data, SessionData):
            sessions = [data]
        elif isinstance(data, list):
            sessions = data
        else:
            # Handle raw data
            sessions = data.get("sessions", []) if isinstance(data, dict) else []

        # Convert session data to JSON-serializable format
        sessions_data = []
        for session in sessions:
            if isinstance(session, SessionData):
                session_data = (
                    session.to_dict()
                    if hasattr(session, "to_dict")
                    else {
                        "name": session.name,
                        "id": session.id,
                        "status": session.status.value,
                        "created_at": (session.created_at.isoformat() if session.created_at else None),
                        "windows": len(session.windows),
                        "panes": session.panes,
                        "claude_active": session.claude_active,
                        "cpu_usage": getattr(session, "cpu_usage", 0.0),
                        "memory_usage": getattr(session, "memory_usage", 0.0),
                        "last_activity": (session.last_activity.isoformat() if getattr(session, "last_activity", None) else None),
                    }
                )
            else:
                session_data = session

            sessions_data.append(session_data)

        widget_json["data"] = {
            "sessions": sessions_data,
            "view_mode": view_mode,
            "total_count": len(sessions_data),
            "active_count": len([s for s in sessions_data if s.get("status") == "active"]),
            "claude_count": len([s for s in sessions_data if s.get("claude_active", False)]),
        }

        # Add action buttons for Tauri
        widget_json["actions"] = [
            {"id": "refresh", "label": "Refresh", "icon": "refresh", "type": "button"},
            {
                "id": "new_session",
                "label": "New Session",
                "icon": "plus",
                "type": "button",
            },
            {
                "id": "view_mode",
                "label": "View Mode",
                "icon": "grid",
                "type": "dropdown",
                "options": ["table", "cards", "list"],
            },
        ]

    def _process_health_meter(self, widget_json: dict[str, Any], data: HealthData, options: dict[str, Any]):
        """Process health meter widget"""
        if not isinstance(data, HealthData):
            widget_json["data"] = {"error": "Invalid health data"}
            return

        # Create chart data for the health radar chart
        categories = []
        scores = []
        colors = []

        for category in data.categories:
            categories.append(category.category.title())
            scores.append(category.score)
            colors.append(self._get_health_color(category.level))

        widget_json["data"] = {
            "overall_score": data.overall_score,
            "overall_level": (data.overall_level.label if hasattr(data.overall_level, "label") else str(data.overall_level)),
            "overall_emoji": (data.overall_level.emoji if hasattr(data.overall_level, "emoji") else ""),
            "categories": [
                {
                    "category": cat.category,
                    "score": cat.score,
                    "level": (cat.level.label if hasattr(cat.level, "label") else str(cat.level)),
                    "emoji": cat.level.emoji if hasattr(cat.level, "emoji") else "",
                    "message": cat.message,
                    "last_checked": (cat.last_checked.isoformat() if cat.last_checked else None),
                }
                for cat in data.categories
            ],
            "last_updated": (data.last_updated.isoformat() if data.last_updated else None),
            "project_path": data.project_path,
        }

        # Chart data for radar chart
        widget_json["chart_data"] = {
            "type": "radar",
            "labels": categories,
            "datasets": [
                {
                    "label": "Health Score",
                    "data": scores,
                    "backgroundColor": "rgba(59, 130, 246, 0.2)",
                    "borderColor": "rgb(59, 130, 246)",
                    "pointBackgroundColor": colors,
                    "pointBorderColor": colors,
                }
            ],
            "options": {
                "scales": {
                    "r": {
                        "beginAtZero": True,
                        "max": 100,
                    },
                },
            },
        }

        # Update style based on overall health
        widget_json["style"].update(
            self._style_classes.get(
                ("success" if data.overall_score >= 80 else "warning" if data.overall_score >= 60 else "error"),
                self._style_classes["neutral"],
            )
        )

    def _process_activity_heatmap(self, widget_json: dict[str, Any], data: ActivityData, options: dict[str, Any]):
        """Process activity heatmap widget"""
        if not isinstance(data, ActivityData):
            widget_json["data"] = {"error": "Invalid activity data"}
            return

        # Process activity entries for matrix display
        activities_by_date = {}
        for entry in data.entries:
            if hasattr(entry, "timestamp") and entry.timestamp:
                date_key = entry.timestamp.strftime("%Y-%m-%d") if isinstance(entry.timestamp, datetime) else str(entry.timestamp)[:10]
                if date_key not in activities_by_date:
                    activities_by_date[date_key] = {"count": 0, "types": set()}
                activities_by_date[date_key]["count"] += 1
                activities_by_date[date_key]["types"].add(entry.activity_type.value if hasattr(entry.activity_type, "value") else str(entry.activity_type))

        # Convert to matrix format for heatmap
        heatmap_data = []
        for date, activity_info in activities_by_date.items():
            heatmap_data.append(
                {
                    "date": date,
                    "value": activity_info["count"],
                    "level": min(4, max(0, activity_info["count"] // 5)),  # 0-4 levels
                    "types": list(activity_info["types"]),
                }
            )

        widget_json["data"] = {
            "total_activities": data.total_activities,
            "active_days": data.active_days,
            "activity_rate": data.activity_rate,
            "current_streak": data.current_streak,
            "longest_streak": data.longest_streak,
            "avg_per_day": data.avg_per_day,
            "heatmap_data": heatmap_data,
            "activity_levels": [
                {"level": 0, "color": "#ebedf0", "label": "No activity"},
                {"level": 1, "color": "#9be9a8", "label": "Low activity"},
                {"level": 2, "color": "#40c463", "label": "Medium activity"},
                {"level": 3, "color": "#30a14e", "label": "High activity"},
                {"level": 4, "color": "#216e39", "label": "Very high activity"},
            ],
        }

        # Heat level styling
        heat_level = "high" if data.activity_rate > 80 else "medium" if data.activity_rate > 40 else "low"
        widget_json["style"].update(
            self._style_classes.get(
                ("error" if heat_level == "high" else "warning" if heat_level == "medium" else "info"),
                self._style_classes["neutral"],
            )
        )

    def _process_progress_tracker(self, widget_json: dict[str, Any], data: ProgressData, options: dict[str, Any]):
        """Process progress tracker widget"""
        if not isinstance(data, ProgressData):
            widget_json["data"] = {"error": "Invalid progress data"}
            return

        widget_json["data"] = {
            "phase": data.phase.value,
            "phase_emoji": self._get_phase_emoji(data.phase),
            "phase_progress": data.phase_progress,
            "overall_progress": data.overall_progress,
            "files_created": data.files_created,
            "files_modified": data.files_modified,
            "commands_executed": data.commands_executed,
            "commands_succeeded": data.commands_succeeded,
            "commands_failed": data.commands_failed,
            "start_time": data.start_time.isoformat() if data.start_time else None,
            "active_duration": data.active_duration,
            "todos_identified": data.todos_identified,
            "todos_completed": data.todos_completed,
            "success_rate": ((data.commands_succeeded / data.commands_executed * 100) if data.commands_executed > 0 else 0),
            "completion_rate": ((data.todos_completed / data.todos_identified * 100) if data.todos_identified > 0 else 0),
        }

        # Progress chart data
        widget_json["chart_data"] = {
            "type": "doughnut",
            "labels": ["Completed", "Remaining"],
            "datasets": [
                {
                    "data": [data.overall_progress, 100 - data.overall_progress],
                    "backgroundColor": ["#10b981", "#f3f4f6"],
                    "borderWidth": 0,
                }
            ],
        }

        # Phase-based styling
        phase_color = "success" if data.phase == ProgressPhase.COMPLETED else "warning" if data.phase == ProgressPhase.ERROR else "info"
        widget_json["style"].update(self._style_classes.get(phase_color, self._style_classes["neutral"]))

    def _process_log_viewer(self, widget_json: dict[str, Any], data: dict[str, Any], options: dict[str, Any]):
        """Process log viewer widget"""
        logs = data.get("logs", []) if isinstance(data, dict) else []
        max_lines = options.get("max_lines", 100)

        # Process log entries
        processed_logs = []
        for log_entry in logs[-max_lines:]:
            if isinstance(log_entry, dict):
                processed_logs.append(
                    {
                        "timestamp": log_entry.get("timestamp", ""),
                        "level": log_entry.get("level", "INFO"),
                        "message": log_entry.get("message", ""),
                        "source": log_entry.get("source", ""),
                        "color": self._get_log_level_color(log_entry.get("level", "INFO")),
                    }
                )
            else:
                processed_logs.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "message": str(log_entry),
                        "source": "system",
                        "color": self._get_log_level_color("INFO"),
                    }
                )

        widget_json["data"] = {
            "logs": processed_logs,
            "total_count": len(logs),
            "displayed_count": len(processed_logs),
            "max_lines": max_lines,
            "level_counts": self._count_log_levels(processed_logs),
        }

        # Log viewer actions
        widget_json["actions"] = [
            {"id": "refresh", "label": "Refresh", "icon": "refresh", "type": "button"},
            {"id": "clear", "label": "Clear", "icon": "trash", "type": "button"},
            {
                "id": "download",
                "label": "Download",
                "icon": "download",
                "type": "button",
            },
            {
                "id": "filter",
                "label": "Filter",
                "icon": "filter",
                "type": "dropdown",
                "options": ["ALL", "ERROR", "WARNING", "INFO", "DEBUG"],
            },
        ]

    def _process_metric_card(self, widget_json: dict[str, Any], data: MetricCardData, options: dict[str, Any]):
        """Process metric card widget"""
        if not isinstance(data, MetricCardData):
            widget_json["data"] = {"error": "Invalid metric data"}
            return

        # Format value
        formatted_value = self.format_number(data.value) + data.suffix if isinstance(data.value, int | float) else str(data.value) + data.suffix

        widget_json["data"] = {
            "title": data.title,
            "value": data.value,
            "formatted_value": formatted_value,
            "suffix": data.suffix,
            "trend": data.trend,
            "trend_direction": ("up" if data.trend and data.trend > 0 else "down" if data.trend and data.trend < 0 else "neutral"),
            "comparison": data.comparison,
            "color": data.color,
            "icon": data.icon,
        }

        # Trend chart data (small sparkline)
        if data.trend is not None:
            trend_data = [0, data.trend] if data.trend != 0 else [0, 0]
            widget_json["chart_data"] = {
                "type": "line",
                "labels": ["Previous", "Current"],
                "datasets": [
                    {
                        "data": trend_data,
                        "borderColor": "#10b981" if data.trend >= 0 else "#ef4444",
                        "backgroundColor": "transparent",
                        "borderWidth": 2,
                        "pointRadius": 0,
                    }
                ],
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "scales": {"x": {"display": False}, "y": {"display": False}},
                    "plugins": {"legend": {"display": False}},
                },
            }

        # Color-based styling
        widget_json["style"].update(self._style_classes.get(data.color, self._style_classes["neutral"]))

    def _process_status_indicator(
        self,
        widget_json: dict[str, Any],
        data: StatusIndicatorData,
        options: dict[str, Any],
    ):
        """Process status indicator widget"""
        if not isinstance(data, StatusIndicatorData):
            widget_json["data"] = {"error": "Invalid status data"}
            return

        widget_json["data"] = {
            "status": data.status,
            "label": data.label,
            "color": data.color,
            "icon": data.icon,
            "pulse": data.pulse,
            "timestamp": datetime.now().isoformat(),
        }

        # Animation configuration for Tauri
        if data.pulse:
            widget_json["animation"] = {
                "type": "pulse",
                "duration": 2000,
                "infinite": True,
            }

        # Color-based styling
        widget_json["style"].update(self._style_classes.get(data.color, self._style_classes["neutral"]))

    def _process_chart(self, widget_json: dict[str, Any], data: ChartData, options: dict[str, Any]):
        """Process chart widget"""
        if not isinstance(data, ChartData):
            widget_json["data"] = {"error": "Invalid chart data"}
            return

        # Convert data points to chart.js format
        chart_labels = []
        chart_values = []

        for point in data.data_points:
            if hasattr(point.x, "strftime"):  # datetime
                chart_labels.append(point.x.strftime("%H:%M"))
            else:
                chart_labels.append(str(point.x))
            chart_values.append(point.y)

        widget_json["data"] = {
            "title": data.title,
            "chart_type": data.chart_type,
            "x_label": data.x_label,
            "y_label": data.y_label,
            "data_points": len(data.data_points),
        }

        # Chart.js configuration
        widget_json["chart_data"] = {
            "type": data.chart_type,
            "labels": chart_labels,
            "datasets": [
                {
                    "label": data.title,
                    "data": chart_values,
                    "backgroundColor": data.colors[0] if data.colors else "#3b82f6",
                    "borderColor": data.colors[0] if data.colors else "#3b82f6",
                    "borderWidth": 2,
                    "fill": data.chart_type == "area",
                }
            ],
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "scales": {
                    "x": {"title": {"display": True, "text": data.x_label}},
                    "y": {"title": {"display": True, "text": data.y_label}},
                },
            },
        }

    def _process_table(self, widget_json: dict[str, Any], data: dict[str, Any], options: dict[str, Any]):
        """Process table widget"""
        rows = data.get("rows", []) if isinstance(data, dict) else []
        headers = data.get("headers", []) if isinstance(data, dict) else []

        # Process table data
        processed_rows = []
        for row in rows:
            if isinstance(row, list | tuple):
                processed_rows.append([str(cell) for cell in row])
            elif isinstance(row, dict):
                processed_rows.append([str(row.get(header, "")) for header in headers])

        widget_json["data"] = {
            "headers": [str(h) for h in headers],
            "rows": processed_rows,
            "total_rows": len(processed_rows),
            "total_columns": len(headers),
        }

        # Table actions
        widget_json["actions"] = [
            {"id": "sort", "label": "Sort", "icon": "sort", "type": "button"},
            {"id": "filter", "label": "Filter", "icon": "filter", "type": "button"},
            {"id": "export", "label": "Export", "icon": "download", "type": "button"},
        ]

    def _process_generic_widget(
        self,
        widget_json: dict[str, Any],
        widget_type: WidgetType,
        data: Any,
        options: dict[str, Any],
    ):
        """Process generic widget fallback"""
        widget_json["data"] = {
            "raw_data": str(data)[:500],  # Limit size
            "data_type": type(data).__name__,
            "error": f"No specific processor for {widget_type.value}",
        }

        widget_json["style"].update(self._style_classes["warning"])

    # Helper methods

    def _generate_widget_id(self) -> str:
        """Generate unique widget ID"""
        self.widget_id_counter += 1
        return f"tauri-widget-{self.widget_id_counter}-{uuid.uuid4().hex[:8]}"

    def _get_default_style(self) -> dict[str, Any]:
        """Get default widget style"""
        return {
            "background": "surface",
            "border": True,
            "shadow": True,
            "rounded": True,
            "padding": "medium",
            "text_color": "on-surface",
            "border_color": "border",
        }

    def _get_container_style(self, config: dict[str, Any]) -> dict[str, Any]:
        """Get container style based on configuration"""
        style = self._get_default_style()

        if config.get("style"):
            style.update(self._style_classes.get(config["style"], {}))

        style.update(
            {
                "padding": config.get("padding", "medium"),
                "background": config.get("background", "surface"),
                "shadow": config.get("shadow", True),
                "rounded": config.get("rounded", True),
            }
        )

        return style

    def _get_health_color(self, health_level: HealthLevel) -> str:
        """Get color for health level"""
        color_mapping = {
            HealthLevel.EXCELLENT: "#10b981",
            HealthLevel.GOOD: "#3b82f6",
            HealthLevel.WARNING: "#f59e0b",
            HealthLevel.CRITICAL: "#ef4444",
            HealthLevel.UNKNOWN: "#6b7280",
        }
        return color_mapping.get(health_level, "#6b7280")

    def _get_phase_emoji(self, phase: ProgressPhase) -> str:
        """Get emoji for progress phase"""
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
        return phase_emojis.get(phase, "❓")

    def _get_log_level_color(self, level: str) -> str:
        """Get color for log level"""
        level_colors = {
            "ERROR": "#ef4444",
            "WARNING": "#f59e0b",
            "INFO": "#3b82f6",
            "DEBUG": "#6b7280",
        }
        return level_colors.get(level.upper(), "#6b7280")

    def _count_log_levels(self, logs: list[dict[str, Any]]) -> dict[str, int]:
        """Count log entries by level"""
        counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0}
        for log in logs:
            level = log.get("level", "INFO").upper()
            if level in counts:
                counts[level] += 1
        return counts

    def supports_feature(self, feature: str) -> bool:
        """Check if feature is supported"""
        features = {
            "json": True,
            "charts": True,
            "interactive": True,
            "actions": True,
            "animations": True,
            "themes": True,
            "serializable": True,
        }
        return features.get(feature, False)
