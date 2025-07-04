"""Session caching system for dashboard performance optimization"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
import logging
from pathlib import Path
import hashlib
import json

from .models import SessionInfo
from ..utils import ensure_log_directory, get_default_log_path


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    data: Any
    timestamp: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    content_hash: str = ""
    
    def is_expired(self, ttl: float) -> bool:
        """Check if entry has expired"""
        return time.time() - self.timestamp > ttl
    
    def mark_access(self) -> None:
        """Mark cache entry as accessed"""
        self.access_count += 1
        self.last_access = time.time()


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0
    memory_size_bytes: int = 0
    hit_rate: float = 0.0
    
    def update_hit_rate(self) -> None:
        """Update hit rate calculation"""
        total_requests = self.hits + self.misses
        self.hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0


class SessionCache:
    """High-performance TTL-based cache for session data"""
    
    def __init__(self, default_ttl: float = 5.0, max_entries: int = 1000):
        """
        Initialize session cache
        
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
        
        self.logger.info(f"SessionCache initialized - TTL: {default_ttl}s, Max entries: {max_entries}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup cache-specific logger"""
        logger = logging.getLogger("yesman.dashboard.session_cache")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = ensure_log_directory(get_default_log_path())
        log_file = log_path / "session_cache.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _generate_content_hash(self, data: Any) -> str:
        """Generate hash for data content"""
        try:
            # Convert data to JSON string for consistent hashing
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(data_str.encode('utf-8')).hexdigest()[:8]
        except Exception:
            # Fallback to string representation
            return hashlib.md5(str(data).encode('utf-8')).hexdigest()[:8]
    
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
            content_hash = self._generate_content_hash(value)
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
    
    def get_or_compute(self, key: str, compute_func: Callable[[], Any], 
                      ttl: Optional[float] = None) -> Any:
        """
        Get cached value or compute and cache if not found
        
        Args:
            key: Cache key
            compute_func: Function to compute value if cache miss
            ttl: Optional TTL override
            
        Returns:
            Cached or computed value
        """
        # Try cache first
        cached_value = self.get(key, ttl)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - compute value
        start_time = time.time()
        try:
            computed_value = compute_func()
            self.put(key, computed_value, ttl)
            
            compute_time = time.time() - start_time
            self.logger.debug(f"Cache miss computed: {key} ({compute_time:.3f}s)")
            
            return computed_value
            
        except Exception as e:
            self.logger.error(f"Failed to compute cache value for {key}: {e}")
            raise
    
    def get_cache_keys(self) -> List[str]:
        """Get list of all cache keys"""
        with self._lock:
            return list(self._cache.keys())
    
    def export_stats_json(self) -> str:
        """Export cache statistics as JSON"""
        stats = self.get_stats()
        return json.dumps({
            'hits': stats.hits,
            'misses': stats.misses,
            'evictions': stats.evictions,
            'total_entries': stats.total_entries,
            'memory_size_bytes': stats.memory_size_bytes,
            'hit_rate_percent': round(stats.hit_rate, 2),
            'default_ttl': self.default_ttl,
            'max_entries': self.max_entries,
            'cache_keys': self.get_cache_keys()
        }, indent=2)