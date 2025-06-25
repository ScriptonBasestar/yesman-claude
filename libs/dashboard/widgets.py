"""UI widgets for dashboard"""

from textual.widgets import Static, Button, Tree as TextualTree, Select, Switch
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


class ProjectPanel(Static):
    """Left panel showing tmux project status"""
    
    class SessionSelected(Message):
        """Message when a session is selected"""
        def __init__(self, session_info: 'SessionInfo') -> None:
            self.session_info = session_info
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
        
        # Add session info
        info_node = session_node.add(f"📋 Template: {session.template}")
        
        # Controller status
        if session.controller_status == 'running':
            controller_text = "🤖 Controller: Active"
        elif session.controller_status == 'not running':
            controller_text = "🔧 Controller: Ready"
        else:
            controller_text = "❓ Controller: Unknown"
        
        session_node.add(controller_text)
        
        # Add windows if running
        if session.windows:
            windows_node = session_node.add(f"🪟 Windows ({len(session.windows)})")
            windows_node.expand()
            
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
        if event.node.data and hasattr(event.node.data, 'session_name'):
            self.selected_session = event.node.data
            self.post_message(self.SessionSelected(event.node.data))
            self.logger.info(f"Selected session: {event.node.data.session_name}")


class ControlPanel(Static):
    """Right top panel for controller operations"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_session = None
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("[dim]No session selected[/]", id="session-title")
            
            with Horizontal():
                yield Button("🔄 Restart Claude", id="restart-claude-btn", variant="warning")
                yield Button("▶️ Start Controller", id="start-controller-btn", variant="success")
            
            with Horizontal():
                yield Static("Model:", classes="control-label")
                yield Select([
                    ("Default", "default"),
                    ("Claude Opus", "opus"),
                    ("Claude Sonnet", "sonnet"),
                ], value="default", id="model-select")
            
            with Horizontal():
                yield Static("Auto Next:", classes="control-label")
                yield Switch(value=False, id="auto-next-switch")
            
            yield Static("[dim]Ready[/]", id="control-status")
    
    def update_session(self, session_info) -> None:
        """Update controls for selected session"""
        self.current_session = session_info
        try:
            title = self.query_one("#session-title", Static)
            title.update(f"[bold]{session_info.session_name}[/] ({session_info.project_name})")
            
            status = self.query_one("#control-status", Static)
            if session_info.controller_status == 'running':
                status.update("[green]Controller: Active[/]")
            else:
                status.update("[yellow]Controller: Ready[/]")
        except Exception:
            pass
    
    def update_status(self, message: str) -> None:
        """Update the status message"""
        try:
            status = self.query_one("#control-status", Static)
            status.update(message)
        except Exception:
            pass


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