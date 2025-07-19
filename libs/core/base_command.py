#!/usr/bin/env python3
"""Base command class with common functionality."""

import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import click

from ..tmux_manager import TmuxManager
from ..yesman_config import YesmanConfig
from .claude_manager import ClaudeManager
from .error_handling import (
    ConfigurationError,
    ErrorContext,
    ErrorSeverity,
    YesmanError,
    error_handler,
)
from .services import get_config, get_tmux_manager, initialize_services
from .settings import settings


class CommandError(YesmanError):
    """Command-specific error."""

    def __init__(
        self,
        message: str,
        exit_code: int = 1,
        recovery_hint: str | None = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            exit_code=exit_code,
            recovery_hint=recovery_hint,
            **kwargs,
        )


class BaseCommand(ABC):
    """Base class for all yesman commands."""

    def __init__(
        self,
        config: YesmanConfig | None = None,
        tmux_manager: TmuxManager | None = None,
        claude_manager: ClaudeManager | None = None,
    ):
        """Initialize base command with dependency injection support.

        Args:
            config: YesmanConfig instance (will use DI container if None)
            tmux_manager: TmuxManager instance (will use DI container if None)
            claude_manager: ClaudeManager instance (will be created if None)
        """
        self.logger = self._setup_logger()

        # Ensure services are initialized
        initialize_services()

        # Initialize dependencies - use DI container if not provided
        self.config = config or self._resolve_config()
        self.tmux_manager = tmux_manager or self._resolve_tmux_manager()
        self.claude_manager = claude_manager or self._create_claude_manager()

        # Ensure required directories exist
        settings.ensure_directories()

    def _setup_logger(self) -> logging.Logger:
        """Set up logger for this command."""
        logger = logging.getLogger(f"yesman.{self.__class__.__name__.lower()}")

        if not logger.handlers:
            # Configure logger if not already configured
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(settings.logging.format)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        logger.setLevel(getattr(logging, settings.logging.level))
        return logger

    def _resolve_config(self) -> YesmanConfig:
        """Resolve YesmanConfig from DI container with error handling."""
        try:
            return get_config()
        except Exception as e:
            context = ErrorContext(
                operation="resolve_config",
                component=self.__class__.__name__,
            )
            raise ConfigurationError(
                f"Failed to resolve configuration from DI container: {e}",
                context=context,
                cause=e,
                recovery_hint="Check if the DI container is properly initialized",
            ) from e

    def _resolve_tmux_manager(self) -> TmuxManager:
        """Resolve TmuxManager from DI container with error handling."""
        try:
            return get_tmux_manager()
        except Exception as e:
            self.logger.error(f"Failed to resolve tmux manager from DI container: {e}")
            raise CommandError(f"Tmux manager error: {e}") from e

    def _create_config(self) -> YesmanConfig:
        """Create YesmanConfig instance with error handling (fallback method)."""
        try:
            return YesmanConfig()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise CommandError(f"Configuration error: {e}") from e

    def _create_tmux_manager(self) -> TmuxManager:
        """Create TmuxManager instance with error handling (fallback method)."""
        try:
            return TmuxManager(self.config)
        except Exception as e:
            self.logger.error(f"Failed to initialize tmux manager: {e}")
            raise CommandError(f"Tmux manager error: {e}") from e

    def _create_claude_manager(self) -> ClaudeManager:
        """Create ClaudeManager instance with error handling."""
        try:
            return ClaudeManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize claude manager: {e}")
            raise CommandError(f"Claude manager error: {e}") from e

    def validate_preconditions(self) -> None:
        """Validate command preconditions (can be overridden)."""
        # Check if tmux is available
        if not self._is_tmux_available():
            raise CommandError("tmux is not available or not properly installed")

        # Check if required directories exist
        required_paths = [settings.paths.home_dir]
        for path in required_paths:
            if not Path(path).exists():
                self.logger.warning(f"Creating missing directory: {path}")
                Path(path).mkdir(parents=True, exist_ok=True)

    def _is_tmux_available(self) -> bool:
        """Check if tmux is available."""
        import shutil

        return shutil.which("tmux") is not None

    def handle_error(self, error: Exception, context_str: str = "") -> None:
        """Standard error handling using centralized error handler."""
        # Create error context if needed
        if not isinstance(error, YesmanError):
            context = ErrorContext(
                operation=context_str or "command_execution",
                component=self.__class__.__name__,
            )
            error_handler.handle_error(error, context, exit_on_critical=True)
        else:
            error_handler.handle_error(error, exit_on_critical=True)

    def log_command_start(self, command_name: str, **kwargs) -> None:
        """Log command start with parameters."""
        params = ", ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        self.logger.info(f"Starting command: {command_name}" + (f" with {params}" if params else ""))

    def log_command_end(self, command_name: str, success: bool = True) -> None:
        """Log command completion."""
        status = "completed successfully" if success else "failed"
        self.logger.info(f"Command {command_name} {status}")

    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Ask for user confirmation."""
        try:
            return click.confirm(message, default=default)
        except click.Abort:
            self.logger.info("Operation cancelled by user")
            sys.exit(0)

    def print_success(self, message: str) -> None:
        """Print success message with formatting."""
        click.echo(click.style(f"✅ {message}", fg="green"))

    def print_warning(self, message: str) -> None:
        """Print warning message with formatting."""
        click.echo(click.style(f"⚠️  {message}", fg="yellow"))

    def print_error(self, message: str) -> None:
        """Print error message with formatting."""
        click.echo(click.style(f"❌ {message}", fg="red"))

    def print_info(self, message: str) -> None:
        """Print info message with formatting."""
        click.echo(click.style(f"ℹ️  {message}", fg="blue"))

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the command (must be implemented by subclasses)."""
        pass

    def run(self, **kwargs) -> Any:
        """Main execution wrapper with error handling."""
        command_name = self.__class__.__name__.replace("Command", "").lower()

        try:
            self.log_command_start(command_name, **kwargs)
            self.validate_preconditions()

            result = self.execute(**kwargs)

            self.log_command_end(command_name, success=True)
            self.handle_success(result)
            return result

        except YesmanError as e:
            self.log_command_end(command_name, success=False)
            self.handle_yesman_error(e)
        except Exception as e:
            self.log_command_end(command_name, success=False)
            self.handle_unexpected_error(e)

    def handle_success(self, result: Any) -> None:
        """Handle successful command execution."""
        # Default implementation - can be overridden
        if result and isinstance(result, dict):
            if result.get("message"):
                self.print_success(result["message"])

    def handle_yesman_error(self, error: YesmanError) -> None:
        """Handle YesmanError with recovery hints."""
        self.print_error(error.message)

        if error.recovery_hint:
            self.print_info(f"Hint: {error.recovery_hint}")

        error_handler.handle_error(error, exit_on_critical=True)

    def handle_unexpected_error(self, error: Exception) -> None:
        """Handle unexpected errors."""
        self.print_error(f"Unexpected error: {error}")

        # Create context for unexpected error
        context = ErrorContext(
            operation="command_execution",
            component=self.__class__.__name__,
        )

        error_handler.handle_error(error, context, exit_on_critical=True)


class SessionCommandMixin:
    """Mixin for commands that work with sessions."""

    # Expected attributes from BaseCommand
    tmux_manager: "TmuxManager"
    logger: logging.Logger

    def get_session_list(self) -> list[str]:
        """Get list of available sessions."""
        try:
            sessions = self.tmux_manager.get_cached_sessions_list()
            return [session.get("session_name", "unknown") for session in sessions]
        except Exception as e:
            self.logger.error(f"Failed to get session list: {e}")
            return []

    def validate_session_name(self, session_name: str) -> None:
        """Validate session name format."""
        if not session_name:
            raise CommandError("Session name cannot be empty")

        if len(session_name) > settings.sessions.session_name_max_length:
            raise CommandError(f"Session name too long (max {settings.sessions.session_name_max_length} characters)")

        import re

        from .settings import ValidationPatterns

        if not re.match(ValidationPatterns.SESSION_NAME, session_name):
            raise CommandError("Session name can only contain letters, numbers, underscores, and hyphens")

    def session_exists(self, session_name: str) -> bool:
        """Check if session exists."""
        try:
            return session_name in self.get_session_list()
        except Exception:
            return False


class ConfigCommandMixin:
    """Mixin for commands that work with configuration."""

    # Expected attributes from BaseCommand
    logger: logging.Logger

    def load_projects_config(self) -> dict[str, Any]:
        """Load projects configuration with error handling."""
        try:
            import yaml

            with open(settings.paths.projects_file) as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.logger.warning(f"Projects file not found: {settings.paths.projects_file}")
            return {}
        except Exception as e:
            raise CommandError(f"Failed to load projects configuration: {e}") from e

    def save_projects_config(self, config: dict[str, Any]) -> None:
        """Save projects configuration with error handling."""
        try:
            import yaml

            with open(settings.paths.projects_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            raise CommandError(f"Failed to save projects configuration: {e}") from e

    def backup_config(self, config_path: str) -> str:
        """Create backup of configuration file."""
        import shutil
        from datetime import datetime

        backup_path = f"{config_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.copy2(config_path, backup_path)
            self.logger.info(f"Configuration backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")
            return ""


class OutputFormatterMixin:
    """Mixin for commands that need output formatting."""

    def format_table(self, data: list[dict[str, Any]], headers: list[str]) -> str:
        """Format data as table."""
        if not data:
            return "No data to display"

        # Calculate column widths
        widths = {}
        for header in headers:
            widths[header] = len(header)
            for row in data:
                value = str(row.get(header, ""))
                widths[header] = max(widths[header], len(value))

        # Build table
        lines = []

        # Header
        header_line = " | ".join(header.ljust(widths[header]) for header in headers)
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Data rows
        for row in data:
            row_line = " | ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers)
            lines.append(row_line)

        return "\n".join(lines)

    def format_json(self, data: Any, indent: int = 2) -> str:
        """Format data as JSON."""
        import json

        return json.dumps(data, indent=indent, default=str)

    def format_yaml(self, data: Any) -> str:
        """Format data as YAML."""
        import yaml

        return yaml.dump(data, default_flow_style=False)
