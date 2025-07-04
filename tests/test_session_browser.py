#!/usr/bin/env python3
"""Test session browser widget"""

import sys
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.streamlit_dashboard.widgets.session_browser import (
    SessionTreeBrowser, TreeNode, NodeType
)
from libs.core.models import SessionInfo, WindowInfo, PaneInfo


def test_tree_node_creation():
    """Test TreeNode creation and structure"""
    print("Testing TreeNode creation...")
    
    # Create a simple tree structure
    root = TreeNode(
        id="root",
        name="Test Root",
        node_type=NodeType.ROOT,
        status_icon="📁"
    )
    
    child1 = TreeNode(
        id="child1",
        name="Child 1",
        node_type=NodeType.SESSION,
        status_icon="🟢"
    )
    
    child2 = TreeNode(
        id="child2", 
        name="Child 2",
        node_type=NodeType.SESSION,
        status_icon="🔴"
    )
    
    root.children.extend([child1, child2])
    
    assert root.name == "Test Root"
    assert len(root.children) == 2
    assert root.children[0].name == "Child 1"
    assert root.children[1].name == "Child 2"
    
    print("✓ TreeNode creation works")
    print("Tree node creation tests passed!")


def test_session_tree_browser():
    """Test SessionTreeBrowser functionality"""
    print("\nTesting SessionTreeBrowser...")
    
    browser = SessionTreeBrowser(session_key="test_browser")
    
    # Create mock session data
    pane1 = PaneInfo(id="pane1", command="bash", is_claude=False, is_controller=False)
    pane2 = PaneInfo(id="pane2", command="claude", is_claude=True, is_controller=False)
    pane3 = PaneInfo(id="pane3", command="yesman", is_claude=False, is_controller=True)
    
    window1 = WindowInfo(name="main", index=0, panes=[pane1, pane2])
    window2 = WindowInfo(name="debug", index=1, panes=[pane3])
    
    session1 = SessionInfo(
        project_name="frontend",
        session_name="frontend-dev",
        template="react",
        exists=True,
        status="running",
        windows=[window1, window2],
        controller_status="running"
    )
    
    session2 = SessionInfo(
        project_name="backend",
        session_name="backend-api",
        template="django",
        exists=False,
        status="stopped",
        windows=[],
        controller_status="not running"
    )
    
    sessions = [session1, session2]
    
    # Test tree building
    tree_root = browser._build_tree_from_sessions(sessions)
    
    assert tree_root.name == "Sessions"
    assert tree_root.node_type == NodeType.ROOT
    assert len(tree_root.children) == 2
    
    # Check first session
    session_node = tree_root.children[0]
    assert session_node.node_type == NodeType.SESSION
    assert "frontend" in session_node.name
    assert session_node.status_icon == "🟢"  # Running with controller
    assert len(session_node.children) == 2  # Two windows
    
    # Check window structure
    window_node = session_node.children[0]
    assert window_node.node_type == NodeType.WINDOW
    assert window_node.name == "Window 0: main"
    assert len(window_node.children) == 2  # Two panes
    
    # Check pane structure
    claude_pane_node = window_node.children[1]
    assert claude_pane_node.node_type == NodeType.PANE
    assert "claude" in claude_pane_node.name
    assert claude_pane_node.status_icon == "🔵"  # Claude pane
    
    print("✓ Tree building from sessions works")
    
    # Test status icons
    icon, color = browser._get_status_icon_and_color(session1)
    assert icon == "🟢"  # Running with controller
    
    icon, color = browser._get_status_icon_and_color(session2)
    assert icon == "⚫"  # Stopped
    
    print("✓ Status icon determination works")
    
    # Test pane icons
    icon, color = browser._get_pane_icon_and_color(pane1)
    assert icon == "⚪"  # Regular pane
    
    icon, color = browser._get_pane_icon_and_color(pane2)
    assert icon == "🔵"  # Claude pane
    
    icon, color = browser._get_pane_icon_and_color(pane3)
    assert icon == "🟡"  # Controller pane
    
    print("✓ Pane icon determination works")
    
    print("SessionTreeBrowser tests passed!")


def test_node_types_and_enums():
    """Test NodeType enum and related functionality"""
    print("\nTesting NodeType enum...")
    
    # Test all node types
    assert NodeType.ROOT.value == "root"
    assert NodeType.PROJECT.value == "project"
    assert NodeType.SESSION.value == "session"
    assert NodeType.WINDOW.value == "window"
    assert NodeType.PANE.value == "pane"
    
    print("✓ NodeType enum values correct")
    
    # Test node creation with different types
    nodes = []
    for node_type in NodeType:
        node = TreeNode(
            id=f"test_{node_type.value}",
            name=f"Test {node_type.value}",
            node_type=node_type
        )
        nodes.append(node)
        assert node.node_type == node_type
    
    print("✓ Node creation with all types works")
    
    print("NodeType enum tests passed!")


def test_tree_navigation_logic():
    """Test tree navigation and expansion logic"""
    print("\nTesting tree navigation logic...")
    
    # Create a hierarchical structure
    root = TreeNode("root", "Root", NodeType.ROOT)
    session = TreeNode("s1", "Session 1", NodeType.SESSION)
    window = TreeNode("w1", "Window 1", NodeType.WINDOW)
    pane = TreeNode("p1", "Pane 1", NodeType.PANE)
    
    # Build hierarchy
    window.children.append(pane)
    session.children.append(window)
    root.children.append(session)
    
    # Test hierarchy navigation
    assert len(root.children) == 1
    assert root.children[0] == session
    assert session.children[0] == window
    assert window.children[0] == pane
    assert len(pane.children) == 0
    
    print("✓ Tree hierarchy navigation works")
    
    # Test expansion state
    assert not root.expanded  # Default false
    assert not session.expanded
    
    # Test selection state
    assert not root.selected  # Default false
    assert not session.selected
    
    print("✓ Tree node state management works")
    
    print("Tree navigation logic tests passed!")


def main():
    """Run all session browser tests"""
    try:
        test_tree_node_creation()
        test_session_tree_browser()
        test_node_types_and_enums()
        test_tree_navigation_logic()
        
        print("\n🎉 All session browser tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())