"""High-level cache manager interface combining all cache components"""

from typing import Dict, Any, Optional, Set, List, Callable

from .cache_storage import CacheStorage
from .cache_analytics import CacheAnalytics
from .cache_core import InvalidationStrategy


class SessionCache:
    """High-performance TTL-based cache for session data with analytics"""
    
    def __init__(self, default_ttl: float = 5.0, max_entries: int = 1000):
        """
        Initialize session cache
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_entries: Maximum number of entries to cache
        """
        # Initialize core components
        self.storage = CacheStorage(default_ttl, max_entries)
        self.analytics = CacheAnalytics(self.storage)
        
        # Expose commonly used properties
        self.default_ttl = self.storage.default_ttl
        self.max_entries = self.storage.max_entries
        self.stats = self.storage.stats
        self.logger = self.storage.logger
    
    # Core cache operations - delegate to storage
    def get(self, key: str, ttl: Optional[float] = None) -> Optional[Any]:
        """Get cached value"""
        return self.storage.get(key, ttl)
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Store value in cache"""
        result = self.storage.put(key, value, ttl)
        # Log periodic status after successful operations
        self.analytics.log_periodic_status()
        return result
    
    def put_with_strategy(self, key: str, value: Any, 
                         ttl: Optional[float] = None,
                         strategy: InvalidationStrategy = InvalidationStrategy.TIME_BASED,
                         tags: Optional[Set[str]] = None,
                         dependencies: Optional[Set[str]] = None,
                         change_detector: Optional[Callable[[Any, Any], bool]] = None) -> bool:
        """Store value in cache with advanced TTL and invalidation strategy"""
        return self.storage.put_with_strategy(key, value, ttl, strategy, tags, dependencies, change_detector)
    
    def invalidate(self, key: str) -> bool:
        """Invalidate specific cache entry"""
        return self.storage.invalidate(key)
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with the specified tag"""
        return self.storage.invalidate_by_tag(tag)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching pattern"""
        return self.storage.invalidate_pattern(pattern)
    
    def clear(self) -> int:
        """Clear all cache entries"""
        result = self.storage.clear()
        # Log status after major operation
        self.analytics.log_cache_status("cache_cleared")
        return result
    
    def get_cache_keys(self) -> List[str]:
        """Get list of all cache keys"""
        return self.storage.get_cache_keys()
    
    def get_stats(self):
        """Get current cache statistics"""
        return self.storage.get_stats()
    
    # TTL management operations
    def set_ttl_for_key(self, key: str, new_ttl: float) -> bool:
        """Update TTL for a specific cache entry"""
        return self.storage.set_ttl_for_key(key, new_ttl)
    
    def extend_ttl(self, key: str, additional_time: float) -> bool:
        """Extend TTL for a cache entry by refreshing its timestamp"""
        return self.storage.extend_ttl(key, additional_time)
    
    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a cache entry"""
        return self.storage.get_entry_info(key)
    
    # Callback management
    def register_invalidation_callback(self, key: str, callback: Callable[[str], None]) -> None:
        """Register callback to be called when key is invalidated"""
        self.storage.register_invalidation_callback(key, callback)
    
    # Convenience methods
    def get_or_compute(self, key: str, compute_func: Callable[[], Any], 
                      ttl: Optional[float] = None) -> Any:
        """Get cached value or compute and cache if not found"""
        # Try cache first
        cached_value = self.get(key, ttl)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - compute value
        import time
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
    
    # Analytics and monitoring - delegate to analytics
    def get_cache_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive cache health report"""
        return self.analytics.get_cache_health_report()
    
    def get_visual_status_summary(self) -> Dict[str, Any]:
        """Get cache status summary optimized for dashboard visualization"""
        return self.analytics.get_visual_status_summary()
    
    def export_stats_json(self) -> str:
        """Export cache statistics as JSON"""
        return self.analytics.export_stats_json()
    
    def log_cache_status(self, operation: str = "status_check") -> None:
        """Log comprehensive cache status for visualization and monitoring"""
        self.analytics.log_cache_status(operation)
    
    def log_periodic_status(self, force: bool = False) -> None:
        """Log cache status periodically (every 5 minutes by default)"""
        self.analytics.log_periodic_status(force)