# Yesman-Claude Configuration Guide

This guide covers all configuration options for Yesman-Claude, from basic setup to advanced customization.

## 📚 Table of Contents

1. [Configuration Hierarchy](#configuration-hierarchy)
1. [Main Configuration Files](#main-configuration-files)
1. [Environment Variables](#environment-variables)
1. [Dashboard Configuration](#dashboard-configuration)
1. [Theme Configuration](#theme-configuration)
1. [Performance Tuning](#performance-tuning)
1. [AI Learning Configuration](#ai-learning-configuration)
1. [Automation Configuration](#automation-configuration)
1. [Logging Configuration](#logging-configuration)
1. [Troubleshooting](#troubleshooting)

## 🏗️ Configuration Hierarchy

Yesman-Claude uses a hierarchical configuration system that merges settings from multiple sources:

```
1. Default settings (built-in)
2. Global configuration (~/.scripton/yesman/yesman.yaml)
3. Global projects (~/.scripton/yesman/projects.yaml)
4. Local overrides (./.scripton/yesman/yesman.yaml)
5. Environment variables
6. Command-line arguments
```

### Configuration Merge Modes

- **merge** (default): Local configs override global settings
- **isolated**: Use only local configs, ignore global settings
- **local**: Deprecated, use `isolated` instead

## 📄 Main Configuration Files

### Global Configuration

**File**: `~/.scripton/yesman/yesman.yaml`

```yaml
# Logging configuration
logging:
  level: INFO
  file: ~/.scripton/yesman/logs/yesman.log
  max_size: 10MB
  backup_count: 5
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Dashboard settings
dashboard:
  default_interface: auto  # auto, tui, web, tauri
  update_interval: 1.0
  theme: auto  # auto, light, dark, or theme name
  cache_size: 100
  animations: true

# Performance settings
performance:
  optimization_level: medium  # none, low, medium, high, aggressive
  monitoring_enabled: true
  profiling_enabled: false
  cache_ttl: 300

# AI learning settings
ai:
  learning_enabled: true
  confidence_threshold: 0.7
  response_timeout: 30
  training_data_size: 1000
  pattern_analysis: true

# Automation settings
automation:
  enabled: true
  monitoring_interval: 5.0
  context_detection: true
  workflow_chains: true

# Security settings
security:
  enable_auth: false
  api_key: null
  cors_enabled: true
  trusted_hosts: []

# Default choices for interactive prompts
default_choices:
  trust_prompts: true
  numbered_selections: 1
  yes_no_prompts: "y"
```

### Projects Configuration

**File**: `~/.scripton/yesman/projects.yaml`

```yaml
# Configuration merge mode
merge_mode: merge  # merge, isolated

# Session definitions
sessions:
  my_django_app:
    template_name: django
    override:
      session_name: django-dev
      start_directory: ~/projects/my-django-app
      environment:
        DEBUG: "1"
        DATABASE_URL: "sqlite:///db.sqlite3"
    
  my_react_app:
    template_name: react
    override:
      session_name: react-dev
      start_directory: ~/projects/my-react-app
      before_script: |
        if [ ! -d "node_modules" ]; then
          npm install
        fi
    
  custom_session:
    # Inline session definition (no template)
    session_name: custom-dev
    start_directory: ~/projects/custom
    windows:
      - window_name: main
        layout: even-horizontal
        panes:
          - shell_command: |
              echo "Starting development environment..."
              code .
          - shell_command: |
              echo "Starting server..."
              python -m http.server 8000
```

### Template Configuration

**File**: `~/.scripton/yesman/templates/{template_name}.yaml`

```yaml
# Django template example
session_name: "{{ session_name }}"
start_directory: "{{ start_directory }}"
before_script: |
  # Setup virtual environment if needed
  if [ ! -d "venv" ]; then
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
  else
    source venv/bin/activate
  fi

windows:
  - window_name: django server
    layout: even-horizontal
    panes:
      - claude --dangerously-skip-permissions
      - shell_command: |
          echo "Starting Django development server..."
          python manage.py runserver {{ port | default("8000") }}
      - htop

  - window_name: testing
    panes:
      - shell_command: |
          echo "Test environment ready"
          python manage.py shell

environment:
  DJANGO_DEBUG: "{{ debug | default('1') }}"
  DATABASE_URL: "{{ database_url | default('sqlite:///db.sqlite3') }}"
```

## 🌍 Environment Variables

Override configuration settings using environment variables:

### Core Settings

```bash
# Logging
export YESMAN_LOG_LEVEL=DEBUG
export YESMAN_LOG_FILE=~/.scripton/yesman/logs/debug.log

# Dashboard
export YESMAN_DASHBOARD_INTERFACE=tui
export YESMAN_DASHBOARD_THEME=dark
export YESMAN_DASHBOARD_UPDATE_INTERVAL=2.0

# Performance
export YESMAN_OPTIMIZATION_LEVEL=high
export YESMAN_MONITORING_ENABLED=true

# AI Learning
export YESMAN_AI_ENABLED=true
export YESMAN_AI_CONFIDENCE=0.8
export YESMAN_AI_TIMEOUT=60

# Automation
export YESMAN_AUTOMATION_ENABLED=true
export YESMAN_AUTOMATION_INTERVAL=10.0
```

### Debug Settings

```bash
# Enable debug mode
export YESMAN_DEBUG=1
export YESMAN_VERBOSE=1

# Performance profiling
export YESMAN_PROFILING=1
export YESMAN_PROFILE_OUTPUT=~/.scripton/yesman/profiles/

# Development mode
export YESMAN_DEV_MODE=1
export YESMAN_DEV_RELOAD=1
```

### Security Settings

```bash
# API authentication
export YESMAN_API_KEY=your-secret-key
export YESMAN_AUTH_ENABLED=true

# CORS configuration
export YESMAN_CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
export YESMAN_TRUSTED_HOSTS="localhost,127.0.0.1"
```

## 📊 Dashboard Configuration

### Interface Selection

Configure which dashboard interface to use by default:

```yaml
dashboard:
  default_interface: auto  # Options: auto, tui, web, tauri
  
  # Interface-specific settings
  tui:
    color_depth: 256
    mouse_enabled: true
    scroll_buffer: 1000
    
  web:
    port: 8000
    host: "0.0.0.0"
    auto_open: false
    cors_enabled: true
    
  tauri:
    development_mode: false
    window_size: [1200, 800]
    window_position: center
    always_on_top: false
```

### Update Settings

Control how frequently the dashboard updates:

```yaml
dashboard:
  update_interval: 1.0  # Seconds between updates
  batch_size: 50       # Max items per batch update
  lazy_loading: true   # Enable lazy loading for large datasets
  
  # Performance thresholds
  performance_thresholds:
    max_update_time: 0.1    # Max time per update (seconds)
    max_memory_usage: 500   # Max memory usage (MB)
    max_cpu_usage: 50       # Max CPU usage (%)
```

### Cache Configuration

Configure dashboard caching:

```yaml
dashboard:
  cache:
    enabled: true
    size: 100           # Max cached items
    ttl: 300           # Time to live (seconds)
    compress: true     # Enable compression
    
    # Cache policies
    policies:
      sessions: 60      # Cache session data for 60s
      health: 30        # Cache health data for 30s
      activity: 10      # Cache activity data for 10s
```

## 🎨 Theme Configuration

### Built-in Themes

Use predefined themes:

```yaml
dashboard:
  theme: default_dark  # Options: default_light, default_dark, high_contrast, etc.
  
  # Theme fallbacks
  theme_fallbacks:
    - default_dark
    - default_light
```

### Custom Themes

Create custom themes:

```yaml
# ~/.scripton/yesman/themes/my_theme.yaml
name: "My Custom Theme"
mode: custom

colors:
  primary: "#3498db"
  secondary: "#2ecc71"
  background: "#2c3e50"
  surface: "#34495e"
  text: "#ecf0f1"
  text_secondary: "#bdc3c7"
  success: "#2ecc71"
  warning: "#f39c12"
  error: "#e74c3c"
  info: "#3498db"

typography:
  primary_font: "JetBrains Mono"
  secondary_font: "Inter"
  size_small: "12px"
  size_normal: "14px"
  size_large: "16px"
  size_extra_large: "18px"
  weight_normal: "400"
  weight_bold: "700"

spacing:
  small: "4px"
  medium: "8px"
  large: "16px"
  extra_large: "24px"

effects:
  border_radius: "4px"
  shadow: "0 2px 4px rgba(0,0,0,0.1)"
  transition: "0.2s ease"
```

### Automatic Theme Detection

Configure automatic theme detection:

```yaml
dashboard:
  theme: auto
  
  # Auto-detection settings
  theme_detection:
    method: system     # system, time, manual
    light_hours: [6, 18]  # Light theme between 6 AM - 6 PM
    dark_hours: [18, 6]   # Dark theme between 6 PM - 6 AM
    
    # System integration
    follow_system: true
    update_interval: 300  # Check every 5 minutes
```

## ⚡ Performance Tuning

### Optimization Levels

Configure performance optimization:

```yaml
performance:
  optimization_level: medium  # none, low, medium, high, aggressive
  
  # Level-specific settings
  optimizations:
    none:
      animations: true
      transitions: true
      shadows: true
      
    low:
      animations: true
      transitions: true
      shadows: false
      
    medium:
      animations: true
      transitions: false
      shadows: false
      batch_updates: true
      
    high:
      animations: false
      transitions: false
      shadows: false
      batch_updates: true
      lazy_rendering: true
      
    aggressive:
      animations: false
      transitions: false
      shadows: false
      batch_updates: true
      lazy_rendering: true
      minimal_ui: true
```

### Memory Management

Configure memory usage:

```yaml
performance:
  memory:
    max_usage: 512      # Max memory usage in MB
    cleanup_interval: 300  # Cleanup every 5 minutes
    cache_limit: 100    # Max cached items
    
    # Garbage collection
    gc_enabled: true
    gc_threshold: [700, 10, 10]
    gc_interval: 60
```

### Monitoring Settings

Configure performance monitoring:

```yaml
performance:
  monitoring:
    enabled: true
    interval: 1.0        # Monitoring interval in seconds
    metrics_retention: 3600  # Keep metrics for 1 hour
    
    # Thresholds for alerts
    thresholds:
      cpu_warning: 70    # CPU usage warning at 70%
      cpu_critical: 90   # CPU usage critical at 90%
      memory_warning: 80 # Memory warning at 80%
      memory_critical: 95 # Memory critical at 95%
      
    # Profiling
    profiling:
      enabled: false
      sample_rate: 0.1   # Profile 10% of operations
      output_dir: ~/.scripton/yesman/profiles/
```

## 🤖 AI Learning Configuration

### Learning Settings

Configure AI learning behavior:

```yaml
ai:
  learning_enabled: true
  confidence_threshold: 0.7  # Minimum confidence for auto-response
  response_timeout: 30       # Timeout for responses in seconds
  
  # Training data
  training:
    max_samples: 1000        # Max training samples to keep
    min_samples: 10          # Min samples before learning
    validation_split: 0.2    # 20% for validation
    
  # Pattern analysis
  patterns:
    enabled: true
    min_pattern_count: 5     # Min occurrences to recognize pattern
    similarity_threshold: 0.8 # Pattern similarity threshold
    
  # Response generation
  responses:
    use_learned: true        # Use learned responses
    fallback_to_default: true # Fall back to defaults
    log_decisions: true      # Log AI decisions
```

### Model Configuration

Configure AI model settings:

```yaml
ai:
  model:
    type: pattern_matching   # pattern_matching, neural_network
    
    # Pattern matching settings
    pattern_matching:
      fuzzy_matching: true
      edit_distance_threshold: 2
      case_sensitive: false
      
    # Neural network settings (if available)
    neural_network:
      hidden_layers: [64, 32]
      activation: relu
      learning_rate: 0.001
      epochs: 100
```

## 🔄 Automation Configuration

### Context Detection

Configure context-aware automation:

```yaml
automation:
  enabled: true
  monitoring_interval: 5.0  # Check every 5 seconds
  
  # Context types to monitor
  contexts:
    git_commits: true
    test_failures: true
    build_events: true
    file_changes: true
    error_patterns: true
    performance_issues: true
    dependency_changes: true
    todo_progress: true
    
  # Detection thresholds
  thresholds:
    file_change_threshold: 3      # Min files changed to trigger
    error_count_threshold: 5      # Min errors to trigger
    performance_degradation: 20   # % performance drop to trigger
```

### Workflow Configuration

Define automation workflows:

```yaml
# ~/.scripton/yesman/automation.yaml
workflows:
  test_and_build:
    name: "Test and Build Pipeline"
    triggers:
      - git_commit
      - file_changes
    conditions:
      - file_patterns: ["src/**/*.py", "tests/**/*.py"]
      - branch: ["main", "develop"]
    steps:
      - name: run_tests
        command: python -m pytest
        timeout: 300
        retry_count: 3
        
      - name: build_project
        command: python setup.py build
        timeout: 600
        depends_on: [run_tests]
        
      - name: notify
        type: notification
        message: "Build completed successfully"
        depends_on: [build_project]
        
  dependency_update:
    name: "Dependency Update Handler"
    triggers:
      - dependency_changes
    conditions:
      - files: ["requirements.txt", "package.json", "Pipfile"]
    steps:
      - name: install_deps
        command: pip install -r requirements.txt
        timeout: 300
        
      - name: security_scan
        command: safety check
        timeout: 60
        continue_on_error: true
        
      - name: update_docs
        command: python -m sphinx docs/ docs/_build/
        timeout: 120
```

## 📝 Logging Configuration

### Log Levels and Output

Configure logging behavior:

```yaml
logging:
  level: INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: ~/.scripton/yesman/logs/yesman.log
  max_size: 10MB          # Max log file size
  backup_count: 5         # Number of backup files
  
  # Log format
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  date_format: '%Y-%m-%d %H:%M:%S'
  
  # Component-specific logging
  components:
    dashboard: INFO
    automation: DEBUG
    ai_learning: INFO
    performance: WARNING
    
  # Async logging
  async_logging:
    enabled: true
    queue_size: 1000
    batch_size: 100
    flush_interval: 5.0
```

### Log Rotation

Configure log rotation:

```yaml
logging:
  rotation:
    enabled: true
    when: midnight         # midnight, hourly, daily, weekly
    interval: 1           # Rotate every 1 day
    backup_count: 7       # Keep 7 days of logs
    compress: true        # Compress old logs
    
  # Cleanup old logs
  cleanup:
    enabled: true
    max_age_days: 30      # Delete logs older than 30 days
    cleanup_interval: 86400  # Check daily
```

### Structured Logging

Enable structured logging:

```yaml
logging:
  structured: true
  format: json            # json, logfmt, text
  
  # Additional fields
  extra_fields:
    service: yesman-claude
    version: "1.0.0"
    environment: development
    
  # Sensitive data filtering
  sensitive_patterns:
    - "password"
    - "secret"
    - "token"
    - "key"
```

## 🔧 Troubleshooting

### Common Configuration Issues

#### Invalid YAML Syntax

**Problem**: Configuration file has syntax errors

**Solution**: Validate YAML syntax

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('~/.scripton/yesman/yesman.yaml'))"

# Use online YAML validator
# Or install yamllint
pip install yamllint
yamllint ~/.scripton/yesman/yesman.yaml
```

#### Permission Issues

**Problem**: Cannot read/write configuration files

**Solution**: Fix permissions

```bash
# Fix directory permissions
chmod 755 ~/.scripton/yesman
chmod 644 ~/.scripton/yesman/*.yaml

# Check ownership
ls -la ~/.scripton/yesman/
```

#### Environment Variable Conflicts

**Problem**: Environment variables override expected config

**Solution**: Check environment variables

```bash
# List all YESMAN environment variables
env | grep YESMAN

# Unset problematic variables
unset YESMAN_DEBUG
```

### Configuration Validation

Validate your configuration:

```bash
# Validate all configuration
uv run ./yesman.py config --validate

# Check specific configuration file
uv run ./yesman.py config --validate ~/.scripton/yesman/yesman.yaml

# Export current effective configuration
uv run ./yesman.py config --export > current_config.yaml
```

### Reset Configuration

Reset to defaults:

```bash
# Reset to default configuration
uv run ./yesman.py config --reset

# Reset specific component
uv run ./yesman.py config --reset dashboard

# Backup current config before reset
cp ~/.scripton/yesman/yesman.yaml ~/.scripton/yesman/yesman.yaml.backup
```

### Debug Configuration Loading

Debug configuration loading issues:

```bash
# Enable debug logging for config
export YESMAN_DEBUG=1
uv run ./yesman.py --help

# Check configuration merge
uv run ./yesman.py config --show-merge

# Trace configuration loading
uv run ./yesman.py config --trace-loading
```

______________________________________________________________________

For more advanced configuration examples, see the [examples directory](../examples/) and
[API Reference](api-reference.md).
