#!/usr/bin/env python3
"""Test advanced cache TTL and invalidation strategies"""

import sys
import time
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.session_cache import SessionCache, InvalidationStrategy, CacheTag


def test_invalidation_strategies():
    """Test different invalidation strategies"""
    print("Testing invalidation strategies...")
    
    cache = SessionCache(default_ttl=5.0, max_entries=20)
    
    # Test TIME_BASED strategy (default)
    cache.put_with_strategy("time_based", {"data": "value1"}, 
                           strategy=InvalidationStrategy.TIME_BASED, ttl=1.0)
    
    assert cache.get("time_based") is not None
    time.sleep(1.1)
    assert cache.get("time_based") is None  # Should be expired
    print("✓ TIME_BASED strategy works")
    
    # Test MANUAL strategy
    cache.put_with_strategy("manual", {"data": "value2"}, 
                           strategy=InvalidationStrategy.MANUAL)
    
    time.sleep(0.1)  # Wait but should not expire
    assert cache.get("manual") is not None
    print("✓ MANUAL strategy works (no expiration)")
    
    # Test CONTENT_CHANGE strategy
    def simple_change_detector(old_data, new_data):
        return old_data['data'] != new_data['data']
    
    cache.put_with_strategy("content_change", {"data": "original"}, 
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           change_detector=simple_change_detector)
    
    # Same content should not update cache
    cache.put_with_strategy("content_change", {"data": "original"}, 
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           change_detector=simple_change_detector)
    
    # Different content should update cache
    cache.put_with_strategy("content_change", {"data": "modified"}, 
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           change_detector=simple_change_detector)
    
    assert cache.get("content_change")["data"] == "modified"
    print("✓ CONTENT_CHANGE strategy works")
    
    print("Invalidation strategies tests passed!")


def test_tag_based_invalidation():
    """Test tag-based cache invalidation"""
    print("\nTesting tag-based invalidation...")
    
    cache = SessionCache(default_ttl=10.0, max_entries=20)
    
    # Add entries with different tags
    cache.put_with_strategy("session1", {"name": "frontend"}, 
                           tags={CacheTag.SESSION_DATA, CacheTag.SESSION_STATUS})
    cache.put_with_strategy("session2", {"name": "backend"}, 
                           tags={CacheTag.SESSION_DATA})
    cache.put_with_strategy("controller1", {"status": "running"}, 
                           tags={CacheTag.CONTROLLER_STATE})
    
    # Verify all entries exist
    assert cache.get("session1") is not None
    assert cache.get("session2") is not None
    assert cache.get("controller1") is not None
    print("✓ Entries stored with tags")
    
    # Invalidate by SESSION_DATA tag
    invalidated = cache.invalidate_by_tag(CacheTag.SESSION_DATA)
    assert invalidated == 2
    
    # Verify correct entries were invalidated
    assert cache.get("session1") is None
    assert cache.get("session2") is None
    assert cache.get("controller1") is not None  # Should still exist
    print("✓ Tag-based invalidation works")
    
    print("Tag-based invalidation tests passed!")


def test_dependency_invalidation():
    """Test dependency-based invalidation"""
    print("\nTesting dependency invalidation...")
    
    cache = SessionCache(default_ttl=10.0, max_entries=20)
    
    # Add entries with dependencies
    cache.put_with_strategy("global_config", {"setting": "value"})
    
    cache.put_with_strategy("session_list", {"sessions": ["s1", "s2"]}, 
                           dependencies={"global_config"})
    
    cache.put_with_strategy("session_detail", {"details": "info"}, 
                           dependencies={"session_list", "global_config"})
    
    # Verify all entries exist
    assert cache.get("global_config") is not None
    assert cache.get("session_list") is not None
    assert cache.get("session_detail") is not None
    print("✓ Entries stored with dependencies")
    
    # Update global_config - should invalidate dependents
    cache.put_with_strategy("global_config", {"setting": "new_value"})
    
    # Verify dependents were invalidated
    assert cache.get("global_config") is not None  # Should exist (just updated)
    assert cache.get("session_list") is None       # Should be invalidated
    assert cache.get("session_detail") is None     # Should be invalidated
    print("✓ Dependency-based invalidation works")
    
    print("Dependency invalidation tests passed!")


def test_custom_ttl():
    """Test custom TTL for individual entries"""
    print("\nTesting custom TTL...")
    
    cache = SessionCache(default_ttl=5.0, max_entries=20)
    
    # Entry with short custom TTL
    cache.put_with_strategy("short_ttl", {"data": "expires_soon"}, ttl=0.5)
    
    # Entry with long custom TTL
    cache.put_with_strategy("long_ttl", {"data": "expires_later"}, ttl=10.0)
    
    # Entry with default TTL
    cache.put("default_ttl", {"data": "default"})
    
    # Wait for short TTL to expire
    time.sleep(0.6)
    
    assert cache.get("short_ttl") is None      # Should be expired
    assert cache.get("long_ttl") is not None  # Should still exist
    assert cache.get("default_ttl") is not None  # Should still exist
    print("✓ Custom TTL works")
    
    # Test TTL modification
    cache.set_ttl_for_key("long_ttl", 0.1)  # Make it expire soon
    time.sleep(0.2)
    assert cache.get("long_ttl") is None  # Should now be expired
    print("✓ TTL modification works")
    
    # Test TTL extension
    cache.put("extend_test", {"data": "extend_me"})
    cache.extend_ttl("extend_test", 10.0)  # Extend by 10 seconds
    
    # Entry should still exist after default TTL would have expired
    time.sleep(0.1)  # Small delay
    assert cache.get("extend_test") is not None
    print("✓ TTL extension works")
    
    print("Custom TTL tests passed!")


def test_entry_info_and_health_report():
    """Test entry information and health reporting"""
    print("\nTesting entry info and health reporting...")
    
    cache = SessionCache(default_ttl=5.0, max_entries=10)
    
    # Add entries with various configurations
    cache.put_with_strategy("info_test", {"data": "test"}, 
                           ttl=10.0,
                           tags={CacheTag.SESSION_DATA},
                           dependencies={"dependency_key"})
    
    # Test entry info
    entry_info = cache.get_entry_info("info_test")
    assert entry_info is not None
    assert entry_info['key'] == "info_test"
    assert entry_info['custom_ttl'] == 10.0
    assert CacheTag.SESSION_DATA in entry_info['tags']
    assert 'dependency_key' in entry_info['dependencies']
    assert entry_info['age_seconds'] >= 0
    assert entry_info['time_to_expire'] > 0
    print("✓ Entry info retrieval works")
    
    # Add more entries for health report
    for i in range(5):
        cache.put_with_strategy(f"health_test_{i}", {"data": i}, 
                               tags={CacheTag.SESSION_STATUS})
    
    # Generate cache hits and misses
    for i in range(3):
        cache.get(f"health_test_{i}")  # hits
    
    for i in range(5, 8):
        cache.get(f"missing_{i}")  # misses
    
    # Test health report
    health_report = cache.get_cache_health_report()
    
    assert 'basic_stats' in health_report
    assert 'advanced_stats' in health_report
    assert 'health_indicators' in health_report
    
    basic_stats = health_report['basic_stats']
    assert basic_stats['total_entries'] > 0
    assert basic_stats['hits'] >= 3
    assert basic_stats['misses'] >= 3
    
    advanced_stats = health_report['advanced_stats']
    assert 'strategy_distribution' in advanced_stats
    assert 'tag_distribution' in advanced_stats
    
    health_indicators = health_report['health_indicators']
    assert health_indicators['cache_efficiency'] in ['good', 'needs_improvement']
    
    print("✓ Health report generation works")
    print(f"  Cache efficiency: {health_indicators['cache_efficiency']}")
    print(f"  Total entries: {basic_stats['total_entries']}")
    print(f"  Hit rate: {basic_stats['hit_rate']:.1f}%")
    
    print("Entry info and health reporting tests passed!")


def test_session_change_detection():
    """Test session change detection scenario"""
    print("\nTesting session change detection scenario...")
    
    cache = SessionCache(default_ttl=10.0, max_entries=20)
    
    # Simulate session data change detection
    def session_change_detector(old_session, new_session):
        """Detect if session status or window configuration changed"""
        if old_session.get('status') != new_session.get('status'):
            return True
        if len(old_session.get('windows', [])) != len(new_session.get('windows', [])):
            return True
        return False
    
    # Initial session state
    initial_session = {
        'name': 'frontend',
        'status': 'running',
        'windows': ['main', 'debug']
    }
    
    cache.put_with_strategy("session_frontend", initial_session,
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           tags={CacheTag.SESSION_DATA, CacheTag.SESSION_STATUS},
                           change_detector=session_change_detector)
    
    # Try to update with same data (should not change)
    same_session = initial_session.copy()
    cache.put_with_strategy("session_frontend", same_session,
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           change_detector=session_change_detector)
    
    # Verify timestamp wasn't changed significantly
    info1 = cache.get_entry_info("session_frontend")
    print("✓ No update for unchanged session data")
    
    # Update with status change
    changed_session = initial_session.copy()
    changed_session['status'] = 'stopped'
    
    cache.put_with_strategy("session_frontend", changed_session,
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           change_detector=session_change_detector)
    
    updated_data = cache.get("session_frontend")
    assert updated_data['status'] == 'stopped'
    print("✓ Session status change detected and updated")
    
    # Update with window change
    window_changed_session = changed_session.copy()
    window_changed_session['windows'] = ['main', 'debug', 'test']
    
    cache.put_with_strategy("session_frontend", window_changed_session,
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           change_detector=session_change_detector)
    
    updated_data = cache.get("session_frontend")
    assert len(updated_data['windows']) == 3
    print("✓ Session window change detected and updated")
    
    print("Session change detection tests passed!")


def main():
    """Run all advanced cache strategy tests"""
    try:
        test_invalidation_strategies()
        test_tag_based_invalidation()
        test_dependency_invalidation()
        test_custom_ttl()
        test_entry_info_and_health_report()
        test_session_change_detection()
        
        print("\n🎉 All advanced cache strategy tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())