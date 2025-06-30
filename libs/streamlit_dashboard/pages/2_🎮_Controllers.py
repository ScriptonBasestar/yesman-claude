"""Controller management page"""

import streamlit as st
import sys
from pathlib import Path
import time

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from libs.dashboard.session_manager import SessionManager
from libs.dashboard.claude_manager import ClaudeManager

st.set_page_config(
    page_title="Controller Management",
    page_icon="🎮",
    layout="wide"
)

def initialize_managers():
    """Initialize session state managers"""
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    
    if 'claude_manager' not in st.session_state:
        st.session_state.claude_manager = ClaudeManager()

def render_controller_card(session):
    """Render controller management card for a session"""
    try:
        controller = st.session_state.claude_manager.get_controller(session.session_name)
        if not controller:
            st.warning(f"Controller not available for {session.session_name}")
            return
        
        # Controller header
        status_icon = "🟢" if controller.is_running else "⚪"
        status_text = "Active" if controller.is_running else "Ready"
        
        st.subheader(f"{status_icon} {session.project_name} ({session.session_name})")
        
        col1, col2, col3 = st.columns(3)
        
        # Status and basic info
        with col1:
            st.write(f"**Status:** {status_text}")
            st.write(f"**Model:** {controller.selected_model}")
            st.write(f"**Auto Next:** {'✅' if controller.is_auto_next_enabled else '❌'}")
        
        # Action buttons
        with col2:
            st.write("**Actions:**")
            
            if controller.is_running:
                if st.button(f"⏹️ Stop", key=f"stop_{session.session_name}"):
                    if controller.stop():
                        st.success("Controller stopped")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to stop controller")
            else:
                if st.button(f"▶️ Start", key=f"start_{session.session_name}"):
                    if controller.start():
                        st.success("Controller started")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to start controller")
            
            if st.button(f"🔄 Restart Claude", key=f"restart_{session.session_name}"):
                if controller.restart_claude_pane():
                    st.success("Claude pane restarted")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to restart Claude pane")
        
        # Settings
        with col3:
            st.write("**Settings:**")
            
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
                time.sleep(0.5)
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
                time.sleep(0.5)
                st.rerun()
        
        # Prompt handling
        if controller.is_waiting_for_input():
            st.warning("⏳ Controller is waiting for input")
            
            prompt_info = controller.get_current_prompt()
            if prompt_info:
                st.write(f"**Question:** {prompt_info.question}")
                
                if prompt_info.options:
                    st.write("**Options:**")
                    for i, option in enumerate(prompt_info.options):
                        st.write(f"  [{i+1}] {option}")
                
                # Response input
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    response = st.text_input(
                        "Your response:",
                        key=f"response_{session.session_name}"
                    )
                
                with col2:
                    st.write("")  # Spacing
                    if st.button("📤 Send", key=f"send_{session.session_name}"):
                        if response.strip():
                            controller.send_input(response)
                            controller.clear_prompt_state()
                            st.success(f"Response sent: {response}")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Please enter a response")
        
        # Collection stats
        try:
            stats = controller.get_collection_stats()
            if stats.get('total_files', 0) > 0:
                st.info(f"📁 Collected {stats.get('total_files', 0)} files ({stats.get('total_size_mb', 0):.1f} MB)")
        except Exception:
            pass
        
        # Response history (if available)
        try:
            history = controller.get_response_history()
            if history:
                with st.expander(f"📜 Response History ({len(history)} entries)"):
                    for entry in history[-5:]:  # Show last 5 entries
                        st.write(f"**{entry['timestamp']}** - {entry['prompt_type']}: {entry['response']}")
        except Exception:
            pass
        
        st.divider()
        
    except Exception as e:
        st.error(f"Error managing controller for {session.session_name}: {e}")

def main():
    """Main controllers page"""
    initialize_managers()
    
    st.title("🎮 Controller Management")
    st.write("Manage Claude controllers for all sessions")
    
    # Refresh button
    if st.button("🔄 Refresh Controllers"):
        st.rerun()
    
    try:
        sessions = st.session_state.session_manager.get_all_sessions()
        
        if not sessions:
            st.warning("No sessions found. Run `./yesman.py setup` to create sessions.")
            st.stop()
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        
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
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("No controllers were started")
        
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
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("No controllers were stopped")
        
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
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("No Claude panes were restarted")
        
        st.divider()
        
        # Controller cards
        st.subheader("📋 Individual Controllers")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Controller Status:",
                ["All", "Active", "Ready", "No Controller"]
            )
        
        with col2:
            show_waiting_only = st.checkbox("Show only controllers waiting for input")
        
        # Apply filters
        filtered_sessions = []
        
        for session in sessions:
            try:
                controller = st.session_state.claude_manager.get_controller(session.session_name)
                
                # Status filter
                if status_filter == "Active" and (not controller or not controller.is_running):
                    continue
                elif status_filter == "Ready" and (not controller or controller.is_running):
                    continue
                elif status_filter == "No Controller" and controller:
                    continue
                
                # Waiting for input filter
                if show_waiting_only and (not controller or not controller.is_waiting_for_input()):
                    continue
                
                filtered_sessions.append(session)
                
            except Exception:
                if status_filter == "No Controller":
                    filtered_sessions.append(session)
        
        if not filtered_sessions:
            st.info("No sessions match the current filters.")
        else:
            for session in filtered_sessions:
                render_controller_card(session)
    
    except Exception as e:
        st.error(f"Error loading controllers: {e}")

if __name__ == "__main__":
    main()