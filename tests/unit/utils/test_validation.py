#!/usr/bin/env python3

# Copyright notice.

import pytest

# Licensed under the MIT License

"""Tests for validation utilities."""

from libs.validation import (
    ValidationError,
    validate_input,
    validate_log_level,
    validate_pane_command,
    validate_port_number,
    validate_session_name,
    validate_window_name,
)


class TestValidationFunctions:
    """Test validation functions."""

    @staticmethod
    def test_validate_session_name_valid() -> None:
        """Test valid session names."""
        valid_names = [
            "my-session",
            "my_session",
            "session123",
            "test_123_session",
            "a",  # single character
        ]
        for name in valid_names:
            valid, error = validate_session_name(name)
            assert valid is True, f"'{name}' should be valid"
            assert error is None

    @staticmethod
    def test_validate_session_name_invalid() -> None:
        """Test invalid session names."""
        invalid_cases = [
            ("", "Session name cannot be empty"),
            ("my session", "contains invalid characters"),
            ("123session", "cannot start with a number"),
            ("session@name", "contains invalid characters"),
            ("a" * 65, "exceeds maximum length"),
            ("session.name", "contains invalid characters"),
        ]
        for name, expected_error in invalid_cases:
            valid, error = validate_session_name(name)
            assert valid is False, f"'{name}' should be invalid"
            assert expected_error in error

    @staticmethod
    def test_validate_window_name_valid() -> None:
        """Test valid window names."""
        valid_names = [
            "my-window",
            "my_window",
            "window 123",  # spaces allowed
            "test window name",
        ]
        for name in valid_names:
            valid, error = validate_window_name(name)
            assert valid is True, f"'{name}' should be valid"
            assert error is None

    @staticmethod
    def test_validate_window_name_invalid() -> None:
        """Test invalid window names."""
        invalid_cases = [
            ("", "Window name cannot be empty"),
            ("window@name", "contains invalid characters"),
            ("a" * 33, "exceeds maximum length"),
        ]
        for name, expected_error in invalid_cases:
            valid, error = validate_window_name(name)
            assert valid is False, f"'{name}' should be invalid"
            assert expected_error in error

    @staticmethod
    def test_validate_pane_command_valid() -> None:
        """Test valid pane commands."""
        valid_commands = [
            "",  # empty is valid
            "vim",
            "python script.py",
            "cd /home/user && ls -la",
        ]
        for cmd in valid_commands:
            valid, error = validate_pane_command(cmd)
            assert valid is True, f"'{cmd}' should be valid"
            assert error is None

    @staticmethod
    def test_validate_pane_command_invalid() -> None:
        """Test invalid/dangerous pane commands."""
        invalid_cases = [
            ("rm -rf /", "dangerous pattern"),
            (":() { :|:& };:", "dangerous pattern"),  # fork bomb
            ("a" * 1025, "exceeds maximum length"),
        ]
        for cmd, expected_error in invalid_cases:
            valid, error = validate_pane_command(cmd)
            assert valid is False, f"'{cmd}' should be invalid"
            assert expected_error in error

    @staticmethod
    def test_validate_port_number_valid() -> None:
        """Test valid port numbers."""
        valid_ports = ["80", "443", "8080", "3000", "65535"]
        for port in valid_ports:
            valid, error = validate_port_number(port)
            assert valid is True, f"'{port}' should be valid"

    @staticmethod
    def test_validate_port_number_invalid() -> None:
        """Test invalid port numbers."""
        invalid_cases = [
            ("", "cannot be empty"),
            ("0", "must be between"),
            ("65536", "must be between"),
            ("abc", "must be a number"),
            ("-1", "must be a number"),
        ]
        for port, expected_error in invalid_cases:
            valid, error = validate_port_number(port)
            assert valid is False, f"'{port}' should be invalid"
            assert expected_error in error

    @staticmethod
    def test_validate_port_privileged_warning() -> None:
        """Test privileged port warning."""
        valid, message = validate_port_number("22")
        assert valid is True
        assert "root privileges" in message

    @staticmethod
    def test_validate_log_level_valid() -> None:
        """Test valid log levels."""
        valid_levels = [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
            "debug",
            "info",
        ]
        for level in valid_levels:
            valid, error = validate_log_level(level)
            assert valid is True, f"'{level}' should be valid"
            assert error is None

    @staticmethod
    def test_validate_log_level_invalid() -> None:
        """Test invalid log levels."""
        invalid_cases = [
            ("", "cannot be empty"),
            ("TRACE", "Invalid log level"),
            ("invalid", "Invalid log level"),
        ]
        for level, expected_error in invalid_cases:
            valid, error = validate_log_level(level)
            assert valid is False, f"'{level}' should be invalid"
            assert expected_error in error


class TestValidationDecorator:
    """Test validation decorator."""

    @staticmethod
    def test_validate_input_decorator_success() -> None:
        """Test decorator with valid input."""

        @validate_input(validate_session_name, "session_name")
        def create_session(session_name: str) -> str:
            return f"Created {session_name}"

        result = create_session("my-session")
        assert result == "Created my-session"

    @staticmethod
    def test_validate_input_decorator_failure() -> None:
        """Test decorator with invalid input."""

        @validate_input(validate_session_name, "session_name")
        def create_session(session_name: str) -> str:
            return f"Created {session_name}"

        with pytest.raises(ValidationError) as exc_info:
            create_session("invalid session")

        assert exc_info.value.field == "session_name"
        assert "invalid characters" in str(exc_info.value)

    @staticmethod
    def test_validate_input_decorator_kwargs() -> None:
        """Test decorator with keyword arguments."""

        @validate_input(validate_port_number, "port")
        def start_server(host: str = "localhost", port: str = "8080") -> str:
            return f"Server on {host}:{port}"

        result = start_server(port="3000")
        assert result == "Server on localhost:3000"

        with pytest.raises(ValidationError):
            start_server(port="invalid")
