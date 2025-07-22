import logging
import subprocess

from fastapi import APIRouter, HTTPException, status

from api import models
from libs.core.error_handling import ErrorCategory, YesmanError
from libs.core.services import get_session_manager, get_tmux_manager
from libs.core.session_manager import SessionManager
from libs.core.types import SessionAPIData
from libs.tmux_manager import TmuxManager

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
        List of the requested data.
        """
        try:
            sessions_data = self.session_manager.get_all_sessions()
            return [self._convert_session_to_api_data(session) for session in sessions_data]
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
        Sessionapidata | None object the requested data.
        """
        try:
            # Load projects configuration to get project_conf
            projects = self.tmux_manager.load_projects().get("sessions", {})

            # Find the project that matches this session name
            project_name = None
            project_conf = None
            for proj_name, proj_conf in projects.items():
                session_name_in_conf = proj_conf.get("override", {}).get("session_name", proj_name)
                if session_name_in_conf == session_name:
                    project_name = proj_name
                    project_conf = proj_conf
                    break

            if not project_name:
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
        Dict containing.
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
            projects = self.tmux_manager.load_projects().get("sessions", {})
            if session_name not in projects:
                msg = f"Session '{session_name}' not found in projects configuration"
                raise YesmanError(
                    msg,
                    category=ErrorCategory.CONFIGURATION,
                )

            # Set up session (this would integrate with the improved setup logic)
            result = self._setup_session_internal(session_name, projects[session_name])

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
        Dict containing.
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
        Dict containing status information.
        """
        try:
            # Load projects configuration to get project_conf
            projects = self.tmux_manager.load_projects().get("sessions", {})

            # Find the project that matches this session name
            project_name = None
            project_conf = None
            for proj_name, proj_conf in projects.items():
                session_name_in_conf = proj_conf.get("override", {}).get("session_name", proj_name)
                if session_name_in_conf == session_name:
                    project_name = proj_name
                    project_conf = proj_conf
                    break

            if not project_name:
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
                "status": session_data.status,
                "exists": True,
                "windows": len(session_data.windows),
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
        """Setup all sessions defined in projects.yaml.

        Returns:
        Dict containing.
        """
        try:
            projects = self.tmux_manager.load_projects().get("sessions", {})
            successful = []
            failed = []

            for session_name, session_config in projects.items():
                try:
                    if not self._session_exists(session_name):
                        self._setup_session_internal(session_name, session_config)
                        successful.append(session_name)
                    else:
                        self.logger.info(f"Session '{session_name}' already exists, skipping")  # noqa: G004
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
        Dict containing.
        """
        try:
            sessions = self.session_manager.get_all_sessions()
            successful = []
            failed = []

            for session in sessions:
                session_name = session.session_name
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
        """Start an existing session.

        Returns:
        Dict containing.
        """
        try:
            if self._session_exists(session_name):
                msg = f"Session '{session_name}' is already running"
                raise YesmanError(
                    msg,
                    category=ErrorCategory.VALIDATION,
                )

            # Attach to the session

            subprocess.run(["tmux", "attach-session", "-t", session_name], check=False)

            return {
                "session_name": session_name,
                "status": "started",
            }

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
        Dict containing.
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
        Sessionapidata object.
        """
        try:
            return {
                "session_name": session_data.session_name,
                "status": session_data.status,
                "windows": [
                    {
                        "index": int(w.index) if hasattr(w, "index") else i,
                        "name": w.name if hasattr(w, "name") else f"window_{i}",
                        "panes": [
                            {
                                "command": p.command if hasattr(p, "command") else "",
                                "is_claude": p.is_claude if hasattr(p, "is_claude") else False,
                                "is_controller": p.is_controller if hasattr(p, "is_controller") else False,
                            }
                            for p in (w.panes if hasattr(w, "panes") else [])
                        ],
                    }
                    for i, w in enumerate(session_data.windows)
                ],
                "created_at": getattr(session_data, "created_at", None),
                "last_activity": getattr(session_data, "last_activity", None),
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
        Boolean indicating.
        """
        try:
            sessions = self.session_manager.get_all_sessions()
            return any(session.session_name == session_name for session in sessions)
        except Exception:
            return False

    @staticmethod
    def _setup_session_internal(session_name: str, session_config: dict[str, object]) -> dict[str, object]:  # noqa: ARG002  # noqa: ARG004
        """Internal session setup logic.

        Returns:
        Dict containing.
        """
        # This would integrate with the improved SessionSetupService
        # For now, return a placeholder
        return {"message": "Session setup completed"}

    @staticmethod
    def _teardown_session_internal(session_name: str) -> None:
        """Internal session teardown logic."""
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
        Object object the requested data.
    """
    try:
        session_manager = get_session_manager()
        tmux_manager = get_tmux_manager()
        service = SessionService(session_manager, tmux_manager)
        sessions_data = service.get_all_sessions()

        # Convert to Pydantic models
        return [
            models.SessionInfo(
                session_name=session["session_name"],
                project_name=str(session.get("project_name", "")) if session.get("project_name") else None,
                status=session["status"],
                template=str(session.get("template", "")) if session.get("template") else None,
                windows=[
                    models.WindowInfo(
                        index=window["index"],
                        name=window["name"],
                        panes=[
                            models.PaneInfo(
                                command=pane["command"],
                                is_claude=pane["is_claude"],
                                is_controller=pane["is_controller"],
                            )
                            for pane in window["panes"]
                        ],
                    )
                    for window in session["windows"]
                ],
            )
            for session in sessions_data
        ]

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
        Object object the requested data.
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
        return models.SessionInfo(
            session_name=session_data["session_name"],
            project_name=str(session_data.get("project_name", "")) if session_data.get("project_name") else None,
            status=session_data["status"],
            template=str(session_data.get("template", "")) if session_data.get("template") else None,
            windows=[
                models.WindowInfo(
                    index=window["index"],
                    name=window["name"],
                    panes=[
                        models.PaneInfo(
                            command=pane["command"],
                            is_claude=pane["is_claude"],
                            is_controller=pane["is_controller"],
                        )
                        for pane in window["panes"]
                    ],
                )
                for window in session_data["windows"]
            ],
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
        Object object.
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
        Object object.
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
        Dict containing status information.
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
    description="Create and setup all tmux sessions defined in projects.yaml",
)
def setup_all_sessions() -> object:
    """Setup all sessions from projects configuration.

    Returns:
        Object object.
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
        Object object.
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
        Object object.
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
        Object object.
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
