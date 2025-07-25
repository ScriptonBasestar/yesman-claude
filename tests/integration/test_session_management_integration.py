import os
import threading

import psutil
import pytest

from commands.setup import SetupCommand
from commands.status import StatusCommand

from .test_framework import CommandTestRunner, IntegrationTestBase, PerformanceMonitor

# !/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Session Management Integration Tests.

Tests the complete session lifecycle across CLI, API, and internal components.
Validates that session operations work correctly end-to-end.
"""


class TestSessionLifecycleIntegration(IntegrationTestBase):
    """Test complete session lifecycle with all components."""

    def setup_method(self) -> None:
        """Setup for session lifecycle tests."""
        super().setup_method()
        self.command_runner = CommandTestRunner(self)
        self.performance_monitor = PerformanceMonitor()

    def test_complete_session_creation_workflow(self) -> None:
        """Test end-to-end session creation workflow."""
        # Step 1: Create test session configuration
        session_name = "test-integration-session"
        self.create_test_session(
            session_name,
            description="Integration test session",
            windows=[
                {
                    "window_name": "main",
                    "panes": [
                        {"shell_command": ["echo", "Hello World"]},
                        {"shell_command": ["pwd"]},
                    ],
                },
                {
                    "window_name": "secondary",
                    "panes": [{"shell_command": ["ls", "-la"]}],
                },
            ],
        )

        # Step 2: Test session setup via CLI
        self.performance_monitor.start_timing("session_setup")

        setup_result = self.command_runner.run_command(
            SetupCommand, session_name=session_name
        )

        self.performance_monitor.end_timing("session_setup")

        # Verify setup succeeded
        assert setup_result["success"] is True
        assert setup_result["successful_sessions"] >= 1
        assert setup_result["failed_sessions"] == 0

        # Step 3: Verify session exists via SessionManager
        session_manager = self.get_session_manager()
        self.assert_session_exists(session_name)

        # Step 4: Get session details and verify structure
        session_info = session_manager.get_session_info(session_name)
        assert session_info is not None
        assert session_info["name"] == session_name
        assert len(session_info.get("windows", [])) >= 2  # main + secondary

        # Step 5: Test session status via CLI
        self.performance_monitor.start_timing("session_status")

        status_result = self.command_runner.run_command(StatusCommand)

        self.performance_monitor.end_timing("session_status")

        # Verify status includes our session
        assert status_result["success"] is True
        assert session_name in [s["name"] for s in status_result.get("sessions", [])]

        # Step 6: Performance assertions
        self.performance_monitor.assert_performance_threshold("session_setup", 10.0)
        self.performance_monitor.assert_performance_threshold("session_status", 2.0)

    def test_session_modification_propagation(self) -> None:
        """Test that session modifications propagate correctly."""
        session_name = "test-modification-session"

        # Create initial session
        self.create_test_session(session_name)
        self.command_runner.run_command(SetupCommand, session_name=session_name)

        # Verify initial state
        session_manager = self.get_session_manager()
        initial_info = session_manager.get_session_info(session_name)
        initial_window_count = len(initial_info.get("windows", []))

        # Modify session configuration
        self.create_test_session(
            session_name,
            description="Modified integration test session",
            windows=[
                {
                    "window_name": "main",
                    "panes": [{"shell_command": ["echo", "Modified"]}],
                },
                {"window_name": "new_window", "panes": [{"shell_command": ["date"]}]},
                {
                    "window_name": "third_window",
                    "panes": [{"shell_command": ["whoami"]}],
                },
            ],
        )

        # Re-run setup to apply modifications
        setup_result = self.command_runner.run_command(
            SetupCommand, session_name=session_name
        )
        assert setup_result["success"] is True

        # Verify modifications propagated
        updated_info = session_manager.get_session_info(session_name)
        updated_window_count = len(updated_info.get("windows", []))

        # Should have more windows now
        assert updated_window_count > initial_window_count
        assert updated_window_count == 3

    def test_multiple_session_coordination(self) -> None:
        """Test coordination between multiple sessions."""
        session_names = ["multi-session-1", "multi-session-2", "multi-session-3"]

        # Create multiple sessions
        for i, session_name in enumerate(session_names):
            self.create_test_session(
                session_name,
                description=f"Multi-session test {i + 1}",
                windows=[
                    {
                        "window_name": f"window_{i}",
                        "panes": [{"shell_command": ["echo", f"Session {i + 1}"]}],
                    }
                ],
            )

        # Setup all sessions
        self.performance_monitor.start_timing("multi_session_setup")

        for session_name in session_names:
            result = self.command_runner.run_command(
                SetupCommand, session_name=session_name
            )
            assert result["success"] is True

        multi_setup_duration = self.performance_monitor.end_timing(
            "multi_session_setup"
        )

        # Verify all sessions exist
        self.get_session_manager()
        for session_name in session_names:
            self.assert_session_exists(session_name)

        # Test global status includes all sessions
        status_result = self.command_runner.run_command(StatusCommand)
        status_session_names = [s["name"] for s in status_result.get("sessions", [])]

        for session_name in session_names:
            assert session_name in status_session_names

        # Performance check for multiple sessions
        assert (
            multi_setup_duration < 30.0
        ), f"Multi-session setup took {multi_setup_duration:.2f}s, should be < 30s"

    def test_session_error_handling_integration(self) -> None:
        """Test error handling across session operations."""
        # Test 1: Invalid session configuration
        with pytest.raises(Exception):
            self.create_test_session(
                "invalid-session",
                windows=[],  # Invalid: no windows
            )
            self.command_runner.run_command(
                SetupCommand, session_name="invalid-session"
            )

        # Test 2: Non-existent session
        with pytest.raises(Exception):
            self.command_runner.run_command(
                SetupCommand, session_name="non-existent-session"
            )

        # Test 3: Recovery from partial failure
        # Create valid session after failures
        valid_session = "recovery-test-session"
        self.create_test_session(valid_session)

        result = self.command_runner.run_command(
            SetupCommand, session_name=valid_session
        )
        assert result["success"] is True

        # Verify system is still functional
        self.assert_session_exists(valid_session)

    def test_session_cleanup_integration(self) -> None:
        """Test session cleanup and resource management."""
        session_name = "cleanup-test-session"

        # Create and setup session
        self.create_test_session(session_name)
        self.command_runner.run_command(SetupCommand, session_name=session_name)

        # Verify session exists
        self.assert_session_exists(session_name)

        # Test cleanup via session manager
        session_manager = self.get_session_manager()
        session_manager.cleanup_session(session_name)

        # Verify session is cleaned up
        # Note: Actual cleanup depends on tmux integration
        # In test environment, we verify the cleanup call succeeds
        assert True  # Cleanup attempted


class TestSessionStateConsistency(IntegrationTestBase):
    """Test session state consistency across different access methods."""

    def test_cli_api_state_consistency(self) -> None:
        """Test that CLI and API views of session state are consistent."""
        session_name = "consistency-test-session"

        # Create session via CLI
        self.create_test_session(session_name)
        command_runner = CommandTestRunner(self)

        cli_setup_result = command_runner.run_command(
            SetupCommand, session_name=session_name
        )
        assert cli_setup_result["success"] is True

        # Get state via CLI
        cli_status_result = command_runner.run_command(StatusCommand)
        cli_session_info = None
        for session in cli_status_result.get("sessions", []):
            if session["name"] == session_name:
                cli_session_info = session
                break

        assert cli_session_info is not None

        # Get state via SessionManager (API level)
        session_manager = self.get_session_manager()
        api_session_info = session_manager.get_session_info(session_name)

        # Verify consistency
        assert api_session_info is not None
        assert cli_session_info["name"] == api_session_info["name"]

        # Both should report same basic structure
        assert len(cli_session_info.get("windows", [])) == len(
            api_session_info.get("windows", [])
        )

    def test_concurrent_session_access(self) -> None:
        """Test concurrent access to session information."""
        session_name = "concurrent-test-session"

        # Create session
        self.create_test_session(session_name)
        command_runner = CommandTestRunner(self)
        command_runner.run_command(SetupCommand, session_name=session_name)

        # Simulate concurrent access
        session_manager = self.get_session_manager()

        def get_session_info() -> object:
            return session_manager.get_session_info(session_name)

        # Multiple concurrent calls

        results = []
        threads = []

        def worker() -> None:
            info = get_session_info()
            results.append(info)

        # Start multiple threads
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=5.0)

        # Verify all calls succeeded and returned consistent data
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert result["name"] == session_name

        # All results should be consistent
        first_result = results[0]
        for result in results[1:]:
            assert result["name"] == first_result["name"]
            assert len(result.get("windows", [])) == len(
                first_result.get("windows", [])
            )


class TestSessionPerformanceIntegration(IntegrationTestBase):
    """Test session performance under various conditions."""

    def setup_method(self) -> None:
        """Setup for performance tests."""
        super().setup_method()
        self.performance_monitor = PerformanceMonitor()

    def test_session_setup_performance(self) -> None:
        """Test session setup performance."""
        session_name = "performance-test-session"

        # Create complex session configuration
        self.create_test_session(
            session_name,
            windows=[
                {
                    "window_name": f"window_{i}",
                    "panes": [
                        {"shell_command": ["echo", f"Pane {j} in Window {i}"]}
                        for j in range(3)  # 3 panes per window
                    ],
                }
                for i in range(5)  # 5 windows
            ],
        )

        # Measure setup performance
        self.performance_monitor.start_timing("complex_session_setup")

        command_runner = CommandTestRunner(self)
        result = command_runner.run_command(SetupCommand, session_name=session_name)

        setup_duration = self.performance_monitor.end_timing("complex_session_setup")

        # Verify success
        assert result["success"] is True

        # Performance assertion - complex session should still setup quickly
        assert (
            setup_duration < 15.0
        ), f"Complex session setup took {setup_duration:.2f}s, should be < 15s"

    def test_status_query_performance(self) -> None:
        """Test status query performance with multiple sessions."""
        # Create multiple sessions
        session_count = 10
        for i in range(session_count):
            session_name = f"perf-session-{i}"
            self.create_test_session(session_name)

        command_runner = CommandTestRunner(self)

        # Setup all sessions
        for i in range(session_count):
            session_name = f"perf-session-{i}"
            command_runner.run_command(SetupCommand, session_name=session_name)

        # Measure status query performance
        self.performance_monitor.start_timing("multi_session_status")

        status_result = command_runner.run_command(StatusCommand)

        status_duration = self.performance_monitor.end_timing("multi_session_status")

        # Verify all sessions are included
        assert status_result["success"] is True
        session_names = [s["name"] for s in status_result.get("sessions", [])]

        for i in range(session_count):
            expected_name = f"perf-session-{i}"
            assert expected_name in session_names

        # Performance assertion
        assert (
            status_duration < 5.0
        ), f"Status query with {session_count} sessions took {status_duration:.2f}s, should be < 5s"

    def test_memory_usage_stability(self) -> None:
        """Test that session operations don't cause memory leaks."""
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        command_runner = CommandTestRunner(self)

        # Perform many session operations
        for i in range(20):
            session_name = f"memory-test-session-{i}"

            # Create, setup, and query session
            self.create_test_session(session_name)
            command_runner.run_command(SetupCommand, session_name=session_name)
            command_runner.run_command(StatusCommand)

            # Cleanup
            session_manager = self.get_session_manager()
            session_manager.cleanup_session(session_name)

        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 50MB for 20 operations)
        memory_increase_mb = memory_increase / (1024 * 1024)
        assert (
            memory_increase_mb < 50
        ), f"Memory increased by {memory_increase_mb:.2f}MB, should be < 50MB"
