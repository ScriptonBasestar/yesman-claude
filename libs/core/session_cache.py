"""Session caching system for dashboard performance optimization

This module has been refactored for better maintainability.
The SessionCache class is now composed of specialized components:
- CacheStorage: Core storage and TTL management
- CacheAnalytics: Analytics and monitoring functionality  
- CacheManager: High-level interface combining all components

For backward compatibility, this module re-exports the main SessionCache class.

"""

# Re-export the main SessionCache class for backward compatibility
from .cache_manager import SessionCache
from .cache_core import InvalidationStrategy, CacheTag

# Re-export core types for compatibility
__all__ = [
    'SessionCache',
    'InvalidationStrategy', 
    'CacheTag'
]