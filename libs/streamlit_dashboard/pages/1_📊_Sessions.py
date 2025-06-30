"""Session management page"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from libs.dashboard.session_manager import SessionManager
from libs.dashboard.claude_manager import ClaudeManager

st.set_page_config(
    page_title="Session Management",
    page_icon="📊",
    layout="wide"
)

def initialize_managers():
    """Initialize session state managers"""
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    
    if 'claude_manager' not in st.session_state:
        st.session_state.claude_manager = ClaudeManager()

def render_session_details(session):
    """Render detailed session information"""
    st.subheader(f"📋 {session.project_name} ({session.session_name})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Template:** {session.template}")
        st.write(f"**Status:** {'🟢 Running' if session.status == 'running' else '🔴 Stopped'}")
        st.write(f"**Total Windows:** {len(session.windows)}")
    
    with col2:
        # Controller info
        try:
            controller = st.session_state.claude_manager.get_controller(session.session_name)
            if controller:
                controller_status = "🟢 Active" if controller.is_running else "⚪ Ready"
                st.write(f"**Controller:** {controller_status}")
                st.write(f"**Model:** {controller.selected_model}")
                st.write(f"**Auto Next:** {'✅ Enabled' if controller.is_auto_next_enabled else '❌ Disabled'}")
            else:
                st.write("**Controller:** ❓ Not Available")
        except Exception as e:
            st.write(f"**Controller:** ❌ Error: {e}")
    
    # Windows details
    if session.windows:
        st.write("**Windows:**")
        for window in session.windows:
            with st.expander(f"Window [{window.index}] {window.name} ({len(window.panes)} panes)"):
                for i, pane in enumerate(window.panes):
                    pane_type = ""
                    if pane.is_claude:
                        pane_type = " 🔵 (Claude)"
                    elif pane.is_controller:
                        pane_type = " 🟡 (Controller)"
                    
                    st.write(f"• Pane {i}: {pane.command}{pane_type}")
    else:
        st.write("**Windows:** None")
    
    st.divider()

def main():
    """Main sessions page"""
    initialize_managers()
    
    st.title("📊 Session Management")
    st.write("Detailed view of all tmux sessions and their status")
    
    # Refresh button
    if st.button("🔄 Refresh Sessions"):
        st.rerun()
    
    try:
        sessions = st.session_state.session_manager.get_all_sessions()
        
        if not sessions:
            st.warning("No sessions found. Run `./yesman.py setup` to create sessions.")
            st.stop()
        
        # Session filter
        st.subheader("Filter Sessions")
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status:",
                ["All", "Running", "Stopped"]
            )
        
        with col2:
            search_term = st.text_input("Search by name:")
        
        # Apply filters
        filtered_sessions = sessions
        
        if status_filter != "All":
            target_status = "running" if status_filter == "Running" else "stopped"
            filtered_sessions = [s for s in filtered_sessions if s.status == target_status]
        
        if search_term:
            filtered_sessions = [
                s for s in filtered_sessions 
                if search_term.lower() in s.session_name.lower() or 
                   search_term.lower() in s.project_name.lower()
            ]
        
        st.divider()
        
        # Session list
        st.subheader(f"Sessions ({len(filtered_sessions)} of {len(sessions)})")
        
        if not filtered_sessions:
            st.info("No sessions match the current filters.")
        else:
            for session in filtered_sessions:
                render_session_details(session)
    
    except Exception as e:
        st.error(f"Error loading sessions: {e}")

if __name__ == "__main__":
    main()