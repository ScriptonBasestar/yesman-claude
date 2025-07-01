"""Streamlit main dashboard application"""

import streamlit as st
import time
import logging
import sys
import os
import yaml
from pathlib import Path
from typing import Optional

# Add parent directories to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.core.session_manager import SessionManager
from libs.core.claude_manager import ClaudeManager
from libs.core.models import SessionInfo, DashboardStats
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager


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
        
        with col2:
            st.write(f"**Model:** {model}")
            st.write(f"**Controller:** {controller_status}")
        
        with col3:
            st.write("**Actions:**")
            
            # Get controller for actions
            try:
                controller = st.session_state.claude_manager.get_controller(session.session_name)
                if controller:
                    # Action buttons
                    if controller.is_running:
                        if st.button(f"⏹️ Stop Controller", key=f"stop_{session.session_name}"):
                            if controller.stop():
                                st.success("Controller stopped")
                                add_activity_log("success", f"Controller stopped for {session.session_name}")
                                st.rerun()
                            else:
                                st.error("Failed to stop controller")
                                add_activity_log("error", f"Failed to stop controller for {session.session_name}")
                    else:
                        if st.button(f"▶️ Start Controller", key=f"start_{session.session_name}"):
                            if controller.start():
                                st.success("Controller started")
                                add_activity_log("success", f"Controller started for {session.session_name}")
                                st.rerun()
                            else:
                                st.error("Failed to start controller")
                                add_activity_log("error", f"Failed to start controller for {session.session_name}")
                    
                    if st.button(f"🔄 Restart Claude", key=f"restart_{session.session_name}"):
                        if controller.restart_claude_pane():
                            st.success("Claude pane restarted")
                            add_activity_log("success", f"Claude pane restarted for {session.session_name}")
                            st.rerun()
                        else:
                            st.error("Failed to restart Claude pane")
                            add_activity_log("error", f"Failed to restart Claude pane for {session.session_name}")
                    
                    # Setup Tmux 버튼
                    if st.button(f"🚀 Setup Tmux", key=f"setup_{session.session_name}"):
                        with st.spinner("Setting up tmux sessions..."):
                            if setup_tmux_sessions(session.session_name):
                                # 메시지 상태 저장 (성공)
                                st.session_state[f"setup_msg_{session.session_name}"] = {
                                    "type": "success",
                                    "msg": "Tmux setup completed successfully",
                                    "timestamp": time.time()
                                }
                                st.rerun()
                            else:
                                st.session_state[f"setup_msg_{session.session_name}"] = {
                                    "type": "error",
                                    "msg": "Tmux setup failed or completed with errors",
                                    "timestamp": time.time()
                                }
                                st.rerun()
                    # Teardown Tmux 버튼
                    if st.button(f"🗑️ Teardown Tmux", key=f"teardown_{session.session_name}"):
                        with st.spinner("Tearing down tmux session(s)..."):
                            if teardown_tmux_sessions(session.session_name):
                                st.session_state[f"teardown_msg_{session.session_name}"] = {
                                    "type": "success",
                                    "msg": "Tmux teardown completed successfully",
                                    "timestamp": time.time()
                                }
                                st.rerun()
                            else:
                                st.session_state[f"teardown_msg_{session.session_name}"] = {
                                    "type": "error",
                                    "msg": "Tmux teardown failed or completed with errors",
                                    "timestamp": time.time()
                                }
                                st.rerun()
                    # Setup/Teardown 메시지 표시 (3초 후 자동 사라짐)
                    now = time.time()
                    setup_key = f"setup_msg_{session.session_name}"
                    teardown_key = f"teardown_msg_{session.session_name}"
                    for msg_key in [setup_key, teardown_key]:
                        msg_state = st.session_state.get(msg_key)
                        if msg_state:
                            elapsed = now - msg_state["timestamp"]
                            if elapsed < 3:
                                # 메시지 표시 (3초간)
                                if msg_state["type"] == "success":
                                    st.success(msg_state["msg"])
                                else:
                                    st.error(msg_state["msg"])
                            else:
                                st.session_state.pop(msg_key, None)
                else:
                    st.write("Controller not available")
            except Exception as e:
                st.write(f"Error: {str(e)}")
        
        with col4:
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
                        add_activity_log("info", f"Model set to {new_model} for {session.session_name}")
                        st.rerun()
                    
                    # Auto next setting
                    new_auto_next = st.checkbox(
                        "Auto Next",
                        value=controller.is_auto_next_enabled,
                        key=f"auto_{session.session_name}"
                    )
                    
                    if new_auto_next != controller.is_auto_next_enabled:
                        controller.set_auto_next(new_auto_next)
                        st.success(f"Auto next {'enabled' if new_auto_next else 'disabled'}")
                        add_activity_log("info", f"Auto next {'enabled' if new_auto_next else 'disabled'} for {session.session_name}")
                        st.rerun()
                else:
                    st.write("Controller not available")
            except Exception as e:
                st.write(f"Settings error: {str(e)}")
        
        with col5:
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
        
        st.divider()


def render_main_content():
    """Render the main content area"""
    sessions, stats = render_header()
    
    if not sessions:
        st.warning("No sessions found. Run `./yesman.py setup` to create sessions.")
        return
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    # First row: Refresh buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Sessions"):
            add_activity_log("info", "Sessions refreshed")
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Controllers"):
            add_activity_log("info", "Controllers refreshed")
            st.rerun()
    
    # Second row: Controller actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start All Controllers"):
            success_count = 0
            for session in sessions:
                try:
                    controller = st.session_state.claude_manager.get_controller(session.session_name)
                    if controller and not controller.is_running:
                        if controller.start():
                            success_count += 1
                except Exception:
                    pass
            
            if success_count > 0:
                st.success(f"Started {success_count} controllers")
                add_activity_log("success", f"Started {success_count} controllers")
                st.rerun()
            else:
                st.warning("No controllers were started")
                add_activity_log("warning", "No controllers were started")
    
    with col2:
        if st.button("⏹️ Stop All Controllers"):
            success_count = 0
            for session in sessions:
                try:
                    controller = st.session_state.claude_manager.get_controller(session.session_name)
                    if controller and controller.is_running:
                        if controller.stop():
                            success_count += 1
                except Exception:
                    pass
            
            if success_count > 0:
                st.success(f"Stopped {success_count} controllers")
                add_activity_log("success", f"Stopped {success_count} controllers")
                st.rerun()
            else:
                st.warning("No controllers were stopped")
                add_activity_log("warning", "No controllers were stopped")
    
    with col3:
        if st.button("🔄 Restart All Claude Panes"):
            success_count = 0
            for session in sessions:
                try:
                    controller = st.session_state.claude_manager.get_controller(session.session_name)
                    if controller:
                        if controller.restart_claude_pane():
                            success_count += 1
                except Exception:
                    pass
            
            if success_count > 0:
                st.success(f"Restarted {success_count} Claude panes")
                add_activity_log("success", f"Restarted {success_count} Claude panes")
                st.rerun()
            else:
                st.warning("No Claude panes were restarted")
                add_activity_log("warning", "No Claude panes were restarted")
    
    st.divider()
    
    # Sessions cards
    st.subheader("📊 Tmux Sessions")
    
    # Sessions filter section (inside Tmux Sessions)
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
    
    # Show filtered results count
    if len(filtered_sessions) != len(sessions):
        st.write(f"*Showing {len(filtered_sessions)} of {len(sessions)} sessions*")
    
    st.divider()
    
    if not filtered_sessions:
        st.info("No sessions match the current filters.")
        return
    
    # Display each filtered session as a horizontal card
    for session in filtered_sessions:
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


def setup_tmux_sessions(session_name=None):
    """Setup tmux sessions based on projects.yaml configuration"""
    try:
        config = YesmanConfig()
        tmux_manager = TmuxManager(config)
        sessions = tmux_manager.load_projects().get("sessions", {})
        
        if not sessions:
            st.error("No sessions defined in projects.yaml")
            return False
        
        # If a specific session is provided, only set up that session
        if session_name:
            if session_name not in sessions:
                st.error(f"Session {session_name} not defined in projects.yaml")
                return False
            sessions = {session_name: sessions[session_name]}
        
        success_count = 0
        error_count = 0
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_sessions = len(sessions)
        
        for i, (sess_name, sess_conf) in enumerate(sessions.items()):
            status_text.text(f"Setting up session: {sess_name}")
            progress_bar.progress((i + 1) / total_sessions)
            
            try:
                template_name = sess_conf.get("template_name")
                template_conf = {}

                if template_name:
                    template_file = tmux_manager.templates_path / f"{template_name}.yaml"
                    if template_file.is_file():
                        with open(template_file, "r", encoding="utf-8") as tf:
                            template_conf = yaml.safe_load(tf) or {}
                    else:
                        st.warning(f"Template file not found: {template_file}")

                # Prepare configuration
                override_conf = sess_conf.get("override", {})
                config_dict = template_conf.copy()
                config_dict["session_name"] = override_conf.get("session_name", sess_name)
                config_dict["start_directory"] = override_conf.get("start_directory", os.getcwd())
                
                # Apply all overrides
                for key, value in override_conf.items():
                    config_dict[key] = value

                # Validate start_directory
                start_dir = config_dict.get("start_directory")
                if start_dir:
                    expanded_dir = os.path.expanduser(start_dir)
                    if not os.path.exists(expanded_dir):
                        try:
                            os.makedirs(expanded_dir, exist_ok=True)
                            st.info(f"Created directory: {expanded_dir}")
                        except Exception as e:
                            st.error(f"Failed to create directory {expanded_dir}: {e}")
                            error_count += 1
                            continue
                    config_dict["start_directory"] = expanded_dir

                # Validate window directories
                windows = config_dict.get("windows", [])
                validation_failed = False
                for window in windows:
                    window_start_dir = window.get("start_directory")
                    if window_start_dir:
                        if not os.path.isabs(window_start_dir):
                            base_dir = config_dict.get("start_directory", os.getcwd())
                            window_start_dir = os.path.join(base_dir, window_start_dir)
                        
                        expanded_window_dir = os.path.expanduser(window_start_dir)
                        if not os.path.exists(expanded_window_dir):
                            try:
                                os.makedirs(expanded_window_dir, exist_ok=True)
                            except Exception as e:
                                st.error(f"Failed to create window directory {expanded_window_dir}: {e}")
                                validation_failed = True
                                break
                        window["start_directory"] = expanded_window_dir

                if validation_failed:
                    error_count += 1
                    continue

                # Create tmux session
                if tmux_manager.create_session(sess_name, config_dict):
                    st.success(f"Created session: {sess_name}")
                    success_count += 1
                else:
                    st.warning(f"Session {sess_name} already exists or failed to create")
                    error_count += 1

            except Exception as e:
                st.error(f"Error setting up {sess_name}: {e}")
                error_count += 1

        status_text.text("Setup completed!")
        
        if success_count > 0:
            session_text = f"session {session_name}" if session_name else f"{success_count} sessions"
            add_activity_log("success", f"Setup completed: {session_text} created, {error_count} errors")
            return True
        else:
            add_activity_log("warning", f"Setup completed with {error_count} errors")
            return False
            
    except Exception as e:
        st.error(f"Setup failed: {e}")
        add_activity_log("error", f"Setup failed: {e}")
        return False


def teardown_tmux_sessions(session_name=None):
    """Teardown (kill) tmux sessions based on projects.yaml configuration"""
    try:
        config = YesmanConfig()
        tmux_manager = TmuxManager(config)
        sessions = tmux_manager.load_projects().get("sessions", {})
        if not sessions:
            st.error("No sessions defined in projects.yaml")
            return False
        # 특정 세션만 지정된 경우
        if session_name:
            if session_name not in sessions:
                st.error(f"Session {session_name} not defined in projects.yaml")
                return False
            sessions = {session_name: sessions[session_name]}
        import libtmux
        import subprocess
        server = libtmux.Server()
        success_count = 0
        error_count = 0
        for sess_name, sess_conf in sessions.items():
            override_conf = sess_conf.get("override", {})
            actual_session_name = override_conf.get("session_name", sess_name)
            if server.find_where({"session_name": actual_session_name}):
                try:
                    subprocess.run(["tmux", "kill-session", "-t", actual_session_name], check=True)
                    st.success(f"Killed session: {actual_session_name}")
                    success_count += 1
                except Exception as e:
                    st.error(f"Failed to kill session {actual_session_name}: {e}")
                    error_count += 1
            else:
                st.info(f"Session {actual_session_name} not found")
        if success_count > 0:
            add_activity_log("success", f"Teardown completed: {success_count} session(s) killed, {error_count} errors")
            return True
        else:
            add_activity_log("warning", f"Teardown completed with {error_count} errors")
            return False
    except Exception as e:
        st.error(f"Teardown failed: {e}")
        add_activity_log("error", f"Teardown failed: {e}")
        return False


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