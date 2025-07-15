"""
Centralized Mock Factory System
Provides standardized mock objects to reduce duplication across test files
"""

from unittest.mock import MagicMock, patch

from .mock_data import MOCK_API_RESPONSES, MOCK_SESSION_DATA


class ManagerMockFactory:
    """Factory for commonly mocked manager classes"""

    @staticmethod
    def create_session_manager_mock(**kwargs) -> MagicMock:
        """
        Create a standardized SessionManager mock

        Args:
            sessions: List of session data (default: [MOCK_SESSION_DATA])
            create_session_result: Return value for create_session (default: True)
            get_session_info_result: Return value for get_session_info (default: MOCK_SESSION_DATA)
            validate_session_name_side_effect: Side effect for validation (default: None)
            **kwargs: Additional attributes to set on the mock

        Returns:
            MagicMock configured with standard SessionManager behavior
        """
        mock_manager = MagicMock()

        # Default behaviors
        sessions = kwargs.get("sessions", [MOCK_SESSION_DATA])
        mock_manager.get_sessions.return_value = sessions
        mock_manager.list_sessions.return_value = [s["session_name"] for s in sessions]

        # Create session behavior (return value or side effect)
        if "create_session_side_effect" in kwargs:
            mock_manager.create_session.side_effect = kwargs["create_session_side_effect"]
        else:
            mock_manager.create_session.return_value = kwargs.get("create_session_result", True)

        mock_manager.get_session_info.return_value = kwargs.get("get_session_info_result", MOCK_SESSION_DATA)

        # Validation behavior
        if "validate_session_name_side_effect" in kwargs:
            mock_manager.validate_session_name.side_effect = kwargs["validate_session_name_side_effect"]
        else:
            mock_manager.validate_session_name.return_value = None  # No exception = valid

        # Additional session operations
        mock_manager.start_session.return_value = True
        mock_manager.stop_session.return_value = True
        mock_manager.restart_session.return_value = True
        mock_manager.session_exists.return_value = True
        mock_manager.kill_session.return_value = True

        # Project management operations
        mock_manager.get_all_projects.return_value = kwargs.get("get_all_projects_result", [])

        # Set any additional attributes
        for key, value in kwargs.items():
            if not key.startswith("_") and not hasattr(mock_manager, key):
                setattr(mock_manager, key, value)

        return mock_manager

    @staticmethod
    def create_claude_manager_mock(**kwargs) -> MagicMock:
        """
        Create a standardized ClaudeManager mock

        Args:
            controller_count: Number of active controllers (default: 1)
            get_controller_result: Mock controller object (default: auto-generated)
            controllers_status: Status dict for all controllers (default: {"test-session": "running"})
            **kwargs: Additional attributes to set on the mock

        Returns:
            MagicMock configured with standard ClaudeManager behavior
        """
        mock_manager = MagicMock()

        # Default controller
        controller_count = kwargs.get("controller_count", 1)
        if "get_controller_result" in kwargs:
            mock_controller = kwargs["get_controller_result"]
        else:
            mock_controller = MagicMock()
            mock_controller.session_name = "test-session"
            mock_controller.status = "running"
            mock_controller.pid = 12345
            mock_controller.start.return_value = True
            mock_controller.stop.return_value = True
            mock_controller.restart.return_value = True
            mock_controller.is_running.return_value = True

        # Manager behaviors
        mock_manager.get_controller.return_value = mock_controller
        mock_manager.create_controller.return_value = mock_controller
        mock_manager.list_controllers.return_value = [mock_controller] * controller_count
        mock_manager.get_controller_count.return_value = controller_count

        # Status tracking
        controllers_status = kwargs.get("controllers_status", {"test-session": "running"})
        mock_manager.get_all_status.return_value = controllers_status
        mock_manager.get_status.return_value = list(controllers_status.values())[0] if controllers_status else "stopped"

        # Session operations
        mock_manager.start_session.return_value = True
        mock_manager.stop_session.return_value = True
        mock_manager.stop_all.return_value = True

        # Set any additional attributes
        for key, value in kwargs.items():
            if not key.startswith("_") and not hasattr(mock_manager, key):
                setattr(mock_manager, key, value)

        return mock_manager

    @staticmethod
    def create_tmux_manager_mock(**kwargs) -> MagicMock:
        """
        Create a standardized TmuxManager mock

        Args:
            sessions: List of session names (default: ["test-session"])
            list_sessions_result: Return value for list_sessions (default: sessions)
            session_exists_result: Return value for session_exists (default: True)
            **kwargs: Additional attributes to set on the mock

        Returns:
            MagicMock configured with standard TmuxManager behavior
        """
        mock_manager = MagicMock()

        # Default sessions
        sessions = kwargs.get("sessions", ["test-session"])
        mock_manager.list_sessions.return_value = kwargs.get("list_sessions_result", sessions)
        mock_manager.session_exists.return_value = kwargs.get("session_exists_result", True)

        # Session operations
        mock_manager.create_session.return_value = True
        mock_manager.kill_session.return_value = True
        mock_manager.attach_session.return_value = True

        # Server operations
        mock_manager.server_running.return_value = True
        mock_manager.start_server.return_value = True

        # Project loading operations (for setup/up commands)
        mock_manager.load_projects.return_value = kwargs.get("load_projects_result", {"sessions": {}})
        mock_manager.list_running_sessions.return_value = None

        # Set any additional attributes
        for key, value in kwargs.items():
            if not key.startswith("_") and not hasattr(mock_manager, key):
                setattr(mock_manager, key, value)

        return mock_manager


class ComponentMockFactory:
    """Factory for commonly mocked component objects"""

    @staticmethod
    def create_tmux_session_mock(name: str = "test-session", **kwargs) -> MagicMock:
        """Create a standardized tmux session mock"""
        mock_session = MagicMock()
        mock_session.name = name
        mock_session.id = f"${name}:0"
        mock_session.created = kwargs.get("created", "2024-01-01T00:00:00")

        # Windows
        windows = kwargs.get("windows", [])
        mock_session.list_windows.return_value = windows
        mock_session.window_count = len(windows)

        # Operations
        mock_session.kill_session.return_value = None
        mock_session.rename_session.return_value = None
        mock_session.new_window.return_value = MagicMock()

        return mock_session

    @staticmethod
    def create_subprocess_mock(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
        """Create a standardized subprocess.run result mock"""
        mock_result = MagicMock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        mock_result.stderr = stderr
        mock_result.check_returncode.return_value = None if returncode == 0 else Exception(f"Command failed with code {returncode}")

        return mock_result

    @staticmethod
    def create_api_response_mock(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
        """Create a standardized API response mock"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or MOCK_API_RESPONSES["sessions_list"]
        mock_response.text = str(json_data) if json_data else ""
        mock_response.ok = status_code < 400

        return mock_response


class PatchContextFactory:
    """Factory for common patch contexts"""

    @staticmethod
    def patch_session_manager(**kwargs):
        """Create a patch context for SessionManager with standard mock"""
        mock_manager = ManagerMockFactory.create_session_manager_mock(**kwargs)
        return patch("libs.core.session_manager.SessionManager", return_value=mock_manager)

    @staticmethod
    def patch_claude_manager(**kwargs):
        """Create a patch context for ClaudeManager with standard mock"""
        mock_manager = ManagerMockFactory.create_claude_manager_mock(**kwargs)
        return patch("libs.core.claude_manager.ClaudeManager", return_value=mock_manager)

    @staticmethod
    def patch_tmux_manager(**kwargs):
        """Create a patch context for TmuxManager with standard mock"""
        mock_manager = ManagerMockFactory.create_tmux_manager_mock(**kwargs)
        return patch("libs.tmux_manager.TmuxManager", return_value=mock_manager)

    @staticmethod
    def patch_setup_tmux_manager(**kwargs):
        """Create a patch context for TmuxManager in setup commands"""
        mock_manager = ManagerMockFactory.create_tmux_manager_mock(**kwargs)
        return patch("commands.setup.TmuxManager", return_value=mock_manager)

    @staticmethod
    def patch_subprocess_run(**kwargs):
        """Create a patch context for subprocess.run with standard mock"""
        mock_result = ComponentMockFactory.create_subprocess_mock(**kwargs)
        return patch("subprocess.run", return_value=mock_result)


# Convenience exports for easy importing
__all__ = [
    "ManagerMockFactory",
    "ComponentMockFactory",
    "PatchContextFactory",
]
