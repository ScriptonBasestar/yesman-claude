#!/usr/bin/env python3
"""Test real-time status icon system"""

import sys
import time
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.streamlit_dashboard.widgets.session_browser import (
    SessionTreeBrowser, SessionState, PaneState
)
from libs.core.models import SessionInfo, WindowInfo, PaneInfo


def test_session_state_detection():
    """Test session state detection"""
    print("Testing session state detection...")
    
    browser = SessionTreeBrowser(session_key="test_status")
    
    # Test different session states
    test_cases = [
        # (exists, status, controller_status, expected_state)
        (False, "stopped", "not running", SessionState.STOPPED),
        (True, "running", "running", SessionState.RUNNING),
        (True, "running", "not running", SessionState.RUNNING_NO_CONTROLLER),
        (True, "error", "not running", SessionState.ERROR),
        (True, "unknown", "not running", SessionState.UNKNOWN),
    ]
    
    for exists, status, controller_status, expected_state in test_cases:
        session = SessionInfo(
            project_name="test",
            session_name="test",
            template="test",
            exists=exists,
            status=status,
            windows=[],
            controller_status=controller_status
        )
        
        detected_state = browser._detect_session_state(session)
        assert detected_state == expected_state
        print(f"✓ {status}/{controller_status} -> {expected_state.name}")
    
    print("Session state detection tests passed!")


def test_pane_state_detection():
    """Test pane state detection"""
    print("\nTesting pane state detection...")
    
    browser = SessionTreeBrowser(session_key="test_pane_status")
    
    # Test different pane states
    test_cases = [
        # (command, is_claude, is_controller, expected_state)
        ("claude", True, False, PaneState.CLAUDE_IDLE),
        ("claude --read file.py", True, False, PaneState.CLAUDE_ACTIVE),
        ("yesman controller", False, True, PaneState.CONTROLLER_STOPPED),
        ("yesman controller running", False, True, PaneState.CONTROLLER_RUNNING),
        ("vim test.py", False, False, PaneState.EDITOR),
        ("code .", False, False, PaneState.EDITOR),
        ("bash", False, False, PaneState.TERMINAL),
        ("zsh", False, False, PaneState.TERMINAL),
        ("sleep 100", False, False, PaneState.REGULAR_IDLE),
        ("python app.py", False, False, PaneState.REGULAR_ACTIVE),
    ]
    
    for command, is_claude, is_controller, expected_state in test_cases:
        pane = PaneInfo(
            id="test_pane",
            command=command,
            is_claude=is_claude,
            is_controller=is_controller
        )
        
        detected_state = browser._detect_pane_state(pane)
        assert detected_state == expected_state
        print(f"✓ {command} -> {expected_state.name}")
    
    print("Pane state detection tests passed!")


def test_status_change_tracking():
    """Test status change tracking"""
    print("\nTesting status change tracking...")
    
    browser = SessionTreeBrowser(session_key="test_tracking")
    
    entity_id = "test_entity"
    
    # Initial status
    browser._track_status_change(entity_id, "🟢")
    history = browser._status_history[entity_id]
    assert len(history) == 1
    assert history[0][1] == "🟢"
    print("✓ Initial status tracking")
    
    # Same status (should not add duplicate)
    browser._track_status_change(entity_id, "🟢")
    assert len(history) == 1
    print("✓ Duplicate status prevention")
    
    # Different status
    browser._track_status_change(entity_id, "🔴")
    assert len(history) == 2
    assert history[1][1] == "🔴"
    print("✓ Status change tracking")
    
    # Test status indicator with recent change
    indicator = browser._get_status_indicator(entity_id, "🔴")
    assert "🔄" in indicator  # Should show change indicator
    print("✓ Recent change indicator")
    
    # Wait and test again (simulating time passage)
    time.sleep(0.1)
    # Manually set old timestamp to simulate 6 seconds ago
    browser._status_history[entity_id][-1] = (time.time() - 6, "🔴")
    
    indicator = browser._get_status_indicator(entity_id, "🔴")
    assert indicator == "🔴"  # Should not show change indicator
    print("✓ Change indicator timeout")
    
    print("Status change tracking tests passed!")


def test_health_indicators():
    """Test health indicator generation"""
    print("\nTesting health indicators...")
    
    browser = SessionTreeBrowser(session_key="test_health")
    
    # Test different health states
    test_cases = [
        (True, "running", "running", "🟢 Healthy"),
        (True, "running", "not running", "⚠️ No Controller"),
        (False, "stopped", "not running", "⚫ Stopped"),
        (True, "error", "not running", "🔴 Error"),
        (True, "unknown", "not running", "❓ Unknown"),
    ]
    
    for exists, status, controller_status, expected_health in test_cases:
        session = SessionInfo(
            project_name="test",
            session_name="test",
            template="test",
            exists=exists,
            status=status,
            windows=[],
            controller_status=controller_status
        )
        
        health = browser._get_session_health_indicator(session)
        assert health == expected_health
        print(f"✓ {status}/{controller_status} -> {expected_health}")
    
    print("Health indicator tests passed!")


def test_icon_and_color_mapping():
    """Test icon and color mapping for states"""
    print("\nTesting icon and color mapping...")
    
    browser = SessionTreeBrowser(session_key="test_icons")
    
    # Test session icons
    session = SessionInfo(
        project_name="test",
        session_name="test", 
        template="test",
        exists=True,
        status="running",
        windows=[],
        controller_status="running"
    )
    
    icon, color = browser._get_status_icon_and_color(session)
    assert icon == "🟢"
    assert color == "#00ff00"
    print("✓ Session icon mapping")
    
    # Test pane icons
    claude_pane = PaneInfo(
        id="claude_pane",
        command="claude",
        is_claude=True,
        is_controller=False
    )
    
    icon, color = browser._get_pane_icon_and_color(claude_pane)
    assert icon == "💤"  # Claude idle
    assert color == "#4080ff"
    print("✓ Pane icon mapping")
    
    controller_pane = PaneInfo(
        id="controller_pane",
        command="yesman controller running",
        is_claude=False,
        is_controller=True
    )
    
    icon, color = browser._get_pane_icon_and_color(controller_pane)
    assert icon == "🟡"  # Controller running
    assert color == "#ffa500"
    print("✓ Controller pane icon mapping")
    
    print("Icon and color mapping tests passed!")


def test_state_enum_completeness():
    """Test that all state enums have required values"""
    print("\nTesting state enum completeness...")
    
    # Test SessionState enum
    for state in SessionState:
        assert len(state.value) == 3  # icon, color, description
        assert isinstance(state.value[0], str)  # icon
        assert state.value[1].startswith("#")  # color hex
        assert isinstance(state.value[2], str)  # description
    print("✓ SessionState enum complete")
    
    # Test PaneState enum  
    for state in PaneState:
        assert len(state.value) == 3  # icon, color, description
        assert isinstance(state.value[0], str)  # icon
        assert state.value[1].startswith("#")  # color hex
        assert isinstance(state.value[2], str)  # description
    print("✓ PaneState enum complete")
    
    print("State enum completeness tests passed!")


def test_real_time_tree_building():
    """Test tree building with real-time status"""
    print("\nTesting real-time tree building...")
    
    browser = SessionTreeBrowser(session_key="test_realtime", auto_refresh=True)
    
    # Create mock data
    claude_pane = PaneInfo(id="p1", command="claude", is_claude=True, is_controller=False)
    controller_pane = PaneInfo(id="p2", command="controller", is_claude=False, is_controller=True)
    
    window = WindowInfo(name="main", index=0, panes=[claude_pane, controller_pane])
    
    session = SessionInfo(
        project_name="test_project",
        session_name="test_session",
        template="test",
        exists=True,
        status="running",
        windows=[window],
        controller_status="running"
    )
    
    # Build tree
    tree_root = browser._build_tree_from_sessions([session])
    
    # Verify tree structure with status tracking
    assert tree_root.name == "Sessions"
    assert len(tree_root.children) == 1
    
    session_node = tree_root.children[0]
    assert session_node.status_icon == "🟢"  # Running with controller
    
    window_node = session_node.children[0]
    assert len(window_node.children) == 2  # Two panes
    
    # Check pane nodes have enhanced names
    claude_pane_node = window_node.children[0]
    controller_pane_node = window_node.children[1]
    
    assert "Claude (Idle)" in claude_pane_node.name
    assert "Controller" in controller_pane_node.name
    
    print("✓ Tree building with real-time status works")
    
    print("Real-time tree building tests passed!")


def main():
    """Run all real-time status icon tests"""
    try:
        test_session_state_detection()
        test_pane_state_detection()
        test_status_change_tracking()
        test_health_indicators()
        test_icon_and_color_mapping()
        test_state_enum_completeness()
        test_real_time_tree_building()
        
        print("\n🎉 All real-time status icon tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())