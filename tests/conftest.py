"""pytest 전역 설정 파일
테스트 실행 시 자동으로 로드되며, 공통 fixture와 설정을 제공.
"""

import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fixture imports
from tests.fixtures.mock_data import (
    MOCK_PROMPTS,
    MOCK_SESSION_DATA,
    MockClaudeProcess,
    MockTmuxSession,
)
from tests.fixtures.mock_factories import ComponentMockFactory, ManagerMockFactory
from tests.fixtures.test_helpers import temp_directory


# 공통 Fixtures
@pytest.fixture
def mock_tmux_session():
    """Mock tmux 세션 fixture."""
    return MockTmuxSession("test-session")


@pytest.fixture
def mock_claude_process():
    """Mock Claude 프로세스 fixture."""
    return MockClaudeProcess()


# New Factory-based Fixtures
@pytest.fixture
def mock_session_manager():
    """Centralized SessionManager mock fixture."""
    return ManagerMockFactory.create_session_manager_mock()


@pytest.fixture
def mock_claude_manager():
    """Centralized ClaudeManager mock fixture."""
    return ManagerMockFactory.create_claude_manager_mock()


@pytest.fixture
def mock_tmux_manager():
    """Centralized TmuxManager mock fixture."""
    return ManagerMockFactory.create_tmux_manager_mock()


@pytest.fixture
def mock_subprocess_result():
    """Standard subprocess.run result mock."""
    return ComponentMockFactory.create_subprocess_mock()


@pytest.fixture
def mock_api_response():
    """Standard API response mock."""
    return ComponentMockFactory.create_api_response_mock()


@pytest.fixture
def temp_dir():
    """임시 디렉토리 fixture."""
    with temp_directory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_session_data():
    """샘플 세션 데이터 fixture."""
    return MOCK_SESSION_DATA.copy()


@pytest.fixture
def sample_prompts():
    """샘플 프롬프트 데이터 fixture."""
    return MOCK_PROMPTS.copy()


@pytest.fixture
def test_config_file(temp_dir):
    """테스트용 설정 파일 fixture."""
    config = {
        "yesman": {
            "log_level": "DEBUG",
            "auto_response": {
                "enabled": True,
                "default_choice": "1",
            },
        },
    }
    config_path = Path(temp_dir) / "test_config.yaml"
    import yaml

    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def temp_project_root():
    """Create temporary project directory."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)

        # Create tauri-dashboard directory with package.json
        tauri_dir = project_root / "tauri-dashboard"
        tauri_dir.mkdir()
        (tauri_dir / "package.json").write_text('{"name": "test-dashboard"}')

        yield project_root


@pytest.fixture
def launcher(temp_project_root):
    """Create DashboardLauncher with temp project root."""
    from libs.dashboard import DashboardLauncher

    return DashboardLauncher(project_root=temp_project_root)


@pytest.fixture
def theme_manager():
    """Create ThemeManager instance."""
    import tempfile
    from pathlib import Path

    from libs.dashboard import ThemeManager

    with tempfile.TemporaryDirectory() as temp_dir:
        yield ThemeManager(config_dir=Path(temp_dir))


@pytest.fixture
def keyboard_manager():
    """Create KeyboardNavigationManager instance."""
    from libs.dashboard import KeyboardNavigationManager

    manager = KeyboardNavigationManager()
    yield manager
    # Cleanup
    manager.actions.clear()
    manager.bindings.clear()


@pytest.fixture
def performance_optimizer():
    """Create PerformanceOptimizer instance."""
    from libs.dashboard import PerformanceOptimizer

    optimizer = PerformanceOptimizer()
    yield optimizer
    # Cleanup
    if optimizer.monitoring:
        optimizer.stop_monitoring()


# pytest 설정
def pytest_configure(config):
    """Pytest 설정 커스터마이징."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests",
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests",
    )


# 테스트 세션 시작/종료 훅
def pytest_sessionstart(session):
    """테스트 세션 시작 시 실행."""
    print("\n🧪 Starting Yesman-Claude test suite...")


def pytest_sessionfinish(session, exitstatus):
    """테스트 세션 종료 시 실행."""
    print(f"\n✅ Test suite completed with exit status: {exitstatus}")


# 테스트 결과 리포팅 커스터마이징
def pytest_report_teststatus(report, config):
    """테스트 상태 리포팅 커스터마이징."""
    if report.when == "call":
        if report.passed:
            return "passed", "✓", "PASSED"
        elif report.failed:
            return "failed", "✗", "FAILED"
        elif report.skipped:
            return "skipped", "⊘", "SKIPPED"
