"""Cache analytics and monitoring functionality"""

import time
import json
from typing import Dict, Any
import logging

from .cache_core import CacheStats


class CacheAnalytics:
    """Cache analytics and monitoring functionality"""
    
    def __init__(self, cache_storage):
        """
        Initialize cache analytics
        
        Args:
            cache_storage: CacheStorage instance to analyze
        """
        self.storage = cache_storage
        self.logger = logging.getLogger("yesman.dashboard.cache_analytics")
    
    def get_cache_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive cache health report
        
        Returns:
            Detailed health report
        """
        with self.storage._lock:
            stats = self.storage.get_stats()
            current_time = time.time()
            
            # Analyze entry distribution by strategy
            strategy_distribution = {}
            tag_distribution = {}
            dependency_count = 0
            expired_count = 0
            
            for entry in self.storage._cache.values():
                # Strategy distribution
                strategy = entry.invalidation_strategy.value
                strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
                
                # Tag distribution
                for tag in entry.tags:
                    tag_distribution[tag] = tag_distribution.get(tag, 0) + 1
                
                # Count dependencies and expired entries
                dependency_count += len(entry.dependencies)
                if entry.is_expired(self.storage.default_ttl):
                    expired_count += 1
            
            return {
                'basic_stats': {
                    'total_entries': stats.total_entries,
                    'hits': stats.hits,
                    'misses': stats.misses,
                    'hit_rate': stats.hit_rate,
                    'memory_kb': round(stats.memory_size_bytes / 1024, 2)
                },
                'advanced_stats': {
                    'strategy_distribution': strategy_distribution,
                    'tag_distribution': tag_distribution,
                    'total_dependencies': dependency_count,
                    'expired_entries': expired_count,
                    'active_tags': len(self.storage._tag_registry),
                    'dependency_chains': len(self.storage._dependency_graph)
                },
                'health_indicators': {
                    'cache_efficiency': 'good' if stats.hit_rate >= 70 else 'needs_improvement',
                    'memory_usage': 'normal' if stats.memory_size_bytes < 1024*1024 else 'high',
                    'expiration_health': 'good' if expired_count < stats.total_entries * 0.2 else 'cleanup_needed'
                },
                'timestamp': current_time
            }
    
    def get_visual_status_summary(self) -> Dict[str, Any]:
        """
        Get cache status summary optimized for dashboard visualization
        
        Returns:
            Dictionary with visual indicators and formatted metrics
        """
        with self.storage._lock:
            stats = self.storage.get_stats()
            current_time = time.time()
            
            # Visual performance indicators
            hit_rate = stats.hit_rate
            if hit_rate >= 80:
                performance_emoji = "🟢"
                performance_text = "Excellent"
            elif hit_rate >= 60:
                performance_emoji = "🟡"
                performance_text = "Good"
            elif hit_rate >= 40:
                performance_emoji = "🟠"
                performance_text = "Average"
            else:
                performance_emoji = "🔴"
                performance_text = "Poor"
            
            # Memory usage indicators
            memory_kb = stats.memory_size_bytes / 1024
            usage_percent = (stats.total_entries / self.storage.max_entries) * 100 if self.storage.max_entries > 0 else 0
            
            if usage_percent >= 90:
                capacity_emoji = "🔴"
                capacity_text = "Near Full"
            elif usage_percent >= 70:
                capacity_emoji = "🟡"
                capacity_text = "High Usage"
            else:
                capacity_emoji = "🟢"
                capacity_text = "Normal"
            
            # Cache freshness
            oldest_age = 0
            if self.storage._cache:
                entry_ages = [current_time - entry.timestamp for entry in self.storage._cache.values()]
                oldest_age = max(entry_ages) if entry_ages else 0
            
            freshness_percent = max(0, (self.storage.default_ttl - oldest_age) / self.storage.default_ttl * 100) if self.storage.default_ttl > 0 else 100
            
            return {
                # Performance indicators
                'performance': {
                    'emoji': performance_emoji,
                    'text': performance_text,
                    'hit_rate': round(hit_rate, 1),
                    'level': performance_text.lower()
                },
                
                # Capacity indicators
                'capacity': {
                    'emoji': capacity_emoji,
                    'text': capacity_text,
                    'usage_percent': round(usage_percent, 1),
                    'entries': f"{stats.total_entries}/{self.storage.max_entries}"
                },
                
                # Memory indicators
                'memory': {
                    'size_kb': round(memory_kb, 1),
                    'size_mb': round(memory_kb / 1024, 2),
                    'avg_entry_bytes': round(stats.memory_size_bytes / max(1, stats.total_entries), 0)
                },
                
                # Activity indicators
                'activity': {
                    'total_requests': stats.hits + stats.misses,
                    'efficiency_ratio': f"{stats.hits}/{stats.hits + stats.misses}",
                    'eviction_rate': round(stats.evictions / max(1, stats.total_entries), 2)
                },
                
                # Freshness indicators
                'freshness': {
                    'percent': round(freshness_percent, 1),
                    'oldest_age_seconds': round(oldest_age, 1),
                    'ttl_seconds': self.storage.default_ttl
                },
                
                # Timestamp
                'last_update': current_time,
                'last_update_formatted': time.strftime('%H:%M:%S', time.localtime(current_time))
            }
    
    def export_stats_json(self) -> str:
        """Export cache statistics as JSON"""
        stats = self.storage.get_stats()
        return json.dumps({
            'hits': stats.hits,
            'misses': stats.misses,
            'evictions': stats.evictions,
            'total_entries': stats.total_entries,
            'memory_size_bytes': stats.memory_size_bytes,
            'hit_rate_percent': round(stats.hit_rate, 2),
            'default_ttl': self.storage.default_ttl,
            'max_entries': self.storage.max_entries,
            'cache_keys': self.storage.get_cache_keys()
        }, indent=2)
    
    def log_cache_status(self, operation: str = "status_check") -> None:
        """
        Log comprehensive cache status for visualization and monitoring
        
        Args:
            operation: Description of the operation triggering this log
        """
        with self.storage._lock:
            stats = self.storage.get_stats()
            current_time = time.time()
            
            # Calculate cache ages
            oldest_entry_age = 0.0
            newest_entry_age = 0.0
            avg_entry_age = 0.0
            
            if self.storage._cache:
                entry_ages = [current_time - entry.timestamp for entry in self.storage._cache.values()]
                oldest_entry_age = max(entry_ages)
                newest_entry_age = min(entry_ages)
                avg_entry_age = sum(entry_ages) / len(entry_ages)
            
            # Performance classification
            if stats.hit_rate >= 80:
                performance_level = "EXCELLENT"
            elif stats.hit_rate >= 60:
                performance_level = "GOOD"
            elif stats.hit_rate >= 40:
                performance_level = "AVERAGE"
            else:
                performance_level = "POOR"
            
            # Memory efficiency
            memory_kb = stats.memory_size_bytes / 1024
            avg_entry_size = (stats.memory_size_bytes / stats.total_entries) if stats.total_entries > 0 else 0
            
            # Log comprehensive status
            self.logger.info(f"""
=== CACHE STATUS REPORT ({operation}) ===
Performance: {performance_level} ({stats.hit_rate:.1f}% hit rate)
Activity: {stats.hits} hits, {stats.misses} misses, {stats.evictions} evictions
Storage: {stats.total_entries}/{self.storage.max_entries} entries ({memory_kb:.1f} KB)
Memory Efficiency: {avg_entry_size:.0f} bytes/entry average
Cache Ages: newest={newest_entry_age:.1f}s, oldest={oldest_entry_age:.1f}s, avg={avg_entry_age:.1f}s
TTL Settings: {self.storage.default_ttl}s default TTL
Last Cleanup: {current_time - self.storage._last_cleanup:.1f}s ago
Active Keys: {len(self.storage.get_cache_keys())}
===========================================""")
    
    def log_periodic_status(self, force: bool = False) -> None:
        """
        Log cache status periodically (every 5 minutes by default)
        
        Args:
            force: Force logging regardless of time interval
        """
        current_time = time.time()
        
        # Check if we should log (every 5 minutes)
        if not force and hasattr(self, '_last_status_log'):
            if current_time - self._last_status_log < 300:  # 5 minutes
                return
        
        self._last_status_log = current_time
        self.log_cache_status("periodic_report")
        
        # Log visual summary for dashboard
        visual_status = self.get_visual_status_summary()
        self.logger.info(f"Dashboard Status: {visual_status['performance']['emoji']} "
                        f"{visual_status['performance']['hit_rate']}% hit rate, "
                        f"{visual_status['capacity']['emoji']} {visual_status['capacity']['usage_percent']}% capacity, "
                        f"{visual_status['memory']['size_kb']} KB memory")