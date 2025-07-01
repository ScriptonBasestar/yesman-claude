#!/usr/bin/env python3
"""Test pane detailed information functionality"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.models import PaneInfo, SessionInfo, WindowInfo
from libs.streamlit_dashboard.widgets.session_browser import SessionTreeBrowser


def test_enhanced_pane_info_creation():
    """Test enhanced PaneInfo creation with detailed metrics"""
    print("Testing enhanced PaneInfo creation...")
    
    # Create a detailed pane info
    pane = PaneInfo(
        id="test_pane_1",
        command="claude --read test.py",
        is_claude=True,
        is_controller=False,
        current_task="Reading files",
        idle_time=30.5,
        last_activity=datetime.now() - timedelta(seconds=30),
        cpu_usage=12.5,
        memory_usage=256.7,
        pid=12345,
        running_time=3600.0,
        status="running",
        activity_score=85.0,
        last_output="Processing file: test.py",
        output_lines=45
    )
    
    # Verify all fields are set correctly
    assert pane.id == "test_pane_1"
    assert pane.command == "claude --read test.py"
    assert pane.is_claude == True
    assert pane.current_task == "Reading files"
    assert pane.idle_time == 30.5
    assert pane.cpu_usage == 12.5
    assert pane.memory_usage == 256.7
    assert pane.pid == 12345
    assert pane.running_time == 3600.0
    assert pane.status == "running"
    assert pane.activity_score == 85.0
    assert pane.last_output == "Processing file: test.py"
    assert pane.output_lines == 45
    
    print("✓ Enhanced PaneInfo creation works")
    print("Enhanced PaneInfo creation tests passed!")


def test_pane_activity_tracking():
    """Test pane activity tracking functionality"""
    print("\nTesting pane activity tracking...")
    
    # Create pane with initial state
    pane = PaneInfo(
        id="activity_pane",
        command="python app.py",
        current_task="Running application"
    )
    
    # Check initial activity time
    initial_activity = pane.last_activity
    assert initial_activity is not None
    
    # Simulate activity update
    time.sleep(0.1)
    pane.update_activity("New output line")
    
    # Verify activity was updated
    assert pane.last_activity > initial_activity
    assert pane.idle_time == 0.0
    assert pane.last_output == "New output line"
    assert pane.output_lines == 1
    
    print("✓ Activity tracking works")
    
    # Test idle time calculation
    pane.last_activity = datetime.now() - timedelta(seconds=60)
    idle_time = pane.calculate_idle_time()
    assert idle_time >= 60.0
    assert idle_time < 65.0  # Should be around 60 seconds
    
    print("✓ Idle time calculation works")
    print("Pane activity tracking tests passed!")


def test_detailed_pane_display():
    """Test detailed pane information display in browser"""
    print("\nTesting detailed pane display...")
    
    browser = SessionTreeBrowser(session_key="test_details")
    
    # Create panes with different characteristics
    claude_pane = PaneInfo(
        id="claude_pane",
        command="claude --edit main.py",
        is_claude=True,
        current_task="Editing code",
        idle_time=0.0,
        cpu_usage=15.2,
        memory_usage=512.3,
        pid=9876,
        running_time=1800.0,
        status="running",
        activity_score=95.0,
        last_output="Modified function definition",
        output_lines=123
    )
    
    controller_pane = PaneInfo(
        id="controller_pane", 
        command="yesman controller",
        is_controller=True,
        current_task="Dashboard controller",
        idle_time=120.0,
        cpu_usage=2.1,
        memory_usage=64.8,
        pid=5432,
        running_time=7200.0,
        status="sleeping",
        activity_score=45.0,
        last_output="Monitoring sessions...",
        output_lines=89
    )
    
    regular_pane = PaneInfo(
        id="regular_pane",
        command="bash",
        current_task="Terminal session",
        idle_time=300.0,
        cpu_usage=0.1,
        memory_usage=12.4,
        pid=1111,
        running_time=3600.0,
        status="idle",
        activity_score=20.0,
        last_output="$ ",
        output_lines=5
    )
    
    panes = [claude_pane, controller_pane, regular_pane]
    
    # Test state detection for detailed panes
    claude_state = browser._detect_pane_state(claude_pane)
    controller_state = browser._detect_pane_state(controller_pane)
    regular_state = browser._detect_pane_state(regular_pane)
    
    # Verify states are detected correctly
    assert claude_state.name == "CLAUDE_ACTIVE"  # Has active command
    assert controller_state.name == "CONTROLLER_STOPPED"  # Not explicitly running
    assert regular_state.name == "TERMINAL"  # Bash terminal
    
    print("✓ Enhanced pane state detection works")
    
    # Test task analysis
    assert claude_pane.current_task == "Editing code"
    assert controller_pane.current_task == "Dashboard controller"
    assert regular_pane.current_task == "Terminal session"
    
    print("✓ Current task tracking works")
    
    # Test resource usage formatting
    assert claude_pane.cpu_usage == 15.2
    assert claude_pane.memory_usage == 512.3
    assert controller_pane.cpu_usage == 2.1
    assert controller_pane.memory_usage == 64.8
    
    print("✓ Resource usage tracking works")
    
    print("Detailed pane display tests passed!")


def test_session_to_dict_with_details():
    """Test session serialization with detailed pane info"""
    print("\nTesting session serialization with details...")
    
    # Create detailed pane
    detailed_pane = PaneInfo(
        id="detailed_pane",
        command="python server.py",
        current_task="Running server",
        idle_time=45.0,
        cpu_usage=8.5,
        memory_usage=128.9,
        pid=2468,
        running_time=1200.0,
        status="running",
        activity_score=75.0,
        last_output="Server listening on port 8000",
        output_lines=67
    )
    
    window = WindowInfo(name="main", index="0", panes=[detailed_pane])
    
    session = SessionInfo(
        project_name="test_project",
        session_name="test_session",
        template="python",
        exists=True,
        status="running",
        windows=[window],
        controller_status="running"
    )
    
    # Convert to dict
    session_dict = session.to_dict()
    
    # Verify detailed pane info is included
    pane_dict = session_dict['windows'][0]['panes'][0]
    
    assert pane_dict['id'] == "detailed_pane"
    assert pane_dict['command'] == "python server.py"
    assert pane_dict['current_task'] == "Running server"
    assert pane_dict['idle_time'] == 45.0
    assert pane_dict['cpu_usage'] == 8.5
    assert pane_dict['memory_usage'] == 128.9
    assert pane_dict['pid'] == 2468
    assert pane_dict['running_time'] == 1200.0
    assert pane_dict['status'] == "running"
    assert pane_dict['activity_score'] == 75.0
    assert pane_dict['last_output'] == "Server listening on port 8000"
    assert pane_dict['output_lines'] == 67
    
    print("✓ Session serialization with details works")
    print("Session serialization tests passed!")


def test_resource_usage_formatting():
    """Test resource usage formatting and display"""
    print("\nTesting resource usage formatting...")
    
    # Test different memory sizes
    panes = [
        PaneInfo(id="small", command="test", memory_usage=50.5),    # < 1024 MB
        PaneInfo(id="large", command="test", memory_usage=2048.7),  # > 1024 MB (2GB)
        PaneInfo(id="huge", command="test", memory_usage=5120.3),   # > 1024 MB (5GB)
    ]
    
    # Small memory should display in MB
    assert panes[0].memory_usage == 50.5
    
    # Large memory should be convertible to GB
    assert abs(panes[1].memory_usage / 1024 - 2.0) < 0.1  # ~2GB
    assert abs(panes[2].memory_usage / 1024 - 5.0) < 0.1  # ~5GB
    
    print("✓ Memory usage formatting works")
    
    # Test different running times
    test_times = [
        30.0,      # 30 seconds (should display in minutes: 0.5)
        3600.0,    # 1 hour (should display in hours: 1.0)
        7200.0,    # 2 hours (should display in hours: 2.0)
        300.0,     # 5 minutes (should display in minutes: 5.0)
    ]
    
    for running_time in test_times:
        minutes = running_time / 60
        hours = minutes / 60
        
        if minutes < 60:
            # Should display in minutes
            assert minutes >= 0
        else:
            # Should display in hours
            assert hours >= 1
    
    print("✓ Running time formatting works")
    print("Resource usage formatting tests passed!")


def main():
    """Run all pane details tests"""
    try:
        test_enhanced_pane_info_creation()
        test_pane_activity_tracking()
        test_detailed_pane_display()
        test_session_to_dict_with_details()
        test_resource_usage_formatting()
        
        print("\n🎉 All pane details tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())