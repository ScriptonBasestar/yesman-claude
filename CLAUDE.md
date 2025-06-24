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
```

### Running Commands
```bash
# List available templates and projects
./yesman.py ls

# Show running tmux sessions  
./yesman.py show

# Create all tmux sessions from projects.yaml
./yesman.py setup

# Teardown all sessions from projects.yaml
./yesman.py teardown

# Enter (attach to) a tmux session
./yesman.py enter [session_name]
./yesman.py enter  # Interactive selection

# Run controller for a specific session
./yesman.py controller <session_name>

# Run dashboard to monitor all sessions
./yesman.py dashboard
```

### Testing and Linting
Currently no test suite or linting is configured. Future plans include:
- pytest for testing
- ruff for linting/formatting
- mypy for type checking

## Architecture

### Directory Structure
- `yesman.py` - Main CLI entry point using Click
- `commands/` - CLI command implementations (ls, show, setup, teardown)
- `libs/` - Core functionality (YesmanConfig, TmuxManager)
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

**Session Templates**:
- Support Jinja2-style variable substitution (removed in latest version)
- Can be overridden per-project in projects.yaml
- Define windows, panes, layouts, and startup commands

### Important Implementation Details

1. **Template Processing**: The `setup` command reads templates from `~/.yesman/templates/`, applies overrides from `projects.yaml`, and creates tmux sessions.

2. **Session Naming**: Sessions can have different names than their project keys using the `session_name` override.

3. **Error Handling**: Commands check for existing sessions before creation and validate template existence.

4. **Logging**: Configured via `yesman.yaml` with configurable log levels and paths.

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

## Dependencies

Core dependencies (from pyproject.toml):
- click>=8.0 - CLI framework
- pyyaml>=5.4 - YAML parsing
- pexpect>=4.8 - Process automation
- tmuxp>=1.55.0 - Tmux session management
- libtmux>=0.46.2 - Python tmux bindings