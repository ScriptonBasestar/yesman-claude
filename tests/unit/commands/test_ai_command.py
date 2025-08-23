# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for ai command."""

from unittest.mock import MagicMock, patch
import pytest

from click.testing import CliRunner

from commands.ai import (
    AIStatusCommand, AIConfigCommand, AIHistoryCommand, 
    AIExportCommand, AICleanupCommand, AIPredictCommand, ai
)
from libs.core.base_command import BaseCommand, CommandError


class TestAICommands:
    """Test AI command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    def test_ai_status_command_inheritance(self) -> None:
        """Test that AIStatusCommand properly inherits from BaseCommand."""
        assert issubclass(AIStatusCommand, BaseCommand)

    def test_ai_config_command_inheritance(self) -> None:
        """Test that AIConfigCommand properly inherits from BaseCommand."""
        assert issubclass(AIConfigCommand, BaseCommand)

    def test_ai_history_command_inheritance(self) -> None:
        """Test that AIHistoryCommand properly inherits from BaseCommand."""
        assert issubclass(AIHistoryCommand, BaseCommand)

    def test_ai_export_command_inheritance(self) -> None:
        """Test that AIExportCommand properly inherits from BaseCommand."""
        assert issubclass(AIExportCommand, BaseCommand)

    def test_ai_cleanup_command_inheritance(self) -> None:
        """Test that AICleanupCommand properly inherits from BaseCommand."""
        assert issubclass(AICleanupCommand, BaseCommand)

    def test_ai_predict_command_inheritance(self) -> None:
        """Test that AIPredictCommand properly inherits from BaseCommand."""
        assert issubclass(AIPredictCommand, BaseCommand)

    @patch("commands.ai.AIStatusCommand")
    def test_ai_status_cli(self, mock_command_class: MagicMock) -> None:
        """Test ai status CLI command."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command
        result = self.runner.invoke(ai, ["status"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with()

    @patch("commands.ai.AIConfigCommand")
    def test_ai_config_cli_with_threshold(self, mock_command_class: MagicMock) -> None:
        """Test ai config CLI command with threshold option."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with threshold
        result = self.runner.invoke(ai, ["config", "--threshold", "0.8"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(threshold=0.8, auto_response=None, learning=None)

    @patch("commands.ai.AIHistoryCommand")
    def test_ai_history_cli_with_options(self, mock_command_class: MagicMock) -> None:
        """Test ai history CLI command with options."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with options
        result = self.runner.invoke(ai, ["history", "--limit", "20", "--type", "prompt", "--project", "test"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(limit=20, type="prompt", project="test")

    @patch("commands.ai.AIExportCommand")
    def test_ai_export_cli_with_output(self, mock_command_class: MagicMock) -> None:
        """Test ai export CLI command with output option."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with output
        result = self.runner.invoke(ai, ["export", "--output", "test.json"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(output="test.json")

    @patch("commands.ai.AICleanupCommand")
    def test_ai_cleanup_cli_with_days(self, mock_command_class: MagicMock) -> None:
        """Test ai cleanup CLI command with days option."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with days
        result = self.runner.invoke(ai, ["cleanup", "--days", "7"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(days=7)

    @patch("commands.ai.AIPredictCommand")
    def test_ai_predict_cli(self, mock_command_class: MagicMock) -> None:
        """Test ai predict CLI command."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with prompt text
        result = self.runner.invoke(ai, ["predict", "test prompt"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(prompt_text="test prompt", context="", project=None)

    @patch("commands.ai.AdaptiveResponse")
    def test_ai_status_validate_preconditions_failure(self, mock_adaptive: MagicMock) -> None:
        """Test AIStatusCommand validate_preconditions handles initialization failure."""
        mock_adaptive.side_effect = Exception("Initialization failed")

        with patch.object(AIStatusCommand, '__init__', lambda x: None):
            command = AIStatusCommand()
            
            with pytest.raises(CommandError) as exc_info:
                command.validate_preconditions()

            assert "Failed to initialize AI components" in str(exc_info.value)

    @patch("commands.ai.AdaptiveResponse")
    def test_ai_status_execute_success(self, mock_adaptive: MagicMock) -> None:
        """Test AIStatusCommand execute returns learning statistics."""
        # Setup mocks
        mock_adaptive_instance = MagicMock()
        mock_adaptive.return_value = mock_adaptive_instance
        mock_stats = {
            "total_responses": 100,
            "total_patterns": 50,
            "recent_activity": 10,
            "adaptive_config": {"auto_response_enabled": True, "learning_enabled": True, "min_confidence_threshold": 0.8},
            "runtime_info": {"response_queue_size": 5, "cache_size": 20}
        }
        mock_adaptive_instance.get_learning_statistics.return_value = mock_stats

        with patch.object(AIStatusCommand, '__init__', lambda x: None):
            command = AIStatusCommand()
            command.console = MagicMock()
            command.adaptive = mock_adaptive_instance

            result = command.execute()

            assert result == mock_stats
            command.console.print.assert_called()

    @patch("commands.ai.AdaptiveResponse")
    def test_ai_config_execute_with_threshold(self, mock_adaptive: MagicMock) -> None:
        """Test AIConfigCommand execute with threshold parameter."""
        # Setup mocks
        mock_adaptive_instance = MagicMock()
        mock_adaptive.return_value = mock_adaptive_instance

        with patch.object(AIConfigCommand, '__init__', lambda x: None):
            command = AIConfigCommand()
            command.console = MagicMock()
            command.adaptive = mock_adaptive_instance
            command.print_success = MagicMock()

            result = command.execute(threshold=0.7)

            assert result == {"changes": ["Confidence threshold set to 0.70"]}
            mock_adaptive_instance.adjust_confidence_threshold.assert_called_once_with(0.7)
            command.print_success.assert_called_once()

    @patch("commands.ai.AdaptiveResponse")
    def test_ai_config_execute_invalid_threshold(self, mock_adaptive: MagicMock) -> None:
        """Test AIConfigCommand execute with invalid threshold."""
        with patch.object(AIConfigCommand, '__init__', lambda x: None):
            command = AIConfigCommand()
            command.adaptive = MagicMock()

            with pytest.raises(CommandError) as exc_info:
                command.execute(threshold=1.5)

            assert "Threshold must be between 0.0 and 1.0" in str(exc_info.value)

    @patch("commands.ai.ResponseAnalyzer")
    def test_ai_history_execute_success(self, mock_analyzer: MagicMock) -> None:
        """Test AIHistoryCommand execute returns response history."""
        # Setup mock response records
        mock_record = MagicMock()
        mock_record.timestamp = 1000000000.0
        mock_record.prompt_type = "command"
        mock_record.prompt_text = "test prompt"
        mock_record.user_response = "yes"
        mock_record.project_name = "test-project"

        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.response_history = [mock_record]
        mock_analyzer.return_value = mock_analyzer_instance

        with patch.object(AIHistoryCommand, '__init__', lambda x: None):
            command = AIHistoryCommand()
            command.console = MagicMock()
            command.analyzer = mock_analyzer_instance

            result = command.execute(limit=10)

            assert result["history"] == [mock_record]
            command.console.print.assert_called()

    @patch("commands.ai.AdaptiveResponse")
    @patch("commands.ai.Path")
    def test_ai_export_execute_success(self, mock_path: MagicMock, mock_adaptive: MagicMock) -> None:
        """Test AIExportCommand execute successful export."""
        # Setup mocks
        mock_adaptive_instance = MagicMock()
        mock_adaptive_instance.export_learning_data.return_value = True
        mock_adaptive.return_value = mock_adaptive_instance

        mock_path_instance = MagicMock()
        mock_path_instance.__str__ = lambda x: "test_export.json"
        mock_path.return_value = mock_path_instance

        with patch.object(AIExportCommand, '__init__', lambda x: None):
            command = AIExportCommand()
            command.console = MagicMock()
            command.adaptive = mock_adaptive_instance
            command.print_success = MagicMock()

            result = command.execute(output="test_export.json")

            assert result["success"] is True
            assert "test_export.json" in result["output_path"]
            command.print_success.assert_called_once()

    @patch("commands.ai.ResponseAnalyzer")
    def test_ai_cleanup_execute_success(self, mock_analyzer: MagicMock) -> None:
        """Test AICleanupCommand execute successful cleanup."""
        # Setup mocks
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.cleanup_old_data.return_value = 15
        mock_analyzer.return_value = mock_analyzer_instance

        with patch.object(AICleanupCommand, '__init__', lambda x: None):
            command = AICleanupCommand()
            command.console = MagicMock()
            command.analyzer = mock_analyzer_instance
            command.print_success = MagicMock()

            result = command.execute(days=7)

            assert result == {"removed_count": 15, "days_kept": 7}
            command.print_success.assert_called_once()

    @patch("commands.ai.AdaptiveResponse")
    @patch("commands.ai.asyncio.run")
    def test_ai_predict_execute_success(self, mock_asyncio_run: MagicMock, mock_adaptive: MagicMock) -> None:
        """Test AIPredictCommand execute successful prediction."""
        # Setup mocks
        mock_adaptive_instance = MagicMock()
        mock_adaptive.return_value = mock_adaptive_instance
        mock_asyncio_run.return_value = (True, "Predicted response", 0.85)

        with patch.object(AIPredictCommand, '__init__', lambda x: None):
            command = AIPredictCommand()
            command.console = MagicMock()
            command.adaptive = mock_adaptive_instance

            result = command.execute(prompt_text="test prompt", context="test context", project="test-project")

            expected = {
                "should_respond": True,
                "predicted_response": "Predicted response",
                "confidence": 0.85
            }
            assert result == expected
            command.console.print.assert_called()