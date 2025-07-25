# Copyright notice.

from datetime import UTC, datetime
from typing import Any, cast

from libs.dashboard.renderers.widget_adapter import WidgetDataAdapter
from libs.dashboard.renderers.widget_models import (
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

"""Tests for Widget Models and Data Adapter."""


class TestWidgetModels:
    """Test cases for widget data models."""

    @staticmethod
    def test_session_data_creation() -> None:
        """Test SessionData model creation."""
        now = datetime.now(UTC)
        window = WindowData(id="1", name="test-window", active=True, panes=2)

        session = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            windows=[window],
            panes=2,
            claude_active=True,
        )

        assert session.name == "test-session"
        assert session.id == "session-123"
        assert session.status == SessionStatus.ACTIVE
        assert session.created_at == now
        assert len(session.windows) == 1
        assert session.windows[0].name == "test-window"
        assert session.panes == 2
        assert session.claude_active is True

    @staticmethod
    def test_session_data_to_dict() -> None:
        """Test SessionData to_dict conversion."""
        now = datetime.now(UTC)
        window = WindowData(id="1", name="test-window")

        session = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            windows=[window],
        )

        data = cast(dict[str, Any], session.to_dict())

        assert data["name"] == "test-session"
        assert data["status"] == "active"
        assert data["created_at"] == now.isoformat()
        assert len(cast(list[Any], data["windows"])) == 1
        assert cast(list[dict[str, Any]], data["windows"])[0]["name"] == "test-window"

    @staticmethod
    def test_session_data_from_dict() -> None:
        """Test SessionData from_dict creation."""
        now = datetime.now(UTC)
        data = {
            "name": "test-session",
            "id": "session-123",
            "status": "active",
            "created_at": now.isoformat(),
            "windows": [
                {"id": "1", "name": "test-window", "active": True, "panes": 2},
            ],
            "panes": 2,
            "claude_active": True,
        }

        session = SessionData.from_dict(data)

        assert session.name == "test-session"
        assert session.status == SessionStatus.ACTIVE
        assert session.windows[0].name == "test-window"
        assert session.claude_active is True

    @staticmethod
    def test_health_data_creation() -> None:
        """Test HealthData model creation."""
        now = datetime.now(UTC)
        category = HealthCategoryData(
            category="build",
            score=85,
            level=HealthLevel.GOOD,
            message="Build successful",
        )

        health = HealthData(
            overall_score=85,
            overall_level=HealthLevel.GOOD,
            categories=[category],
            last_updated=now,
            project_path="/test/project",
        )

        assert health.overall_score == 85
        assert health.overall_level == HealthLevel.GOOD
        assert len(health.categories) == 1
        assert health.categories[0].category == "build"
        assert health.project_path == "/test/project"

    @staticmethod
    def test_health_level_from_score() -> None:
        """Test HealthLevel.from_score method."""
        assert HealthLevel.from_score(95) == HealthLevel.EXCELLENT
        assert HealthLevel.from_score(80) == HealthLevel.GOOD
        assert HealthLevel.from_score(60) == HealthLevel.WARNING
        assert HealthLevel.from_score(30) == HealthLevel.CRITICAL
        assert HealthLevel.from_score(-1) == HealthLevel.UNKNOWN

    @staticmethod
    def test_activity_data_creation() -> None:
        """Test ActivityData model creation."""
        now = datetime.now(UTC)
        entry = ActivityEntry(
            timestamp=now,
            activity_type=ActivityType.FILE_CREATED,
            description="Created new file",
        )

        activity = ActivityData(
            entries=[entry],
            total_activities=1,
            active_days=1,
            activity_rate=100.0,
            current_streak=1,
        )

        assert len(activity.entries) == 1
        assert activity.entries[0].activity_type == ActivityType.FILE_CREATED
        assert activity.total_activities == 1
        assert activity.activity_rate == 100.0

    @staticmethod
    def test_progress_data_creation() -> None:
        """Test ProgressData model creation."""
        now = datetime.now(UTC)

        progress = ProgressData(
            phase=ProgressPhase.IMPLEMENTING,
            phase_progress=50.0,
            overall_progress=25.0,
            files_created=5,
            commands_executed=10,
            start_time=now,
        )

        assert progress.phase == ProgressPhase.IMPLEMENTING
        assert progress.phase_progress == 50.0
        assert progress.overall_progress == 25.0
        assert progress.files_created == 5
        assert progress.commands_executed == 10

    @staticmethod
    def test_metric_card_data() -> None:
        """Test MetricCardData model."""
        metric = MetricCardData(
            title="CPU Usage",
            value=75.5,
            suffix="%",
            trend=5.2,
            color="warning",
            icon="cpu",
        )

        assert metric.title == "CPU Usage"
        assert metric.value == 75.5
        assert metric.suffix == "%"
        assert metric.trend == 5.2
        assert metric.color == "warning"

    @staticmethod
    def test_status_indicator_data() -> None:
        """Test StatusIndicatorData model."""
        status = StatusIndicatorData(
            status="running",
            label="Service Active",
            color="success",
            icon="check",
            pulse=True,
        )

        assert status.status == "running"
        assert status.label == "Service Active"
        assert status.color == "success"
        assert status.pulse is True

    @staticmethod
    def test_chart_data_creation() -> None:
        """Test ChartData model creation."""
        now = datetime.now(UTC)
        points = [
            ChartDataPoint(x=now, y=10),
            ChartDataPoint(x="2023-01-02", y=20),
            ChartDataPoint(x=3, y=30),
        ]

        chart = ChartData(
            title="Test Chart",
            chart_type="line",
            data_points=points,
            x_label="Time",
            y_label="Value",
        )

        assert chart.title == "Test Chart"
        assert chart.chart_type == "line"
        assert len(chart.data_points) == 3
        assert chart.data_points[0].y == 10


class TestWidgetDataAdapter:
    """Test cases for WidgetDataAdapter."""

    def setup_method(self) -> None:
        """Setup test adapter."""
        self.adapter = WidgetDataAdapter()

    def test_adapt_session_data_dict(self) -> None:
        """Test adapting session data from dictionary."""
        raw_data = {
            "name": "test-session",
            "id": "session-123",
            "status": "active",
            "created_at": "2023-01-01T10:00:00",
            "windows": [
                {"id": "1", "name": "window1", "active": True, "panes": 2},
            ],
            "claude_active": True,
            "cpu_usage": 15.5,
            "memory_usage": 25.2,
        }

        session = self.adapter.adapt_session_data(raw_data)

        assert isinstance(session, SessionData)
        assert session.name == "test-session"
        assert session.status == SessionStatus.ACTIVE
        assert session.claude_active is True
        assert session.cpu_usage == 15.5
        assert len(session.windows) == 1
        assert session.windows[0].name == "window1"

    def test_adapt_session_data_list(self) -> None:
        """Test adapting multiple session data."""
        raw_data = [
            {"name": "session1", "id": "1", "status": "active"},
            {"name": "session2", "id": "2", "status": "idle"},
        ]

        sessions = self.adapter.adapt_session_data(raw_data)

        assert isinstance(sessions, list)
        assert len(sessions) == 2
        assert sessions[0].name == "session1"
        assert sessions[1].name == "session2"
        assert sessions[0].status == SessionStatus.ACTIVE
        assert sessions[1].status == SessionStatus.IDLE

    def test_adapt_session_data_error_handling(self) -> None:
        """Test session data adaptation error handling."""
        # Test with invalid data
        raw_data = {
            "name": "test-session",
            "id": None,  # This might cause issues
            "status": "invalid_status",  # Invalid status
            "created_at": "invalid_date",  # Invalid date
        }

        session = self.adapter.adapt_session_data(raw_data)

        assert isinstance(session, SessionData)
        assert session.name == "test-session"
        # Should handle errors gracefully
        assert session.status in {SessionStatus.IDLE, SessionStatus.ERROR}

    def test_adapt_health_data(self) -> None:
        """Test adapting health data."""
        raw_data = {
            "overall_score": 85,
            "categories": {
                "build": {
                    "score": 90,
                    "message": "Build passing",
                    "details": {"tests": "all_pass"},
                },
                "security": {
                    "score": 80,
                    "message": "Minor vulnerabilities",
                },
            },
            "last_updated": "2023-01-01T10:00:00",
            "project_path": "/test/project",
        }

        health = self.adapter.adapt_health_data(raw_data)

        assert isinstance(health, HealthData)
        assert health.overall_score == 85
        assert health.overall_level == HealthLevel.GOOD
        assert len(health.categories) == 2
        assert health.categories[0].category == "build"
        assert health.categories[0].score == 90
        assert health.project_path == "/test/project"

    def test_adapt_activity_data(self) -> None:
        """Test adapting activity data."""
        raw_data = {
            "activities": [
                {
                    "timestamp": "2023-01-01T10:00:00",
                    "type": "file_created",
                    "description": "Created new file",
                    "details": {"file": "test.py"},
                },
                {
                    "timestamp": "2023-01-01T11:00:00",
                    "type": "commit",
                    "description": "Initial commit",
                },
            ],
            "total_activities": 2,
            "active_days": 1,
            "current_streak": 1,
        }

        activity = self.adapter.adapt_activity_data(raw_data)

        assert isinstance(activity, ActivityData)
        assert len(activity.entries) == 2
        assert activity.entries[0].activity_type == ActivityType.FILE_CREATED
        assert activity.entries[1].activity_type == ActivityType.COMMIT
        assert activity.total_activities == 2
        assert activity.active_days == 1

    def test_adapt_progress_data(self) -> None:
        """Test adapting progress data."""
        raw_data = {
            "phase": "implementing",
            "phase_progress": 75.0,
            "overall_progress": 50.0,
            "files_created": 5,
            "files_modified": 10,
            "commands_executed": 20,
            "commands_succeeded": 18,
            "commands_failed": 2,
            "start_time": "2023-01-01T09:00:00",
            "active_duration": 3600.0,
            "todos_identified": 10,
            "todos_completed": 7,
        }

        progress = self.adapter.adapt_progress_data(raw_data)

        assert isinstance(progress, ProgressData)
        assert progress.phase == ProgressPhase.IMPLEMENTING
        assert progress.phase_progress == 75.0
        assert progress.overall_progress == 50.0
        assert progress.files_created == 5
        assert progress.files_modified == 10
        assert progress.commands_executed == 20
        assert progress.commands_succeeded == 18
        assert progress.commands_failed == 2
        assert progress.active_duration == 3600.0
        assert progress.todos_identified == 10
        assert progress.todos_completed == 7

    def test_adapt_metric_card_data(self) -> None:
        """Test adapting metric card data."""
        raw_data = {
            "title": "Response Time",
            "value": 150,
            "suffix": "ms",
            "trend": -5.2,
            "color": "success",
            "icon": "timer",
        }

        metric = self.adapter.adapt_metric_card_data(raw_data)

        assert isinstance(metric, MetricCardData)
        assert metric.title == "Response Time"
        assert metric.value == 150
        assert metric.suffix == "ms"
        assert metric.trend == -5.2
        assert metric.color == "success"

    def test_adapt_chart_data(self) -> None:
        """Test adapting chart data."""
        raw_data = {
            "title": "CPU Usage Over Time",
            "type": "line",
            "data": [
                {"x": "2023-01-01T10:00:00", "y": 25},
                {"x": "2023-01-01T11:00:00", "y": 30},
                {"x": "2023-01-01T12:00:00", "y": 28},
            ],
            "x_label": "Time",
            "y_label": "CPU %",
            "colors": ["#3B82F6"],
        }

        chart = self.adapter.adapt_chart_data(raw_data)

        assert isinstance(chart, ChartData)
        assert chart.title == "CPU Usage Over Time"
        assert chart.chart_type == "line"
        assert len(chart.data_points) == 3
        assert chart.data_points[0].y == 25
        assert chart.x_label == "Time"
        assert chart.y_label == "CPU %"

    def test_parse_timestamp_formats(self) -> None:
        """Test timestamp parsing with various formats."""
        adapter = self.adapter

        # Test datetime object
        now = datetime.now(UTC)
        assert adapter._parse_timestamp(now) == now  # noqa: SLF001

        # Test None
        assert adapter._parse_timestamp(None) is None  # noqa: SLF001

        # Test integer timestamp
        timestamp = 1672574400  # 2023-01-01 10:00:00 UTC
        result = adapter._parse_timestamp(timestamp)  # noqa: SLF001
        assert isinstance(result, datetime)

        # Test ISO format string
        iso_string = "2023-01-01T10:00:00"
        result = adapter._parse_timestamp(iso_string)  # noqa: SLF001
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 1

        # Test ISO format with timezone
        iso_string_tz = "2023-01-01T10:00:00Z"
        result = adapter._parse_timestamp(iso_string_tz)  # noqa: SLF001
        assert isinstance(result, datetime)

        # Test date only
        date_string = "2023-01-01"
        result = adapter._parse_timestamp(date_string)  # noqa: SLF001
        assert isinstance(result, datetime)

        # Test invalid string
        assert adapter._parse_timestamp("invalid") is None  # noqa: SLF001

    def test_parse_enums(self) -> None:
        """Test enum parsing methods."""
        adapter = self.adapter

        # Test session status parsing
        assert (
            adapter._parse_session_status("active") == SessionStatus.ACTIVE
        )  # noqa: SLF001
        assert (
            adapter._parse_session_status("RUNNING") == SessionStatus.ACTIVE
        )  # noqa: SLF001
        assert (
            adapter._parse_session_status("idle") == SessionStatus.IDLE
        )  # noqa: SLF001
        assert (
            adapter._parse_session_status("invalid") == SessionStatus.IDLE
        )  # noqa: SLF001

        # Test activity type parsing
        assert (
            adapter._parse_activity_type("file_created") == ActivityType.FILE_CREATED
        )  # noqa: SLF001
        assert (
            adapter._parse_activity_type("CREATED") == ActivityType.FILE_CREATED
        )  # noqa: SLF001
        assert (
            adapter._parse_activity_type("commit") == ActivityType.COMMIT
        )  # noqa: SLF001
        assert (
            adapter._parse_activity_type("invalid") == ActivityType.FILE_MODIFIED
        )  # noqa: SLF001

        # Test progress phase parsing
        assert (
            adapter._parse_progress_phase("implementing") == ProgressPhase.IMPLEMENTING
        )  # noqa: SLF001
        assert (
            adapter._parse_progress_phase("TESTING") == ProgressPhase.TESTING
        )  # noqa: SLF001
        assert (
            adapter._parse_progress_phase("invalid") == ProgressPhase.IDLE
        )  # noqa: SLF001


class TestModelSerialization:
    """Test model serialization and deserialization."""

    @staticmethod
    def test_session_data_roundtrip() -> None:
        """Test SessionData serialization roundtrip."""
        now = datetime.now(UTC)
        window = WindowData(id="1", name="test-window", active=True)

        original = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            windows=[window],
            claude_active=True,
        )

        # Convert to dict and back
        data_dict = original.to_dict()
        restored = SessionData.from_dict(data_dict)

        assert restored.name == original.name
        assert restored.id == original.id
        assert restored.status == original.status
        assert restored.claude_active == original.claude_active
        assert len(restored.windows) == len(original.windows)
        assert restored.windows[0].name == original.windows[0].name

    @staticmethod
    def test_health_data_roundtrip() -> None:
        """Test HealthData serialization roundtrip."""
        now = datetime.now(UTC)
        category = HealthCategoryData(
            category="build",
            score=85,
            level=HealthLevel.GOOD,
            last_checked=now,
        )

        original = HealthData(
            overall_score=85,
            overall_level=HealthLevel.GOOD,
            categories=[category],
            last_updated=now,
        )

        # Convert to dict and back
        data_dict = original.to_dict()
        restored = HealthData.from_dict(data_dict)

        assert restored.overall_score == original.overall_score
        assert restored.overall_level == original.overall_level
        assert len(restored.categories) == len(original.categories)
        assert restored.categories[0].category == original.categories[0].category
        assert restored.categories[0].score == original.categories[0].score

    @staticmethod
    def test_activity_data_roundtrip() -> None:
        """Test ActivityData serialization roundtrip."""
        now = datetime.now(UTC)
        entry = ActivityEntry(
            timestamp=now,
            activity_type=ActivityType.FILE_CREATED,
            description="Test entry",
        )

        original = ActivityData(
            entries=[entry],
            total_activities=1,
            active_days=1,
        )

        # Convert to dict and back
        data_dict = original.to_dict()
        restored = ActivityData.from_dict(data_dict)

        assert restored.total_activities == original.total_activities
        assert restored.active_days == original.active_days
        assert len(restored.entries) == len(original.entries)
        assert restored.entries[0].activity_type == original.entries[0].activity_type
        assert restored.entries[0].description == original.entries[0].description
