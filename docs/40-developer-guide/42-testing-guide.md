# Testing Guide

Yesman-Agent의 통합 테스트 가이드입니다. 단위 테스트부터 통합 테스트, 성능 테스트까지 모든 테스트 전략을 다룹니다.

## 📚 목차

1. [테스트 전략](#%ED%85%8C%EC%8A%A4%ED%8A%B8-%EC%A0%84%EB%9E%B5)
1. [테스트 환경 설정](#%ED%85%8C%EC%8A%A4%ED%8A%B8-%ED%99%98%EA%B2%BD-%EC%84%A4%EC%A0%95)
1. [통합 테스트 실행](#%ED%86%B5%ED%95%A9-%ED%85%8C%EC%8A%A4%ED%8A%B8-%EC%8B%A4%ED%96%89)
1. [단위 테스트](#%EB%8B%A8%EC%9C%84-%ED%85%8C%EC%8A%A4%ED%8A%B8)
1. [성능 테스트](#%EC%84%B1%EB%8A%A5-%ED%85%8C%EC%8A%A4%ED%8A%B8)
1. [보안 테스트](#%EB%B3%B4%EC%95%88-%ED%85%8C%EC%8A%A4%ED%8A%B8)
1. [테스트 자동화](#%ED%85%8C%EC%8A%A4%ED%8A%B8-%EC%9E%90%EB%8F%99%ED%99%94)
1. [문제 해결](#%EB%AC%B8%EC%A0%9C-%ED%95%B4%EA%B2%B0)

## 🎯 테스트 전략

### 테스트 피라미드

```
    🔺 E2E Tests (10%)
   🔺🔺 Integration Tests (20%)
  🔺🔺🔺 Unit Tests (70%)
```

- **단위 테스트**: 개별 함수/클래스 검증
- **통합 테스트**: 컴포넌트 간 상호작용 검증
- **E2E 테스트**: 전체 워크플로우 검증

### 테스트 카테고리

1. **Functional Tests**: 핵심 기능 검증
1. **Performance Tests**: 응답 시간 및 리소스 사용량
1. **Security Tests**: 보안 취약점 검증
1. **Reliability Tests**: 에러 처리 및 복구
1. **Compatibility Tests**: 크로스 플랫폼 호환성

## 🛠️ 테스트 환경 설정

### 요구사항

- Python 3.8+
- tmux
- uv (Python package manager)
- curl (for HTTP testing)
- git (for repository tests)

### 설치

```bash
# 테스트 의존성 설치
pip install pytest pytest-cov pytest-asyncio pytest-mock

# 또는 uv 사용
uv sync --dev

# 통합 테스트 설정
cd test-integration
chmod +x *.sh
```

### 환경 변수

```bash
# 테스트 환경 설정
export YESMAN_TEST_MODE=1
export YESMAN_LOG_LEVEL=DEBUG
export YESMAN_TEST_DATA_DIR=/tmp/yesman-test
```

## 🚀 통합 테스트 실행

### Quick Start

```bash
# 모든 통합 테스트 실행
./test-integration/run_tests.sh

# 특정 테스트 스위트 실행
./test-integration/run_tests.sh --suite basic

# 빠른 테스트만 실행
./test-integration/run_tests.sh --quick

# 병렬 실행 (60% 시간 단축)
python3 test-integration/lib/parallel_runner.py --suites scripts/basic scripts/ai --workers 4
```

### 테스트 스위트

#### 1. Basic Tests (`scripts/basic/`)

기본적인 세션 관리 및 Claude 자동화 기능을 테스트합니다.

```bash
# 세션 생명주기 테스트
./test-integration/scripts/basic/test_session_lifecycle.sh

# Claude 자동화 테스트
./test-integration/scripts/basic/test_claude_automation.sh
```

**검증 포인트**:

- tmux 세션 생성/삭제
- 세션 설정 적용
- Claude 자동 응답

#### 2. Performance Tests (`scripts/performance/`)

성능 및 리소스 사용량을 테스트합니다.

```bash
# 로드 테스트
./test-integration/scripts/performance/test_load_performance.sh

# 캐시 효율성 테스트
./test-integration/scripts/performance/test_cache_efficiency.sh
```

**검증 포인트**:

- 응답 시간 < 2초
- 메모리 사용량 < 200MB
- 캐시 히트율 > 80%

#### 3. AI Learning Tests (`scripts/ai/`)

AI 학습 시스템을 테스트합니다.

```bash
# 패턴 인식 테스트
./test-integration/scripts/ai/test_pattern_learning.sh

# 응답 정확도 테스트
./test-integration/scripts/ai/test_response_accuracy.sh
```

**검증 포인트**:

- 패턴 분류 정확도 > 90%
- 학습 데이터 저장/로드
- 신뢰도 점수 계산

#### 4. Health Monitoring (`scripts/monitoring/`)

프로젝트 건강도 모니터링을 테스트합니다.

```bash
# 건강도 계산 테스트
./test-integration/scripts/monitoring/test_health_monitoring.sh

# 실시간 모니터링 테스트
./test-integration/scripts/monitoring/test_realtime_monitoring.sh
```

**검증 포인트**:

- 8개 카테고리 건강도 계산
- 실시간 업데이트
- 임계값 알림

### 테스트 결과

테스트 결과는 `test-integration/results/` 디렉토리에 저장됩니다:

- `test_results.log`: 원시 테스트 출력
- `test_report.md`: 포맷된 테스트 보고서
- `*_*.log`: 개별 테스트 로그

## 🧪 단위 테스트

### 테스트 구조

```bash
tests/
├── unit/
│   ├── test_session_manager.py
│   ├── test_claude_manager.py
│   ├── test_ai_learning.py
│   └── test_config_loader.py
├── integration/
│   ├── test_api_integration.py
│   ├── test_command_integration.py
│   └── test_dashboard_integration.py
└── fixtures/
    ├── test_sessions.yaml
    └── mock_data.json
```

### 단위 테스트 실행

```bash
# 모든 단위 테스트 실행
pytest tests/unit/

# 커버리지 포함 실행
pytest --cov=libs --cov=commands tests/

# 특정 테스트 파일 실행
pytest tests/unit/test_session_manager.py

# 특정 테스트 함수 실행
pytest tests/unit/test_session_manager.py::test_create_session
```

### 테스트 작성 예시

```python
# tests/unit/test_session_manager.py
import pytest
from unittest.mock import MagicMock, patch
from libs.core.session_manager import SessionManager
from libs.core.error_handling import SessionError

class TestSessionManager:
    @pytest.fixture
    def session_manager(self):
        """SessionManager 인스턴스 생성"""
        config = MagicMock()
        tmux_manager = MagicMock()
        return SessionManager(config, tmux_manager)
    
    def test_create_session_success(self, session_manager):
        """세션 생성 성공 테스트"""
        session_name = "test-session"
        session_config = {"session_name": session_name}
        
        # Mock 설정
        session_manager.tmux_manager.create_session.return_value = True
        
        # 테스트 실행
        result = session_manager.create_session(session_name, session_config)
        
        # 검증
        assert result["success"] is True
        assert result["session_name"] == session_name
        session_manager.tmux_manager.create_session.assert_called_once()
    
    def test_create_session_duplicate(self, session_manager):
        """중복 세션 생성 에러 테스트"""
        session_name = "existing-session"
        
        # Mock 설정 (세션이 이미 존재)
        session_manager._session_exists = MagicMock(return_value=True)
        
        # 테스트 실행 및 검증
        with pytest.raises(SessionError) as exc_info:
            session_manager.create_session(session_name, {})
        
        assert "already exists" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_session_exists_check(self, mock_subprocess, session_manager):
        """세션 존재 확인 테스트"""
        mock_subprocess.return_value.returncode = 0
        
        result = session_manager._session_exists("test-session")
        
        assert result is True
        mock_subprocess.assert_called_once()
```

### 모킹 전략

```python
# 의존성 주입을 통한 모킹
@pytest.fixture
def mock_services():
    """테스트용 서비스 모킹"""
    from libs.core.services import register_test_services
    
    mock_config = MagicMock()
    mock_tmux_manager = MagicMock()
    
    register_test_services(
        config=mock_config,
        tmux_manager=mock_tmux_manager
    )
    
    return {
        "config": mock_config,
        "tmux_manager": mock_tmux_manager
    }

# 외부 프로세스 모킹
@patch('subprocess.run')
def test_tmux_command(mock_subprocess):
    """tmux 명령어 실행 모킹"""
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "session_output"
    
    # 테스트 코드
    result = run_tmux_command(["tmux", "list-sessions"])
    
    assert result.returncode == 0
```

## ⚡ 성능 테스트

### 벤치마크 테스트

```python
# tests/performance/test_benchmarks.py
import time
import pytest
from libs.core.session_manager import SessionManager

class TestPerformanceBenchmarks:
    def test_session_creation_performance(self):
        """세션 생성 성능 테스트"""
        start_time = time.time()
        
        # 10개 세션 생성
        for i in range(10):
            session_manager.create_session(f"test-{i}", {})
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 10개 세션이 5초 이내에 생성되어야 함
        assert duration < 5.0
        
    def test_cache_performance(self):
        """캐시 성능 테스트"""
        # 첫 번째 호출 (캐시 미스)
        start_time = time.time()
        result1 = session_manager.get_all_sessions()
        cache_miss_time = time.time() - start_time
        
        # 두 번째 호출 (캐시 히트)
        start_time = time.time()
        result2 = session_manager.get_all_sessions()
        cache_hit_time = time.time() - start_time
        
        # 캐시 히트가 최소 50% 빠르다
        assert cache_hit_time < cache_miss_time * 0.5
        assert result1 == result2
```

### 메모리 사용량 테스트

```python
import psutil
import os

def test_memory_usage():
    """메모리 사용량 테스트"""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 많은 세션 생성
    for i in range(50):
        session_manager.create_session(f"memory-test-{i}", {})
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # 메모리 증가가 200MB 이하여야 함
    assert memory_increase < 200
```

## 🔒 보안 테스트

### API 보안 테스트

```python
# tests/security/test_api_security.py
import requests

class TestAPISecurity:
    def test_sql_injection_protection(self):
        """SQL 인젝션 방지 테스트"""
        malicious_input = "'; DROP TABLE sessions; --"
        
        response = requests.post(
            "http://localhost:8001/sessions",
            json={"name": malicious_input}
        )
        
        # 400 Bad Request 또는 유사한 에러 응답
        assert response.status_code in [400, 422]
        
    def test_xss_protection(self):
        """XSS 방지 테스트"""
        xss_payload = "<script>alert('xss')</script>"
        
        response = requests.post(
            "http://localhost:8001/sessions",
            json={"name": xss_payload}
        )
        
        # 응답에 스크립트가 실행되지 않도록 이스케이프됨
        assert "<script>" not in response.text
        
    def test_path_traversal_protection(self):
        """경로 탐색 공격 방지 테스트"""
        malicious_path = "../../etc/passwd"
        
        response = requests.get(f"/api/sessions/{malicious_path}")
        
        assert response.status_code == 404
```

### 민감 정보 보호 테스트

```bash
# 로그에서 민감 정보 검색
grep -r "password\|secret\|key\|token" ~/.scripton/yesman/logs/

# 환경 변수 노출 확인
python -c "
import os
import json
env_vars = {k: v for k, v in os.environ.items() if 'SECRET' in k or 'PASSWORD' in k}
print(json.dumps(env_vars, indent=2))
"
```

## 🤖 테스트 자동화

### GitHub Actions 워크플로우

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
        
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Install tmux
      run: sudo apt-get install -y tmux
    
    - name: Run unit tests
      run: pytest tests/unit/ --cov=libs --cov-report=xml
    
    - name: Run integration tests
      run: ./test-integration/run_tests.sh --quick
      
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit 훅

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/unit/ --tb=short
        language: system
        pass_filenames: false
        
      - id: integration-test-quick
        name: integration-test-quick
        entry: ./test-integration/run_tests.sh --quick
        language: system
        pass_filenames: false
```

### 테스트 데이터 관리

```bash
# 테스트 데이터 구조
test-data/
├── fixtures/
│   ├── test_sessions.yaml
│   ├── test_projects.yaml
│   └── test_responses.json
├── generators/
│   ├── generate_test_prompts.py
│   └── generate_mock_data.py
└── snapshots/
    ├── ui_snapshots/
    └── api_responses/
```

## 🔧 문제 해결

### 일반적인 테스트 문제

#### 테스트 환경 격리

```python
# 테스트 간 상태 격리
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """각 테스트 후 정리"""
    yield
    # 테스트 세션 정리
    subprocess.run(["tmux", "kill-server"], check=False)
    # 테스트 파일 정리
    shutil.rmtree("/tmp/yesman-test", ignore_errors=True)
```

#### 플래키 테스트 처리

```python
# 재시도 로직
@pytest.mark.flaky(reruns=3)
def test_network_dependent_feature():
    """네트워크 의존적 테스트"""
    # 불안정할 수 있는 테스트 코드
    pass

# 타임아웃 설정
@pytest.mark.timeout(30)
def test_long_running_operation():
    """장시간 실행 테스트"""
    # 30초 내에 완료되어야 함
    pass
```

#### 병렬 테스트 실행

```bash
# pytest-xdist를 사용한 병렬 실행
pip install pytest-xdist

# 4개 워커로 병렬 실행
pytest -n 4 tests/

# 자동 워커 수 결정
pytest -n auto tests/
```

### 디버깅

```bash
# 상세 출력으로 테스트 실행
pytest -v -s tests/unit/test_session_manager.py

# 특정 테스트에서 중단점 설정
pytest --pdb tests/unit/test_session_manager.py::test_create_session

# 로그 출력 포함
pytest --log-cli-level=DEBUG tests/
```

### CI/CD 트러블슈팅

```bash
# CI 환경에서 테스트 실행
export CI=true
export YESMAN_TEST_MODE=1
pytest tests/ --tb=short --maxfail=5
```

## 📊 테스트 메트릭

### 코드 커버리지

```bash
# 커버리지 보고서 생성
pytest --cov=libs --cov=commands --cov-report=html

# 커버리지 임계값 설정
pytest --cov=libs --cov-fail-under=80
```

### 테스트 실행 시간

```bash
# 가장 느린 테스트 10개 표시
pytest --durations=10

# 1초 이상 걸리는 테스트만 표시
pytest --durations=0 | grep -E '\s+[1-9]\d*\.\d+s'
```

## 📝 테스트 작성 가이드라인

### Best Practices

1. **테스트 이름**: 기능을 명확히 설명하는 이름 사용
1. **Arrange-Act-Assert**: 테스트 구조를 명확히 분리
1. **하나의 관심사**: 각 테스트는 하나의 기능만 검증
1. **독립성**: 테스트 간 의존성 없이 독립적 실행
1. **반복 가능**: 동일한 조건에서 동일한 결과

### 테스트 코드 예시

```python
def test_should_create_session_when_valid_config_provided():
    """유효한 설정이 제공되면 세션을 생성해야 함"""
    # Arrange
    session_name = "test-session"
    valid_config = {
        "session_name": session_name,
        "start_directory": "/tmp"
    }
    
    # Act
    result = session_manager.create_session(session_name, valid_config)
    
    # Assert
    assert result["success"] is True
    assert result["session_name"] == session_name
    assert session_manager._session_exists(session_name)
```

______________________________________________________________________

**마지막 업데이트**: 2025-08-19\
**테스트 커버리지**: 85%+\
**지원 플랫폼**: Linux, macOS, Windows (WSL2)
