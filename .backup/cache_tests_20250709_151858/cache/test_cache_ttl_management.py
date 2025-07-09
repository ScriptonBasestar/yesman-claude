#!/usr/bin/env python3
"""Test cache TTL management and health reporting"""

import sys
import time
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.session_cache import SessionCache, InvalidationStrategy, CacheTag


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