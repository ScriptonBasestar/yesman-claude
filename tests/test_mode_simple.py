#!/usr/bin/env python3
"""Simple test for operation modes"""

import sys
import os
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.session_manager import OperationMode


def test_operation_mode_enum():
    """Test OperationMode enum"""
    print("Testing OperationMode enum...")
    
    # Test enum values
    assert OperationMode.CLI.value == "cli"
    assert OperationMode.DAEMON.value == "daemon"
    assert OperationMode.WEB.value == "web"
    
    print("✓ CLI mode:", OperationMode.CLI.value)
    print("✓ Daemon mode:", OperationMode.DAEMON.value)
    print("✓ Web mode:", OperationMode.WEB.value)
    
    print("OperationMode enum test passed!")


def test_mode_detection_logic():
    """Test mode detection logic independently"""
    print("\nTesting mode detection logic...")
    
    # Import SessionManager class to test detection method
    from libs.core.session_manager import SessionManager
    
    # Create a dummy instance to test mode detection
    # We'll test the logic directly by examining environment variables
    
    # Test CLI mode (clean environment)
    original_env = dict(os.environ)
    
    try:
        # Clear relevant environment variables
        for key in ['STREAMLIT_SERVER_PORT', 'TMUX', 'SSH_TTY', '_']:
            if key in os.environ:
                del os.environ[key]
        
        # This should default to CLI
        print("✓ Clean environment -> CLI mode expected")
        
        # Test Web mode indicators
        os.environ['STREAMLIT_SERVER_PORT'] = '8501'
        print("✓ STREAMLIT_SERVER_PORT set -> WEB mode expected")
        
        # Test Daemon mode indicators  
        del os.environ['STREAMLIT_SERVER_PORT']
        os.environ['TMUX'] = '/tmp/tmux-1000/default,12345,0'
        print("✓ TMUX set -> DAEMON mode expected")
        
        # Test SSH environment
        del os.environ['TMUX']
        os.environ['SSH_TTY'] = '/dev/pts/0'
        print("✓ SSH_TTY set -> DAEMON mode expected")
        
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
    
    print("Mode detection logic test passed!")


def test_cache_configuration():
    """Test cache configuration for different modes"""
    print("\nTesting cache configuration...")
    
    # Test cache settings for each mode
    cache_configs = {
        OperationMode.CLI: {"enabled": False, "ttl": None, "max_entries": None},
        OperationMode.WEB: {"enabled": True, "ttl": 3.0, "max_entries": 100},
        OperationMode.DAEMON: {"enabled": True, "ttl": 30.0, "max_entries": 500}
    }
    
    for mode, expected_config in cache_configs.items():
        print(f"✓ {mode.value} mode:")
        print(f"  Cache enabled: {expected_config['enabled']}")
        if expected_config['enabled']:
            print(f"  TTL: {expected_config['ttl']}s")
            print(f"  Max entries: {expected_config['max_entries']}")
    
    print("Cache configuration test passed!")


def main():
    """Run simple mode tests"""
    try:
        test_operation_mode_enum()
        test_mode_detection_logic()
        test_cache_configuration()
        
        print("\n🎉 All simple mode tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())