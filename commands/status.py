"""Comprehensive project status dashboard command"""

import click
import time
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.columns import Columns

from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
from libs.dashboard.widgets import (
    SessionBrowser, ActivityHeatmap, ProjectHealthWidget,
    GitActivityWidget, ProgressTracker, SessionProgressWidget
)
from libs.core.session_manager import SessionManager


class StatusDashboard:
    """Comprehensive status dashboard"""
    
    def __init__(self, project_path: str = ".", update_interval: float = 5.0):
        self.console = Console()
        self.project_path = Path(project_path).resolve()
        self.project_name = self.project_path.name
        self.update_interval = update_interval
        
        # Initialize components
        self.config = YesmanConfig()
        self.tmux_manager = TmuxManager(self.config)
        
        # Initialize widgets
        self.session_browser = SessionBrowser(self.console)
        self.activity_heatmap = ActivityHeatmap(self.console)
        self.project_health = ProjectHealthWidget(self.console)
        self.git_activity = GitActivityWidget(self.console, str(self.project_path))
        self.progress_tracker = ProgressTracker(self.console)
        self.session_progress = SessionProgressWidget(self.console)
        
        # Initialize session manager
        self.session_manager = SessionManager()
        
        # Load initial data
        self._load_todo_data()
        self.progress_data = None
    
    def _load_todo_data(self):
        """Load TODO data from various sources"""
        # Try to load from common TODO file locations
        todo_files = [
            self.project_path / "TODO.md",
            self.project_path / "BACKLOG.md",
            self.project_path / "results" / "todos" / "high-priority-improvements.md",
            self.project_path / "results" / "todos" / "medium-priority-tasks.md"
        ]
        
        for todo_file in todo_files:
            if todo_file.exists():
                if self.progress_tracker.load_todos_from_file(str(todo_file)):
                    break
    
    def update_data(self):
        """Update all dashboard data"""
        try:
            # Update session data
            sessions_list = self.tmux_manager.get_cached_sessions_list()
            detailed_sessions = []
            
            for session_info in sessions_list:
                session_name = session_info["session_name"]
                detailed_info = self.tmux_manager.get_session_info(session_name)
                detailed_sessions.append(detailed_info)
                
                # Calculate activity for heatmap
                activity_level = self._calculate_session_activity(detailed_info)
                self.activity_heatmap.add_activity_point(session_name, activity_level)
            
            # Update session browser
            self.session_browser.update_sessions(detailed_sessions)
            
            # Update project health
            self.project_health.update_project_health(str(self.project_path), self.project_name)
            
            # Update session progress
            self.progress_data = self.session_manager.get_progress_overview()
            
            # Git and progress data updates happen automatically in their respective widgets
            
        except Exception as e:
            self.console.print(f"[red]Error updating data: {e}[/]")
    
    def _calculate_session_activity(self, session_info: dict) -> float:
        """Calculate activity level for a session"""
        if not session_info.get("exists", True):
            return 0.0
        
        activity = 0.0
        windows = session_info.get("windows", [])
        
        for window in windows:
            for pane in window.get("panes", []):
                command = pane.get("pane_current_command", "")
                
                if command and command not in ["zsh", "bash", "sh"]:
                    activity += 0.2
                
                if "claude" in command.lower():
                    activity += 0.4
                
                if pane.get("pane_active"):
                    activity += 0.1
        
        return min(activity, 1.0)
    
    def create_layout(self) -> Layout:
        """Create the dashboard layout"""
        layout = Layout()
        
        # Main layout structure
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Split main area
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=2)
        )
        
        # Split left column
        layout["left"].split_column(
            Layout(name="sessions", ratio=3),
            Layout(name="health", ratio=2)
        )
        
        # Split right column
        layout["right"].split_column(
            Layout(name="activity", ratio=2),
            Layout(name="progress", ratio=2),
            Layout(name="session_progress", ratio=2)
        )
        
        return layout
    
    def update_layout(self, layout: Layout):
        """Update layout with current data"""
        # Header
        header_text = (
            f"🚀 Yesman Project Dashboard - {self.project_name} | "
            f"{time.strftime('%H:%M:%S')} | "
            f"Cache Hit Rate: {self.tmux_manager.get_cache_stats().get('hit_rate', 0):.1%}"
        )
        layout["header"].update(Panel(header_text, style="bold blue"))
        
        # Sessions
        session_content, _ = self.session_browser.render()
        layout["sessions"].update(session_content)
        
        # Project health
        health_content = self.project_health.render_health_overview(self.project_name)
        layout["health"].update(health_content)
        
        # Activity heatmap
        activity_content = self.activity_heatmap.render_combined_heatmap()
        layout["activity"].update(activity_content)
        
        # Progress tracking
        progress_content = self.progress_tracker.render_progress_overview()
        layout["progress"].update(progress_content)
        
        # Session progress
        if self.progress_data:
            session_progress_content = self.session_progress.render_progress_overview(self.progress_data)
            layout["session_progress"].update(session_progress_content)
        else:
            layout["session_progress"].update(Panel("[dim]Loading session progress...[/dim]", title="📊 Session Progress"))
        
        # Footer with compact status
        footer_parts = []
        footer_parts.append(self.project_health.render_compact_status(self.project_name))
        footer_parts.append(self.git_activity.render_compact_status())
        footer_parts.append(self.progress_tracker.render_compact_progress())
        footer_parts.append(self.activity_heatmap.render_compact_overview())
        
        footer_text = " | ".join(str(part) for part in footer_parts)
        layout["footer"].update(Panel(footer_text, style="dim"))
    
    def run_interactive(self):
        """Run interactive dashboard"""
        layout = self.create_layout()
        
        try:
            with Live(layout, console=self.console, refresh_per_second=2) as live:
                while True:
                    self.update_data()
                    self.update_layout(layout)
                    time.sleep(self.update_interval)
                    
        except KeyboardInterrupt:
            self.console.print("\\n[yellow]Dashboard stopped[/]")
    
    def render_detailed_view(self):
        """Render detailed view with all components"""
        self.update_data()
        
        # Create detailed panels
        panels = []
        
        # Session browser
        session_content, _ = self.session_browser.render()
        panels.append(session_content)
        
        # Project health detailed
        health_detailed = self.project_health.render_detailed_breakdown(self.project_name)
        panels.append(health_detailed)
        
        # Git activity
        git_overview = self.git_activity.render_activity_overview()
        git_commits = self.git_activity.render_recent_commits()
        panels.extend([git_overview, git_commits])
        
        # Progress tracking
        progress_overview = self.progress_tracker.render_progress_overview()
        todo_list = self.progress_tracker.render_todo_list(limit=8)
        panels.extend([progress_overview, todo_list])
        
        # Activity heatmap
        activity_heatmap = self.activity_heatmap.render_combined_heatmap()
        panels.append(activity_heatmap)
        
        # Display all panels
        for panel in panels:
            self.console.print(panel)
            self.console.print()


@click.command()
@click.option('--project-path', '-p', default=".", help='Project directory path')
@click.option('--interactive', '-i', is_flag=True, help='Run interactive dashboard')
@click.option('--update-interval', '-u', default=5.0, type=float, help='Update interval in seconds')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed view')
def status(project_path, interactive, update_interval, detailed):
    """Comprehensive project status dashboard"""
    
    try:
        dashboard = StatusDashboard(project_path, update_interval)
        
        if interactive:
            click.echo("Starting interactive project status dashboard...")
            click.echo("Press Ctrl+C to exit")
            dashboard.run_interactive()
        elif detailed:
            dashboard.render_detailed_view()
        else:
            # Quick status overview
            dashboard.update_data()
            
            console = Console()
            
            # Quick summary
            console.print(f"🎯 Project: {dashboard.project_name}", style="bold cyan")
            console.print()
            
            # Compact status from each widget
            health_status = dashboard.project_health.render_compact_status(dashboard.project_name)
            git_status = dashboard.git_activity.render_compact_status()
            progress_status = dashboard.progress_tracker.render_compact_progress()
            
            console.print("📊 Quick Status:")
            console.print(f"  Health: {health_status}")
            console.print(f"  Git: {git_status}")
            console.print(f"  Progress: {progress_status}")
            
            console.print("\\n💡 Use --interactive for live dashboard or --detailed for full view")
            
    except KeyboardInterrupt:
        click.echo("\\nStatus dashboard stopped.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)