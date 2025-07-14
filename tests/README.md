# Yesman-Claude 테스트 가이드

## 📖 개요
이 디렉토리는 Yesman-Claude 프로젝트의 모든 테스트를 포함합니다. 체계적인 테스트 구조로 단위 테스트, 통합 테스트, E2E 테스트를 분리하여 관리합니다.

## 📁 디렉토리 구조

```
tests/
├── unit/                  # 단위 테스트
│   ├── core/             # 핵심 기능 테스트
│   │   ├── cache/        # 캐시 시스템
│   │   ├── prompt/       # 프롬프트 감지
│   │   └── session/      # 세션 관리
│   ├── commands/         # CLI 명령어 테스트
│   ├── api/              # FastAPI 엔드포인트 테스트
│   └── utils/            # 유틸리티 함수 테스트
├── integration/          # 통합 테스트
│   ├── cache/            # 캐시 통합 테스트
│   └── scripts/          # 다양한 통합 시나리오
├── e2e/                  # End-to-End 테스트
│   ├── tauri/            # Tauri 앱 E2E 테스트
│   └── dashboard/        # 웹 대시보드 E2E 테스트
├── fixtures/             # 공통 테스트 데이터
│   ├── mock_data.py      # Mock 객체 정의
│   └── test_helpers.py   # 헬퍼 함수
├── scripts/              # 테스트 실행 스크립트
│   ├── run_all_tests.sh  # 전체 테스트 실행
│   └── coverage_report.sh # 커버리지 리포트
├── conftest.py           # pytest 설정 및 fixtures
└── README.md             # 이 파일
```

## 🚀 빠른 시작

### 테스트 실행

```bash
# 전체 테스트 실행
make test

# 단위 테스트만
make test-unit

# 통합 테스트만
make test-integration

# 커버리지 포함
make test-coverage

# 특정 파일 테스트
make test-file FILE=tests/unit/core/cache/test_session_cache.py
```

### 스크립트 실행

```bash
# 종합 테스트 스크립트
./tests/scripts/run_all_tests.sh

# 커버리지 리포트만
./tests/scripts/coverage_report.sh
```

## 📋 테스트 작성 가이드

### 명명 규칙

#### 파일명
- 테스트 파일: `test_<module>_<feature>.py`
- 예: `test_cache_strategies.py`, `test_ls_command.py`

#### 함수명
- 패턴: `test_<기능>_<시나리오>_<예상결과>`
- 예:
  ```python
  def test_cache_set_with_ttl_expires_after_timeout():
  def test_session_create_with_invalid_name_raises_error():
  def test_api_get_nonexistent_returns_404():
  ```

#### 클래스명
- 패턴: `Test<Module><Feature>`
- 예: `TestCacheExpiration`, `TestSessionManager`

### 테스트 작성 예시

```python
import pytest
from tests.fixtures.mock_data import MockTmuxSession


class TestSessionManager:
    """세션 관리자 테스트"""
    
    @pytest.fixture
    def manager(self):
        """세션 매니저 fixture"""
        return SessionManager()
    
    def test_create_session_with_valid_name_succeeds(self, manager):
        """
        유효한 이름으로 세션 생성 시 성공하는지 테스트
        
        Given: 유효한 세션 이름
        When: 세션을 생성할 때
        Then: 성공적으로 생성됨
        """
        # Given
        session_name = "test-session"
        
        # When
        result = manager.create_session(session_name)
        
        # Then
        assert result is True
        assert manager.session_exists(session_name)
```

### Mock 사용법

```python
from tests.fixtures.mock_data import MockTmuxSession, MOCK_SESSION_DATA
from tests.fixtures.test_helpers import temp_directory

def test_with_mock_session():
    """Mock 세션 사용 예시"""
    session = MockTmuxSession("test")
    assert session.name == "test"

def test_with_temp_directory():
    """임시 디렉토리 사용 예시"""
    with temp_directory() as tmpdir:
        # tmpdir 사용
        pass
```

## 🏷️ 테스트 마커

pytest 마커를 사용하여 테스트를 분류합니다:

```python
@pytest.mark.unit
def test_basic_function():
    """단위 테스트 마커"""
    pass

@pytest.mark.integration
def test_integration_flow():
    """통합 테스트 마커"""
    pass

@pytest.mark.slow
def test_performance_heavy():
    """느린 테스트 마커"""
    pass
```

### 마커별 실행

```bash
# 빠른 테스트만 (slow 제외)
pytest -m "not slow"

# 단위 테스트만
pytest -m unit

# 통합 테스트만
pytest -m integration
```

## 📊 커버리지

### 목표
- **최소 커버리지**: 80%
- **권장 커버리지**: 90%

### 확인 방법

```bash
# HTML 리포트 생성
make test-coverage-report

# 터미널에서 확인
pytest --cov=libs --cov=commands --cov-report=term-missing
```

### 커버리지 제외
`.coveragerc` 또는 `pyproject.toml`에서 설정:

```toml
[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
]
```

## 🔧 도구 및 의존성

### 테스트 프레임워크
- **pytest**: 주요 테스트 프레임워크
- **pytest-cov**: 커버리지 측정
- **pytest-mock**: Mock 지원
- **pytest-asyncio**: 비동기 테스트

### 설치

```bash
# 테스트 의존성 설치
make test-deps

# 또는 직접 설치
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

## 🐛 트러블슈팅

### 일반적인 문제

1. **Import 에러**
   ```bash
   # 프로젝트 루트에서 실행
   cd /path/to/yesman-claude
   python -m pytest tests/
   ```

2. **Mock 에러**
   ```python
   # 올바른 import
   from tests.fixtures.mock_data import MockTmuxSession
   ```

3. **Fixture 에러**
   ```python
   # conftest.py의 fixture 사용
   def test_example(mock_tmux_session):
       assert mock_tmux_session.name == "test-session"
   ```

### 성능 최적화

1. **병렬 실행**
   ```bash
   pip install pytest-xdist
   pytest -n auto
   ```

2. **캐시 활용**
   ```bash
   pytest --cache-clear  # 캐시 초기화
   pytest --lf          # 마지막 실패한 테스트만
   ```

## 🔄 CI/CD 통합

### GitHub Actions
- 모든 PR에서 자동 테스트 실행
- Python 3.11, 3.12 매트릭스 테스트
- 커버리지 리포트 자동 생성
- 실패 시 머지 차단

### 로컬 pre-commit 훅
```bash
# pre-commit 설치 (선택사항)
pip install pre-commit
pre-commit install
```

## 📚 추가 자료

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-cov 사용법](https://pytest-cov.readthedocs.io/)
- [테스트 리팩토링 진행 상황](./refactoring_progress.md)

---

## 🤝 기여 가이드

1. 새 기능 개발 시 테스트 작성 필수
2. 기존 테스트 수정 시 이유 명시
3. 커버리지 80% 유지
4. 테스트 이름은 명확하고 구체적으로
5. Mock은 최소한으로 사용

**테스트 관련 질문이나 제안사항은 이슈로 등록해 주세요.**