"""Test session cache functionality"""

import unittest
import time
import threading
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from libs.core.session_cache import SessionCache, CacheEntry, CacheStats


class TestCacheEntry(unittest.TestCase):
    
    def test_cache_entry_creation(self):
        """Test cache entry creation and properties"""
        data = {"test": "data"}
        entry = CacheEntry(data=data, timestamp=time.time())
        
        self.assertEqual(entry.data, data)
        self.assertEqual(entry.access_count, 0)
        self.assertGreater(entry.last_access, 0)
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic"""
        entry = CacheEntry(data="test", timestamp=time.time() - 10)
        
        # Should be expired with 5 second TTL
        self.assertTrue(entry.is_expired(5.0))
        
        # Should not be expired with 15 second TTL
        self.assertFalse(entry.is_expired(15.0))
    
    def test_cache_entry_access_tracking(self):
        """Test access count tracking"""
        entry = CacheEntry(data="test", timestamp=time.time())
        
        initial_access_time = entry.last_access
        time.sleep(0.01)  # Small delay
        
        entry.mark_access()
        
        self.assertEqual(entry.access_count, 1)
        self.assertGreater(entry.last_access, initial_access_time)


class TestSessionCache(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the log directory
        with patch('libs.core.session_cache.get_default_log_path') as mock_log_path:
            mock_log_path.return_value = Path(self.temp_dir)
            self.cache = SessionCache(default_ttl=1.0, max_entries=3)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_cache_put_and_get(self):
        """Test basic cache put and get operations"""
        key = "test_key"
        value = {"session": "data"}
        
        # Put value
        result = self.cache.put(key, value)
        self.assertTrue(result)
        
        # Get value
        cached_value = self.cache.get(key)
        self.assertEqual(cached_value, value)
        
        # Check stats
        stats = self.cache.get_stats()
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.misses, 0)
    
    def test_cache_miss(self):
        """Test cache miss behavior"""
        cached_value = self.cache.get("nonexistent_key")
        self.assertIsNone(cached_value)
        
        # Check stats
        stats = self.cache.get_stats()
        self.assertEqual(stats.hits, 0)
        self.assertEqual(stats.misses, 1)
    
    def test_cache_expiration(self):
        """Test cache entry expiration"""
        key = "expiring_key"
        value = "test_value"
        
        # Put with short TTL
        self.cache.put(key, value)
        
        # Should get value immediately
        cached_value = self.cache.get(key)
        self.assertEqual(cached_value, value)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should return None after expiration
        cached_value = self.cache.get(key)
        self.assertIsNone(cached_value)
        
        # Should count as miss and eviction
        stats = self.cache.get_stats()
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.misses, 1)
        self.assertEqual(stats.evictions, 1)
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        # Fill cache to max capacity (3 entries)
        for i in range(3):
            self.cache.put(f"key_{i}", f"value_{i}")
        
        # Access key_1 to make it more recent
        self.cache.get("key_1")
        
        # Add one more entry, should evict LRU (key_0)
        self.cache.put("key_3", "value_3")
        
        # key_0 should be evicted
        self.assertIsNone(self.cache.get("key_0"))
        
        # key_1 should still exist (was accessed recently)
        self.assertEqual(self.cache.get("key_1"), "value_1")
        
        # key_3 should exist (newly added)
        self.assertEqual(self.cache.get("key_3"), "value_3")
        
        # Check eviction count
        stats = self.cache.get_stats()
        self.assertEqual(stats.evictions, 1)
    
    def test_cache_invalidation(self):
        """Test cache invalidation"""
        key = "test_key"
        value = "test_value"
        
        self.cache.put(key, value)
        self.assertEqual(self.cache.get(key), value)
        
        # Invalidate
        result = self.cache.invalidate(key)
        self.assertTrue(result)
        
        # Should return None after invalidation
        self.assertIsNone(self.cache.get(key))
        
        # Invalidating non-existent key should return False
        result = self.cache.invalidate("nonexistent")
        self.assertFalse(result)
    
    def test_cache_pattern_invalidation(self):
        """Test pattern-based invalidation"""
        # Put multiple entries
        self.cache.put("session_1", "data_1")
        self.cache.put("session_2", "data_2")
        self.cache.put("config_1", "config_data")
        
        # Invalidate all session entries
        invalidated_count = self.cache.invalidate_pattern("session_")
        self.assertEqual(invalidated_count, 2)
        
        # Session entries should be gone
        self.assertIsNone(self.cache.get("session_1"))
        self.assertIsNone(self.cache.get("session_2"))
        
        # Config entry should remain
        self.assertEqual(self.cache.get("config_1"), "config_data")
    
    def test_cache_clear(self):
        """Test cache clear operation"""
        # Add some entries
        for i in range(3):
            self.cache.put(f"key_{i}", f"value_{i}")
        
        # Clear cache
        cleared_count = self.cache.clear()
        self.assertEqual(cleared_count, 3)
        
        # All entries should be gone
        for i in range(3):
            self.assertIsNone(self.cache.get(f"key_{i}"))
        
        # Stats should reflect clearing
        stats = self.cache.get_stats()
        self.assertEqual(stats.total_entries, 0)
    
    def test_get_or_compute(self):
        """Test get_or_compute functionality"""
        key = "computed_key"
        
        def compute_func():
            return "computed_value"
        
        # First call should compute and cache
        result = self.cache.get_or_compute(key, compute_func)
        self.assertEqual(result, "computed_value")
        
        # Second call should return cached value
        result = self.cache.get_or_compute(key, lambda: "different_value")
        self.assertEqual(result, "computed_value")  # Should be cached value
        
        # Check that we had one miss (first call) and one hit (second call)
        stats = self.cache.get_stats()
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.misses, 1)
    
    def test_get_or_compute_exception(self):
        """Test get_or_compute with exception in compute function"""
        key = "error_key"
        
        def failing_compute():
            raise ValueError("Computation failed")
        
        # Should raise the exception
        with self.assertRaises(ValueError):
            self.cache.get_or_compute(key, failing_compute)
        
        # Key should not be cached
        self.assertIsNone(self.cache.get(key))
    
    def test_content_hash_detection(self):
        """Test content hash detection for unchanged data"""
        key = "hash_test"
        value = {"data": "test"}
        
        # First put
        self.cache.put(key, value)
        entry1 = self.cache._cache[key]
        original_timestamp = entry1.timestamp
        
        # Small delay
        time.sleep(0.01)
        
        # Put same content again
        self.cache.put(key, value)
        entry2 = self.cache._cache[key]
        
        # Should be same entry (hash unchanged)
        self.assertIs(entry1, entry2)
        # But timestamp should be updated
        self.assertGreater(entry2.timestamp, original_timestamp)
    
    def test_thread_safety(self):
        """Test thread safety of cache operations"""
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(10):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"
                    
                    self.cache.put(key, value)
                    retrieved = self.cache.get(key)
                    
                    if retrieved == value:
                        results.append(True)
                    else:
                        results.append(False)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")
        self.assertTrue(all(results), "Some thread operations failed")
    
    def test_stats_export(self):
        """Test statistics export"""
        # Add some data and operations
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.get("key1")  # hit
        self.cache.get("nonexistent")  # miss
        
        # Export stats
        stats_json = self.cache.export_stats_json()
        self.assertIsInstance(stats_json, str)
        
        # Should be valid JSON
        import json
        stats_data = json.loads(stats_json)
        
        self.assertEqual(stats_data['hits'], 1)
        self.assertEqual(stats_data['misses'], 1)
        self.assertEqual(stats_data['total_entries'], 2)
        self.assertIn('key1', stats_data['cache_keys'])
        self.assertIn('key2', stats_data['cache_keys'])


if __name__ == '__main__':
    unittest.main()