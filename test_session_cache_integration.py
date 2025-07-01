#!/usr/bin/env python3
"""Integration test for session manager cache functionality"""

import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.session_manager import SessionManager
from libs.core.session_cache import SessionCache


def test_session_cache_basic():
    """Test basic session cache functionality"""
    print("Testing basic session cache...")
    
    cache = SessionCache(default_ttl=2.0, max_entries=10)
    
    # Test put and get
    cache.put("test_key", {"data": "test_value"})
    result = cache.get("test_key")
    
    assert result is not None
    assert result["data"] == "test_value"
    print("✓ Basic put/get works")
    
    # Test cache stats
    stats = cache.get_stats()
    assert stats.hits == 1
    assert stats.misses == 0
    assert stats.total_entries == 1
    print("✓ Cache stats work")
    
    # Test cache miss
    result = cache.get("nonexistent_key")
    assert result is None
    stats = cache.get_stats()
    assert stats.misses == 1
    print("✓ Cache miss handling works")
    
    # Test get_or_compute
    def compute_func():
        return {"computed": "value"}
    
    result = cache.get_or_compute("computed_key", compute_func)
    assert result["computed"] == "value"
    print("✓ get_or_compute works")
    
    # Test cache hit for computed value
    result2 = cache.get_or_compute("computed_key", compute_func)
    assert result == result2
    stats = cache.get_stats()
    assert stats.hits >= 2
    print("✓ Computed value caching works")
    
    print("Session cache basic tests passed!")


def test_session_manager_cache_integration():
    """Test session manager with cache integration"""
    print("\nTesting session manager cache integration...")
    
    # Mock dependencies
    mock_config = Mock()
    mock_config.get.return_value = "/tmp/test_logs"
    mock_config.get_config_dir.return_value = Path("/tmp/test_config")
    
    mock_tmux_manager = Mock()
    mock_tmux_manager.load_projects.return_value = {
        "sessions": {
            "test_project": {
                "template_name": "test_template"
            }
        }
    }
    
    mock_server = Mock()
    mock_server.find_where.return_value = None  # No running session
    
    # Create session manager with mocks
    with patch('libs.core.session_manager.YesmanConfig', return_value=mock_config), \
         patch('libs.core.session_manager.TmuxManager', return_value=mock_tmux_manager), \
         patch('libs.core.session_manager.libtmux.Server', return_value=mock_server), \
         patch('libs.core.session_manager.ensure_log_directory'):
        
        manager = SessionManager()
        
        # Test cache initialization
        assert manager.cache is not None
        print("✓ SessionManager cache initialized")
        
        # Test get_all_sessions with caching
        sessions1 = manager.get_all_sessions()
        sessions2 = manager.get_all_sessions()
        
        assert len(sessions1) == 1
        assert sessions1[0].project_name == "test_project"
        print("✓ get_all_sessions works with caching")
        
        # Test cache stats
        stats = manager.get_cache_stats()
        assert stats['hits'] >= 1
        assert stats['total_entries'] >= 1
        print("✓ Cache stats accessible through manager")
        
        # Test cache invalidation
        manager.invalidate_cache("test_project")
        stats_after = manager.get_cache_stats()
        assert stats_after['evictions'] >= 1
        print("✓ Cache invalidation works")
        
        print("Session manager cache integration tests passed!")


def test_cache_ttl():
    """Test cache TTL functionality"""
    print("\nTesting cache TTL...")
    
    cache = SessionCache(default_ttl=0.1, max_entries=10)  # Very short TTL
    
    # Put value and get immediately
    cache.put("ttl_test", {"data": "value"})
    result1 = cache.get("ttl_test")
    assert result1 is not None
    print("✓ Immediate retrieval works")
    
    # Wait for TTL expiration
    time.sleep(0.2)
    
    # Should be expired now
    result2 = cache.get("ttl_test")
    assert result2 is None
    print("✓ TTL expiration works")
    
    stats = cache.get_stats()
    assert stats.misses >= 1
    print("✓ TTL expiration updates stats")
    
    print("Cache TTL tests passed!")


def main():
    """Run all tests"""
    try:
        test_session_cache_basic()
        test_session_manager_cache_integration()
        test_cache_ttl()
        
        print("\n🎉 All tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())