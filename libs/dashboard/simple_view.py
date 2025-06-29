"""Simple fallback view for incompatible terminals"""

import time
import sys
from typing import Optional
from .session_manager import SessionManager
from .models import DashboardStats


class SimpleDashboardView:
    """Simple text-based dashboard for incompatible terminals"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.running = True
        
    def clear_screen(self):
        """Clear screen in a portable way"""
        print("\033[2J\033[H", end="")
        
    def display_header(self):
        """Display dashboard header"""
        print("=" * 60)
        print("  Yesman Dashboard - Simple View Mode")
        print("=" * 60)
        print()
        
    def display_sessions(self):
        """Display tmux session information"""
        try:
            sessions = self.session_manager.get_all_sessions()
            stats = DashboardStats.from_sessions(sessions)
            
            print(f"Total Sessions: {stats.total_sessions}")
            print(f"Active Sessions: {stats.active_sessions}")
            print(f"Claude Instances: {stats.claude_instances}")
            print()
            
            for session in sessions:
                status = "✓" if session.is_active else "✗"
                print(f"[{status}] {session.session_name} - {session.project_type}")
                
                for window in session.windows:
                    print(f"    └─ {window.name} ({len(window.panes)} panes)")
                    for pane in window.panes:
                        pane_type = pane.pane_type or "unknown"
                        print(f"        └─ {pane_type}")
                print()
                
        except Exception as e:
            print(f"Error loading sessions: {e}")
            
    def display_footer(self):
        """Display footer with instructions"""
        print("-" * 60)
        print("Press Ctrl+C to exit | Refreshes every 2 seconds")
        
    def run(self):
        """Run the simple dashboard loop"""
        try:
            while self.running:
                self.clear_screen()
                self.display_header()
                self.display_sessions()
                self.display_footer()
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nExiting dashboard...")
            sys.exit(0)


def run_simple_dashboard():
    """Entry point for simple dashboard"""
    dashboard = SimpleDashboardView()
    dashboard.run()