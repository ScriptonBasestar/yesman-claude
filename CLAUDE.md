# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Yesman-Claude is a CLI automation tool that manages tmux sessions and automates interactions with Claude Code. It
provides multiple dashboard interfaces (TUI, Web, Tauri) for monitoring and controlling development environments.

## Key Architecture Concepts

### 1. Command Pattern Architecture

All CLI commands inherit from `BaseCommand` in `libs/core/base_command.py`. Commands must implement:

- `execute()` method that returns a dict with success status
- Mixins for shared functionality (SessionCommandMixin, ConfigCommandMixin)
- Standardized error handling via `CommandError`

### 2. Session Management System

- Sessions are defined in YAML files under `~/.scripton/yesman/sessions/`
- Templates live in `~/.scripton/yesman/templates/`
- The `TmuxManager` class handles all tmux interactions
- Projects.yaml has been removed - use individual session files only

### 3. Dashboard Architecture

- Three interfaces: TUI (terminal), Web (SvelteKit/FastAPI), Tauri (desktop)
- All dashboards share the same SvelteKit codebase
- FastAPI backend at `api/` provides REST endpoints
- Real-time updates via WebSocket connections

### 4. Claude Automation

- `ClaudeMonitor` watches tmux panes for Claude prompts
- `ClaudePromptDetector` identifies different prompt types
- `AdaptiveResponse` system learns from user behavior
- Auto-response to Y/N, selection, and continuation prompts

## Essential Development Commands

### Running and Testing

```bash
# Development with uv (recommended)
uv run ./yesman.py --help
uv run ./yesman.py setup [session-name]
uv run ./yesman.py dash run -i web --port 8000

# Testing
make test              # Run all tests with coverage
make test-unit         # Run unit tests only
make test-integration  # Run integration tests
pytest tests/unit/test_specific.py::TestClass::test_method  # Run single test

# Linting and formatting
make lint              # Run ruff and mypy checks
make fmt               # Format with black and isort
make quick             # Quick check (lint-fast + test-unit)
make full              # Full quality check before commits
```

### Building

```bash
# Build everything
make build-all

# Build specific components
make build             # Build Python package
make build-dashboard   # Build SvelteKit (required for web interface)
cd tauri-dashboard && npm run build

# Run Tauri development
cd tauri-dashboard && npm run tauri:dev
```

### Session Management

```bash
# List sessions
./yesman.py ls

# Setup sessions
./yesman.py setup              # Setup all sessions
./yesman.py setup session-name  # Setup specific session

# Teardown
./yesman.py teardown           # Teardown all
./yesman.py teardown name      # Teardown specific
```

## Code Organization Patterns

### Adding New Commands

1. Create file in `commands/` directory
1. Import and use `@click.command()` decorator
1. Create command class inheriting from `BaseCommand`
1. Implement `execute()` method
1. Add command to `yesman.py` imports and CLI group

Example:

```python
from libs.core.base_command import BaseCommand, CommandError

class MyCommand(BaseCommand):
    def execute(self, **kwargs) -> dict:
        try:
            # Implementation
            return {"success": True, "result": data}
        except Exception as e:
            raise CommandError(f"Failed: {e}") from e
```

### Working with Sessions

- Session configs use Pydantic models in `libs/core/config_schema.py`
- Always validate paths with `validate_directory_path()` from `libs/validation.py`
- Use `TmuxManager.create_session()` for session creation
- Handle missing directories by prompting user to create them

### API Development

- All API routes in `api/routers/`
- Use dependency injection with `get_tmux_manager()`
- Return standardized responses using models from `api/models.py`
- WebSocket support via `api/routers/websocket_router.py`

## Important Configuration

### Lint Configuration (ruff.toml)

- Line length: 200
- Python 3.11+
- Classes with many methods are allowed for facade patterns:
  - `DashboardController`, `ClaudeMonitor`, `EventStrategy`, `KeyboardNavigationManager`

### Type Checking

- All code should have type hints
- Use `from typing import Any` when needed
- Run `make type-check` to verify

### Testing Patterns

- Unit tests mirror source structure under `tests/unit/`
- Integration tests in `tests/integration/`
- Use pytest fixtures from `tests/conftest.py`
- Mock tmux operations, don't require actual tmux for unit tests

## Common Issues and Solutions

### Import Errors

- Ensure running with `uv run` or proper virtualenv
- Check PYTHONPATH includes project root
- Use absolute imports: `from libs.core.base_command import BaseCommand`

### Session Creation Failures

- Verify tmux is installed: `which tmux`
- Check session YAML syntax
- Ensure start_directory exists or handle creation
- Check for existing sessions with same name

### Dashboard Issues

- Web dashboard requires building first: `cd tauri-dashboard && npm run build`
- API must be running for web interface: check port 8000
- Tauri requires Rust toolchain for development

## Development Workflow

1. Make changes following existing patterns
1. Run `make quick` for fast validation
1. Run `make full` before committing
1. Use standardized commit messages: `type(scope): description`
1. All commits should be signed with `--no-verify` if using pre-commit hooks

## Key Technical Decisions

- Removed `projects.yaml` in favor of individual session files
- Removed commands: browse, logs, automate, multi-agent, task-runner
- Using uv for Python package management
- All dashboards share SvelteKit codebase
- Pydantic for configuration validation
- Phase-3 refactoring emphasizes type safety and dependency injection
