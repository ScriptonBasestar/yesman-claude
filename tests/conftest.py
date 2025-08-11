import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Dashboard imports
from libs.dashboard import (
    DashboardLauncher,
    KeyboardNavigationManager,
    PerformanceOptimizer,
    ThemeManager,
)

# Fixture imports
from tests.fixtures.mock_data import (
    MOCK_PROMPTS,
    MOCK_SESSION_DATA,
    MockClaudeProcess,
    MockTmuxSession,
)
from tests.fixtures.mock_factories import ComponentMockFactory, ManagerMockFactory
from tests.fixtures.test_helpers import temp_directory

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""pytest 전역 설정 파일
테스트 실행 시 자동으로 로드되며, 공통 fixture와 설정을 제공.
"""

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# 공통 Fixtures
@pytest.fixture
def mock_tmux_session() -> object:
    """Mock tmux 세션 fixture."""
    return MockTmuxSession("test-session")


@pytest.fixture
def mock_claude_process() -> object:
    """Mock Claude 프로세스 fixture."""
    return MockClaudeProcess()


# New Factory-based Fixtures
@pytest.fixture
def mock_session_manager() -> object:
    """Centralized SessionManager mock fixture."""
    return ManagerMockFactory.create_session_manager_mock()


@pytest.fixture
def mock_claude_manager() -> object:
    """Centralized ClaudeManager mock fixture."""
    return ManagerMockFactory.create_claude_manager_mock()


@pytest.fixture
def mock_tmux_manager() -> object:
    """Centralized TmuxManager mock fixture."""
    return ManagerMockFactory.create_tmux_manager_mock()


@pytest.fixture
def mock_subprocess_result() -> object:
    """Standard subprocess.run result mock."""
    return ComponentMockFactory.create_subprocess_mock()


@pytest.fixture
def mock_api_response() -> object:
    """Standard API response mock."""
    return ComponentMockFactory.create_api_response_mock()


@pytest.fixture
def temp_dir() -> object:
    """임시 디렉토리 fixture."""
    with temp_directory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_session_data() -> object:
    """샘플 세션 데이터 fixture."""
    return MOCK_SESSION_DATA.copy()


@pytest.fixture
def sample_prompts() -> object:
    """샘플 프롬프트 데이터 fixture."""
    return MOCK_PROMPTS.copy()


@pytest.fixture
def test_config_file(temp_dir: str) -> Path:
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
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def temp_project_root() -> object:
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)

        # Create tauri-dashboard directory with package.json
        tauri_dir = project_root / "tauri-dashboard"
        tauri_dir.mkdir()
        (tauri_dir / "package.json").write_text('{"name": "test-dashboard"}')

        yield project_root


@pytest.fixture
def launcher(temp_project_root: Path) -> object:
    """Create DashboardLauncher with temp project root."""
    return DashboardLauncher(project_root=temp_project_root)


@pytest.fixture
def theme_manager() -> object:
    """Create ThemeManager instance."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield ThemeManager(config_dir=Path(temp_dir))


@pytest.fixture
def keyboard_manager() -> object:
    """Create KeyboardNavigationManager instance."""
    manager = KeyboardNavigationManager()
    yield manager
    # Cleanup
    manager.actions.clear()
    manager.bindings.clear()


@pytest.fixture
def performance_optimizer() -> object:
    """Create PerformanceOptimizer instance."""
    optimizer = PerformanceOptimizer()
    yield optimizer
    # Cleanup
    if optimizer.monitoring:
        optimizer.stop_monitoring()


# Enhanced pytest configuration with performance monitoring
import asyncio
import time
import psutil
import threading
from collections import deque
from typing import Dict, Any, Optional

# Performance monitoring storage
_test_performance_data: Dict[str, deque] = {}
_monitoring_enabled = True
_performance_lock = threading.Lock()


@pytest.fixture(autouse=True)
def test_performance_monitoring(request):
    """Automatically track test performance with minimal overhead."""
    if not _monitoring_enabled:
        yield
        return
    
    # Start performance monitoring
    start_time = time.perf_counter()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    test_name = f"{request.module.__name__}::{request.function.__name__}"
    
    yield
    
    # Calculate metrics
    duration = time.perf_counter() - start_time
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    memory_delta = end_memory - start_memory
    
    # Determine test status
    status = 'passed'
    if hasattr(request.session, 'testsfailed') and request.session.testsfailed > 0:
        status = 'failed'
    elif hasattr(request.node, 'rep_call') and hasattr(request.node.rep_call, 'skipped'):
        status = 'skipped'
    
    # Store performance data
    performance_data = {
        'test_name': test_name,
        'duration_ms': duration * 1000,
        'memory_delta_mb': memory_delta,
        'status': status,
        'timestamp': time.time(),
        'suite': request.module.__name__.split('.')[0] if '.' in request.module.__name__ else 'root',
    }
    
    # Thread-safe storage update
    with _performance_lock:
        if test_name not in _test_performance_data:
            _test_performance_data[test_name] = deque(maxlen=100)  # Keep last 100 runs
        _test_performance_data[test_name].append(performance_data)
    
    # Publish metrics to monitoring system (async, non-blocking)
    if duration > 0.001:  # Only if overhead is minimal
        try:
            _publish_test_metrics_async(performance_data)
        except Exception:
            pass  # Don't let monitoring failures break tests


def _publish_test_metrics_async(metrics_data: Dict[str, Any]) -> None:
    """Publish test metrics to monitoring system asynchronously."""
    try:
        # Try to get monitoring dashboard integration
        from libs.dashboard.monitoring_integration import get_monitoring_dashboard
        monitoring = get_monitoring_dashboard()
        
        # Create async task to publish metrics (non-blocking)
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in current thread, skip async publishing
            return
            
        if loop and not loop.is_closed():
            # Publish as background task
            task = loop.create_task(_async_publish_metrics(monitoring, metrics_data))
            # Don't wait for completion to avoid test delays
            
    except Exception:
        # Monitoring integration not available or failed, continue silently
        pass


async def _async_publish_metrics(monitoring, metrics_data: Dict[str, Any]) -> None:
    """Async helper to publish metrics data."""
    try:
        from libs.core.async_event_bus import Event, EventType, EventPriority
        
        # Create test metrics event
        event = Event(
            type=EventType.CUSTOM,
            data={
                'event_subtype': 'test_execution_metrics',
                'test_metrics': metrics_data,
                'category': 'test_performance',
            },
            timestamp=metrics_data['timestamp'],
            source='test_runner',
            priority=EventPriority.LOW,
        )
        
        # Publish to event bus
        await monitoring.event_bus.publish(event)
        
    except Exception:
        # Fail silently to not impact test execution
        pass


@pytest.fixture
def chaos_test_context():
    """Context fixture for chaos engineering tests."""
    context = {
        'failures_injected': [],
        'recovery_times': [],
        'system_state_before': None,
        'system_state_after': None,
        'chaos_active': False,
    }
    
    yield context
    
    # Cleanup after chaos test
    if context.get('chaos_active'):
        try:
            # Restore normal system state
            _cleanup_chaos_test(context)
        except Exception as e:
            print(f"Warning: Chaos test cleanup failed: {e}")


def _cleanup_chaos_test(context: Dict[str, Any]) -> None:
    """Clean up after chaos engineering test."""
    # Reset any system modifications made during chaos test
    # This would include network settings, resource limits, etc.
    pass


@pytest.fixture
def performance_baseline():
    """Fixture to provide performance baseline data for regression testing."""
    from tests.fixtures.mock_factories import EnhancedTestDataFactory
    
    # Load or create baseline data
    baseline_data = EnhancedTestDataFactory.create_performance_metrics(24)
    
    return {
        'response_time_p95_ms': 200,
        'memory_usage_mb': 100,
        'cpu_usage_percent': 30,
        'error_rate_percent': 1.0,
        'baseline_data': baseline_data,
        'thresholds': {
            'response_time_regression': 1.5,  # 50% increase triggers regression
            'memory_regression': 2.0,  # 100% increase triggers regression
            'error_rate_regression': 2.0,  # 100% increase triggers regression
        }
    }


@pytest.fixture
def property_test_config():
    """Configuration fixture for property-based tests."""
    return {
        'max_examples': 100,
        'deadline': 5000,  # 5 seconds max per property test
        'suppress_health_check': [],
        'verbosity': 1,
        'database': None,  # Disable example database for CI
    }


# pytest 설정
def pytest_configure(config: object) -> None:
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
    config.addinivalue_line(
        "markers",
        "chaos: marks tests as chaos engineering tests",
    )
    config.addinivalue_line(
        "markers",
        "property: marks tests as property-based tests",
    )
    config.addinivalue_line(
        "markers",
        "contract: marks tests as API contract tests",
    )
    config.addinivalue_line(
        "markers",
        "performance: marks tests as performance benchmarks",
    )


# 테스트 세션 시작/종료 훅
def pytest_sessionstart(session: object) -> None:
    """테스트 세션 시작 시 실행."""


def pytest_sessionfinish(session: object, exitstatus: int) -> None:
    """테스트 세션 종료 시 실행."""


# 테스트 결과 리포팅 커스터마이징
def pytest_report_teststatus(report: object, config: object) -> tuple[str, str, str] | None:
    """테스트 상태 리포팅 커스터마이징."""
    if report.when == "call":
        if report.passed:
            return "passed", "✓", "PASSED"
        if report.failed:
            return "failed", "✗", "FAILED"
        if report.skipped:
            return "skipped", "⊘", "SKIPPED"
    return None
