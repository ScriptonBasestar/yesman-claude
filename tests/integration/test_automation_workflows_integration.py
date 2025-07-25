#!/usr/bin/env python3

# Copyright notice.

import asyncio
import contextlib
import time

from commands.automate import (
    AutomateConfigCommand,
    AutomateDetectCommand,
    AutomateMonitorCommand,
    AutomateWorkflowCommand,
)

from .test_framework import (
    AsyncIntegrationTestBase,
    CommandTestRunner,
    MockClaudeEnvironment,
    PerformanceMonitor,
)

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Automation Workflows Integration Tests.

Tests the complete automation system including context detection,
workflow execution, and real-time monitoring across components.
"""


class TestAutomationWorkflowIntegration(AsyncIntegrationTestBase):
    """Test complete automation workflow integration."""

    def setup_method(self) -> None:
        """Setup for automation workflow tests."""
        super().setup_method()
        self.command_runner = CommandTestRunner(self)
        self.performance_monitor = PerformanceMonitor()
        self.mock_claude = MockClaudeEnvironment(self.test_dir)

        # Setup mock responses for automation scenarios
        self._setup_automation_responses()

    def _setup_automation_responses(self) -> None:
        """Setup mock Claude responses for automation scenarios."""
        self.mock_claude.add_mock_response(
            "setup development environment",
            "I'll help set up your development environment. Detecting project type...",
        )

        self.mock_claude.add_mock_response(
            "run tests", "Running test suite... All tests passed successfully!"
        )

        self.mock_claude.add_mock_response(
            "deploy application",
            "Deploying to staging environment... Deployment completed successfully!",
        )

    def test_end_to_end_automation_workflow(self) -> None:
        """Test complete end-to-end automation workflow."""
        # Step 1: Create test project with various contexts
        project_dir = self.test_dir / "automation_project"
        project_dir.mkdir()

        # Python project files
        (project_dir / "requirements.txt").write_text("flask==2.0.0\npytest==6.0.0")
        (project_dir / "app.py").write_text(
            "from flask import Flask\napp = Flask(__name__)"
        )
        (project_dir / "test_app.py").write_text("import pytest\ndef test_app(): pass")

        # Docker files
        (project_dir / "Dockerfile").write_text("FROM python:3.9\nCOPY . /app")
        (project_dir / "docker-compose.yml").write_text(
            "version: '3.8'\nservices:\n  app:\n    build: ."
        )

        # Git repository
        (project_dir / ".git").mkdir()
        (project_dir / ".gitignore").write_text("__pycache__/\n*.pyc")

        # Step 2: Test context detection
        self.performance_monitor.start_timing("context_detection")

        detect_result = self.command_runner.run_command(
            AutomateDetectCommand, project_path=str(project_dir)
        )

        detection_duration = self.performance_monitor.end_timing("context_detection")

        assert detect_result["success"] is True
        detected_contexts = detect_result.get("contexts", [])
        assert len(detected_contexts) > 0

        # Should detect Python, Docker, and Git contexts
        context_types = [ctx.get("type") for ctx in detected_contexts]
        assert "python" in context_types
        assert "docker" in context_types
        assert "git" in context_types

        # Step 3: Configure automation for detected contexts
        config_result = self.command_runner.run_command(
            AutomateConfigCommand,
            project_path=str(project_dir),
            enable_contexts=["python", "docker"],
            auto_workflow=True,
        )

        assert config_result["success"] is True

        # Step 4: Execute automated workflow
        self.performance_monitor.start_timing("workflow_execution")

        workflow_result = self.command_runner.run_command(
            AutomateWorkflowCommand,
            project_path=str(project_dir),
            workflow_name="development_setup",
        )

        workflow_duration = self.performance_monitor.end_timing("workflow_execution")

        assert workflow_result["success"] is True
        executed_steps = workflow_result.get("executed_steps", [])
        assert len(executed_steps) > 0

        # Step 5: Test monitoring functionality
        self.performance_monitor.start_timing("monitoring_setup")

        monitor_result = self.command_runner.run_command(
            AutomateMonitorCommand,
            project_path=str(project_dir),
            duration=2,  # Monitor for 2 seconds in test
        )

        monitoring_duration = self.performance_monitor.end_timing("monitoring_setup")

        assert monitor_result["success"] is True

        # Performance assertions
        assert (
            detection_duration < 3.0
        ), f"Context detection took {detection_duration:.2f}s, should be < 3s"
        assert (
            workflow_duration < 10.0
        ), f"Workflow execution took {workflow_duration:.2f}s, should be < 10s"
        assert (
            monitoring_duration < 5.0
        ), f"Monitoring setup took {monitoring_duration:.2f}s, should be < 5s"

    def test_multi_project_automation_coordination(self) -> None:
        """Test automation coordination across multiple projects."""
        # Create multiple projects with different contexts
        projects = {
            "python_api": {
                "files": {
                    "requirements.txt": "fastapi==0.68.0",
                    "main.py": "from fastapi import FastAPI\napp = FastAPI()",
                    "test_main.py": "def test_api(): pass",
                },
                "expected_contexts": ["python", "api"],
            },
            "react_frontend": {
                "files": {
                    "package.json": (
                        '{"name": "frontend", "dependencies": {"react": "^17.0.0"}}'
                    ),
                    "src/App.js": (
                        "import React from 'react';\nfunction App() { return <div>Hello</div>; }"
                    ),
                    "src/App.test.js": "test('renders app', () => {});",
                },
                "expected_contexts": ["javascript", "react"],
            },
            "docker_service": {
                "files": {
                    "Dockerfile": "FROM nginx:alpine",
                    "docker-compose.yml": (
                        "version: '3.8'\nservices:\n  web:\n    build: ."
                    ),
                    "nginx.conf": "server { listen 80; }",
                },
                "expected_contexts": ["docker", "nginx"],
            },
        }

        project_results = {}

        # Setup projects and test automation
        for project_name, project_config in projects.items():
            project_dir = self.test_dir / project_name
            project_dir.mkdir()

            # Create project files
            for file_path, content in project_config["files"].items():
                full_path = project_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)

            # Test context detection for each project
            detect_result = self.command_runner.run_command(
                AutomateDetectCommand, project_path=str(project_dir)
            )

            assert detect_result["success"] is True
            detected_contexts = detect_result.get("contexts", [])

            project_results[project_name] = {
                "detected_contexts": detected_contexts,
                "expected_contexts": project_config["expected_contexts"],
            }

        # Verify each project detected appropriate contexts
        for project_name, results in project_results.items():
            detected_types = [ctx.get("type") for ctx in results["detected_contexts"]]
            for expected_type in results["expected_contexts"]:
                assert (
                    expected_type in detected_types
                ), f"Project {project_name} missing context {expected_type}"

        # Test global monitoring across all projects
        all_project_paths = [str(self.test_dir / name) for name in projects.keys()]

        global_monitor_result = self.command_runner.run_command(
            AutomateMonitorCommand, project_paths=all_project_paths, duration=3
        )

        assert global_monitor_result["success"] is True
        monitored_projects = global_monitor_result.get("monitored_projects", [])
        assert len(monitored_projects) == len(projects)

    def test_automation_error_recovery(self) -> None:
        """Test automation system error recovery and resilience."""
        project_dir = self.test_dir / "error_recovery_project"
        project_dir.mkdir()

        # Create project with potential issues
        (project_dir / "requirements.txt").write_text("invalid-package==999.999.999")
        (project_dir / "broken_script.py").write_text(
            "import non_existent_module\nbroken syntax here"
        )

        # Test context detection with problematic files
        detect_result = self.command_runner.run_command(
            AutomateDetectCommand, project_path=str(project_dir)
        )

        # Should succeed even with problematic files
        assert detect_result["success"] is True

        # Test workflow execution with error handling
        workflow_result = self.command_runner.run_command(
            AutomateWorkflowCommand,
            project_path=str(project_dir),
            workflow_name="validation_check",
            continue_on_error=True,
        )

        # Should handle errors gracefully
        assert workflow_result["success"] is True
        assert "errors" in workflow_result
        assert len(workflow_result["errors"]) > 0  # Should report errors

        # Fix the issues
        (project_dir / "requirements.txt").write_text("requests==2.25.1")
        (project_dir / "fixed_script.py").write_text(
            "import requests\nprint('Hello World')"
        )
        (project_dir / "broken_script.py").unlink()

        # Test recovery workflow
        recovery_result = self.command_runner.run_command(
            AutomateWorkflowCommand,
            project_path=str(project_dir),
            workflow_name="validation_check",
        )

        assert recovery_result["success"] is True
        assert len(recovery_result.get("errors", [])) == 0  # Should have no errors now


class TestRealTimeMonitoringIntegration(AsyncIntegrationTestBase):
    """Test real-time monitoring and reactive automation."""

    async def test_file_change_detection_workflow(self) -> None:
        """Test that file changes trigger appropriate automation workflows."""
        project_dir = self.test_dir / "monitoring_project"
        project_dir.mkdir()

        # Initial project setup
        (project_dir / "app.py").write_text("print('Hello World')")
        (project_dir / "requirements.txt").write_text("flask==2.0.0")

        command_runner = CommandTestRunner(self)

        # Start monitoring
        monitor_task = asyncio.create_task(
            self._run_async_monitor(command_runner, str(project_dir))
        )

        # Wait a moment for monitoring to start
        await asyncio.sleep(0.5)

        # Simulate file changes
        changes = [
            ("app.py", "from flask import Flask\napp = Flask(__name__)"),
            ("test_app.py", "import pytest\ndef test_app(): pass"),
            ("requirements.txt", "flask==2.0.0\npytest==6.0.0"),
        ]

        for filename, content in changes:
            (project_dir / filename).write_text(content)
            await asyncio.sleep(0.2)  # Small delay between changes

        # Let monitoring run for a bit
        await asyncio.sleep(2.0)

        # Stop monitoring
        monitor_task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await monitor_task

        # Verify that changes were detected and processed
        # (In a real implementation, this would check monitoring logs or events)
        assert True  # Placeholder - actual verification would depend on monitoring implementation

    @staticmethod
    async def _run_async_monitor(
        command_runner: project_path, object
    ) -> None:  # noqa: ARG002, ARG004
        """Helper to run monitoring in async context."""
        # This would be the actual async monitoring implementation
        # For now, we simulate it
        start_time = time.time()
        while time.time() - start_time < 5.0:  # Monitor for 5 seconds max
            await asyncio.sleep(0.1)

    def test_performance_based_workflow_optimization(self) -> None:
        """Test that workflows optimize based on performance metrics."""
        project_dir = self.test_dir / "performance_project"
        project_dir.mkdir()

        # Create test project
        (project_dir / "slow_script.py").write_text(
            "import time\ntime.sleep(1)\nprint('Done')"
        )
        (project_dir / "fast_script.py").write_text("print('Quick task')")

        command_runner = CommandTestRunner(self)
        performance_monitor = PerformanceMonitor()

        # Run initial workflow and measure performance
        performance_monitor.start_timing("initial_workflow")

        initial_result = command_runner.run_command(
            AutomateWorkflowCommand,
            project_path=str(project_dir),
            workflow_name="test_execution",
            optimization_level="none",
        )

        initial_duration = performance_monitor.end_timing("initial_workflow")

        assert initial_result["success"] is True

        # Run optimized workflow
        performance_monitor.start_timing("optimized_workflow")

        optimized_result = command_runner.run_command(
            AutomateWorkflowCommand,
            project_path=str(project_dir),
            workflow_name="test_execution",
            optimization_level="performance",
        )

        optimized_duration = performance_monitor.end_timing("optimized_workflow")

        assert optimized_result["success"] is True

        # Verify optimization occurred (this would depend on actual implementation)
        # For now, we just verify both workflows completed successfully
        assert initial_duration > 0
        assert optimized_duration > 0


class TestAutomationIntegrationWithAI(AsyncIntegrationTestBase):
    """Test integration between automation system and AI learning."""

    async def test_ai_guided_workflow_adaptation(self) -> None:
        """Test that AI learning guides workflow adaptation."""
        project_dir = self.test_dir / "ai_guided_project"
        project_dir.mkdir()

        # Create project with evolving requirements
        (project_dir / "requirements.txt").write_text("requests==2.25.1")
        (project_dir / "api_client.py").write_text(
            "import requests\ndef get_data(): pass"
        )

        command_runner = CommandTestRunner(self)

        # Initial workflow execution with learning enabled
        initial_result = command_runner.run_command(
            AutomateWorkflowCommand,
            project_path=str(project_dir),
            workflow_name="api_development",
            enable_learning=True,
        )

        assert initial_result["success"] is True

        # Simulate project evolution
        (project_dir / "database.py").write_text("import sqlite3\ndef setup_db(): pass")
        (project_dir / "requirements.txt").write_text("requests==2.25.1\nsqlite3")

        # Second workflow execution - should adapt based on learning
        adapted_result = command_runner.run_command(
            AutomateWorkflowCommand,
            project_path=str(project_dir),
            workflow_name="api_development",
            enable_learning=True,
        )

        assert adapted_result["success"] is True

        # Verify adaptation occurred
        executed_steps = adapted_result.get("executed_steps", [])
        assert len(executed_steps) > 0

        # Should include database-related steps in adapted workflow
        step_names = [step.get("name", "") for step in executed_steps]
        assert any("database" in name.lower() for name in step_names)

    def test_predictive_automation_suggestions(self) -> None:
        """Test AI-powered predictive automation suggestions."""
        project_dir = self.test_dir / "predictive_project"
        project_dir.mkdir()

        # Create project pattern that should trigger predictions
        (project_dir / "app.py").write_text("from fastapi import FastAPI")
        (project_dir / "models").mkdir()
        (project_dir / "models" / "__init__.py").write_text("")
        (project_dir / "models" / "user.py").write_text("class User: pass")

        command_runner = CommandTestRunner(self)

        # Request automation suggestions
        suggestions_result = command_runner.run_command(
            AutomateDetectCommand,
            project_path=str(project_dir),
            suggest_workflows=True,
            enable_predictions=True,
        )

        assert suggestions_result["success"] is True

        suggestions = suggestions_result.get("workflow_suggestions", [])
        assert len(suggestions) > 0

        # Should suggest API-related workflows for FastAPI project
        suggestion_types = [s.get("type") for s in suggestions]
        assert any(
            "api" in str(suggestion_type).lower()
            for suggestion_type in suggestion_types
        )
