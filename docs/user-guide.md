# Yesman-Claude User Guide

This comprehensive guide covers all aspects of using Yesman-Claude, from basic setup to advanced automation features.

## 📚 Table of Contents

1. [Quick Start](#quick-start)
1. [Dashboard Interfaces](#dashboard-interfaces)
1. [Session Management](#session-management)
1. [Keyboard Shortcuts](#keyboard-shortcuts)
1. [Theme Customization](#theme-customization)
1. [AI Learning System](#ai-learning-system)
1. [Performance Optimization](#performance-optimization)
1. [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd yesman-claude
   ```

1. **Install dependencies**:

   ```bash
   # Development installation (recommended)
   make dev-install

   # Or using uv (fastest)
   uv sync
   ```

1. **Create configuration**:

   ```bash
   mkdir -p ~/.scripton/yesman
   cp examples/global-yesman/* ~/.scripton/yesman/
   ```

1. **Test installation**:

   ```bash
   uv run ./yesman.py --help
   ```

### First Steps

1. **List available templates**:

   ```bash
   uv run ./yesman.py ls
   ```

1. **Create your first session**:

   ```bash
   uv run ./yesman.py up
   ```

1. **Open the dashboard**:

   ```bash
   uv run ./yesman.py dash
   ```

## 📊 Dashboard Interfaces

Yesman-Claude provides three dashboard interfaces, each optimized for different use cases.

### Terminal User Interface (TUI)

The TUI provides a rich terminal-based dashboard with live updates and full keyboard navigation.

**Launch TUI**:

```bash
uv run ./yesman.py dash tui
```

**Features**:

- Real-time session monitoring
- Activity heatmaps
- Project health indicators
- Keyboard-only navigation
- Low resource usage
- SSH-friendly

**Best for**: SSH sessions, headless servers, minimal environments

### Web Interface

The web interface provides a browser-based dashboard with REST API backend.

**Launch Web Interface**:

```bash
# Default port (8000)
uv run ./yesman.py dash web

# Custom port
uv run ./yesman.py dash web --port 3000

# Open browser automatically
uv run ./yesman.py dash web --open
```

**Features**:

- Cross-platform compatibility
- Remote access capability
- Rich interactive widgets
- WebSocket real-time updates
- Mobile-responsive design
- Team collaboration

**Best for**: Remote monitoring, team environments, mobile access

### Desktop Application (Tauri)

The desktop application provides a native experience with system integration.

**Launch Desktop App**:

```bash
# Development mode
uv run ./yesman.py dash tauri --dev

# Production mode
uv run ./yesman.py dash tauri
```

**Features**:

- Native performance
- System tray integration
- Native notifications
- File system access
- Offline capability
- OS-specific features

**Best for**: Daily development, best UX, desktop integration

## 🎮 Session Management

### Creating Sessions

Sessions are defined in individual YAML files under `~/.scripton/yesman/sessions/`:

```yaml
sessions:
  my_project:
    template_name: django
    override:
      session_name: my-django-app
      start_directory: ~/projects/my-app
```

**Commands**:

```bash
# Create all sessions
uv run ./yesman.py up

# Create specific session
uv run ./yesman.py up my_project

# Show running sessions
uv run ./yesman.py show

# Interactive session browser
uv run ./yesman.py browse
```

### Session Templates

Templates are reusable session configurations stored in `~/.scripton/yesman/templates/`.

**Example template** (`~/.scripton/yesman/templates/django.yaml`):

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
```

**Smart Templates** support conditional commands:

```yaml
panes:
  - shell_command: |
      if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
      fi
      npm run dev
```

### Session Lifecycle

```bash
# Create sessions
uv run ./yesman.py up

# Monitor sessions
uv run ./yesman.py status

# Enter specific session
uv run ./yesman.py enter my_project

# Tear down sessions
uv run ./yesman.py down
```

## ⌨️ Keyboard Shortcuts

### TUI Dashboard Shortcuts

| Key | Action | Context |
| ----------- | ---------------- | ---------- |
| `q` | Quit application | Global |
| `h` | Show help | Global |
| `r` | Refresh data | Global |
| `d` | Toggle dark mode | Global |
| `1-5` | Switch views | Global |
| `↑/↓` | Navigate items | Lists |
| `←/→` | Navigate panes | Horizontal |
| `Enter` | Select/Activate | Lists |
| `Tab` | Next focus | Forms |
| `Shift+Tab` | Previous focus | Forms |

### Navigation Contexts

Different contexts provide specialized keyboard shortcuts:

**Dashboard Context**:

- `s` - Session browser
- `h` - Health monitor
- `a` - Activity tracker
- `l` - Logs viewer
- `p` - Performance monitor

**Session Browser Context**:

- `c` - Create session
- `d` - Delete session
- `r` - Restart session
- `e` - Enter session

**Health Monitor Context**:

- `t` - Run tests
- `b` - Build project
- `g` - Git status

### Custom Shortcuts

Register custom keyboard shortcuts:

```python
from libs.dashboard import get_keyboard_manager

keyboard_manager = get_keyboard_manager()

def custom_action():
    print("Custom action triggered!")

keyboard_manager.register_action("custom", custom_action)
keyboard_manager.register_binding("c", [KeyModifier.CTRL], "custom", "Custom action")
```

## 🎨 Theme Customization

### Built-in Themes

Yesman-Claude includes several built-in themes:

- **Default Light**: Clean light theme
- **Default Dark**: Dark theme optimized for low light
- **High Contrast**: Accessibility-focused theme
- **Cyberpunk**: Futuristic neon theme
- **Ocean**: Blue-based calming theme
- **Forest**: Green nature-inspired theme

### Switching Themes

**Via Command Line**:

```bash
# List available themes
uv run ./yesman.py dash --theme-list

# Use specific theme
uv run ./yesman.py dash tui --theme dark

# Set system theme detection
uv run ./yesman.py dash tui --theme auto
```

**Via API**:

```python
from libs.dashboard import get_theme_manager

theme_manager = get_theme_manager()

# Switch to dark theme
theme_manager.set_mode(ThemeMode.DARK)

# List all themes
themes = theme_manager.get_all_themes()
```

### Creating Custom Themes

Create a custom theme file:

```python
# docs/examples/custom-theme.py
from libs.dashboard.theme_system import Theme, ThemeMode, ColorPalette, Typography, Spacing

custom_theme = Theme(
    name="My Custom Theme",
    mode=ThemeMode.CUSTOM,
    colors=ColorPalette(
        primary="#ff6b6b",
        secondary="#4ecdc4", 
        background="#2c3e50",
        surface="#34495e",
        text="#ecf0f1",
        text_secondary="#bdc3c7"
    ),
    typography=Typography(
        primary_font="JetBrains Mono",
        secondary_font="Inter",
        size_small="12px",
        size_normal="14px",
        size_large="16px"
    ),
    spacing=Spacing(
        small="4px",
        medium="8px", 
        large="16px",
        extra_large="24px"
    )
)

# Save theme
from libs.dashboard import get_theme_manager
theme_manager = get_theme_manager()
theme_manager.save_theme("my_custom", custom_theme)
```

### Theme Export

Export themes for other applications:

```python
# Export CSS variables
css = theme_manager.export_css()

# Export Rich theme
rich_theme = theme_manager.export_rich_theme()

# Export Textual CSS
textual_css = theme_manager.export_textual_css()
```

## 🤖 AI Learning System

The AI learning system automatically improves response accuracy over time by learning from user behavior patterns.

### Configuration

```bash
# View current AI status
uv run ./yesman.py ai status

# Configure confidence threshold
uv run ./yesman.py ai config --threshold 0.8

# Enable/disable learning
uv run ./yesman.py ai config --learning-enabled true

# Set response timeout
uv run ./yesman.py ai config --timeout 30
```

### Learning Analytics

```bash
# View response history
uv run ./yesman.py ai history

# Show learning statistics
uv run ./yesman.py ai stats

# Export learning data
uv run ./yesman.py ai export --format json
```

### Response Patterns

The AI system recognizes different prompt patterns:

- **Yes/No prompts**: Binary confirmation dialogs
- **Numbered selections**: Multiple choice menus (1, 2, 3...)
- **Binary choices**: Simple A/B decisions
- **Trust prompts**: Claude Code permission requests

### Manual Training

```bash
# Add training data
uv run ./yesman.py ai train --pattern "Continue?" --response "y"

# Import training data
uv run ./yesman.py ai import --file training_data.json

# Reset learning data
uv run ./yesman.py ai reset --confirm
```

## ⚡ Performance Optimization

### Optimization Levels

The performance optimizer provides 5 optimization levels:

1. **None**: No optimizations
1. **Low**: Basic optimizations
1. **Medium**: Balanced performance/features
1. **High**: Aggressive optimizations
1. **Aggressive**: Maximum performance

### Configuration

```bash
# View performance status
uv run ./yesman.py status --performance

# Set optimization level
uv run ./yesman.py config --optimization medium

# Enable performance monitoring
uv run ./yesman.py monitor --performance
```

### Manual Optimization

```python
from libs.dashboard import get_performance_optimizer

optimizer = get_performance_optimizer()

# Set optimization level
optimizer.set_optimization_level(OptimizationLevel.HIGH)

# Get performance report
report = optimizer.get_performance_report()

# Start monitoring
optimizer.start_monitoring()
```

### Performance Metrics

Monitor key performance indicators:

- **CPU Usage**: Process CPU utilization
- **Memory Usage**: RAM consumption
- **Render Time**: Dashboard render performance
- **Response Time**: System responsiveness
- **Cache Hit Rate**: Caching efficiency

## 🔧 Troubleshooting

### Common Issues

#### Dashboard Won't Start

**Problem**: Dashboard interface fails to launch

**Solutions**:

1. Check system requirements:

   ```bash
   uv run ./yesman.py dash --check-requirements
   ```

1. Install missing dependencies:

   ```bash
   uv run ./yesman.py dash --install-deps
   ```

1. Try alternative interface:

   ```bash
   uv run ./yesman.py dash tui  # Always works
   ```

#### Poor Performance

**Problem**: Dashboard is slow or unresponsive

**Solutions**:

1. Enable performance optimization:

   ```bash
   uv run ./yesman.py config --optimization high
   ```

1. Reduce update frequency:

   ```bash
   uv run ./yesman.py dash --interval 2.0
   ```

1. Clear cache:

   ```bash
   uv run ./yesman.py cache --clear
   ```

#### Theme Issues

**Problem**: Theme not applying correctly

**Solutions**:

1. Reset theme to default:

   ```bash
   uv run ./yesman.py dash --theme default
   ```

1. Clear theme cache:

   ```bash
   rm -rf ~/.scripton/yesman/cache/themes/
   ```

1. Check theme file syntax:

   ```bash
   uv run ./yesman.py theme --validate my_theme
   ```

#### AI Learning Problems

**Problem**: AI responses are inaccurate

**Solutions**:

1. Reset learning data:

   ```bash
   uv run ./yesman.py ai reset --confirm
   ```

1. Adjust confidence threshold:

   ```bash
   uv run ./yesman.py ai config --threshold 0.9
   ```

1. Add manual training data:

   ```bash
   uv run ./yesman.py ai train --interactive
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Enable debug mode
export YESMAN_DEBUG=1
uv run ./yesman.py dash tui

# View debug logs
tail -f ~/.scripton/yesman/logs/debug.log
```

### Getting Help

1. **Built-in help**:

   ```bash
   uv run ./yesman.py --help
   uv run ./yesman.py dash --help
   ```

1. **Check status**:

   ```bash
   uv run ./yesman.py status --verbose
   ```

1. **Report issues**: Create an issue with debug logs and system information

### System Information

Gather system information for bug reports:

```bash
# System diagnostics
uv run ./yesman.py diagnose --full

# Export configuration
uv run ./yesman.py config --export > config_backup.yaml
```

## 📖 Additional Resources

- [API Reference](api-reference.md)
- [Configuration Guide](configuration.md)
- [Examples Directory](../examples/)
- [Template Gallery](templates.md)
- [Contributing Guide](../CONTRIBUTING.md)

______________________________________________________________________

For more advanced usage and API documentation, see the [API Reference](api-reference.md).
