# Development Setup Guide

Yesman-Claude 개발 환경 설정 및 개발 워크플로우 가이드입니다.

## 📋 목차

1. [개발 환경 설정](#개발-환경-설정)
2. [프로젝트 구조](#프로젝트-구조)
3. [개발 명령어](#개발-명령어)
4. [아키텍처 개요](#아키텍처-개요)
5. [새로운 기능 추가](#새로운-기능-추가)
6. [코딩 가이드라인](#코딩-가이드라인)

## 🛠️ 개발 환경 설정

### 요구 사항

- Python 3.11+
- tmux
- Git
- Node.js (Tauri 대시보드용)

### 설치

```bash
# 저장소 클론
git clone <repository-url>
cd yesman-agent

# 개발 설치 (권장)
make dev-install
# 또는 직접:
pip install -e . --config-settings editable_mode=compat

# uv 사용 (개발용 권장)
uv sync
```

### 개발 환경 설정

```bash
# 개발 환경 설정
export YESMAN_ENV=development

# 설정 파일 생성 (선택적)
mkdir -p ~/.scripton/yesman
cp config/development.yaml ~/.scripton/yesman/yesman.yaml

# Git hooks 설치 (권장)
make hooks-install

# 코드 품질 검사
make lint
make format
```

## 📁 프로젝트 구조

### Directory Structure

- `yesman.py` - Main CLI entry point using Click
- `commands/` - CLI command implementations (ls, show, setup, teardown, dashboard, enter, browse, status, ai, logs)
- `libs/core/` - Core functionality (SessionManager, ClaudeManager, models, caching)
- `libs/ai/` - AI learning and adaptive response system
- `libs/automation/` - [Deprecated] Previously contained automation features
- `libs/dashboard/` - Dashboard components and health monitoring
- `libs/logging/` - Asynchronous logging system
- `libs/` - Additional functionality (YesmanConfig, TmuxManager)
- `patterns/` - Auto-response patterns for selection prompts
- `examples/global-yesman/` - Example configuration files
- `api/` - FastAPI server for REST API endpoints
- `tauri-dashboard/` - Native desktop app (Tauri + Svelte)
- `debug/` - Debug utilities and standalone test scripts
- `test-integration/` - Integration testing utilities

### Configuration Hierarchy

1. Global config: `~/.scripton/yesman/yesman.yaml` (logging, default choices)
2. Session files: `~/.scripton/yesman/sessions/*.yaml` (individual session definitions)
3. Templates: `~/.scripton/yesman/templates/*.yaml` (reusable session templates)
4. Local overrides: `./.scripton/yesman/*` (project-specific configs)

Configuration merge modes:

- `merge` (default): Local configs override global
- `local`: Use only local configs

## 🚀 개발 명령어

### Installation

```bash
# Development installation (recommended)
make dev-install
# or directly:
pip install -e . --config-settings editable_mode=compat

# Alternative using uv (recommended for development)
uv run ./yesman.py --help
```

### Running Commands

```bash
# List available templates and projects
./yesman.py ls
# or with uv:
uv run ./yesman.py ls

# Show running tmux sessions  
uv run ./yesman.py show

# Create all tmux sessions from session files
uv run ./yesman.py setup

# Create specific session
uv run ./yesman.py setup session-name

# Teardown all sessions
uv run ./yesman.py teardown

# Teardown specific session
uv run ./yesman.py teardown session-name

# Enter (attach to) a tmux session
uv run ./yesman.py enter [session_name]
uv run ./yesman.py enter  # Interactive selection

# Run Tauri desktop dashboard to monitor all sessions
uv run ./yesman.py dashboard --dev  # Development mode
uv run ./yesman.py dashboard        # Production mode

# NEW: Interactive session browser with activity monitoring
uv run ./yesman.py browse           # Interactive session browser
uv run ./yesman.py browse -i 1.0    # Custom update interval

# NEW: Comprehensive project status dashboard
uv run ./yesman.py status           # Quick status overview
uv run ./yesman.py status -i        # Interactive live dashboard
uv run ./yesman.py status -d        # Detailed view

# NEW: AI learning system management
uv run ./yesman.py ai status        # Show AI learning status
uv run ./yesman.py ai config -t 0.8 # Adjust confidence threshold
uv run ./yesman.py ai history       # Show response history
uv run ./yesman.py ai export        # Export learning data

# NEW: Log management and analysis
uv run ./yesman.py logs configure   # Configure async logging
uv run ./yesman.py logs analyze     # Analyze log patterns
uv run ./yesman.py logs tail -f     # Follow logs in real-time
uv run ./yesman.py logs cleanup     # Clean up old logs
```

### Testing and Development Commands

```bash
# Run specific test files
python -m pytest tests/test_prompt_detector.py
python -m pytest tests/test_content_collector.py

# Run integration tests  
python -m pytest tests/test_full_automation.py
python -m pytest tests/test_session_manager_cache.py

# Debug specific components (located in debug/ directory)
python debug/debug_content.py      # Debug content collection
python debug/debug_controller.py   # Debug dashboard controller  
python debug/debug_tmux.py        # Debug tmux operations

# FastAPI server for REST API
cd api && python -m uvicorn main:app --reload

# Tauri desktop app development
cd tauri-dashboard && npm run tauri dev
```

### Code Quality Tools

The project uses comprehensive code quality tools:

- **Ruff** for linting, formatting, and import sorting (replaces Black + isort)
- **mypy** for static type checking
- **pytest** for testing with coverage reports
- **bandit** for security vulnerability scanning
- **pre-commit** for automatic quality checks

Quick commands:

```bash
make format      # Format code with Ruff
make lint        # Check code quality
make lint-fix    # Auto-fix linting issues
make test        # Run all tests
make full        # Complete quality check
```

## 🏗️ 아키텍처 개요

Yesman Claude는 다음과 같은 핵심 패턴들을 사용합니다:

### Command Pattern

모든 CLI 명령어는 `BaseCommand`를 상속받아 표준화된 방식으로 구현됩니다.

```python
from libs.core.base_command import BaseCommand

class MyCommand(BaseCommand):
    def execute(self, **kwargs) -> dict:
        # 명령어 실행 로직
        return {"success": True, "message": "작업 완료"}
```

### Dependency Injection

서비스들은 DI 컨테이너를 통해 관리되며, 테스트와 유지보수를 용이하게 합니다.

```python
from libs.core.services import get_config, get_tmux_manager

config = get_config()           # YesmanConfig 인스턴스
tmux_manager = get_tmux_manager()  # TmuxManager 인스턴스
```

### Configuration Management

Pydantic 스키마 기반의 타입 안전한 설정 관리를 제공합니다.

```python
# 타입 안전한 설정 접근
log_level = config.schema.logging.level
tmux_shell = config.schema.tmux.default_shell
```

### Error Handling

중앙화된 에러 처리 시스템으로 일관된 에러 응답을 제공합니다.

```python
from libs.core.error_handling import SessionError

raise SessionError(
    "세션을 찾을 수 없습니다",
    session_name="myproject",
    recovery_hint="'yesman show'로 세션 목록을 확인하세요"
)
```

### Key Components

**YesmanConfig** (`libs/yesman_config.py`):

- Loads and merges global/local configurations
- Sets up logging based on config
- Provides config access methods

**TmuxManager** (`libs/tmux_manager.py`):

- Creates tmux sessions from YAML configs using tmuxp
- Lists available templates and running sessions
- Handles project loading and session lifecycle

**ClaudeManager** (`libs/core/claude_manager.py`):

- Monitors Claude Code sessions for interactive prompts
- Auto-responds to trust prompts and selection menus
- Detects idle states and input states in Claude Code
- Provides real-time feedback with progress indicators
- **NEW**: AI-powered adaptive response system with machine learning capabilities

**Tauri Desktop Dashboard** (`tauri-dashboard/`):

- Native desktop application built with Tauri + SvelteKit for monitoring sessions
- Shows project status, session state, and claude manager activity
- Real-time updates with auto-refresh capability
- Interactive controller management and session monitoring
- High-performance native UI with system integration

**FastAPI Server** (`api/main.py`):

- REST API endpoints for session and controller management
- Provides backend services for external integrations
- Includes routers for sessions and controllers

**AI Learning System** (`libs/ai/`):

- **ResponseAnalyzer** (`libs/ai/response_analyzer.py`): Pattern analysis and learning engine
- **AdaptiveResponse** (`libs/ai/adaptive_response.py`): AI-powered auto-response system
- Learns from user behavior and improves response accuracy over time
- Pattern classification for different prompt types (yes/no, numbered selections, etc.)
- Confidence scoring and prediction algorithms
- JSON-based persistence for learned patterns and responses

## ➕ 새로운 명령어 추가

### 1. 명령어 클래스 생성

새로운 명령어를 `commands/` 디렉토리에 생성합니다:

```python
# commands/example.py
"""Example command implementation"""

import click
from libs.core.base_command import BaseCommand
from libs.core.error_handling import ValidationError


class ExampleCommand(BaseCommand):
    """예시 명령어 클래스"""

    def execute(self, name: str = None, **kwargs) -> dict:
        """
        명령어 실행 로직
        
        Args:
            name: 예시 매개변수
            **kwargs: 추가 매개변수들
            
        Returns:
            실행 결과 딕셔너리
            
        Raises:
            ValidationError: 잘못된 입력값
        """
        if not name:
            raise ValidationError(
                "이름이 필요합니다",
                field_name="name",
                recovery_hint="--name 옵션으로 이름을 지정하세요"
            )
        
        # 실제 명령어 로직
        self.print_info(f"안녕하세요, {name}님!")
        
        return {
            "success": True,
            "message": f"{name}님에게 인사했습니다",
            "data": {"name": name}
        }


@click.command()
@click.option("--name", help="인사할 대상의 이름")
def example(name):
    """예시 명령어"""
    command = ExampleCommand()
    command.run(name=name)
```

### 2. yesman.py에 명령어 등록

```python
# yesman.py
from commands.example import example

@cli.command()
def example_cmd():
    """예시 명령어"""
    example()
```

### 3. 명령어 믹스인 사용

공통 기능이 필요한 경우 믹스인을 사용합니다:

```python
from libs.core.base_command import BaseCommand, SessionCommandMixin

class SessionExampleCommand(BaseCommand, SessionCommandMixin):
    """세션 관련 예시 명령어"""
    
    def execute(self, session_name: str, **kwargs) -> dict:
        # 세션 관련 기능 사용
        session = self.get_session(session_name)
        if not session:
            raise SessionError(f"세션 '{session_name}'을 찾을 수 없습니다")
        
        # 세션 작업 수행
        return {"success": True}
```

## 🌐 API 엔드포인트 추가

### 1. 라우터 생성

```python
# api/routers/example.py
"""Example API endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from libs.core.services import get_config
from libs.core.error_handling import ValidationError

router = APIRouter()


class ExampleRequest(BaseModel):
    name: str
    message: str | None = None


class ExampleResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


@router.post("/example", response_model=ExampleResponse)
async def create_example(request: ExampleRequest):
    """예시 API 엔드포인트"""
    try:
        # DI를 통한 서비스 접근
        config = get_config()
        
        # 비즈니스 로직
        result = process_example(request.name, request.message)
        
        return ExampleResponse(
            success=True,
            message="처리 완료",
            data=result
        )
    except ValidationError as e:
        # YesmanError는 자동으로 적절한 HTTP 상태코드로 변환됩니다
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. main.py에 라우터 등록

```python
# api/main.py
from api.routers import example

app.include_router(example.router, prefix="/api", tags=["example"])
```

## ⚙️ 설정 관리

### 환경별 설정

```yaml
# config/development.yaml
logging:
  level: DEBUG
  
confidence_threshold: 0.5
auto_cleanup_days: 7

# config/production.yaml
logging:
  level: WARNING
  max_size: 52428800  # 50MB
  
confidence_threshold: 0.9
auto_cleanup_days: 30
```

### 환경변수 사용

```bash
# 특정 설정을 환경변수로 오버라이드
export YESMAN_LOGGING_LEVEL=ERROR
export YESMAN_TMUX_DEFAULT_SHELL=/bin/zsh
export YESMAN_CONFIDENCE_THRESHOLD=0.95
```

## 🚨 에러 처리

### 표준 에러 클래스 사용

```python
from libs.core.error_handling import (
    ConfigurationError,
    SessionError,
    ValidationError,
    NetworkError
)

# 설정 관련 에러
raise ConfigurationError(
    "설정 파일을 찾을 수 없습니다",
    config_file="/path/to/config.yaml"
)

# 세션 관련 에러
raise SessionError(
    "세션이 이미 존재합니다",
    session_name="myproject",
    recovery_hint="다른 이름을 사용하거나 기존 세션을 종료하세요"
)

# 검증 에러
raise ValidationError(
    "포트 번호가 유효하지 않습니다",
    field_name="port",
    recovery_hint="1-65535 범위의 포트 번호를 입력하세요"
)
```

## 📝 코딩 가이드라인

### 코드 스타일

프로젝트는 Ruff를 사용하여 일관된 코드 스타일을 유지합니다:

```bash
# 코드 포맷팅 (Ruff 사용)
make format

# 린팅 검사
make lint

# 자동 수정 포함 린팅
make lint-fix

# 타입 체킹
make type-check

# 전체 품질 검사
make full
```

### 커밋 메시지

```
feat(commands): add example command
fix(api): resolve session creation error
docs(adr): add configuration management decision
test(integration): add API endpoint tests
refactor(core): improve error handling
```

### 브랜치 전략

- `main`: 안정된 프로덕션 코드
- `develop`: 개발 브랜치
- `feature/task-name`: 기능 개발
- `hotfix/issue-name`: 긴급 수정

## 🔍 디버깅 팁

### 로깅 설정

```python
# 개발 시 상세 로깅
export YESMAN_LOGGING_LEVEL=DEBUG

# 특정 모듈만 로깅
import logging
logging.getLogger("yesman.tmux_manager").setLevel(logging.DEBUG)
```

### 에러 추적

```python
# 에러 컨텍스트 확인
try:
    command.execute()
except YesmanError as e:
    print(f"에러 코드: {e.error_code}")
    print(f"복구 힌트: {e.recovery_hint}")
    print(f"컨텍스트: {e.context}")
```

## 🔧 Development Workflow

When working on this codebase:

1. **Adding New Commands**: Create new command files in `commands/` directory and register them in `yesman.py:17-22`
2. **Claude Manager Modifications**:
   - Core logic in `libs/core/claude_manager.py` (DashboardController class)
   - Pattern detection in `libs/core/prompt_detector.py` (ClaudePromptDetector class)
   - Content collection in `libs/core/content_collector.py`
   - Auto-response patterns stored in `patterns/` subdirectories
   - Caching system components in `libs/core/cache_*.py` modules
3. **Dashboard Updates**:
   - Tauri: Native desktop app components in `tauri-dashboard/src/`
   - FastAPI: REST API endpoints in `api/routers/`
   - Web Interface: Browser-based components via Tauri's embedded WebView
4. **Configuration Changes**: Global config structure defined in `YesmanConfig` class (`libs/yesman_config.py`)
5. **Testing**: Use debug scripts in `debug/` directory and test files in `tests/` for component testing

## 📚 추가 리소스

- [테스트 가이드](42-testing-guide.md)
- [API 문서](../20-api/21-rest-api-reference.md) (서버 실행 시)
- [설정 스키마](../../libs/core/config_schema.py)
- [에러 처리](../../libs/core/error_handling.py)

## 🤝 기여하기

1. 이슈 생성 또는 기존 이슈 확인
2. 기능 브랜치 생성: `git checkout -b feature/my-feature`
3. 변경사항 커밋: `git commit -m 'feat: add my feature'`
4. 브랜치 푸시: `git push origin feature/my-feature`
5. Pull Request 생성

### PR 체크리스트

- [ ] 테스트가 모두 통과하는가?
- [ ] 코드 스타일 가이드를 따르는가?
- [ ] 문서가 업데이트되었는가?
- [ ] 새로운 기능에 대한 테스트가 추가되었는가?
- [ ] CHANGELOG가 업데이트되었는가?