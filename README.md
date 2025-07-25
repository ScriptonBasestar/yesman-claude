# Yesman Claude

Yesman-Claude is a comprehensive CLI automation tool that manages tmux sessions and automates interactions with Claude
Code. It provides multiple dashboard interfaces for monitoring and controlling your development environment.

## 🚀 Key Features

### Core Functionality

- **Session Management**: Create and manage tmux sessions using YAML templates
- **Claude Code Automation**: Automatic response to Claude Code prompts and selections
- **Multiple Dashboard Interfaces**: Choose from TUI, Web, or native desktop interfaces
- **Real-time Monitoring**: Live session activity tracking and health monitoring
- **AI-Powered Learning**: Adaptive response system that learns from user behavior

### Architecture (Phase-3 Refactoring Completed)

- **Command Pattern**: Standardized command execution with BaseCommand pattern
- **Dependency Injection**: Type-safe DI container for service management
- **Configuration Management**: Pydantic-based configuration with environment support
- **Error Handling**: Centralized error handling with recovery hints
- **Type Safety**: Full TypeScript-style type hints and validation

## 📊 Dashboard Interfaces

Yesman-Claude offers three distinct dashboard interfaces to suit different environments and preferences:

### 🖥️ Terminal User Interface (TUI)

Rich-based terminal dashboard with live updates and keyboard navigation.

```bash
uv run ./yesman.py dash run --interface tui
```

### 🌐 Web Interface (SvelteKit)

Modern web dashboard built with SvelteKit, served via FastAPI.

```bash
# Build SvelteKit first (required for web interface)
cd tauri-dashboard && npm run build

# Start web dashboard
uv run ./yesman.py dash run --interface web --port 8000
# Access at: http://localhost:8000

# Background mode
uv run ./yesman.py dash run --interface web --detach
```

### 🖱️ Desktop Application (Tauri + SvelteKit)

Native desktop app with the same SvelteKit codebase as web interface.

```bash
uv run ./yesman.py dash run --interface tauri
uv run ./yesman.py dash run --interface tauri --dev  # Development mode
```

## 🔧 Quick Start

### Installation

```bash
# Development installation (recommended)
make dev-install
# or directly:
pip install -e . --config-settings editable_mode=compat

# Alternative using uv (recommended for development)
uv run ./yesman.py --help
```

### Basic Commands

```bash
# List available templates and projects
./yesman.py ls

# Create tmux sessions from sessions/ directory
uv run ./yesman.py setup [session-name]
# Or setup all sessions
uv run ./yesman.py setup

# Build SvelteKit for web interface (one-time setup)
cd tauri-dashboard && npm run build && cd ..

# Launch unified SvelteKit dashboard
uv run ./yesman.py dash run -i web --port 8000
# Access at: http://localhost:8000

# Auto-detect best interface
uv run ./yesman.py dash run

# AI learning system management
uv run ./yesman.py ai status

# Comprehensive project status dashboard
uv run ./yesman.py status -i
```

## 📋 Interface Comparison

| Feature | TUI | Web | Tauri | |---------|-----|-----|-------| | **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | | **Resource
Usage** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | | **Cross-platform** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | | **Remote Access** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | |
**User Experience** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | | **Customization** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | | **System Integration** | ⭐⭐ |
⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### When to Use Each Interface

- **TUI**: SSH sessions, minimal resource usage, terminal-only environments
- **Web**: Remote monitoring, team collaboration, browser-based workflows
- **Tauri**: Daily development, best user experience, desktop integration

## 🎯 Advanced Features

### AI Learning System

```bash
# Configure adaptive responses
uv run ./yesman.py ai config -t 0.8

# View learning analytics
uv run ./yesman.py ai history

# Export learning data
uv run ./yesman.py ai export
```


### Performance Monitoring

```bash
# Live performance dashboard
uv run ./yesman.py status -i
```

### Chrome DevTools Integration (Development Only)

The Tauri dashboard includes optional Chrome DevTools Workspace integration for enhanced development experience. This
feature allows direct file editing from Chrome DevTools with automatic hot-reload.

**⚠️ Security Note**: This feature is automatically disabled in production builds.

```bash
# DevTools integration is enabled automatically in development
cd tauri-dashboard && npm run dev

# Access DevTools endpoint (development only)
# http://localhost:5173/.well-known/appspecific/com.chrome.devtools.json
```

For detailed setup and usage instructions, see
[Chrome DevTools Integration Guide](docs/development/chrome-devtools-integration.md).

## 설정 파일

### 글로벌 설정

글로벌 설정 파일은 다음 경로에 위치합니다:

```bash
$HOME/.scripton/yesman/yesman.yaml
$HOME/.scripton/yesman/sessions/   # Individual session files
```

파일 구조 examples/참고

## 템플릿 시스템

Yesman-Claude는 재사용 가능한 tmux 세션 템플릿을 지원합니다. 템플릿을 사용하면 여러 프로젝트에서 일관된 개발 환경을 쉽게 구성할 수 있습니다.

### 템플릿 위치

템플릿 파일은 `~/.scripton/yesman/templates/` 디렉터리에 YAML 형식으로 저장됩니다.

### 기본 템플릿 구조

```yaml
session_name: "{{ session_name }}"
start_directory: "{{ start_directory }}"
windows:
  - window_name: main
    layout: even-horizontal
    panes:
      - claude --dangerously-skip-permissions
      - npm run dev
```

### Smart Templates

"스마트 템플릿"은 조건부 명령 실행을 지원합니다:

```yaml
panes:
  - shell_command: |
      # 의존성이 없거나 오래된 경우에만 설치
      if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
        echo "Dependencies missing or outdated, installing..."
        pnpm install
      else
        echo "Dependencies up to date, skipping install"
      fi
      pnpm dev
```

### 템플릿 사용하기

개별 세션 파일에서 템플릿을 참조하고 필요한 값을 오버라이드할 수 있습니다:

```yaml
# ~/.scripton/yesman/sessions/my_project.yaml
session_name: "my_project"
template_name: "django"
    override:
      session_name: my_django_app
      start_directory: ~/projects/django-app
```

자세한 내용은 [템플릿 문서](docs/user-guide/templates.md)를 참조하세요.

## 🏗️ Development

### Architecture Overview

Yesman Claude는 Phase-3 리팩토링을 통해 현대적이고 유지보수 가능한 아키텍처로 구축되었습니다:

- **Command Pattern**: 모든 CLI 명령어는 `BaseCommand`를 상속하여 일관된 인터페이스 제공
- **Dependency Injection**: 타입 안전한 DI 컨테이너로 서비스 관리 및 테스트 용이성 향상
- **Configuration Management**: Pydantic 스키마 기반의 검증 가능한 설정 시스템
- **Error Handling**: 중앙화된 에러 처리와 사용자 친화적인 복구 힌트

### Quick Start for Developers

```bash
# 개발 환경 설정
git clone <repository-url>
cd yesman-claude
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -e .
pip install pytest pytest-cov ruff black mypy

# 테스트 실행
pytest tests/

# 코드 포맷팅
black .
ruff check .
```

### Documentation

- 📚 [Developer Guide](docs/developer-guide.md) - 개발자를 위한 상세 가이드
- 🏗️ [Architecture Decision Records](docs/adr/) - 아키텍처 결정 기록
- 🧪 [Testing Guide](docs/developer-guide.md#%ED%85%8C%EC%8A%A4%ED%8A%B8-%EA%B0%80%EC%9D%B4%EB%93%9C) - 테스트 작성 및 실행 가이드
- ⚙️ [Configuration](docs/developer-guide.md#%EC%84%A4%EC%A0%95-%EA%B4%80%EB%A6%AC) - 설정 관리 가이드

### Contributing

1. Fork the repository
1. Create a feature branch: `git checkout -b feature/my-feature`
1. Make your changes following the [Developer Guide](docs/developer-guide.md)
1. Add tests for new functionality
1. Ensure all tests pass: `pytest`
1. Format code: `black . && ruff check .`
1. Commit changes: `git commit -m 'feat: add my feature'`
1. Push to the branch: `git push origin feature/my-feature`
1. Create a Pull Request

### Project Structure

```
yesman-claude/
├── commands/           # CLI command implementations
├── libs/core/         # Core architecture components
│   ├── base_command.py    # Command pattern base class
│   ├── container.py       # DI container
│   ├── config_*.py       # Configuration management
│   └── error_handling.py # Error handling system
├── api/               # FastAPI web service
├── tests/             # Test suites
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/              # Documentation
│   ├── adr/              # Architecture Decision Records
│   └── developer-guide.md # Development guide
└── config/            # Environment configurations
```

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.
