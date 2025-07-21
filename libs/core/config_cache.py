#!/usr/bin/env python3

# Copyright notice.

import hashlib
import json
import logging
import os
import threading
import time
from pathlib import Path
import yaml
from .config_schema import YesmanConfigSchema

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Configuration caching system for improved performance."""


class ConfigCache:
    """Thread-safe configuration cache with TTL and invalidation."""

    def __init__(self, cache_ttl: float = 300.0, max_cache_size: int = 100) -> None:
        """Initialize configuration cache.

        Args:
            cache_ttl: Time to live for cache entries in seconds (default: 5 minutes)
            max_cache_size: Maximum number of cache entries to keep
        """
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self._cache: dict[str, dict[str]] = {}
        self._access_times: dict[str, float] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

    @staticmethod
    def _generate_cache_key(config_sources: list, env_vars: dict | None = None) -> str:
        """Generate a unique cache key based on configuration sources and environment.

    Returns:
        String containing."""
        key_data: dict[str] = {
            "sources": [],
            "env_vars": env_vars or {},
            "timestamp": int(time.time() / 300),  # Round to 5-minute intervals
        }

        for source in config_sources:
            if hasattr(source, "get_cache_key"):
                source_key = source.get_cache_key()
            else:
                # Fallback: use source type and basic info
                source_key = f"{type(source).__name__}:{source!s}"
            key_data["sources"].append(source_key)

        # Create hash of the key data
        key_json = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_json.encode()).hexdigest()[:16]

    def get(self, cache_key: str) -> YesmanConfigSchema | None:
        """Get configuration from cache if valid.

    Returns:
        Yesmanconfigschema | None object the requested data."""
        with self._lock:
            if cache_key not in self._cache:
                return None

            cache_entry = self._cache[cache_key]
            current_time = time.time()

            # Check if cache entry is still valid
            if current_time - cache_entry["timestamp"] > self.cache_ttl:
                self._logger.debug("Cache entry expired: %s", cache_key)
                del self._cache[cache_key]
                if cache_key in self._access_times:
                    del self._access_times[cache_key]
                return None

            # Update access time
            self._access_times[cache_key] = current_time

            self._logger.debug("Cache hit: %s", cache_key)
            return cache_entry["config"]  # type: ignore[no-any-return]

    def put(self, cache_key: str, config: YesmanConfigSchema) -> None:
        """Store configuration in cache."""
        with self._lock:
            current_time = time.time()

            # Check if we need to evict old entries
            if len(self._cache) >= self.max_cache_size:
                self._evict_oldest()

            self._cache[cache_key] = {"config": config, "timestamp": current_time}
            self._access_times[cache_key] = current_time

            self._logger.debug("Cache store: %s", cache_key)

    def _evict_oldest(self) -> None:
        """Evict the least recently used cache entry."""
        if not self._access_times:
            return

        # Find the least recently accessed entry
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])

        del self._cache[oldest_key]
        del self._access_times[oldest_key]

        self._logger.debug("Cache eviction: %s", oldest_key)

    def invalidate(self, cache_key: str | None = None) -> None:
        """Invalidate cache entry or entire cache."""
        with self._lock:
            if cache_key:
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    self._logger.debug("Cache invalidated: %s", cache_key)
                if cache_key in self._access_times:
                    del self._access_times[cache_key]
            else:
                # Clear entire cache
                cleared_count = len(self._cache)
                self._cache.clear()
                self._access_times.clear()
                self._logger.debug("Cache cleared: %d entries", cleared_count)

    def get_stats(self) -> dict[str]:
        """Get cache statistics.

    Returns:
        Dict containing the requested data."""
        with self._lock:
            current_time = time.time()
            valid_entries = 0
            expired_entries = 0

            for cache_entry in self._cache.values():
                age = current_time - cache_entry["timestamp"]
                if age <= self.cache_ttl:
                    valid_entries += 1
                else:
                    expired_entries += 1

            return {
                "total_entries": len(self._cache),
                "valid_entries": valid_entries,
                "expired_entries": expired_entries,
                "cache_size": len(self._cache),
                "max_cache_size": self.max_cache_size,
                "cache_ttl": self.cache_ttl,
                "hit_rate": getattr(self, "_hit_count", 0) / max(getattr(self, "_total_requests", 1), 1),
            }

    def cleanup_expired(self) -> int:
        """Remove expired cache entries and return count removed.

    Returns:
        Integer representing."""
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for cache_key, cache_entry in self._cache.items():
                if current_time - cache_entry["timestamp"] > self.cache_ttl:
                    expired_keys.append(cache_key)

            for key in expired_keys:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]

            if expired_keys:
                self._logger.debug("Cleaned up %d expired cache entries", len(expired_keys))

            return len(expired_keys)


class FileWatcher:
    """Watch configuration files for changes to invalidate cache."""

    def __init__(self, config_cache: ConfigCache) -> None:
        self.config_cache = config_cache
        self._watched_files: dict[str, float] = {}
        self._logger = logging.getLogger(__name__)

    def watch_file(self, file_path: Path) -> None:
        """Add a file to the watch list."""
        if file_path.exists():
            mtime = file_path.stat().st_mtime
            self._watched_files[str(file_path)] = mtime
            self._logger.debug("Watching config file: %s", file_path)

    def check_for_changes(self) -> bool:
        """Check if any watched files have changed.

    Returns:
        Boolean indicating."""
        changes_detected = False

        for file_path_str, last_mtime in list(self._watched_files.items()):
            file_path = Path(file_path_str)

            if not file_path.exists():
                # File was deleted
                del self._watched_files[file_path_str]
                changes_detected = True
                self._logger.info("Config file deleted: %s", file_path)
                continue

            current_mtime = file_path.stat().st_mtime
            if current_mtime > last_mtime:
                # File was modified
                self._watched_files[file_path_str] = current_mtime
                changes_detected = True
                self._logger.info("Config file changed: %s", file_path)

        if changes_detected:
            # Invalidate entire cache when any config file changes
            self.config_cache.invalidate()
            self._logger.info("Configuration cache invalidated due to file changes")

        return changes_detected


class CachedConfigLoader:
    """Configuration loader with caching capabilities."""

    def __init__(base_loader: cache_ttl, float = 300.0) -> None:
        """Initialize cached config loader.

        Args:
            base_loader: The underlying ConfigLoader instance
            cache_ttl: Cache time-to-live in seconds
        """
        self.base_loader = base_loader
        self.cache = ConfigCache(cache_ttl=cache_ttl)
        self.file_watcher = FileWatcher(self.cache)
        self._logger = logging.getLogger(__name__)

        # Track cache hits/misses for statistics
        self._hit_count = 0
        self._miss_count = 0

    def load(self) -> YesmanConfigSchema:
        """Load configuration with caching.

    Returns:
        Yesmanconfigschema object."""
        # Check for file changes first
        self.file_watcher.check_for_changes()

        # Generate cache key based on current sources
        cache_key = self._generate_current_cache_key()

        # Try to get from cache first
        cached_config = self.cache.get(cache_key)
        if cached_config is not None:
            self._hit_count += 1
            self._logger.debug("Configuration loaded from cache")
            return cached_config

        # Cache miss - load from base loader
        self._miss_count += 1
        self._logger.debug("Configuration cache miss - loading from sources")

        # Force reload to ensure fresh data
        config = self.base_loader.reload()

        # Store in cache
        self.cache.put(cache_key, config)

        # Update file watchers
        self._update_file_watchers()

        return config  # type: ignore[no-any-return]

    def _generate_current_cache_key(self) -> str:
        """Generate cache key for current loader state.

    Returns:
        String containing."""
        # Get environment variables that affect configuration
        env_vars = {key: value for key, value in os.environ.items() if key.startswith("YESMAN_")}

        return self.cache._generate_cache_key(self.base_loader.sources, env_vars)

    def _update_file_watchers(self) -> None:
        """Update file watchers for all config file sources."""
        for source in self.base_loader.sources:
            if hasattr(source, "file_path") and source.file_path:
                file_path = Path(source.file_path)
                self.file_watcher.watch_file(file_path)

    def invalidate_cache(self) -> None:
        """Manually invalidate the configuration cache."""
        self.cache.invalidate()
        self._logger.info("Configuration cache manually invalidated")

    def get_cache_stats(self) -> dict[str]:
        """Get comprehensive cache statistics.

    Returns:
        Dict containing the requested data."""
        cache_stats = self.cache.get_stats()

        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / max(total_requests, 1)

        return {
            **cache_stats,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "watched_files": len(self.file_watcher._watched_files),
        }

    def cleanup(self) -> dict[str, int]:
        """Cleanup expired cache entries and return statistics.

    Returns:
        Dict containing."""
        expired_count = self.cache.cleanup_expired()
        return {
            "expired_entries_removed": expired_count,
            "remaining_entries": len(self.cache._cache),
        }

    def get_config_sources_info(self) -> list[dict[str]]:
        """Get information about configured sources (delegate to base loader).

    Returns:
        Dict containing service information."""
        return self.base_loader.get_config_sources_info()  # type: ignore[no-any-return]


# Enhanced config source classes with cache key support
class CacheableYamlFileSource:
    """YAML file source with cache key support."""

    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)

    def exists(self) -> bool:
        return self.file_path.exists()

    def load(self) -> dict:
        with open(self.file_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_cache_key(self) -> str:
        """Generate cache key based on file path and modification time.

    Returns:
        String containing the requested data."""
        if not self.file_path.exists():
            return f"file:{self.file_path}:missing"

        mtime = self.file_path.stat().st_mtime
        return f"file:{self.file_path}:mtime:{mtime}"


class CacheableEnvironmentSource:
    """Environment source with cache key support."""

    def __init__(self, prefix: str = "YESMAN_") -> None:
        self.prefix = prefix

    @staticmethod
    def exists() -> bool:
        return True

    def load(self) -> dict:
        config: dict[str] = {}
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                # Convert YESMAN_LOGGING_LEVEL to logging.level
                config_key = key[len(self.prefix) :].lower().replace("_", ".")

                # Type conversion
                converted_value: object = value
                if value.lower() in {"true", "false"}:
                    converted_value = value.lower() == "true"
                elif value.isdigit():
                    converted_value = int(value)
                elif "." in value and value.replace(".", "").isdigit():
                    converted_value = float(value)

                # Set nested dictionary value
                self._set_nested_value(config, config_key, converted_value)

        return config

    @staticmethod
    def _set_nested_value(d: dict, key: str, value: object) -> None:
        """Set value in nested dictionary using dot notation."""
        keys = key.split(".")
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    def get_cache_key(self) -> str:
        """Generate cache key based on relevant environment variables.

    Returns:
        String containing the requested data."""
        env_vars = {key: value for key, value in os.environ.items() if key.startswith(self.prefix)}

        env_json = json.dumps(env_vars, sort_keys=True)
        env_hash = hashlib.sha256(env_json.encode()).hexdigest()[:16]
        return f"env:{self.prefix}:{env_hash}"
