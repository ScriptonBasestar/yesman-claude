import hashlib
import json
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import wraps

from .base_renderer import BaseRenderer, RenderFormat, WidgetType

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Rendering Optimizations and Caching
Performance optimization system for dashboard renderers.
"""

from typing import Any


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0

    def update_hit_rate(self) -> None:
        """Update hit rate calculation."""
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests
        else:
            self.hit_rate = 0.0


class RenderCache:
    """Thread-safe LRU cache for rendered output.

    Provides efficient caching of render results with configurable size limits,
    automatic eviction, and performance tracking.
    """

    def __init__(self, max_size: int = 1000, ttl: float | None = None) -> None:
        """Initialize render cache.

        Args:
            max_size: Maximum number of cached items
            ttl: Time-to-live in seconds (None for no expiry)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, dict[str, str | float]] = OrderedDict()
        self._lock = threading.RLock()
        self.stats = CacheStats()

    @staticmethod
    def _generate_cache_key(
        widget_type: WidgetType,
        data: dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool,  # noqa: FBT001
        options: dict[str, str | int | float | bool] | None = None,
        renderer_format: RenderFormat | None = None,
    ) -> str:
        """Generate consistent cache key from render parameters.

        Args:
            widget_type: Type of widget being rendered
            data: Widget data to render
            options: Rendering options
            renderer_format: Format of renderer

        Returns:
            Unique cache key string
        """
        # Create deterministic representation
        key_components = {
            "widget_type": widget_type.value,
            "options": options or {},
            "format": renderer_format.value if renderer_format else None,
        }

        # Handle data serialization carefully
        try:
            if hasattr(data, "to_dict"):
                data_repr = data.to_dict()
            elif hasattr(data, "__dict__"):
                data_repr = {k: str(v) for k, v in data.__dict__.items()}
            elif isinstance(data, list | tuple):
                data_repr = [str(item) for item in data]
            elif isinstance(data, dict):
                data_repr = {k: str(v) for k, v in data.items()}
            else:
                data_repr = str(data)

            key_components["data"] = data_repr

        except Exception:
            # Fallback to string representation
            key_components["data"] = str(data)[:1000]  # Limit size

        # Create hash from JSON representation
        try:
            key_string = json.dumps(key_components, sort_keys=True, default=str)
            return hashlib.sha256(key_string.encode()).hexdigest()
        except Exception:
            # Ultimate fallback
            return hashlib.sha256(str(key_components).encode()).hexdigest()

    def get(self, cache_key: str) -> str | dict[str, str | int | float | bool] | list[str | int | float | bool] | None:
        """Get cached result.

        Args:
            cache_key: Cache key to lookup

        Returns:
            Cached result or None if not found/expired
        """
        with self._lock:
            self.stats.total_requests += 1

            if cache_key not in self._cache:
                self.stats.misses += 1
                self.stats.update_hit_rate()
                return None

            cache_entry = self._cache[cache_key]

            # Check TTL if configured
            if self.ttl is not None and time.time() - cache_entry["timestamp"] > self.ttl:
                del self._cache[cache_key]
                self.stats.misses += 1
                self.stats.evictions += 1
                self.stats.update_hit_rate()
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)

            self.stats.hits += 1
            self.stats.update_hit_rate()
            return cache_entry["result"]

    def set(self, cache_key: str, result: str | dict[str, str | int | float | bool] | list[str | int | float | bool]) -> None:
        """Store result in cache.

        Args:
            cache_key: Cache key
            result: Result to cache
        """
        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._cache.popitem(last=False)
                self.stats.evictions += 1

            self._cache[cache_key] = {
                "result": result,
                "timestamp": time.time(),
            }

            # Move to end
            self._cache.move_to_end(cache_key)

    def invalidate(self, cache_key: str) -> bool:
        """Remove specific entry from cache.

        Args:
            cache_key: Key to remove

        Returns:
            True if key was found and removed
        """
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self.stats = CacheStats()

    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        with self._lock:
            return CacheStats(
                hits=self.stats.hits,
                misses=self.stats.misses,
                evictions=self.stats.evictions,
                total_requests=self.stats.total_requests,
                hit_rate=self.stats.hit_rate,
            )

    def get_size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)


# Global cache instances
_widget_cache = RenderCache(max_size=500, ttl=300)  # 5 minute TTL
_layout_cache = RenderCache(max_size=100, ttl=600)  # 10 minute TTL


def cached_render(cache: RenderCache | None = None) -> object:
    """Decorator for caching render method results.

    Args:
        cache: Cache instance to use (default: global widget cache)

    Returns:
        Description of return value
    """
    if cache is None:
        cache = _widget_cache

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            self: object | None,
            widget_type: WidgetType,
            data: dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool,  # noqa: FBT001
            options: dict[str, str | int | float | bool] | None = None,
        ):
            # Generate cache key
            renderer_format = getattr(self, "format_type", None)
            cache_key = RenderCache._generate_cache_key(widget_type, data, options, renderer_format)

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Render and cache - call with explicit arguments
            result = func(self, widget_type, data, options)
            cache.set(cache_key, result)
            return result

        return wrapper

    return decorator


def cached_layout(cache: RenderCache | None = None) -> object:
    """Decorator for caching layout method results.

    Args:
        cache: Cache instance to use (default: global layout cache)
    """
    if cache is None:
        cache = _layout_cache

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            self: object | None,
            widgets: list[dict[str, str | int | float | bool | object]],
            layout_config: dict[str, str | int | float | bool] | None = None,
        ):
            # Generate cache key from widgets and layout config
            cache_key_data = {
                "widgets": [
                    {
                        "type": (w.get("type", "").value if hasattr(w.get("type", ""), "value") else str(w.get("type", ""))),
                        "data_hash": str(hash(str(w.get("data", {}))))[:16],
                        "options": w.get("options", {}),
                    }
                    for w in widgets
                ],
                "layout_config": layout_config or {},
            }

            renderer_format = getattr(self, "format_type", None)
            cache_key = RenderCache._generate_cache_key(
                WidgetType.TABLE,  # Dummy widget type for layout
                cache_key_data,
                None,
                renderer_format,
            )

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Render and cache
            result = func(self, widgets, layout_config)
            cache.set(cache_key, result)
            return result

        return wrapper

    return decorator


class LazyRenderer:
    """Lazy rendering wrapper that defers actual rendering until needed.

    Useful for scenarios where render results might not be immediately consumed,
    reducing unnecessary computation.
    """

    def __init__(
        self,
        renderer: BaseRenderer,
        widget_type: WidgetType,
        data: dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool,  # noqa: FBT001
        options: dict[str, str | int | float | bool] | None = None,
    ) -> None:
        """Initialize lazy renderer.

        Args:
            renderer: Renderer instance to use
            widget_type: Type of widget to render
            data: Widget data
            options: Rendering options
        """
        self.renderer = renderer
        self.widget_type = widget_type
        self.data = data
        self.options = options or {}
        self._result: str | dict[str, str | int | float | bool] | list[str | int | float | bool] | None = None
        self._rendered = False
        self._lock = threading.Lock()

    def render(self) -> str | dict[str, str | int | float | bool] | list[str | int | float | bool]:
        """Perform actual rendering (called automatically when needed).

        Returns:
            Rendered result
        """
        if not self._rendered:
            with self._lock:
                if not self._rendered:  # Double-check pattern
                    self._result = self.renderer.render_widget(
                        self.widget_type,
                        self.data,
                        self.options,
                    )
                    self._rendered = True

        return self._result

    def __repr__(self) -> str:
        """String representation."""
        status = "rendered" if self._rendered else "pending"
        return f"LazyRenderer({self.widget_type.value}, {status})"

    def __str__(self) -> str:
        """Get rendered result as string."""
        return str(self.render())

    def is_rendered(self) -> bool:
        """Check if rendering has been performed."""
        return self._rendered


class BatchRenderer:
    """Batch renderer for efficiently processing multiple widgets.

    Optimizes rendering by grouping operations, reusing resources,
    and potentially parallelizing work.
    """

    def __init__(self, renderer: BaseRenderer, max_workers: int = 4) -> None:
        """Initialize batch renderer.

        Args:
            renderer: Base renderer to use
            max_workers: Maximum parallel workers
        """
        self.renderer = renderer
        self.max_workers = max_workers
        self._batch_cache = RenderCache(max_size=50, ttl=60)

    def render_batch(
        self,
        render_requests: list[
            tuple[WidgetType, dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool, dict[str, str | int | float | bool] | None]
        ],
        parallel: bool = True,  # noqa: FBT001
    ) -> list[str | dict[str, str | int | float | bool] | list[str | int | float | bool]]:
        """Render multiple widgets in batch.

        Args:
            render_requests: List of (widget_type, data, options) tuples
            parallel: Whether to use parallel processing

        Returns:
            List of rendered results in same order as requests
        """
        if not render_requests:
            return []

        if parallel and len(render_requests) > 1:
            return self._render_parallel(render_requests)
        return self._render_sequential(render_requests)

    def _render_sequential(
        self,
        render_requests: list[
            tuple[WidgetType, dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool, dict[str, str | int | float | bool] | None]
        ],
    ) -> list[str | dict[str, str | int | float | bool] | list[str | int | float | bool]]:
        """Render requests sequentially."""
        results = []
        for widget_type, data, options in render_requests:
            result = self.renderer.render_widget(widget_type, data, options or {})
            results.append(result)
        return results

    def _render_parallel(
        self,
        render_requests: list[
            tuple[WidgetType, dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool, dict[str, str | int | float | bool] | None]
        ],
    ) -> list[str | dict[str, str | int | float | bool] | list[str | int | float | bool]]:
        """Render requests in parallel."""
        results = [None] * len(render_requests)

        def render_single(
            index: int,
            widget_type: WidgetType,
            data: dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool,  # noqa: FBT001
            options: dict[str, str | int | float | bool] | None,
        ) -> tuple[int, str | dict[str, str | int | float | bool] | list[str | int | float | bool]]:
            try:
                result = self.renderer.render_widget(widget_type, data, options or {})
                return index, result
            except Exception as e:
                return index, f"Error: {e}"

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {executor.submit(render_single, i, widget_type, data, options): i for i, (widget_type, data, options) in enumerate(render_requests)}

            # Collect results
            for future in as_completed(future_to_index):
                index, result = future.result()
                results[index] = result

        return results

    def render_lazy_batch(
        self,
        render_requests: list[
            tuple[WidgetType, dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool, dict[str, str | int | float | bool] | None]
        ],
    ) -> list[LazyRenderer]:
        """Create lazy renderers for batch processing.

        Args:
            render_requests: List of render request tuples

        Returns:
            List of LazyRenderer instances
        """
        return [LazyRenderer(self.renderer, widget_type, data, options) for widget_type, data, options in render_requests]


class PerformanceProfiler:
    """Performance profiler for renderer operations.

    Tracks timing, memory usage, and other performance metrics
    for optimization purposes.
    """

    def __init__(self) -> None:
        self.metrics: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def time_operation(self, operation_name: str) -> object:
        """Context manager for timing operations.

        Args:
            operation_name: Name of operation being timed

        Returns:
            Description of return value
        """
        return TimingContext(self, operation_name)

    def record_time(self, operation_name: str, duration: float) -> None:
        """Record timing data.

        Args:
            operation_name: Name of operation
            duration: Duration in seconds
        """
        with self._lock:
            if operation_name not in self.metrics:
                self.metrics[operation_name] = []
            self.metrics[operation_name].append(duration)

    def get_stats(self, operation_name: str) -> dict[str, float]:
        """Get statistics for an operation.

        Args:
            operation_name: Name of operation

        Returns:
            Dictionary with min, max, avg, count statistics
        """
        with self._lock:
            if operation_name not in self.metrics:
                return {"min": 0, "max": 0, "avg": 0, "count": 0}

            times = self.metrics[operation_name]
            return {
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
                "count": len(times),
            }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics for all tracked operations."""
        return {name: self.get_stats(name) for name in self.metrics}

    def clear(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self.metrics.clear()


class TimingContext:
    """Context manager for timing operations."""

    def __init__(self, profiler: PerformanceProfiler, operation_name: str) -> None:
        self.profiler = profiler
        self.operation_name = operation_name
        self.start_time: float | None = None

    def __enter__(self) -> object:
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object | None) -> None:
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.profiler.record_time(self.operation_name, duration)


# Global profiler instance
global_profiler = PerformanceProfiler()


def profile_render(operation_name: str | None = None) -> object:
    """Decorator for profiling render operations.

    Args:
        operation_name: Name for the operation (defaults to function name)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs: Any) -> object:
            name = operation_name or f"{func.__module__}.{func.__name__}"
            with global_profiler.time_operation(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Utility functions


def get_cache_stats() -> dict[str, CacheStats]:
    """Get statistics for all caches."""
    return {
        "widget_cache": _widget_cache.get_stats(),
        "layout_cache": _layout_cache.get_stats(),
    }


def clear_all_caches() -> None:
    """Clear all global caches."""
    _widget_cache.clear()
    _layout_cache.clear()


def get_performance_stats() -> dict[str, dict[str, float]]:
    """Get all performance statistics."""
    return global_profiler.get_all_stats()


def clear_performance_stats() -> None:
    """Clear all performance statistics."""
    global_profiler.clear()
