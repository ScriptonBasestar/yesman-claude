"""
Performance Optimizer

Comprehensive performance monitoring and optimization system for dashboard interfaces
with automatic tuning, metrics collection, and intelligent resource management.
"""

import asyncio
import gc
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Optional

import psutil

logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Performance optimization levels"""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AGGRESSIVE = "aggressive"


class PerformanceThreshold(Enum):
    """Performance threshold indicators"""

    EXCELLENT = "excellent"  # <30% CPU, <40% Memory
    GOOD = "good"  # <50% CPU, <60% Memory
    WARNING = "warning"  # <70% CPU, <80% Memory
    CRITICAL = "critical"  # >=70% CPU or >=80% Memory


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics data"""

    # System metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_available: int = 0
    disk_io_read: int = 0
    disk_io_write: int = 0

    # Dashboard-specific metrics
    render_time: float = 0.0
    widget_count: int = 0
    active_connections: int = 0
    cache_hit_rate: float = 0.0
    cache_size: int = 0

    # Performance indicators
    fps: float = 0.0
    response_time: float = 0.0
    update_frequency: float = 1.0

    # Timestamps
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "memory_available": self.memory_available,
            "disk_io_read": self.disk_io_read,
            "disk_io_write": self.disk_io_write,
            "render_time": self.render_time,
            "widget_count": self.widget_count,
            "active_connections": self.active_connections,
            "cache_hit_rate": self.cache_hit_rate,
            "cache_size": self.cache_size,
            "fps": self.fps,
            "response_time": self.response_time,
            "update_frequency": self.update_frequency,
            "timestamp": self.timestamp.isoformat(),
        }

    def get_threshold_level(self) -> PerformanceThreshold:
        """Get performance threshold level based on metrics"""
        if self.cpu_usage >= 70 or self.memory_usage >= 80:
            return PerformanceThreshold.CRITICAL
        elif self.cpu_usage >= 50 or self.memory_usage >= 60:
            return PerformanceThreshold.WARNING
        elif self.cpu_usage >= 30 or self.memory_usage >= 40:
            return PerformanceThreshold.GOOD
        else:
            return PerformanceThreshold.EXCELLENT


@dataclass
class OptimizationStrategy:
    """Optimization strategy configuration"""

    name: str
    level: OptimizationLevel
    cpu_threshold: float = 60.0
    memory_threshold: float = 70.0

    # Optimization actions
    reduce_update_frequency: bool = True
    enable_aggressive_caching: bool = True
    limit_widget_count: bool = True
    disable_animations: bool = False
    force_garbage_collection: bool = False

    # Limits
    max_widget_count: int = 50
    min_update_interval: float = 2.0
    max_update_interval: float = 10.0

    def should_optimize(self, metrics: PerformanceMetrics) -> bool:
        """Check if optimization should be applied"""
        return metrics.cpu_usage > self.cpu_threshold or metrics.memory_usage > self.memory_threshold


class PerformanceProfiler:
    """Performance profiling and measurement utilities"""

    def __init__(self):
        self.measurements: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=100))
        self.start_times: dict[str, float] = {}
        self.lock = threading.Lock()

    @contextmanager
    def measure(self, operation_name: str):
        """Context manager for measuring operation time"""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time

            with self.lock:
                self.measurements[operation_name].append(duration)

    def measure_function(self, operation_name: str | None = None):
        """Decorator for measuring function execution time"""

        def decorator(func: Callable) -> Callable:
            name = operation_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.measure(name):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def get_stats(self, operation_name: str) -> dict[str, float]:
        """Get statistics for an operation"""
        with self.lock:
            measurements = list(self.measurements[operation_name])

        if not measurements:
            return {
                "count": 0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
            }

        return {
            "count": len(measurements),
            "avg": statistics.mean(measurements),
            "min": min(measurements),
            "max": max(measurements),
            "std": statistics.stdev(measurements) if len(measurements) > 1 else 0.0,
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics for all operations"""
        with self.lock:
            return {name: self.get_stats(name) for name in self.measurements}


class PerformanceOptimizer:
    """
    Main performance optimization system

    Monitors system and application performance, automatically applies
    optimizations, and provides detailed performance reports.
    """

    _instance: Optional["PerformanceOptimizer"] = None

    @classmethod
    def get_instance(cls, monitoring_interval: float = 1.0) -> "PerformanceOptimizer":
        """Get the singleton instance of the performance optimizer."""
        if cls._instance is None:
            cls._instance = cls(monitoring_interval=monitoring_interval)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance."""
        if cls._instance and cls._instance.monitoring:
            cls._instance.stop_monitoring()
        cls._instance = None

    def __init__(self, monitoring_interval: float = 1.0):
        """
        Initialize performance optimizer

        Args:
            monitoring_interval: Interval between performance measurements in seconds
        """
        if PerformanceOptimizer._instance is not None:
            raise RuntimeError("PerformanceOptimizer is a singleton, use get_instance()")

        self.monitoring_interval = monitoring_interval
        self.monitoring = False
        self.monitor_thread: threading.Thread | None = None

        # Performance data
        self.metrics_history: deque[PerformanceMetrics] = deque(maxlen=300)  # 5 minutes at 1s interval
        self.current_metrics = PerformanceMetrics()

        # Profiler
        self.profiler = PerformanceProfiler()

        # Optimization
        self.current_optimization_level = OptimizationLevel.NONE
        self.optimization_strategies = self._create_optimization_strategies()
        self.applied_optimizations: list[str] = []

        # Callbacks
        self.optimization_callbacks: list[Callable[[OptimizationLevel], None]] = []
        self.metrics_callbacks: list[Callable[[PerformanceMetrics], None]] = []

        # Thread safety
        self.lock = threading.Lock()

        # System monitoring
        self.process = psutil.Process()

    def _create_optimization_strategies(
        self,
    ) -> dict[OptimizationLevel, OptimizationStrategy]:
        """Create built-in optimization strategies"""
        return {
            OptimizationLevel.NONE: OptimizationStrategy(
                name="No Optimization",
                level=OptimizationLevel.NONE,
                cpu_threshold=100.0,
                memory_threshold=100.0,
                reduce_update_frequency=False,
                enable_aggressive_caching=False,
                limit_widget_count=False,
            ),
            OptimizationLevel.LOW: OptimizationStrategy(
                name="Low Optimization",
                level=OptimizationLevel.LOW,
                cpu_threshold=70.0,
                memory_threshold=80.0,
                reduce_update_frequency=True,
                enable_aggressive_caching=True,
                limit_widget_count=False,
                min_update_interval=1.5,
            ),
            OptimizationLevel.MEDIUM: OptimizationStrategy(
                name="Medium Optimization",
                level=OptimizationLevel.MEDIUM,
                cpu_threshold=60.0,
                memory_threshold=70.0,
                reduce_update_frequency=True,
                enable_aggressive_caching=True,
                limit_widget_count=True,
                disable_animations=False,
                max_widget_count=30,
                min_update_interval=2.0,
            ),
            OptimizationLevel.HIGH: OptimizationStrategy(
                name="High Optimization",
                level=OptimizationLevel.HIGH,
                cpu_threshold=50.0,
                memory_threshold=60.0,
                reduce_update_frequency=True,
                enable_aggressive_caching=True,
                limit_widget_count=True,
                disable_animations=True,
                force_garbage_collection=True,
                max_widget_count=20,
                min_update_interval=3.0,
            ),
            OptimizationLevel.AGGRESSIVE: OptimizationStrategy(
                name="Aggressive Optimization",
                level=OptimizationLevel.AGGRESSIVE,
                cpu_threshold=40.0,
                memory_threshold=50.0,
                reduce_update_frequency=True,
                enable_aggressive_caching=True,
                limit_widget_count=True,
                disable_animations=True,
                force_garbage_collection=True,
                max_widget_count=10,
                min_update_interval=5.0,
                max_update_interval=15.0,
            ),
        }

    def start_monitoring(self) -> bool:
        """Start performance monitoring"""
        if self.monitoring:
            logger.warning("Performance monitoring already running")
            return False

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("Performance monitoring started")
        return True

    def stop_monitoring(self) -> bool:
        """Stop performance monitoring"""
        if not self.monitoring:
            logger.warning("Performance monitoring not running")
            return False

        self.monitoring = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)

        logger.info("Performance monitoring stopped")
        return True

    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        logger.debug("Performance monitoring loop started")

        while self.monitoring:
            try:
                # Collect metrics
                with self.profiler.measure("metrics_collection"):
                    metrics = self._collect_metrics()

                # Update current metrics
                with self.lock:
                    self.current_metrics = metrics
                    self.metrics_history.append(metrics)

                # Check for optimization needs
                self._check_optimization_needs(metrics)

                # Notify callbacks
                for callback in self.metrics_callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.error(f"Error in metrics callback: {e}")

                # Sleep until next measurement
                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

        logger.debug("Performance monitoring loop stopped")

    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        try:
            # System metrics
            cpu_usage = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()

            # System-wide memory
            system_memory = psutil.virtual_memory()

            # IO metrics
            io_counters = self.process.io_counters() if hasattr(self.process, "io_counters") else None

            # Dashboard metrics (would be updated by dashboard components)
            render_stats = self.profiler.get_stats("render")
            cache_stats = self._get_cache_stats()

            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_percent,
                memory_available=system_memory.available,
                disk_io_read=io_counters.read_bytes if io_counters else 0,
                disk_io_write=io_counters.write_bytes if io_counters else 0,
                render_time=render_stats.get("avg", 0.0),
                widget_count=self._get_widget_count(),
                active_connections=self._get_active_connections(),
                cache_hit_rate=cache_stats.get("hit_rate", 0.0),
                cache_size=cache_stats.get("size", 0),
                fps=1.0 / max(render_stats.get("avg", 0.001), 0.001),
                response_time=render_stats.get("avg", 0.0),
                update_frequency=1.0 / self.monitoring_interval,
            )

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return PerformanceMetrics()

    def _get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics (placeholder for actual cache integration)"""
        # This would integrate with actual cache systems
        return {
            "hit_rate": 0.85,  # Mock data
            "size": 1024 * 1024,  # 1MB
            "entries": 100,
        }

    def _get_widget_count(self) -> int:
        """Get current widget count (placeholder for actual integration)"""
        # This would integrate with dashboard widget system
        return 25  # Mock data

    def _get_active_connections(self) -> int:
        """Get active connection count (placeholder for actual integration)"""
        # This would integrate with web server or connection manager
        return 3  # Mock data

    def _check_optimization_needs(self, metrics: PerformanceMetrics) -> None:
        """Check if optimization is needed and apply if necessary"""
        threshold_level = metrics.get_threshold_level()

        # Determine needed optimization level
        if threshold_level == PerformanceThreshold.CRITICAL:
            needed_level = OptimizationLevel.AGGRESSIVE
        elif threshold_level == PerformanceThreshold.WARNING:
            needed_level = OptimizationLevel.HIGH
        elif threshold_level == PerformanceThreshold.GOOD:
            needed_level = OptimizationLevel.MEDIUM
        else:
            needed_level = OptimizationLevel.LOW

        # Apply optimization if level changed
        if needed_level != self.current_optimization_level:
            self._apply_optimization(needed_level)

    def _apply_optimization(self, level: OptimizationLevel) -> None:
        """Apply optimization strategy"""
        if level not in self.optimization_strategies:
            logger.error(f"Unknown optimization level: {level}")
            return

        strategy = self.optimization_strategies[level]
        previous_level = self.current_optimization_level

        with self.lock:
            self.current_optimization_level = level
            self.applied_optimizations = []

        logger.info(f"Applying optimization: {strategy.name}")

        # Apply optimizations
        if strategy.reduce_update_frequency:
            self._optimize_update_frequency(strategy)
            self.applied_optimizations.append("update_frequency")

        if strategy.enable_aggressive_caching:
            self._optimize_caching(strategy)
            self.applied_optimizations.append("caching")

        if strategy.limit_widget_count:
            self._optimize_widget_count(strategy)
            self.applied_optimizations.append("widget_count")

        if strategy.disable_animations:
            self._optimize_animations(strategy)
            self.applied_optimizations.append("animations")

        if strategy.force_garbage_collection:
            self._force_garbage_collection()
            self.applied_optimizations.append("garbage_collection")

        # Notify callbacks
        for callback in self.optimization_callbacks:
            try:
                callback(level)
            except Exception as e:
                logger.error(f"Error in optimization callback: {e}")

        logger.info(f"Optimization applied: {previous_level.value} -> {level.value}")

    def _optimize_update_frequency(self, strategy: OptimizationStrategy) -> None:
        """Optimize update frequency based on strategy"""
        new_interval = min(strategy.min_update_interval, strategy.max_update_interval)
        self.monitoring_interval = new_interval
        logger.debug(f"Update frequency optimized: {new_interval}s interval")

    def _optimize_caching(self, strategy: OptimizationStrategy) -> None:
        """Optimize caching behavior"""
        # This would integrate with actual cache systems
        logger.debug("Caching optimization applied")

    def _optimize_widget_count(self, strategy: OptimizationStrategy) -> None:
        """Optimize widget count"""
        # This would integrate with widget management system
        logger.debug(f"Widget count limited to: {strategy.max_widget_count}")

    def _optimize_animations(self, strategy: OptimizationStrategy) -> None:
        """Optimize animations"""
        # This would integrate with animation system
        logger.debug("Animations disabled for performance")

    def _force_garbage_collection(self) -> None:
        """Force garbage collection"""
        collected = gc.collect()
        logger.debug(f"Garbage collection forced: {collected} objects collected")

    def measure_render_time(self, func: Callable) -> Callable:
        """Decorator to measure render time"""
        return self.profiler.measure_function("render")(func)

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        with self.lock:
            return self.current_metrics

    def get_metrics_history(self, duration_minutes: int = 5) -> list[PerformanceMetrics]:
        """Get metrics history for specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)

        with self.lock:
            return [metrics for metrics in self.metrics_history if metrics.timestamp >= cutoff_time]

    def get_performance_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report"""
        current = self.get_current_metrics()
        history = self.get_metrics_history(5)
        profiler_stats = self.profiler.get_all_stats()

        # Calculate averages from history
        if history:
            avg_cpu = statistics.mean([m.cpu_usage for m in history])
            avg_memory = statistics.mean([m.memory_usage for m in history])
            avg_render_time = statistics.mean([m.render_time for m in history])
        else:
            avg_cpu = avg_memory = avg_render_time = 0.0

        # Generate recommendations
        recommendations = self._generate_recommendations(current, history)

        return {
            "timestamp": datetime.now().isoformat(),
            "current": current.to_dict(),
            "averages": {
                "cpu_usage": avg_cpu,
                "memory_usage": avg_memory,
                "render_time": avg_render_time,
            },
            "optimization": {
                "current_level": self.current_optimization_level.value,
                "applied_optimizations": self.applied_optimizations,
                "threshold": current.get_threshold_level().value,
            },
            "profiler_stats": profiler_stats,
            "recommendations": recommendations,
            "history_count": len(history),
        }

    def _generate_recommendations(self, current: PerformanceMetrics, history: list[PerformanceMetrics]) -> list[str]:
        """Generate performance recommendations"""
        recommendations = []

        # CPU recommendations
        if current.cpu_usage > 70:
            recommendations.append("High CPU usage detected. Consider reducing update frequency or widget count.")

        # Memory recommendations
        if current.memory_usage > 80:
            recommendations.append("High memory usage detected. Consider enabling aggressive caching or garbage collection.")

        # Render time recommendations
        if current.render_time > 0.1:
            recommendations.append("Slow rendering detected. Consider optimizing widget complexity or enabling caching.")

        # Cache recommendations
        if current.cache_hit_rate < 0.8:
            recommendations.append("Low cache hit rate. Consider adjusting cache size or retention policies.")

        # Historical trends
        if len(history) > 10:
            recent_cpu = statistics.mean([m.cpu_usage for m in history[-10:]])
            older_cpu = statistics.mean([m.cpu_usage for m in history[:10]])

            if recent_cpu > older_cpu * 1.2:
                recommendations.append("CPU usage trend increasing. Monitor for performance degradation.")

        if not recommendations:
            recommendations.append("Performance is optimal. No recommendations at this time.")

        return recommendations

    def add_optimization_callback(self, callback: Callable[[OptimizationLevel], None]) -> None:
        """Add callback for optimization level changes"""
        self.optimization_callbacks.append(callback)

    def add_metrics_callback(self, callback: Callable[[PerformanceMetrics], None]) -> None:
        """Add callback for metrics updates"""
        self.metrics_callbacks.append(callback)

    def set_optimization_level(self, level: OptimizationLevel) -> None:
        """Manually set optimization level"""
        self._apply_optimization(level)

    def reset_optimizations(self) -> None:
        """Reset all optimizations to default"""
        self._apply_optimization(OptimizationLevel.NONE)


class AsyncPerformanceOptimizer:
    """
    Asynchronous version of performance optimizer

    Provides non-blocking performance monitoring with rate limiting
    and concurrent optimization strategies.
    """

    def __init__(self, monitoring_interval: float = 1.0, max_concurrent_tasks: int = 10):
        """
        Initialize async performance optimizer

        Args:
            monitoring_interval: Interval between measurements
            max_concurrent_tasks: Maximum concurrent optimization tasks
        """
        self.monitoring_interval = monitoring_interval
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.monitoring_task: asyncio.Task | None = None
        self.optimizer = PerformanceOptimizer(monitoring_interval)

        # Rate limiting
        self.rate_limiter = defaultdict(float)
        self.rate_limit_window = 60.0  # 1 minute

    async def start_monitoring(self) -> bool:
        """Start async performance monitoring"""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("Async monitoring already running")
            return False

        self.monitoring_task = asyncio.create_task(self._async_monitor_loop())
        logger.info("Async performance monitoring started")
        return True

    async def stop_monitoring(self) -> bool:
        """Stop async performance monitoring"""
        if not self.monitoring_task or self.monitoring_task.done():
            logger.warning("Async monitoring not running")
            return False

        self.monitoring_task.cancel()

        with suppress(asyncio.CancelledError):
            await self.monitoring_task

        logger.info("Async performance monitoring stopped")
        return True

    async def _async_monitor_loop(self) -> None:
        """Async monitoring loop"""
        while True:
            try:
                async with self.semaphore:
                    # Collect metrics in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    metrics = await loop.run_in_executor(
                        None,
                        self.optimizer._collect_metrics,
                    )

                    # Update metrics with rate limiting
                    if self._should_update_metrics():
                        self.optimizer.current_metrics = metrics
                        self.optimizer.metrics_history.append(metrics)

                        # Check optimization needs
                        await self._async_check_optimization(metrics)

                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in async monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    def _should_update_metrics(self) -> bool:
        """Check if metrics should be updated based on rate limiting"""
        current_time = time.time()
        last_update = self.rate_limiter.get("metrics_update", 0)

        if current_time - last_update >= 1.0:  # Max 1 update per second
            self.rate_limiter["metrics_update"] = current_time
            return True

        return False

    async def _async_check_optimization(self, metrics: PerformanceMetrics) -> None:
        """Async optimization checking"""
        threshold_level = metrics.get_threshold_level()

        # Rate limit optimization applications
        current_time = time.time()
        last_optimization = self.rate_limiter.get("optimization", 0)

        if current_time - last_optimization < 30.0:  # Max 1 optimization per 30 seconds
            return

        if threshold_level == PerformanceThreshold.CRITICAL:
            self.rate_limiter["optimization"] = current_time
            await self._apply_async_optimization(OptimizationLevel.AGGRESSIVE)

    async def _apply_async_optimization(self, level: OptimizationLevel) -> None:
        """Apply optimization asynchronously"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.optimizer._apply_optimization,
            level,
        )

    async def get_performance_report(self) -> dict[str, Any]:
        """Get async performance report"""
        # For simplicity, delegate to sync implementation for now
        with self.lock:
            history = list(self.metrics_history)
            current = self.current_metrics
        return self.optimizer._generate_performance_report(current, history)


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance"""
    return PerformanceOptimizer.get_instance()


def reset_performance_optimizer() -> None:
    """Reset the global performance optimizer"""
    PerformanceOptimizer.reset_instance()
