"""Session Details page - View and interact with tmux sessions"""

import streamlit as st
import sys
import time
import libtmux
from pathlib import Path
from typing import Optional, List, Dict

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from libs.core.session_manager import SessionManager
from libs.core.claude_manager import ClaudeManager
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager

st.set_page_config(
    page_title="Session Details",
    page_icon="🔍",
    layout="wide"
)

def initialize_managers():
    """Initialize session state managers"""
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    
    if 'claude_manager' not in st.session_state:
        st.session_state.claude_manager = ClaudeManager()
    
    if 'tmux_server' not in st.session_state:
        st.session_state.tmux_server = libtmux.Server()
    
    if 'selected_session' not in st.session_state:
        st.session_state.selected_session = None
    
    if 'selected_window' not in st.session_state:
        st.session_state.selected_window = None
    
    if 'selected_pane' not in st.session_state:
        st.session_state.selected_pane = None
    
    if 'auto_refresh_pane' not in st.session_state:
        st.session_state.auto_refresh_pane = True

def get_session_info(session_name: str) -> Optional[Dict]:
    """Get detailed session information"""
    try:
        session = st.session_state.tmux_server.find_where({"session_name": session_name})
        if not session:
            return None
        
        session_info = {
            'session': session,
            'name': session.session_name,
            'windows': []
        }
        
        for window in session.windows:
            window_info = {
                'window': window,
                'name': window.window_name,
                'index': window.window_index,
                'active': window.window_active == '1',
                'panes': []
            }
            
            for pane in window.panes:
                try:
                    cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                    pane_info = {
                        'pane': pane,
                        'id': pane.pane_id,
                        'index': pane.pane_index,
                        'active': pane.pane_active == '1',
                        'command': cmd,
                        'width': int(pane.pane_width or 0),
                        'height': int(pane.pane_height or 0),
                        'is_claude': 'claude' in cmd.lower(),
                        'is_controller': 'controller' in cmd.lower() or 'yesman' in cmd.lower()
                    }
                    window_info['panes'].append(pane_info)
                except Exception as e:
                    st.error(f"Error getting pane info: {e}")
            
            session_info['windows'].append(window_info)
        
        return session_info
    except Exception as e:
        st.error(f"Error getting session info: {e}")
        return None

def capture_pane_content(pane, lines: int = 50) -> str:
    """Capture content from a tmux pane"""
    try:
        result = pane.cmd("capture-pane", "-p", "-S", f"-{lines}")
        return '\n'.join(result.stdout) if result.stdout else "No content"
    except Exception as e:
        return f"Error capturing pane content: {e}"

def send_keys_to_pane(pane, keys: str):
    """Send keys to a tmux pane"""
    try:
        pane.send_keys(keys)
        return True
    except Exception as e:
        st.error(f"Error sending keys: {e}")
        return False

def render_session_overview(session_info: Dict):
    """Render session overview information"""
    st.subheader(f"📋 Session: {session_info['name']}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Windows", len(session_info['windows']))
    
    with col2:
        total_panes = sum(len(w['panes']) for w in session_info['windows'])
        st.metric("Total Panes", total_panes)
    
    with col3:
        active_window = next((w for w in session_info['windows'] if w['active']), None)
        st.metric("Active Window", active_window['name'] if active_window else "None")

def render_window_tabs(session_info: Dict):
    """Render window selection tabs"""
    if not session_info['windows']:
        st.warning("No windows found in this session")
        return None
    
    window_names = [f"[{w['index']}] {w['name']}" for w in session_info['windows']]
    
    selected_tab = st.radio(
        "Select Window:",
        range(len(window_names)),
        format_func=lambda x: window_names[x],
        horizontal=True,
        key="window_selector"
    )
    
    selected_window = session_info['windows'][selected_tab]
    
    if st.session_state.selected_window != selected_window['index']:
        st.session_state.selected_window = selected_window['index']
        st.session_state.selected_pane = None
        st.rerun()
    
    return selected_window

def render_pane_selection(window_info: Dict):
    """Render pane selection interface"""
    if not window_info['panes']:
        st.warning("No panes found in this window")
        return None
    
    st.write("**Select Pane:**")
    
    for i, pane_info in enumerate(window_info['panes']):
        pane_type = ""
        if pane_info['is_claude']:
            pane_type = " 🔵"
        elif pane_info['is_controller']:
            pane_type = " 🟡"
        
        if st.button(
            f"Pane {pane_info['index']}{pane_type} - {pane_info['command'][:30]}...",
            key=f"pane_select_{pane_info['id']}",
            use_container_width=True
        ):
            st.session_state.selected_pane = pane_info['id']
            st.rerun()
    
    # Find selected pane
    if st.session_state.selected_pane:
        selected_pane = next((p for p in window_info['panes'] if p['id'] == st.session_state.selected_pane), None)
        return selected_pane
    
    return None

def render_pane_content(pane_info: Dict):
    """Render pane content viewer"""
    st.subheader(f"📺 Pane Content - {pane_info['id']} ({pane_info['command']})")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        lines_to_show = st.slider("Lines to show:", 10, 200, 50, key="pane_lines")
    
    with col2:
        auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh_pane)
        if auto_refresh != st.session_state.auto_refresh_pane:
            st.session_state.auto_refresh_pane = auto_refresh
    
    # Capture and display pane content
    content = capture_pane_content(pane_info['pane'], lines_to_show)
    
    st.code(content, language="bash")
    
    # Pane information
    with st.expander("Pane Information"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Pane ID:** {pane_info['id']}")
            st.write(f"**Command:** {pane_info['command']}")
            st.write(f"**Active:** {'Yes' if pane_info['active'] else 'No'}")
        with col2:
            st.write(f"**Size:** {pane_info['width']}x{pane_info['height']}")
            st.write(f"**Claude Pane:** {'Yes' if pane_info['is_claude'] else 'No'}")
            st.write(f"**Controller Pane:** {'Yes' if pane_info['is_controller'] else 'No'}")

def render_pane_input(pane_info: Dict):
    """Render pane input interface"""
    st.subheader(f"⌨️ Send Input to Pane")
    
    # Prepare keys for textarea and clear flag
    text_key = f"text_input_{pane_info['id']}"
    clear_flag = f"clear_{text_key}"
    # If clear_flag is set, reset the textarea value before widget renders
    if st.session_state.pop(clear_flag, False):
        st.session_state[text_key] = ""
    
    # Text send form: supports Ctrl+Enter to submit
    form_key = f"text_send_form_{pane_info['id']}"
    with st.form(form_key):
        text = st.text_area("Text to send:", key=text_key)
        submitted = st.form_submit_button("📤 Send Text")
    # Handle submission after form
    if submitted:
        if text.strip():
            # Send text line by line
            lines = text.split("\n")
            for line in lines:
                send_keys_to_pane(pane_info['pane'], line)
                time.sleep(0.1)
            st.success(f"Sent {len(lines)} lines of text")
            # Set clear flag for next run
            st.session_state[clear_flag] = True
            time.sleep(0.1)
            st.rerun()
        else:
            st.warning("Please enter text to send")

    # Quick Actions
    st.write("**Quick Actions:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⚡ Ctrl+C"):
            send_keys_to_pane(pane_info['pane'], "C-c")
            st.success("Sent Ctrl+C")
            time.sleep(0.5)
    
    with col2:
        if st.button("↩️ Enter"):
            send_keys_to_pane(pane_info['pane'], "Enter")
            st.success("Sent Enter")
            time.sleep(0.5)
    
    with col3:
        if st.button("🔄 Ctrl+R"):
            send_keys_to_pane(pane_info['pane'], "C-r")
            st.success("Sent Ctrl+R")
            time.sleep(0.5)
    
    with col4:
        if st.button("📋 Clear"):
            send_keys_to_pane(pane_info['pane'], "clear")
            send_keys_to_pane(pane_info['pane'], "Enter")
            st.success("Sent clear command")
            time.sleep(0.5)

def main(session_name: str):
    """Main function for the session details page"""
    initialize_managers()

    st.title(f"🔍 Session Details: {session_name}")

    session_info = get_session_info(session_name)
    
    if session_info:
        render_session_overview(session_info)
        st.divider()
        
        selected_window = render_window_tabs(session_info)
        
        if selected_window:
            st.divider()
            col1, col2 = st.columns([1, 4])
            with col1:
                selected_pane = render_pane_selection(selected_window)
            
            with col2:
                if selected_pane:
                    render_pane_content(selected_pane)
                    render_pane_input(selected_pane)
                else:
                    st.info("Select a pane to view its content and send commands.")

        # Auto-refresh logic
        if st.session_state.get('auto_refresh_pane', False):
            time.sleep(2)
            st.rerun()
    else:
        st.error(f"Could not find session: {session_name}")
        st.page_link("app.py", label="Go to Dashboard", icon="🏠")
        st.stop()


if __name__ == "__main__":
    # Determine session_name from navigation state or URL query params
    session_name_from_nav = st.session_state.get("selected_session_name")
    session_name_from_url = st.query_params.get("session_name")
    session_name = session_name_from_nav or session_name_from_url

    # Clean up the one-time navigation state variable
    if "selected_session_name" in st.session_state:
        del st.session_state["selected_session_name"]

    if not session_name:
        st.warning("Please select a session from the main dashboard to view details.")
        st.page_link("app.py", label="Go to Dashboard", icon="🏠")
        st.stop()

    # Ensure the URL reflects the current state for bookmarking/refreshing
    if st.query_params.get("session_name") != session_name:
        st.query_params['session_name'] = session_name
    
    main(session_name) 