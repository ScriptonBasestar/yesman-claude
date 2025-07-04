"""Core cache data structures and statistics"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class InvalidationStrategy(Enum):
    """Cache invalidation strategies"""
    TIME_BASED = "time_based"          # Standard TTL expiration
    CONTENT_CHANGE = "content_change"  # Invalidate when content changes
    DEPENDENCY = "dependency"          # Invalidate based on dependencies
    MANUAL = "manual"                  # Manual invalidation only


class CacheTag:
    """Tags for cache entries to enable smart invalidation"""
    SESSION_DATA = "session_data"
    SESSION_STATUS = "session_status"
    CONTROLLER_STATE = "controller_state"
    WINDOW_INFO = "window_info"
    GLOBAL_STATE = "global_state"


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    data: Any
    timestamp: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    content_hash: str = ""
    tags: Set[str] = field(default_factory=set)
    custom_ttl: Optional[float] = None
    invalidation_strategy: InvalidationStrategy = InvalidationStrategy.TIME_BASED
    dependencies: Set[str] = field(default_factory=set)
    
    def is_expired(self, default_ttl: float) -> bool:
        """Check if entry has expired based on strategy"""
        if self.invalidation_strategy == InvalidationStrategy.MANUAL:
            return False
        
        effective_ttl = self.custom_ttl or default_ttl
        return time.time() - self.timestamp > effective_ttl
    
    def mark_access(self) -> None:
        """Mark cache entry as accessed"""
        self.access_count += 1
        self.last_access = time.time()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this cache entry"""
        self.tags.add(tag)
    
    def add_dependency(self, dependency: str) -> None:
        """Add a dependency to this cache entry"""
        self.dependencies.add(dependency)


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


def generate_content_hash(data: Any) -> str:
    """Generate hash for data content"""
    try:
        # Convert data to JSON string for consistent hashing
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()[:8]
    except Exception:
        # Fallback to string representation
        return hashlib.md5(str(data).encode('utf-8')).hexdigest()[:8]