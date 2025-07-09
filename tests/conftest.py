"""
pytest 전역 설정 파일
테스트 실행 시 자동으로 로드되며, 공통 fixture와 설정을 제공
"""

import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fixture imports
from tests.fixtures.mock_data import (
    MockTmuxSession, MockClaudeProcess,
    MOCK_SESSION_DATA, MOCK_PROMPTS
)
from tests.fixtures.test_helpers import (
    temp_directory, temp_file, create_test_config
)

# 공통 Fixtures
@pytest.fixture
def mock_tmux_session():
    """Mock tmux 세션 fixture"""
    return MockTmuxSession("test-session")

@pytest.fixture
def mock_claude_process():
    """Mock Claude 프로세스 fixture"""
    return MockClaudeProcess()


@pytest.fixture
def temp_dir():
    """임시 디렉토리 fixture"""
    with temp_directory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_session_data():
    """샘플 세션 데이터 fixture"""
    return MOCK_SESSION_DATA.copy()

@pytest.fixture
def sample_prompts():
    """샘플 프롬프트 데이터 fixture"""
    return MOCK_PROMPTS.copy()

@pytest.fixture
def test_config_file(temp_dir):
    """테스트용 설정 파일 fixture"""
    config = {
        "yesman": {
            "log_level": "DEBUG",
            "auto_response": {
                "enabled": True,
                "default_choice": "1"
            }
        }
    }
    config_path = Path(temp_dir) / "test_config.yaml"
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return config_path

# pytest 설정
def pytest_configure(config):
    """pytest 설정 커스터마이징"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

# 테스트 세션 시작/종료 훅
def pytest_sessionstart(session):
    """테스트 세션 시작 시 실행"""
    print("\n🧪 Starting Yesman-Claude test suite...")

def pytest_sessionfinish(session, exitstatus):
    """테스트 세션 종료 시 실행"""
    print(f"\n✅ Test suite completed with exit status: {exitstatus}")

# 테스트 결과 리포팅 커스터마이징
def pytest_report_teststatus(report, config):
    """테스트 상태 리포팅 커스터마이징"""
    if report.when == 'call':
        if report.passed:
            return "passed", "✓", "PASSED"
        elif report.failed:
            return "failed", "✗", "FAILED"
        elif report.skipped:
            return "skipped", "⊘", "SKIPPED"