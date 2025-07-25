# Copyright notice.

import json
import os
import shutil
import tempfile
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml

from .mock_data import MockTmuxPane, MockTmuxSession

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""테스트 헬퍼 함수 및 유틸리티
테스트에서 자주 사용되는 공통 함수들을 제공.
"""


@contextmanager
def temp_directory() -> Generator[str, None, None]:
    """임시 디렉토리 생성 컨텍스트 매니저."""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@contextmanager
def temp_file(content: str = "", suffix: str = ".txt") -> Generator[str, None, None]:
    """임시 파일 생성 컨텍스트 매니저."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        yield path
    finally:
        os.unlink(path)


def create_test_config(config_dict: dict[str, Any], format: str = "yaml") -> str:
    """테스트용 설정 파일 생성."""
    with temp_file(suffix=f".{format}") as config_path:
        with open(config_path, "w", encoding="utf-8") as f:
            if format == "yaml":
                yaml.dump(config_dict, f)
            elif format == "json":
                json.dump(config_dict, f)
        return config_path


def create_mock_tmux_session(session_name: str = "test-session") -> object:
    """Mock tmux 세션 생성 헬퍼."""
    session = MockTmuxSession(session_name)
    window = session.new_window("main")
    window.panes = [
        MockTmuxPane(0, "$ claude code"),
        MockTmuxPane(1, "logs output here"),
    ]
    return session


def assert_files_equal(file1: str, file2: str) -> None:
    """두 파일의 내용이 동일한지 확인."""
    with open(file1, encoding="utf-8") as f1, open(file2, encoding="utf-8") as f2:
        assert f1.read() == f2.read(), f"Files {file1} and {file2} are not equal"


def create_test_project_structure(base_dir: str) -> None:
    """테스트용 프로젝트 구조 생성."""
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

    def create_structure(base_path: str, structure: dict[str, Any]) -> None:
        for name, content in structure.items():
            path = Path(base_path) / name
            if isinstance(content, dict):
                path.mkdir(exist_ok=True)
                create_structure(path, content)
            else:
                path.write_text(content)

    create_structure(base_dir, project_structure)


class CaptureOutput:
    """Stdout/stderr 캡처 헬퍼 클래스."""

    def __init__(self) -> None:
        self.stdout: list[str] = []
        self.stderr: list[str] = []

    def capture_stdout(self, text: str) -> None:
        self.stdout.append(text)

    def capture_stderr(self, text: str) -> None:
        self.stderr.append(text)

    def get_stdout(self) -> object:
        return "\n".join(self.stdout)

    def get_stderr(self) -> object:
        return "\n".join(self.stderr)

    def clear(self) -> None:
        self.stdout.clear()
        self.stderr.clear()


def wait_for_condition(
    condition_func: Callable[[], bool], timeout: float = 5, interval: float = 0.1
) -> bool:
    """조건이 만족될 때까지 대기."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)

    return False


def generate_test_data(data_type: str, count: int = 10) -> list[dict[str, Any]]:
    """테스트 데이터 생성기."""
    if data_type == "sessions":
        return [
            {
                "session_name": f"session-{i}",
                "status": "active" if i % 2 == 0 else "inactive",
                "created_at": f"2024-01-{i + 1:02d}T10:00:00",
            }
            for i in range(count)
        ]
    if data_type == "prompts":
        return [f"Test prompt {i}: [y/n]" for i in range(count)]
    return []
