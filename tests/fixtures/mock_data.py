# Copyright notice.

from datetime import UTC, datetime

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


# Simplified versions without factory dependencies
class EnhancedMockTmuxSession(MockTmuxSession):
    """Enhanced TmuxSession mock."""

    @classmethod
    def with_windows(cls, name: str = "test-session", window_count: int = 2) -> object:
        """Create mock with specified number of windows."""
        windows = [MockTmuxWindow(f"window-{i}") for i in range(window_count)]
        return cls(name=name, windows=windows)
