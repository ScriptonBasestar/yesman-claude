# Features

Yesman-Claude is a CLI automation tool that manages tmux sessions and automates interactions with Claude Code. This
document outlines all implemented features and capabilities.

## 🖥️ CLI Commands

### Session Management

- **`./yesman.py ls`** - List available templates and projects
- **`./yesman.py show`** - Show running tmux sessions status
- **`./yesman.py setup`** - Create all tmux sessions from projects.yaml configuration
- **`./yesman.py teardown`** - Stop and remove all sessions defined in projects.yaml
- **`./yesman.py enter [session_name]`** - Attach to a tmux session (interactive selection if no name provided)

### Dashboard & Monitoring

- **`./yesman.py dashboard`** - Launch TUI dashboard for real-time session monitoring

## 📊 Dashboard & Monitoring

### Terminal Compatibility

- **Smart Terminal Detection** - Automatically detects terminal capabilities and sets appropriate environment variables
- **Universal Compatibility** - Works across different terminal types (xterm, tmux, screen, etc.)
- **Fallback Safe Mode** - Provides simple text-based interface when TUI mode is incompatible
- **Environment Auto-Fix** - Automatically configures TERM and FORCE_COLOR variables for optimal display

### Real-Time Session Monitoring

- **Live Session Status** - Real-time display of all tmux sessions, windows, and panes
- **Session Statistics** - Shows total sessions, active sessions, and running Claude instances
- **Interactive Controls** - Start/stop Claude automation controllers directly from dashboard
- **Performance-Optimized Updates** - Smart caching system reduces tmux server load by 70%
- **Session Tree Browser** - Interactive file-browser style interface for exploring sessions
- **Status Icons** - Visual indicators (🟢 running, ⚠️ error, 🔄 loading) for quick status assessment
- **Pane Details View** - Shows idle time, current task, and resource usage per pane
- **Click-to-Attach** - Direct tmux session attachment from dashboard interface

## 🤖 Claude Code Automation

### Intelligent Claude Detection

- **Multi-Pattern Recognition** - Detects Claude Code using command names, content patterns, and process information
- **Enhanced Detection Patterns** - Recognizes "Welcome to Claude Code", "? for shortcuts", and other Claude-specific
  indicators
- **Reliable Process Monitoring** - Continuously monitors pane content to maintain automation state

### Auto-Response System

- **Trust Prompt Automation** - Automatically responds "1" to Claude Code trust prompts
- **Selection Menu Handling** - Auto-selects first option in numbered choice menus with automatic advancement
- **Yes/No Decision Making** - Responds "yes" to confirmation prompts
- **Multi-line Selection Support** - Handles complex selection screens with line wrapping and ctrl+r expansion prompts
- **Response History Tracking** - Logs all automated responses for debugging and audit

### Advanced Controller Management

- **Thread-Safe Operation** - Claude managers run in separate threads with proper event loop handling
- **Auto-Start/Stop** - Controllers can be started and stopped dynamically from dashboard
- **Safe Claude Restart** - Automatically terminates existing Claude processes before restarting to prevent command
  injection
- **Session Recovery** - Re-initializes connections when sessions are recreated
- **Graceful Shutdown** - Properly terminates monitoring threads and event loops
- **Content Collection** - Automatically collects Claude Code interactions for pattern analysis and future improvement

## ⚙️ Configuration System

### Hierarchical Configuration

- **Global Settings** - `~/.yesman/yesman.yaml` for logging and default choices
- **Project Definitions** - `~/.yesman/projects.yaml` for session configurations
- **Template System** - `~/.yesman/templates/*.yaml` for reusable session templates
- **Local Overrides** - `./.yesman/*` for project-specific customizations

### Configuration Modes

- **Merge Mode** (default) - Local configs override global settings
- **Local Mode** - Use only local configurations, ignore global

### Smart Template Features

- **Dependency Optimization** - Smart pnpm/npm install that only runs when dependencies are outdated
- **Conditional Commands** - Templates can include shell logic for intelligent setup
- **Variable Substitution** - Dynamic configuration based on project context

## 🔧 System Management

### Logging & Debugging

- **Centralized Logging** - All components log to `~/tmp/logs/yesman/` with proper permissions
- **Component-Specific Logs** - Separate log files for dashboard, claude manager, and session management
- **Configurable Log Levels** - Control verbosity through configuration files
- **Auto-Directory Creation** - Log directories created automatically with correct permissions (755)

### Process Management

- **Session Lifecycle** - Complete tmux session creation, monitoring, and cleanup
- **Resource Cleanup** - Proper cleanup of threads, event loops, and file handles
- **Error Recovery** - Graceful handling of missing directories, failed sessions, and connection issues

### Development Tools

- **Interactive Selection** - User-friendly prompts for session and template selection
- **Status Reporting** - Clear feedback on operations and error states
- **Development Mode** - Easy installation with `make dev-install` or `uv` support

## 🚀 Performance Optimization

### Smart Session Caching

- **Intelligent Cache Management** - TTL-based caching with automatic invalidation on session changes
- **Reduced Server Load** - Minimizes tmux server queries from 2-second intervals to on-demand
- **Memory-Efficient Storage** - Optimized cache keys and memory management strategies
- **Mode-Aware Caching** - Different caching behaviors for CLI vs daemon operation modes
- **Cache Analytics** - Tracks hit/miss ratios, memory usage, and last update times

## 🛡️ Reliability Features

### Error Handling

- **Graceful Degradation** - Falls back to simple mode when TUI features fail
- **Connection Recovery** - Automatically reconnects to tmux sessions when possible
- **Input Validation** - Validates templates and configurations before execution
- **Safe Defaults** - Sensible fallback behavior when configurations are missing

### Cross-Platform Support

- **Terminal Independence** - Works across different terminal emulators and environments
- **Path Handling** - Proper handling of user paths and directory expansion
- **Permission Management** - Automatic setup of required file and directory permissions

### Debugging Support

- **Verbose Logging** - Detailed operation logs for troubleshooting
- **Status Indicators** - Clear visual feedback in dashboard and CLI
- **History Tracking** - Maintains history of automated actions for analysis
