#!/usr/bin/env python3
"""Test pane attachment functionality"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.session_manager import SessionManager
from libs.core.models import PaneInfo, SessionInfo, WindowInfo
from libs.streamlit_dashboard.widgets.session_browser import SessionTreeBrowser


def test_session_manager_attachment():
    """Test session manager pane attachment functionality"""
    print("Testing session manager pane attachment...")
    
    # Create mock tmux objects
    mock_server = Mock()
    mock_session = Mock()
    mock_window = Mock()
    mock_pane = Mock()
    
    # Configure mock hierarchy
    mock_server.find_where.return_value = mock_session
    mock_session.find_where.return_value = mock_window
    mock_window.find_where.return_value = mock_pane
    
    # Create session manager with CLI mode
    session_manager = SessionManager()
    session_manager.server = mock_server
    
    # Test successful attachment
    result = session_manager.attach_to_pane("test_session", "0", "pane_1")
    
    assert result["success"] == True
    assert result["session_name"] == "test_session"
    assert result["window_index"] == "0"
    assert result["pane_id"] == "pane_1"
    assert "attach_command" in result
    assert "tmux attach-session" in result["attach_command"]
    
    print("✓ Basic pane attachment works")
    
    # Test attachment with missing session
    mock_server.find_where.return_value = None
    result = session_manager.attach_to_pane("nonexistent_session", "0", "pane_1")
    
    assert result["success"] == False
    assert "not found" in result["error"]
    
    print("✓ Missing session handling works")
    
    print("Session manager attachment tests passed!")


def test_terminal_script_creation():
    """Test terminal script creation functionality"""
    print("\nTesting terminal script creation...")
    
    # Create session manager
    session_manager = SessionManager()
    
    # Test script creation
    attach_command = "tmux attach-session -t test_session \\; select-window -t 0 \\; select-pane -t pane_1"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = os.path.join(temp_dir, "test_attach.sh")
        
        created_path = session_manager.create_terminal_script(attach_command, script_path)
        
        # Verify script was created
        assert os.path.exists(created_path)
        assert created_path == script_path
        
        # Verify script content
        with open(script_path, 'r') as f:
            content = f.read()
        
        assert "#!/bin/bash" in content
        assert attach_command in content
        assert "Auto-generated" in content
        
        # Verify script is executable
        assert os.access(script_path, os.X_OK)
        
        print("✓ Script creation works")
        print("✓ Script content correct")
        print("✓ Script executable")
    
    print("Terminal script creation tests passed!")


def test_session_browser_attachment():
    """Test session browser attachment integration"""
    print("\nTesting session browser attachment integration...")
    
    # Create mock session manager
    mock_session_manager = Mock()
    mock_session_manager.execute_pane_attachment.return_value = {
        "success": True,
        "script_path": "/tmp/test_attach.sh",
        "attach_command": "tmux attach-session -t test_session",
        "session_name": "test_session",
        "window_index": "0",
        "pane_id": "pane_1",
        "action": "execute",
        "message": "Attachment script created"
    }
    
    # Create session browser with mock session manager
    browser = SessionTreeBrowser(session_manager=mock_session_manager)
    
    # Test attachment execution
    result = browser._execute_pane_attachment("test_session", "0", "pane_1")
    
    assert result["success"] == True
    assert result["session_name"] == "test_session"
    assert result["window_index"] == "0"
    assert result["pane_id"] == "pane_1"
    assert "script_path" in result
    
    print("✓ Browser attachment integration works")
    
    # Test with no session manager
    browser_no_manager = SessionTreeBrowser()
    result = browser_no_manager._execute_pane_attachment("test_session", "0", "pane_1")
    
    assert result["success"] == False
    assert "not available" in result["error"]
    
    print("✓ No session manager handling works")
    
    print("Session browser attachment tests passed!")


def test_context_extraction():
    """Test context extraction from node IDs"""
    print("\nTesting context extraction...")
    
    browser = SessionTreeBrowser()
    
    # Test valid pane node ID
    session_name, window_index = browser._extract_context_from_node_id("pane_frontend-dev_0_1")
    assert session_name == "frontend-dev"
    assert window_index == "0"
    
    print("✓ Valid node ID extraction works")
    
    # Test invalid node ID with fallback
    browser._current_session_context = {
        "session_name": "fallback_session",
        "window_index": "2"
    }
    
    session_name, window_index = browser._extract_context_from_node_id("invalid_node_id")
    assert session_name == "fallback_session"
    assert window_index == "2"
    
    print("✓ Fallback context works")
    
    # Test session context update
    mock_session = Mock()
    mock_session.session_name = "test_session"
    
    mock_window = Mock()
    mock_window.index = "3"
    
    browser._update_session_context(mock_session, mock_window)
    
    assert browser._current_session_context["session_name"] == "test_session"
    assert browser._current_session_context["window_index"] == "3"
    
    print("✓ Session context update works")
    
    print("Context extraction tests passed!")


def test_attachment_command_generation():
    """Test attachment command generation"""
    print("\nTesting attachment command generation...")
    
    # Create session manager
    session_manager = SessionManager()
    
    # Mock successful hierarchy
    mock_server = Mock()
    mock_session = Mock()
    mock_window = Mock()
    mock_pane = Mock()
    
    mock_server.find_where.return_value = mock_session
    mock_session.find_where.return_value = mock_window
    mock_window.find_where.return_value = mock_pane
    
    session_manager.server = mock_server
    
    # Test attachment command generation
    result = session_manager.attach_to_pane("my-session", "2", "pane_5")
    
    expected_cmd = "tmux attach-session -t my-session \\; select-window -t 2 \\; select-pane -t pane_5"
    assert result["attach_command"] == expected_cmd
    
    print("✓ Command generation works")
    
    # Test execution with script creation
    result = session_manager.execute_pane_attachment("my-session", "2", "pane_5")
    
    assert result["success"] == True
    assert "script_path" in result
    assert result["attach_command"] == expected_cmd
    
    print("✓ Execution with script creation works")
    
    print("Attachment command generation tests passed!")


def test_error_handling():
    """Test error handling in attachment functionality"""
    print("\nTesting error handling...")
    
    # Create session manager
    session_manager = SessionManager()
    
    # Mock server that raises exception
    mock_server = Mock()
    mock_server.find_where.side_effect = Exception("Connection failed")
    session_manager.server = mock_server
    
    # Test exception handling
    result = session_manager.attach_to_pane("test_session", "0", "pane_1")
    
    assert result["success"] == False
    assert "failed" in result["error"]
    assert result["action"] == "error"
    
    print("✓ Exception handling works")
    
    # Test missing window
    mock_server.find_where.side_effect = None
    mock_session = Mock()
    mock_session.find_where.return_value = None  # No window found
    mock_server.find_where.return_value = mock_session
    
    result = session_manager.attach_to_pane("test_session", "99", "pane_1")
    
    assert result["success"] == False
    assert "Window 99 not found" in result["error"]
    
    print("✓ Missing window handling works")
    
    # Test missing pane
    mock_window = Mock()
    mock_window.find_where.return_value = None  # No pane found
    mock_session.find_where.return_value = mock_window
    
    result = session_manager.attach_to_pane("test_session", "0", "pane_99")
    
    assert result["success"] == False
    assert "Pane pane_99 not found" in result["error"]
    
    print("✓ Missing pane handling works")
    
    print("Error handling tests passed!")


def main():
    """Run all pane attachment tests"""
    try:
        test_session_manager_attachment()
        test_terminal_script_creation()
        test_session_browser_attachment()
        test_context_extraction()
        test_attachment_command_generation()
        test_error_handling()
        
        print("\n🎉 All pane attachment tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())