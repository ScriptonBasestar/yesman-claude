"""Streamlit main dashboard application"""

import streamlit as st
import time
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directories to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.core.session_manager import SessionManager
from libs.core.claude_manager import ClaudeManager
from libs.core.models import SessionInfo, DashboardStats


def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Yesman Claude Dashboard",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/anthropics/claude-code',
            'Report a bug': 'https://github.com/anthropics/claude-code/issues',
            'About': """
            # Yesman Claude Dashboard
            
            A Streamlit-based web dashboard for monitoring tmux sessions and Claude controllers.
            
            **Features:**
            - Real-time session monitoring
            - Controller management
            - Interactive prompt responses
            - Analytics and metrics
            """
        }
    )
    
    # Custom CSS for dark theme and styling
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    
    .metric-container {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #333;
    }
    
    .session-card {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00d4aa;
        margin-bottom: 1rem;
    }
    
    .controller-status {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
        color: white;
    }
    
    .controller-active {
        background-color: #10b981;
    }
    
    .controller-ready {
        background-color: #6b7280;
    }
    
    .stButton > button {
        width: 100%;
    }
    
    .log-entry {
        background-color: #1a1a1a;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-bottom: 0.25rem;
        font-family: monospace;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    
    if 'claude_manager' not in st.session_state:
        st.session_state.claude_manager = ClaudeManager()
    
    if 'selected_session' not in st.session_state:
        st.session_state.selected_session = None
    
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 2
    
    if 'activity_logs' not in st.session_state:
        st.session_state.activity_logs = []


def add_activity_log(level: str, message: str):
    """Add activity log entry"""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    
    st.session_state.activity_logs.append(log_entry)
    
    # Keep only last 50 logs
    if len(st.session_state.activity_logs) > 50:
        st.session_state.activity_logs = st.session_state.activity_logs[-50:]


def render_header():
    """Render the dashboard header with metrics"""
    st.title("🚀 Yesman Claude Dashboard")
    
    # Get session data
    try:
        sessions = st.session_state.session_manager.get_all_sessions()
        stats = DashboardStats.from_sessions(sessions)
        
        # Metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Sessions", stats.total_sessions)
        
        with col2:
            st.metric("Running Sessions", stats.running_sessions, 
                     delta=stats.running_sessions - (stats.total_sessions - stats.running_sessions))
        
        with col3:
            # Get real-time controller count
            active_controllers = 0
            for session in sessions:
                try:
                    controller = st.session_state.claude_manager.get_controller(session.session_name)
                    if controller and controller.is_running:
                        active_controllers += 1
                except Exception:
                    pass
            
            st.metric("Active Controllers", active_controllers)
        
        with col4:
            current_time = time.strftime("%H:%M:%S")
            st.metric("Last Update", current_time)
        
        with col5:
            if st.button("🔄 Refresh Now"):
                st.rerun()
        
        return sessions, stats
        
    except Exception as e:
        st.error(f"Error loading sessions: {e}")
        add_activity_log("error", f"Failed to load sessions: {e}")
        return [], DashboardStats(0, 0, 0)


def render_session_card(session: SessionInfo):
    """Render a session card"""
    # Session status icon
    status_icon = "🟢" if session.status == "running" else "🔴"
    
    # Controller status
    controller_status = "Unknown"
    controller_class = "controller-ready"
    
    try:
        controller = st.session_state.claude_manager.get_controller(session.session_name)
        if controller and controller.is_running:
            controller_status = "Active"
            controller_class = "controller-active"
        else:
            controller_status = "Ready"
            controller_class = "controller-ready"
    except Exception:
        pass
    
    with st.container():
        st.markdown(f"""
        <div class="session-card">
            <h4>{status_icon} {session.project_name} ({session.session_name})</h4>
            <p><strong>Template:</strong> {session.template}</p>
            <p><strong>Status:</strong> {session.status}</p>
            <p><strong>Windows:</strong> {len(session.windows)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Controller controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"🎮 Controller: {controller_status}", 
                        key=f"controller_{session.session_name}",
                        help="Click to toggle controller"):
                toggle_controller(session.session_name, controller_status)
        
        with col2:
            if st.button("📋 Select", key=f"select_{session.session_name}"):
                st.session_state.selected_session = session.session_name
                add_activity_log("info", f"Selected session: {session.session_name}")
                st.rerun()


def toggle_controller(session_name: str, current_status: str):
    """Toggle controller for a session"""
    try:
        controller = st.session_state.claude_manager.get_controller(session_name)
        if not controller:
            st.error(f"Controller not found for session: {session_name}")
            return
        
        if current_status == "Active":
            success = controller.stop()
            action = "stopped"
        else:
            success = controller.start()
            action = "started"
        
        if success:
            st.success(f"Controller {action} for {session_name}")
            add_activity_log("success", f"Controller {action} for {session_name}")
        else:
            st.error(f"Failed to {action.replace('ped', '')} controller for {session_name}")
            add_activity_log("error", f"Failed to {action.replace('ped', '')} controller for {session_name}")
        
        time.sleep(0.5)  # Brief pause for user feedback
        st.rerun()
        
    except Exception as e:
        st.error(f"Error toggling controller: {e}")
        add_activity_log("error", f"Error toggling controller: {e}")


def render_main_content():
    """Render the main content area"""
    sessions, stats = render_header()
    
    if not sessions:
        st.warning("No sessions found. Run `./yesman.py setup` to create sessions.")
        return
    
    # Session grid
    st.subheader("📊 Tmux Sessions")
    
    # Create columns for session cards
    cols_per_row = 2
    for i in range(0, len(sessions), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, session in enumerate(sessions[i:i+cols_per_row]):
            with cols[j]:
                render_session_card(session)


def render_controller_sidebar():
    """Render the controller control sidebar"""
    st.sidebar.title("🎮 Controller Operations")
    
    # Session selection
    sessions = st.session_state.session_manager.get_all_sessions()
    session_names = [s.session_name for s in sessions]
    
    if not session_names:
        st.sidebar.warning("No sessions available")
        return
    
    # Select session
    if st.session_state.selected_session not in session_names:
        st.session_state.selected_session = session_names[0] if session_names else None
    
    selected_session = st.sidebar.selectbox(
        "Select Session",
        session_names,
        index=session_names.index(st.session_state.selected_session) if st.session_state.selected_session in session_names else 0,
        key="session_selector"
    )
    
    if selected_session != st.session_state.selected_session:
        st.session_state.selected_session = selected_session
        st.rerun()
    
    if not selected_session:
        return
    
    st.sidebar.divider()
    
    # Get controller for selected session
    try:
        controller = st.session_state.claude_manager.get_controller(selected_session)
        if not controller:
            st.sidebar.error("Controller not available")
            return
        
        # Controller status
        status = "Active" if controller.is_running else "Ready"
        st.sidebar.markdown(f"**Status:** {status}")
        
        # Control buttons
        st.sidebar.subheader("Actions")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("▶️ Start", disabled=controller.is_running):
                if controller.start():
                    st.success("Controller started")
                    add_activity_log("success", f"Controller started for {selected_session}")
                else:
                    st.error("Failed to start controller")
                    add_activity_log("error", f"Failed to start controller for {selected_session}")
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop", disabled=not controller.is_running):
                if controller.stop():
                    st.success("Controller stopped")
                    add_activity_log("success", f"Controller stopped for {selected_session}")
                else:
                    st.error("Failed to stop controller")
                    add_activity_log("error", f"Failed to stop controller for {selected_session}")
                st.rerun()
        
        if st.sidebar.button("🔄 Restart Claude"):
            if controller.restart_claude_pane():
                st.success("Claude pane restarted")
                add_activity_log("success", f"Claude pane restarted for {selected_session}")
            else:
                st.error("Failed to restart Claude pane")
                add_activity_log("error", f"Failed to restart Claude pane for {selected_session}")
            st.rerun()
        
        st.sidebar.divider()
        
        # Model selection
        st.sidebar.subheader("Model")
        model = st.sidebar.selectbox(
            "Select Model",
            ["default", "opus", "sonnet"],
            index=["default", "opus", "sonnet"].index(controller.selected_model),
            key="model_selector"
        )
        
        if model != controller.selected_model:
            controller.set_model(model)
            add_activity_log("info", f"Model set to {model} for {selected_session}")
            st.rerun()
        
        # Auto next setting
        auto_next = st.sidebar.checkbox(
            "Auto Next",
            value=controller.is_auto_next_enabled,
            key="auto_next_checkbox"
        )
        
        if auto_next != controller.is_auto_next_enabled:
            controller.set_auto_next(auto_next)
            add_activity_log("info", f"Auto next {'enabled' if auto_next else 'disabled'} for {selected_session}")
            st.rerun()
        
        st.sidebar.divider()
        
        # Prompt handling
        if controller.is_waiting_for_input():
            st.sidebar.subheader("⏳ Waiting for Input")
            prompt_info = controller.get_current_prompt()
            
            if prompt_info:
                st.sidebar.write(f"**Type:** {prompt_info.type.value}")
                st.sidebar.write(f"**Question:** {prompt_info.question}")
                
                if prompt_info.options:
                    st.sidebar.write("**Options:**")
                    for i, option in enumerate(prompt_info.options):
                        st.sidebar.write(f"[{i+1}] {option}")
                
                # Response input
                response = st.sidebar.text_input("Your Response:", key="prompt_response")
                
                if st.sidebar.button("📤 Send Response"):
                    if response.strip():
                        controller.send_input(response)
                        controller.clear_prompt_state()
                        add_activity_log("success", f"Response sent: {response}")
                        st.rerun()
                    else:
                        st.sidebar.error("Please enter a response")
        
        # Collection stats
        try:
            stats = controller.get_collection_stats()
            if stats.get('total_files', 0) > 0:
                st.sidebar.subheader("📁 Collection Stats")
                st.sidebar.write(f"**Files:** {stats.get('total_files', 0)}")
                st.sidebar.write(f"**Size:** {stats.get('total_size_mb', 0):.1f} MB")
        except Exception:
            pass
        
    except Exception as e:
        st.sidebar.error(f"Error: {e}")
        add_activity_log("error", f"Controller error: {e}")


def render_activity_logs():
    """Render activity logs"""
    st.subheader("📋 Activity Logs")
    
    # Log controls
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🗑️ Clear Logs"):
            st.session_state.activity_logs = []
            add_activity_log("info", "Logs cleared")
            st.rerun()
    
    # Display logs
    if not st.session_state.activity_logs:
        st.info("No activity logs yet")
    else:
        # Show logs in reverse order (newest first)
        log_container = st.container()
        
        with log_container:
            for log in reversed(st.session_state.activity_logs[-10:]):  # Show last 10 logs
                level_color = {
                    'info': '#3b82f6',
                    'success': '#10b981', 
                    'warning': '#f59e0b',
                    'error': '#ef4444'
                }.get(log['level'], '#6b7280')
                
                st.markdown(f"""
                <div class="log-entry" style="border-left: 3px solid {level_color};">
                    <strong>[{log['timestamp']}]</strong> {log['message']}
                </div>
                """, unsafe_allow_html=True)


def render_settings_sidebar():
    """Render settings in sidebar"""
    st.sidebar.title("⚙️ Settings")
    
    # Auto refresh setting
    auto_refresh = st.sidebar.checkbox(
        "Auto Refresh",
        value=st.session_state.auto_refresh,
        help="Automatically refresh the dashboard"
    )
    
    if auto_refresh != st.session_state.auto_refresh:
        st.session_state.auto_refresh = auto_refresh
        if auto_refresh:
            add_activity_log("info", "Auto refresh enabled")
        else:
            add_activity_log("info", "Auto refresh disabled")
    
    # Refresh interval
    if auto_refresh:
        refresh_interval = st.sidebar.slider(
            "Refresh Interval (seconds)",
            min_value=1,
            max_value=10,
            value=st.session_state.refresh_interval,
            help="How often to refresh the data"
        )
        
        if refresh_interval != st.session_state.refresh_interval:
            st.session_state.refresh_interval = refresh_interval
            add_activity_log("info", f"Refresh interval set to {refresh_interval}s")
    
    st.sidebar.divider()


def main():
    """Main dashboard application"""
    setup_page_config()
    initialize_session_state()
    
    # Add initial log
    if not st.session_state.activity_logs:
        add_activity_log("info", "Dashboard initialized")

    # Render sidebar
    render_settings_sidebar()

    # Render main content
    render_main_content()
    
    st.divider()
    
    # Render activity logs
    render_activity_logs()
    
    # Auto refresh
    if st.session_state.auto_refresh:
        time.sleep(st.session_state.refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()