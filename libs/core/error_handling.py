import hashlib
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

# !/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Centralized error handling and exception management."""


class ErrorCategory(Enum):
    """Categories of errors for better classification."""

    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    SYSTEM = "system"
    NETWORK = "network"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    USER_INPUT = "user_input"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for errors."""

    operation: str
    component: str
    session_name: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    additional_info: dict[str, object] | None = None


class YesmanError(Exception):
    """Base exception class for all Yesman errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: ErrorContext | None = None,
        cause: Exception | None = None,
        exit_code: int = 1,
        recovery_hint: str | None = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context
        self.cause = cause
        self.exit_code = exit_code
        self.recovery_hint = recovery_hint
        self.error_code = error_code or self._generate_error_code()
        super().__init__(message)

    def _generate_error_code(self) -> str:
        """Generate error code from category and message."""
        # Create a simple error code from category and hash of message
        msg_hash = hashlib.sha256(self.message.encode()).hexdigest()[:8].upper()
        return f"{self.category.value.upper()}_{msg_hash}"

    def to_dict(self) -> dict[str, object]:
        """Convert error to dictionary for logging/serialization."""
        result: dict[str, object] = {
            "code": self.error_code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "recovery_hint": self.recovery_hint,
        }

        # Add context if available
        if self.context:
            context_dict: dict[str, object] = {
                "operation": self.context.operation,
                "component": self.context.component,
            }
            if self.context.session_name:
                context_dict["session_name"] = self.context.session_name
            if self.context.file_path:
                context_dict["file_path"] = self.context.file_path
            if self.context.line_number:
                context_dict["line_number"] = self.context.line_number
            if self.context.additional_info:
                context_dict.update(self.context.additional_info)
            result["context"] = context_dict

        # Add cause if available
        if self.cause:
            result["cause"] = str(self.cause)

        return result


class ConfigurationError(YesmanError):
    """Configuration-related errors."""

    def __init__(self, message: str, config_file: str | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        context = ErrorContext(
            operation="configuration_loading",
            component="config",
            file_path=config_file,
        )

        # Set default recovery hint if not provided
        if "recovery_hint" not in kwargs:
            kwargs["recovery_hint"] = "Check the configuration file syntax and ensure all required fields are present. Run 'yesman validate' to check configuration."

        # Remove context from kwargs if it exists to avoid conflict
        kwargs.pop("context", None)

        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            context=context,
            **kwargs,
        )


class ValidationError(YesmanError):
    """Validation-related errors."""

    def __init__(self, message: str, field_name: str | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        context = ErrorContext(
            operation="validation",
            component="validator",
            additional_info={"field_name": field_name} if field_name else None,
        )

        # Set default recovery hint if not provided
        if "recovery_hint" not in kwargs:
            if field_name:
                kwargs["recovery_hint"] = f"Check the value of '{field_name}' field and ensure it meets the requirements."
            else:
                kwargs["recovery_hint"] = "Review the input data and ensure all values meet the validation requirements."

        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            context=context,
            **kwargs,
        )


class SessionError(YesmanError):
    """Session management related errors."""

    def __init__(self, message: str, session_name: str | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        context = ErrorContext(
            operation="session_management",
            component="tmux_manager",
            session_name=session_name,
        )

        # Set default recovery hint if not provided
        if "recovery_hint" not in kwargs:
            if session_name:
                kwargs["recovery_hint"] = f"Check if session '{session_name}' exists using 'yesman show'. If not, create it with 'yesman enter {{session_name}}'."
            else:
                kwargs["recovery_hint"] = "List available sessions with 'yesman show' or check tmux directly with 'tmux ls'."

        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            context=context,
            **kwargs,
        )


class NetworkError(YesmanError):
    """Network-related errors."""

    def __init__(self, message: str, endpoint: str | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        context = ErrorContext(
            operation="network_operation",
            component="api_client",
            additional_info={"endpoint": endpoint} if endpoint else None,
        )
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            context=context,
            **kwargs,
        )


class PermissionError(YesmanError):
    """Permission-related errors."""

    def __init__(self, message: str, resource_path: str | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        context = ErrorContext(
            operation="permission_check",
            component="filesystem",
            file_path=resource_path,
        )
        super().__init__(
            message,
            category=ErrorCategory.PERMISSION,
            context=context,
            **kwargs,
        )


class TimeoutError(YesmanError):
    """Timeout-related errors."""

    def __init__(self, message: str, timeout_duration: float | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        context = ErrorContext(
            operation="timeout_operation",
            component="timeout_handler",
            additional_info=({"timeout_duration": timeout_duration} if timeout_duration else None),
        )
        super().__init__(
            message,
            category=ErrorCategory.TIMEOUT,
            context=context,
            **kwargs,
        )


class ErrorHandler:
    """Centralized error handling and reporting."""

    def __init__(self, logger_name: str = "yesman.error_handler") -> None:
        self.logger = logging.getLogger(logger_name)
        self.error_stats: dict[str, Any] = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {},
            "by_component": {},
        }

    def handle_error(
        self,
        error: YesmanError | Exception,
        context: ErrorContext | None = None,
        log_traceback: bool = True,  # noqa: FBT001
        exit_on_critical: bool = True,  # noqa: FBT001
    ) -> None:
        """Handle an error with logging and optional exit.

        Args:
            error: The error to handle
            context: Additional context if error is not YesmanError
            log_traceback: Whether to log full traceback
            exit_on_critical: Whether to exit on critical errors
        """
        # Convert to YesmanError if needed
        yesman_error = YesmanError(message=str(error), context=context, cause=error) if not isinstance(error, YesmanError) else error

        # Update statistics
        self._update_error_stats(yesman_error)

        # Log error
        self._log_error(yesman_error, log_traceback)

        # Handle critical errors
        if yesman_error.severity == ErrorSeverity.CRITICAL and exit_on_critical:
            self._handle_critical_error(yesman_error)

    def _update_error_stats(self, error: YesmanError) -> None:
        """Update error statistics."""
        self.error_stats["total_errors"] += 1

        # By category
        category = error.category.value
        self.error_stats["by_category"][category] = self.error_stats["by_category"].get(category, 0) + 1

        # By severity
        severity = error.severity.value
        self.error_stats["by_severity"][severity] = self.error_stats["by_severity"].get(severity, 0) + 1

        # By component
        if error.context and error.context.component:
            component = error.context.component
            self.error_stats["by_component"][component] = self.error_stats["by_component"].get(component, 0) + 1

    def _log_error(self, error: YesmanError, log_traceback: bool) -> None:  # noqa: FBT001
        """Log error with appropriate level."""
        # Determine log level
        level_map = {
            ErrorSeverity.LOW: logging.WARNING,
            ErrorSeverity.MEDIUM: logging.ERROR,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }
        log_level = level_map.get(error.severity, logging.ERROR)

        # Format error message
        message_parts = [f"[{error.category.value.upper()}] {error.message}"]

        if error.context:
            context_info = []
            if error.context.operation:
                context_info.append(f"operation={error.context.operation}")
            if error.context.component:
                context_info.append(f"component={error.context.component}")
            if error.context.session_name:
                context_info.append(f"session={error.context.session_name}")
            if error.context.file_path:
                context_info.append(f"file={error.context.file_path}")

            if context_info:
                message_parts.append(f"Context: {', '.join(context_info)}")

        if error.cause:
            message_parts.append(f"Caused by: {error.cause}")

        log_message = " | ".join(message_parts)

        # Log the error
        self.logger.log(log_level, log_message)

        # Log traceback if requested and available
        if log_traceback and error.cause:
            self.logger.debug("Full traceback:", exc_info=error.cause)

    def _handle_critical_error(self, error: YesmanError) -> None:
        """Handle critical errors."""
        self.logger.critical(f"CRITICAL ERROR - System exiting: {error.message}")  # noqa: G004

        # Print user-friendly error message
        if error.context and error.context.operation:
            pass

        sys.exit(error.exit_code)

    def get_error_summary(self) -> dict[str, object]:
        """Get error statistics summary."""
        return self.error_stats.copy()

    def reset_stats(self) -> None:
        """Reset error statistics."""
        self.error_stats = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {},
            "by_component": {},
        }


# Global error handler instance
error_handler = ErrorHandler()


def handle_exceptions(func: Callable[..., object]) -> Callable[..., object]:
    """Decorator for automatic exception handling."""

    def wrapper(*args: Any, **kwargs: Any) -> object:  # noqa: ANN401
        try:
            return func(*args, **kwargs)
        except YesmanError as e:
            error_handler.handle_error(e)
            return None
        except Exception as e:
            # Create context from function
            context = ErrorContext(
                operation=func.__name__,
                component=(func.__module__.split(".")[-1] if hasattr(func, "__module__") else "unknown"),
            )
            error_handler.handle_error(e, context)
            return None

    return wrapper


def safe_execute(
    operation: str,
    component: str,
    func: Callable[..., object],
    *args: Any,  # noqa: ANN401
    error_category: ErrorCategory = ErrorCategory.UNKNOWN,
    **kwargs: Any,  # noqa: ANN401
) -> object:
    """Safely execute a function with error handling.

    Args:
        operation: Description of the operation
        component: Component performing the operation
        func: Function to execute
        *args: Function arguments
        error_category: Category of potential errors
        **kwargs: Function keyword arguments

    Returns:
        Function result or None on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        context = ErrorContext(
            operation=operation,
            component=component,
        )

        yesman_error = YesmanError(
            message=f"Failed to execute {operation}: {e!s}",
            category=error_category,
            context=context,
            cause=e,
        )

        error_handler.handle_error(yesman_error, exit_on_critical=False)
        return None
