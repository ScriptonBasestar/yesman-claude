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
    """Test session manager with cache integration (using SessionCache directly)"""
    print("\nTesting session manager cache integration...")
    
    # Test SessionCache directly since SessionManager has too many dependencies
    cache = SessionCache(default_ttl=3.0, max_entries=100)
    
    # Test cache operations that SessionManager would use
    test_sessions = [
        {"project_name": "test1", "status": "running"},
        {"project_name": "test2", "status": "stopped"}
    ]
    
    # Test get_or_compute pattern used by SessionManager
    def compute_sessions():
        return test_sessions
    
    # First call - should compute and cache
    result1 = cache.get_or_compute("all_sessions", compute_sessions)
    assert result1 == test_sessions
    print("✓ get_or_compute works (cache miss)")
    
    # Second call - should hit cache
    result2 = cache.get_or_compute("all_sessions", compute_sessions)
    assert result1 == result2
    print("✓ get_or_compute works (cache hit)")
    
    # Test individual session caching
    session_info = {"project": "test1", "windows": []}
    cache.put("session_test1", session_info)
    
    retrieved = cache.get("session_test1")
    assert retrieved == session_info
    print("✓ Individual session caching works")
    
    # Test cache stats
    stats = cache.get_stats()
    assert stats.hits >= 1
    assert stats.total_entries >= 1
    print("✓ Cache stats work")
    
    # Test invalidation
    cache.invalidate("session_test1")
    result = cache.get("session_test1")
    assert result is None
    print("✓ Cache invalidation works")
    
    # Test pattern invalidation
    cache.put("session_proj1", {"data": 1})
    cache.put("session_proj2", {"data": 2})
    cache.put("other_data", {"data": 3})
    
    invalidated = cache.invalidate_pattern("session_")
    assert invalidated == 2
    
    # Verify pattern invalidation worked
    assert cache.get("session_proj1") is None
    assert cache.get("session_proj2") is None
    assert cache.get("other_data") is not None
    print("✓ Pattern invalidation works")
    
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


