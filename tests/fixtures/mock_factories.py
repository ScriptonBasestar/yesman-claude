from typing import Any, cast
from unittest.mock import MagicMock, patch

# Convenience exports for easy importing

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Centralized Mock Factory System
Provides standardized mock objects to reduce duplication across test files.
"""

# Default mock data - duplicated here to avoid circular imports
MOCK_SESSION_DATA = {
    "session_name": "test-session",
    "project_name": "test-project",
    "status": "active",
    "windows": [
        {"name": "main", "panes": 2},
        {"name": "logs", "panes": 1},
    ],
    "controller_status": "running",
    "controller_pid": 12345,
    "created_at": "2024-01-08T10:00:00",
    "last_activity": "2024-01-08T10:30:00",
}

MOCK_API_RESPONSES = {
    "sessions_list": {
        "status": "success",
        "data": [MOCK_SESSION_DATA],
        "count": 1,
    },
    "controller_start": {
        "status": "success",
        "message": "Controller started",
        "pid": 12345,
    },
    "error_response": {
        "status": "error",
        "message": "Internal server error",
        "code": 500,
    },
}


class ManagerMockFactory:
    """Factory for commonly mocked manager classes."""

    @staticmethod
    def create_session_manager_mock(**kwargs: object) -> MagicMock:
        """Create a standardized SessionManager mock.

        Args:
            sessions: List of session data (default: [MOCK_SESSION_DATA])
            create_session_result: Return value for create_session (default: True)
            get_session_info_result: Return value for get_session_info (default: MOCK_SESSION_DATA)
            validate_session_name_side_effect: Side effect for validation (default: None)
            **kwargs: dict[str, object]: Additional attributes to set on the mock

        Returns:
            MagicMock configured with standard SessionManager behavior
        """
        mock_manager = MagicMock()

        # Default behaviors
        sessions = cast("list[dict[str, Any]]", kwargs.get("sessions", [MOCK_SESSION_DATA]))
        mock_manager.get_sessions.return_value = sessions
        mock_manager.list_sessions.return_value = [s["session_name"] for s in sessions]

        # Create session behavior (return value or side effect)
        if "create_session_side_effect" in kwargs:
            mock_manager.create_session.side_effect = kwargs["create_session_side_effect"]
        else:
            mock_manager.create_session.return_value = kwargs.get("create_session_result", True)

        mock_manager.get_session_info.return_value = kwargs.get("get_session_info_result", MOCK_SESSION_DATA)

        # Validation behavior
        if "validate_session_name_side_effect" in kwargs:
            mock_manager.validate_session_name.side_effect = kwargs["validate_session_name_side_effect"]
        else:
            mock_manager.validate_session_name.return_value = None  # No exception = valid

        # Additional session operations
        mock_manager.start_session.return_value = True
        mock_manager.stop_session.return_value = True
        mock_manager.restart_session.return_value = True
        mock_manager.session_exists.return_value = True
        mock_manager.kill_session.return_value = True

        # Project management operations
        mock_manager.get_all_projects.return_value = kwargs.get("get_all_projects_result", [])

        # Set any additional attributes
        for key, value in kwargs.items():
            if not key.startswith("_") and not hasattr(mock_manager, key):
                setattr(mock_manager, key, value)

        return mock_manager

    @staticmethod
    def create_claude_manager_mock(**kwargs: object) -> MagicMock:
        """Create a standardized ClaudeManager mock.

        Args:
            controller_count: Number of active controllers (default: 1)
            get_controller_result: Mock controller object (default: auto-generated)
            controllers_status: Status dict for all controllers (default: {"test-session": "running"})
            **kwargs: dict[str, object]: Additional attributes to set on the mock

        Returns:
            MagicMock configured with standard ClaudeManager behavior
        """
        mock_manager = MagicMock()

        # Default controller
        controller_count = cast("int", kwargs.get("controller_count", 1))
        if "get_controller_result" in kwargs:
            mock_controller = kwargs["get_controller_result"]
        else:
            mock_controller = MagicMock()
            mock_controller.session_name = "test-session"
            mock_controller.status = "running"
            mock_controller.pid = 12345
            mock_controller.start.return_value = True
            mock_controller.stop.return_value = True
            mock_controller.restart.return_value = True
            mock_controller.is_running.return_value = True

        # Manager behaviors
        mock_manager.get_controller.return_value = mock_controller
        mock_manager.create_controller.return_value = mock_controller
        mock_manager.list_controllers.return_value = [mock_controller] * controller_count
        mock_manager.get_controller_count.return_value = controller_count

        # Status tracking
        controllers_status = cast(
            "dict[str, str]",
            kwargs.get("controllers_status", {"test-session": "running"}),
        )
        mock_manager.get_all_status.return_value = controllers_status
        mock_manager.get_status.return_value = next(iter(controllers_status.values())) if controllers_status else "stopped"

        # Session operations
        mock_manager.start_session.return_value = True
        mock_manager.stop_session.return_value = True
        mock_manager.stop_all.return_value = True

        # Set any additional attributes
        for key, value in kwargs.items():
            if not key.startswith("_") and not hasattr(mock_manager, key):
                setattr(mock_manager, key, value)

        return mock_manager

    @staticmethod
    def create_tmux_manager_mock(**kwargs: object) -> MagicMock:
        """Create a standardized TmuxManager mock.

        Args:
            sessions: List of session names (default: ["test-session"])
            list_sessions_result: Return value for list_sessions (default: sessions)
            session_exists_result: Return value for session_exists (default: True)
            **kwargs: dict[str, object]: Additional attributes to set on the mock

        Returns:
            MagicMock configured with standard TmuxManager behavior
        """
        mock_manager = MagicMock()

        # Default sessions
        sessions = kwargs.get("sessions", ["test-session"])
        mock_manager.list_sessions.return_value = kwargs.get("list_sessions_result", sessions)
        mock_manager.session_exists.return_value = kwargs.get("session_exists_result", True)

        # Session operations
        mock_manager.create_session.return_value = True
        mock_manager.kill_session.return_value = True
        mock_manager.attach_session.return_value = True

        # Server operations
        mock_manager.server_running.return_value = True
        mock_manager.start_server.return_value = True

        # Project loading operations (for setup/up commands)
        mock_manager.load_projects.return_value = kwargs.get("load_projects_result", {"sessions": {}})
        mock_manager.list_running_sessions.return_value = None

        # Set any additional attributes
        for key, value in kwargs.items():
            if not key.startswith("_") and not hasattr(mock_manager, key):
                setattr(mock_manager, key, value)

        return mock_manager


class ComponentMockFactory:
    """Factory for commonly mocked component objects."""

    @staticmethod
    def create_tmux_session_mock(name: str = "test-session", **kwargs: Any) -> MagicMock:
        """Create a standardized tmux session mock."""
        mock_session = MagicMock()
        mock_session.name = name
        mock_session.id = f"${name}:0"
        mock_session.created = kwargs.get("created", "2024-01-01T00:00:00")

        # Windows
        windows = kwargs.get("windows", [])
        mock_session.list_windows.return_value = windows
        mock_session.window_count = len(windows)

        # Operations
        mock_session.kill_session.return_value = None
        mock_session.rename_session.return_value = None
        mock_session.new_window.return_value = MagicMock()

        return mock_session

    @staticmethod
    def create_subprocess_mock(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
        """Create a standardized subprocess.run result mock."""
        mock_result = MagicMock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        mock_result.stderr = stderr
        mock_result.check_returncode.return_value = None if returncode == 0 else Exception(f"Command failed with code {returncode}")

        return mock_result

    @staticmethod
    def create_api_response_mock(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
        """Create a standardized API response mock."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or MOCK_API_RESPONSES["sessions_list"]
        mock_response.text = str(json_data) if json_data else ""
        mock_response.ok = status_code < 400

        return mock_response


class PatchContextFactory:
    """Factory for common patch contexts."""

    @staticmethod
    def patch_session_manager(**kwargs: object) -> object:
        """Create a patch context for SessionManager with standard mock."""
        mock_manager = ManagerMockFactory.create_session_manager_mock(**kwargs)
        return patch("libs.core.session_manager.SessionManager", return_value=mock_manager)

    @staticmethod
    def patch_claude_manager(**kwargs: object) -> object:
        """Create a patch context for ClaudeManager with standard mock."""
        mock_manager = ManagerMockFactory.create_claude_manager_mock(**kwargs)
        return patch("libs.core.claude_manager.ClaudeManager", return_value=mock_manager)

    @staticmethod
    def patch_tmux_manager(**kwargs: object) -> object:
        """Create a patch context for TmuxManager with standard mock."""
        mock_manager = ManagerMockFactory.create_tmux_manager_mock(**kwargs)
        return patch("libs.tmux_manager.TmuxManager", return_value=mock_manager)

    @staticmethod
    def patch_setup_tmux_manager(**kwargs: object) -> object:
        """Create a patch context for TmuxManager in setup commands."""
        mock_manager = ManagerMockFactory.create_tmux_manager_mock(**kwargs)
        return patch("commands.setup.TmuxManager", return_value=mock_manager)

    @staticmethod
    def patch_subprocess_run(**kwargs: object) -> object:
        """Create a patch context for subprocess.run with standard mock."""
        mock_result = ComponentMockFactory.create_subprocess_mock(**cast("dict[str, Any]", kwargs))
        return patch("subprocess.run", return_value=mock_result)


# Enhanced Test Factories for Advanced Testing Infrastructure
import random
from datetime import UTC, datetime, timedelta
from typing import Any

from faker import Faker

fake = Faker()


class EnhancedTestDataFactory:
    """Factory for creating comprehensive test data for advanced testing scenarios."""

    @staticmethod
    def create_property_test_data(num_samples: int = 100) -> list[dict[str, Any]]:
        """Create property-based test data samples.

        Args:
            num_samples: Number of test data samples to generate

        Returns:
            List of property test data dictionaries
        """
        samples = []
        for _ in range(num_samples):
            sample = {
                "session_name": fake.slug() + "_" + str(random.randint(1, 999)),
                "session_data": {
                    "user_id": fake.uuid4(),
                    "preferences": {
                        "theme": random.choice(["light", "dark"]),
                        "auto_response": random.choice([True, False]),
                        "timeout_seconds": random.randint(5, 300),
                    },
                    "tasks": [
                        {
                            "task_id": fake.uuid4(),
                            "priority": random.choice(["low", "medium", "high", "critical"]),
                            "duration": random.randint(60, 7200),
                        }
                        for _ in range(random.randint(1, 10))
                    ],
                    "metadata": {
                        "created_at": datetime.now(UTC).isoformat(),
                        "version": f"1.{random.randint(0, 100)}.{random.randint(0, 100)}",
                        "checksum": fake.md5(),
                    },
                },
                # Property validation flags
                "valid_name": True,
                "data_serializable": True,
                "constraints_satisfied": True,
            }
            samples.append(sample)
        return samples

    @staticmethod
    def create_chaos_scenario(scenario_type: str = None) -> dict[str, Any]:
        """Create a chaos engineering test scenario.

        Args:
            scenario_type: Type of chaos scenario to create

        Returns:
            Chaos scenario configuration dictionary
        """
        if not scenario_type:
            scenario_type = random.choice(["network_failure", "memory_pressure", "cpu_saturation", "disk_full", "dependency_unavailable", "process_crash"])

        scenario = {
            "scenario_id": fake.uuid4(),
            "scenario_type": scenario_type,
            "target_component": random.choice(["claude_monitor_async", "session_manager", "event_bus", "dashboard_integration", "api_server"]),
            "severity": random.choice(["low", "medium", "high", "critical"]),
            "duration_seconds": random.randint(5, 300),
            "failure_conditions": {},
            "expected_behavior": {
                "should_degrade_gracefully": True,
                "should_retry_operations": True,
                "max_recovery_time_s": random.randint(10, 300),
            },
            "validation_rules": [],
        }

        # Add scenario-specific conditions
        if scenario_type == "network_failure":
            scenario["failure_conditions"] = {
                "packet_loss_percent": random.randint(5, 100),
                "latency_increase_ms": random.randint(100, 5000),
                "timeout_multiplier": random.uniform(2.0, 10.0),
            }
            scenario["validation_rules"] = [
                {"rule": "response_time_increase", "threshold": "baseline * 2"},
                {"rule": "retry_attempts_triggered", "expected": True},
            ]
        elif scenario_type == "memory_pressure":
            scenario["failure_conditions"] = {
                "memory_limit_mb": random.randint(64, 512),
                "pressure_rate": random.uniform(0.1, 2.0),
                "gc_frequency_multiplier": random.uniform(0.5, 3.0),
            }
            scenario["validation_rules"] = [
                {"rule": "memory_usage_controlled", "threshold": "< 90%"},
                {"rule": "gc_triggered", "expected": True},
            ]

        return scenario

    @staticmethod
    def create_performance_metrics(time_range_hours: int = 24) -> dict[str, Any]:
        """Create performance test metrics data.

        Args:
            time_range_hours: Time range for metrics generation

        Returns:
            Performance metrics data dictionary
        """
        start_time = datetime.now(UTC) - timedelta(hours=time_range_hours)
        metrics_data = []

        components = ["content_capture", "claude_status_check", "prompt_detection", "content_processing", "response_sending", "automation_analysis"]

        for hour_offset in range(time_range_hours):
            timestamp = start_time + timedelta(hours=hour_offset)
            for component in components:
                metric = {
                    "timestamp": timestamp.timestamp(),
                    "component": component,
                    "response_times": {
                        "p50_ms": random.uniform(10, 100),
                        "p90_ms": random.uniform(50, 200),
                        "p95_ms": random.uniform(100, 300),
                        "p99_ms": random.uniform(200, 500),
                        "mean_ms": random.uniform(20, 150),
                    },
                    "resource_usage": {
                        "cpu_percent": random.uniform(0, 100),
                        "memory_mb": random.uniform(50, 512),
                        "network_io_mb_s": random.uniform(0, 10),
                    },
                    "error_metrics": {
                        "error_count": random.randint(0, 10),
                        "error_rate": random.uniform(0, 0.05),
                    },
                }
                metrics_data.append(metric)

        return {
            "metadata": {
                "generated_at": datetime.now(UTC).isoformat(),
                "time_range_hours": time_range_hours,
                "sample_count": len(metrics_data),
            },
            "metrics": metrics_data,
            "summary": {
                "total_samples": len(metrics_data),
                "components_covered": len(components),
                "avg_response_time_ms": sum(m["response_times"]["mean_ms"] for m in metrics_data) / len(metrics_data),
            },
        }

    @staticmethod
    def create_test_execution_metrics(test_name: str, **kwargs) -> dict[str, Any]:
        """Create test execution metrics for performance monitoring.

        Args:
            test_name: Name of the test
            **kwargs: Additional test configuration

        Returns:
            Test execution metrics dictionary
        """
        status = kwargs.get("status", random.choice(["passed", "failed", "skipped"]))
        duration_ms = kwargs.get("duration_ms", random.uniform(1, 5000))

        return {
            "test_id": fake.uuid4(),
            "test_name": test_name,
            "test_suite": kwargs.get("test_suite", "unit.core"),
            "timestamp": datetime.now(UTC).timestamp(),
            "execution_metrics": {
                "duration_ms": duration_ms,
                "setup_time_ms": random.uniform(0.1, 100),
                "teardown_time_ms": random.uniform(0.1, 50),
                "memory_peak_mb": random.uniform(1, 100),
                "memory_delta_mb": random.uniform(-10, 50),
                "cpu_time_ms": random.uniform(0.1, 1000),
                "io_operations": random.randint(0, 100),
                "network_calls": random.randint(0, 20),
            },
            "result": {
                "status": status,
                "assertions_count": random.randint(1, 50),
                "error_message": fake.sentence() if status == "failed" else None,
                "failure_details": [
                    {
                        "assertion": fake.sentence(),
                        "expected": fake.word(),
                        "actual": fake.word(),
                        "location": f"{fake.file_name()}.py:{random.randint(1, 500)}",
                    }
                ]
                if status == "failed"
                else [],
            },
            "flakiness_indicators": {
                "execution_count": kwargs.get("execution_count", 1),
                "failure_count": kwargs.get("failure_count", 1 if status == "failed" else 0),
                "duration_variance_ms": random.uniform(0, duration_ms * 0.3),
                "consistency_score": random.uniform(0.7, 1.0),
            },
        }

    @staticmethod
    def create_contract_test_data(endpoint: str, method: str = "GET") -> dict[str, Any]:
        """Create API contract test data.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Returns:
            Contract test data dictionary
        """
        return {
            "contract_id": fake.uuid4(),
            "api_endpoint": endpoint,
            "method": method,
            "request_schema": {
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {fake.uuid4()}",
                    "User-Agent": fake.user_agent(),
                },
                "query_params": {
                    "limit": random.randint(1, 100),
                    "offset": random.randint(0, 1000),
                },
                "body_schema": {
                    "data": {},
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                if method in {"POST", "PUT", "PATCH"}
                else None,
            },
            "expected_response": {
                "status_codes": [200] if method == "GET" else [200, 201],
                "headers": {
                    "Content-Type": "application/json",
                    "X-Response-Time": f"{random.randint(1, 100)}ms",
                },
                "body_schema": {
                    "success": True,
                    "data": {},
                    "meta": {
                        "request_id": fake.uuid4(),
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                },
            },
            "contract_rules": [
                {"rule": "response_time_under_threshold", "threshold_ms": 1000},
                {"rule": "valid_json_response", "expected": True},
                {"rule": "proper_http_status_code", "expected": True},
            ],
        }


class PerformanceAlertFactory(MagicMock):
    """Factory for creating performance alert mock objects."""

    @classmethod
    def create_alert(cls, severity: str = "warning", **kwargs) -> MagicMock:
        """Create a performance alert mock.

        Args:
            severity: Alert severity level
            **kwargs: Additional alert properties

        Returns:
            Performance alert mock object
        """
        alert = cls()
        alert.timestamp = kwargs.get("timestamp", datetime.now(UTC).timestamp())
        alert.severity = severity
        alert.metric_type = kwargs.get("metric_type", "response_time")
        alert.component = kwargs.get("component", "claude_monitor_async")
        alert.current_value = kwargs.get("current_value", random.uniform(100, 500))
        alert.threshold = kwargs.get("threshold", random.uniform(50, 200))
        alert.message = kwargs.get("message", f"Performance threshold exceeded for {alert.component}")
        alert.context = kwargs.get(
            "context",
            {
                "samples": random.randint(10, 100),
                "window_seconds": random.randint(30, 300),
            },
        )

        return alert


class ChaosTestRunner:
    """Utility class for running chaos engineering tests."""

    @staticmethod
    def create_test_scenario_suite(num_scenarios: int = 10) -> list[dict[str, Any]]:
        """Create a complete chaos test scenario suite.

        Args:
            num_scenarios: Number of scenarios to create

        Returns:
            List of chaos test scenarios
        """
        scenarios = []
        scenario_types = ["network_failure", "memory_pressure", "cpu_saturation", "disk_full", "dependency_unavailable", "process_crash"]

        for i in range(num_scenarios):
            scenario_type = scenario_types[i % len(scenario_types)]
            scenario = EnhancedTestDataFactory.create_chaos_scenario(scenario_type)
            scenario["test_order"] = i + 1
            scenario["prerequisites"] = []
            scenario["cleanup_required"] = True
            scenarios.append(scenario)

        return scenarios

    @staticmethod
    def create_resilience_test_matrix() -> dict[str, list[dict[str, Any]]]:
        """Create a matrix of resilience test scenarios organized by category.

        Returns:
            Dictionary mapping test categories to scenario lists
        """
        return {
            "network_resilience": [EnhancedTestDataFactory.create_chaos_scenario("network_failure") for _ in range(5)],
            "resource_resilience": [EnhancedTestDataFactory.create_chaos_scenario("memory_pressure") for _ in range(3)]
            + [EnhancedTestDataFactory.create_chaos_scenario("cpu_saturation") for _ in range(2)],
            "dependency_resilience": [EnhancedTestDataFactory.create_chaos_scenario("dependency_unavailable") for _ in range(4)],
            "process_resilience": [EnhancedTestDataFactory.create_chaos_scenario("process_crash") for _ in range(3)],
        }


__all__ = [
    "ChaosTestRunner",
    "ComponentMockFactory",
    "EnhancedTestDataFactory",
    "ManagerMockFactory",
    "PatchContextFactory",
    "PerformanceAlertFactory",
]
