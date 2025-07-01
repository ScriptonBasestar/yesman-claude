"""Interactive session browser widget with tree view"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from libs.core.models import SessionInfo, WindowInfo, PaneInfo


class NodeType(Enum):
    """Tree node types"""
    ROOT = "root"
    PROJECT = "project"
    SESSION = "session"
    WINDOW = "window"
    PANE = "pane"


class SessionState(Enum):
    """Session state types with icons"""
    RUNNING = ("🟢", "#00ff00", "Running")
    RUNNING_NO_CONTROLLER = ("🟡", "#ffff00", "Running (No Controller)")
    STOPPED = ("⚫", "#666666", "Stopped")
    ERROR = ("🔴", "#ff0000", "Error")
    LOADING = ("🔄", "#0080ff", "Loading")
    WARNING = ("⚠️", "#ffa500", "Warning")
    UNKNOWN = ("❓", "#888888", "Unknown")


class PaneState(Enum):
    """Pane state types with icons"""
    CLAUDE_ACTIVE = ("🔵", "#0080ff", "Claude (Active)")
    CLAUDE_IDLE = ("💤", "#4080ff", "Claude (Idle)")
    CONTROLLER_RUNNING = ("🟡", "#ffa500", "Controller (Running)")
    CONTROLLER_STOPPED = ("⚫", "#666666", "Controller (Stopped)")
    REGULAR_ACTIVE = ("⚪", "#cccccc", "Regular (Active)")
    REGULAR_IDLE = ("⭕", "#999999", "Regular (Idle)")
    TERMINAL = ("📺", "#00ff00", "Terminal")
    EDITOR = ("📝", "#ff8000", "Editor")
    UNKNOWN = ("❓", "#888888", "Unknown")


@dataclass
class TreeNode:
    """Tree node for hierarchical display"""
    id: str
    name: str
    node_type: NodeType
    data: Any = None
    children: List['TreeNode'] = None
    expanded: bool = False
    selected: bool = False
    status_icon: str = "📄"
    status_color: str = "#888888"
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class SessionTreeBrowser:
    """File-browser style session tree widget"""
    
    def __init__(self, session_key: str = "session_browser", auto_refresh: bool = True, session_manager=None):
        self.session_key = session_key
        self.auto_refresh = auto_refresh
        self.session_manager = session_manager
        self._init_session_state()
        self._status_history: Dict[str, List[tuple[float, str]]] = {}  # Track status changes
        self._current_session_context: Dict[str, str] = {}  # Track current session context
    
    def _init_session_state(self):
        """Initialize session state for browser"""
        if f"{self.session_key}_expanded" not in st.session_state:
            st.session_state[f"{self.session_key}_expanded"] = set()
        if f"{self.session_key}_selected" not in st.session_state:
            st.session_state[f"{self.session_key}_selected"] = None
    
    def _detect_session_state(self, session_info: SessionInfo) -> SessionState:
        """Detect current session state"""
        if not session_info.exists:
            return SessionState.STOPPED
        
        if session_info.controller_status == 'running':
            return SessionState.RUNNING
        elif session_info.status == 'running':
            return SessionState.RUNNING_NO_CONTROLLER
        elif session_info.status == 'error':
            return SessionState.ERROR
        else:
            return SessionState.UNKNOWN
    
    def _detect_pane_state(self, pane_info: PaneInfo) -> PaneState:
        """Detect current pane state with activity analysis"""
        command = pane_info.command.lower()
        
        if pane_info.is_claude:
            # Check if Claude is likely active or idle
            if any(keyword in command for keyword in ['read', 'edit', 'processing']):
                return PaneState.CLAUDE_ACTIVE
            else:
                return PaneState.CLAUDE_IDLE
        
        elif pane_info.is_controller:
            # Check controller activity
            if 'running' in command or 'active' in command:
                return PaneState.CONTROLLER_RUNNING
            else:
                return PaneState.CONTROLLER_STOPPED
        
        else:
            # Detect regular pane types
            if any(term in command for term in ['vim', 'nano', 'code', 'editor']):
                return PaneState.EDITOR
            elif any(term in command for term in ['bash', 'zsh', 'sh', 'terminal']):
                return PaneState.TERMINAL
            elif 'sleep' in command or 'idle' in command:
                return PaneState.REGULAR_IDLE
            else:
                return PaneState.REGULAR_ACTIVE
    
    def _get_status_icon_and_color(self, session_info: SessionInfo) -> tuple[str, str]:
        """Get status icon and color for session"""
        state = self._detect_session_state(session_info)
        return state.value[0], state.value[1]
    
    def _get_pane_icon_and_color(self, pane_info: PaneInfo) -> tuple[str, str]:
        """Get icon and color for pane with state detection"""
        state = self._detect_pane_state(pane_info)
        return state.value[0], state.value[1]
    
    def _track_status_change(self, entity_id: str, new_status: str):
        """Track status changes for real-time monitoring"""
        current_time = time.time()
        
        if entity_id not in self._status_history:
            self._status_history[entity_id] = []
        
        history = self._status_history[entity_id]
        
        # Add new status if different from last
        if not history or history[-1][1] != new_status:
            history.append((current_time, new_status))
            
            # Keep only last 10 status changes
            if len(history) > 10:
                history.pop(0)
    
    def _get_status_indicator(self, entity_id: str, current_state: str) -> str:
        """Get status indicator with change animation"""
        self._track_status_change(entity_id, current_state)
        
        history = self._status_history.get(entity_id, [])
        if len(history) < 2:
            return current_state
        
        # Check if status changed recently (within 5 seconds)
        current_time = time.time()
        last_change_time = history[-1][0]
        
        if current_time - last_change_time < 5.0:
            # Show change indicator
            return f"🔄 {current_state}"
        
        return current_state
    
    def _execute_pane_attachment(self, session_name: str, window_index: str, pane_id: str) -> Dict[str, Any]:
        """Execute pane attachment using session manager"""
        if not self.session_manager:
            return {
                "success": False,
                "error": "Session manager not available",
                "action": "error"
            }
        
        try:
            return self.session_manager.execute_pane_attachment(session_name, window_index, pane_id)
        except Exception as e:
            return {
                "success": False,
                "error": f"Attachment execution failed: {str(e)}",
                "action": "error"
            }
    
    def _update_session_context(self, session_info: SessionInfo, window_info: WindowInfo = None):
        """Update current session context for pane operations"""
        self._current_session_context = {
            "session_name": session_info.session_name,
            "window_index": window_info.index if window_info else "0"
        }
    
    def _extract_context_from_node_id(self, node_id: str) -> tuple[str, str]:
        """Extract session name and window index from pane node ID"""
        # Pane node IDs are formatted as: pane_{session_name}_{window_index}_{pane_index}
        try:
            parts = node_id.split('_')
            if len(parts) >= 4 and parts[0] == 'pane':
                session_name = parts[1]
                window_index = parts[2]
                return session_name, window_index
        except:
            pass
        
        # Fallback to current context if parsing fails
        return (
            self._current_session_context.get('session_name', 'unknown'),
            self._current_session_context.get('window_index', '0')
        )
    
    def _get_session_health_indicator(self, session_info: SessionInfo) -> str:
        """Get health indicator based on session state"""
        state = self._detect_session_state(session_info)
        
        if state == SessionState.RUNNING:
            return "🟢 Healthy"
        elif state == SessionState.RUNNING_NO_CONTROLLER:
            return "⚠️ No Controller"
        elif state == SessionState.STOPPED:
            return "⚫ Stopped"
        elif state == SessionState.ERROR:
            return "🔴 Error"
        else:
            return "❓ Unknown"
    
    def _build_tree_from_sessions(self, sessions: List[SessionInfo]) -> TreeNode:
        """Build tree structure from session data"""
        root = TreeNode(
            id="root",
            name="Sessions",
            node_type=NodeType.ROOT,
            status_icon="📁",
            expanded=True
        )
        
        for session in sessions:
            # Get session status with real-time tracking
            status_icon, status_color = self._get_status_icon_and_color(session)
            state = self._detect_session_state(session)
            
            # Track status changes
            entity_id = f"session_{session.session_name}"
            status_indicator = self._get_status_indicator(entity_id, status_icon)
            
            session_node = TreeNode(
                id=entity_id,
                name=f"{session.project_name} ({session.session_name})",
                node_type=NodeType.SESSION,
                data=session,
                status_icon=status_indicator,
                status_color=status_color
            )
            
            # Add windows
            for window in session.windows:
                window_node = TreeNode(
                    id=f"window_{session.session_name}_{window.index}",
                    name=f"Window {window.index}: {window.name}",
                    node_type=NodeType.WINDOW,
                    data=window,
                    status_icon="🪟",
                    status_color="#4a90e2"
                )
                
                # Add panes with state tracking
                for i, pane in enumerate(window.panes):
                    pane_icon, pane_color = self._get_pane_icon_and_color(pane)
                    
                    # Track pane status changes
                    pane_entity_id = f"pane_{session.session_name}_{window.index}_{i}"
                    pane_status_indicator = self._get_status_indicator(pane_entity_id, pane_icon)
                    
                    # Enhanced pane name with type indicator
                    pane_state = self._detect_pane_state(pane)
                    pane_type = pane_state.value[2]  # Human readable description
                    
                    pane_node = TreeNode(
                        id=pane_entity_id,
                        name=f"Pane {i}: {pane.command} [{pane_type}]",
                        node_type=NodeType.PANE,
                        data=pane,
                        status_icon=pane_status_indicator,
                        status_color=pane_color
                    )
                    window_node.children.append(pane_node)
                
                session_node.children.append(window_node)
            
            root.children.append(session_node)
        
        return root
    
    def _render_tree_node(self, node: TreeNode, level: int = 0) -> Optional[TreeNode]:
        """Render a single tree node"""
        indent = "  " * level
        expanded_set = st.session_state[f"{self.session_key}_expanded"]
        
        # Build node display
        has_children = len(node.children) > 0
        
        if has_children:
            expander_icon = "📂" if node.id in expanded_set else "📁"
        else:
            expander_icon = ""
        
        # Create columns for tree structure
        col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
        
        selected_node = None
        
        with col1:
            if has_children:
                if st.button(expander_icon, key=f"expand_{node.id}", help="Expand/Collapse"):
                    if node.id in expanded_set:
                        expanded_set.remove(node.id)
                    else:
                        expanded_set.add(node.id)
                    st.rerun()
        
        with col2:
            # Node content with status
            node_style = f"color: {node.status_color}; font-weight: {'bold' if node.node_type == NodeType.SESSION else 'normal'};"
            
            if st.button(
                f"{indent}{node.status_icon} {node.name}",
                key=f"select_{node.id}",
                help=f"Select {node.node_type.value}: {node.name}"
            ):
                st.session_state[f"{self.session_key}_selected"] = node.id
                selected_node = node
                st.rerun()
        
        with col3:
            # Action buttons based on node type
            if node.node_type == NodeType.SESSION and node.data:
                if st.button("🔍", key=f"detail_{node.id}", help="View Details"):
                    self._update_session_context(node.data)
                    selected_node = node
            elif node.node_type == NodeType.WINDOW and node.data:
                if st.button("🪟", key=f"window_{node.id}", help="View Window"):
                    selected_node = node
            elif node.node_type == NodeType.PANE and node.data:
                if st.button("📱", key=f"attach_{node.id}", help="Attach to Pane"):
                    selected_node = node
        
        # Render children if expanded
        if has_children and node.id in expanded_set:
            for child in node.children:
                child_selected = self._render_tree_node(child, level + 1)
                if child_selected:
                    selected_node = child_selected
        
        return selected_node
    
    def render(self, sessions: List[SessionInfo], 
               on_select: Optional[Callable[[TreeNode], None]] = None) -> Optional[TreeNode]:
        """
        Render the session tree browser
        
        Args:
            sessions: List of session information
            on_select: Callback for node selection
            
        Returns:
            Selected tree node if any
        """
        st.subheader("📁 Session Browser")
        
        if not sessions:
            st.info("No sessions available")
            return None
        
        # Build tree structure
        tree_root = self._build_tree_from_sessions(sessions)
        
        # Add expand/collapse all buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📂 Expand All", help="Expand all nodes"):
                expanded_set = st.session_state[f"{self.session_key}_expanded"]
                for session in sessions:
                    expanded_set.add(f"session_{session.session_name}")
                    for window in session.windows:
                        expanded_set.add(f"window_{session.session_name}_{window.index}")
                st.rerun()
        
        with col2:
            if st.button("📁 Collapse All", help="Collapse all nodes"):
                st.session_state[f"{self.session_key}_expanded"] = set()
                st.rerun()
        
        with col3:
            if st.button("🔄 Refresh", help="Refresh session data"):
                st.rerun()
        
        # Auto-refresh indicator
        if self.auto_refresh:
            st.caption("🔄 Auto-refresh enabled (real-time status updates)")
        
        st.divider()
        
        # Render tree
        with st.container():
            selected_node = self._render_tree_node(tree_root)
            
            if selected_node and on_select:
                on_select(selected_node)
            
            return selected_node
    
    def render_node_details(self, node: TreeNode):
        """Render details for selected node"""
        if not node or not node.data:
            return
        
        st.subheader(f"📋 {node.node_type.value.title()} Details")
        
        if node.node_type == NodeType.SESSION:
            session = node.data
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Project:** {session.project_name}")
                st.write(f"**Session:** {session.session_name}")
                st.write(f"**Template:** {session.template}")
                st.write(f"**Status:** {session.status}")
            
            with col2:
                st.write(f"**Exists:** {'Yes' if session.exists else 'No'}")
                st.write(f"**Controller:** {session.controller_status}")
                
                # Show health indicator
                health = self._get_session_health_indicator(session)
                st.write(f"**Health:** {health}")
                
                st.write(f"**Windows:** {len(session.windows)}")
                total_panes = sum(len(w.panes) for w in session.windows)
                st.write(f"**Total Panes:** {total_panes}")
            
            # Show status history if available
            entity_id = f"session_{session.session_name}"
            if entity_id in self._status_history:
                history = self._status_history[entity_id]
                if len(history) > 1:
                    st.write("**Recent Status Changes:**")
                    for timestamp, status in history[-3:]:  # Show last 3 changes
                        time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
                        st.write(f"  - {time_str}: {status}")
        
        elif node.node_type == NodeType.WINDOW:
            window = node.data
            st.write(f"**Window Index:** {window.index}")
            st.write(f"**Window Name:** {window.name}")
            st.write(f"**Panes Count:** {len(window.panes)}")
            
            # Show pane summary
            if window.panes:
                st.write("**Panes:**")
                for i, pane in enumerate(window.panes):
                    pane_type = "Claude" if pane.is_claude else "Controller" if pane.is_controller else "Regular"
                    st.write(f"  - Pane {i}: {pane.command} ({pane_type})")
        
        elif node.node_type == NodeType.PANE:
            pane = node.data
            pane_state = self._detect_pane_state(pane)
            
            # Extract session and window context from node ID
            session_name, window_index = self._extract_context_from_node_id(node.id)
            
            # Basic pane information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Pane ID:** {pane.id}")
                st.write(f"**Command:** {pane.command}")
                st.write(f"**Type:** {pane_state.value[2]}")
                st.write(f"**Status:** {pane_state.value[0]} {pane_state.name}")
                
                # Current task and activity
                if pane.current_task:
                    st.write(f"**Current Task:** {pane.current_task}")
                
                # Activity information
                if pane.idle_time > 0:
                    idle_minutes = pane.idle_time / 60
                    if idle_minutes < 1:
                        st.write(f"**Idle Time:** {pane.idle_time:.1f} seconds")
                    elif idle_minutes < 60:
                        st.write(f"**Idle Time:** {idle_minutes:.1f} minutes")
                    else:
                        idle_hours = idle_minutes / 60
                        st.write(f"**Idle Time:** {idle_hours:.1f} hours")
                else:
                    st.write("**Status:** Active")
            
            with col2:
                # Resource usage information
                if pane.pid:
                    st.write(f"**Process ID:** {pane.pid}")
                
                if pane.cpu_usage > 0:
                    st.write(f"**CPU Usage:** {pane.cpu_usage:.1f}%")
                
                if pane.memory_usage > 0:
                    if pane.memory_usage < 1024:
                        st.write(f"**Memory:** {pane.memory_usage:.1f} MB")
                    else:
                        st.write(f"**Memory:** {pane.memory_usage/1024:.1f} GB")
                
                if pane.running_time > 0:
                    running_minutes = pane.running_time / 60
                    if running_minutes < 60:
                        st.write(f"**Running Time:** {running_minutes:.1f} minutes")
                    else:
                        running_hours = running_minutes / 60
                        st.write(f"**Running Time:** {running_hours:.1f} hours")
                
                # Activity score
                if pane.activity_score > 0:
                    activity_color = "🟢" if pane.activity_score > 70 else "🟡" if pane.activity_score > 30 else "🔴"
                    st.write(f"**Activity Score:** {activity_color} {pane.activity_score:.0f}/100")
            
            # Last activity and output
            if pane.last_activity:
                st.write(f"**Last Activity:** {pane.last_activity.strftime('%H:%M:%S')}")
            
            if pane.last_output:
                st.write("**Last Output:**")
                st.code(pane.last_output, language="text")
            
            if pane.output_lines > 0:
                st.write(f"**Output Lines:** {pane.output_lines}")
            
            # Show specialized info based on pane type
            if pane.is_claude:
                st.write("**Claude Integration:** ✅ Active")
                if pane_state == PaneState.CLAUDE_ACTIVE:
                    st.info("Claude is currently processing")
                else:
                    st.info("Claude is idle and ready")
            elif pane.is_controller:
                st.write("**Controller Pane:** ✅ Detected")
                if pane_state == PaneState.CONTROLLER_RUNNING:
                    st.success("Controller is active")
                else:
                    st.warning("Controller appears stopped")
            
            # Action buttons for pane
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📱 Attach", key=f"attach_detail_{pane.id}"):
                    # Use extracted context for attachment
                    result = self._execute_pane_attachment(session_name, window_index, pane.id)
                    if result["success"]:
                        st.success(result["message"])
                        st.code(f"Run: {result['attach_command']}", language="bash")
                        
                        # Also provide a download link for the script
                        if "script_path" in result:
                            st.download_button(
                                label="📁 Download Script",
                                data=f"#!/bin/bash\n{result['attach_command']}\n",
                                file_name=f"attach_{pane.id}.sh",
                                mime="text/plain",
                                key=f"download_{pane.id}"
                            )
                    else:
                        st.error(result["error"])
            
            with col2:
                if st.button("📊 Monitor", key=f"monitor_detail_{pane.id}"):
                    st.info(f"Monitoring pane: {pane.id}")
                    # TODO: Implement pane monitoring
            
            with col3:
                if st.button("🔄 Refresh", key=f"refresh_detail_{pane.id}"):
                    st.rerun()


def render_session_tree_browser(sessions: List[SessionInfo], session_manager=None) -> Optional[TreeNode]:
    """
    Convenience function to render session tree browser
    
    Args:
        sessions: List of session information
        session_manager: Optional session manager for pane operations
        
    Returns:
        Selected tree node if any
    """
    browser = SessionTreeBrowser(session_manager=session_manager)
    
    def on_node_select(node: TreeNode):
        """Handle node selection"""
        st.write(f"Selected: {node.name}")
    
    selected_node = browser.render(sessions, on_select=on_node_select)
    
    # Show details in sidebar or separate section
    if selected_node:
        with st.expander(f"Details: {selected_node.name}", expanded=True):
            browser.render_node_details(selected_node)
    
    return selected_node