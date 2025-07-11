# Yesman Claude

Yesman-Claude is a comprehensive CLI automation tool that manages tmux sessions and automates interactions with Claude Code. It provides multiple dashboard interfaces for monitoring and controlling your development environment.

## 🚀 Key Features

- **Session Management**: Create and manage tmux sessions using YAML templates
- **Claude Code Automation**: Automatic response to Claude Code prompts and selections
- **Multiple Dashboard Interfaces**: Choose from TUI, Web, or native desktop interfaces
- **Real-time Monitoring**: Live session activity tracking and health monitoring
- **AI-Powered Learning**: Adaptive response system that learns from user behavior
- **Performance Optimization**: Built-in performance monitoring and optimization strategies

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
uv run ./yesman.py dash run --interface web --port 8080
# Access at: http://localhost:8080

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

# Create all tmux sessions from projects.yaml
uv run ./yesman.py up

# Build SvelteKit for web interface (one-time setup)
cd tauri-dashboard && npm run build && cd ..

# Launch unified SvelteKit dashboard
uv run ./yesman.py dash run -i web --port 8080
# Access at: http://localhost:8080

# Auto-detect best interface
uv run ./yesman.py dash run

# Interactive session browser
uv run ./yesman.py browse

# AI learning system management
uv run ./yesman.py ai status

# Comprehensive project status dashboard
uv run ./yesman.py status -i

# Context-aware automation
uv run ./yesman.py automate monitor
```

## 📋 Interface Comparison

| Feature | TUI | Web | Tauri |
|---------|-----|-----|-------|
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Resource Usage** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Cross-platform** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Remote Access** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| **User Experience** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Customization** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **System Integration** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

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

### Context-Aware Automation
```bash
# Monitor development context
uv run ./yesman.py automate monitor

# Detect workflow patterns
uv run ./yesman.py automate detect

# Configure automation rules
uv run ./yesman.py automate config
```

### Performance Monitoring
```bash
# Live performance dashboard
uv run ./yesman.py status -i

# Analyze log patterns
uv run ./yesman.py logs analyze

# Cleanup old logs
uv run ./yesman.py logs cleanup
```

### Chrome DevTools Integration (Development Only)
The Tauri dashboard includes optional Chrome DevTools Workspace integration for enhanced development experience. This feature allows direct file editing from Chrome DevTools with automatic hot-reload.

**⚠️ Security Note**: This feature is automatically disabled in production builds.

```bash
# DevTools integration is enabled automatically in development
cd tauri-dashboard && npm run dev

# Access DevTools endpoint (development only)
# http://localhost:5173/.well-known/appspecific/com.chrome.devtools.json
```

For detailed setup and usage instructions, see [Chrome DevTools Integration Guide](docs/development/chrome-devtools-integration.md).

## 설정 파일

### 글로벌 설정

글로벌 설정 파일은 다음 경로에 위치합니다:

```bash
$HOME/.yesman/yesman.yaml
$HOME/.yesman/projects.yaml
```

파일 구조 examples/참고

## 템플릿 시스템

Yesman-Claude는 재사용 가능한 tmux 세션 템플릿을 지원합니다. 템플릿을 사용하면 여러 프로젝트에서 일관된 개발 환경을 쉽게 구성할 수 있습니다.

### 템플릿 위치
템플릿 파일은 `~/.yesman/templates/` 디렉터리에 YAML 형식으로 저장됩니다.

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
`projects.yaml`에서 템플릿을 참조하고 필요한 값을 오버라이드할 수 있습니다:

```yaml
sessions:
  my_project:
    template_name: django
    override:
      session_name: my_django_app
      start_directory: ~/projects/django-app
```

자세한 내용은 [템플릿 문서](docs/user-guide/templates.md)를 참조하세요.
