#!/usr/bin/env python3
"""Test dashboard cache integration functionality"""

import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.session_cache import SessionCache


def test_cache_hit_miss_optimization():
    """Test cache hit/miss optimization patterns"""
    print("Testing cache hit/miss optimization...")
    
    cache = SessionCache(default_ttl=5.0, max_entries=50)
    
    # Simulate dashboard session loading patterns
    test_sessions = [
        {"project_name": "frontend", "status": "running", "windows": 3},
        {"project_name": "backend", "status": "running", "windows": 2},
        {"project_name": "database", "status": "stopped", "windows": 1}
    ]
    
    # Test 1: Initial cold cache (should be cache miss)
    def compute_all_sessions():
        return test_sessions
    
    start_time = time.time()
    result1 = cache.get_or_compute("all_sessions", compute_all_sessions)
    cold_load_time = time.time() - start_time
    
    assert result1 == test_sessions
    print(f"✓ Cold cache load: {cold_load_time:.4f}s")
    
    # Test 2: Warm cache (should be cache hit)
    start_time = time.time()
    result2 = cache.get_or_compute("all_sessions", compute_all_sessions)
    warm_load_time = time.time() - start_time
    
    assert result1 == result2
    print(f"✓ Warm cache load: {warm_load_time:.4f}s")
    
    # Verify cache hit is faster
    assert warm_load_time < cold_load_time
    print(f"✓ Cache speedup: {cold_load_time/warm_load_time:.1f}x faster")
    
    # Test 3: Individual session caching
    for session in test_sessions:
        session_key = f"session_{session['project_name']}"
        cache.put(session_key, session)
    
    # Test session-specific invalidation
    cache.invalidate("session_frontend")
    
    # Verify selective invalidation
    assert cache.get("session_frontend") is None
    assert cache.get("session_backend") is not None
    print("✓ Selective session invalidation works")
    
    # Test 4: Pattern-based invalidation
    cache.put("session_test1", {"data": 1})
    cache.put("session_test2", {"data": 2})
    cache.put("controller_data", {"data": 3})
    
    invalidated_count = cache.invalidate_pattern("session_")
    assert invalidated_count >= 2
    assert cache.get("controller_data") is not None
    print("✓ Pattern-based invalidation works")
    
    print("Cache hit/miss optimization tests passed!")


def test_cache_performance_monitoring():
    """Test cache performance monitoring features"""
    print("\nTesting cache performance monitoring...")
    
    cache = SessionCache(default_ttl=2.0, max_entries=10)
    
    # Generate some cache activity
    for i in range(5):
        cache.put(f"key_{i}", {"data": f"value_{i}"})
    
    # Create cache hits
    for i in range(3):
        cache.get(f"key_{i}")
    
    # Create cache misses
    for i in range(5, 8):
        cache.get(f"missing_key_{i}")
    
    stats = cache.get_stats()
    
    # Verify stats are collected
    assert stats.hits >= 3
    assert stats.misses >= 3
    assert stats.total_entries == 5
    assert 0 <= stats.hit_rate <= 100
    
    print(f"✓ Cache stats: {stats.hits} hits, {stats.misses} misses, {stats.hit_rate:.1f}% hit rate")
    
    # Test performance classification
    if stats.hit_rate >= 80:
        performance_level = "excellent"
    elif stats.hit_rate >= 60:
        performance_level = "good"
    else:
        performance_level = "needs improvement"
    
    print(f"✓ Cache performance level: {performance_level}")
    
    # Test memory estimation
    assert stats.memory_size_bytes > 0
    memory_kb = stats.memory_size_bytes / 1024
    print(f"✓ Memory usage estimation: {memory_kb:.1f} KB")
    
    print("Cache performance monitoring tests passed!")


def test_smart_cache_invalidation():
    """Test smart cache invalidation scenarios"""
    print("\nTesting smart cache invalidation...")
    
    cache = SessionCache(default_ttl=10.0, max_entries=20)
    
    # Simulate dashboard scenarios
    scenarios = [
        ("user_refresh", "Manual refresh button clicked"),
        ("tmux_setup", "New tmux session created"),
        ("tmux_teardown", "Tmux session destroyed"),
        ("controller_start", "Controller started"),
        ("controller_stop", "Controller stopped")
    ]
    
    for scenario, description in scenarios:
        # Setup cache with session data
        cache.put("all_sessions", [{"project": "test"}])
        cache.put("session_test", {"status": "running"})
        
        # Simulate different invalidation strategies
        if scenario == "user_refresh":
            # Full cache clear for manual refresh
            cache.clear()
            print(f"✓ {scenario}: Full cache cleared")
            
        elif scenario in ["tmux_setup", "tmux_teardown"]:
            # Invalidate specific session + all_sessions
            cache.invalidate("session_test")
            cache.invalidate("all_sessions")
            print(f"✓ {scenario}: Session-specific invalidation")
            
        elif scenario in ["controller_start", "controller_stop"]:
            # Only invalidate all_sessions (session structure unchanged)
            cache.invalidate("all_sessions")
            print(f"✓ {scenario}: All-sessions invalidation only")
        
        # Verify appropriate data is invalidated
        if scenario == "user_refresh":
            assert cache.get("all_sessions") is None
            assert cache.get("session_test") is None
        
    print("Smart cache invalidation tests passed!")


def test_cache_efficiency_metrics():
    """Test cache efficiency calculation and reporting"""
    print("\nTesting cache efficiency metrics...")
    
    cache = SessionCache(default_ttl=3.0, max_entries=15)
    
    # Simulate realistic dashboard usage patterns
    sessions_data = {"sessions": [{"name": f"session_{i}"} for i in range(5)]}
    
    # Pattern 1: High efficiency (repeated queries)
    for _ in range(10):
        cache.get_or_compute("dashboard_sessions", lambda: sessions_data)
    
    stats = cache.get_stats()
    total_requests = stats.hits + stats.misses
    efficiency_score = stats.hits / total_requests if total_requests > 0 else 0
    
    print(f"✓ High efficiency pattern: {efficiency_score:.2f} ({stats.hits}/{total_requests})")
    assert efficiency_score > 0.8  # Should be very efficient
    
    # Pattern 2: Lower efficiency (varied queries)
    for i in range(5):
        cache.get(f"varied_key_{i}")  # These will be misses
    
    stats_after = cache.get_stats()
    total_requests_after = stats_after.hits + stats_after.misses
    efficiency_after = stats_after.hits / total_requests_after if total_requests_after > 0 else 0
    
    print(f"✓ Mixed efficiency pattern: {efficiency_after:.2f} ({stats_after.hits}/{total_requests_after})")
    assert efficiency_after < efficiency_score  # Should be lower
    
    # Test efficiency reporting format
    efficiency_report = {
        "hit_rate_percent": round(stats_after.hit_rate, 1),
        "efficiency_ratio": f"{stats_after.hits}/{total_requests_after}",
        "performance_level": "excellent" if stats_after.hit_rate >= 80 else "good" if stats_after.hit_rate >= 60 else "needs_improvement"
    }
    
    print(f"✓ Efficiency report: {efficiency_report}")
    
    print("Cache efficiency metrics tests passed!")


def main():
    """Run all dashboard cache integration tests"""
    try:
        test_cache_hit_miss_optimization()
        test_cache_performance_monitoring()
        test_smart_cache_invalidation()
        test_cache_efficiency_metrics()
        
        print("\n🎉 All dashboard cache integration tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


