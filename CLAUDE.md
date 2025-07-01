# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Yesman-Claude is a CLI automation tool that manages tmux sessions and automates interactions with Claude Code. It uses YAML configuration files with template support to create reproducible development environments.

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

# Create all tmux sessions from projects.yaml
uv run ./yesman.py setup

# Teardown all sessions from projects.yaml
uv run ./yesman.py teardown

# Enter (attach to) a tmux session
uv run ./yesman.py enter [session_name]
uv run ./yesman.py enter  # Interactive selection


# Run TUI dashboard to monitor all sessions
uv run ./yesman.py dashboard
```

### Testing and Development Commands
```bash
# Run specific test files
python -m pytest tests/test_prompt_detector.py
python -m pytest tests/test_content_collector.py

# Run integration tests  
python test_full_automation.py
python test_controller.py

# Debug specific components
python debug_content.py      # Debug content collection
python debug_controller.py   # Debug dashboard controller  
python debug_tmux.py        # Debug tmux operations
```

Currently no formal linting is configured. Future plans include:
- pytest for testing
- ruff for linting/formatting  
- mypy for type checking

## Architecture

### Directory Structure
- `yesman.py` - Main CLI entry point using Click
- `commands/` - CLI command implementations (ls, show, setup, teardown, dashboard)
- `libs/core/` - Core functionality (SessionManager, ClaudeManager, models)
- `libs/streamlit_dashboard/` - Streamlit web dashboard application
- `libs/` - Additional functionality (YesmanConfig, TmuxManager)
- `patterns/` - Auto-response patterns for selection prompts
- `examples/global-yesman/` - Example configuration files

### Configuration Hierarchy
1. Global config: `~/.yesman/yesman.yaml` (logging, default choices)
2. Global projects: `~/.yesman/projects.yaml` (session definitions)
3. Templates: `~/.yesman/templates/*.yaml` (reusable session templates)
4. Local overrides: `./.yesman/*` (project-specific configs)

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

**Streamlit Dashboard** (`libs/streamlit_dashboard/app.py`):
- Web application built with Streamlit for monitoring sessions
- Shows project status, session state, and claude manager activity
- Real-time updates with auto-refresh capability
- Interactive controller management and session monitoring

**Session Templates**:
- Support Jinja2-style variable substitution (removed in latest version)
- Can be overridden per-project in projects.yaml
- Define windows, panes, layouts, and startup commands

### Important Implementation Details

1. **Template Processing**: The `setup` command reads templates from `~/.yesman/templates/`, applies overrides from `projects.yaml`, and creates tmux sessions.

2. **Session Naming**: Sessions can have different names than their project keys using the `session_name` override.

3. **Claude Manager Operation**: The claude manager implements a sophisticated monitoring system:
   - **DashboardController** (`libs/core/claude_manager.py:17`): Main controller manageable from the dashboard
   - **Content Collection** (`libs/core/content_collector.py`): Captures tmux pane content efficiently
   - **Prompt Detection** (`libs/core/prompt_detector.py`): Advanced regex-based prompt recognition system
   - **Auto-Response Patterns**: Pattern files in `patterns/` directory (123/, yn/, 12/) for different prompt types
   - **Monitoring Loop**: Captures content every second and detects interactive prompts
   - **Safe Restart**: Properly terminates existing Claude processes before restarting

4. **Dashboard Architecture**: Uses Streamlit framework for web-based dashboard with reactive data updates. Dashboard displays project configurations from `projects.yaml` and real-time tmux session status.

5. **Error Handling**: Commands check for existing sessions before creation and validate template existence.

6. **Logging**: Configured via `yesman.yaml` with configurable log levels and paths. Claude manager and dashboard use separate log files.

## Current Limitations

- No Jinja2 template rendering (code was removed)
- No automated response system implemented yet
- No LLM integration for continuous workflow
- Limited error recovery mechanisms

## Future Features (from TODO.md)

- Pattern-based automatic response to selection prompts
- LLM integration for decision making
- Session monitoring and status display
- Performance improvements with caching
- Multi-engine support (GPT, Claude-3, etc.)

## Development Workflow

When working on this codebase:

1. **Adding New Commands**: Create new command files in `commands/` directory and register them in `yesman.py:17-22`
2. **Claude Manager Modifications**: 
   - Core logic in `libs/core/claude_manager.py` (DashboardController class)
   - Pattern detection in `libs/core/prompt_detector.py` (ClaudePromptDetector class)
   - Content collection in `libs/core/content_collector.py`
   - Auto-response patterns stored in `patterns/` subdirectories
3. **Dashboard Updates**: Web dashboard components in `libs/streamlit_dashboard/app.py` using Streamlit framework
4. **Configuration Changes**: Global config structure defined in `YesmanConfig` class (`libs/yesman_config.py`)
5. **Testing**: Use debug scripts (`debug_*.py`) and test files in `tests/` for component testing

### Pattern-Based Auto-Response System
The system uses pattern files to recognize and respond to different prompt types:
- `patterns/123/`: For numbered selection prompts (1, 2, 3 options)
- `patterns/yn/`: For yes/no binary choices  
- `patterns/12/`: For simple binary selections (1/2 options)
Each pattern file contains regex patterns to match specific prompt formats.

## Dependencies

Core dependencies (from pyproject.toml):
- click>=8.0 - CLI framework
- pyyaml>=5.4 - YAML parsing  
- pexpect>=4.8 - Process automation
- tmuxp>=1.55.0 - Tmux session management
- libtmux>=0.46.2 - Python tmux bindings
- streamlit>=1.28.0 - Web framework for dashboard
- rich>=13.0.0 - Terminal formatting and UI components

## Key Implementation Notes

### Claude Code Integration
- The tool specifically targets Claude Code (claude.ai/code) automation
- Monitors tmux panes running Claude Code sessions
- Detects interactive prompts using advanced pattern matching
- Auto-responds to trust prompts, selections, and confirmations

### Session Management
- Uses tmuxp for declarative session configuration
- Sessions defined in YAML templates with window/pane layouts
- Supports both global (`~/.yesman/`) and local (`./.yesman/`) configurations
- Templates can be overridden per-project in `projects.yaml`

### Monitoring and Control
- Real-time content collection from tmux panes
- Sophisticated prompt detection with confidence scoring
- Dashboard provides web-based session monitoring and control
- Auto-response history tracking and management