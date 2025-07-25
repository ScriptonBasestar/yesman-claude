#!/usr/bin/env python3

# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Session setup logic extracted from setup command."""

import os
import re
import subprocess  # noqa: S404
from typing import Any

import click
import yaml
from rich.progress import track

from .base_command import CommandError
from .settings import ValidationPatterns, settings


class SessionValidator:
    """Validates session configuration."""

    def __init__(self) -> None:
        self.validation_errors: list[str] = []

    def validate_session_config(
        self, session_name: str, config_dict: dict[str, Any]
    ) -> bool:
        """Validate session configuration.

        Args:
            session_name: Name of the session
            config_dict: Session configuration dictionary

        Returns:
            True if validation passes, False otherwise
        """
        self.validation_errors.clear()

        # Validate session name
        if not self._validate_session_name(session_name):
            return False

        # Validate start directory
        if not self._validate_start_directory(session_name, config_dict):
            return False

        # Validate windows
        if not self._validate_windows(session_name, config_dict):
            return False

        return len(self.validation_errors) == 0

    def _validate_session_name(self, session_name: str) -> bool:
        """Validate session name format."""
        if not session_name:
            self.validation_errors.append("Session name cannot be empty")
            return False

        if len(session_name) > settings.sessions.session_name_max_length:
            self.validation_errors.append(
                f"Session name '{session_name}' too long (max {settings.sessions.session_name_max_length} characters)",
            )
            return False

        if not re.match(ValidationPatterns.SESSION_NAME, session_name):
            self.validation_errors.append(
                f"Session name '{session_name}' contains invalid characters",
            )
            return False

        return True

    def _validate_start_directory(
        self, session_name: str, config_dict: dict[str, Any]
    ) -> bool:
        """Validate and potentially create start directory."""
        start_dir = config_dict.get("start_directory")
        if not start_dir:
            return True

        expanded_dir = os.path.expanduser(start_dir)

        if not os.path.exists(expanded_dir):
            click.echo(
                f"❌ Error: start_directory '{start_dir}' does not exist for session '{session_name}'"
            )
            click.echo(f"   Resolved path: {expanded_dir}")

            if click.confirm(
                f"Would you like to create the missing directory '{expanded_dir}'?"
            ):
                try:
                    os.makedirs(expanded_dir, exist_ok=True)
                    click.echo(f"✅ Created directory: {expanded_dir}")
                    config_dict["start_directory"] = expanded_dir
                    return True
                except Exception as e:
                    self.validation_errors.append(
                        f"Failed to create directory '{expanded_dir}': {e}"
                    )
                    return False
            else:
                self.validation_errors.append(
                    f"Missing start_directory: {expanded_dir}"
                )
                return False

        elif not os.path.isdir(expanded_dir):
            self.validation_errors.append(
                f"start_directory '{start_dir}' is not a directory for session '{session_name}'",
            )
            return False

        # Update with expanded path
        config_dict["start_directory"] = expanded_dir
        return True

    def _validate_windows(self, session_name: str, config_dict: dict[str, Any]) -> bool:
        """Validate window configurations."""
        windows = config_dict.get("windows", [])

        if len(windows) > settings.sessions.max_windows_per_session:
            self.validation_errors.append(
                f"Too many windows ({len(windows)}) for session '{session_name}' (max {settings.sessions.max_windows_per_session})",
            )
            return False

        return all(
            self._validate_window(session_name, i, window, config_dict)
            for i, window in enumerate(windows)
        )

    def _validate_window(
        self,
        session_name: str,
        window_index: int,
        window: dict[str, Any],
        config_dict: dict[str, Any],
    ) -> bool:
        """Validate individual window configuration."""
        window_name = window.get("window_name", f"window_{window_index}")

        # Validate window name
        if len(window_name) > settings.sessions.max_windows_per_session:
            self.validation_errors.append(f"Window name '{window_name}' too long")
            return False

        # Validate window start directory
        window_start_dir = window.get("start_directory")
        if window_start_dir and not self._validate_window_start_directory(
            session_name,
            window_name,
            window_start_dir,
            config_dict,
        ):
            return False

        # Validate panes
        panes = window.get("panes", [])
        if len(panes) > settings.sessions.max_panes_per_window:
            self.validation_errors.append(
                f"Too many panes ({len(panes)}) in window '{window_name}' (max {settings.sessions.max_panes_per_window})",
            )
            return False

        return True

    def _validate_window_start_directory(
        self,
        session_name: str,  # noqa: ARG002
        window_name: str,
        window_start_dir: str,
        config_dict: dict[str, Any],
    ) -> bool:
        """Validate window start directory."""
        # If relative path, make it relative to session start_directory
        if not os.path.isabs(window_start_dir):
            base_dir = config_dict.get("start_directory", os.getcwd())
            window_start_dir = os.path.join(base_dir, window_start_dir)

        expanded_window_dir = os.path.expanduser(window_start_dir)

        if not os.path.exists(expanded_window_dir):
            click.echo(
                f"❌ Error: Window '{window_name}' start_directory does not exist"
            )
            click.echo(f"   Resolved path: {expanded_window_dir}")

            if click.confirm(
                f"Would you like to create the missing directory '{expanded_window_dir}'?"
            ):
                try:
                    os.makedirs(expanded_window_dir, exist_ok=True)
                    click.echo(f"✅ Created directory: {expanded_window_dir}")
                    return True
                except Exception as e:
                    self.validation_errors.append(
                        f"Failed to create window directory '{expanded_window_dir}': {e}",
                    )
                    return False
            else:
                self.validation_errors.append(
                    f"Missing window directory: {expanded_window_dir}"
                )
                return False

        elif not os.path.isdir(expanded_window_dir):
            self.validation_errors.append(
                f"Window '{window_name}' start_directory is not a directory: {expanded_window_dir}",
            )
            return False

        return True

    def get_validation_errors(self) -> list[str]:
        """Get list of validation errors."""
        return self.validation_errors.copy()


class SessionConfigBuilder:
    """Builds session configuration from template and overrides."""

    def __init__(self, tmux_manager: object) -> None:
        self.tmux_manager = tmux_manager

    def build_session_config(
        self, session_name: str, session_conf: dict[str, Any]
    ) -> dict[str, Any]:
        """Build complete session configuration.

        Args:
            session_name: Name of the session
            session_conf: Session configuration from projects.yaml

        Returns:
            Complete session configuration dictionary

        Raises:
            CommandError: If template loading fails
        """
        template_name = session_conf.get("template_name")
        template_conf = self._load_template(template_name)
        override_conf = session_conf.get("override", {})

        # Start with template configuration as base
        config_dict = template_conf.copy()

        # Apply default values
        config_dict["session_name"] = override_conf.get("session_name", session_name)
        config_dict["start_directory"] = override_conf.get(
            "start_directory", os.getcwd()
        )

        # Apply all overrides
        for key, value in override_conf.items():
            config_dict[key] = value

        return config_dict

    def _load_template(self, template_name: str | None) -> dict[str, Any]:
        """Load template configuration.

        Args:
            template_name: Name of the template to load

        Returns:
            Template configuration dictionary

        Raises:
            CommandError: If template loading fails
        """
        if not template_name:
            return {}

        from pathlib import Path

        templates_path = getattr(self.tmux_manager, "templates_path", Path("."))
        template_file = templates_path / f"{template_name}.yaml"

        if not template_file.is_file():
            msg = f"Template '{template_name}' not found at {template_file}"
            raise CommandError(
                msg,
            )

        try:
            with open(template_file, encoding="utf-8") as tf:
                return yaml.safe_load(tf) or {}
        except Exception as e:
            msg = f"Failed to read template {template_file}: {e}"
            raise CommandError(msg) from e


class SessionSetupService:
    """Service for setting up tmux sessions."""

    def __init__(self, tmux_manager: object) -> None:
        self.tmux_manager = tmux_manager
        self.config_builder = SessionConfigBuilder(tmux_manager)
        self.validator = SessionValidator()

    def setup_sessions(self, session_filter: str | None = None) -> tuple[int, int]:
        """Set up tmux sessions.

        Args:
            session_filter: Optional filter to set up only specific session

        Returns:
            Tuple of (successful_count, failed_count)
        """
        sessions = self._load_sessions_config(session_filter)

        if not sessions:
            click.echo("No sessions to set up")
            return 0, 0

        successful_count = 0
        failed_count = 0

        # Use progress bar for session setup
        session_items = list(sessions.items())
        for session_name, session_conf in track(
            session_items, description="🔧 Setting up sessions...", style="bold blue"
        ):
            try:
                if self._setup_single_session(session_name, session_conf):
                    successful_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                click.echo(f"❌ Failed to set up session '{session_name}': {e}")
                failed_count += 1

        # Summary
        click.echo("\n📊 Setup Summary:")
        click.echo(f"  ✅ Successful: {successful_count}")
        if failed_count > 0:
            click.echo(f"  ❌ Failed: {failed_count}")

        return successful_count, failed_count

    def _load_sessions_config(
        self, session_filter: str | None = None
    ) -> dict[str, Any]:
        """Load sessions configuration with optional filter."""
        projects_data = getattr(self.tmux_manager, "load_projects", lambda: {})() or {}
        all_sessions: dict[str, Any] = (
            projects_data.get("sessions", {}) if isinstance(projects_data, dict) else {}
        )

        if not all_sessions:
            return {}

        if session_filter:
            if session_filter not in all_sessions:
                msg = f"Session '{session_filter}' not defined in projects.yaml"
                raise CommandError(msg)
            return {session_filter: all_sessions[session_filter]}

        return all_sessions

    def _setup_single_session(
        self, session_name: str, session_conf: dict[str, Any]
    ) -> bool:
        """Set up a single tmux session.

        Args:
            session_name: Name of the session
            session_conf: Session configuration

        Returns:
            True if successful, False otherwise
        """
        click.echo(f"🔧 Setting up session: {session_name}")

        try:
            # Build configuration
            config_dict = self.config_builder.build_session_config(
                session_name, session_conf
            )

            # Validate configuration
            if not self.validator.validate_session_config(session_name, config_dict):
                for error in self.validator.get_validation_errors():
                    click.echo(f"❌ Validation error: {error}")
                return False

            # Check if session already exists
            if self._session_exists(session_name):
                click.echo(f"⚠️  Session '{session_name}' already exists")
                if not click.confirm(
                    "Do you want to kill the existing session and recreate it?"
                ):
                    click.echo(f"⏭️  Skipping session '{session_name}'")
                    return False
                self._kill_session(session_name)

            # Create session
            self._create_session(config_dict)
            click.echo(f"✅ Successfully created session: {session_name}")
            return True

        except CommandError as e:
            click.echo(f"❌ Error setting up session '{session_name}': {e.message}")
            return False
        except Exception as e:
            click.echo(f"❌ Unexpected error setting up session '{session_name}': {e}")
            return False

    def _session_exists(self, session_name: str) -> bool:
        """Check if session already exists."""
        try:
            from collections.abc import Callable

            get_sessions_func: Callable[[], list] = getattr(
                self.tmux_manager, "get_all_sessions", lambda: []
            )
            sessions = get_sessions_func()
            return any(
                session.get("session_name") == session_name for session in sessions
            )
        except Exception:
            return False

    @staticmethod
    def _kill_session(session_name: str) -> None:
        """Kill existing session."""
        try:
            subprocess.run(
                ["tmux", "kill-session", "-t", session_name],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            msg = f"Failed to kill existing session: {e}"
            raise CommandError(msg) from e

    def _create_session(self, config_dict: dict[str, Any]) -> None:
        """Create tmux session from configuration."""
        try:
            create_func = getattr(self.tmux_manager, "create_session_from_config", None)
            if create_func:
                create_func(config_dict)
            else:
                msg = "tmux_manager does not support create_session_from_config"
                raise CommandError(msg)
        except Exception as e:
            msg = f"Failed to create tmux session: {e}"
            raise CommandError(msg) from e
