"""
테스트 헬퍼 함수 및 유틸리티
테스트에서 자주 사용되는 공통 함수들을 제공
"""

import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

import yaml


@contextmanager
def temp_directory():
    """임시 디렉토리 생성 컨텍스트 매니저"""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@contextmanager
def temp_file(content="", suffix=".txt"):
    """임시 파일 생성 컨텍스트 매니저"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        yield path
    finally:
        os.unlink(path)


def create_test_config(config_dict, format="yaml"):
    """테스트용 설정 파일 생성"""
    with temp_file(suffix=f".{format}") as config_path:
        with open(config_path, "w") as f:
            if format == "yaml":
                yaml.dump(config_dict, f)
            elif format == "json":
                json.dump(config_dict, f)
        return config_path


def create_mock_tmux_session(session_name="test-session"):
    """Mock tmux 세션 생성 헬퍼"""
    from .mock_data import MockTmuxPane, MockTmuxSession

    session = MockTmuxSession(session_name)
    window = session.new_window("main")
    window.panes = [
        MockTmuxPane(0, "$ claude code"),
        MockTmuxPane(1, "logs output here"),
    ]
    return session


def assert_files_equal(file1, file2):
    """두 파일의 내용이 동일한지 확인"""
    with open(file1) as f1, open(file2) as f2:
        assert f1.read() == f2.read(), f"Files {file1} and {file2} are not equal"


def create_test_project_structure(base_dir):
    """테스트용 프로젝트 구조 생성"""
    project_structure = {
        "src": {
            "__init__.py": "",
            "main.py": "# Main application file",
            "utils.py": "# Utility functions",
        },
        "tests": {
            "__init__.py": "",
            "test_main.py": "# Test cases",
        },
        "config.yaml": "app_name: test_app\nversion: 1.0.0",
        "README.md": "# Test Project",
    }

    def create_structure(base_path, structure):
        for name, content in structure.items():
            path = Path(base_path) / name
            if isinstance(content, dict):
                path.mkdir(exist_ok=True)
                create_structure(path, content)
            else:
                path.write_text(content)

    create_structure(base_dir, project_structure)


class CaptureOutput:
    """stdout/stderr 캡처 헬퍼 클래스"""

    def __init__(self):
        self.stdout = []
        self.stderr = []

    def capture_stdout(self, text):
        self.stdout.append(text)

    def capture_stderr(self, text):
        self.stderr.append(text)

    def get_stdout(self):
        return "\n".join(self.stdout)

    def get_stderr(self):
        return "\n".join(self.stderr)

    def clear(self):
        self.stdout.clear()
        self.stderr.clear()


def wait_for_condition(condition_func, timeout=5, interval=0.1):
    """조건이 만족될 때까지 대기"""
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)

    return False


def generate_test_data(data_type, count=10):
    """테스트 데이터 생성기"""
    if data_type == "sessions":
        return [
            {
                "session_name": f"session-{i}",
                "status": "active" if i % 2 == 0 else "inactive",
                "created_at": f"2024-01-{i + 1:02d}T10:00:00",
            }
            for i in range(count)
        ]
    elif data_type == "prompts":
        return [f"Test prompt {i}: [y/n]" for i in range(count)]
    else:
        return []
