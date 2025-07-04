"""Streamlit main dashboard application

This module has been refactored for better maintainability.
The dashboard is now composed of specialized components:
- UI Components: Reusable UI elements and widgets
- Dashboard Layout: Page layout and organization
- Session Actions: Session and controller action handlers

For backward compatibility, this module provides the main entry point.
"""

import streamlit as st
import time
import sys
from pathlib import Path

# Add parent directories to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .ui_components import setup_page_config, render_activity_logs
from .dashboard_layout import (
    initialize_session_state, add_activity_log, 
    render_main_content, render_settings_sidebar
)


def main():
    """Main dashboard application"""
    setup_page_config()
    initialize_session_state()

    # Redirect to details page if a session was selected
    if st.session_state.get("selected_session_name"):
        st.switch_page("pages/_Session_Details.py")

    # Get action message if any
    action_message = st.session_state.get('action_message', {})

    # Add initial log
    if not st.session_state.activity_logs:
        add_activity_log("info", "Dashboard initialized")

    # Render sidebar
    render_settings_sidebar()

    # Render main content
    render_main_content()
    
    st.divider()
    
    # Render activity logs
    logs_cleared = render_activity_logs(st.session_state.activity_logs)
    if logs_cleared:
        add_activity_log("info", "Logs cleared")
        st.rerun()
    
    # Auto refresh
    if st.session_state.auto_refresh:
        time.sleep(st.session_state.refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()