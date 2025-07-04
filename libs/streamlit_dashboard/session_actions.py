"""Session action handlers for tmux and controller operations"""

import streamlit as st
import time
import os
import yaml
import subprocess
from typing import List, Optional
from pathlib import Path

from ..core.models import SessionInfo
from ..yesman_config import YesmanConfig
from ..tmux_manager import TmuxManager


def set_action_message(session_name: str, msg_type: str, message: str):
    """Helper function to set action messages in session_state."""
    st.session_state[f"action_msg_{session_name}"] = {
        "type": msg_type,
        "msg": message,
        "timestamp": time.time()
    }


def handle_bulk_actions(action_type: str, sessions: List[SessionInfo], add_activity_log_func):
    """Handle bulk controller actions"""
    success_count = 0
    
    if action_type == "refresh_sessions":
        from .dashboard_layout import invalidate_session_cache
        invalidate_session_cache(reason="user refresh")
        return
    
    elif action_type == "refresh_controllers":
        # Controllers are refreshed automatically on rerun
        return
    
    elif action_type == "start_all":
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
            add_activity_log_func("success", f"Started {success_count} controllers")
        else:
            st.warning("No controllers were started")
            add_activity_log_func("warning", "No controllers were started")
    
    elif action_type == "stop_all":
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
            add_activity_log_func("success", f"Stopped {success_count} controllers")
        else:
            st.warning("No controllers were stopped")
            add_activity_log_func("warning", "No controllers were stopped")
    
    elif action_type == "restart_all":
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
            add_activity_log_func("success", f"Restarted {success_count} Claude panes")
        else:
            st.warning("No Claude panes were restarted")
            add_activity_log_func("warning", "No Claude panes were restarted")


def setup_tmux_sessions(session_name: Optional[str] = None) -> bool:
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
                    set_action_message(sess_name, "success", f"Created session: {sess_name}")
                    success_count += 1
                else:
                    set_action_message(sess_name, "warning", f"Session {sess_name} already exists or failed.")
                    error_count += 1

            except Exception as e:
                st.error(f"Error setting up {sess_name}: {e}")
                error_count += 1

        status_text.text("Setup completed!")
        
        if success_count > 0:
            session_text = f"session {session_name}" if session_name else f"{success_count} sessions"
            from .dashboard_layout import add_activity_log, invalidate_session_cache
            add_activity_log("success", f"Setup completed: {session_text} created, {error_count} errors")
            # Invalidate cache after successful setup
            invalidate_session_cache(session_name, "tmux setup")
            return True
        else:
            from .dashboard_layout import add_activity_log
            add_activity_log("warning", f"Setup completed with {error_count} errors")
            return False
            
    except Exception as e:
        st.error(f"Setup failed: {e}")
        from .dashboard_layout import add_activity_log
        add_activity_log("error", f"Setup failed: {e}")
        return False


def teardown_tmux_sessions(session_name: Optional[str] = None) -> bool:
    """Teardown (kill) tmux sessions based on projects.yaml configuration"""
    try:
        config = YesmanConfig()
        tmux_manager = TmuxManager(config)
        sessions = tmux_manager.load_projects().get("sessions", {})
        if not sessions:
            # session_state에 오류 메시지 저장
            if session_name:
                st.session_state[f"teardown_msg_{session_name}"] = {
                    "type": "error",
                    "msg": "No sessions defined in projects.yaml",
                    "timestamp": time.time()
                }
            return False
        
        # 특정 세션만 지정된 경우
        if session_name:
            if session_name not in sessions:
                st.session_state[f"teardown_msg_{session_name}"] = {
                    "type": "error",
                    "msg": f"Session {session_name} not defined in projects.yaml",
                    "timestamp": time.time()
                }
                return False
            sessions = {session_name: sessions[session_name]}
        
        import libtmux
        server = libtmux.Server()
        success_count = 0
        error_count = 0
        
        for sess_name, sess_conf in sessions.items():
            override_conf = sess_conf.get("override", {})
            actual_session_name = override_conf.get("session_name", sess_name)
            if server.find_where({"session_name": actual_session_name}):
                try:
                    subprocess.run(["tmux", "kill-session", "-t", actual_session_name], check=True)
                    set_action_message(sess_name, "success", f"Killed session: {actual_session_name}")
                    success_count += 1
                except Exception as e:
                    set_action_message(sess_name, "error", f"Failed to kill session {actual_session_name}: {e}")
                    error_count += 1
            else:
                set_action_message(sess_name, "info", f"Session {actual_session_name} not found")
        
        if success_count > 0:
            from .dashboard_layout import add_activity_log, invalidate_session_cache
            add_activity_log("success", f"Teardown completed: {success_count} session(s) killed, {error_count} errors")
            # Invalidate cache after successful teardown
            invalidate_session_cache(session_name, "tmux teardown")
            return True
        else:
            from .dashboard_layout import add_activity_log
            add_activity_log("warning", f"Teardown completed with {error_count} errors")
            return False
            
    except Exception as e:
        # session_state에 오류 메시지 저장
        if session_name:
            st.session_state[f"teardown_msg_{session_name}"] = {
                "type": "error",
                "msg": f"Teardown failed: {e}",
                "timestamp": time.time()
            }
        from .dashboard_layout import add_activity_log
        add_activity_log("error", f"Teardown failed: {e}")
        return False