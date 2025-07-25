# Yesman-Claude Configuration Examples

This directory contains comprehensive configuration examples for various use cases, scenarios, and edge cases.

## Directory Structure

```
examples/
├── README.md                    # This file
├── basic/                       # Basic configuration examples
├── advanced/                    # Advanced configuration with complex layouts
├── multi-project/              # Multi-project workspace examples
├── team-collaboration/         # Team collaboration setups
├── edge-cases/                 # Edge cases and error handling examples
├── templates/                  # Reusable template examples
├── sessions-directory/         # Using sessions/*.yaml files
├── sessions-only/              # Complete migration to sessions-only structure
├── configuration-hierarchy/    # Configuration inheritance examples
├── global-yesman/              # Global configuration with templates
├── local-yesman/               # Project-local configurations
└── mixed-configuration/        # Mixing projects.yaml and sessions/*.yaml
```

## Configuration Files

### Core Configuration Files

1. **yesman.yaml** - Main configuration file
2. **projects.yaml** - Project definitions and session configurations
3. **templates/*.yaml** - Reusable session templates

### Configuration Hierarchy

```
~/.scripton/yesman/yesman.yaml     # Global user configuration
~/project/.yesman/yesman.yaml      # Project-specific configuration
./yesman.yaml                      # Local directory configuration
```

## Quick Start

1. Copy the example that matches your use case
2. Modify the paths and settings to match your environment
3. Run `yesman up` to create sessions

## Examples Overview

### Core Examples
- **basic/** - Simple single-project setups for getting started
- **advanced/** - Complex layouts with multiple panes, windows, and advanced features
- **templates/** - Reusable session templates for common workflows

### Organization Patterns
- **multi-project/** - Managing multiple projects simultaneously
- **team-collaboration/** - Shared team configurations and conventions
- **sessions-directory/** - Using individual session files in sessions/*.yaml
- **sessions-only/** - Complete migration from projects.yaml to sessions/*.yaml

### Configuration Management
- **configuration-hierarchy/** - Understanding configuration inheritance and overrides
- **global-yesman/** - Global user configuration with template library
- **local-yesman/** - Project-specific local configurations
- **mixed-configuration/** - Combining projects.yaml with sessions/*.yaml

### Special Cases
- **edge-cases/** - Handling errors, missing dependencies, and special scenarios

## Common Patterns

### 1. Development Workflow
```yaml
# Common development setup with editor, server, and logs
windows:
  - window_name: "dev"
    panes:
      - claude --dangerously-skip-permissions
      - command: "npm run dev"
      - command: "tail -f logs/app.log"
```

### 2. Multi-Service Architecture
```yaml
# Microservices with frontend, backend, and database
sessions:
  frontend:
    template_name: "react-app"
  backend:
    template_name: "fastapi"
  database:
    template_name: "postgres-dev"
```

### 3. Data Science Workflow
```yaml
# Jupyter, data processing, and monitoring
windows:
  - window_name: "jupyter"
    panes:
      - command: "jupyter lab"
  - window_name: "processing"
    panes:
      - claude
      - command: "python data_pipeline.py --watch"
```

## Best Practices

1. **Use Templates** - Create reusable templates for common patterns
2. **Environment Variables** - Use environment-specific variables
3. **Modular Sessions** - Split complex setups into multiple sessions
4. **Version Control** - Keep configurations in version control
5. **Documentation** - Document custom commands and workflows

## Quick Reference

### Session Configuration Keys
- `session_name` - Unique session identifier
- `template_name` - Reference to a template
- `start_directory` - Working directory for the session
- `environment` - Environment variables
- `before_script` - Setup commands run once
- `windows` - Window and pane configurations

### Window Layout Options
- `even-horizontal` - Equal horizontal splits
- `even-vertical` - Equal vertical splits
- `main-horizontal` - Large top pane, smaller bottom
- `main-vertical` - Large left pane, smaller right
- `tiled` - Equal sized grid layout