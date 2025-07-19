#!/usr/bin/env python3
"""Session helper utilities for tmux session management.

This module provides common functions for working with tmux sessions,
windows, and panes across the Yesman-Claude project.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import libtmux
from libtmux.exc import LibTmuxException

from libs.core.error_handling import ErrorCategory, ErrorContext, YesmanError
from libs.validation import validate_session_name

logger = logging.getLogger(__name__)


# Custom exceptions for session operations
class SessionNotFoundError(YesmanError):
    """Raised when a session is not found."""

    def __init__(self, session_name: str):
        super().__init__(
            f"Session '{session_name}' not found",
            category=ErrorCategory.VALIDATION,
        )
        self.session_name = session_name


class SessionAlreadyExistsError(YesmanError):
    """Raised when trying to create a session that already exists."""

    def __init__(self, session_name: str):
        super().__init__(
            f"Session '{session_name}' already exists",
            category=ErrorCategory.VALIDATION,
        )
        self.session_name = session_name


class SessionConfigurationError(YesmanError):
    """Raised when session configuration is invalid."""

    def __init__(self, message: str, config: dict | None = None):
        context = ErrorContext(operation="session_configuration", component="session_helpers", additional_info={"config": config} if config else None)
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            context=context,
        )


def get_tmux_server() -> libtmux.Server:
    """Get or create a tmux server instance.

    Returns:
        libtmux.Server: The tmux server instance

    Raises:
        YesmanError: If tmux is not available or server creation fails
    """
    try:
        return libtmux.Server()
    except Exception as e:
        raise YesmanError(
            "Failed to connect to tmux server. Is tmux running?",
            category=ErrorCategory.SYSTEM,
            cause=e,
        ) from e


def check_session_exists(session_name: str, server: libtmux.Server | None = None) -> bool:
    """Check if a tmux session exists.

    Args:
        session_name: Name of the session to check
        server: Optional tmux server instance (creates one if not provided)

    Returns:
        bool: True if session exists, False otherwise
    """
    try:
        server = server or get_tmux_server()
        session = server.find_where({"session_name": session_name})
        return session is not None
    except Exception as e:
        logger.error(f"Error checking session existence: {e}")
        return False


@dataclass
class PaneInfo:
    """Information about a tmux pane."""

    pane_id: str
    pane_index: int
    command: str
    is_active: bool
    width: int
    height: int
    is_claude: bool = False
    is_controller: bool = False


@dataclass
class WindowInfo:
    """Information about a tmux window."""

    window_id: str
    window_index: int
    window_name: str
    layout: str
    panes: list[PaneInfo] = field(default_factory=list)
    is_active: bool = False


@dataclass
class SessionInfo:
    """Information about a tmux session."""

    session_name: str
    session_id: str
    created_at: str
    attached: bool
    windows: list[WindowInfo] = field(default_factory=list)
    project_name: str = ""
    template: str = ""
    status: str = "running"


def get_session_info(session_name: str, server: libtmux.Server | None = None) -> SessionInfo:
    """Get detailed information about a tmux session.

    Args:
        session_name: Name of the session
        server: Optional tmux server instance

    Returns:
        SessionInfo: Detailed session information

    Raises:
        SessionNotFoundError: If session doesn't exist
        YesmanError: For other errors
    """
    server = server or get_tmux_server()
    session = server.find_where({"session_name": session_name})

    if not session:
        raise SessionNotFoundError(session_name)

    try:
        windows = []
        for window in session.list_windows():
            panes = []
            for pane in window.list_panes():
                pane_info = PaneInfo(
                    pane_id=pane.pane_id,
                    pane_index=int(pane.pane_index),
                    command=pane.pane_current_command or "",
                    is_active=pane.pane_active == "1",
                    width=int(pane.pane_width),
                    height=int(pane.pane_height),
                    is_claude=False,  # Will be determined by command inspection
                    is_controller=False,  # Will be determined by command inspection
                )
                panes.append(pane_info)

            window_info = WindowInfo(
                window_id=window.window_id,
                window_index=int(window.window_index),
                window_name=window.window_name,
                layout=window.window_layout or "",
                panes=panes,
                is_active=window.window_active == "1",
            )
            windows.append(window_info)

        return SessionInfo(
            session_name=session_name,
            session_id=session.session_id,
            created_at=str(session.session_created),
            attached=int(session.session_attached) > 0,
            windows=windows,
            project_name="",  # Would need to be looked up from config
            template="",  # Would need to be looked up from config
            status="running" if int(session.session_attached) > 0 else "detached",
        )

    except Exception as e:
        logger.error(f"Error getting session info for {session_name}: {e}")
        raise YesmanError(
            f"Failed to get session information for '{session_name}'",
            category=ErrorCategory.SYSTEM,
            cause=e,
        ) from e


def create_session_windows(
    session_name: str,
    windows_config: list[dict[str, Any]],
    start_directory: str | None = None,
    server: libtmux.Server | None = None,
) -> libtmux.Session:
    """Create windows for a session from configuration.

    Args:
        session_name: Name of the session
        windows_config: List of window configurations
        start_directory: Optional starting directory
        server: Optional tmux server instance

    Returns:
        libtmux.Session: The created/updated session

    Raises:
        SessionConfigurationError: If configuration is invalid
        YesmanError: For other errors
    """
    # Validate session name
    valid, error = validate_session_name(session_name)
    if not valid:
        raise SessionConfigurationError(f"Invalid session name: {error}")

    server = server or get_tmux_server()

    # Check if session exists
    session = server.find_where({"session_name": session_name})
    if not session:
        # Create new session
        try:
            session = server.new_session(
                session_name=session_name,
                start_directory=start_directory,
                kill_session=False,
            )
        except LibTmuxException as e:
            raise YesmanError(
                f"Failed to create session '{session_name}'",
                category=ErrorCategory.SYSTEM,
                cause=e,
            ) from e

    # Create windows
    for i, window_config in enumerate(windows_config):
        window_name = window_config.get("window_name", f"window_{i}")
        layout = window_config.get("layout", "tiled")
        panes = window_config.get("panes", [])

        # Create or get window
        if i == 0:
            # Rename first window
            window = session.windows[0]
            window.rename_window(window_name)
        else:
            window = session.new_window(window_name=window_name)

        # Create panes
        for j, pane_config in enumerate(panes):
            if j == 0:
                # First pane already exists
                pane = window.panes[0]
            else:
                # Split window for additional panes
                pane = window.split_window()

            # Send commands to pane
            command = pane_config.get("command", "")
            if command:
                send_keys_to_pane(
                    session_name=session_name,
                    window_index=int(window.window_index),
                    pane_index=int(pane.pane_index),
                    keys=command,
                    server=server,
                )

        # Apply layout
        if len(panes) > 1:
            window.select_layout(layout)

    return session


def get_active_pane(
    session_name: str,
    window_name: str | None = None,
    server: libtmux.Server | None = None,
) -> PaneInfo:
    """Get the active pane in a window.

    Args:
        session_name: Name of the session
        window_name: Optional window name (uses current window if not specified)
        server: Optional tmux server instance

    Returns:
        PaneInfo: Information about the active pane

    Raises:
        SessionNotFoundError: If session doesn't exist
        YesmanError: For other errors
    """
    server = server or get_tmux_server()
    session = server.find_where({"session_name": session_name})

    if not session:
        raise SessionNotFoundError(session_name)

    try:
        # Get window
        if window_name:
            window = session.find_where({"window_name": window_name})
            if not window:
                raise YesmanError(
                    f"Window '{window_name}' not found in session '{session_name}'",
                    category=ErrorCategory.VALIDATION,
                )
        else:
            # Get active window
            window = session.active_window

        # Get active pane
        active_pane = window.active_pane

        return PaneInfo(
            pane_id=active_pane.pane_id,
            pane_index=int(active_pane.pane_index),
            command=active_pane.pane_current_command or "",
            is_active=True,
            width=int(active_pane.pane_width),
            height=int(active_pane.pane_height),
            is_claude=False,
            is_controller=False,
        )

    except Exception as e:
        logger.error(f"Error getting active pane: {e}")
        raise YesmanError(
            "Failed to get active pane information",
            category=ErrorCategory.SYSTEM,
            cause=e,
        ) from e


def send_keys_to_pane(
    session_name: str,
    window_index: int,
    pane_index: int,
    keys: str,
    server: libtmux.Server | None = None,
    enter: bool = True,
) -> None:
    """Send keys to a specific pane.

    Args:
        session_name: Name of the session
        window_index: Index of the window
        pane_index: Index of the pane
        keys: Keys to send
        server: Optional tmux server instance
        enter: Whether to send Enter key after the keys

    Raises:
        SessionNotFoundError: If session doesn't exist
        YesmanError: For other errors
    """
    server = server or get_tmux_server()
    session = server.find_where({"session_name": session_name})

    if not session:
        raise SessionNotFoundError(session_name)

    try:
        # Get window by index
        window = None
        for w in session.list_windows():
            if int(w.window_index) == window_index:
                window = w
                break

        if not window:
            raise YesmanError(
                f"Window index {window_index} not found in session '{session_name}'",
                category=ErrorCategory.VALIDATION,
            )

        # Get pane by index
        pane = None
        for p in window.list_panes():
            if int(p.pane_index) == pane_index:
                pane = p
                break

        if not pane:
            raise YesmanError(
                f"Pane index {pane_index} not found in window {window_index}",
                category=ErrorCategory.VALIDATION,
            )

        # Send keys
        pane.send_keys(keys, enter=enter)
        logger.debug(f"Sent keys to {session_name}:{window_index}.{pane_index}")

    except Exception as e:
        if not isinstance(e, YesmanError):
            logger.error(f"Error sending keys to pane: {e}")
            raise YesmanError(
                "Failed to send keys to pane",
                category=ErrorCategory.SYSTEM,
                cause=e,
            ) from e
        raise


def list_session_windows(session_name: str, server: libtmux.Server | None = None) -> list[WindowInfo]:
    """List all windows in a session.

    Args:
        session_name: Name of the session
        server: Optional tmux server instance

    Returns:
        List of WindowInfo objects

    Raises:
        SessionNotFoundError: If session doesn't exist
    """
    session_info = get_session_info(session_name, server)
    return session_info.windows


def merge_template_override(template_config: dict[str, Any], override_config: dict[str, Any]) -> dict[str, Any]:
    """Merge template configuration with override configuration.

    Override values take precedence over template values.

    Args:
        template_config: Base template configuration
        override_config: Override configuration

    Returns:
        Merged configuration dictionary
    """
    import copy

    # Deep copy template to avoid modifying original
    merged = copy.deepcopy(template_config)

    # Apply overrides
    for key, value in override_config.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            # Recursively merge dictionaries
            merged[key] = merge_template_override(merged[key], value)
        else:
            # Override value
            merged[key] = value

    return merged


def expand_and_validate_directory(directory: str, create_if_missing: bool = False) -> Path:
    """Expand user paths and validate directory existence.

    Args:
        directory: Directory path (may contain ~ or environment variables)
        create_if_missing: Whether to create directory if it doesn't exist

    Returns:
        Path: Resolved directory path

    Raises:
        YesmanError: If directory is invalid or cannot be created
    """
    try:
        # Expand user and environment variables
        expanded = os.path.expanduser(os.path.expandvars(directory))
        path = Path(expanded).resolve()

        if not path.exists():
            if create_if_missing:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")
            else:
                raise YesmanError(
                    f"Directory does not exist: {path}",
                    category=ErrorCategory.VALIDATION,
                )

        if not path.is_dir():
            raise YesmanError(
                f"Path exists but is not a directory: {path}",
                category=ErrorCategory.VALIDATION,
            )

        return path

    except Exception as e:
        if isinstance(e, YesmanError):
            raise
        raise YesmanError(
            f"Failed to validate directory: {directory}",
            category=ErrorCategory.SYSTEM,
            cause=e,
        ) from e


def get_session_by_project(
    project_name: str,
    projects_config: dict[str, Any],
    server: libtmux.Server | None = None,
) -> SessionInfo | None:
    """Get session information by project name.

    Args:
        project_name: Name of the project
        projects_config: Projects configuration dictionary
        server: Optional tmux server instance

    Returns:
        SessionInfo if found, None otherwise
    """
    sessions = projects_config.get("sessions", {})

    # Find session with matching project name
    for session_name, session_config in sessions.items():
        if session_config.get("project_name") == project_name:
            try:
                return get_session_info(session_name, server)
            except SessionNotFoundError:
                return None

    return None
