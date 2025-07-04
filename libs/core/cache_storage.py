"""Cache storage and TTL management functionality"""

import time
import threading
import logging
from typing import Dict, Any, Optional, Set, List, Callable
from pathlib import Path

from .cache_core import CacheEntry, CacheStats, InvalidationStrategy, generate_content_hash
from ..utils import ensure_log_directory, get_default_log_path


class CacheStorage:
    """Core cache storage with TTL and eviction management"""
    
    def __init__(self, default_ttl: float = 5.0, max_entries: int = 1000):
        """
        Initialize cache storage
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_entries: Maximum number of entries to cache
        """
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        
        # Cache storage
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        
        # Statistics
        self.stats = CacheStats()
        
        # Logging
        self.logger = self._setup_logger()
        
        # Cache configuration
        self._invalidation_callbacks: Dict[str, List[Callable]] = {}
        self._cleanup_interval = 60.0  # seconds
        self._last_cleanup = time.time()
        
        # Advanced TTL and invalidation features
        self._tag_registry: Dict[str, Set[str]] = {}  # tag -> set of keys
        self._dependency_graph: Dict[str, Set[str]] = {}  # key -> dependent keys
        self._change_detectors: Dict[str, Callable[[Any, Any], bool]] = {}  # key -> change detector
        
        self.logger.info(f"CacheStorage initialized - TTL: {default_ttl}s, Max entries: {max_entries}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup cache-specific logger"""
        logger = logging.getLogger("yesman.dashboard.cache_storage")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = ensure_log_directory(get_default_log_path())
        log_file = log_path / "cache_storage.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _cleanup_expired(self) -> int:
        """Clean up expired entries"""
        current_time = time.time()
        
        # Only cleanup if enough time has passed
        if current_time - self._last_cleanup < self._cleanup_interval:
            return 0
        
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired(self.default_ttl):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self.stats.evictions += 1
            
            self._last_cleanup = current_time
            
            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    def _evict_lru(self) -> bool:
        """Evict least recently used entry"""
        with self._lock:
            if not self._cache:
                return False
            
            # Find LRU entry
            lru_key = min(self._cache.keys(), 
                         key=lambda k: self._cache[k].last_access)
            
            del self._cache[lru_key]
            self.stats.evictions += 1
            self.logger.debug(f"Evicted LRU entry: {lru_key}")
            return True
    
    def get(self, key: str, ttl: Optional[float] = None) -> Optional[Any]:
        """
        Get cached value
        
        Args:
            key: Cache key
            ttl: Optional TTL override
            
        Returns:
            Cached value or None if not found/expired
        """
        effective_ttl = ttl or self.default_ttl
        
        with self._lock:
            # Periodic cleanup
            self._cleanup_expired()
            
            entry = self._cache.get(key)
            if entry is None:
                self.stats.misses += 1
                self.stats.update_hit_rate()
                return None
            
            if entry.is_expired(effective_ttl):
                del self._cache[key]
                self.stats.misses += 1
                self.stats.evictions += 1
                self.stats.update_hit_rate()
                self.logger.debug(f"Cache expired: {key}")
                return None
            
            # Cache hit
            entry.mark_access()
            self.stats.hits += 1
            self.stats.update_hit_rate()
            
            self.logger.debug(f"Cache hit: {key} (access #{entry.access_count})")
            return entry.data
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Store value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
            
        Returns:
            True if stored successfully
        """
        with self._lock:
            # Check if we need to make space
            while len(self._cache) >= self.max_entries:
                if not self._evict_lru():
                    break
            
            # Create new entry
            content_hash = generate_content_hash(value)
            entry = CacheEntry(
                data=value,
                timestamp=time.time(),
                content_hash=content_hash
            )
            
            # Check if content actually changed
            old_entry = self._cache.get(key)
            if old_entry and old_entry.content_hash == content_hash:
                # Content unchanged, just update timestamp
                old_entry.timestamp = time.time()
                self.logger.debug(f"Cache refreshed (unchanged): {key}")
                return True
            
            self._cache[key] = entry
            self.stats.total_entries = len(self._cache)
            
            self.logger.debug(f"Cache stored: {key} (hash: {content_hash})")
            return True
    
    def put_with_strategy(self, key: str, value: Any, 
                         ttl: Optional[float] = None,
                         strategy: InvalidationStrategy = InvalidationStrategy.TIME_BASED,
                         tags: Optional[Set[str]] = None,
                         dependencies: Optional[Set[str]] = None,
                         change_detector: Optional[Callable[[Any, Any], bool]] = None) -> bool:
        """
        Store value in cache with advanced TTL and invalidation strategy
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Custom TTL for this entry
            strategy: Invalidation strategy
            tags: Tags for group invalidation
            dependencies: Keys this entry depends on
            change_detector: Function to detect if content has changed
            
        Returns:
            True if stored successfully
        """
        with self._lock:
            # Check for content changes if strategy requires it
            if strategy == InvalidationStrategy.CONTENT_CHANGE:
                old_entry = self._cache.get(key)
                if old_entry and change_detector:
                    if not change_detector(old_entry.data, value):
                        # Content hasn't changed, just update timestamp
                        old_entry.timestamp = time.time()
                        self.logger.debug(f"Content unchanged, refreshed timestamp: {key}")
                        return True
            
            # Check if we need to make space
            while len(self._cache) >= self.max_entries:
                if not self._evict_lru():
                    break
            
            # Create new entry with advanced features
            content_hash = generate_content_hash(value)
            entry = CacheEntry(
                data=value,
                timestamp=time.time(),
                content_hash=content_hash,
                tags=tags or set(),
                custom_ttl=ttl,
                invalidation_strategy=strategy,
                dependencies=dependencies or set()
            )
            
            # Update registries
            self._update_tag_registry(key, entry.tags)
            self._update_dependency_graph(key, entry.dependencies)
            
            if change_detector:
                self._change_detectors[key] = change_detector
            
            # Store entry
            self._cache[key] = entry
            self.stats.total_entries = len(self._cache)
            
            self.logger.debug(f"Advanced cache stored: {key} (strategy: {strategy.value}, "
                            f"tags: {entry.tags}, deps: {entry.dependencies})")
            
            # Check for dependency invalidation
            self._check_and_invalidate_dependents(key)
            
            return True
    
    def _update_tag_registry(self, key: str, tags: Set[str]) -> None:
        """Update the tag registry"""
        for tag in tags:
            if tag not in self._tag_registry:
                self._tag_registry[tag] = set()
            self._tag_registry[tag].add(key)
    
    def _update_dependency_graph(self, key: str, dependencies: Set[str]) -> None:
        """Update the dependency graph"""
        for dep_key in dependencies:
            if dep_key not in self._dependency_graph:
                self._dependency_graph[dep_key] = set()
            self._dependency_graph[dep_key].add(key)
    
    def _check_and_invalidate_dependents(self, changed_key: str) -> None:
        """Check and invalidate entries that depend on the changed key"""
        if changed_key in self._dependency_graph:
            dependent_keys = self._dependency_graph[changed_key].copy()
            for dependent_key in dependent_keys:
                self.invalidate(dependent_key)
                self.logger.debug(f"Invalidated dependent: {dependent_key} (changed: {changed_key})")
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate specific cache entry
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if entry was found and removed
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.stats.evictions += 1
                self.stats.total_entries = len(self._cache)
                
                # Call invalidation callbacks
                callbacks = self._invalidation_callbacks.get(key, [])
                for callback in callbacks:
                    try:
                        callback(key)
                    except Exception as e:
                        self.logger.error(f"Invalidation callback failed for {key}: {e}")
                
                self.logger.debug(f"Cache invalidated: {key}")
                return True
            return False
    
    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all cache entries with the specified tag
        
        Args:
            tag: Tag to invalidate
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if tag not in self._tag_registry:
                return 0
            
            keys_to_invalidate = self._tag_registry[tag].copy()
            invalidated_count = 0
            
            for key in keys_to_invalidate:
                if self.invalidate(key):
                    invalidated_count += 1
            
            # Clean up tag registry
            if tag in self._tag_registry:
                del self._tag_registry[tag]
            
            self.logger.info(f"Invalidated {invalidated_count} entries with tag: {tag}")
            return invalidated_count
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate entries matching pattern
        
        Args:
            pattern: Pattern to match (simple substring match)
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            matching_keys = [key for key in self._cache.keys() if pattern in key]
            
            for key in matching_keys:
                self.invalidate(key)
            
            self.logger.debug(f"Cache pattern invalidated: {pattern} ({len(matching_keys)} entries)")
            return len(matching_keys)
    
    def clear(self) -> int:
        """
        Clear all cache entries
        
        Returns:
            Number of entries cleared
        """
        with self._lock:
            entry_count = len(self._cache)
            self._cache.clear()
            self.stats.evictions += entry_count
            self.stats.total_entries = 0
            
            self.logger.info(f"Cache cleared: {entry_count} entries")
            return entry_count
    
    def get_cache_keys(self) -> List[str]:
        """Get list of all cache keys"""
        with self._lock:
            return list(self._cache.keys())
    
    def get_stats(self) -> CacheStats:
        """Get current cache statistics"""
        with self._lock:
            # Update memory size estimate
            memory_estimate = sum(
                len(str(entry.data)) + len(key) + 100  # rough estimate
                for key, entry in self._cache.items()
            )
            
            self.stats.memory_size_bytes = memory_estimate
            self.stats.total_entries = len(self._cache)
            self.stats.update_hit_rate()
            
            return self.stats
    
    def register_invalidation_callback(self, key: str, callback: Callable[[str], None]) -> None:
        """Register callback to be called when key is invalidated"""
        if key not in self._invalidation_callbacks:
            self._invalidation_callbacks[key] = []
        self._invalidation_callbacks[key].append(callback)
    
    def set_ttl_for_key(self, key: str, new_ttl: float) -> bool:
        """
        Update TTL for a specific cache entry
        
        Args:
            key: Cache key
            new_ttl: New TTL in seconds
            
        Returns:
            True if TTL was updated
        """
        with self._lock:
            if key in self._cache:
                self._cache[key].custom_ttl = new_ttl
                self.logger.debug(f"Updated TTL for {key}: {new_ttl}s")
                return True
            return False
    
    def extend_ttl(self, key: str, additional_time: float) -> bool:
        """
        Extend TTL for a cache entry by refreshing its timestamp
        
        Args:
            key: Cache key
            additional_time: Additional time in seconds
            
        Returns:
            True if TTL was extended
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                entry.timestamp = time.time() + additional_time
                self.logger.debug(f"Extended TTL for {key} by {additional_time}s")
                return True
            return False
    
    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a cache entry
        
        Args:
            key: Cache key
            
        Returns:
            Entry information or None if not found
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            age = current_time - entry.timestamp
            effective_ttl = entry.custom_ttl or self.default_ttl
            time_to_expire = max(0, effective_ttl - age)
            
            return {
                'key': key,
                'age_seconds': round(age, 2),
                'time_to_expire': round(time_to_expire, 2),
                'access_count': entry.access_count,
                'last_access': entry.last_access,
                'tags': list(entry.tags),
                'dependencies': list(entry.dependencies),
                'strategy': entry.invalidation_strategy.value,
                'custom_ttl': entry.custom_ttl,
                'content_hash': entry.content_hash,
                'is_expired': entry.is_expired(self.default_ttl)
            }