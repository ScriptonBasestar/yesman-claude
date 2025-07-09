"""
공통 Mock 데이터 정의
테스트에서 재사용 가능한 mock 객체들을 중앙화
"""

from unittest.mock import Mock, MagicMock
from datetime import datetime

# Tmux 관련 Mock
class MockTmuxSession:
    """Tmux 세션 Mock 객체"""
    def __init__(self, name="test-session", windows=None):
        self.name = name
        self.windows = windows or []
        self.id = f"${name}:0"
        self.created_time = datetime.now()
        
    def list_windows(self):
        return self.windows
        
    def new_window(self, window_name):
        window = MockTmuxWindow(window_name)
        self.windows.append(window)
        return window

class MockTmuxWindow:
    """Tmux 윈도우 Mock 객체"""
    def __init__(self, name="test-window"):
        self.name = name
        self.panes = []
        
    def list_panes(self):
        return self.panes

class MockTmuxPane:
    """Tmux 패인 Mock 객체"""
    def __init__(self, index=0, content=""):
        self.index = index
        self.content = content
        
    def capture_pane(self):
        return self.content

# Claude 관련 Mock
class MockClaudeProcess:
    """Claude 프로세스 Mock 객체"""
    def __init__(self, pid=12345, status="running"):
        self.pid = pid
        self.status = status
        self.start_time = datetime.now()
        
    def terminate(self):
        self.status = "terminated"
        
    def is_running(self):
        return self.status == "running"


# 세션 관련 Mock 데이터
MOCK_SESSION_DATA = {
    "session_name": "test-session",
    "project_name": "test-project",
    "status": "active",
    "windows": [
        {"name": "main", "panes": 2},
        {"name": "logs", "panes": 1}
    ],
    "controller_status": "running",
    "controller_pid": 12345,
    "created_at": "2024-01-08T10:00:00",
    "last_activity": "2024-01-08T10:30:00"
}

# 프롬프트 관련 Mock 데이터
MOCK_PROMPTS = {
    "yes_no": "Do you want to continue? [y/n]: ",
    "numbered": "Select an option:\n1. Option A\n2. Option B\n3. Option C\nEnter choice: ",
    "file_overwrite": "File exists. Overwrite? (y/N): ",
    "trust_prompt": "Do you trust this workspace? [y/n]: "
}

# API 응답 Mock 데이터
MOCK_API_RESPONSES = {
    "sessions_list": {
        "status": "success",
        "data": [MOCK_SESSION_DATA],
        "count": 1
    },
    "controller_start": {
        "status": "success",
        "message": "Controller started",
        "pid": 12345
    },
    "error_response": {
        "status": "error",
        "message": "Internal server error",
        "code": 500
    }
}