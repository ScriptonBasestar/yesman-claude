#!/usr/bin/env python3
import click
import time
import libtmux
import logging
from pathlib import Path
from typing import List, Dict, Any
import os
from datetime import datetime
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Button, Label, Tree, ListItem, ListView
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual import events

class ProjectPanel(Static):
    """Left panel showing tmux project status"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sessions_info = []
        self.selected_project = None
        self.logger = logging.getLogger("yesman.project_panel")
        self.logger.setLevel(logging.INFO)
        # 파일 로깅만 사용하도록 설정 (console 핸들러 비활성화)
        self.logger.propagate = False
        log_path_str = "~/tmp/logs/yesman/"
        log_path = Path(os.path.expanduser(log_path_str))
        log_path.mkdir(parents=True, exist_ok=True)
        project_panel_log_file = log_path / "project_panel.log"
        file_handler = logging.FileHandler(project_panel_log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def compose(self) -> ComposeResult:
        yield Static("[dim]Loading sessions...[/]", id="sessions-content")
    

class ControlPanel(Static):
    """Right top panel for controller operations"""
    
    def compose(self) -> ComposeResult:
        yield Button("▶️  Start Controller", id="start-btn", variant="success")
        yield Button("⏹️  Stop Controller", id="stop-btn", variant="error")
        yield Button("🔄 Restart Session", id="restart-btn", variant="warning")
        yield Static("[dim]No action selected[/]", id="selected-info")

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

class DashboardApp(App):
    """Main dashboard application with 3-panel layout"""
    
    CSS = """
    /* Main layout */
    #main-container {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        grid-columns: 2fr 1fr;
        grid-rows: 1fr 1fr;
        background: $surface;
    }
    
    /* Project panel styling */
    #project-panel {
        row-span: 2;
        border: round $primary;
        border-title-align: center;
        border-title-style: bold;
        border-title-color: $primary;
        border-title-background: $surface;
        padding: 1;
        background: $panel;
        box-sizing: border-box;
    }
    
    #sessions-content {
        padding: 1;
        color: $text;
        height: 100%;
        overflow-y: auto;
    }
    
    /* Control panel styling */
    #control-panel {
        border: round $secondary;
        border-title-align: center;
        border-title-style: bold;
        border-title-color: $secondary;
        border-title-background: $surface;
        padding: 1;
        background: $panel;
    }
    
    #info-panel {
        border: round $accent;
        border-title-align: center;
        border-title-style: bold;
        border-title-color: $accent;
        border-title-background: $surface;
        padding: 1;
        background: $panel;
    }
    
    /* Button styling */
    Button {
        margin: 1 0;
        width: 100%;
        border: round;
        text-style: bold;
    }
    
    Button:hover {
        border: thick;
    }
    
    Button.-success {
        background: $success;
        color: $text;
    }
    
    Button.-error {
        background: $error;
        color: $text;
    }
    
    Button.-warning {
        background: $warning;
        color: $text;
    }
    
    #selected-info {
        margin-top: 1;
        text-align: center;
        text-style: italic;
        color: $text-muted;
        background: $surface;
        padding: 1;
        border: round;
    }
    
    #info-content {
        text-align: left;
        color: $text-muted;
        padding: 1;
    }
    
    /* Header and footer styling */
    Header {
        background: $primary;
        color: $text;
        text-style: bold;
    }
    
    Footer {
        background: $surface;
        color: $text-muted;
    }
    """
    
    sessions_data = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger("yesman.dashboard_app")
        self.logger.setLevel(logging.INFO)
        # 파일 로깅만 사용하도록 설정 (console 핸들러 비활성화)
        self.logger.propagate = False
        log_path_str = "~/tmp/logs/yesman/"
        log_path = Path(os.path.expanduser(log_path_str))
        log_path.mkdir(parents=True, exist_ok=True)
        dashboard_log_file = log_path / "dashboard_app.log"
        file_handler = logging.FileHandler(dashboard_log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            project_panel = ProjectPanel(id="project-panel")
            project_panel.border_title = "📊 Tmux Sessions"
            yield project_panel
            
            control_panel = ControlPanel(id="control-panel")
            control_panel.border_title = "🎮 Controller Operations"
            yield control_panel
            
            info_panel = InfoPanel(id="info-panel")
            info_panel.border_title = "📋 Session Details"
            yield info_panel
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(2, self.refresh_data)
        self.refresh_data()

    def refresh_data(self) -> None:
        self.logger.info("refresh_data called")
        try:
            sessions_info = self.get_session_info()
            self.logger.info(f"Got {len(sessions_info)} sessions")
            
            # Format the sessions data
            if not sessions_info:
                content = "[dim]No sessions found. Run './yesman.py setup' first.[/]"
            else:
                content_lines = []
                
                # Summary stats
                total = len(sessions_info)
                running = sum(1 for s in sessions_info if s['status'] == 'running')
                controllers = sum(1 for s in sessions_info if s['controller_status'] == 'running')
                
                content_lines.append(f"Sessions: {running}/{total} running")
                content_lines.append(f"Controllers: {controllers} active")
                content_lines.append("")
                
                # Project details
                for i, info in enumerate(sessions_info):
                    # Status indicators
                    if info['status'] == 'running':
                        status_icon = "●"
                        status_text = "Running"
                    else:
                        status_icon = "○"
                        status_text = "Stopped"
                    
                    # Controller status
                    if info['controller_status'] == 'running':
                        controller_text = "🤖 Active"
                    elif info['controller_status'] == 'not running':
                        controller_text = "🔧 Ready"
                    else:
                        controller_text = "❓ Unknown"
                    
                    # Project header
                    content_lines.append(f"{status_icon} {info['project_name']}")
                    content_lines.append(f"  Session: {info['session_name']}")
                    content_lines.append(f"  Template: {info['template']}")
                    content_lines.append(f"  Controller: {controller_text}")
                    
                    # Windows and panes info
                    if info['windows']:
                        content_lines.append(f"  Windows: {len(info['windows'])}")
                        for window in info['windows']:
                            pane_count = len(window['panes'])
                            claude_panes = sum(1 for p in window['panes'] if p['is_claude'])
                            controller_panes = sum(1 for p in window['panes'] if p['is_controller'])
                            
                            window_info = f"    [{window['index']}] {window['name']} ({pane_count} panes"
                            if claude_panes:
                                window_info += f", {claude_panes} Claude"
                            if controller_panes:
                                window_info += f", {controller_panes} Controller"
                            window_info += ")"
                            content_lines.append(window_info)
                    else:
                        content_lines.append("  No windows")
                    
                    content_lines.append("")
                
                content = "\n".join(content_lines)
            
            # Update reactive data which will trigger watch_sessions_data
            self.sessions_data = content
            self.logger.info(f"Updated sessions_data with content length: {len(content)}")
            
        except Exception as e:
            self.logger.error(f"Error in refresh_data: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def watch_sessions_data(self, new_data: str) -> None:
        """Watch for changes in sessions_data and update the UI"""
        self.logger.info(f"watch_sessions_data called with data length: {len(new_data)}")
        try:
            sessions_content = self.query_one("#sessions-content", Static)
            sessions_content.update(new_data)
            self.logger.info("sessions-content updated successfully")
        except Exception as e:
            self.logger.error(f"Error updating sessions-content: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def get_session_info(self) -> List[Dict[str, Any]]:
        """Retrieve session information directly"""
        try:
            config = YesmanConfig()
            tmux_manager = TmuxManager(config)
            server = libtmux.Server()
            
            sessions_info = []
            
            # Load project configurations
            projects = tmux_manager.load_projects().get("sessions", {})
            self.logger.info(f"Loaded projects: {list(projects.keys())}")
            
            for project_name, project_conf in projects.items():
                override = project_conf.get("override", {})
                session_name = override.get("session_name", project_name)
                
                # Check if session exists
                session = server.find_where({"session_name": session_name})
                
                info = {
                    'project_name': project_name,
                    'session_name': session_name,
                    'template': project_conf.get("template_name", "N/A"),
                    'exists': session is not None,
                    'status': 'running' if session else 'stopped',
                    'windows': [],
                    'controller_status': 'unknown'
                }
                
                if session:
                    # Get window information
                    for window in session.list_windows():
                        window_info = {
                            'name': window.get('window_name'),
                            'index': window.get('window_index'),
                            'panes': []
                        }
                        
                        for pane in window.list_panes():
                            cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                            pane_info = {
                                'id': pane.get('pane_id'),
                                'command': cmd,
                                'is_claude': 'claude' in cmd.lower(),
                                'is_controller': 'controller' in cmd.lower() or 'yesman' in cmd.lower()
                            }
                            window_info['panes'].append(pane_info)
                            
                            # Update controller status
                            if pane_info['is_controller']:
                                info['controller_status'] = 'running'
                        
                        info['windows'].append(window_info)
                    
                    # If no controller found, mark as not running
                    if info['controller_status'] == 'unknown':
                        info['controller_status'] = 'not running'
                
                sessions_info.append(info)
            
            self.logger.info(f"Retrieved session info: {len(sessions_info)} sessions")
            return sessions_info
            
        except Exception as e:
            self.logger.error(f"Error getting session info: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        selected_info = self.query_one("#selected-info", Static)
        
        if button_id == "start-btn":
            selected_info.update("[green]Action: Starting controller...[/]")
        elif button_id == "stop-btn":
            selected_info.update("[red]Action: Stopping controller...[/]")
        elif button_id == "restart-btn":
            selected_info.update("[yellow]Action: Restarting session...[/]")
    
    def on_click(self, event) -> None:
        """Handle clicks on project panel to select projects"""
        # This could be enhanced to detect which project was clicked
        # For now, we'll just update the selected info
        selected_info = self.query_one("#selected-info", Static)
        if self.sessions_info:
            selected_info.update(f"[cyan]Sessions available: {len(self.sessions_info)}[/]")

    def on_key(self, event: events.Key) -> None:
        """Handle key press events"""
        if event.key == "ctrl+c":
            self.exit()
        elif event.key == "r":
            # Manual refresh
            self.refresh_data()
            selected_info = self.query_one("#selected-info", Static)
            selected_info.update("[cyan]Data refreshed![/]")
        elif event.key == "question_mark":
            # Show help
            selected_info = self.query_one("#selected-info", Static)
            selected_info.update("[yellow]Help: Use Ctrl+C to exit, R to refresh[/]")

class Dashboard:
    def __init__(self):
        self.config = YesmanConfig()
        self.tmux_manager = TmuxManager(self.config)
        self.server = libtmux.Server()
        self.logger = logging.getLogger("yesman.dashboard")
        # 파일 로깅만 사용하도록 설정 (console 핸들러 비활성화)
        self.logger.propagate = False
        log_path_str = self.config.get("log_path", "~/tmp/logs/yesman/")
        log_path = Path(os.path.expanduser(log_path_str))
        log_path.mkdir(parents=True, exist_ok=True)
        dashboard_log_file = log_path / "dashboard.log"
        file_handler = logging.FileHandler(dashboard_log_file)
        file_handler.setLevel(self.logger.level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        # libtmux 로그 출력 억제
        libtmux_logger = logging.getLogger('libtmux')
        libtmux_logger.setLevel(logging.WARNING)
        

    def get_session_info(self) -> List[Dict[str, Any]]:
        """Get information about all yesman sessions"""
        sessions_info = []
        
        # Load project configurations
        projects = self.tmux_manager.load_projects().get("sessions", {})
        
        for project_name, project_conf in projects.items():
            override = project_conf.get("override", {})
            session_name = override.get("session_name", project_name)
            
            # Check if session exists
            session = self.server.find_where({"session_name": session_name})
            
            info = {
                'project_name': project_name,
                'session_name': session_name,
                'template': project_conf.get("template_name", "N/A"),
                'exists': session is not None,
                'status': 'running' if session else 'stopped',
                'windows': [],
                'controller_status': 'unknown'
            }
            
            if session:
                # Get window information
                for window in session.list_windows():
                    window_info = {
                        'name': window.get('window_name'),
                        'index': window.get('window_index'),
                        'panes': []
                    }
                    
                    for pane in window.list_panes():
                        cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                        pane_info = {
                            'id': pane.get('pane_id'),
                            'command': cmd,
                            'is_claude': 'claude' in cmd.lower(),
                            'is_controller': 'controller' in cmd.lower() or 'yesman' in cmd.lower()
                        }
                        window_info['panes'].append(pane_info)
                        
                        # Update controller status
                        if pane_info['is_controller']:
                            info['controller_status'] = 'running'
                    
                    info['windows'].append(window_info)
                
                # If no controller found, mark as not running
                if info['controller_status'] == 'unknown':
                    info['controller_status'] = 'not running'
            
            sessions_info.append(info)
        
        return sessions_info
    
    def format_dashboard(self, sessions_info: List[Dict[str, Any]]) -> str:
        """Format session information for display"""
        output = []
        output.append("=" * 80)
        output.append(f"YESMAN DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 80)
        output.append("")
        
        # Summary
        total = len(sessions_info)
        running = sum(1 for s in sessions_info if s['status'] == 'running')
        controllers = sum(1 for s in sessions_info if s['controller_status'] == 'running')
        
        output.append(f"Total Projects: {total} | Running: {running} | Controllers Active: {controllers}")
        output.append("-" * 80)
        output.append("")
        
        # Detailed session info
        for info in sessions_info:
            status_icon = "🟢" if info['status'] == 'running' else "🔴"
            controller_icon = "🤖" if info['controller_status'] == 'running' else "❌"
            
            output.append(f"{status_icon} Project: {info['project_name']} (Session: {info['session_name']})")
            output.append(f"   Template: {info['template']}")
            output.append(f"   Controller: {controller_icon} {info['controller_status']}")
            
            if info['windows']:
                output.append(f"   Windows:")
                for window in info['windows']:
                    output.append(f"     [{window['index']}] {window['name']}")
                    for pane in window['panes']:
                        pane_type = ""
                        if pane['is_claude']:
                            pane_type = " [CLAUDE]"
                        elif pane['is_controller']:
                            pane_type = " [CONTROLLER]"
                        output.append(f"       - {pane['command']}{pane_type}")
            
            output.append("")
        
        output.append("-" * 80)
        output.append("Press Ctrl+C to exit dashboard")
        
        return "\n".join(output)
    
    def run_dashboard(self, refresh_interval: float = 2.0):
        """Run the dashboard with periodic updates using textual"""
        self.logger.info("Starting yesman dashboard")
        app = DashboardApp()
        app.run()

def run_dashboard(refresh_interval: float = 2.0):
    """Run the dashboard"""
    dashboard = Dashboard()
    dashboard.run_dashboard(refresh_interval)
