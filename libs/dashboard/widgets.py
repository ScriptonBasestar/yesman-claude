"""UI widgets for dashboard"""

from textual.widgets import Static, Button, Tree as TextualTree, Select, Switch, RadioSet, RadioButton
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
from .controller_manager import ControllerManager


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
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file-only output"""
        logger = logging.getLogger("yesman.dashboard.project_panel")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = Path("~/tmp/logs/yesman/").expanduser()
        log_path.mkdir(parents=True, exist_ok=True)
        
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
        session_node.expand()
        session_node.allow_expand = False  # Prevent collapsing
        
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
            windows_node.expand()
            windows_node.allow_expand = False  # Prevent collapsing
            
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
        """Keep nodes expanded"""
        pass  # Do nothing, let it expand
    
    def on_tree_node_collapsed(self, event: TextualTree.NodeCollapsed) -> None:
        """Prevent nodes from collapsing"""
        event.node.expand()  # Re-expand immediately
        event.stop()  # Stop the collapse event
    
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
        self.controller_manager = ControllerManager()
        self.current_controller = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for control panel"""
        logger = logging.getLogger("yesman.dashboard.control_panel")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = Path("~/tmp/logs/yesman/").expanduser()
        log_path.mkdir(parents=True, exist_ok=True)
        
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
        self.current_controller = self.controller_manager.get_controller(session_info.session_name)
        
        # Set up callbacks for status updates
        self.current_controller.set_status_callback(self._on_controller_status)
        self.current_controller.set_activity_callback(self._on_controller_activity)
        
        try:
            title = self.query_one("#session-title", Static)
            title.update(f"[bold]{session_info.session_name}[/] ({session_info.project_name})")
            
            # Update status based on controller state
            if self.current_controller.is_running:
                self.update_status("[green]Controller: Active[/]")
            else:
                self.update_status("[yellow]Controller: Ready[/]")
                
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


class InfoPanel(Static):
    """Right bottom panel showing session details"""
    
    def compose(self) -> ComposeResult:
        yield Static(
            "[bold cyan]Quick Stats:[/]\n\n"
            "[green]●[/] [bold]Active Features:[/]\n"
            "  • Real-time session monitoring\n"
            "  • Controller status tracking\n"
            "  • Window/pane detection\n"
            "  • Claude integration status\n\n"
            "[yellow]●[/] [bold]Keyboard Shortcuts:[/]\n"
            "  • [bold]Ctrl+C[/] - Exit dashboard\n"
            "  • [bold]R[/] - Refresh data\n"
            "  • [bold]?[/] - Show help\n\n"
            "[dim]Dashboard updates every 2 seconds[/]",
            id="info-content"
        )