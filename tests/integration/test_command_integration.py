"""Integration tests for CLI commands"""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from commands.show import ShowCommand
from commands.validate import ValidateCommand
from libs.core.services import register_test_services


class TestCommandLineInterface:
    """Test CLI integration"""

    def test_yesman_help(self):
        """Test that yesman --help works"""
        result = subprocess.run(["python", "-m", "yesman", "--help"], check=False, capture_output=True, text=True, cwd=os.getcwd())

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Commands:" in result.stdout

    @pytest.mark.skip(reason="Requires tmux setup")
    def test_yesman_show_command(self):
        """Test yesman show command"""
        result = subprocess.run(["python", "-m", "yesman", "show"], check=False, capture_output=True, text=True, timeout=10)

        # Should either show sessions or indicate no sessions
        assert result.returncode == 0 or "No active sessions" in result.stdout

    def test_yesman_validate_command(self):
        """Test yesman validate command"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary config file
            config_path = Path(temp_dir) / "test_config.yaml"
            config_path.write_text("""
mode: merge
logging:
  level: INFO
tmux:
  default_shell: /bin/bash
""")

            # Run validate command
            result = subprocess.run(["python", "-m", "yesman", "validate"], check=False, capture_output=True, text=True, timeout=10, env={**os.environ, "YESMAN_CONFIG_PATH": str(config_path)})

            # Should complete successfully
            assert result.returncode == 0


class TestCommandExecution:
    """Test command execution without CLI"""

    @pytest.fixture(autouse=True)
    def setup_test_services(self):
        """Setup test services before each test"""
        mock_config = MagicMock()
        mock_config.get.return_value = "test_value"
        mock_config.schema.logging.level = "INFO"
        mock_config.root_dir = Path("/tmp/test")

        mock_tmux = MagicMock()
        mock_tmux.list_running_sessions.return_value = []
        mock_tmux.get_all_sessions.return_value = []

        register_test_services(config=mock_config, tmux_manager=mock_tmux)

    def test_show_command_execution(self):
        """Test ShowCommand execution"""
        command = ShowCommand()

        # Should not raise exception
        result = command.execute()

        assert result is not None
        assert isinstance(result, dict)

    def test_validate_command_execution(self):
        """Test ValidateCommand execution"""
        command = ValidateCommand()

        # Mock configuration validation
        with patch.object(command, "config") as mock_config:
            mock_config.validate.return_value = True

            result = command.execute()

            assert result["success"] is True
            assert "validation" in result["message"].lower()

    def test_command_error_handling(self):
        """Test command error handling"""
        from commands.show import ShowCommand
        from libs.core.error_handling import SessionError

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
    """Test configuration integration"""

    def test_environment_variable_override(self):
        """Test that environment variables override config"""
        from libs.core.config_loader import ConfigLoader, EnvironmentSource
        from libs.yesman_config import YesmanConfig

        # Create loader with environment source
        loader = ConfigLoader()
        loader.add_source(EnvironmentSource())

        with patch.dict(os.environ, {"YESMAN_LOGGING_LEVEL": "ERROR", "YESMAN_TMUX_MOUSE": "false"}):
            config = YesmanConfig(config_loader=loader)

            assert config.get("logging.level") == "ERROR"
            assert config.get("tmux.mouse") is False

    def test_config_file_loading(self):
        """Test configuration file loading"""
        from libs.core.config_loader import ConfigLoader, YamlFileSource
        from libs.yesman_config import YesmanConfig

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
mode: isolated
logging:
  level: WARNING
custom:
  test_value: 42
""")
            f.flush()

            try:
                loader = ConfigLoader()
                loader.add_source(YamlFileSource(f.name))

                config = YesmanConfig(config_loader=loader)

                assert config.get("mode") == "isolated"
                assert config.get("logging.level") == "WARNING"
                assert config.get("custom.test_value") == 42

            finally:
                os.unlink(f.name)


class TestErrorHandlingIntegration:
    """Test error handling integration"""

    def test_command_error_propagation(self):
        """Test that errors propagate correctly through command execution"""
        from libs.core.base_command import BaseCommand
        from libs.core.error_handling import ValidationError

        class TestCommand(BaseCommand):
            def execute(self, **kwargs):
                raise ValidationError("Test validation error", field_name="test_field", recovery_hint="Fix the test field")

        command = TestCommand()

        with pytest.raises(ValidationError) as exc_info:
            command.run()

        error = exc_info.value
        assert error.message == "Test validation error"
        assert error.context.additional_info["field_name"] == "test_field"
        assert error.recovery_hint == "Fix the test field"

    def test_error_serialization(self):
        """Test error serialization for API responses"""
        from libs.core.error_handling import ConfigurationError

        error = ConfigurationError("Config file not found", config_file="/missing/config.yaml")

        error_dict = error.to_dict()

        assert error_dict["message"] == "Config file not found"
        assert error_dict["category"] == "configuration"
        assert error_dict["context"]["file_path"] == "/missing/config.yaml"
        assert "recovery_hint" in error_dict
        assert error_dict["code"].startswith("CONFIGURATION_")


class TestDependencyInjectionIntegration:
    """Test DI container integration"""

    def test_service_resolution(self):
        """Test that services are resolved correctly"""
        from libs.core.services import get_config, get_tmux_manager

        # Services should be resolvable
        config = get_config()
        tmux_manager = get_tmux_manager()

        assert config is not None
        assert tmux_manager is not None

        # Should return same instances (singleton behavior)
        config2 = get_config()
        assert config is config2

    def test_service_mocking_for_tests(self):
        """Test that services can be mocked for testing"""
        from libs.core.services import get_config, register_test_services

        mock_config = MagicMock()
        mock_config.test_value = "mocked"

        register_test_services(config=mock_config)

        resolved_config = get_config()
        assert resolved_config.test_value == "mocked"


class TestPerformanceIntegration:
    """Test performance aspects"""

    def test_command_execution_time(self):
        """Test that commands execute within reasonable time"""
        import time

        from commands.show import ShowCommand

        command = ShowCommand()

        start_time = time.time()
        result = command.execute()
        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete within 1 second
        assert execution_time < 1.0
        assert result is not None

    def test_config_loading_performance(self):
        """Test configuration loading performance"""
        import time

        from libs.yesman_config import YesmanConfig

        start_time = time.time()
        config = YesmanConfig()
        end_time = time.time()

        loading_time = end_time - start_time

        # Should load within 0.5 seconds
        assert loading_time < 0.5
        assert config is not None


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    @pytest.mark.skip(reason="Requires tmux and session setup")
    def test_full_session_workflow(self):
        """Test complete session creation and management workflow"""
        # This would test:
        # 1. Creating a new session
        # 2. Verifying it exists
        # 3. Attaching to it
        # 4. Running commands
        # 5. Detaching
        # 6. Destroying the session
        pass

    def test_error_recovery_scenario(self):
        """Test error recovery scenarios"""
        from commands.show import ShowCommand
        from libs.core.error_handling import SessionError

        command = ShowCommand()

        # Simulate tmux not available
        with patch.object(command, "tmux_manager") as mock_tmux:
            mock_tmux.list_running_sessions.side_effect = SessionError("tmux server not found", recovery_hint="Start tmux server with 'tmux new-session'")

            with pytest.raises(SessionError) as exc_info:
                command.execute()

            # Error should contain helpful recovery information
            error = exc_info.value
            assert "tmux server not found" in error.message
            assert "tmux new-session" in error.recovery_hint
