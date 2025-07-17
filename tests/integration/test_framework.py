#!/usr/bin/env python3
"""
Integration Test Framework for Yesman-Claude

Provides base classes, utilities, and fixtures for comprehensive integration testing
across CLI, API, dashboard, and multi-agent components.
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest
import yaml

from libs.core.session_manager import SessionManager
from libs.yesman_config import YesmanConfig


class IntegrationTestBase:
    """Base class for integration tests with common setup and utilities"""

    def setup_method(self):
        """Setup for each test method"""
        # Create temporary test environment
        self.test_dir = Path(tempfile.mkdtemp(prefix="yesman_test_"))
        self.test_config_dir = self.test_dir / ".scripton" / "yesman"
        self.test_config_dir.mkdir(parents=True, exist_ok=True)

        # Create test configuration
        self.test_config = self._create_test_config()
        self._write_test_config()

        # Initialize test components
        self.session_manager = None
        self.config = None

        # Track created resources for cleanup
        self.created_sessions = []
        self.created_processes = []

    def teardown_method(self):
        """Cleanup after each test method"""
        # Stop any created processes
        for process in self.created_processes:
            if hasattr(process, "terminate"):
                process.terminate()

        # Cleanup sessions
        if self.session_manager:
            for session_name in self.created_sessions:
                try:
                    self.session_manager.cleanup_session(session_name)
                except Exception:
                    pass  # Best effort cleanup

        # Remove test directory
        import shutil

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_test_config(self) -> dict[str, Any]:
        """Create test configuration"""
        return {
            "mode": "test",
            "root_dir": str(self.test_dir),
            "logging": {"level": "DEBUG", "log_path": str(self.test_dir / "logs"), "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
            "session": {"sessions_dir": "sessions", "templates_dir": "templates", "projects_file": "projects.yaml", "default_shell": "/bin/bash"},
            "tmux": {"default_shell": "/bin/bash", "session_prefix": "yesman-test", "base_index": 1},
            "ai": {"learning_enabled": True, "prediction_threshold": 0.7, "pattern_history_limit": 1000},
            "automation": {"enabled": True, "context_detection_interval": 5, "workflow_timeout": 30},
        }

    def _write_test_config(self):
        """Write test configuration to file"""
        config_file = self.test_config_dir / "yesman.yaml"
        with open(config_file, "w") as f:
            yaml.dump(self.test_config, f, default_flow_style=False)

    def get_test_config(self) -> YesmanConfig:
        """Get YesmanConfig instance for testing"""
        if not self.config:
            # Set environment to use test directory
            os.environ["YESMAN_TEST_CONFIG"] = str(self.test_config_dir / "yesman.yaml")
            self.config = YesmanConfig()
        return self.config

    def get_session_manager(self) -> SessionManager:
        """Get SessionManager instance for testing"""
        if not self.session_manager:
            config = self.get_test_config()
            self.session_manager = SessionManager()
        return self.session_manager

    def create_test_session(self, session_name: str, **kwargs) -> dict[str, Any]:
        """Create a test session with specified configuration"""
        config = {"name": session_name, "start_directory": str(self.test_dir), "windows": [{"window_name": "main", "panes": [{"shell_command": ["echo", "test session"]}]}], **kwargs}

        # Add to projects file
        projects_file = self.test_config_dir.parent / "sessions" / "projects.yaml"
        projects_file.parent.mkdir(exist_ok=True)

        projects_data = {"sessions": {session_name: config}}
        if projects_file.exists():
            with open(projects_file) as f:
                existing = yaml.safe_load(f) or {}
            if "sessions" in existing:
                existing["sessions"][session_name] = config
                projects_data = existing

        with open(projects_file, "w") as f:
            yaml.dump(projects_data, f, default_flow_style=False)

        self.created_sessions.append(session_name)
        return config

    def wait_for_condition(self, condition_func, timeout: float = 5.0, interval: float = 0.1) -> bool:
        """Wait for a condition to become true"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        return False

    def assert_session_exists(self, session_name: str):
        """Assert that a session exists"""
        session_manager = self.get_session_manager()
        sessions = session_manager.list_sessions()
        session_names = [s.get("name") for s in sessions]
        assert session_name in session_names, f"Session {session_name} not found in {session_names}"

    def assert_session_state(self, session_name: str, expected_state: str):
        """Assert that a session is in the expected state"""
        session_manager = self.get_session_manager()
        session_info = session_manager.get_session_info(session_name)
        assert session_info is not None, f"Session {session_name} not found"
        assert session_info.get("state") == expected_state, f"Session {session_name} state is {session_info.get('state')}, expected {expected_state}"


class AsyncIntegrationTestBase(IntegrationTestBase):
    """Base class for async integration tests"""

    def setup_method(self):
        """Setup for async tests"""
        super().setup_method()
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)

    def teardown_method(self):
        """Cleanup for async tests"""
        if hasattr(self, "event_loop") and self.event_loop:
            self.event_loop.close()
        super().teardown_method()

    async def async_wait_for_condition(self, condition_func, timeout: float = 5.0, interval: float = 0.1) -> bool:
        """Async version of wait_for_condition"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
                return True
            await asyncio.sleep(interval)
        return False


class MockClaudeEnvironment:
    """Mock Claude environment for testing without actual Claude processes"""

    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.mock_responses = {}
        self.interaction_history = []

    def add_mock_response(self, prompt_pattern: str, response: str):
        """Add a mock response for a prompt pattern"""
        self.mock_responses[prompt_pattern] = response

    def simulate_interaction(self, prompt: str) -> str:
        """Simulate Claude interaction"""
        # Find matching response
        for pattern, response in self.mock_responses.items():
            if pattern.lower() in prompt.lower():
                self.interaction_history.append({"prompt": prompt, "response": response, "timestamp": time.time()})
                return response

        # Default response
        default_response = f"Mock Claude response to: {prompt[:50]}..."
        self.interaction_history.append({"prompt": prompt, "response": default_response, "timestamp": time.time()})
        return default_response

    def get_interaction_count(self) -> int:
        """Get total number of interactions"""
        return len(self.interaction_history)

    def clear_history(self):
        """Clear interaction history"""
        self.interaction_history.clear()


class IntegrationTestFixtures:
    """Collection of test fixtures for integration testing"""

    @staticmethod
    @pytest.fixture
    def test_environment():
        """Provide clean test environment"""
        base = IntegrationTestBase()
        base.setup_method()
        yield base
        base.teardown_method()

    @staticmethod
    @pytest.fixture
    def async_test_environment():
        """Provide clean async test environment"""
        base = AsyncIntegrationTestBase()
        base.setup_method()
        yield base
        base.teardown_method()

    @staticmethod
    @pytest.fixture
    def mock_claude():
        """Provide mock Claude environment"""
        test_dir = Path(tempfile.mkdtemp(prefix="claude_mock_"))
        mock_env = MockClaudeEnvironment(test_dir)

        # Add common mock responses
        mock_env.add_mock_response("help", "I'm here to help! What would you like to know?")
        mock_env.add_mock_response("code", "Here's some code for you...")
        mock_env.add_mock_response("explain", "Let me explain that concept...")

        yield mock_env

        # Cleanup
        import shutil

        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)


class CommandTestRunner:
    """Utility for running and testing CLI commands in integration tests"""

    def __init__(self, test_base: IntegrationTestBase):
        self.test_base = test_base
        self.command_results = []

    def run_command(self, command_class: type, **kwargs) -> dict[str, Any]:
        """Run a command and capture results"""
        command = command_class()

        # Setup command with test environment
        command.config = self.test_base.get_test_config()

        try:
            result = command.execute(**kwargs)
            self.command_results.append({"command": command_class.__name__, "kwargs": kwargs, "result": result, "success": True, "error": None})
            return result
        except Exception as e:
            error_result = {"command": command_class.__name__, "kwargs": kwargs, "result": None, "success": False, "error": str(e)}
            self.command_results.append(error_result)
            raise

    def get_command_history(self) -> list[dict[str, Any]]:
        """Get history of executed commands"""
        return self.command_results.copy()

    def assert_command_succeeded(self, command_class: type):
        """Assert that the most recent command of given type succeeded"""
        matching_results = [r for r in self.command_results if r["command"] == command_class.__name__]
        assert matching_results, f"No {command_class.__name__} command found in history"

        latest_result = matching_results[-1]
        assert latest_result["success"], f"Command {command_class.__name__} failed: {latest_result['error']}"


class PerformanceMonitor:
    """Monitor performance metrics during integration tests"""

    def __init__(self):
        self.metrics = {}
        self.start_times = {}

    def start_timing(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()

    def end_timing(self, operation: str) -> float:
        """End timing an operation and return duration"""
        if operation not in self.start_times:
            raise ValueError(f"No start time recorded for operation: {operation}")

        duration = time.time() - self.start_times[operation]

        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)

        del self.start_times[operation]
        return duration

    def get_average_time(self, operation: str) -> float:
        """Get average time for an operation"""
        if operation not in self.metrics or not self.metrics[operation]:
            return 0.0
        return sum(self.metrics[operation]) / len(self.metrics[operation])

    def assert_performance_threshold(self, operation: str, max_time: float):
        """Assert that operation average time is below threshold"""
        avg_time = self.get_average_time(operation)
        assert avg_time <= max_time, f"Operation {operation} average time {avg_time:.3f}s exceeds threshold {max_time}s"


# Export main classes for easy importing
__all__ = ["IntegrationTestBase", "AsyncIntegrationTestBase", "MockClaudeEnvironment", "IntegrationTestFixtures", "CommandTestRunner", "PerformanceMonitor"]
