"""Dashboard layout and page organization components"""

import streamlit as st
import time
from typing import List, Optional

from ..core.models import SessionInfo, DashboardStats
from .ui_components import (
    render_header, render_session_card, render_activity_logs, 
    render_session_filters, apply_session_filters, render_quick_actions
)


def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'session_manager' not in st.session_state:
        from ..core.session_manager import SessionManager
        st.session_state.session_manager = SessionManager()
    
    if 'claude_manager' not in st.session_state:
        from ..core.claude_manager import ClaudeManager
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


def invalidate_session_cache(session_name: str = None, reason: str = "manual"):
    """
    Smart cache invalidation with logging
    
    Args:
        session_name: Specific session to invalidate, or None for all
        reason: Reason for invalidation (for logging)
    """
    try:
        if session_name:
            # Invalidate specific session
            st.session_state.session_manager.invalidate_cache(session_name)
            add_activity_log("info", f"Cache invalidated for {session_name} ({reason})")
        else:
            # Invalidate all sessions
            st.session_state.session_manager.invalidate_cache()
            add_activity_log("info", f"All cache invalidated ({reason})")
    except Exception as e:
        add_activity_log("error", f"Cache invalidation failed: {e}")


def get_sessions_with_cache_optimization():
    """
    Get sessions with optimized caching and preloading
    
    Returns:
        List of SessionInfo objects
    """
    try:
        # Check if we need to preload cache
        cache_stats = st.session_state.session_manager.get_cache_stats()
        
        # If cache is empty or has low hit rate, we might want to preload
        if cache_stats['total_entries'] == 0 or cache_stats['hit_rate'] < 50:
            add_activity_log("info", "Preloading session cache...")
        
        # Get sessions with timing
        start_time = time.time()
        sessions = st.session_state.session_manager.get_all_sessions()
        query_time = time.time() - start_time
        
        # Log performance if slow
        if query_time > 1.0:
            add_activity_log("warning", f"Slow session query: {query_time:.3f}s")
        
        return sessions
        
    except Exception as e:
        add_activity_log("error", f"Failed to get sessions: {e}")
        return []


def render_main_content():
    """Render the main content area"""
    # Get session data with optimized caching
    try:
        sessions = get_sessions_with_cache_optimization()
        stats = DashboardStats.from_sessions(sessions)
        
        # Render header with metrics
        render_header(sessions, stats)
        
        if not sessions:
            st.warning("No sessions found. Run `./yesman.py setup` to create sessions.")
            return
        
        # Handle quick actions
        from .session_actions import handle_bulk_actions, set_action_message
        action_result = render_quick_actions(sessions, add_activity_log)
        if action_result:
            handle_bulk_actions(action_result, sessions, add_activity_log)
            st.rerun()
        
        st.divider()
        
        # Sessions cards
        st.subheader("📊 Tmux Sessions")
        
        # Filter sessions
        status_filter, search_term = render_session_filters()
        filtered_sessions = apply_session_filters(sessions, status_filter, search_term)
        
        # Show filtered results count
        if len(filtered_sessions) != len(sessions):
            st.write(f"*Showing {len(filtered_sessions)} of {len(sessions)} sessions*")
        
        st.divider()
        
        if not filtered_sessions:
            st.info("No sessions match the current filters.")
            return
        
        # Display each filtered session as a horizontal card
        from .session_actions import setup_tmux_sessions, teardown_tmux_sessions
        for session in filtered_sessions:
            render_session_card(
                session, 
                add_activity_log, 
                set_action_message,
                setup_tmux_sessions,
                teardown_tmux_sessions
            )
        
    except Exception as e:
        st.error(f"Error loading sessions: {e}")
        add_activity_log("error", f"Failed to load sessions: {e}")


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
    
    # Cache statistics
    st.sidebar.subheader("📊 Cache Statistics")
    try:
        cache_stats = st.session_state.session_manager.get_cache_stats()
        
        # Performance indicator color
        hit_rate = cache_stats['hit_rate']
        if hit_rate >= 80:
            hit_rate_color = "🟢"
        elif hit_rate >= 60:
            hit_rate_color = "🟡"
        else:
            hit_rate_color = "🔴"
        
        st.sidebar.metric(
            f"{hit_rate_color} Hit Rate",
            f"{hit_rate:.1f}%",
            help="Percentage of requests served from cache (🟢>80%, 🟡>60%, 🔴<60%)"
        )
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Hits", cache_stats['hits'])
            st.metric("Entries", cache_stats['total_entries'])
        
        with col2:
            st.metric("Misses", cache_stats['misses'])
            st.metric("Evictions", cache_stats['evictions'])
        
        # Memory usage in KB
        memory_kb = cache_stats['memory_size_bytes'] / 1024
        st.sidebar.metric(
            "Memory",
            f"{memory_kb:.1f} KB",
            help="Estimated cache memory usage"
        )
        
        # Cache efficiency info
        total_requests = cache_stats['hits'] + cache_stats['misses']
        if total_requests > 0:
            efficiency = f"Efficiency: {cache_stats['hits']}/{total_requests} requests cached"
            st.sidebar.caption(efficiency)
        
        # Cache controls
        if st.sidebar.button("🗑️ Clear Cache", help="Clear all cached session data"):
            invalidate_session_cache(reason="manual clear")
            st.rerun()
            
    except Exception as e:
        st.sidebar.error(f"Cache stats error: {e}")
    
    st.sidebar.divider()