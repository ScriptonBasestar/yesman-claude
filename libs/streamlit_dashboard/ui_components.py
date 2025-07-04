"""Reusable UI components for the Streamlit dashboard"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional

from ..core.models import SessionInfo, DashboardStats


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
    
    /* Hide the 'Session Details' page from the sidebar navigation */
    section[data-testid="stSidebar"] li a[href*="_Session_Details"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header(sessions: List[SessionInfo], stats: DashboardStats) -> None:
    """Render the dashboard header with metrics"""
    st.title("🚀 Yesman Claude Dashboard")
    
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


def render_session_card(session: SessionInfo, add_activity_log_func, set_action_message_func, 
                       setup_tmux_func, teardown_tmux_func) -> None:
    """Render a session as a horizontal card"""
    # Session status icon
    status_icon = "🟢" if session.status == "running" else "🔴"
    
    # Get controller info
    controller_status = "❓ Unknown"
    model = "N/A"
    
    try:
        controller = st.session_state.claude_manager.get_controller(session.session_name)
        if controller:
            if controller.is_running:
                controller_status = "🟢 Active"
            else:
                controller_status = "⚪ Ready"
            model = controller.selected_model
        else:
            controller_status = "❓ Not Available"
    except Exception:
        controller_status = "❌ Error"
    
    with st.container():
        # Create a card-like container
        st.markdown(f"""
        <div style="
            background-color: #2d2d2d;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #00d4aa;
            margin-bottom: 1rem;
        ">
            <h4 style="margin: 0 0 0.5rem 0;">{status_icon} {session.project_name} ({session.session_name})</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Main info in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.write(f"**Template:** {session.template}")
            st.write(f"**Status:** {session.status}")
            if st.button("🔍 세션 상세보기", key=f"details_{session.session_name}"):
                st.session_state.selected_session_name = session.session_name
                st.rerun()
        
        with col2:
            st.write(f"**Model:** {model}")
            st.write(f"**Controller:** {controller_status}")
        
        with col3:
            _render_session_actions(session, controller_status, add_activity_log_func, 
                                  set_action_message_func, setup_tmux_func, teardown_tmux_func)
        
        with col4:
            _render_session_settings(session, add_activity_log_func)
        
        with col5:
            _render_session_windows(session)
        
        st.divider()


def _render_session_actions(session: SessionInfo, controller_status: str, add_activity_log_func,
                           set_action_message_func, setup_tmux_func, teardown_tmux_func):
    """Render session action buttons"""
    st.write("**Actions:**")
    
    # Get controller for actions
    try:
        controller = st.session_state.claude_manager.get_controller(session.session_name)
        if controller:
            # Action buttons
            if controller.is_running:
                if st.button(f"⏹️ Stop Controller", key=f"stop_{session.session_name}"):
                    if controller.stop():
                        set_action_message_func(session.session_name, "success", "Controller stopped.")
                        add_activity_log_func("success", f"Controller stopped for {session.session_name}")
                    else:
                        set_action_message_func(session.session_name, "error", "Failed to stop controller.")
                        add_activity_log_func("error", f"Failed to stop controller for {session.session_name}")
            else:
                if st.button(f"▶️ Start Controller", key=f"start_{session.session_name}"):
                    if controller.start():
                        set_action_message_func(session.session_name, "success", "Controller started.")
                        add_activity_log_func("success", f"Controller started for {session.session_name}")
                    else:
                        set_action_message_func(session.session_name, "error", "Failed to start controller.")
                        add_activity_log_func("error", f"Failed to start controller for {session.session_name}")
            
            if st.button(f"🔄 Restart Claude", key=f"restart_{session.session_name}"):
                if controller.restart_claude_pane():
                    set_action_message_func(session.session_name, "success", "Claude pane restarted.")
                    add_activity_log_func("success", f"Claude pane restarted for {session.session_name}")
                else:
                    set_action_message_func(session.session_name, "error", "Failed to restart Claude pane.")
                    add_activity_log_func("error", f"Failed to restart Claude pane for {session.session_name}")
            
            # Setup Tmux button
            if st.button(f"🚀 Setup Tmux", key=f"setup_{session.session_name}"):
                with st.spinner("Setting up tmux sessions..."):
                    setup_tmux_func(session.session_name)

            # Teardown Tmux button
            if st.button(f"🗑️ Teardown Tmux", key=f"teardown_{session.session_name}"):
                with st.spinner("Tearing down tmux session(s)..."):
                    teardown_tmux_func(session.session_name)
        else:
            st.write("Controller not available for actions")

        # Display action messages
        _render_action_messages(session.session_name)

    except Exception as e:
        st.write(f"Error in actions: {str(e)}")


def _render_session_settings(session: SessionInfo, add_activity_log_func):
    """Render session settings controls"""
    st.write("**Settings:**")
    
    # Get controller for settings
    try:
        controller = st.session_state.claude_manager.get_controller(session.session_name)
        if controller:
            # Model selection
            models = ["default", "opus", "sonnet"]
            current_model_idx = models.index(controller.selected_model) if controller.selected_model in models else 0
            
            new_model = st.selectbox(
                "Model:",
                models,
                index=current_model_idx,
                key=f"model_{session.session_name}"
            )
            
            if new_model != controller.selected_model:
                controller.set_model(new_model)
                st.success(f"Model set to {new_model}")
                add_activity_log_func("info", f"Model set to {new_model} for {session.session_name}")
            
            # Auto next setting
            new_auto_next = st.checkbox(
                "Auto Next",
                value=controller.is_auto_next_enabled,
                key=f"auto_{session.session_name}"
            )
            
            if new_auto_next != controller.is_auto_next_enabled:
                controller.set_auto_next(new_auto_next)
                st.success(f"Auto next {'enabled' if new_auto_next else 'disabled'}")
                add_activity_log_func("info", f"Auto next {'enabled' if new_auto_next else 'disabled'} for {session.session_name}")
        else:
            st.write("Controller not available")
    except Exception as e:
        st.write(f"Settings error: {str(e)}")


def _render_session_windows(session: SessionInfo):
    """Render session windows and panes information"""
    # Windows and Panes details
    if session.windows:
        st.write("**Windows:**")
        for window in session.windows:
            st.write(f"Window [{window.index}] {window.name} ({len(window.panes)} panes)")
            for i, pane in enumerate(window.panes):
                pane_type = ""
                if pane.is_claude:
                    pane_type = " 🔵 (Claude)"
                elif pane.is_controller:
                    pane_type = " 🟡 (Controller)"
                st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;- Pane {i}: {pane.command}{pane_type}", unsafe_allow_html=True)
    else:
        st.write("**Windows:** None")


def _render_action_messages(session_name: str):
    """Render action messages for a session"""
    now = time.time()
    msg_key = f"action_msg_{session_name}"
    if msg_key in st.session_state:
        msg_state = st.session_state[msg_key]
        if now - msg_state["timestamp"] < 3:
            msg_type = msg_state["type"]
            if msg_type == "success":
                st.success(msg_state["msg"])
            elif msg_type == "error":
                st.error(msg_state["msg"])
            elif msg_type == "info":
                st.info(msg_state["msg"])
            elif msg_type == "warning":
                st.warning(msg_state["msg"])
        else:
            st.session_state.pop(msg_key, None)


def render_activity_logs(activity_logs: List[Dict[str, Any]]):
    """Render activity logs"""
    st.subheader("📋 Activity Logs")
    
    # Log controls
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🗑️ Clear Logs"):
            st.session_state.activity_logs = []
            return True  # Signal that logs were cleared
    
    # Display logs
    if not activity_logs:
        st.info("No activity logs yet")
    else:
        # Show logs in reverse order (newest first)
        log_container = st.container()
        
        with log_container:
            for log in reversed(activity_logs[-10:]):  # Show last 10 logs
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
    
    return False


def render_session_filters():
    """Render session filter controls and return filter values"""
    st.write("**🔍 Filter Sessions**")
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status:",
            ["All", "Running", "Stopped"],
            key="main_status_filter"
        )
    
    with col2:
        search_term = st.text_input(
            "Search by name:",
            key="main_search_term",
            placeholder="Enter session or project name..."
        )
    
    return status_filter, search_term


def apply_session_filters(sessions: List[SessionInfo], status_filter: str, search_term: str) -> List[SessionInfo]:
    """Apply filters to session list"""
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
    
    return filtered_sessions


def render_quick_actions(sessions: List[SessionInfo], add_activity_log_func):
    """Render quick action buttons"""
    st.subheader("🚀 Quick Actions")
    
    # First row: Refresh buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Sessions"):
            return "refresh_sessions"
    
    with col2:
        if st.button("🔄 Refresh Controllers"):
            add_activity_log_func("info", "Controllers refreshed")
            return "refresh_controllers"
    
    # Second row: Controller actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start All Controllers"):
            return "start_all"
    
    with col2:
        if st.button("⏹️ Stop All Controllers"):
            return "stop_all"
    
    with col3:
        if st.button("🔄 Restart All Claude Panes"):
            return "restart_all"
    
    return None