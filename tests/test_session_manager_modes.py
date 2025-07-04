#!/usr/bin/env python3
"""Test session manager operation modes"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.session_manager import SessionManager, OperationMode


def test_operation_mode_detection():
    """Test automatic operation mode detection"""
    print("Testing operation mode detection...")
    
    # Mock config and dependencies
    mock_config = Mock()
    mock_config.get.return_value = "/tmp/test_logs"
    mock_config.get_config_dir.return_value = Path("/tmp/test_config")
    
    mock_tmux_manager = Mock()
    mock_tmux_manager.load_projects.return_value = {"sessions": {}}
    
    mock_server = Mock()
    
    with patch('libs.core.session_manager.YesmanConfig', return_value=mock_config), \
         patch('libs.core.session_manager.TmuxManager', return_value=mock_tmux_manager), \
         patch('libs.core.session_manager.libtmux.Server', return_value=mock_server), \
         patch('libs.core.session_manager.ensure_log_directory'):
        
        # Test CLI mode detection (default)
        with patch.dict(os.environ, {}, clear=True):
            manager = SessionManager()
            assert manager.operation_mode == OperationMode.CLI
            assert manager.cache is None
            print("✓ CLI mode detection works")
        
        # Test Web mode detection (Streamlit)
        with patch.dict(os.environ, {'STREAMLIT_SERVER_PORT': '8501'}):
            manager = SessionManager()
            assert manager.operation_mode == OperationMode.WEB
            assert manager.cache is not None
            print("✓ Web mode detection works")
        
        # Test Daemon mode detection (TMUX)
        with patch.dict(os.environ, {'TMUX': '/tmp/tmux-1000/default,12345,0'}):
            manager = SessionManager()
            assert manager.operation_mode == OperationMode.DAEMON
            assert manager.cache is not None
            print("✓ Daemon mode detection works")
    
    print("Operation mode detection tests passed!")


def test_cache_behavior_by_mode():
    """Test cache behavior differences by operation mode"""
    print("\nTesting cache behavior by mode...")
    
    mock_config = Mock()
    mock_config.get.return_value = "/tmp/test_logs"
    mock_config.get_config_dir.return_value = Path("/tmp/test_config")
    
    mock_tmux_manager = Mock()
    mock_tmux_manager.load_projects.return_value = {
        "sessions": {
            "test_project": {"template_name": "test"}
        }
    }
    
    mock_server = Mock()
    mock_server.find_where.return_value = None
    
    with patch('libs.core.session_manager.YesmanConfig', return_value=mock_config), \
         patch('libs.core.session_manager.TmuxManager', return_value=mock_tmux_manager), \
         patch('libs.core.session_manager.libtmux.Server', return_value=mock_server), \
         patch('libs.core.session_manager.ensure_log_directory'):
        
        # Test CLI mode (no caching)
        cli_manager = SessionManager(OperationMode.CLI)
        sessions1 = cli_manager.get_all_sessions()
        sessions2 = cli_manager.get_all_sessions()
        
        stats = cli_manager.get_cache_stats()
        assert stats['cache_enabled'] is False
        assert stats['mode'] == 'cli'
        print("✓ CLI mode: No caching, fresh data every time")
        
        # Test Web mode (moderate caching)
        web_manager = SessionManager(OperationMode.WEB)
        assert web_manager.cache.default_ttl == 3.0
        assert web_manager.cache.max_entries == 100
        print("✓ Web mode: Moderate caching (3s TTL, 100 entries)")
        
        # Test Daemon mode (aggressive caching)
        daemon_manager = SessionManager(OperationMode.DAEMON)
        assert daemon_manager.cache.default_ttl == 30.0
        assert daemon_manager.cache.max_entries == 500
        print("✓ Daemon mode: Aggressive caching (30s TTL, 500 entries)")
    
    print("Cache behavior by mode tests passed!")


def test_mode_aware_cache_operations():
    """Test cache operations are mode-aware"""
    print("\nTesting mode-aware cache operations...")
    
    mock_config = Mock()
    mock_config.get.return_value = "/tmp/test_logs"
    mock_config.get_config_dir.return_value = Path("/tmp/test_config")
    
    mock_tmux_manager = Mock()
    mock_tmux_manager.load_projects.return_value = {"sessions": {}}
    
    mock_server = Mock()
    
    with patch('libs.core.session_manager.YesmanConfig', return_value=mock_config), \
         patch('libs.core.session_manager.TmuxManager', return_value=mock_tmux_manager), \
         patch('libs.core.session_manager.libtmux.Server', return_value=mock_server), \
         patch('libs.core.session_manager.ensure_log_directory'):
        
        # Test CLI mode cache operations
        cli_manager = SessionManager(OperationMode.CLI)
        
        # These should be no-ops in CLI mode
        cli_manager.invalidate_cache()
        cli_manager.invalidate_all_sessions_cache()
        
        stats = cli_manager.get_cache_stats()
        assert stats['cache_enabled'] is False
        print("✓ CLI mode: Cache operations are no-ops")
        
        # Test Web mode cache operations
        web_manager = SessionManager(OperationMode.WEB)
        
        # These should work in Web mode
        web_manager.invalidate_cache()
        web_manager.invalidate_all_sessions_cache()
        
        stats = web_manager.get_cache_stats()
        assert stats['cache_enabled'] is True
        assert stats['mode'] == 'web'
        print("✓ Web mode: Cache operations work normally")
    
    print("Mode-aware cache operations tests passed!")


def test_explicit_mode_override():
    """Test explicit operation mode override"""
    print("\nTesting explicit mode override...")
    
    mock_config = Mock()
    mock_config.get.return_value = "/tmp/test_logs"
    mock_config.get_config_dir.return_value = Path("/tmp/test_config")
    
    mock_tmux_manager = Mock()
    mock_tmux_manager.load_projects.return_value = {"sessions": {}}
    
    mock_server = Mock()
    
    with patch('libs.core.session_manager.YesmanConfig', return_value=mock_config), \
         patch('libs.core.session_manager.TmuxManager', return_value=mock_tmux_manager), \
         patch('libs.core.session_manager.libtmux.Server', return_value=mock_server), \
         patch('libs.core.session_manager.ensure_log_directory'):
        
        # Force CLI mode even in Streamlit environment
        with patch.dict(os.environ, {'STREAMLIT_SERVER_PORT': '8501'}):
            manager = SessionManager(OperationMode.CLI)
            assert manager.operation_mode == OperationMode.CLI
            assert manager.cache is None
            print("✓ Explicit CLI mode override works")
        
        # Force Daemon mode in normal environment
        with patch.dict(os.environ, {}, clear=True):
            manager = SessionManager(OperationMode.DAEMON)
            assert manager.operation_mode == OperationMode.DAEMON
            assert manager.cache is not None
            print("✓ Explicit Daemon mode override works")
    
    print("Explicit mode override tests passed!")


def main():
    """Run all operation mode tests"""
    try:
        test_operation_mode_detection()
        test_cache_behavior_by_mode()
        test_mode_aware_cache_operations()
        test_explicit_mode_override()
        
        print("\n🎉 All operation mode tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())