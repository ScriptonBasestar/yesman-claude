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
            'name': session.get('session_name'),
            'windows': []
        }
        
        for window in session.list_windows():
            window_info = {
                'window': window,
                'name': window.get('window_name'),
                'index': window.get('window_index'),
                'active': window.get('window_active') == '1',
                'panes': []
            }
            
            for pane in window.list_panes():
                try:
                    cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                    pane_info = {
                        'pane': pane,
                        'id': pane.get('pane_id'),
                        'index': pane.get('pane_index'),
                        'active': pane.get('pane_active') == '1',
                        'command': cmd,
                        'width': int(pane.get('pane_width', 0)),
                        'height': int(pane.get('pane_height', 0)),
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

def render_session_selector():
    """Render session selection dropdown"""
    sessions = st.session_state.session_manager.get_all_sessions()
    running_sessions = [s for s in sessions if s.status == 'running']
    
    if not running_sessions:
        st.warning("No running sessions found")
        return None
    
    session_names = [s.session_name for s in running_sessions]
    
    selected_session = st.selectbox(
        "Select Session:",
        session_names,
        index=session_names.index(st.session_state.selected_session) if st.session_state.selected_session in session_names else 0,
        key="session_detail_selector"
    )
    
    if selected_session != st.session_state.selected_session:
        st.session_state.selected_session = selected_session
        st.session_state.selected_window = None
        st.session_state.selected_pane = None
        st.rerun()
    
    return selected_session

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
    
    cols = st.columns(min(len(window_info['panes']), 4))
    
    for i, pane_info in enumerate(window_info['panes']):
        with cols[i % 4]:
            pane_type = ""
            if pane_info['is_claude']:
                pane_type = " 🔵"
            elif pane_info['is_controller']:
                pane_type = " 🟡"
            
            if st.button(
                f"Pane {pane_info['index']}{pane_type}\n{pane_info['command'][:20]}...",
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
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        lines_to_show = st.slider("Lines to show:", 10, 200, 50, key="pane_lines")
    
    with col2:
        auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh_pane)
        if auto_refresh != st.session_state.auto_refresh_pane:
            st.session_state.auto_refresh_pane = auto_refresh
    
    with col3:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
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
    
    # Input methods
    input_method = st.radio(
        "Input Method:",
        ["Send Command", "Send Keys", "Send Text"],
        horizontal=True
    )
    
    if input_method == "Send Command":
        col1, col2 = st.columns([4, 1])
        with col1:
            command = st.text_input("Command to send:", key="command_input")
        with col2:
            st.write("")  # Spacing
            if st.button("📤 Send"):
                if command.strip():
                    if send_keys_to_pane(pane_info['pane'], command):
                        st.success(f"Sent command: {command}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to send command")
                else:
                    st.warning("Please enter a command")
    
    elif input_method == "Send Keys":
        col1, col2 = st.columns([4, 1])
        with col1:
            keys = st.text_input("Keys to send (e.g., 'C-c', 'Enter'):", key="keys_input")
        with col2:
            st.write("")  # Spacing
            if st.button("📤 Send"):
                if keys.strip():
                    if send_keys_to_pane(pane_info['pane'], keys):
                        st.success(f"Sent keys: {keys}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to send keys")
                else:
                    st.warning("Please enter keys")
    
    elif input_method == "Send Text":
        text = st.text_area("Text to send:", key="text_input")
        if st.button("📤 Send Text"):
            if text.strip():
                # Send text line by line
                lines = text.split('\n')
                success_count = 0
                for line in lines:
                    if send_keys_to_pane(pane_info['pane'], line):
                        success_count += 1
                    time.sleep(0.1)  # Small delay between lines
                
                if success_count == len(lines):
                    st.success(f"Sent {success_count} lines of text")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning(f"Sent {success_count}/{len(lines)} lines")
            else:
                st.warning("Please enter text to send")
    
    # Quick actions
    st.write("**Quick Actions:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⚡ Ctrl+C"):
            send_keys_to_pane(pane_info['pane'], "C-c")
            st.success("Sent Ctrl+C")
            time.sleep(0.5)
            st.rerun()
    
    with col2:
        if st.button("↩️ Enter"):
            send_keys_to_pane(pane_info['pane'], "Enter")
            st.success("Sent Enter")
            time.sleep(0.5)
            st.rerun()
    
    with col3:
        if st.button("🔄 Ctrl+R"):
            send_keys_to_pane(pane_info['pane'], "C-r")
            st.success("Sent Ctrl+R")
            time.sleep(0.5)
            st.rerun()
    
    with col4:
        if st.button("📋 Clear"):
            send_keys_to_pane(pane_info['pane'], "clear")
            send_keys_to_pane(pane_info['pane'], "Enter")
            st.success("Sent clear command")
            time.sleep(0.5)
            st.rerun()

def main():
    """Main session details page"""
    initialize_managers()
    
    st.title("🔍 Session Details")
    st.write("View detailed tmux session information and interact with panes")
    
    # Session selection
    selected_session_name = render_session_selector()
    
    if not selected_session_name:
        return
    
    # Get detailed session info
    session_info = get_session_info(selected_session_name)
    
    if not session_info:
        st.error(f"Session '{selected_session_name}' not found or error occurred")
        return
    
    # Session overview
    render_session_overview(session_info)
    
    st.divider()
    
    # Window selection
    selected_window = render_window_tabs(session_info)
    
    if not selected_window:
        return
    
    st.divider()
    
    # Pane selection
    selected_pane = render_pane_selection(selected_window)
    
    if not selected_pane:
        st.info("👆 Select a pane above to view its content and send input")
        return
    
    st.divider()
    
    # Create two columns for content and input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_pane_content(selected_pane)
    
    with col2:
        render_pane_input(selected_pane)
    
    # Auto refresh
    if st.session_state.auto_refresh_pane:
        time.sleep(2)
        st.rerun()

if __name__ == "__main__":
    main() 