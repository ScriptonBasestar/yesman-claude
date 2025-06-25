"""UI widgets for dashboard"""

from textual.widgets import Static, Button
from textual.containers import Container
from textual.app import ComposeResult
import logging
from pathlib import Path
import os

from .models import SessionInfo, DashboardStats


class ProjectPanel(Static):
    """Left panel showing tmux project status"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sessions_info = []
        self.selected_project = None
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
        yield Static(
            "[bold cyan]Quick Stats:[/]\n\n"
            "[dim]Loading sessions...[/]",
            id="session-content"
        )
    
    def update_sessions(self, sessions: list[SessionInfo], stats: DashboardStats) -> None:
        """Update the panel with session information"""
        self.sessions_info = sessions
        content = self._format_sessions(sessions, stats)
        
        try:
            sessions_content = self.query_one("#session-content", Static)
            sessions_content.update(content)
            self.logger.info(f"Updated {len(sessions)} sessions")
        except Exception as e:
            self.logger.error(f"Error updating sessions: {e}", exc_info=True)
    
    def _format_sessions(self, sessions: list[SessionInfo], stats: DashboardStats) -> str:
        """Format session information for display"""
        if not sessions:
            return "[dim]No sessions found. Run './yesman.py setup' first.[/]"
        
        lines = []
        
        # Summary stats
        lines.append(f"Sessions: {stats.running_sessions}/{stats.total_sessions} running")
        lines.append(f"Controllers: {stats.active_controllers} active")
        lines.append("")
        
        # Project details
        for session in sessions:
            # Status indicators
            status_icon = "●" if session.status == 'running' else "○"
            
            # Controller status
            if session.controller_status == 'running':
                controller_text = "🤖 Active"
            elif session.controller_status == 'not running':
                controller_text = "�� Ready"
            else:
                controller_text = "❓ Unknown"
            
            # Project header
            lines.append(f"{status_icon} {session.project_name}")
            lines.append(f"  Session: {session.session_name}")
            lines.append(f"  Template: {session.template}")
            lines.append(f"  Controller: {controller_text}")
            
            # Windows and panes info
            if session.windows:
                lines.append(f"  Windows: {len(session.windows)}")
                for window in session.windows:
                    pane_count = len(window.panes)
                    claude_panes = sum(1 for p in window.panes if p.is_claude)
                    controller_panes = sum(1 for p in window.panes if p.is_controller)
                    
                    window_info = f"    [{window.index}] {window.name} ({pane_count} panes"
                    if claude_panes:
                        window_info += f", {claude_panes} Claude"
                    if controller_panes:
                        window_info += f", {controller_panes} Controller"
                    window_info += ")"
                    lines.append(window_info)
            else:
                lines.append("  No windows")
            
            lines.append("")
        
        return "\n".join(lines)


class ControlPanel(Static):
    """Right top panel for controller operations"""
    
    def compose(self) -> ComposeResult:
        yield Button("▶️  Start Controller", id="start-btn", variant="success")
        yield Button("⏹️  Stop Controller", id="stop-btn", variant="error")
        yield Button("🔄 Restart Session", id="restart-btn", variant="warning")
        yield Static("[dim]No action selected[/]", id="selected-info")
    
    def update_status(self, message: str) -> None:
        """Update the status message"""
        try:
            selected_info = self.query_one("#selected-info", Static)
            selected_info.update(message)
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