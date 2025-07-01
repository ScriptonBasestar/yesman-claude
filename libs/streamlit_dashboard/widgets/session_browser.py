"""Interactive session browser widget with tree view"""

import streamlit as st
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
    
    def __init__(self, session_key: str = "session_browser"):
        self.session_key = session_key
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state for browser"""
        if f"{self.session_key}_expanded" not in st.session_state:
            st.session_state[f"{self.session_key}_expanded"] = set()
        if f"{self.session_key}_selected" not in st.session_state:
            st.session_state[f"{self.session_key}_selected"] = None
    
    def _get_status_icon_and_color(self, session_info: SessionInfo) -> tuple[str, str]:
        """Get status icon and color for session"""
        if not session_info.exists:
            return "⚫", "#666666"  # Stopped
        
        if session_info.controller_status == 'running':
            return "🟢", "#00ff00"  # Running with controller
        elif session_info.status == 'running':
            return "🟡", "#ffff00"  # Running without controller
        else:
            return "🔴", "#ff0000"  # Error state
    
    def _get_pane_icon_and_color(self, pane_info: PaneInfo) -> tuple[str, str]:
        """Get icon and color for pane"""
        if pane_info.is_claude:
            return "🔵", "#0080ff"  # Claude pane
        elif pane_info.is_controller:
            return "🟡", "#ffa500"  # Controller pane
        else:
            return "⚪", "#cccccc"  # Regular pane
    
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
            # Get session status
            status_icon, status_color = self._get_status_icon_and_color(session)
            
            session_node = TreeNode(
                id=f"session_{session.session_name}",
                name=f"{session.project_name} ({session.session_name})",
                node_type=NodeType.SESSION,
                data=session,
                status_icon=status_icon,
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
                
                # Add panes
                for i, pane in enumerate(window.panes):
                    pane_icon, pane_color = self._get_pane_icon_and_color(pane)
                    
                    pane_node = TreeNode(
                        id=f"pane_{session.session_name}_{window.index}_{i}",
                        name=f"Pane {i}: {pane.command}",
                        node_type=NodeType.PANE,
                        data=pane,
                        status_icon=pane_icon,
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
                st.write(f"**Windows:** {len(session.windows)}")
                total_panes = sum(len(w.panes) for w in session.windows)
                st.write(f"**Total Panes:** {total_panes}")
        
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
            st.write(f"**Pane ID:** {pane.id}")
            st.write(f"**Command:** {pane.command}")
            st.write(f"**Type:** {'Claude' if pane.is_claude else 'Controller' if pane.is_controller else 'Regular'}")
            
            # Action buttons for pane
            if st.button("📱 Attach to Pane", key=f"attach_detail_{pane.id}"):
                st.success(f"Attaching to pane: {pane.id}")
                # TODO: Implement actual pane attachment


def render_session_tree_browser(sessions: List[SessionInfo]) -> Optional[TreeNode]:
    """
    Convenience function to render session tree browser
    
    Args:
        sessions: List of session information
        
    Returns:
        Selected tree node if any
    """
    browser = SessionTreeBrowser()
    
    def on_node_select(node: TreeNode):
        """Handle node selection"""
        st.write(f"Selected: {node.name}")
    
    selected_node = browser.render(sessions, on_select=on_node_select)
    
    # Show details in sidebar or separate section
    if selected_node:
        with st.expander(f"Details: {selected_node.name}", expanded=True):
            browser.render_node_details(selected_node)
    
    return selected_node