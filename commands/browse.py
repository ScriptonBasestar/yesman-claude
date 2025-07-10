"""Interactive session browser command"""

import click
import sys
import time
import threading
from typing import Optional

from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
from libs.dashboard.widgets.session_browser import SessionBrowser
from libs.dashboard.widgets.activity_heatmap import ActivityHeatmapGenerator
from libs.dashboard.widgets.session_progress import SessionProgressWidget
from libs.core.session_manager import SessionManager

from rich.console import Console
from rich.live import Live
from rich.layout import Layout


class InteractiveBrowser:
    """Interactive session browser with live updates"""
    
    def __init__(self, update_interval: float = 2.0):
        self.console = Console()
        self.config = YesmanConfig()
        self.tmux_manager = TmuxManager(self.config)
        
        # Initialize widgets
        self.session_browser = SessionBrowser(self.console)
        self.activity_heatmap = ActivityHeatmapGenerator(self.config)
        self.progress_widget = SessionProgressWidget(self.console)
        
        # Initialize session manager for progress tracking
        self.session_manager = SessionManager()
        
        self.update_interval = update_interval
        self.running = False
        self.update_thread: Optional[threading.Thread] = None
        self.progress_data = None
        
    def update_data(self):
        """Update session data and activity metrics"""
        try:
            # Get session information using cached method
            sessions_list = self.tmux_manager.get_cached_sessions_list()
            detailed_sessions = []
            
            for session_info in sessions_list:
                session_name = session_info["session_name"]
                detailed_info = self.tmux_manager.get_session_info(session_name)
                detailed_sessions.append(detailed_info)
                
                # Calculate and record activity
                activity_level = self._calculate_session_activity(detailed_info)
                self.activity_heatmap.add_activity_point(session_name, activity_level)
            
            # Update browser with new data
            self.session_browser.update_sessions(detailed_sessions)
            
            # Update progress data
            self.progress_data = self.session_manager.get_progress_overview()
            
        except Exception as e:
            self.console.print(f"[red]Error updating session data: {e}[/]")
    
    def _calculate_session_activity(self, session_info: dict) -> float:
        """Calculate activity level for a session"""
        if not session_info.get("exists", True):
            return 0.0
        
        activity = 0.0
        windows = session_info.get("windows", [])
        
        for window in windows:
            for pane in window.get("panes", []):
                command = pane.get("pane_current_command", "")
                
                # Active processes contribute to activity
                if command and command not in ["zsh", "bash", "sh"]:
                    activity += 0.2
                
                # Claude sessions get higher weight
                if "claude" in command.lower():
                    activity += 0.4
                
                # Active panes get bonus
                if pane.get("pane_active"):
                    activity += 0.1
        
        return min(activity, 1.0)
    
    def create_layout(self) -> Layout:
        """Create the main dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        # Split left panel for sessions and progress
        layout["left"].split_column(
            Layout(name="sessions", ratio=3),
            Layout(name="progress", size=10)
        )
        
        # Right panel is for activity heatmap
        layout["right"].update(Layout(name="activity"))
        
        return layout
    
    def update_layout(self, layout: Layout):
        """Update layout content"""
        # Header
        header_text = f"🚀 Yesman Session Browser - {time.strftime('%H:%M:%S')}"
        cache_stats = self.tmux_manager.get_cache_stats()
        header_text += f" | Cache: {cache_stats.get('hit_rate', 0):.1%} hit rate"
        layout["header"].update(self.console.render_str(header_text, style="bold blue"))
        
        # Main session browser
        browser_content, status_bar = self.session_browser.render()
        layout["sessions"].update(browser_content)
        
        # Progress overview
        if self.progress_data:
            progress_panel = self.progress_widget.render_progress_overview(self.progress_data)
            layout["progress"].update(progress_panel)
        else:
            layout["progress"].update("[dim]Loading progress data...[/dim]")
        
        # Activity heatmap
        heatmap_content = self.activity_heatmap.render_combined_heatmap()
        layout["activity"].update(heatmap_content)
        
        # Footer
        layout["footer"].update(status_bar)
    
    def background_updater(self):
        """Background thread for updating data"""
        while self.running:
            self.update_data()
            time.sleep(self.update_interval)
    
    def start(self):
        """Start the interactive browser"""
        self.running = True
        
        # Initial data load
        self.update_data()
        
        # Start background update thread
        self.update_thread = threading.Thread(target=self.background_updater, daemon=True)
        self.update_thread.start()
        
        # Create layout
        layout = self.create_layout()
        
        try:
            with Live(layout, console=self.console, refresh_per_second=10) as live:
                while self.running:
                    self.update_layout(layout)
                    
                    # Handle keyboard input (basic implementation)
                    # In a real implementation, you'd use a library like keyboard or blessed
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the browser"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)


@click.command()
@click.option('--update-interval', '-i', default=2.0, type=float, 
              help='Update interval in seconds (default: 2.0)')
def browse(update_interval):
    """Interactive session browser with activity monitoring"""
    
    try:
        browser = InteractiveBrowser(update_interval)
        click.echo("Starting interactive session browser...")
        click.echo("Press Ctrl+C to exit")
        
        browser.start()
        
    except KeyboardInterrupt:
        click.echo("\nSession browser stopped.")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)