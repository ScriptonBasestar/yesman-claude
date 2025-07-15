# Yesman-Claude API Reference

This document provides comprehensive API documentation for Yesman-Claude's dashboard system and automation components.

## 📚 Table of Contents

1. [Renderer API](#renderer-api)
1. [Theme System API](#theme-system-api)
1. [Keyboard Navigation API](#keyboard-navigation-api)
1. [Performance Optimizer API](#performance-optimizer-api)
1. [Dashboard Launcher API](#dashboard-launcher-api)
1. [WebSocket Protocol](#websocket-protocol)
1. [REST API Endpoints](#rest-api-endpoints)

## 🎨 Renderer API

The renderer system provides unified rendering across TUI, Web, and Tauri interfaces.

### RendererFactory

Central factory for creating renderer instances.

```python
from libs.dashboard.renderers import RendererFactory, RenderFormat

factory = RendererFactory()

# Create specific renderer
tui_renderer = factory.create_renderer(RenderFormat.TUI)
web_renderer = factory.create_renderer(RenderFormat.WEB)
tauri_renderer = factory.create_renderer(RenderFormat.TAURI)

# Create with custom theme
renderer = factory.create_renderer(
    RenderFormat.TUI, 
    theme={"primary": "#ff0000"}
)

# Batch rendering across all formats
results = factory.render_all_formats(
    WidgetType.SESSION_BROWSER, 
    session_data
)
```

### Base Renderer

All renderers inherit from the base renderer class.

```python
class BaseRenderer:
    def render_widget(self, widget_type: WidgetType, data: Any) -> Dict[str, Any]:
        """Render a widget with given data"""
        pass
    
    def apply_theme(self, theme: Dict[str, Any]) -> None:
        """Apply theme to renderer"""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Get renderer capabilities"""
        pass
```

### Widget Types

Available widget types for rendering:

```python
from libs.dashboard.renderers import WidgetType

# Available widget types
WidgetType.SESSION_BROWSER    # Session list/grid view
WidgetType.PROJECT_HEALTH     # Health indicators
WidgetType.ACTIVITY_MONITOR   # Activity tracking
WidgetType.LOG_VIEWER         # Log display
WidgetType.PERFORMANCE_CHART  # Performance graphs
```

### Data Models

Standard data models for widgets:

```python
from libs.dashboard.renderers.widget_models import (
    SessionData, HealthData, ActivityData, LogData
)

# Session data
session = SessionData(
    name="my-session",
    status=SessionStatus.ACTIVE,
    uptime=3600,
    windows=3,
    last_activity=datetime.now(),
    cpu_usage=15.5,
    memory_usage=256.7
)

# Health data
health = HealthData(
    overall_score=85,
    overall_level=HealthLevel.GOOD,
    categories={
        "build": 90,
        "tests": 80,
        "security": 75,
        "performance": 85
    },
    last_updated=datetime.now()
)

# Activity data
activity = ActivityData(
    session_name="my-session",
    timestamp=datetime.now(),
    activity_type=ActivityType.COMMAND,
    level=ActivityLevel.HIGH,
    details={"command": "npm run build"}
)
```

## 🎨 Theme System API

### ThemeManager

Central theme management system.

```python
from libs.dashboard import get_theme_manager, ThemeMode

theme_manager = get_theme_manager()

# Get all available themes
themes = theme_manager.get_all_themes()

# Switch themes
theme_manager.set_theme("default_dark")
theme_manager.set_mode(ThemeMode.DARK)

# Get current theme
current = theme_manager.current_theme

# Save custom theme
theme_manager.save_theme("my_theme", custom_theme)

# Export theme data
css = theme_manager.export_css()
rich_theme = theme_manager.export_rich_theme()
textual_css = theme_manager.export_textual_css()
```

### Theme Model

Theme data structure:

```python
from libs.dashboard.theme_system import Theme, ColorPalette, Typography, Spacing

theme = Theme(
    name="Custom Theme",
    mode=ThemeMode.CUSTOM,
    colors=ColorPalette(
        primary="#3498db",
        secondary="#2ecc71",
        background="#2c3e50",
        surface="#34495e",
        text="#ecf0f1",
        text_secondary="#bdc3c7",
        success="#2ecc71",
        warning="#f39c12",
        error="#e74c3c",
        info="#3498db"
    ),
    typography=Typography(
        primary_font="JetBrains Mono",
        secondary_font="Inter",
        size_small="12px",
        size_normal="14px",
        size_large="16px",
        size_extra_large="18px",
        weight_normal="400",
        weight_bold="700"
    ),
    spacing=Spacing(
        small="4px",
        medium="8px",
        large="16px",
        extra_large="24px"
    )
)
```

### System Theme Detection

Automatic system theme detection:

```python
from libs.dashboard.theme_system import SystemThemeDetector

# Detect system theme
system_theme = SystemThemeDetector.get_system_theme()

# Platform-specific detection
if platform.system() == "Darwin":
    # macOS theme detection
    theme = SystemThemeDetector._get_macos_theme()
elif platform.system() == "Windows":
    # Windows theme detection  
    theme = SystemThemeDetector._get_windows_theme()
else:
    # Linux theme detection
    theme = SystemThemeDetector._get_linux_theme()
```

## ⌨️ Keyboard Navigation API

### KeyboardNavigationManager

Central keyboard navigation system.

```python
from libs.dashboard import get_keyboard_manager
from libs.dashboard.keyboard_navigation import KeyModifier, NavigationContext

keyboard_manager = get_keyboard_manager()

# Register action
def my_action():
    print("Action triggered!")

keyboard_manager.register_action("my_action", my_action)

# Register key binding
keyboard_manager.register_binding(
    key="t",
    modifiers=[KeyModifier.CTRL],
    action="my_action",
    description="Test action"
)

# Handle key events
handled = keyboard_manager.handle_key_event("t", [KeyModifier.CTRL])

# Context management
keyboard_manager.set_context(NavigationContext.DASHBOARD)
keyboard_manager.push_context(NavigationContext.SESSION_BROWSER)
keyboard_manager.pop_context()
```

### Focus Management

Managing focusable elements:

```python
# Add focusable elements
keyboard_manager.add_focusable_element(
    element_id="button1",
    element_type="button",
    tab_order=0
)

# Navigate focus
keyboard_manager.focus_next()
keyboard_manager.focus_previous()
keyboard_manager.focus_element("button1")

# Get focus state
focused = keyboard_manager.get_focused_element()
focusable = keyboard_manager.focusable_elements
```

### Key Bindings

Key binding management:

```python
from libs.dashboard.keyboard_navigation import KeyBinding

# Create key binding
binding = KeyBinding(
    key="s",
    modifiers=[KeyModifier.CTRL, KeyModifier.SHIFT],
    action="save_session",
    description="Save current session",
    context=NavigationContext.SESSION_BROWSER
)

# Register binding
keyboard_manager.register_binding_object(binding)

# Get bindings by context
bindings = keyboard_manager.get_bindings_for_context(
    NavigationContext.DASHBOARD
)

# Remove binding
keyboard_manager.remove_binding("s", [KeyModifier.CTRL])
```

## ⚡ Performance Optimizer API

### PerformanceOptimizer

Main performance optimization system.

```python
from libs.dashboard import get_performance_optimizer
from libs.dashboard.performance_optimizer import OptimizationLevel

optimizer = get_performance_optimizer()

# Set optimization level
optimizer.set_optimization_level(OptimizationLevel.HIGH)

# Start/stop monitoring
optimizer.start_monitoring()
optimizer.stop_monitoring()

# Get performance metrics
metrics = optimizer.get_current_metrics()
report = optimizer.get_performance_report()

# Performance profiling
profiler = optimizer.profiler

with profiler.measure("operation_name"):
    # Your code here
    pass

# Get profiling stats
stats = profiler.get_stats("operation_name")
all_stats = profiler.get_all_stats()
```

### AsyncPerformanceOptimizer

Asynchronous performance optimizer for async environments.

```python
from libs.dashboard.performance_optimizer import AsyncPerformanceOptimizer

async_optimizer = AsyncPerformanceOptimizer(monitoring_interval=1.0)

# Start async monitoring
await async_optimizer.start_monitoring()

# Get async performance report
report = await async_optimizer.get_performance_report()

# Stop monitoring
await async_optimizer.stop_monitoring()
```

### Performance Metrics

Performance data structure:

```python
from libs.dashboard.performance_optimizer import PerformanceMetrics

metrics = PerformanceMetrics(
    cpu_usage=15.5,
    memory_usage=256.7,
    memory_percent=12.3,
    render_time=0.032,
    response_time=0.015,
    cache_hit_rate=0.85,
    active_connections=5,
    queue_size=0
)

# Metric analysis
is_healthy = metrics.cpu_usage < 80.0
needs_optimization = metrics.render_time > 0.05
```

## 🚀 Dashboard Launcher API

### DashboardLauncher

Interface detection and management.

```python
from libs.dashboard import DashboardLauncher

launcher = DashboardLauncher()

# Detect best interface
best_interface = launcher.detect_best_interface()

# Get interface information
interfaces = launcher.get_available_interfaces()
interface_info = launcher.get_interface_info("tui")

# Check system requirements
requirements = launcher.check_system_requirements()

# Install dependencies
success = launcher.install_dependencies("tauri")
```

### Interface Information

Interface data structure:

```python
from libs.dashboard.dashboard_launcher import InterfaceInfo

interface_info = InterfaceInfo(
    name="Terminal User Interface",
    description="Rich-based terminal dashboard",
    requirements=["rich", "python"],
    available=True,
    reason=None,
    priority=2
)
```

## 🌐 WebSocket Protocol

Real-time communication protocol for web interface.

### Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function(event) {
    console.log('Connected to dashboard');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleDashboardUpdate(data);
};
```

### Message Types

#### Session Update

```json
{
    "type": "session_update",
    "data": {
        "session_name": "my-session",
        "status": "active",
        "uptime": 3600,
        "windows": 3,
        "cpu_usage": 15.5,
        "memory_usage": 256.7
    }
}
```

#### Health Update

```json
{
    "type": "health_update",
    "data": {
        "overall_score": 85,
        "overall_level": "good",
        "categories": {
            "build": 90,
            "tests": 80,
            "security": 75
        }
    }
}
```

#### Activity Update

```json
{
    "type": "activity_update",
    "data": {
        "session_name": "my-session",
        "timestamp": "2025-07-10T12:00:00Z",
        "activity_type": "command",
        "level": "high",
        "details": {
            "command": "npm run build"
        }
    }
}
```

### Client Commands

Send commands to dashboard:

```javascript
// Request data refresh
ws.send(JSON.stringify({
    "type": "refresh",
    "target": "sessions"
}));

// Change theme
ws.send(JSON.stringify({
    "type": "theme_change",
    "theme": "dark"
}));

// Performance optimization
ws.send(JSON.stringify({
    "type": "optimization",
    "level": "high"
}));
```

## 🔌 REST API Endpoints

HTTP API for dashboard integration.

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

```http
Authorization: Bearer <token>
```

### Sessions

#### Get All Sessions

```http
GET /sessions
```

Response:

```json
{
    "sessions": [
        {
            "name": "my-session",
            "status": "active",
            "uptime": 3600,
            "windows": 3,
            "cpu_usage": 15.5,
            "memory_usage": 256.7
        }
    ]
}
```

#### Get Session Details

```http
GET /sessions/{session_name}
```

#### Create Session

```http
POST /sessions
Content-Type: application/json

{
    "name": "new-session",
    "template": "django",
    "config": {
        "start_directory": "/path/to/project"
    }
}
```

#### Delete Session

```http
DELETE /sessions/{session_name}
```

### Health Monitoring

#### Get Health Status

```http
GET /health
```

Response:

```json
{
    "overall_score": 85,
    "overall_level": "good",
    "categories": {
        "build": 90,
        "tests": 80,
        "security": 75,
        "performance": 85,
        "dependencies": 88,
        "git": 92,
        "documentation": 70,
        "code_quality": 82
    },
    "last_updated": "2025-07-10T12:00:00Z"
}
```

#### Get Health History

```http
GET /health/history?days=7
```

### Performance

#### Get Performance Metrics

```http
GET /performance/metrics
```

Response:

```json
{
    "cpu_usage": 15.5,
    "memory_usage": 256.7,
    "memory_percent": 12.3,
    "render_time": 0.032,
    "response_time": 0.015,
    "cache_hit_rate": 0.85,
    "timestamp": "2025-07-10T12:00:00Z"
}
```

#### Set Optimization Level

```http
POST /performance/optimization
Content-Type: application/json

{
    "level": "high"
}
```

### Themes

#### Get Available Themes

```http
GET /themes
```

#### Get Current Theme

```http
GET /themes/current
```

#### Set Theme

```http
POST /themes/current
Content-Type: application/json

{
    "theme": "dark"
}
```

### Configuration

#### Get Configuration

```http
GET /config
```

#### Update Configuration

```http
PUT /config
Content-Type: application/json

{
    "dashboard": {
        "update_interval": 1.0,
        "theme": "auto"
    },
    "performance": {
        "optimization_level": "medium"
    }
}
```

## 🔧 Error Handling

### API Errors

Standard error response format:

```json
{
    "error": {
        "code": "INVALID_SESSION",
        "message": "Session 'invalid-name' not found",
        "details": {
            "session_name": "invalid-name",
            "available_sessions": ["session1", "session2"]
        }
    }
}
```

### Error Codes

| Code                  | Description                     |
| --------------------- | ------------------------------- |
| `INVALID_SESSION`     | Session not found               |
| `PERMISSION_DENIED`   | Insufficient permissions        |
| `INVALID_CONFIG`      | Invalid configuration           |
| `THEME_NOT_FOUND`     | Theme not available             |
| `OPTIMIZATION_FAILED` | Performance optimization failed |
| `WEBSOCKET_ERROR`     | WebSocket connection error      |

## 📊 Usage Examples

### Basic Dashboard Integration

```python
from libs.dashboard import (
    DashboardLauncher, get_theme_manager, get_keyboard_manager
)

# Create dashboard
launcher = DashboardLauncher()
interface = launcher.detect_best_interface()

# Configure theme
theme_manager = get_theme_manager()
theme_manager.set_mode(ThemeMode.DARK)

# Setup keyboard shortcuts
keyboard_manager = get_keyboard_manager()
keyboard_manager.register_action("refresh", lambda: print("Refreshing..."))
keyboard_manager.register_binding("r", [], "refresh", "Refresh data")

print(f"Best interface: {interface}")
```

### Custom Renderer

```python
from libs.dashboard.renderers import BaseRenderer, RenderFormat

class CustomRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()
        self.format = RenderFormat.CUSTOM
    
    def render_widget(self, widget_type, data):
        # Custom rendering logic
        return {
            "content": f"Custom render of {widget_type}",
            "data": data
        }
    
    def apply_theme(self, theme):
        # Apply theme to custom renderer
        self.theme = theme

# Register custom renderer
from libs.dashboard.renderers import RendererFactory
factory = RendererFactory()
factory.register_renderer("custom", CustomRenderer)
```

### Performance Monitoring

```python
from libs.dashboard import get_performance_optimizer

optimizer = get_performance_optimizer()

# Monitor performance
optimizer.start_monitoring()

# Simulate work
import time
with optimizer.profiler.measure("heavy_operation"):
    time.sleep(1)

# Get results
stats = optimizer.profiler.get_stats("heavy_operation")
print(f"Operation took: {stats['avg']:.3f}s")

optimizer.stop_monitoring()
```

______________________________________________________________________

For more examples and advanced usage, see the [User Guide](user-guide.md) and [examples directory](../examples/).
