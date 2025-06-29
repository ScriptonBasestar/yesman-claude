"""Main dashboard application"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual import events
import logging
from pathlib import Path
import os
import sys

from .widgets import ProjectPanel, ControlPanel, LogViewerPanel
from .session_manager import SessionManager
from .models import DashboardStats
from .styles import DASHBOARD_CSS
from .simple_view import run_simple_dashboard


class CustomFooter(Static):
    """Custom footer with keyboard shortcuts"""
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="footer-container"):
            yield Static("🚪 [bold]Ctrl+C[/bold] Exit", classes="footer-key")
            yield Static("🔄 [bold]R[/bold] Refresh", classes="footer-key")
            yield Static("❓ [bold]?[/bold] Help", classes="footer-key")


class DashboardApp(App):
    """Main dashboard application with 3-panel layout"""
    
    CSS = DASHBOARD_CSS
    
    sessions_data = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_manager = SessionManager()
        self._project_panel = None
        self._control_panel = None
        self.logger = self._setup_logger()
        self._check_terminal_compatibility()
        
    def _check_terminal_compatibility(self) -> None:
        """Check terminal compatibility and set up environment if needed"""
        term = os.environ.get('TERM', '')
        colorterm = os.environ.get('COLORTERM', '')
        
        # List of known compatible terminals
        compatible_terms = [
            'xterm', 'xterm-256color', 'xterm-color',
            'screen', 'screen-256color',
            'tmux', 'tmux-256color',
            'rxvt', 'rxvt-unicode', 'rxvt-unicode-256color',
            'linux', 'vt100', 'vt220'
        ]
        
        # Check if terminal is compatible
        is_compatible = any(term.startswith(t) for t in compatible_terms)
        
        if not is_compatible:
            # Try to set a compatible TERM
            os.environ['TERM'] = 'xterm-256color'
            self.logger.warning(f"Terminal '{term}' may not be compatible. Setting TERM=xterm-256color")
        
        # Force color support if not set
        if not colorterm and not os.environ.get('FORCE_COLOR'):
            os.environ['FORCE_COLOR'] = '1'
            
        # Check if we're in a real terminal
        if not sys.stdout.isatty():
            self.logger.error("Not running in a terminal. Dashboard requires interactive terminal.")
            print("Error: Dashboard must be run in an interactive terminal.")
            print("If running from a script, use: script -q /dev/null ./yesman.py dashboard")
            sys.exit(1)
            
        # Check if we should fallback to simple mode
        if os.environ.get('YESMAN_SIMPLE_MODE', '').lower() in ('1', 'true', 'yes'):
            self.logger.info("Simple mode requested via YESMAN_SIMPLE_MODE")
            print("Starting dashboard in simple mode...")
            run_simple_dashboard()
            sys.exit(0)
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file-only output"""
        logger = logging.getLogger("yesman.dashboard.app")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = Path("~/tmp/logs/yesman/").expanduser()
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / "dashboard_app.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Suppress libtmux logs
        libtmux_logger = logging.getLogger('libtmux')
        libtmux_logger.setLevel(logging.WARNING)
        
        return logger

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            self._project_panel = ProjectPanel(id="project-panel")
            self._project_panel.border_title = "📊 Tmux Sessions"
            yield self._project_panel
            
            self._control_panel = ControlPanel(id="control-panel")
            self._control_panel.border_title = "🎮 Controller Operations"
            yield self._control_panel
            
            log_panel = LogViewerPanel(id="log-panel")
            log_panel.border_title = "📋 Live Logs"
            yield log_panel
        yield CustomFooter()

    def on_mount(self) -> None:
        """Start periodic refresh when app is mounted"""
        # Give widgets time to mount before refreshing
        self.set_timer(0.1, self.refresh_data)
        self.set_interval(2, self.refresh_data)

    def refresh_data(self) -> None:
        """Refresh session data"""
        self.logger.info("Refreshing dashboard data")
        try:
            sessions = self.session_manager.get_all_sessions()
            stats = DashboardStats.from_sessions(sessions)
            
            if self._project_panel:
                self._project_panel.update_sessions(sessions, stats)
            
            self.logger.info(f"Updated {len(sessions)} sessions")
            
        except Exception as e:
            self.logger.error(f"Error refreshing data: {e}", exc_info=True)
    
    def on_project_panel_session_selected(self, event: ProjectPanel.SessionSelected) -> None:
        """Handle session selection from ProjectPanel"""
        if self._control_panel:
            self._control_panel.update_session(event.session_info)
            self.logger.info(f"Session selected: {event.session_info.session_name}")
    
    def on_project_panel_controller_toggle(self, event: ProjectPanel.ControllerToggle) -> None:
        """Handle controller toggle from ProjectPanel"""
        if self._control_panel:
            # First update the session if different
            if self._control_panel.current_session != event.session_info:
                self._control_panel.update_session(event.session_info)
            
            # Then toggle the controller
            if event.enable:
                self._control_panel.start_controller()
            else:
                self._control_panel.stop_controller()
            
            self.logger.info(f"Controller toggle for {event.session_info.session_name}: {'start' if event.enable else 'stop'}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if self._control_panel:
            if button_id == "start-controller-btn":
                self._control_panel.start_controller()
            elif button_id == "stop-controller-btn":
                self._control_panel.stop_controller()
            elif button_id == "restart-claude-btn":
                self._control_panel.restart_claude_pane()

    def on_key(self, event: events.Key) -> None:
        """Handle key press events"""
        if event.key == "ctrl+c":
            self.exit()
        elif event.key == "r":
            # Manual refresh
            self.refresh_data()
            if self._control_panel:
                self._control_panel.update_status("[cyan]Data refreshed![/]")
        elif event.key == "question_mark":
            # Show help
            if self._control_panel:
                self._control_panel.update_status("[yellow]Help: Use Ctrl+C to exit, R to refresh[/]")