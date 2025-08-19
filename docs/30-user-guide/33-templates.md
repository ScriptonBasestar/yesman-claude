# Yesman-Claude Templates Documentation

## Overview

Yesman-Claude uses YAML templates to define reusable tmux session configurations. Templates allow you to create
consistent development environments across different projects with minimal configuration.

## Template Structure

Templates are YAML files stored in `~/.scripton/yesman/templates/` with the following structure:

```yaml
session_name: "{{ session_name }}"
start_directory: "{{ start_directory }}"
before_script: # Optional: Commands to run before creating windows
windows:
  - window_name: main
    layout: even-horizontal
    start_directory: ./  # Optional: Override session start_directory
    panes:
      - command1
      - command2
```

## Key Features

### 1. Variable Substitution

Templates support variable substitution using `{{ variable_name }}` syntax:

- `{{ session_name }}`: The name of the tmux session
- `{{ start_directory }}`: The starting directory for the session

These variables are replaced when creating sessions from projects.yaml.

### 2. Smart Templates

The "smart template" feature allows conditional command execution within panes. This is particularly useful for:

- **Dependency Management**: Only install dependencies if needed
- **Environment Setup**: Check conditions before running commands
- **Resource Optimization**: Avoid unnecessary operations

Example from `smart-frontend.yaml`:

```yaml
windows:
  - window_name: main
    panes:
      - claude --dangerously-skip-permissions
      - shell_command: |
          # Smart dependency check - only install if needed
          if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
            echo "Dependencies missing or outdated, installing..."
            pnpm install
          else
            echo "Dependencies up to date, skipping install"
          fi
          # Start dev server after dependency check
          pnpm dev
```

### 3. Template Overrides

When using templates in `projects.yaml`, you can override any template value:

```yaml
sessions:
  my_project:
    template_name: django
    override:
      session_name: custom_name
      start_directory: ~/my/custom/path
      windows:
        - window_name: custom_window
          panes:
            - custom_command
```

## Template Examples

### Basic Template (my-project.yaml)

```yaml
session_name: homepage
windows:
  - window_name: my-awesome-project
    start_directory: ~/dev/my-awesome-project
    layout: even-horizontal
    panes:
      - shell_command:
          - 'claude --dangerously-skip-permissions'
      - # Empty pane (shell)
```

### Django Template (django.yaml)

```yaml
session_name: "{{ session_name }}"
start_directory: "{{ start_directory }}"
before_script: uv sync
windows:
  - window_name: django server
    layout: even-horizontal
    panes:
      - claude --dangerously-skip-permissions
      - uv run ./manage.py runserver
      - htop
  - window_name: django logs
    panes:
      - tail -f django.log
```

### Fiber Template (fiber.yaml)

```yaml
session_name: "{{ session_name }}"
start_directory: "{{ start_directory }}"
before_script:
  - make build
  - make setup
windows:
  - window_name: backend
    layout: even-horizontal
    start_directory: ./backend
    panes:
      - claude --dangerously-skip-permissions
      - make run
  - window_name: frontend
    layout: even-horizontal
    start_directory: ./frontend
    panes:
      - claude --dangerously-skip-permissions
      - pnpm dev
```

## Using Templates

### 1. Create a Template

Place your template file in `~/.scripton/yesman/templates/`:

```bash
# Create templates directory if it doesn't exist
mkdir -p ~/.scripton/yesman/templates

# Create a new template
cat > ~/.scripton/yesman/templates/myapp.yaml << EOF
session_name: "{{ session_name }}"
start_directory: "{{ start_directory }}"
windows:
  - window_name: development
    panes:
      - claude --dangerously-skip-permissions
      - npm run dev
EOF
```

### 2. Reference in projects.yaml

```yaml
sessions:
  my_webapp:
    template_name: myapp
    override:
      session_name: webapp
      start_directory: ~/projects/webapp
```

### 3. Create Sessions

```bash
# Create all sessions from projects.yaml
yesman up

# Or create a specific session
yesman up my_webapp
```

## Best Practices

1. **Use Variables**: Leverage `{{ session_name }}` and `{{ start_directory }}` for reusability
1. **Smart Commands**: Use conditional logic in shell commands to optimize startup time
1. **Meaningful Names**: Use descriptive names for templates and windows
1. **Layout Choice**: Choose appropriate layouts (even-horizontal, even-vertical, main-horizontal, main-vertical, tiled)
1. **Before Scripts**: Use `before_script` for one-time setup commands

## Common Patterns

### Development Environment

```yaml
windows:
  - window_name: editor
    panes:
      - claude --dangerously-skip-permissions
  - window_name: server
    panes:
      - npm run dev
  - window_name: tests
    panes:
      - npm test -- --watch
```

### Full-Stack Application

```yaml
windows:
  - window_name: backend
    start_directory: ./backend
    panes:
      - claude --dangerously-skip-permissions
      - cargo run
  - window_name: frontend
    start_directory: ./frontend
    panes:
      - claude --dangerously-skip-permissions
      - npm run dev
  - window_name: database
    panes:
      - docker-compose up db
```

### Monitoring Setup

```yaml
windows:
  - window_name: logs
    layout: even-vertical
    panes:
      - tail -f app.log
      - tail -f error.log
      - htop
```

## Troubleshooting

1. **Template Not Found**: Ensure the template file exists in `~/.scripton/yesman/templates/`
1. **Variable Not Substituted**: Check that you're using the correct syntax: `{{ variable_name }}`
1. **Commands Not Running**: Verify that commands are executable and dependencies are installed
1. **Session Already Exists**: Use `yesman down` to remove existing sessions before recreating

## Advanced Features

### Conditional Window Creation

While not directly supported in the template syntax, you can use shell scripting in `before_script` to conditionally
modify the environment:

```yaml
before_script: |
  if [ -f "docker-compose.yml" ]; then
    docker-compose up -d
  fi
```

### Dynamic Pane Commands

Use environment variables and shell expansion:

```yaml
panes:
  - shell_command: |
      PROJECT_TYPE=$(cat package.json | jq -r .type)
      if [ "$PROJECT_TYPE" = "module" ]; then
        npm run build:watch
      else
        npm run dev
      fi
```

This documentation provides a comprehensive guide to using Yesman-Claude templates effectively for creating reproducible
development environments.
