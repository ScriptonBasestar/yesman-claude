#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Dashboard Integration Tests.

Tests the real-time dashboard integration with CLI, API, and automation systems.
Validates that dashboard updates reflect system state accurately across components.
"""

import asyncio
import time
from typing import object, Never
from unittest.mock import AsyncMock, Mock

import pytest

from commands.automate import AutomateMonitorCommand
from commands.setup import SetupCommand
from commands.status import StatusCommand

from .test_framework import (
    AsyncIntegrationTestBase,
    CommandTestRunner,
    MockClaudeEnvironment,
    PerformanceMonitor,
)


class TestDashboardSystemIntegration(AsyncIntegrationTestBase):
    """Test complete dashboard system integration."""

    def setup_method(self) -> None:
        """Setup for dashboard integration tests."""
        super().setup_method()
        self.command_runner = CommandTestRunner(self)
        self.performance_monitor = PerformanceMonitor()
        self.mock_claude = MockClaudeEnvironment(self.test_dir)

        # Mock dashboard components for testing
        self.dashboard_server = None
        self.dashboard_client = None

    async def test_dashboard_session_state_sync(self) -> None:
        """Test that dashboard reflects session state changes in real-time."""
        # Create test sessions
        session_names = ["dash-session-1", "dash-session-2"]
        for session_name in session_names:
            self.create_test_session(session_name)

        # Start mock dashboard server
        dashboard = await self._start_mock_dashboard()  # noqa: SLF001

        # Setup first session via CLI
        self.performance_monitor.start_timing("session_setup_dashboard")

        setup_result = self.command_runner.run_command(SetupCommand, session_name=session_names[0])

        setup_duration = self.performance_monitor.end_timing("session_setup_dashboard")

        assert setup_result["success"] is True

        # Wait for dashboard update
        await asyncio.sleep(0.5)

        # Verify dashboard shows session
        dashboard_state = await dashboard.get_current_state()
        dashboard_sessions = dashboard_state.get("sessions", [])
        session_names_in_dashboard = [s["name"] for s in dashboard_sessions]

        assert session_names[0] in session_names_in_dashboard

        # Setup second session
        setup_result_2 = self.command_runner.run_command(SetupCommand, session_name=session_names[1])

        assert setup_result_2["success"] is True

        # Wait for dashboard update
        await asyncio.sleep(0.5)

        # Verify dashboard shows both sessions
        updated_state = await dashboard.get_current_state()
        updated_sessions = updated_state.get("sessions", [])
        updated_session_names = [s["name"] for s in updated_sessions]

        assert session_names[0] in updated_session_names
        assert session_names[1] in updated_session_names

        # Performance check
        assert setup_duration < 5.0, f"Session setup with dashboard took {setup_duration:.2f}s, should be < 5s"

        await self._stop_mock_dashboard(dashboard)  # noqa: SLF001

    async def test_dashboard_automation_monitoring(self) -> None:
        """Test dashboard integration with automation monitoring."""
        # Create project for automation monitoring
        project_dir = self.test_dir / "dashboard_automation_project"
        project_dir.mkdir()

        # Setup project files
        (project_dir / "app.py").write_text("print('Dashboard test')")
        (project_dir / "requirements.txt").write_text("flask==2.0.0")

        dashboard = await self._start_mock_dashboard()  # noqa: SLF001

        # Start automation monitoring
        self.performance_monitor.start_timing("automation_monitoring_dashboard")

        monitor_result = self.command_runner.run_command(
            AutomateMonitorCommand,
            project_path=str(project_dir),
            duration=2,
            dashboard_integration=True,
        )

        monitoring_duration = self.performance_monitor.end_timing("automation_monitoring_dashboard")

        assert monitor_result["success"] is True

        # Wait for dashboard updates
        await asyncio.sleep(1.0)

        # Verify dashboard shows automation data
        dashboard_state = await dashboard.get_current_state()
        automation_data = dashboard_state.get("automation", {})

        assert "monitored_projects" in automation_data
        assert len(automation_data["monitored_projects"]) > 0

        monitored_project = automation_data["monitored_projects"][0]
        assert monitored_project["path"] == str(project_dir)

        # Performance check
        assert monitoring_duration < 8.0, f"Automation monitoring with dashboard took {monitoring_duration:.2f}s, should be < 8s"

        await self._stop_mock_dashboard(dashboard)  # noqa: SLF001

    async def test_dashboard_performance_metrics(self) -> None:
        """Test dashboard performance metrics collection and display."""
        dashboard = await self._start_mock_dashboard()  # noqa: SLF001

        # Perform various operations to generate metrics
        operations = [
            (
                "session_creation",
                lambda: self.command_runner.run_command(SetupCommand, session_name="perf-session"),
            ),
            ("status_query", lambda: self.command_runner.run_command(StatusCommand)),
        ]

        # Create test session first
        self.create_test_session("perf-session")

        for operation_name, operation_func in operations:
            self.performance_monitor.start_timing(operation_name)
            result = operation_func()
            operation_duration = self.performance_monitor.end_timing(operation_name)

            assert result["success"] is True

            # Wait for dashboard to collect metrics
            await asyncio.sleep(0.3)

            # Verify dashboard has performance data
            dashboard_state = await dashboard.get_current_state()
            metrics = dashboard_state.get("performance_metrics", {})

            assert operation_name in metrics
            assert metrics[operation_name]["duration"] > 0
            assert metrics[operation_name]["duration"] == pytest.approx(operation_duration, rel=0.1)

        await self._stop_mock_dashboard(dashboard)  # noqa: SLF001

    async def test_dashboard_real_time_updates(self) -> None:
        """Test dashboard real-time update mechanism."""
        dashboard = await self._start_mock_dashboard()  # noqa: SLF001

        # Track update events
        update_events = []

        async def mock_update_handler(event_type: str, data: object) -> None:
            update_events.append({"type": event_type, "data": data, "timestamp": time.time()})

        # Register update handler
        dashboard.register_update_handler(mock_update_handler)

        # Perform operations that should trigger updates
        self.create_test_session("realtime-session")

        setup_result = self.command_runner.run_command(SetupCommand, session_name="realtime-session")

        assert setup_result["success"] is True

        # Wait for real-time updates
        await asyncio.sleep(1.0)

        # Verify updates were received
        assert len(update_events) > 0

        # Should have session-related updates
        session_updates = [e for e in update_events if "session" in e["type"]]
        assert len(session_updates) > 0

        # Updates should be recent
        latest_update = max(update_events, key=lambda e: e["timestamp"])
        assert time.time() - latest_update["timestamp"] < 5.0

        await self._stop_mock_dashboard(dashboard)  # noqa: SLF001

    async def test_dashboard_websocket_performance(self) -> None:
        """Test dashboard WebSocket performance under load."""
        dashboard = await self._start_mock_dashboard()  # noqa: SLF001

        # Simulate multiple concurrent clients
        client_count = 5
        clients = []

        self.performance_monitor.start_timing("websocket_setup")

        # Create mock WebSocket clients
        for i in range(client_count):
            client = await self._create_mock_websocket_client(dashboard, f"client-{i}")  # noqa: SLF001
            clients.append(client)

        setup_duration = self.performance_monitor.end_timing("websocket_setup")

        # Generate events for real-time updates
        self.performance_monitor.start_timing("bulk_updates")

        for i in range(10):
            session_name = f"bulk-session-{i}"
            self.create_test_session(session_name)

            result = self.command_runner.run_command(SetupCommand, session_name=session_name)
            assert result["success"] is True

            # Small delay to allow processing
            await asyncio.sleep(0.1)

        bulk_duration = self.performance_monitor.end_timing("bulk_updates")

        # Wait for all updates to propagate
        await asyncio.sleep(2.0)

        # Verify all clients received updates
        for client in clients:
            received_updates = await client.get_received_updates()
            assert len(received_updates) > 5  # Should have received multiple updates

        # Performance assertions
        assert setup_duration < 3.0, f"WebSocket setup took {setup_duration:.2f}s, should be < 3s"
        assert bulk_duration < 15.0, f"Bulk updates took {bulk_duration:.2f}s, should be < 15s"

        # Cleanup clients
        for client in clients:
            await client.disconnect()

        await self._stop_mock_dashboard(dashboard)  # noqa: SLF001

    @staticmethod
    async def _start_mock_dashboard():
        """Start mock dashboard for testing."""
        # Create mock dashboard that simulates real behavior
        dashboard = Mock()
        dashboard.get_current_state = AsyncMock(
            return_value={
                "sessions": [],
                "automation": {"monitored_projects": []},
                "performance_metrics": {},
            }
        )
        dashboard.register_update_handler = Mock()

        # Track state changes
        dashboard._state = {  # noqa: SLF001
            "sessions": [],
            "automation": {"monitored_projects": []},
            "performance_metrics": {},
        }

        # Add helper methods for testing
        async def add_session(session_data: dict[str, object]) -> None:
            dashboard._state["sessions"].append(session_data)  # noqa: SLF001

        async def add_automation_project(project_data: dict[str, object]) -> None:
            dashboard._state["automation"]["monitored_projects"].append(project_data)  # noqa: SLF001

        async def add_performance_metric(metric_name: str, metric_data: object) -> None:
            dashboard._state["performance_metrics"][metric_name] = metric_data  # noqa: SLF001

        dashboard.add_session = add_session
        dashboard.add_automation_project = add_automation_project
        dashboard.add_performance_metric = add_performance_metric

        # Update get_current_state to return actual state
        async def get_state():
            return dashboard._state.copy()  # noqa: SLF001

        dashboard.get_current_state = get_state

        return dashboard

    @staticmethod
    async def _stop_mock_dashboard(dashboard: object) -> None:
        """Stop mock dashboard."""
        # Cleanup mock dashboard
        if hasattr(dashboard, "cleanup"):
            await dashboard.cleanup()

    @staticmethod
    async def _create_mock_websocket_client(dashboard: object, client_id: str) -> Mock:  # noqa: ARG002
        """Create mock WebSocket client for testing."""
        client = Mock()
        client.client_id = client_id
        client.received_updates = []

        async def get_updates():
            return client.received_updates.copy()

        async def disconnect() -> None:
            pass

        client.get_received_updates = get_updates
        client.disconnect = disconnect

        return client


class TestDashboardDataConsistency(AsyncIntegrationTestBase):
    """Test dashboard data consistency across different sources."""

    async def test_cli_dashboard_data_consistency(self) -> None:
        """Test that CLI and dashboard show consistent data."""
        # Create test session
        session_name = "consistency-test-session"
        self.create_test_session(session_name)

        dashboard = await self._start_mock_dashboard()  # noqa: SLF001

        # Setup session via CLI
        cli_result = self.command_runner.run_command(SetupCommand, session_name=session_name)
        assert cli_result["success"] is True

        # Get CLI view of sessions
        status_result = self.command_runner.run_command(StatusCommand)
        assert status_result["success"] is True

        cli_sessions = status_result.get("sessions", [])
        cli_session_names = [s["name"] for s in cli_sessions]

        # Wait for dashboard sync
        await asyncio.sleep(0.5)

        # Get dashboard view of sessions
        dashboard_state = await dashboard.get_current_state()
        dashboard_sessions = dashboard_state.get("sessions", [])
        dashboard_session_names = [s["name"] for s in dashboard_sessions]

        # Data should be consistent
        assert session_name in cli_session_names
        assert session_name in dashboard_session_names

        # Session details should match
        cli_session = next(s for s in cli_sessions if s["name"] == session_name)
        dashboard_session = next(s for s in dashboard_sessions if s["name"] == session_name)

        # Key attributes should match
        assert cli_session["name"] == dashboard_session["name"]

        await self._stop_mock_dashboard(dashboard)  # noqa: SLF001

    async def test_automation_dashboard_data_sync(self) -> None:
        """Test automation data synchronization with dashboard."""
        project_dir = self.test_dir / "dashboard_sync_project"
        project_dir.mkdir()

        (project_dir / "main.py").write_text("print('Sync test')")

        dashboard = await self._start_mock_dashboard()  # noqa: SLF001

        # Start automation monitoring
        monitor_result = self.command_runner.run_command(AutomateMonitorCommand, project_path=str(project_dir), duration=1)

        assert monitor_result["success"] is True

        # Wait for dashboard update
        await asyncio.sleep(1.0)

        # Verify dashboard has automation data
        dashboard_state = await dashboard.get_current_state()
        automation_data = dashboard_state.get("automation", {})

        assert "monitored_projects" in automation_data
        monitored_projects = automation_data["monitored_projects"]

        project_paths = [p.get("path") for p in monitored_projects]
        assert str(project_dir) in project_paths

        await self._stop_mock_dashboard(dashboard)  # noqa: SLF001

    @staticmethod
    async def _start_mock_dashboard():
        """Start mock dashboard - reuse from previous class."""
        dashboard = Mock()
        dashboard._state = {  # noqa: SLF001
            "sessions": [],
            "automation": {"monitored_projects": []},
            "performance_metrics": {},
        }

        async def get_state():
            return dashboard._state.copy()  # noqa: SLF001

        dashboard.get_current_state = get_state
        return dashboard

    @staticmethod
    async def _stop_mock_dashboard(dashboard: object) -> None:
        """Stop mock dashboard - reuse from previous class."""


class TestDashboardErrorHandling(AsyncIntegrationTestBase):
    """Test dashboard error handling and recovery."""

    async def test_dashboard_connection_recovery(self) -> None:
        """Test dashboard recovery from connection failures."""
        dashboard = await self._start_mock_dashboard()  # noqa: SLF001

        # Simulate connection failure
        original_get_state = dashboard.get_current_state

        async def failing_get_state() -> Never:
            msg = "Dashboard connection failed"
            raise ConnectionError(msg)

        dashboard.get_current_state = failing_get_state

        # Operations should continue despite dashboard failure
        session_name = "recovery-test-session"
        self.create_test_session(session_name)

        result = self.command_runner.run_command(SetupCommand, session_name=session_name)
        assert result["success"] is True  # Should succeed despite dashboard failure

        # Restore connection
        dashboard.get_current_state = original_get_state

        # Dashboard should recover and show data
        await asyncio.sleep(0.5)

        dashboard_state = await dashboard.get_current_state()
        assert dashboard_state is not None

        await self._stop_mock_dashboard(dashboard)  # noqa: SLF001

    async def test_dashboard_graceful_degradation(self) -> None:
        """Test dashboard graceful degradation under high load."""
        dashboard = await self._start_mock_dashboard()  # noqa: SLF001

        # Simulate high load scenario
        load_operations = 20

        self.performance_monitor.start_timing("high_load_scenario")

        for i in range(load_operations):
            session_name = f"load-session-{i}"
            self.create_test_session(session_name)

            result = self.command_runner.run_command(SetupCommand, session_name=session_name)
            assert result["success"] is True

            # Minimal delay to create load
            await asyncio.sleep(0.05)

        load_duration = self.performance_monitor.end_timing("high_load_scenario")

        # System should remain responsive
        assert load_duration < 30.0, f"High load scenario took {load_duration:.2f}s, should be < 30s"

        # Dashboard should still be functional
        dashboard_state = await dashboard.get_current_state()
        assert dashboard_state is not None

        await self._stop_mock_dashboard(dashboard)  # noqa: SLF001

    @staticmethod
    async def _start_mock_dashboard():
        """Start mock dashboard - reuse pattern."""
        dashboard = Mock()
        dashboard._state = {  # noqa: SLF001
            "sessions": [],
            "automation": {"monitored_projects": []},
            "performance_metrics": {},
        }

        async def get_state():
            return dashboard._state.copy()  # noqa: SLF001

        dashboard.get_current_state = get_state
        return dashboard

    @staticmethod
    async def _stop_mock_dashboard(dashboard: object) -> None:
        """Stop mock dashboard."""
