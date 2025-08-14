import logging
import pathlib
import subprocess
from typing import TYPE_CHECKING, cast

from fastapi import APIRouter, HTTPException, status

from api import models
from libs.core.error_handling import ErrorCategory, YesmanError
from libs.core.services import get_session_manager, get_tmux_manager
from libs.core.session_manager import SessionManager
from libs.core.types import SessionAPIData, SessionStatusType
from libs.tmux_manager import TmuxManager

if TYPE_CHECKING:
    from libs.core.models import SessionInfo

# !/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Improved sessions router with dependency injection and proper error handling."""


# Note: Removed typing.Any usage to fix ANN401 errors


# Set up logger
logger = logging.getLogger("yesman.api.sessions")


class SessionService:
    """Service class for session operations."""

    def __init__(self, session_manager: SessionManager, tmux_manager: TmuxManager) -> None:
        self.session_manager = session_manager
        self.tmux_manager = tmux_manager
        self.logger = logging.getLogger("yesman.api.sessions.service")

    def get_all_sessions(self) -> list[SessionAPIData]:
        """Get all sessions with error handling.

        Returns:
            list[SessionAPIData]: List of all session data.

        Raises:
            YesmanError: If sessions cannot be retrieved.
        """
        try:
            # 1) SessionManager를 통해 세션 정보 수집
            sessions_data = self.session_manager.get_all_sessions()
            api_list = [self._convert_session_to_api_data(session) for session in sessions_data]

            # 2) 폴백: session_manager가 빈 목록을 줄 경우 설정 기반 목록 노출
            if not api_list:
                self.logger.info("No active tmux sessions found; falling back to configured sessions list")
                projects = cast("dict", self.tmux_manager.load_projects().get("sessions", {}))
                for project_name, project_conf in projects.items():
                    # override.session_name 우선, 없으면 project_name 사용
                    override = cast("dict", project_conf.get("override", {})) if isinstance(project_conf, dict) else {}
                    session_name = cast("str", override.get("session_name", project_name))

                    # SessionAPIData 스펙에 맞춘 플레이스홀더 구성
                    api_list.append(
                        {
                            "session_name": session_name,
                            "status": cast("SessionStatusType", "stopped"),
                            "windows": [],
                            "created_at": None,
                            "last_activity": None,
                        },
                    )

            return api_list
        except Exception as e:
            self.logger.exception("Failed to get sessions")
            msg = "Failed to retrieve sessions"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def get_session_by_name(self, session_name: str) -> SessionAPIData | None:
        """Get specific session by name.

        Returns:
            SessionAPIData | None: Session data if found, None otherwise.

        Raises:
            YesmanError: If session retrieval fails.
        """
        try:
            # Load projects configuration to get project_conf
            projects_data = self.tmux_manager.load_projects()
            projects = cast("dict", projects_data.get("sessions", {}))

            # Find the project that matches this session name
            project_name = None
            project_conf = None

            # First, try direct match by project name
            if session_name in projects:
                project_name = session_name
                project_conf = projects[session_name]
            else:
                # Then try to find by override session_name
                for proj_name, proj_conf in projects.items():
                    if isinstance(proj_conf, dict):
                        override_session_name = proj_conf.get("override", {}).get("session_name")
                        if override_session_name == session_name:
                            project_name = proj_name
                            project_conf = proj_conf
                            break

            if not project_name or not project_conf:
                # Session not found in configuration
                return None

            session_data = self.session_manager._get_session_info(project_name, project_conf)
            if session_data:
                return self._convert_session_to_api_data(session_data)
            return None
        except Exception as e:
            self.logger.exception("Failed to get session {session_name}: {e}")
            msg = f"Failed to retrieve session '{session_name}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def setup_session(self, session_name: str) -> dict[str, object]:
        """Set up a specific session.

        Returns:
            dict[str, object]: Dictionary containing session setup details.

        Raises:
            YesmanError: If session already exists or setup fails.
        """
        try:
            # Check if session already exists
            if self._session_exists(session_name):
                msg = f"Session '{session_name}' already exists"
                raise YesmanError(
                    msg,
                    category=ErrorCategory.VALIDATION,
                )

            # Load projects configuration

            projects_data = self.tmux_manager.load_projects()
            projects = cast("dict", projects_data.get("sessions", {}))

            # Find session configuration (direct match or by override)
            session_config = None
            actual_project_name = None

            if session_name in projects:
                actual_project_name = session_name
                session_config = cast("dict", projects[session_name])
            else:
                # Look for session by override session_name
                for proj_name, proj_conf in projects.items():
                    if isinstance(proj_conf, dict):
                        override_session_name = proj_conf.get("override", {}).get("session_name")
                        if override_session_name == session_name:
                            actual_project_name = proj_name
                            session_config = proj_conf
                            break

            if not session_config or not actual_project_name:
                msg = f"Session '{session_name}' not found in projects configuration"
                raise YesmanError(
                    msg,
                    category=ErrorCategory.CONFIGURATION,
                )

            # Set up session (this would integrate with the improved setup logic)
            result = self._setup_session_internal(actual_project_name, session_config)

            return {
                "session_name": session_name,
                "status": "created",
                "details": result,
            }

        except YesmanError:
            raise
        except Exception as e:
            self.logger.exception("Failed to setup session {session_name}: {e}")
            msg = f"Failed to setup session '{session_name}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def teardown_session(self, session_name: str) -> dict[str, object]:
        """Teardown a specific session.

        Returns:
            dict[str, object]: Dictionary containing teardown status.

        Raises:
            YesmanError: If session not found or teardown fails.
        """
        try:
            if not self._session_exists(session_name):
                msg = f"Session '{session_name}' not found"
                raise YesmanError(
                    msg,
                    category=ErrorCategory.VALIDATION,
                )

            # Teardown session
            self._teardown_session_internal(session_name)

            return {
                "session_name": session_name,
                "status": "removed",
            }

        except YesmanError:
            raise
        except Exception as e:
            self.logger.exception("Failed to teardown session {session_name}: {e}")
            msg = f"Failed to teardown session '{session_name}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def get_session_status(self, session_name: str) -> dict[str, object]:
        """Get session status information.

        Returns:
            dict[str, object]: Dictionary containing session status information.

        Raises:
            YesmanError: If status retrieval fails.
        """
        try:
            # Load projects configuration to get project_conf
            projects_data = self.tmux_manager.load_projects()
            projects = cast("dict", projects_data.get("sessions", {}))

            # Find the project that matches this session name
            project_name = None
            project_conf = None

            # First, try direct match by project name
            if session_name in projects:
                project_name = session_name
                project_conf = projects[session_name]
            else:
                # Then try to find by override session_name
                for proj_name, proj_conf in projects.items():
                    if isinstance(proj_conf, dict):
                        override_session_name = proj_conf.get("override", {}).get("session_name")
                        if override_session_name == session_name:
                            project_name = proj_name
                            project_conf = proj_conf
                            break

            if not project_name or not project_conf:
                # Session not found in configuration
                return {
                    "session_name": session_name,
                    "status": "not_found",
                    "exists": False,
                }

            session_data = self.session_manager._get_session_info(project_name, project_conf)
            if not session_data:
                return {
                    "session_name": session_name,
                    "status": "not_found",
                    "exists": False,
                }

            return {
                "session_name": session_name,
                "status": getattr(session_data, "status", "unknown"),
                "exists": True,
                "windows": len(getattr(session_data, "windows", [])),
                "last_activity": getattr(session_data, "last_activity", None),
            }

        except Exception as e:
            self.logger.exception("Failed to get status for session {session_name}: {e}")
            msg = f"Failed to get status for session '{session_name}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def setup_all_sessions(self) -> dict[str, object]:
        """Setup all sessions defined in sessions/ directory.

        Returns:
            dict[str, object]: Dictionary containing setup results.

        Raises:
            YesmanError: If setup fails.
        """
        try:
            projects_data = self.tmux_manager.load_projects()
            projects = cast("dict", projects_data.get("sessions", {}))
            successful = []
            failed = []

            for session_name, session_config in projects.items():
                try:
                    if not self._session_exists(session_name):
                        self._setup_session_internal(session_name, session_config)
                        successful.append(session_name)
                    else:
                        self.logger.info("Session '%s' already exists, skipping", session_name)
                except Exception as e:
                    self.logger.exception("Failed to setup session '{session_name}': {e}")
                    failed.append({"session_name": session_name, "error": str(e)})

            return {
                "successful": successful,
                "failed": failed,
                "total": len(projects),
                "created": len(successful),
            }

        except Exception as e:
            self.logger.exception("Failed to setup all sessions: {e}")
            msg = "Failed to setup all sessions"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def teardown_all_sessions(self) -> dict[str, object]:
        """Teardown all managed sessions.

        Returns:
            dict[str, object]: Dictionary containing teardown results.

        Raises:
            YesmanError: If teardown fails.
        """
        try:
            sessions = self.session_manager.get_all_sessions()
            successful = []
            failed = []

            for session in sessions:
                session_name = getattr(session, "session_name", "unknown")
                try:
                    self._teardown_session_internal(session_name)
                    successful.append(session_name)
                except Exception as e:
                    self.logger.exception("Failed to teardown session '{session_name}': {e}")
                    failed.append({"session_name": session_name, "error": str(e)})

            return {
                "successful": successful,
                "failed": failed,
                "total": len(sessions),
                "removed": len(successful),
            }

        except Exception as e:
            self.logger.exception("Failed to teardown all sessions: {e}")
            msg = "Failed to teardown all sessions"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def start_session(self, session_name: str) -> dict[str, object]:
        """Start or create and start a session.

        Returns:
            dict[str, object]: Dictionary containing session start details.

        Raises:
            YesmanError: If session start fails.
        """
        try:
            # Check if session exists in tmux
            session_exists = False
            try:
                result = subprocess.run(
                    ["tmux", "has-session", "-t", session_name],
                    check=False,
                    capture_output=True,
                )
                session_exists = result.returncode == 0
            except Exception:
                session_exists = False

            if session_exists:
                # Check if session is already attached (has active clients)
                try:
                    client_result = subprocess.run(
                        ["tmux", "list-clients", "-t", session_name],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    if client_result.returncode == 0 and client_result.stdout.strip():
                        msg = f"Session '{session_name}' is already running"
                        raise YesmanError(
                            msg,
                            category=ErrorCategory.VALIDATION,
                        )
                except subprocess.CalledProcessError:
                    # Session exists but no clients attached, continue
                    pass

                # Attach to the existing session in detached mode (for API usage)
                subprocess.run(["tmux", "attach-session", "-d", "-t", session_name], check=False)

                return {
                    "session_name": session_name,
                    "status": "started",
                    "action": "attached_to_existing",
                }
            # Session doesn't exist, try to create it first
            self.logger.info("Session '%s' not found, attempting to create it", session_name)

            # Try to setup the session first
            try:
                setup_result = self.setup_session(session_name)
                self.logger.info("Successfully created session '%s': %s", session_name, setup_result)

                return {
                    "session_name": session_name,
                    "status": "started",
                    "action": "created_and_started",
                    "setup_result": setup_result,
                }
            except YesmanError as setup_error:
                if "already exists" in str(setup_error.message):
                    # Session was created in between checks, try to attach
                    subprocess.run(
                        ["tmux", "attach-session", "-d", "-t", session_name],
                        check=False,
                    )
                    return {
                        "session_name": session_name,
                        "status": "started",
                        "action": "attached_after_race_condition",
                    }
                # Re-raise the setup error instead of silently failing
                self.logger.exception(
                    "Failed to setup session '%s': %s",
                    session_name,
                    setup_error.message,
                )
                raise

        except YesmanError:
            raise
        except Exception as e:
            self.logger.exception("Failed to start session {session_name}: {e}")
            msg = f"Failed to start session '{session_name}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def stop_session(self, session_name: str) -> dict[str, object]:
        """Stop a running session.

        Returns:
            dict[str, object]: Dictionary containing stop status.

        Raises:
            YesmanError: If session not found or stop fails.
        """
        try:
            if not self._session_exists(session_name):
                msg = f"Session '{session_name}' not found"
                raise YesmanError(
                    msg,
                    category=ErrorCategory.VALIDATION,
                )

            # Kill the session
            self._teardown_session_internal(session_name)

            return {
                "session_name": session_name,
                "status": "stopped",
            }

        except YesmanError:
            raise
        except Exception as e:
            self.logger.exception("Failed to stop session {session_name}: {e}")
            msg = f"Failed to stop session '{session_name}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def _convert_session_to_api_data(self, session_data: object) -> SessionAPIData:
        """Convert internal session data to API format.

        Returns:
            SessionAPIData: Converted session data in API format.

        Raises:
            YesmanError: If conversion fails.
        """
        try:
            # Cast to known SessionInfo type for proper attribute access
            if hasattr(session_data, "session_name"):
                session_info = cast("SessionInfo", session_data)

                session_status = session_info.status
                # Ensure status is a valid SessionStatusType
                if session_status not in {
                    "running",
                    "stopped",
                    "unknown",
                    "starting",
                    "stopping",
                }:
                    session_status = "unknown"

                return {
                    "session_name": session_info.session_name,
                    "status": cast("SessionStatusType", session_status),
                    "windows": [
                        {
                            "index": int(getattr(w, "index", i)),
                            "name": getattr(w, "name", f"window_{i}"),
                            "panes": [
                                {
                                    "command": getattr(p, "command", ""),
                                    "is_claude": getattr(p, "is_claude", False),
                                    "is_controller": getattr(p, "is_controller", False),
                                }
                                for p in getattr(w, "panes", [])
                            ],
                        }
                        for i, w in enumerate(session_info.windows)
                    ],
                    "created_at": getattr(session_info, "created_at", None),
                    "last_activity": getattr(session_info, "last_activity", None),
                }
            # Fallback for dict-like objects
            session_status = getattr(session_data, "status", "unknown")
            if session_status not in {
                "running",
                "stopped",
                "unknown",
                "starting",
                "stopping",
            }:
                session_status = "unknown"

            return {
                "session_name": getattr(session_data, "session_name", "unknown"),
                "status": cast("SessionStatusType", session_status),
                "windows": [],
                "created_at": None,
                "last_activity": None,
            }
        except Exception as e:
            self.logger.exception("Failed to convert session data: {e}")
            msg = "Failed to convert session data format"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def _session_exists(self, session_name: str) -> bool:
        """Check if session exists.

        Returns:
            bool: True if session exists, False otherwise.
        """
        try:
            # Check directly with tmux as the source of truth
            result = subprocess.run(
                ["tmux", "has-session", "-t", session_name],
                check=False,
                capture_output=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _setup_session_internal(self, session_name: str, session_config: dict[str, object]) -> dict[str, object]:
        """Internal session setup logic.

        Returns:
            dict[str, object]: Dictionary containing session creation details.

        Raises:
            YesmanError: If session creation fails.
        """
        try:
            # Get template and project path from config
            template = str(session_config.get("template_name", "default"))
            override_config = cast("dict", session_config.get("override", {}))

            # Use override session name if provided, otherwise use session_name
            actual_session_name = str(override_config.get("session_name", session_name))

            # Get start directory from override config
            start_directory = str(override_config.get("start_directory", "."))
            project_path = start_directory
            # Create tmux session
            create_cmd = ["tmux", "new-session", "-d", "-s", actual_session_name]

            # Set working directory if specified
            if project_path and project_path != ".":
                # Expand ~ to home directory
                expanded_path = pathlib.Path(project_path).expanduser()
                create_cmd.extend(["-c", str(expanded_path)])

            # Create the session
            self.logger.info("Running tmux command: %s", " ".join(create_cmd))
            result = subprocess.run(create_cmd, check=False, capture_output=True, text=True)

            self.logger.info(
                "tmux command result: returncode=%s, stdout=%s, stderr=%s",
                result.returncode,
                result.stdout,
                result.stderr,
            )

            if result.returncode != 0:
                if "duplicate session" in result.stderr:
                    msg = f"Session '{actual_session_name}' already exists"
                    raise YesmanError(msg, category=ErrorCategory.VALIDATION)
                msg = f"Failed to create session: {result.stderr}"
                raise YesmanError(msg, category=ErrorCategory.SYSTEM)

            self.logger.info("Created tmux session '%s'", actual_session_name)

            # Setup windows based on override configuration
            windows_config = override_config.get("windows", [])
            if isinstance(windows_config, list) and windows_config:
                for window_idx, window_config in enumerate(windows_config):
                    if isinstance(window_config, dict):
                        window_name = window_config.get("window_name", f"window{window_idx}")
                        # Create new window (except for the first one which already exists)
                        if window_idx > 0:
                            subprocess.run(
                                [
                                    "tmux",
                                    "new-window",
                                    "-t",
                                    actual_session_name,
                                    "-n",
                                    window_name,
                                ],
                                check=False,
                                capture_output=True,
                            )
                        else:
                            # Rename the first window
                            subprocess.run(
                                [
                                    "tmux",
                                    "rename-window",
                                    "-t",
                                    f"{actual_session_name}:0",
                                    window_name,
                                ],
                                check=False,
                                capture_output=True,
                            )

            return {
                "message": "Session setup completed",
                "session_name": actual_session_name,
                "template": template,
                "project_path": project_path,
            }

        except subprocess.CalledProcessError as e:
            msg = f"Failed to create tmux session: {e}"
            raise YesmanError(msg, category=ErrorCategory.SYSTEM, cause=e)
        except Exception as e:
            msg = f"Unexpected error during session setup: {e}"
            raise YesmanError(msg, category=ErrorCategory.SYSTEM, cause=e)

    @staticmethod
    def _teardown_session_internal(session_name: str) -> None:
        """Internal session teardown logic.

        Raises:
            YesmanError: If teardown fails.
        """
        try:
            subprocess.run(
                ["tmux", "kill-session", "-t", session_name],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            msg = f"Failed to kill session: {e}"
            raise YesmanError(msg)


# Router with dependency injection
router = APIRouter(tags=["sessions"])


@router.get(
    "/sessions",
    response_model=list[models.SessionInfo],
    summary="Get all sessions",
    description="Retrieve information about all active tmux sessions",
)
def get_all_sessions() -> object:
    """Get all tmux sessions with detailed information.

    Returns:
        list[models.SessionInfo]: List of all session information.

    Raises:
        HTTPException: If session retrieval fails.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        sessions_data = service.get_all_sessions()

        # Convert to Pydantic models
        result = []
        for session in sessions_data:
            if isinstance(session, dict):
                windows = []
                for window in session.get("windows", []):
                    if isinstance(window, dict):
                        panes = [
                            models.PaneInfo(
                                command=str(pane.get("command", "")),
                                is_claude=bool(pane.get("is_claude", False)),
                                is_controller=bool(pane.get("is_controller", False)),
                            )
                            for pane in cast("list", window.get("panes", []))
                            if isinstance(pane, dict)
                        ]
                        windows.append(
                            models.WindowInfo(
                                index=int(cast("int", window.get("index", 0))),
                                name=str(window.get("name", "")),
                                panes=panes,
                            )
                        )

                # Ensure status is valid
                session_status = str(session.get("status", "unknown"))
                if session_status not in {
                    "running",
                    "stopped",
                    "unknown",
                    "starting",
                    "stopping",
                }:
                    session_status = "unknown"

                result.append(
                    models.SessionInfo(
                        session_name=str(session.get("session_name", "")),
                        project_name=(str(session.get("project_name", "")) if session.get("project_name") else None),
                        status=session_status,
                        template=(str(session.get("template", "")) if session.get("template") else None),
                        windows=windows,
                    )
                )
        return result

    except YesmanError as e:
        logger.exception("YesmanError in get_all_sessions: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
    except Exception:
        logger.exception("Unexpected error in get_all_sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/sessions/{session_name}",
    response_model=models.SessionInfo,
    summary="Get specific session",
    description="Retrieve information about a specific session",
)
def get_session(session_name: str) -> object:
    """Get specific session by name.

    Returns:
        models.SessionInfo: Session information.

    Raises:
        HTTPException: If session not found or retrieval fails.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        session_data = service.get_session_by_name(session_name)

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_name}' not found",
            )

        # Convert to Pydantic model
        windows = []
        if isinstance(session_data, dict):
            for window in session_data.get("windows", []):
                if isinstance(window, dict):
                    panes = [
                        models.PaneInfo(
                            command=str(pane.get("command", "")),
                            is_claude=bool(pane.get("is_claude", False)),
                            is_controller=bool(pane.get("is_controller", False)),
                        )
                        for pane in cast("list", window.get("panes", []))
                        if isinstance(pane, dict)
                    ]
                    windows.append(
                        models.WindowInfo(
                            index=int(cast("int", window.get("index", 0))),
                            name=str(window.get("name", "")),
                            panes=panes,
                        )
                    )

            # Ensure status is valid
            session_status = str(session_data.get("status", "unknown"))
            if session_status not in {
                "running",
                "stopped",
                "unknown",
                "starting",
                "stopping",
            }:
                session_status = "unknown"

            return models.SessionInfo(
                session_name=str(session_data.get("session_name", "")),
                project_name=(str(session_data.get("project_name", "")) if session_data.get("project_name") else None),
                status=session_status,
                template=(str(session_data.get("template", "")) if session_data.get("template") else None),
                windows=windows,
            )
        return models.SessionInfo(
            session_name="unknown",
            project_name=None,
            status="unknown",
            template=None,
            windows=[],
        )

    except HTTPException:
        raise
    except YesmanError as e:
        logger.exception("YesmanError in get_session: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
    except Exception:
        logger.exception("Unexpected error in get_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/{session_name}/setup",
    summary="Setup session",
    description="Create and setup a tmux session",
)
def setup_session(session_name: str) -> object:
    """Setup a specific session.

    Returns:
        dict: Session setup result.

    Raises:
        HTTPException: If session setup fails.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        return service.setup_session(session_name)

    except YesmanError as e:
        logger.exception("YesmanError in setup_session: {e.message}")
        status_code = status.HTTP_400_BAD_REQUEST if e.category == ErrorCategory.VALIDATION else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=e.message)
    except Exception:
        logger.exception("Unexpected error in setup_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete(
    "/sessions/{session_name}",
    summary="Teardown session",
    description="Remove a tmux session",
)
def teardown_session(session_name: str) -> object:
    """Teardown a specific session.

    Returns:
        dict: Session teardown result.

    Raises:
        HTTPException: If session teardown fails.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        return service.teardown_session(session_name)

    except YesmanError as e:
        logger.exception("YesmanError in teardown_session: {e.message}")
        status_code = status.HTTP_404_NOT_FOUND if e.category == ErrorCategory.VALIDATION else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=e.message)
    except Exception:
        logger.exception("Unexpected error in teardown_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/sessions/{session_name}/status",
    summary="Get session status",
    description="Get current status of a session",
)
def get_session_status(session_name: str) -> object:
    """Get session status.

    Returns:
        dict: Dictionary containing session status information.

    Raises:
        HTTPException: If status retrieval fails.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        return service.get_session_status(session_name)

    except YesmanError as e:
        logger.exception("YesmanError in get_session_status: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
    except Exception:
        logger.exception("Unexpected error in get_session_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/setup-all",
    summary="Setup all sessions",
    description="Create and setup all tmux sessions defined in sessions/ directory",
)
def setup_all_sessions() -> object:
    """Setup all sessions from projects configuration.

    Returns:
        dict: Setup results for all sessions.

    Raises:
        HTTPException: If setup fails.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        return service.setup_all_sessions()

    except YesmanError as e:
        logger.exception("YesmanError in setup_all_sessions: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
    except Exception:
        logger.exception("Unexpected error in setup_all_sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/teardown-all",
    summary="Teardown all sessions",
    description="Remove all managed tmux sessions",
)
def teardown_all_sessions() -> object:
    """Teardown all managed sessions.

    Returns:
        dict: Teardown results for all sessions.

    Raises:
        HTTPException: If teardown fails.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        return service.teardown_all_sessions()

    except YesmanError as e:
        logger.exception("YesmanError in teardown_all_sessions: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
    except Exception:
        logger.exception("Unexpected error in teardown_all_sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/{session_name}/start",
    summary="Start session",
    description="Start an existing tmux session",
)
def start_session(session_name: str) -> object:
    """Start a specific session.

    Returns:
        dict: Session start result.

    Raises:
        HTTPException: If session start fails.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        return service.start_session(session_name)

    except YesmanError as e:
        logger.exception("YesmanError in start_session: {e.message}")
        status_code = status.HTTP_400_BAD_REQUEST if e.category == ErrorCategory.VALIDATION else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=e.message)
    except Exception:
        logger.exception("Unexpected error in start_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/{session_name}/stop",
    summary="Stop session",
    description="Stop a running tmux session",
)
def stop_session(session_name: str) -> object:
    """Stop a specific session.

    Returns:
        dict: Session stop result.

    Raises:
        HTTPException: If session stop fails.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        return service.stop_session(session_name)

    except YesmanError as e:
        logger.exception("YesmanError in stop_session: {e.message}")
        status_code = status.HTTP_404_NOT_FOUND if e.category == ErrorCategory.VALIDATION else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=e.message)
    except Exception:
        logger.exception("Unexpected error in stop_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
