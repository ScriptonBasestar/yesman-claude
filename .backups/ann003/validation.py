import os
import re
from pathlib import Path
from typing import Any

from libs.core.settings import ContentLimits, ValidationPatterns

# !/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Centralized validation utilities for the Yesman-Claude project.

This module provides common validation functions used throughout the project
for validating session names, project names, paths, and other inputs.
"""


class ValidationError(Exception):
    """Custom exception for validation errors with detailed messages."""

    def __init__(self, field: str, value: str, reason: str) -> None:
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for {field}: {reason}")


def validate_session_name(name: str, max_length: int | None = None) -> tuple[bool, str | None]:
    """Validate tmux session name.

    Args:
        name: Session name to validate
        max_length: Maximum allowed length (defaults to ContentLimits.MAX_SESSION_NAME_LENGTH)

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_session_name("my-session")
        (True, None)
        >>> validate_session_name("my session")
        (False, "Session name contains invalid characters")
    """
    if not name:
        return False, "Session name cannot be empty"

    # Check length
    max_len = max_length or ContentLimits.MAX_SESSION_NAME_LENGTH
    if len(name) > max_len:
        return False, f"Session name exceeds maximum length of {max_len} characters"

    # Check pattern
    if not re.match(ValidationPatterns.SESSION_NAME, name):
        return False, ("Session name contains invalid characters. Only letters, numbers, underscores, and hyphens are allowed")

    # Check if it starts with a number (tmux restriction)
    if name[0].isdigit():
        return False, "Session name cannot start with a number"

    return True, None


def validate_project_name(name: str) -> tuple[bool, str | None]:
    """Validate project name.

    Project names have the same rules as session names.

    Args:
        name: Project name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_session_name(name)


def validate_window_name(name: str, max_length: int | None = None) -> tuple[bool, str | None]:
    """Validate tmux window name.

    Args:
        name: Window name to validate
        max_length: Maximum allowed length (defaults to ContentLimits.MAX_WINDOW_NAME_LENGTH)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Window name cannot be empty"

    # Check length
    max_len = max_length or ContentLimits.MAX_WINDOW_NAME_LENGTH
    if len(name) > max_len:
        return False, f"Window name exceeds maximum length of {max_len} characters"

    # Check pattern (windows allow spaces)
    if not re.match(ValidationPatterns.WINDOW_NAME, name):
        return False, ("Window name contains invalid characters. Only letters, numbers, underscores, hyphens, and spaces are allowed")

    return True, None


def validate_pane_command(command: str, max_length: int | None = None) -> tuple[bool, str | None]:
    """Validate pane command.

    Args:
        command: Command to validate
        max_length: Maximum allowed length (defaults to ContentLimits.MAX_COMMAND_LENGTH)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not command:
        # Empty command is valid (opens default shell)
        return True, None

    # Check length
    max_len = max_length or ContentLimits.MAX_COMMAND_LENGTH
    if len(command) > max_len:
        return False, f"Command exceeds maximum length of {max_len} characters"

    # Basic security checks
    dangerous_patterns = [
        r";\s*rm\s+-rf\s+/",  # rm -rf /
        r">\s*/dev/sda",  # write to disk device
        r":()\s*{\s*:\|:&\s*};",  # fork bomb
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False, "Command contains potentially dangerous pattern"

    return True, None


def validate_template_exists(template_name: str, templates_dir: str | None = None) -> tuple[bool, str | None]:
    """Check if template exists.

    Args:
        template_name: Name of the template (without extension)
        templates_dir: Directory containing templates (defaults to 'templates')

    Returns:
        Tuple of (exists, error_message)
    """
    if not template_name:
        return False, "Template name cannot be empty"

    # Get templates directory
    if templates_dir is None:
        templates_dir = os.environ.get("YESMAN_TEMPLATES_DIR", "templates")

    template_path = Path(templates_dir) / f"{template_name}.yaml"

    if not template_path.exists():
        return False, f"Template '{template_name}' not found at {template_path}"

    if not template_path.is_file():
        return False, f"Template path '{template_path}' is not a file"

    return True, None


def validate_directory_path(path: str, must_exist: bool = True, create_if_missing: bool = False) -> tuple[bool, str | None]:
    """Validate directory path.

    Args:
        path: Directory path to validate
        must_exist: Whether the directory must already exist
        create_if_missing: Whether to create the directory if it doesn't exist

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Directory path cannot be empty"

    # Expand user home directory
    expanded_path = Path(path).expanduser()
    path_obj = Path(expanded_path)

    # Check if it's an absolute path or can be resolved
    try:
        resolved_path = path_obj.resolve()
    except Exception as e:
        return False, f"Invalid path: {e}"

    if must_exist:
        if not resolved_path.exists():
            if create_if_missing:
                try:
                    resolved_path.mkdir(parents=True, exist_ok=True)
                    return True, None
                except Exception as e:
                    return False, f"Failed to create directory: {e}"
            else:
                return False, f"Directory does not exist: {resolved_path}"

        if not resolved_path.is_dir():
            return False, f"Path exists but is not a directory: {resolved_path}"

    return True, None


def validate_port_number(port: str) -> tuple[bool, str | None]:
    """Validate port number.

    Args:
        port: Port number as string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not port:
        return False, "Port number cannot be empty"

    # Check if it matches the pattern
    if not re.match(ValidationPatterns.PORT_NUMBER, port):
        return False, "Port must be a number between 1 and 65535"

    # Check range
    port_num = int(port)
    if port_num < 1 or port_num > 65535:
        return False, "Port must be between 1 and 65535"

    # Warn about privileged ports
    if port_num < 1024:
        # This is a warning, not an error
        return True, "Note: Port numbers below 1024 require root privileges"

    return True, None


def validate_log_level(level: str) -> tuple[bool, str | None]:
    """Validate log level.

    Args:
        level: Log level string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not level:
        return False, "Log level cannot be empty"

    # Check pattern
    if not re.match(ValidationPatterns.LOG_LEVEL, level.upper()):
        return (
            False,
            "Invalid log level. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL",
        )

    return True, None


def validate_session_config(config: dict) -> tuple[bool, list[str]]:
    """Validate a complete session configuration.

    Args:
        config: Session configuration dictionary

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Validate session name
    session_name = config.get("name", "")
    valid, error = validate_session_name(session_name)
    if not valid:
        errors.append(f"Session name: {error}")

    # Validate windows
    windows = config.get("windows", [])
    if not windows:
        errors.append("Session must have at least one window")
    elif len(windows) > ContentLimits.MAX_WINDOWS_PER_SESSION:
        errors.append(f"Too many windows (max: {ContentLimits.MAX_WINDOWS_PER_SESSION})")
    else:
        # Validate each window
        for i, window in enumerate(windows):
            window_name = window.get("window_name", f"window_{i}")
            valid, error = validate_window_name(window_name)
            if not valid:
                errors.append(f"Window '{window_name}': {error}")

            # Validate panes
            panes = window.get("panes", [])
            if len(panes) > ContentLimits.MAX_PANES_PER_WINDOW:
                errors.append(f"Window '{window_name}': Too many panes (max: {ContentLimits.MAX_PANES_PER_WINDOW})")

    # Validate start directory
    start_dir = config.get("start_directory", "")
    if start_dir:
        valid, error = validate_directory_path(start_dir, must_exist=True)
        if not valid:
            errors.append(f"Start directory: {error}")

    return len(errors) == 0, errors


# Validation decorators for common use cases
def validate_input(validation_func: object, field_name: str) -> object:
    """Decorator to validate function inputs.

    Args:
        validation_func: Validation function to use
        field_name: Name of the field being validated

    Example:
        @validate_input(validate_session_name, "session_name")
        def create_session(session_name: str) -> object:
            pass

    Returns:
        Description of return value
    """

    def decorator(func: Any) -> object:
        def wrapper(*args, **kwargs) -> object:
            # Get the value to validate
            if field_name in kwargs:
                value = kwargs[field_name]
            # Assume it's the first positional argument
            elif args:
                value = args[0]
            else:
                msg = f"Missing required argument: {field_name}"
                raise ValueError(msg)

            # Validate
            valid, error = validation_func(value)
            if not valid:
                raise ValidationError(field_name, str(value), error)

            return func(*args, **kwargs)

        return wrapper

    return decorator
