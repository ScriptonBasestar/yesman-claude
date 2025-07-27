# Copyright notice.

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Never
from unittest.mock import MagicMock, patch

import pytest

from commands.show import ShowCommand
from commands.validate import ValidateCommand
from libs.core.base_command import BaseCommand
from libs.core.config_loader import ConfigLoader, EnvironmentSource, YamlFileSource
from libs.core.error_handling import ConfigurationError, SessionError, ValidationError
from libs.core.services import get_config, get_tmux_manager, register_test_services
from libs.yesman_config import YesmanConfig

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Integration tests for CLI commands."""


class TestCommandLineInterface:
    """Test CLI integration."""

    @staticmethod
    def test_yesman_help() -> None:
        """Test that yesman --help works."""
        result = subprocess.run(
            ["python", "-m", "yesman", "--help"],
            check=False,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Commands:" in result.stdout

    @pytest.mark.skip(reason="Requires tmux setup")
    @staticmethod
    def test_yesman_show_command() -> None:
        """Test yesman show command."""
        result = subprocess.run(
            ["python", "-m", "yesman", "show"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should either show sessions or indicate no sessions
        assert result.returncode == 0 or "No active sessions" in result.stdout

    @staticmethod
    def test_yesman_validate_command() -> None:
        """Test yesman validate command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary config file
            config_path = Path(temp_dir) / "test_config.yaml"
            config_path.write_text(
                """
mode: merge
logging:
  level: INFO
tmux:
  default_shell: /bin/bash
"""
            )

            # Run validate command
            result = subprocess.run(
                ["python", "-m", "yesman", "validate"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                env={**os.environ, "YESMAN_CONFIG_PATH": str(config_path)},
            )

            # Should complete successfully
            assert result.returncode == 0


class TestCommandExecution:
    """Test command execution without CLI."""

    @pytest.fixture(autouse=True)
    @staticmethod
    def setup_test_services() -> None:
        """Setup test services before each test."""
        mock_config = MagicMock()
        mock_config.get.return_value = "test_value"
        mock_config.schema.logging.level = "INFO"
        mock_config.root_dir = Path("/tmp/test")

        mock_tmux = MagicMock()
        mock_tmux.list_running_sessions.return_value = []
        mock_tmux.get_all_sessions.return_value = []

        register_test_services(config=mock_config, tmux_manager=mock_tmux)

    @staticmethod
    def test_show_command_execution() -> None:
        """Test ShowCommand execution."""
        command = ShowCommand()

        # Should not raise exception
        result = command.execute()

        assert result is not None
        assert isinstance(result, dict)

    @staticmethod
    def test_validate_command_execution() -> None:
        """Test ValidateCommand execution."""
        command = ValidateCommand()

        # Mock tmux_manager to return empty sessions
        with patch.object(command, "tmux_manager") as mock_tmux:
            mock_tmux.load_projects.return_value = {"sessions": {}}

            result = command.execute()

            # When no sessions are defined, it should return failure
            assert result["success"] is False
            assert result["error"] == "no_sessions_defined"

    @staticmethod
    def test_command_error_handling() -> None:
        """Test command error handling."""
        command = ShowCommand()

        # Mock tmux_manager to raise an error
        with patch.object(command, "tmux_manager") as mock_tmux:
            mock_tmux.list_running_sessions.side_effect = SessionError("Failed to connect to tmux", recovery_hint="Check if tmux is running")

            # Error should be handled gracefully
            with pytest.raises(SessionError) as exc_info:
                command.execute()

            assert "Failed to connect to tmux" in str(exc_info.value)
            assert "Check if tmux is running" in exc_info.value.recovery_hint


class TestConfigurationIntegration:
    """Test configuration integration."""

    @staticmethod
    def test_environment_variable_override() -> None:
        """Test that environment variables override config."""
        # Create loader with environment source
        loader = ConfigLoader()
        loader.add_source(EnvironmentSource())

        with patch.dict(os.environ, {"YESMAN_LOGGING_LEVEL": "ERROR", "YESMAN_TMUX_MOUSE": "false"}):
            config = YesmanConfig(config_loader=loader)

            assert config.get("logging.level") == "ERROR"
            assert config.get("tmux.mouse") is False

    @staticmethod
    def test_config_file_loading() -> None:
        """Test configuration file loading."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(
                """
mode: isolated
logging:
  level: WARNING
custom:
  test_value: 42
"""
            )
            f.flush()

            try:
                loader = ConfigLoader()
                loader.add_source(YamlFileSource(f.name))

                config = YesmanConfig(config_loader=loader)

                assert config.get("mode") == "isolated"
                assert config.get("logging.level") == "WARNING"
                assert config.get("custom.test_value") == 42

            finally:
                Path(f.name).unlink()


class TestErrorHandlingIntegration:
    """Test error handling integration."""

    @staticmethod
    def test_command_error_propagation() -> None:
        """Test that errors propagate correctly through command execution."""

        class TestCommand(BaseCommand):
            @staticmethod
            def execute(**kwargs: dict[str, object]) -> Never:
                msg = "Test validation error"
                raise ValidationError(
                    msg,
                    field_name="test_field",
                    recovery_hint="Fix the test field",
                )

        command = TestCommand()

        with pytest.raises(ValidationError) as exc_info:
            command.run()

        error = exc_info.value
        assert error.message == "Test validation error"
        assert error.context.additional_info["field_name"] == "test_field"
        assert error.recovery_hint == "Fix the test field"

    @staticmethod
    def test_error_serialization() -> None:
        """Test error serialization for API responses."""
        error = ConfigurationError("Config file not found", config_file="/missing/config.yaml")

        error_dict = error.to_dict()

        assert error_dict["message"] == "Config file not found"
        assert error_dict["category"] == "configuration"
        assert error_dict["context"]["file_path"] == "/missing/config.yaml"
        assert "recovery_hint" in error_dict
        assert error_dict["code"].startswith("CONFIGURATION_")


class TestDependencyInjectionIntegration:
    """Test DI container integration."""

    @staticmethod
    def test_service_resolution() -> None:
        """Test that services are resolved correctly."""
        # Services should be resolvable
        config = get_config()
        tmux_manager = get_tmux_manager()

        assert config is not None
        assert tmux_manager is not None

        # Should return same instances (singleton behavior)
        config2 = get_config()
        assert config is config2

    @staticmethod
    def test_service_mocking_for_tests() -> None:
        """Test that services can be mocked for testing."""
        mock_config = MagicMock()
        mock_config.test_value = "mocked"

        register_test_services(config=mock_config)

        resolved_config = get_config()
        assert resolved_config.test_value == "mocked"


class TestPerformanceIntegration:
    """Test performance aspects."""

    @staticmethod
    def test_command_execution_time() -> None:
        """Test that commands execute within reasonable time."""
        command = ShowCommand()

        start_time = time.time()
        result = command.execute()
        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete within 1 second
        assert execution_time < 1.0
        assert result is not None

    @staticmethod
    def test_config_loading_performance() -> None:
        """Test configuration loading performance."""
        start_time = time.time()
        config = YesmanConfig()
        end_time = time.time()

        loading_time = end_time - start_time

        # Should load within 0.5 seconds
        assert loading_time < 0.5
        assert config is not None


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.skip(reason="Requires tmux and session setup")
    @staticmethod
    def test_full_session_workflow() -> None:
        """Test complete session creation and management workflow."""
        # This would test:
        # 1. Creating a new session
        # 2. Verifying it exists
        # 3. Attaching to it
        # 4. Running commands
        # 5. Detaching
        # 6. Destroying the session

    @staticmethod
    def test_error_recovery_scenario() -> None:
        """Test error recovery scenarios."""
        command = ShowCommand()

        # Simulate tmux not available
        with patch.object(command, "tmux_manager") as mock_tmux:
            mock_tmux.list_running_sessions.side_effect = SessionError(
                "tmux server not found",
                recovery_hint="Start tmux server with 'tmux new-session'",
            )

            with pytest.raises(SessionError) as exc_info:
                command.execute()

            # Error should contain helpful recovery information
            error = exc_info.value
            assert "tmux server not found" in error.message
            assert "tmux new-session" in error.recovery_hint
