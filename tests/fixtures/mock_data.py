# Copyright notice.

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

# Import here to avoid circular imports
# Moved to the end of file to avoid circular imports
from .mock_factories import ComponentMockFactory, ManagerMockFactory

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""공통 Mock 데이터 정의
테스트에서 재사용 가능한 mock 객체들을 중앙화.

Updated: Enhanced with factory system integration for better mock management
"""


# Tmux 관련 Mock


class MockTmuxSession:
    """Tmux 세션 Mock 객체."""

    def __init__(self, name: str = "test-session", windows: list[object] | None = None) -> None:
        self.name = name
        self.windows = windows or []
        self.id = f"${name}:0"
        self.created_time = datetime.now(UTC)

    def list_windows(self) -> object:
        return self.windows

    def new_window(self, window_name: str) -> "MockTmuxWindow":
        window = MockTmuxWindow(window_name)
        self.windows.append(window)
        return window


class MockTmuxWindow:
    """Tmux 윈도우 Mock 객체."""

    def __init__(self, name: str = "test-window") -> None:
        self.name = name
        self.panes: list[MockTmuxPane] = []

    def list_panes(self) -> object:
        return self.panes


class MockTmuxPane:
    """Tmux 패인 Mock 객체."""

    def __init__(self, index: int = 0, content: str = "") -> None:
        self.index = index
        self.content = content

    def capture_pane(self) -> object:
        return self.content


# Claude 관련 Mock
class MockClaudeProcess:
    """Claude 프로세스 Mock 객체."""

    def __init__(self, pid: int = 12345, status: str = "running") -> None:
        self.pid = pid
        self.status = status
        self.start_time = datetime.now(UTC)

    def terminate(self) -> None:
        self.status = "terminated"

    def is_running(self) -> object:
        return self.status == "running"


# 세션 관련 Mock 데이터
MOCK_SESSION_DATA = {
    "session_name": "test-session",
    "project_name": "test-project",
    "status": "active",
    "windows": [
        {"name": "main", "panes": 2},
        {"name": "logs", "panes": 1},
    ],
    "controller_status": "running",
    "controller_pid": 12345,
    "created_at": "2024-01-08T10:00:00",
    "last_activity": "2024-01-08T10:30:00",
}

# 프롬프트 관련 Mock 데이터
MOCK_PROMPTS = {
    "yes_no": "Do you want to continue? [y/n]: ",
    "numbered": ("Select an option:\n1. Option A\n2. Option B\n3. Option C\nEnter choice: "),
    "file_overwrite": "File exists. Overwrite? (y/N): ",
    "trust_prompt": "Do you trust this workspace? [y/n]: ",
}

# API 응답 Mock 데이터
MOCK_API_RESPONSES = {
    "sessions_list": {
        "status": "success",
        "data": [MOCK_SESSION_DATA],
        "count": 1,
    },
    "controller_start": {
        "status": "success",
        "message": "Controller started",
        "pid": 12345,
    },
    "error_response": {
        "status": "error",
        "message": "Internal server error",
        "code": 500,
    },
}


# Factory Integration - Bridge between old and new systems
def get_factory_mock(mock_type: str, **kwargs: Any) -> object:
    """Bridge function to get factory-created mocks Provides backward
    compatibility while encouraging factory usage.

    Args:
        mock_type: Type of mock to create ('session_manager', 'claude_manager', etc.)
        **kwargs: Arguments to pass to the factory

    Returns:
        Configured mock object from factory system
    """
    factory_map: dict[str, Callable[..., MagicMock]] = {
        "session_manager": ManagerMockFactory.create_session_manager_mock,
        "claude_manager": ManagerMockFactory.create_claude_manager_mock,
        "tmux_manager": ManagerMockFactory.create_tmux_manager_mock,
        "tmux_session": ComponentMockFactory.create_tmux_session_mock,
        "subprocess": ComponentMockFactory.create_subprocess_mock,
        "api_response": ComponentMockFactory.create_api_response_mock,
    }

    if mock_type not in factory_map:
        msg = f"Unknown mock type: {mock_type}. Available: {list(factory_map.keys())}"
        raise ValueError(msg)

    return factory_map[mock_type](**kwargs)


# Enhanced mock classes with factory integration
class EnhancedMockTmuxSession(MockTmuxSession):
    """Enhanced TmuxSession mock that integrates with factory system."""

    @classmethod
    def from_factory(cls, name: str = "test-session", **kwargs: Any) -> object:
        """Create enhanced mock using factory system."""
        return get_factory_mock("tmux_session", name=name, **kwargs)

    @classmethod
    def with_windows(cls, name: str = "test-session", window_count: int = 2) -> object:
        """Create mock with specified number of windows."""
        windows = [MockTmuxWindow(f"window-{i}") for i in range(window_count)]
        return cls.from_factory(name=name, windows=windows)


# Convenience functions for common mock patterns
def create_mock_session_with_controller(**kwargs: dict[str, object]) -> dict[str, Any]:
    """Create a complete mock session with controller for integration tests."""
    session_mock = get_factory_mock("session_manager", **kwargs)
    claude_mock = get_factory_mock("claude_manager", **kwargs)

    return {
        "session_manager": session_mock,
        "claude_manager": claude_mock,
        "session_data": MOCK_SESSION_DATA,
    }


def create_api_test_mocks(success: bool = True) -> dict[str, Any]:
    """Create standard API test mocks."""
    if success:
        return {
            "response": get_factory_mock(
                "api_response",
                status_code=200,
                json_data=MOCK_API_RESPONSES["sessions_list"],
            ),
            "session_manager": get_factory_mock("session_manager"),
        }
    return {
        "response": get_factory_mock(
            "api_response",
            status_code=500,
            json_data=MOCK_API_RESPONSES["error_response"],
        ),
        "session_manager": get_factory_mock("session_manager", create_session_result=False),
    }
