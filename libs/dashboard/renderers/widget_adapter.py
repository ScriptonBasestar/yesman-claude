# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Widget Data Adapter Converts raw data from various sources into standardized
widget models."""

import logging
from datetime import UTC, datetime
from typing import Any

from .widget_models import (
    ActivityData,
    ActivityEntry,
    ActivityType,
    ChartData,
    ChartDataPoint,
    HealthCategoryData,
    HealthData,
    HealthLevel,
    MetricCardData,
    ProgressData,
    ProgressPhase,
    SessionData,
    SessionStatus,
    StatusIndicatorData,
    WindowData,
)

logger = logging.getLogger(__name__)


class WidgetDataAdapter:
    """Adapter class for converting raw data into widget model instances.

    This class handles the transformation of various data formats (API
    responses, database records, configuration files) into the
    standardized widget models used by all renderers.
    """

    def __init__(self) -> None:
        """Initialize the adapter."""
        self.logger = logging.getLogger("yesman.dashboard.widget_adapter")

    def adapt_session_data(self, raw_data: dict[str, Any] | list[dict[str, Any]]) -> SessionData | list[SessionData]:
        """Convert raw session data to SessionData model(s).

        Args:
            raw_data: Raw session data from tmux or API

        Returns:
            SessionData instance or list of instances
        """
        if isinstance(raw_data, list):
            return [self._adapt_single_session(session_data) for session_data in raw_data]

        return self._adapt_single_session(raw_data)

    def _adapt_single_session(self, data: dict[str, Any]) -> SessionData:
        """Convert single session data."""
        try:
            # Parse session status
            status_str = data.get("status", "idle").lower()
            status = self._parse_session_status(status_str)

            # Parse timestamps
            created_at = self._parse_timestamp(data.get("created_at") or data.get("created"))
            last_activity = self._parse_timestamp(data.get("last_activity") or data.get("last_active"))

            # Parse windows
            windows = []
            raw_windows = data.get("windows", [])
            if isinstance(raw_windows, list):
                for i, window_data in enumerate(raw_windows):
                    if isinstance(window_data, dict):
                        windows.append(
                            WindowData(
                                id=str(window_data.get("id", i)),
                                name=window_data.get("name", f"window-{i}"),
                                active=window_data.get("active", False),
                                panes=window_data.get("panes", 1),
                                layout=window_data.get("layout", "even-horizontal"),
                                metadata=window_data.get("metadata", {}),
                            )
                        )
                    else:
                        # Handle simple window names
                        windows.append(
                            WindowData(
                                id=str(i),
                                name=str(window_data),
                                active=False,
                                panes=1,
                                layout="even-horizontal",
                                metadata={},
                            )
                        )

            return SessionData(
                name=data.get("name") or data.get("session_name", "unknown"),
                id=str(data.get("id") or data.get("session_id", "")),
                status=status,
                created_at=created_at or datetime.now(UTC),
                last_activity=last_activity,
                windows=windows,
                panes=data.get("panes", len(windows)),
                claude_active=data.get("claude_active", False),
                metadata=data.get("metadata", {}),
                cpu_usage=float(data.get("cpu_usage", 0.0)),
                memory_usage=float(data.get("memory_usage", 0.0)),
            )

        except Exception as e:
            self.logger.exception("Error adapting session data")  # noqa: G004
            # Return a minimal session object
            return SessionData(
                name=data.get("name", "unknown"),
                id=str(data.get("id", "")),
                status=SessionStatus.ERROR,
                created_at=datetime.now(UTC),
                last_activity=None,
                windows=[],
                panes=0,
                claude_active=False,
                metadata={"error": str(e)},
            )

    def adapt_health_data(self, raw_data: dict[str, Any]) -> HealthData:
        """Convert raw health data to HealthData model.

        Args:
            raw_data: Raw health data from health calculator

        Returns:
            HealthData instance
        """
        try:
            # Parse overall score and level
            overall_score = int(raw_data.get("overall_score", 0))
            overall_level = HealthLevel.from_score(overall_score)

            # Parse categories
            categories = []
            raw_categories = raw_data.get("categories", {})

            if isinstance(raw_categories, dict):
                for category_name, category_data in raw_categories.items():
                    if isinstance(category_data, dict):
                        score = int(category_data.get("score", 0))
                        level = HealthLevel.from_score(score)

                        last_checked = self._parse_timestamp(category_data.get("last_checked"))

                        categories.append(
                            HealthCategoryData(
                                category=category_name,
                                score=score,
                                level=level,
                                message=category_data.get("message", ""),
                                details=category_data.get("details", {}),
                                last_checked=last_checked,
                            )
                        )
            elif isinstance(raw_categories, list):
                for category_data in raw_categories:
                    if isinstance(category_data, dict):
                        score = int(category_data.get("score", 0))
                        level = HealthLevel.from_score(score)

                        last_checked = self._parse_timestamp(category_data.get("last_checked"))

                        categories.append(
                            HealthCategoryData(
                                category=category_data.get("category", "unknown"),
                                score=score,
                                level=level,
                                message=category_data.get("message", ""),
                                details=category_data.get("details", {}),
                                last_checked=last_checked,
                            )
                        )

            last_updated = self._parse_timestamp(raw_data.get("last_updated") or raw_data.get("timestamp"))

            return HealthData(
                overall_score=overall_score,
                overall_level=overall_level,
                categories=categories,
                last_updated=last_updated or datetime.now(UTC),
                project_path=raw_data.get("project_path", ""),
                metadata=raw_data.get("metadata", {}),
            )

        except Exception as e:
            self.logger.exception("Error adapting health data")  # noqa: G004
            return HealthData(
                overall_score=0,
                overall_level=HealthLevel.UNKNOWN,
                categories=[],
                last_updated=datetime.now(UTC),
                project_path="",
                metadata={"error": str(e)},
            )

    def adapt_activity_data(self, raw_data: dict[str, Any]) -> ActivityData:
        """Convert raw activity data to ActivityData model.

        Args:
            raw_data: Raw activity data from git or file system

        Returns:
            ActivityData instance
        """
        try:
            # Parse activity entries
            entries = []
            raw_entries = raw_data.get("activities", []) or raw_data.get("entries", [])

            for entry_data in raw_entries:
                if isinstance(entry_data, dict):
                    timestamp = self._parse_timestamp(entry_data.get("timestamp") or entry_data.get("date"))

                    # Parse activity type
                    activity_type_str = entry_data.get("type", "file_modified").lower()
                    activity_type = self._parse_activity_type(activity_type_str)

                    entries.append(
                        ActivityEntry(
                            timestamp=timestamp or datetime.now(UTC),
                            activity_type=activity_type,
                            description=entry_data.get("description", ""),
                            details=entry_data.get("details", {}),
                            metadata=entry_data.get("metadata", {}),
                        )
                    )

            return ActivityData(
                entries=entries,
                total_activities=raw_data.get("total_activities", len(entries)),
                active_days=raw_data.get("active_days", 0),
                activity_rate=float(raw_data.get("activity_rate", 0.0)),
                current_streak=raw_data.get("current_streak", 0),
                longest_streak=raw_data.get("longest_streak", 0),
                avg_per_day=float(raw_data.get("avg_per_day", 0.0)),
                date_range=raw_data.get("date_range", {}),
                metadata=raw_data.get("metadata", {}),
            )

        except Exception as e:
            self.logger.exception("Error adapting activity data")  # noqa: G004
            return ActivityData(
                entries=[],
                total_activities=0,
                active_days=0,
                activity_rate=0.0,
                current_streak=0,
                longest_streak=0,
                avg_per_day=0.0,
                date_range={},
                metadata={"error": str(e)},
            )

    def adapt_progress_data(self, raw_data: dict[str, Any]) -> ProgressData:
        """Convert raw progress data to ProgressData model.

        Args:
            raw_data: Raw progress data from task tracker

        Returns:
            ProgressData instance
        """
        try:
            # Parse phase
            phase_str = raw_data.get("phase", "idle").lower()
            phase = self._parse_progress_phase(phase_str)

            # Parse timestamps
            start_time = self._parse_timestamp(raw_data.get("start_time"))
            phase_start_time = self._parse_timestamp(raw_data.get("phase_start_time"))

            return ProgressData(
                phase=phase,
                phase_progress=float(raw_data.get("phase_progress", 0.0)),
                overall_progress=float(raw_data.get("overall_progress", 0.0)),
                files_created=int(raw_data.get("files_created", 0)),
                files_modified=int(raw_data.get("files_modified", 0)),
                lines_added=int(raw_data.get("lines_added", 0)),
                lines_removed=int(raw_data.get("lines_removed", 0)),
                commands_executed=int(raw_data.get("commands_executed", 0)),
                commands_succeeded=int(raw_data.get("commands_succeeded", 0)),
                commands_failed=int(raw_data.get("commands_failed", 0)),
                start_time=start_time,
                phase_start_time=phase_start_time,
                active_duration=float(raw_data.get("active_duration", 0.0)),
                idle_duration=float(raw_data.get("idle_duration", 0.0)),
                todos_identified=int(raw_data.get("todos_identified", 0)),
                todos_completed=int(raw_data.get("todos_completed", 0)),
                metadata=raw_data.get("metadata", {}),
            )

        except Exception as e:
            self.logger.exception("Error adapting progress data")  # noqa: G004
            return ProgressData(
                phase=ProgressPhase.ERROR,
                phase_progress=0.0,
                overall_progress=0.0,
                files_created=0,
                files_modified=0,
                lines_added=0,
                lines_removed=0,
                commands_executed=0,
                commands_succeeded=0,
                commands_failed=0,
                start_time=None,
                phase_start_time=None,
                active_duration=0.0,
                idle_duration=0.0,
                todos_identified=0,
                todos_completed=0,
                metadata={"error": str(e)},
            )

    @staticmethod
    def adapt_metric_card_data(raw_data: dict[str, Any]) -> MetricCardData:
        """Convert raw data to MetricCardData model."""
        return MetricCardData(
            title=raw_data.get("title", ""),
            value=raw_data.get("value", 0),
            suffix=raw_data.get("suffix", ""),
            trend=raw_data.get("trend"),
            comparison=raw_data.get("comparison"),
            color=raw_data.get("color", "neutral"),
            icon=raw_data.get("icon", ""),
            metadata=raw_data.get("metadata", {}),
        )

    @staticmethod
    def adapt_status_indicator_data(raw_data: dict[str, Any]) -> StatusIndicatorData:
        """Convert raw data to StatusIndicatorData model."""
        return StatusIndicatorData(
            status=raw_data.get("status", "unknown"),
            label=raw_data.get("label", ""),
            color=raw_data.get("color", "neutral"),
            icon=raw_data.get("icon", ""),
            pulse=raw_data.get("pulse", False),
            metadata=raw_data.get("metadata", {}),
        )

    def adapt_chart_data(self, raw_data: dict[str, Any]) -> ChartData:
        """Convert raw data to ChartData model."""
        # Parse data points
        data_points = []
        raw_points = raw_data.get("data", []) or raw_data.get("data_points", [])

        for point_data in raw_points:
            if isinstance(point_data, dict):
                x_value = point_data.get("x")
                if isinstance(x_value, str):
                    # Try to parse as datetime
                    x_value = self._parse_timestamp(x_value) or x_value

                data_points.append(
                    ChartDataPoint(
                        x=x_value,
                        y=point_data.get("y", 0),
                        label=point_data.get("label"),
                        metadata=point_data.get("metadata", {}),
                    )
                )
            elif isinstance(point_data, list | tuple) and len(point_data) >= 2:
                # Handle [x, y] format
                data_points.append(
                    ChartDataPoint(
                        x=point_data[0],
                        y=point_data[1],
                        label=point_data[2] if len(point_data) > 2 else None,
                        metadata={},
                    )
                )

        return ChartData(
            title=raw_data.get("title", ""),
            chart_type=raw_data.get("type", "line"),
            data_points=data_points,
            x_label=raw_data.get("x_label", ""),
            y_label=raw_data.get("y_label", ""),
            colors=raw_data.get("colors", []),
            metadata=raw_data.get("metadata", {}),
        )

    # Helper methods

    @staticmethod
    def _parse_timestamp(timestamp: object) -> datetime | None:
        """Parse various timestamp formats to datetime."""
        if timestamp is None:
            return None

        if isinstance(timestamp, datetime):
            return timestamp

        if isinstance(timestamp, int | float):
            try:
                return datetime.fromtimestamp(timestamp)
            except (ValueError, OSError):
                return None

        if isinstance(timestamp, str):
            # Try various formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d",
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue

            # Try ISO format parsing
            try:
                return datetime.fromisoformat(timestamp)
            except (ValueError, AttributeError):
                pass

        return None

    @staticmethod
    def _parse_session_status(status_str: str) -> SessionStatus:
        """Parse session status string."""
        status_mapping = {
            "active": SessionStatus.ACTIVE,
            "running": SessionStatus.ACTIVE,
            "idle": SessionStatus.IDLE,
            "stopped": SessionStatus.STOPPED,
            "error": SessionStatus.ERROR,
            "starting": SessionStatus.STARTING,
            "stopping": SessionStatus.STOPPING,
        }

        return status_mapping.get(status_str.lower(), SessionStatus.IDLE)

    @staticmethod
    def _parse_activity_type(type_str: str) -> ActivityType:
        """Parse activity type string."""
        type_mapping = {
            "file_created": ActivityType.FILE_CREATED,
            "file_modified": ActivityType.FILE_MODIFIED,
            "file_deleted": ActivityType.FILE_DELETED,
            "command_executed": ActivityType.COMMAND_EXECUTED,
            "test_run": ActivityType.TEST_RUN,
            "build": ActivityType.BUILD,
            "commit": ActivityType.COMMIT,
            "session_start": ActivityType.SESSION_START,
            "session_end": ActivityType.SESSION_END,
            "created": ActivityType.FILE_CREATED,
            "modified": ActivityType.FILE_MODIFIED,
            "deleted": ActivityType.FILE_DELETED,
            "command": ActivityType.COMMAND_EXECUTED,
            "test": ActivityType.TEST_RUN,
            "git": ActivityType.COMMIT,
        }

        return type_mapping.get(type_str.lower(), ActivityType.FILE_MODIFIED)

    @staticmethod
    def _parse_progress_phase(phase_str: str) -> ProgressPhase:
        """Parse progress phase string."""
        phase_mapping = {
            "starting": ProgressPhase.STARTING,
            "analyzing": ProgressPhase.ANALYZING,
            "implementing": ProgressPhase.IMPLEMENTING,
            "testing": ProgressPhase.TESTING,
            "completing": ProgressPhase.COMPLETING,
            "completed": ProgressPhase.COMPLETED,
            "idle": ProgressPhase.IDLE,
            "error": ProgressPhase.ERROR,
        }

        return phase_mapping.get(phase_str.lower(), ProgressPhase.IDLE)


# Global adapter instance
adapter = WidgetDataAdapter()


def adapt_session_data(
    raw_data: dict[str, Any] | list[dict[str, Any]],
) -> SessionData | list[SessionData]:
    """Convenience function for session data adaptation."""
    return adapter.adapt_session_data(raw_data)


def adapt_health_data(raw_data: dict[str, Any]) -> HealthData:
    """Convenience function for health data adaptation."""
    return adapter.adapt_health_data(raw_data)


def adapt_activity_data(raw_data: dict[str, Any]) -> ActivityData:
    """Convenience function for activity data adaptation."""
    return adapter.adapt_activity_data(raw_data)


def adapt_progress_data(raw_data: dict[str, Any]) -> ProgressData:
    """Convenience function for progress data adaptation."""
    return adapter.adapt_progress_data(raw_data)
