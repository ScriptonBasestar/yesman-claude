#!/usr/bin/env python3
"""Test cache visualization and logging features"""

import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch
import json

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.session_cache import SessionCache


def test_cache_status_logging():
    """Test cache status logging functionality"""
    print("Testing cache status logging...")
    
    cache = SessionCache(default_ttl=5.0, max_entries=20)
    
    # Add some test data
    test_data = [
        {"project": "frontend", "status": "running"},
        {"project": "backend", "status": "running"},
        {"project": "database", "status": "stopped"}
    ]
    
    for i, data in enumerate(test_data):
        cache.put(f"session_{i}", data)
    
    # Generate some cache activity
    for i in range(3):
        cache.get(f"session_{i}")  # hits
    
    for i in range(5, 8):
        cache.get(f"missing_{i}")  # misses
    
    # Test comprehensive status logging
    cache.log_cache_status("test_operation")
    print("✓ Comprehensive status logging completed")
    
    # Test periodic logging
    cache.log_periodic_status(force=True)
    print("✓ Periodic status logging completed")
    
    print("Cache status logging tests passed!")


def test_visual_status_summary():
    """Test visual status summary for dashboard"""
    print("\nTesting visual status summary...")
    
    cache = SessionCache(default_ttl=10.0, max_entries=10)
    
    # Test empty cache
    empty_status = cache.get_visual_status_summary()
    assert 'performance' in empty_status
    assert 'capacity' in empty_status
    assert 'memory' in empty_status
    assert 'activity' in empty_status
    assert 'freshness' in empty_status
    print("✓ Empty cache visual status")
    
    # Add data to test different performance levels
    for i in range(5):
        cache.put(f"key_{i}", {"data": f"value_{i}"})
    
    # Create hits for good performance
    for i in range(5):
        cache.get(f"key_{i}")
    
    good_status = cache.get_visual_status_summary()
    
    # Verify performance indicators
    assert good_status['performance']['emoji'] in ['🟢', '🟡', '🟠', '🔴']
    assert good_status['performance']['hit_rate'] > 0
    print(f"✓ Performance indicator: {good_status['performance']['emoji']} {good_status['performance']['text']}")
    
    # Verify capacity indicators
    assert good_status['capacity']['emoji'] in ['🟢', '🟡', '🔴']
    assert good_status['capacity']['usage_percent'] >= 0
    print(f"✓ Capacity indicator: {good_status['capacity']['emoji']} {good_status['capacity']['usage_percent']}%")
    
    # Verify memory indicators
    assert good_status['memory']['size_kb'] >= 0
    assert good_status['memory']['avg_entry_bytes'] >= 0
    print(f"✓ Memory usage: {good_status['memory']['size_kb']} KB")
    
    # Verify timestamp
    assert 'last_update_formatted' in good_status
    print(f"✓ Last update: {good_status['last_update_formatted']}")
    
    print("Visual status summary tests passed!")


def test_performance_classification():
    """Test performance level classification"""
    print("\nTesting performance classification...")
    
    cache = SessionCache(default_ttl=2.0, max_entries=10)
    
    # Test excellent performance (>80% hit rate)
    for i in range(5):
        cache.put(f"excellent_{i}", f"data_{i}")
    
    # Generate many hits
    for _ in range(10):
        for i in range(5):
            cache.get(f"excellent_{i}")
    
    excellent_status = cache.get_visual_status_summary()
    if excellent_status['performance']['hit_rate'] >= 80:
        assert excellent_status['performance']['emoji'] == '🟢'
        assert excellent_status['performance']['text'] == 'Excellent'
        print("✓ Excellent performance classification")
    
    # Test poor performance (many misses)
    cache.clear()
    cache.put("single_key", "data")
    
    # Generate many misses
    for i in range(20):
        cache.get(f"missing_{i}")
    
    # One hit
    cache.get("single_key")
    
    poor_status = cache.get_visual_status_summary()
    if poor_status['performance']['hit_rate'] < 40:
        assert poor_status['performance']['emoji'] == '🔴'
        assert poor_status['performance']['text'] == 'Poor'
        print("✓ Poor performance classification")
    
    print("Performance classification tests passed!")


def test_capacity_monitoring():
    """Test capacity monitoring and indicators"""
    print("\nTesting capacity monitoring...")
    
    cache = SessionCache(default_ttl=5.0, max_entries=10)
    
    # Test normal capacity
    for i in range(3):
        cache.put(f"normal_{i}", f"data_{i}")
    
    normal_status = cache.get_visual_status_summary()
    assert normal_status['capacity']['usage_percent'] < 70
    assert normal_status['capacity']['emoji'] == '🟢'
    print(f"✓ Normal capacity: {normal_status['capacity']['usage_percent']}%")
    
    # Test high capacity
    for i in range(7):
        cache.put(f"high_{i}", f"data_{i}")
    
    high_status = cache.get_visual_status_summary()
    if high_status['capacity']['usage_percent'] >= 70:
        assert high_status['capacity']['emoji'] in ['🟡', '🔴']
        print(f"✓ High capacity: {high_status['capacity']['usage_percent']}%")
    
    print("Capacity monitoring tests passed!")


def test_cache_age_tracking():
    """Test cache entry age tracking"""
    print("\nTesting cache age tracking...")
    
    cache = SessionCache(default_ttl=5.0, max_entries=10)
    
    # Add entries with time gaps
    cache.put("old_entry", "old_data")
    time.sleep(0.1)
    cache.put("new_entry", "new_data")
    
    status = cache.get_visual_status_summary()
    
    # Should have freshness information
    assert 'freshness' in status
    assert status['freshness']['oldest_age_seconds'] >= 0
    assert status['freshness']['ttl_seconds'] == 5.0
    print(f"✓ Cache age tracking: oldest={status['freshness']['oldest_age_seconds']:.1f}s")
    
    print("Cache age tracking tests passed!")


def test_dashboard_integration():
    """Test integration with dashboard requirements"""
    print("\nTesting dashboard integration...")
    
    cache = SessionCache(default_ttl=3.0, max_entries=100)
    
    # Simulate dashboard usage
    dashboard_data = {
        "sessions": [
            {"name": "frontend", "status": "running"},
            {"name": "backend", "status": "running"}
        ]
    }
    
    # Multiple dashboard requests (should be cached)
    for i in range(5):
        cache.put("dashboard_sessions", dashboard_data)
        cached_data = cache.get("dashboard_sessions")
        assert cached_data == dashboard_data
    
    # Get visual status for dashboard display
    visual_status = cache.get_visual_status_summary()
    
    # Verify dashboard-friendly format
    required_fields = [
        'performance', 'capacity', 'memory', 'activity', 
        'freshness', 'last_update_formatted'
    ]
    
    for field in required_fields:
        assert field in visual_status
    
    # Test emoji indicators for UI
    assert visual_status['performance']['emoji'] in ['🟢', '🟡', '🟠', '🔴']
    assert visual_status['capacity']['emoji'] in ['🟢', '🟡', '🔴']
    
    print("✓ Dashboard integration format verified")
    print(f"✓ Dashboard status: {visual_status['performance']['emoji']} "
          f"{visual_status['performance']['hit_rate']}% hit rate")
    
    print("Dashboard integration tests passed!")


def main():
    """Run all cache visualization tests"""
    try:
        test_cache_status_logging()
        test_visual_status_summary()
        test_performance_classification()
        test_capacity_monitoring()
        test_cache_age_tracking()
        test_dashboard_integration()
        
        print("\n🎉 All cache visualization tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())