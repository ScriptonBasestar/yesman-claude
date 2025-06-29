"""UI widgets for dashboard"""

from textual.widgets import Static, Button, Tree as TextualTree, Select, Switch, RadioSet, RadioButton, RichLog
from textual.containers import Container, ScrollableContainer, Horizontal, Vertical
from textual.app import ComposeResult
from textual.message import Message
import logging
from pathlib import Path
import os
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from .models import SessionInfo, DashboardStats
from .claude_manager import ClaudeManager
from ..utils import ensure_log_directory, get_default_log_path


class ProjectPanel(Static):
    """Left panel showing tmux project status"""
    
    class SessionSelected(Message):
        """Message when a session is selected"""
        def __init__(self, session_info: 'SessionInfo') -> None:
            self.session_info = session_info
            super().__init__()
    
    class ControllerToggle(Message):
        """Message when controller is toggled"""
        def __init__(self, session_info: 'SessionInfo', enable: bool) -> None:
            self.session_info = session_info
            self.enable = enable
            super().__init__()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sessions_info = []
        self.selected_session = None
        self.logger = self._setup_logger()
        self.claude_manager = ClaudeManager()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file-only output"""
        logger = logging.getLogger("yesman.dashboard.project_panel")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = ensure_log_directory(get_default_log_path())
        
        log_file = log_path / "project_panel.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
        
    def compose(self) -> ComposeResult:
        tree = TextualTree("📊 Tmux Sessions", id="session-tree")
        tree.show_root = False
        tree.auto_expand = True  # Always expand nodes
        yield tree
    
    def update_sessions(self, sessions: list[SessionInfo], stats: DashboardStats) -> None:
        """Update the panel with session information"""
        self.sessions_info = sessions
        
        try:
            tree = self.query_one("#session-tree", TextualTree)
            
            # Store expansion state before clearing
            expansion_state = self._get_expansion_state(tree)
            
            # Clear existing content
            tree.clear()
            
            # Add stats header
            stats_node = tree.root.add(f"📊 Stats: {stats.total_sessions} sessions, {stats.running_sessions} running, {stats.active_controllers} controllers")
            stats_node.expand()
            stats_node.allow_expand = False  # Prevent collapsing
            
            if not sessions:
                tree.root.add("[dim]No sessions found. Run './yesman.py setup' first.[/]")
            else:
                # Add sessions to tree
                for session in sessions:
                    self._add_session_to_tree(tree.root, session)
            
            # Restore expansion state after rebuilding
            self._restore_expansion_state(tree, expansion_state)
            
            self.logger.info(f"Updated {len(sessions)} sessions")
        except Exception as e:
            self.logger.error(f"Error updating sessions: {e}", exc_info=True)
    
    def _add_session_to_tree(self, root_node, session: SessionInfo) -> None:
        """Add a session to the tree structure"""
        # Session status and icon
        if session.status == 'running':
            status_icon = "🟢"
        else:
            status_icon = "🔴"
        
        # Create session node
        session_label = f"{status_icon} {session.project_name} ({session.session_name})"
        session_node = root_node.add(session_label, data=session)
        # Don't force expand here - let restoration handle it
        
        # Add session info
        info_node = session_node.add(f"📋 Template: {session.template}")
        
        # Controller status with clickable indicator
        if session.controller_status == 'running':
            controller_text = "[on reverse] ▶ [/] Controller: Active"
            controller_data = {"type": "controller", "status": "running", "session": session}
        elif session.controller_status == 'not running':
            controller_text = "[dim] ◼ [/] Controller: Ready"
            controller_data = {"type": "controller", "status": "ready", "session": session}
        else:
            controller_text = "[dim] ◼ [/] Controller: Unknown"
            controller_data = {"type": "controller", "status": "unknown", "session": session}
        
        controller_node = session_node.add(controller_text, data=controller_data)
        
        # Add windows if running
        if session.windows:
            windows_node = session_node.add(f"🪟 Windows ({len(session.windows)})")
            # Don't force expand here - let restoration handle it
            
            for window in session.windows:
                # Window node
                window_label = f"[{window.index}] {window.name}"
                window_node = windows_node.add(window_label)
                
                # Add panes
                if window.panes:
                    for i, pane in enumerate(window.panes):
                        if pane.is_claude:
                            pane_label = f"🔵 Pane {i}: Claude"
                        elif pane.is_controller:
                            pane_label = f"🟡 Pane {i}: Controller"
                        else:
                            pane_label = f"⚪ Pane {i}: {pane.command}"
                        window_node.add(pane_label)
                else:
                    window_node.add("No panes")
        else:
            session_node.add("[dim]No windows[/]")
    
    def _get_expansion_state(self, tree: TextualTree) -> dict:
        """Get current expansion state of tree nodes"""
        expansion_state = {}
        
        def _collect_state(node, path=""):
            # Create a unique path for each node based on its label
            node_path = f"{path}/{node.label}" if path else str(node.label)
            expansion_state[node_path] = node.is_expanded
            
            # Recursively collect state for children
            for child in node.children:
                _collect_state(child, node_path)
        
        if tree.root and tree.root.children:
            for child in tree.root.children:
                _collect_state(child)
        
        return expansion_state
    
    def _restore_expansion_state(self, tree: TextualTree, expansion_state: dict) -> None:
        """Restore expansion state of tree nodes"""
        
        def _restore_state(node, path=""):
            # Create the same unique path used during collection
            node_path = f"{path}/{node.label}" if path else str(node.label)
            
            # Restore expansion state if we have it
            if node_path in expansion_state:
                if expansion_state[node_path]:
                    node.expand()
                else:
                    node.collapse()
            else:
                # Default behavior for new nodes - expand stats and session nodes
                if "📊 Stats:" in str(node.label) or any(icon in str(node.label) for icon in ["🟢", "🔴"]):
                    node.expand()
            
            # Recursively restore state for children
            for child in node.children:
                _restore_state(child, node_path)
        
        if tree.root and tree.root.children:
            for child in tree.root.children:
                _restore_state(child)
    
    def on_tree_node_selected(self, event: TextualTree.NodeSelected) -> None:
        """Handle tree node selection"""
        if event.node.data:
            # Check if it's a controller node
            if isinstance(event.node.data, dict) and event.node.data.get("type") == "controller":
                self._toggle_controller(event.node.data)
                event.stop()  # Prevent further processing
            # Check if it's a session node
            elif hasattr(event.node.data, 'session_name'):
                self.selected_session = event.node.data
                self.post_message(self.SessionSelected(event.node.data))
                self.logger.info(f"Selected session: {event.node.data.session_name}")
    
    def on_tree_node_expanded(self, event: TextualTree.NodeExpanded) -> None:
        """Handle node expansion"""
        # Allow normal expansion behavior now that we preserve state
        pass
    
    def on_tree_node_collapsed(self, event: TextualTree.NodeCollapsed) -> None:
        """Handle node collapse"""
        # Allow normal collapse behavior now that we preserve state
        pass
    
    def _toggle_controller(self, controller_data: dict) -> None:
        """Toggle controller on/off"""
        session = controller_data["session"]
        status = controller_data["status"]
        
        # Send controller toggle message
        if status == "running":
            self.post_message(self.ControllerToggle(session, False))
        elif status == "ready":
            self.post_message(self.ControllerToggle(session, True))
        
        self.logger.info(f"Toggling controller for {session.session_name}: {status}")


class ControlPanel(Static):
    """Right top panel for controller operations"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_session = None
        self.claude_manager = ClaudeManager()
        self.current_controller = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for control panel"""
        logger = logging.getLogger("yesman.dashboard.control_panel")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = ensure_log_directory(get_default_log_path())
        
        log_file = log_path / "control_panel.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("[dim]No session selected[/]", id="session-title")
            
            with Horizontal():
                yield Button("🔄 Restart Claude", id="restart-claude-btn", variant="warning")
                yield Button("▶️ Start Controller", id="start-controller-btn", variant="success")
                yield Button("⏹️ Stop Controller", id="stop-controller-btn", variant="error")
            
            yield Static("Model:", classes="control-label")
            with RadioSet(id="model-radio"):
                yield RadioButton("Default", value=True, id="default-radio")
                yield RadioButton("Opus4", value=False, id="opus-radio") 
                yield RadioButton("Sonnet4", value=False, id="sonnet-radio")
            
            with Horizontal():
                yield Static("Auto:", classes="control-label")
                yield Switch(value=True, id="auto-next-switch")
                yield Static("[green]ON[/]", id="auto-status-text")
            
            yield Static("[dim]Ready[/]", id="control-status")
            yield Static("[dim]No activity[/]", id="controller-activity")
    
    def update_session(self, session_info) -> None:
        """Update controls for selected session"""
        self.current_session = session_info
        
        # Get controller for this session
        self.current_controller = self.claude_manager.get_controller(session_info.session_name)
        
        # Set up callbacks for status updates
        if self.current_controller:
            self.current_controller.set_status_callback(self._on_controller_status)
            self.current_controller.set_activity_callback(self._on_controller_activity)
        
        try:
            title = self.query_one("#session-title", Static)
            title.update(f"[bold]{session_info.session_name}[/] ({session_info.project_name})")
            
            # Update status based on controller state
            if self.current_controller:
                if self.current_controller.is_running:
                    self.update_status("[green]Controller: Active[/]")
                else:
                    self.update_status("[yellow]Controller: Ready[/]")
            else:
                self.update_status("[red]Session not found[/]")
                
        except Exception as e:
            self.logger.error(f"Error updating session: {e}")
    
    def _on_controller_status(self, message: str):
        """Callback for controller status updates"""
        self.update_status(message)
    
    def _on_controller_activity(self, activity: str):
        """Callback for controller activity updates"""
        try:
            activity_widget = self.query_one("#controller-activity", Static)
            activity_widget.update(f"[cyan]{activity}[/]")
        except Exception:
            pass
    
    def update_status(self, message: str) -> None:
        """Update the status message"""
        try:
            status = self.query_one("#control-status", Static)
            status.update(message)
        except Exception:
            pass
    
    def start_controller(self) -> bool:
        """Start controller for current session"""
        if not self.current_controller:
            self.update_status("[red]No session selected[/]")
            return False
        return self.current_controller.start()
    
    def stop_controller(self) -> bool:
        """Stop controller for current session"""
        if not self.current_controller:
            self.update_status("[red]No session selected[/]")
            return False
        return self.current_controller.stop()
    
    def restart_claude_pane(self) -> bool:
        """Restart Claude pane for current session"""
        if not self.current_controller:
            self.update_status("[red]No session selected[/]")
            return False
        return self.current_controller.restart_claude_pane()
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle model radio button change"""
        if event.radio_set.id == "model-radio" and self.current_controller:
            # Map radio button IDs to model names
            model_map = {
                "default-radio": "default",
                "opus-radio": "opus",
                "sonnet-radio": "sonnet"
            }
            
            if event.pressed and event.pressed.id in model_map:
                model = model_map[event.pressed.id]
                self.current_controller.set_model(model)
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle auto next switch change"""
        if event.switch.id == "auto-next-switch":
            try:
                status_text = self.query_one("#auto-status-text", Static)
                if event.value:
                    status_text.update("[green]ON[/]")
                else:
                    status_text.update("[red]OFF[/]")
                
                if self.current_controller:
                    self.current_controller.set_auto_next(event.value)
            except Exception as e:
                self.logger.error(f"Error updating auto status: {e}")


class LogViewerPanel(Static):
    """Right bottom panel showing real-time logs"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_files = []
        self.logger = self._setup_logger()
        self._last_positions = {}  # Track last read position for each file
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for log viewer panel"""
        logger = logging.getLogger("yesman.dashboard.log_viewer")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = Path("~/tmp/logs/yesman/").expanduser()
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / "log_viewer.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def compose(self) -> ComposeResult:
        yield RichLog(highlight=True, markup=True, id="log-viewer")
    
    def on_mount(self) -> None:
        """Setup log file monitoring when mounted"""
        try:
            # Test if we can write to the log widget
            log_widget = self.query_one("#log-viewer", RichLog)
            log_widget.write("[green]Log Viewer Initialized[/]")
            
            self._setup_log_files()
            # Show initial recent logs
            self._show_recent_logs()
            self.set_interval(0.5, self._update_logs)  # Update every 0.5 seconds
        except Exception as e:
            # If there's any error, try to log it
            self.logger.error(f"Error in on_mount: {e}")
    
    def _show_recent_logs(self) -> None:
        """Show last 20 lines from each log file on startup"""
        try:
            log_widget = self.query_one("#log-viewer", RichLog)
            log_widget.write("[bold cyan]===== Dashboard Started - Recent Logs =====[/]")
            
            # Debug: Show number of files being monitored
            log_widget.write(f"[yellow]Monitoring {len(self.log_files)} log files[/]")
            
            for file_path in self.log_files:
                if file_path.exists():
                    try:
                        # Debug: Show file being read
                        log_widget.write(f"[dim]Reading: {file_path.name}[/]")
                        
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            # Get last 5 lines from each file
                            recent_lines = lines[-5:] if len(lines) > 5 else lines
                            for line in recent_lines:
                                if line.strip():
                                    formatted_line = self._format_log_line(line, file_path.name)
                                    if formatted_line:
                                        log_widget.write(formatted_line)
                            # Update position to end of file
                            self._last_positions[str(file_path)] = file_path.stat().st_size
                    except Exception as e:
                        log_widget.write(f"[red]Error reading {file_path.name}: {e}[/]")
                        self.logger.error(f"Error reading recent logs from {file_path}: {e}")
                else:
                    log_widget.write(f"[red]File not found: {file_path}[/]")
                        
            log_widget.write("[bold cyan]===== Live Monitoring Started =====[/]")
        except Exception as e:
            self.logger.error(f"Error showing recent logs: {e}")
    
    def _setup_log_files(self) -> None:
        """Setup list of log files to monitor"""
        log_path = Path("~/tmp/logs/yesman/").expanduser()
        self.log_files = []
        
        try:
            if not log_path.exists():
                log_widget = self.query_one("#log-viewer", RichLog)
                log_widget.write(f"[red]Log directory not found: {log_path}[/]")
                return
                
            # Add specific log files
            specific_files = ["yesman.log", "dashboard.log", "control_panel.log"]
            for filename in specific_files:
                file_path = log_path / filename
                if file_path.exists():
                    self.log_files.append(file_path)
                    self._last_positions[str(file_path)] = 0  # Start from beginning
            
            # Add all controller and dashboard_controller logs
            for pattern in ["controller_*.log", "dashboard_controller_*.log"]:
                for file_path in log_path.glob(pattern):
                    if file_path.exists():
                        self.log_files.append(file_path)
                        self._last_positions[str(file_path)] = 0  # Start from beginning
            
            self.logger.info(f"Monitoring {len(self.log_files)} log files")
            
        except Exception as e:
            try:
                log_widget = self.query_one("#log-viewer", RichLog)
                log_widget.write(f"[red]Error setting up log files: {e}[/]")
            except:
                pass
            self.logger.error(f"Error in _setup_log_files: {e}")
    
    def _update_logs(self) -> None:
        """Read new log entries and display them"""
        try:
            log_widget = self.query_one("#log-viewer", RichLog)
            
            # Read from all monitored log files
            for file_path in self.log_files:
                if file_path.exists():
                    self._read_log_file(file_path, log_widget)
                        
        except Exception as e:
            self.logger.error(f"Error updating logs: {e}")
            # Also show error in the log widget
            log_widget.write(f"[red]Error reading logs: {e}[/]")
    
    def _read_log_file(self, file_path: Path, log_widget: RichLog) -> None:
        """Read new content from a specific log file"""
        try:
            file_str = str(file_path)
            current_size = file_path.stat().st_size
            last_pos = self._last_positions.get(file_str, 0)
            
            if current_size > last_pos:
                with open(file_path, 'r') as f:
                    f.seek(last_pos)
                    new_content = f.read()
                    
                    # Process and display new log lines
                    for line in new_content.splitlines():
                        if line.strip():
                            formatted_line = self._format_log_line(line, file_path.name)
                            log_widget.write(formatted_line)
                    
                    self._last_positions[file_str] = current_size
                    
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
    
    def _format_log_line(self, line: str, filename: str) -> str:
        """Format log line with color based on level"""
        # Skip empty lines
        if not line.strip():
            return ""
            
        # Determine log level and apply color
        if "ERROR" in line or "CRITICAL" in line:
            color = "red"
            emoji = "❌"
        elif "WARNING" in line or "WARN" in line:
            color = "yellow"
            emoji = "⚠️"
        elif "INFO" in line:
            color = "green"
            emoji = "ℹ️"
        elif "DEBUG" in line:
            color = "dim cyan"
            emoji = "🔍"
        else:
            color = "white"
            emoji = "📝"
        
        # Extract source from filename
        source = filename.replace(".log", "").replace("_", " ").replace("dashboard controller", "ctrl")
        
        # Truncate long lines
        max_line_length = 200
        if len(line) > max_line_length:
            line = line[:max_line_length] + "..."
        
        # Format: [source] emoji message
        return f"[dim cyan]{source:>15}[/] {emoji} [{color}]{line.strip()}[/]"