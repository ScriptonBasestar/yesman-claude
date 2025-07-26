# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Yesman-Claude is a CLI automation tool that manages tmux sessions and automates interactions with Claude Code. It uses
YAML configuration files with template support to create reproducible development environments.

## Development Commands

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

# Command removed - automate functionality has been deprecated
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

See [Code Quality Guide](/docs/development/code-quality-guide.md) for detailed information.

## Architecture

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
1. Session files: `~/.scripton/yesman/sessions/*.yaml` (individual session definitions)
1. Templates: `~/.scripton/yesman/templates/*.yaml` (reusable session templates)
1. Local overrides: `./.scripton/yesman/*` (project-specific configs)

Configuration merge modes:

- `merge` (default): Local configs override global
- `local`: Use only local configs

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
- **NEW**: Interactive session browser with grid, list, and heatmap views
- **NEW**: Activity level visualization and session statistics

**FastAPI Server** (`api/main.py`):

- REST API endpoints for session and controller management
- Provides backend services for external integrations
- Includes routers for sessions and controllers

**Tauri Desktop App** (`tauri-dashboard/`):

- Native desktop application using Tauri + SvelteKit
- Rust backend with TypeScript frontend
- Primary dashboard interface for monitoring and control
- System tray integration and native notifications

**AI Learning System** (`libs/ai/`):

- **ResponseAnalyzer** (`libs/ai/response_analyzer.py`): Pattern analysis and learning engine
- **AdaptiveResponse** (`libs/ai/adaptive_response.py`): AI-powered auto-response system
- Learns from user behavior and improves response accuracy over time
- Pattern classification for different prompt types (yes/no, numbered selections, etc.)
- Confidence scoring and prediction algorithms
- JSON-based persistence for learned patterns and responses

**Context-Aware Automation** (`libs/automation/`):

- **ContextDetector** (`libs/automation/context_detector.py`): Workflow context detection system
- **WorkflowEngine** (`libs/automation/workflow_engine.py`): Automation chain execution engine
- **[Removed] AutomationManager**: Previously handled automated workflows (deprecated)

**Project Health Monitoring** (`libs/dashboard/`):

- **HealthCalculator** (`libs/dashboard/health_calculator.py`): Comprehensive project health assessment
- Evaluates 8 categories: build, tests, dependencies, security, performance, code quality, git, documentation
- Real-time health scoring and visualization
- Integration with Tauri dashboard for live monitoring

**High-Performance Logging** (`libs/logging/`):

- **AsyncLogger** (`libs/logging/async_logger.py`): Queue-based asynchronous logging system
- **BatchProcessor** (`libs/logging/batch_processor.py`): Optimized batch log processing
- Non-blocking log queues with compression support
- JSON Lines format with Gzip compression for efficiency
- Performance monitoring and statistics tracking

**Session Templates**:

- Support Jinja2-style variable substitution (removed in latest version)
- Can be customized in individual session files
- Define windows, panes, layouts, and startup commands

### Important Implementation Details

1. **Template Processing**: The `setup` command reads templates from `~/.scripton/yesman/templates/` or individual session files from `~/.scripton/yesman/sessions/`, and creates tmux sessions.

1. **Session Naming**: Sessions can have different names than their project keys using the `session_name` override.

1. **Claude Manager Operation**: The claude manager implements a sophisticated monitoring system:

   - **DashboardController** (`libs/core/claude_manager.py`): Main controller manageable from the dashboard
   - **Content Collection** (`libs/core/content_collector.py`): Captures tmux pane content efficiently
   - **Prompt Detection** (`libs/core/prompt_detector.py`): Advanced regex-based prompt recognition system
   - **Auto-Response Patterns**: Pattern files in `patterns/` directory (123/, yn/, 12/) for different prompt types
   - **Monitoring Loop**: Captures content every second and detects interactive prompts
   - **Safe Restart**: Properly terminates existing Claude processes before restarting
   - **Caching System**: Advanced caching with analytics (`libs/core/cache_*.py` modules)

1. **Multi-Interface Architecture**:

   - **Tauri Desktop App**: Primary native desktop interface for session monitoring
   - **FastAPI Server**: REST API for programmatic access and integration
   - **CLI Interface**: Command-line tool for direct automation and scripting

1. **Error Handling**: Commands check for existing sessions before creation and validate template existence.

1. **Logging**: Configured via `yesman.yaml` with configurable log levels and paths. Claude manager and dashboard use
   separate log files.

## ✅ Recently Implemented Features (2025-07-07)

### 🚀 Performance Improvements

- **Smart Session Caching**: TTL-based caching system with 5-second default cache
- **Async Logging**: High-performance queue-based logging with compression support
- **Optimized Dashboard**: Reduced tmux server load with intelligent caching

### 🎨 Enhanced User Experience

- **Interactive Session Browser**: File-browser-like navigation with tree/list/grid views
- **Activity Heatmap**: Visual session activity tracking over time
- **Comprehensive Status Dashboard**: Real-time project health monitoring
- **Rich Terminal UI**: Enhanced visualization with progress bars, charts, and color coding

### 🤖 AI-Powered Features

- **Adaptive Response System**: Machine learning-based auto-response with confidence scoring
- **Pattern Learning**: System learns from user behavior and improves accuracy over time
- **Response Analytics**: Detailed statistics and trend analysis for AI responses
- **Confidence Thresholds**: Adjustable confidence levels for different prompt types

### 🔧 Advanced Automation

- **Context-Aware Workflows**: Detects git commits, test failures, build events automatically
- **Workflow Chains**: Configurable automation sequences (test → build → deploy)
- **Smart Triggers**: 8 different context types for comprehensive project monitoring
- **Real-time Detection**: Continuous monitoring with customizable intervals

### 📊 Monitoring & Analytics

- **Project Health Calculator**: 8-category health assessment (build, tests, dependencies, etc.)
- **Git Activity Tracking**: Commit history, contributor analysis, file change metrics
- **TODO Progress Tracking**: Visual progress bars and completion statistics
- **Log Analysis**: Pattern detection, error tracking, and performance metrics

### 🛠️ Developer Tools

- **Extended CLI Commands**: Multiple command groups (browse, status, ai, logs, etc.)
- **REST API Integration**: FastAPI endpoints for external tool integration
- **Configuration Management**: Advanced config merging and validation
- **Debug Utilities**: Comprehensive debugging and diagnostic tools

## Current Capabilities

✅ **Automated Response System**: Fully implemented with AI learning ✅ **Session Monitoring**: Real-time activity
tracking and visualization\
✅ **Performance Optimization**: Smart caching and async processing ✅ **Multi-Interface Support**: CLI, REST API, and
native desktop app ✅ **Pattern-Based Recognition**: Advanced prompt detection and auto-response ✅ **Context-Aware
Automation**: Workflow chains triggered by project events

## Development Workflow

When working on this codebase:

1. **Adding New Commands**: Create new command files in `commands/` directory and register them in `yesman.py:17-22`
1. **Claude Manager Modifications**:
   - Core logic in `libs/core/claude_manager.py` (DashboardController class)
   - Pattern detection in `libs/core/prompt_detector.py` (ClaudePromptDetector class)
   - Content collection in `libs/core/content_collector.py`
   - Auto-response patterns stored in `patterns/` subdirectories
   - Caching system components in `libs/core/cache_*.py` modules
1. **Dashboard Updates**:
   - Tauri: Native desktop app components in `tauri-dashboard/src/`
   - FastAPI: REST API endpoints in `api/routers/`
   - Web Interface: Browser-based components via Tauri's embedded WebView
1. **Configuration Changes**: Global config structure defined in `YesmanConfig` class (`libs/yesman_config.py`)
1. **Testing**: Use debug scripts in `debug/` directory and test files in `tests/` for component testing

### Pattern-Based Auto-Response System

The system uses pattern files to recognize and respond to different prompt types:

- `patterns/123/`: For numbered selection prompts (1, 2, 3 options)
- `patterns/yn/`: For yes/no binary choices
- `patterns/12/`: For simple binary selections (1/2 options) Each pattern file contains regex patterns to match specific
  prompt formats.

## Dependencies

Core dependencies (from pyproject.toml):

- click>=8.0 - CLI framework
- pyyaml>=5.4 - YAML parsing
- pexpect>=4.8 - Process automation
- tmuxp>=1.55.0 - Tmux session management
- libtmux>=0.46.2 - Python tmux bindings
- rich>=13.0.0 - Terminal formatting and UI components
- psutil>=5.9.0 - System and process utilities

Additional development dependencies:

- fastapi - REST API framework (api/ directory)
- uvicorn - ASGI server for FastAPI

Tauri Desktop App Stack (tauri-dashboard/ directory):

- tauri - Desktop app framework with Rust backend
- sveltekit - Frontend framework for reactive UI
- typescript - Type safety for frontend development
- tailwindcss + daisyui - CSS framework and component library

## Key Implementation Notes

### Claude Code Integration

- The tool specifically targets Claude Code (claude.ai/code) automation
- Monitors tmux panes running Claude Code sessions
- Detects interactive prompts using advanced pattern matching
- Auto-responds to trust prompts, selections, and confirmations

### Session Management

- Uses tmuxp for declarative session configuration
- Sessions defined in YAML templates with window/pane layouts
- Supports both global (`~/.scripton/yesman/`) and local (`./.scripton/yesman/`) configurations
- Templates can be customized in individual session YAML files

### Monitoring and Control

- Real-time content collection from tmux panes
- Sophisticated prompt detection with confidence scoring
- Tauri desktop dashboard provides native session monitoring and control
- Auto-response history tracking and management
- Cross-platform native performance with web-based flexibility
