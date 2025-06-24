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

class Dashboard:
    def __init__(self):
        self.config = YesmanConfig()
        self.tmux_manager = TmuxManager(self.config)
        self.server = libtmux.Server()
        self.logger = logging.getLogger("yesman.dashboard")
        
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
        """Run the dashboard with periodic updates"""
        self.logger.info("Starting yesman dashboard")
        
        try:
            while True:
                # Clear screen
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # Get and display session information
                sessions_info = self.get_session_info()
                dashboard_text = self.format_dashboard(sessions_info)
                print(dashboard_text)
                
                # Wait before refresh
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Dashboard stopped by user")
            print("\nDashboard stopped.")
        except Exception as e:
            self.logger.error(f"Error in dashboard: {e}")
            raise

def run_dashboard():
    """Run the dashboard"""
    dashboard = Dashboard()
    dashboard.run_dashboard()