# Copyright notice.

from fastapi import status

from api.middleware.error_handler import create_error_response, error_to_status_code
from libs.core.error_handling import (
    ConfigurationError,
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    SessionError,
    ValidationError,
    YesmanError,
)


class TestYesmanError:
    """Test YesmanError base class."""

    @staticmethod
    def test_basic_error_creation() -> None:
        """Test basic error creation."""
        error = YesmanError("Test error")

        assert error.message == "Test error"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.error_code.startswith("UNKNOWN_")

    @staticmethod
    def test_error_with_context() -> None:
        """Test error with context."""
        context = ErrorContext(
            operation="test_operation",
            component="test_component",
            session_name="test_session",
        )

        error = YesmanError(
            "Test error",
            category=ErrorCategory.SYSTEM,
            context=context,
            recovery_hint="Try restarting the service",
        )

        assert error.context.operation == "test_operation"
        assert error.recovery_hint == "Try restarting the service"

    @staticmethod
    def test_error_to_dict() -> None:
        """Test error serialization."""
        context = ErrorContext(operation="test_operation", component="test_component")

        error = YesmanError(
            "Test error",
            category=ErrorCategory.VALIDATION,
            context=context,
            recovery_hint="Check your input",
        )

        error_dict = error.to_dict()

        assert error_dict["message"] == "Test error"
        assert error_dict["category"] == "validation"
        assert error_dict["recovery_hint"] == "Check your input"
        assert error_dict["context"]["operation"] == "test_operation"


class TestSpecificErrors:
    """Test specific error types."""

    @staticmethod
    def test_configuration_error() -> None:
        """Test ConfigurationError."""
        error = ConfigurationError(
            "Invalid config file", config_file="/path/to/config.yaml"
        )

        assert error.category == ErrorCategory.CONFIGURATION
        assert error.context.file_path == "/path/to/config.yaml"
        assert "configuration" in error.recovery_hint.lower()

    @staticmethod
    def test_session_error() -> None:
        """Test SessionError."""
        error = SessionError("Session not found", session_name="my-session")

        assert error.category == ErrorCategory.SYSTEM
        assert error.context.session_name == "my-session"
        assert "my-session" in error.recovery_hint

    @staticmethod
    def test_validation_error() -> None:
        """Test ValidationError."""
        error = ValidationError("Invalid field value", field_name="email")

        assert error.category == ErrorCategory.VALIDATION
        assert error.context.additional_info["field_name"] == "email"
        assert "email" in error.recovery_hint


class TestErrorHandler:
    """Test ErrorHandler class."""

    @staticmethod
    def test_error_stats_tracking() -> None:
        """Test error statistics tracking."""
        handler = ErrorHandler()

        # Create some errors
        config_error = ConfigurationError("Config error")
        session_error = SessionError("Session error")

        # Handle errors (without exiting)
        handler.handle_error(config_error, exit_on_critical=False)
        handler.handle_error(session_error, exit_on_critical=False)

        stats = handler.get_error_summary()

        assert stats["total_errors"] == 2
        assert stats["by_category"]["configuration"] == 1
        assert stats["by_category"]["system"] == 1

    @staticmethod
    def test_error_context_creation() -> None:
        """Test automatic context creation for non-YesmanError."""
        handler = ErrorHandler()

        # Create a regular exception
        regular_error = ValueError("Regular error")
        context = ErrorContext(operation="test_op", component="test_comp")

        # This should not raise an exception
        handler.handle_error(regular_error, context, exit_on_critical=False)

        stats = handler.get_error_summary()
        assert stats["total_errors"] == 1


class TestAPIErrorHandling:
    """Test API error handling middleware."""

    @staticmethod
    def test_error_to_status_code_mapping() -> None:
        """Test error to HTTP status code mapping."""
        # Test validation error
        validation_error = ValidationError("Invalid input")
        assert error_to_status_code(validation_error) == status.HTTP_400_BAD_REQUEST

        # Test configuration error
        config_error = ConfigurationError("Config error")
        assert (
            error_to_status_code(config_error) == status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        # Test session error
        session_error = SessionError("Session not found")
        assert error_to_status_code(session_error) == status.HTTP_404_NOT_FOUND

    @staticmethod
    def test_error_response_creation() -> None:
        """Test standardized error response creation."""
        response = create_error_response(
            code="TEST_ERROR",
            message="Test error message",
            status_code=400,
            recovery_hint="Try again",
            context={"field": "value"},
            request_id="test-123",
        )

        assert response.status_code == 400

        # Parse JSON content

        content = json.loads(response.body)

        assert content["error"]["code"] == "TEST_ERROR"
        assert content["error"]["message"] == "Test error message"
        assert content["error"]["recovery_hint"] == "Try again"
        assert content["error"]["context"]["field"] == "value"
        assert content["error"]["request_id"] == "test-123"


class TestErrorRecoveryHints:
    """Test error recovery hints."""

    @staticmethod
    def test_default_recovery_hints() -> None:
        """Test that specific errors have appropriate recovery hints."""
        # Configuration error
        config_error = ConfigurationError("Missing required field")
        assert "validate" in config_error.recovery_hint.lower()

        # Session error with session name
        session_error = SessionError("Session not found", session_name="test-session")
        assert "test-session" in session_error.recovery_hint
        assert "yesman show" in session_error.recovery_hint

        # Validation error with field name
        validation_error = ValidationError("Invalid value", field_name="port")
        assert "port" in validation_error.recovery_hint

    @staticmethod
    def test_custom_recovery_hints() -> None:
        """Test custom recovery hints override defaults."""
        custom_hint = "Custom recovery instructions"
        error = ConfigurationError("Config error", recovery_hint=custom_hint)

        assert error.recovery_hint == custom_hint


class TestErrorCodes:
    """Test error code generation."""

    @staticmethod
    def test_error_code_generation() -> None:
        """Test that error codes are generated consistently."""
        error1 = YesmanError("Same message", category=ErrorCategory.VALIDATION)
        error2 = YesmanError("Same message", category=ErrorCategory.VALIDATION)

        # Same message and category should generate same code
        assert error1.error_code == error2.error_code

        # Different categories should generate different codes
        error3 = YesmanError("Same message", category=ErrorCategory.SYSTEM)
        assert error1.error_code != error3.error_code

    @staticmethod
    def test_custom_error_codes() -> None:
        """Test custom error codes."""
        custom_code = "CUSTOM_ERROR_123"
        error = YesmanError("Test", error_code=custom_code)

        assert error.error_code == custom_code


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @staticmethod
    def test_command_error_flow() -> None:
        """Test error flow from command to API response."""
        # Simulate a command raising a SessionError
        session_error = SessionError(
            "Session 'myproject' not found", session_name="myproject"
        )

        # Convert to API response
        status_code = error_to_status_code(session_error)
        error_dict = session_error.to_dict()

        assert status_code == status.HTTP_404_NOT_FOUND
        assert "myproject" in error_dict["message"]
        assert "myproject" in error_dict["recovery_hint"]
        assert error_dict["context"]["session_name"] == "myproject"

    @staticmethod
    def test_validation_error_with_multiple_fields() -> None:
        """Test validation error with complex context."""
        error = ValidationError(
            "Multiple validation errors", field_name="config.tmux.port"
        )

        error_dict = error.to_dict()

        assert error_dict["category"] == "validation"
        assert "config.tmux.port" in error_dict["recovery_hint"]
