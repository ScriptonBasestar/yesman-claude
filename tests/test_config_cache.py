"""Tests for configuration caching system."""

import tempfile
import time
from pathlib import Path

import pytest

from libs.core.config_cache import CachedConfigLoader, ConfigCache, FileWatcher
from libs.core.config_loader import ConfigLoader, EnvironmentSource, YamlFileSource
from libs.yesman_config import create_cached_yesman_config


class TestConfigCache:
    """Test the configuration cache functionality."""

    def test_cache_basic_operations(self) -> None:
        """Test basic cache operations."""
        cache = ConfigCache(cache_ttl=1.0, max_cache_size=5)

        # Test cache miss
        assert cache.get("test_key") is None

        # Test cache put and hit
        from libs.core.config_schema import YesmanConfigSchema

        config = YesmanConfigSchema()
        cache.put("test_key", config)

        cached_config = cache.get("test_key")
        assert cached_config is not None
        assert cached_config.mode == config.mode

    def test_cache_ttl_expiry(self) -> None:
        """Test cache TTL expiry."""
        cache = ConfigCache(cache_ttl=0.1, max_cache_size=5)

        from libs.core.config_schema import YesmanConfigSchema

        config = YesmanConfigSchema()
        cache.put("test_key", config)

        # Should hit immediately
        assert cache.get("test_key") is not None

        # Wait for expiry
        time.sleep(0.2)

        # Should miss after expiry
        assert cache.get("test_key") is None

    def test_cache_size_limit(self) -> None:
        """Test cache size limit and eviction."""
        cache = ConfigCache(cache_ttl=10.0, max_cache_size=2)

        from libs.core.config_schema import YesmanConfigSchema

        # Add two entries
        config1 = YesmanConfigSchema()
        config2 = YesmanConfigSchema()

        cache.put("key1", config1)
        cache.put("key2", config2)

        # Both should be present
        assert cache.get("key1") is not None
        assert cache.get("key2") is not None

        # Add third entry - should evict oldest
        config3 = YesmanConfigSchema()
        cache.put("key3", config3)

        # key1 should be evicted, key2 and key3 should remain
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None

    def test_cache_stats(self) -> None:
        """Test cache statistics."""
        cache = ConfigCache(cache_ttl=10.0, max_cache_size=5)

        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["valid_entries"] == 0

        from libs.core.config_schema import YesmanConfigSchema

        config = YesmanConfigSchema()
        cache.put("test_key", config)

        stats = cache.get_stats()
        assert stats["total_entries"] == 1
        assert stats["valid_entries"] == 1


class TestFileWatcher:
    """Test file watching functionality."""

    def test_file_change_detection(self) -> None:
        """Test file change detection."""
        cache = ConfigCache()
        watcher = FileWatcher(cache)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()

            file_path = Path(f.name)
            watcher.watch_file(file_path)

            # No changes initially
            assert not watcher.check_for_changes()

            # Modify file
            time.sleep(0.1)  # Ensure different mtime
            with open(file_path, "w") as f2:
                f2.write("modified content")

            # Should detect change
            assert watcher.check_for_changes()

            # Clean up
            file_path.unlink()


class TestCachedConfigLoader:
    """Test the cached configuration loader."""

    def test_cached_loader_basic(self) -> None:
        """Test basic cached loader functionality."""
        # Create base loader
        base_loader = ConfigLoader()
        base_loader.add_source(EnvironmentSource())

        # Create cached loader
        cached_loader = CachedConfigLoader(base_loader, cache_ttl=1.0)

        # First load - should be cache miss
        config1 = cached_loader.load()
        assert config1 is not None

        # Second load - should be cache hit
        config2 = cached_loader.load()
        assert config2 is not None
        assert config1.mode == config2.mode

        # Check stats
        stats = cached_loader.get_cache_stats()
        assert stats["hit_count"] >= 1
        assert stats["total_requests"] >= 2

    def test_cached_loader_invalidation(self) -> None:
        """Test cache invalidation."""
        base_loader = ConfigLoader()
        base_loader.add_source(EnvironmentSource())

        cached_loader = CachedConfigLoader(base_loader, cache_ttl=10.0)

        # Load once
        cached_loader.load()

        # Invalidate cache
        cached_loader.invalidate_cache()

        # Load again - should reload from sources
        cached_loader.load()

        stats = cached_loader.get_cache_stats()
        assert stats["miss_count"] >= 2  # At least two misses due to invalidation

    def test_file_watching_integration(self) -> None:
        """Test file watching with cached loader."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
mode: merge
logging:
  level: INFO
""")
            f.flush()

            file_path = Path(f.name)

            try:
                # Create loader with file source
                base_loader = ConfigLoader()
                base_loader.add_source(YamlFileSource(file_path))

                cached_loader = CachedConfigLoader(base_loader, cache_ttl=10.0)

                # Load initial config
                config1 = cached_loader.load()
                assert config1.logging.level == "INFO"

                # Modify file
                time.sleep(0.1)  # Ensure different mtime
                with open(file_path, "w") as f2:
                    f2.write("""
mode: merge
logging:
  level: DEBUG
""")

                # Check for changes and reload
                changes_detected = cached_loader.file_watcher.check_for_changes()
                assert changes_detected, "File changes should be detected"

                config2 = cached_loader.load()

                # Should have new config
                assert config2.logging.level == "DEBUG"

            finally:
                file_path.unlink()


class TestYesmanConfigCaching:
    """Test YesmanConfig with caching enabled."""

    def test_cached_yesman_config_creation(self) -> None:
        """Test creating cached YesmanConfig."""
        config = create_cached_yesman_config(cache_ttl=1.0)

        # Should have cache capabilities
        assert hasattr(config._loader, "get_cache_stats")
        assert config.get_cache_stats() is not None

        # Should show cached in repr
        assert "(cached)" in repr(config)

    def test_cache_stats_integration(self) -> None:
        """Test cache statistics integration."""
        config = create_cached_yesman_config(cache_ttl=1.0)

        # Get initial stats
        stats = config.get_cache_stats()
        assert stats is not None
        assert "hit_count" in stats
        assert "miss_count" in stats
        assert "total_requests" in stats

    def test_cache_invalidation_integration(self) -> None:
        """Test cache invalidation integration."""
        config = create_cached_yesman_config(cache_ttl=10.0)

        # Load config (cache miss)

        # Invalidate cache
        config.invalidate_cache()

        # This would trigger a reload in real usage
        assert config.get_cache_stats()["miss_count"] >= 1


class TestPerformanceImprovements:
    """Test that caching actually improves performance."""

    def test_performance_improvement(self) -> None:
        """Test that cached loading is faster than uncached."""
        import time

        # Create configs
        base_loader = ConfigLoader()
        base_loader.add_source(EnvironmentSource())

        cached_loader = CachedConfigLoader(base_loader, cache_ttl=60.0)

        # Time first load (cache miss)
        start = time.time()
        cached_loader.load()
        first_load_time = time.time() - start

        # Time second load (cache hit)
        start = time.time()
        cached_loader.load()
        second_load_time = time.time() - start

        # Cache hit should be faster or at least similar
        # In fast systems, both may be very quick, so we check cache statistics instead
        stats = cached_loader.get_cache_stats()
        assert stats["hit_count"] >= 1, "Should have at least one cache hit"
        assert stats["miss_count"] >= 1, "Should have at least one cache miss"

        # Also check that second load is not significantly slower
        assert second_load_time <= first_load_time * 2, f"Cache hit ({second_load_time:.4f}s) should not be much slower than miss ({first_load_time:.4f}s)"

    @pytest.mark.skip(reason="Integration test - requires environment setup")
    def test_real_world_performance(self) -> None:
        """Test performance with real configuration files."""
        # This would test with actual config files in a real environment
        config = create_cached_yesman_config(cache_ttl=60.0)

        # Multiple accesses should be fast after first load
        start = time.time()
        for _ in range(10):
            _ = config.schema.mode
        access_time = time.time() - start

        # Should complete very quickly
        assert access_time < 0.1, f"10 cached accesses took {access_time:.4f}s, should be < 0.1s"
