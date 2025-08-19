# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Yesman-Claude is a comprehensive CLI automation tool that manages tmux sessions and automates interactions with Claude Code. It features multiple dashboard interfaces (TUI, Web, Tauri), AI-powered learning system, and extensive session management capabilities using YAML configuration templates.

## Development Commands

### Environment Setup

```bash
# Development installation (recommended approach)
make dev-install
# or directly:
pip install -e . --config-settings editable_mode=compat

# Using uv (fastest, preferred for development)
uv run ./yesman.py --help

# Install all development dependencies
make install-all
```

### Core Commands

```bash
# Session management
./yesman.py ls                    # List templates and projects
./yesman.py setup [session-name]  # Create tmux sessions
./yesman.py teardown [session-name] # Remove sessions
./yesman.py show                  # List running sessions
./yesman.py enter [session-name]  # Attach to session
./yesman.py validate             # Validate configurations

# Dashboard interfaces
./yesman.py dashboard run                    # Auto-detect best interface
./yesman.py dashboard run --interface tui   # Rich terminal interface
./yesman.py dashboard run --interface web   # SvelteKit web interface
./yesman.py dashboard run --interface tauri # Native desktop app

# AI learning system
./yesman.py ai status           # Show AI learning status
./yesman.py ai config -t 0.8    # Set confidence threshold
./yesman.py ai history          # View response history
./yesman.py ai export           # Export learning data
./yesman.py ai cleanup          # Clean old data

# Status and monitoring
./yesman.py status              # Quick status overview
./yesman.py status -i           # Interactive live dashboard
./yesman.py status -d           # Detailed view
```

### Development Workflow

```bash
# Build and development
make build-all                  # Build complete project
make build-dashboard            # Build SvelteKit components only
cd tauri-dashboard && npm run build  # Build frontend assets

# Development servers
make dev-dashboard              # Full development environment
make run-web-dashboard          # Web dashboard only
make run-tauri-dev              # Tauri development mode

# API development
cd api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 10501

# Quality checks
make quick                      # Fast check (lint + unit tests)
make full                       # Complete quality check
make format                     # Code formatting
make test                       # Run all tests
make test-unit                  # Unit tests only
make test-integration           # Integration tests only
```

### Testing

```bash
# Test execution
pytest tests/                           # All tests
pytest tests/unit/                      # Unit tests only
pytest tests/integration/               # Integration tests only
pytest tests/test_specific_file.py      # Single test file
pytest -k "test_session"                # Tests matching pattern
pytest --cov=libs --cov=commands        # With coverage

# Test categories (via markers)
pytest -m "unit"                        # Unit tests
pytest -m "integration"                 # Integration tests
pytest -m "slow"                        # Long-running tests
pytest -m "security"                    # Security tests
```

## Architecture Overview

### Core Design Patterns

**Command Pattern**: All CLI commands inherit from `BaseCommand` (`libs/core/base_command.py`) providing:

- Consistent error handling with recovery hints
- Dependency injection integration
- Standardized logging and configuration access
- Type-safe service resolution

**Dependency Injection**: Central DI container (`libs/core/container.py`) manages:

- Service lifecycle (singletons vs factories)
- Type-safe service resolution
- Circular dependency detection
- Configuration-based service registration

**Configuration Management**: Pydantic-based system (`libs/core/config_*`) with:

- Schema validation for YAML configs
- Environment-specific overrides
- Hierarchical config merging (global → local → project)
- Runtime configuration caching

### Key Architectural Components

**Session Management**:

- `libs/core/session_manager.py` - Core session lifecycle
- `libs/tmux_manager.py` - tmux integration layer
- YAML-based session templates with Jinja2-style variables
- Smart dependency optimization for faster session creation

**Claude Code Automation**:

- `libs/core/claude_manager.py` - Main automation controller
- `libs/core/prompt_detector.py` - Pattern-based prompt recognition
- `libs/core/content_collector.py` - Real-time content capture
- AI learning system with confidence scoring and pattern adaptation

**Multi-Interface Dashboard**:

- **TUI**: Rich-based terminal interface with live updates
- **Web**: SvelteKit + FastAPI serving static assets
- **Tauri**: Native desktop app sharing SvelteKit codebase
- Interface auto-detection based on environment capabilities

**Error Handling**:

- Centralized error system (`libs/core/error_handling.py`)
- Categorized error types with severity levels
- Automatic recovery hint generation
- Context preservation across error boundaries

### Data Flow Architecture

1. **Command Execution**: CLI commands → BaseCommand → Service resolution → Business logic
1. **Configuration Loading**: YAML files → Pydantic validation → Config cache → Service injection
1. **Session Creation**: Template selection → Variable substitution → tmux session creation → Claude automation setup
1. **Real-time Monitoring**: Content collection → Pattern detection → AI decision → Automated response
1. **Dashboard Updates**: Service events → FastAPI/WebSocket → Frontend updates

### File Structure Logic

```
libs/core/              # Core architecture components
├── base_command.py        # Command pattern implementation
├── container.py           # Dependency injection system
├── config_*.py           # Configuration management
├── error_handling.py     # Centralized error handling
├── services.py           # Service registration and factories
└── interfaces.py         # Type definitions and contracts

commands/               # CLI command implementations
├── [command].py          # Each inherits from BaseCommand
└── __init__.py          # Command registration

api/                   # FastAPI web service
├── main.py              # FastAPI app with CORS and middleware
├── routers/             # API endpoint groupings
├── middleware/          # Custom middleware
└── background_tasks.py  # Async task management

tauri-dashboard/       # SvelteKit frontend (shared by web/tauri)
├── src/routes/          # SvelteKit pages
├── src/lib/            # Reusable components
└── src-tauri/          # Rust backend for desktop app
```

### Service Registration Pattern

Services are registered in `libs/core/services.py` using the DI container:

```python
# Singleton services (shared state)
container.register_singleton(YesmanConfig, config_instance)

# Factory services (new instance per request) 
container.register_factory(TmuxManager, lambda: TmuxManager(config))

# Type-safe resolution in commands
config = container.resolve(YesmanConfig)
```

### Configuration Hierarchy

1. **Global**: `~/.scripton/yesman/yesman.yaml` (logging, defaults)
1. **Templates**: `~/.scripton/yesman/templates/*.yaml` (reusable patterns)
1. **Sessions**: `~/.scripton/yesman/sessions/*.yaml` (individual session configs)
1. **Local**: `./.scripton/yesman/*` (project-specific overrides)

Templates support variable substitution and conditional logic for intelligent session creation.

### AI Learning System

The adaptive response system (`libs/ai/`) learns user patterns:

- Response confidence scoring with adjustable thresholds
- Pattern classification for different prompt types
- JSON-based persistence of learned behaviors
- Export/import capabilities for data portability

### Dashboard Interface Strategy

**Interface Selection Logic**:

1. Tauri (best UX) if desktop environment detected
1. Web (universal access) if browser available
1. TUI (minimal resources) as fallback

**Shared Frontend**: SvelteKit codebase serves both web and Tauri interfaces, with Tauri providing native desktop integration (system tray, notifications, file system access).

### Error Recovery Design

Errors include context-aware recovery hints:

- Configuration errors → suggest config file locations
- Missing dependencies → provide installation commands
- Session conflicts → offer resolution strategies
- Permission issues → suggest ownership fixes

This architecture emphasizes maintainability, testability, and extensibility while providing consistent behavior across all interfaces and deployment scenarios.
