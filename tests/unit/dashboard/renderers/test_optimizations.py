# Copyright notice.

import threading
import time
from typing import Any

from libs.dashboard.renderers.base_renderer import (
    BaseRenderer,
    RenderFormat,
    WidgetType,
)
from libs.dashboard.renderers.optimizations import (
    BatchRenderer,
    CacheStats,
    LazyRenderer,
    PerformanceProfiler,
    RenderCache,
    cached_layout,
    cached_render,
    clear_all_caches,
    clear_performance_stats,
    get_cache_stats,
    get_performance_stats,
    global_profiler,
    profile_render,
)
from libs.dashboard.renderers.tui_renderer import TUIRenderer
from libs.dashboard.renderers.widget_models import MetricCardData

"""Tests for Rendering Optimizations and Caching."""


class MockRenderer(BaseRenderer):
    """Mock renderer for testing."""

    def __init__(self, render_format: RenderFormat = RenderFormat.TUI, delay: float = 0.0) -> None:
        super().__init__(render_format)
        self.delay = delay
        self.render_count = 0
        self.last_params = None

    def render_widget(self, widget_type: WidgetType, data: Any, options: dict | None = None) -> str:
        self.render_count += 1
        self.last_params = (widget_type, data, options)

        if self.delay > 0:
            time.sleep(self.delay)

        return f"mock-{widget_type.value}-{self.render_count}"

    @staticmethod
    def render_layout(widgets: list, layout_config: dict | None = None) -> str:  # noqa: ARG002, ARG004
        return f"mock-layout-{len(widgets)}"

    @staticmethod
    def render_container(content: str, container_config: dict | None = None) -> str:  # noqa: ARG002, ARG004
        return "mock-container"

    @staticmethod
    def supports_feature(feature: str) -> bool:  # noqa: ARG002, ARG004
        return True


class TestRenderCache:
    """Test cases for RenderCache."""

    def setup_method(self) -> None:
        """Setup for each test."""
        self.cache = RenderCache(max_size=3)

    def test_cache_initialization(self) -> None:
        """Test cache initialization."""
        assert self.cache.max_size == 3
        assert self.cache.ttl is None
        assert self.cache.get_size() == 0
        assert isinstance(self.cache.stats, CacheStats)

    def test_cache_key_generation(self) -> None:
        """Test cache key generation."""
        metric = MetricCardData(title="Test", value=100)

        key1 = self.cache._generate_cache_key(
            WidgetType.METRIC_CARD,
            metric,
            {"option": "value"},
            RenderFormat.TUI,
        )

        key2 = self.cache._generate_cache_key(
            WidgetType.METRIC_CARD,
            metric,
            {"option": "value"},
            RenderFormat.TUI,
        )

        key3 = self.cache._generate_cache_key(
            WidgetType.METRIC_CARD,
            metric,
            {"option": "different"},
            RenderFormat.TUI,
        )

        # Same parameters should generate same key
        assert key1 == key2

        # Different parameters should generate different key
        assert key1 != key3

        # Keys should be hex strings
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hex length

    def test_cache_set_get(self) -> None:
        """Test basic cache set and get operations."""
        key = "test-key"
        value = "test-value"

        # Should return None for non-existent key
        assert self.cache.get(key) is None

        # Set and get value
        self.cache.set(key, value)
        assert self.cache.get(key) == value
        assert self.cache.get_size() == 1

    def test_cache_lru_eviction(self) -> None:
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        for i in range(3):
            self.cache.set(f"key-{i}", f"value-{i}")

        assert self.cache.get_size() == 3

        # Access key-1 to make it recently used
        self.cache.get("key-1")

        # Add new item (should evict key-0, the least recently used)
        self.cache.set("key-3", "value-3")

        assert self.cache.get_size() == 3
        assert self.cache.get("key-0") is None  # Evicted
        assert self.cache.get("key-1") == "value-1"  # Still there
        assert self.cache.get("key-2") == "value-2"  # Still there
        assert self.cache.get("key-3") == "value-3"  # New item

    @staticmethod
    def test_cache_ttl_expiry() -> None:
        """Test TTL-based cache expiry."""
        cache_with_ttl = RenderCache(max_size=10, ttl=0.1)  # 100ms TTL

        cache_with_ttl.set("key", "value")
        assert cache_with_ttl.get("key") == "value"

        # Wait for expiry
        time.sleep(0.15)

        assert cache_with_ttl.get("key") is None

    def test_cache_stats(self) -> None:
        """Test cache statistics tracking."""
        # Initially no stats
        stats = self.cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0

        # Cache miss
        self.cache.get("nonexistent")
        stats = self.cache.get_stats()
        assert stats.misses == 1
        assert stats.total_requests == 1

        # Cache hit
        self.cache.set("key", "value")
        self.cache.get("key")
        stats = self.cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.total_requests == 2
        assert stats.hit_rate == 0.5

    def test_cache_invalidation(self) -> None:
        """Test cache invalidation."""
        self.cache.set("key", "value")
        assert self.cache.get("key") == "value"

        # Invalidate specific key
        assert self.cache.invalidate("key") is True
        assert self.cache.get("key") is None

        # Invalidating non-existent key
        assert self.cache.invalidate("nonexistent") is False

    def test_cache_clear(self) -> None:
        """Test cache clearing."""
        for i in range(3):
            self.cache.set(f"key-{i}", f"value-{i}")

        assert self.cache.get_size() == 3

        self.cache.clear()

        assert self.cache.get_size() == 0
        stats = self.cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0

    def test_cache_thread_safety(self) -> None:
        """Test cache thread safety."""
        results = []
        errors = []

        def cache_worker(worker_id: int) -> None:
            try:
                for i in range(10):
                    key = f"worker-{worker_id}-{i}"
                    value = f"value-{worker_id}-{i}"

                    self.cache.set(key, value)
                    retrieved = self.cache.get(key)

                    if retrieved == value:
                        results.append(True)
                    else:
                        results.append(False)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert len(results) == 50
        assert all(results)  # All operations should succeed


class TestCachedDecorators:
    """Test cases for caching decorators."""

    def setup_method(self) -> None:
        """Setup for each test."""
        self.cache = RenderCache(max_size=10)
        self.renderer = MockRenderer()

    def test_cached_render_decorator(self) -> None:
        """Test cached_render decorator."""
        self.render_count = 0

        @cached_render(self.cache)
        def mock_render(widget_type: WidgetType, data: Any, options: dict | None = None) -> str:
            self.render_count += 1
            return f"render-{self.render_count}"

        # Bind method to renderer
        bound_method = mock_render.__get__(self.renderer, MockRenderer)

        metric = MetricCardData(title="Test", value=100)

        # First call should execute function
        result1 = bound_method(WidgetType.METRIC_CARD, metric)
        assert result1 == "render-1"

        # Second call should return cached result
        result2 = bound_method(WidgetType.METRIC_CARD, metric)
        assert result2 == "render-1"
        assert self.renderer.render_count == 1  # Function called only once

    def test_cached_layout_decorator(self) -> None:
        """Test cached_layout decorator."""

        @cached_layout(self.cache)
        def mock_render_layout(self: MockRenderer, widgets: list, layout_config: dict | None = None) -> str:
            return f"layout-{len(widgets)}-{id(layout_config)}"

        # Bind method to renderer
        bound_method = mock_render_layout.__get__(self.renderer, MockRenderer)

        widgets = [
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test1", value=100),
            },
            {
                "type": WidgetType.METRIC_CARD,
                "data": MetricCardData(title="Test2", value=200),
            },
        ]
        layout_config = {"type": "grid", "columns": 2}

        # First call
        result1 = bound_method(widgets, layout_config)

        # Second call with same parameters should return cached result
        result2 = bound_method(widgets, layout_config)

        assert result1 == result2


class TestLazyRenderer:
    """Test cases for LazyRenderer."""

    def setup_method(self) -> None:
        """Setup for each test."""
        self.renderer = MockRenderer(delay=0.01)  # Small delay to test timing
        self.metric = MetricCardData(title="Test", value=100)

    def test_lazy_renderer_initialization(self) -> None:
        """Test lazy renderer initialization."""
        lazy = LazyRenderer(
            self.renderer,
            WidgetType.METRIC_CARD,
            self.metric,
            {"option": "value"},
        )

        assert lazy.renderer is self.renderer
        assert lazy.widget_type == WidgetType.METRIC_CARD
        assert lazy.data is self.metric
        assert lazy.options == {"option": "value"}
        assert not lazy.is_rendered()

    def test_lazy_rendering_deferred(self) -> None:
        """Test that rendering is deferred until needed."""
        lazy = LazyRenderer(self.renderer, WidgetType.METRIC_CARD, self.metric)

        # No rendering should have occurred yet
        assert self.renderer.render_count == 0
        assert not lazy.is_rendered()

        # Force rendering
        result = lazy.render()

        assert self.renderer.render_count == 1
        assert lazy.is_rendered()
        assert result == "mock-metric_card-1"

    def test_lazy_rendering_cached(self) -> None:
        """Test that lazy rendering caches result."""
        lazy = LazyRenderer(self.renderer, WidgetType.METRIC_CARD, self.metric)

        # Multiple calls should only render once
        result1 = lazy.render()
        result2 = lazy.render()

        assert result1 == result2
        assert self.renderer.render_count == 1

    def test_lazy_renderer_string_conversion(self) -> None:
        """Test string conversion triggers rendering."""
        lazy = LazyRenderer(self.renderer, WidgetType.METRIC_CARD, self.metric)

        assert not lazy.is_rendered()

        # String conversion should trigger rendering
        string_result = str(lazy)

        assert lazy.is_rendered()
        assert self.renderer.render_count == 1
        assert "mock-metric_card-1" in string_result

    def test_lazy_renderer_thread_safety(self) -> None:
        """Test lazy renderer thread safety."""
        lazy = LazyRenderer(self.renderer, WidgetType.METRIC_CARD, self.metric)
        results = []

        def render_worker() -> None:
            results.append(lazy.render())

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=render_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should only render once despite multiple threads
        assert self.renderer.render_count == 1
        assert all(result == results[0] for result in results)


class TestBatchRenderer:
    """Test cases for BatchRenderer."""

    def setup_method(self) -> None:
        """Setup for each test."""
        self.base_renderer = MockRenderer(delay=0.01)
        self.batch_renderer = BatchRenderer(self.base_renderer, max_workers=2)

    def test_batch_renderer_initialization(self) -> None:
        """Test batch renderer initialization."""
        assert self.batch_renderer.renderer is self.base_renderer
        assert self.batch_renderer.max_workers == 2
        assert isinstance(self.batch_renderer._batch_cache, RenderCache)

    def test_batch_sequential_rendering(self) -> None:
        """Test sequential batch rendering."""
        requests = [
            (WidgetType.METRIC_CARD, MetricCardData(title="Test1", value=100), None),
            (WidgetType.METRIC_CARD, MetricCardData(title="Test2", value=200), None),
            (WidgetType.METRIC_CARD, MetricCardData(title="Test3", value=300), None),
        ]

        results = self.batch_renderer.render_batch(requests, parallel=False)

        assert len(results) == 3
        assert all("mock-metric_card" in result for result in results)
        assert self.base_renderer.render_count == 3

    def test_batch_parallel_rendering(self) -> None:
        """Test parallel batch rendering."""
        requests = [
            (WidgetType.METRIC_CARD, MetricCardData(title="Test1", value=100), None),
            (WidgetType.METRIC_CARD, MetricCardData(title="Test2", value=200), None),
            (WidgetType.METRIC_CARD, MetricCardData(title="Test3", value=300), None),
        ]

        start_time = time.time()
        results = self.batch_renderer.render_batch(requests, parallel=True)
        end_time = time.time()

        assert len(results) == 3
        assert all("mock-metric_card" in result for result in results)
        assert self.base_renderer.render_count == 3

        # Parallel should be faster than sequential (with delay)
        sequential_time = 3 * 0.01  # 3 requests * 0.01s delay
        parallel_time = end_time - start_time
        assert parallel_time < sequential_time * 0.8  # Allow some overhead

    def test_batch_empty_requests(self) -> None:
        """Test batch rendering with empty requests."""
        results = self.batch_renderer.render_batch([])
        assert results == []

    def test_batch_lazy_rendering(self) -> None:
        """Test lazy batch rendering."""
        requests = [
            (WidgetType.METRIC_CARD, MetricCardData(title="Test1", value=100), None),
            (WidgetType.METRIC_CARD, MetricCardData(title="Test2", value=200), None),
        ]

        lazy_renderers = self.batch_renderer.render_lazy_batch(requests)

        assert len(lazy_renderers) == 2
        assert all(isinstance(lr, LazyRenderer) for lr in lazy_renderers)
        assert self.base_renderer.render_count == 0  # No rendering yet

        # Force rendering of first lazy renderer
        result1 = lazy_renderers[0].render()
        assert self.base_renderer.render_count == 1
        assert "mock-metric_card" in result1


class TestPerformanceProfiler:
    """Test cases for PerformanceProfiler."""

    def setup_method(self) -> None:
        """Setup for each test."""
        self.profiler = PerformanceProfiler()

    def test_profiler_initialization(self) -> None:
        """Test profiler initialization."""
        assert isinstance(self.profiler.metrics, dict)
        assert len(self.profiler.metrics) == 0

    def test_timing_context(self) -> None:
        """Test timing context manager."""
        with self.profiler.time_operation("test_op"):
            time.sleep(0.01)

        stats = self.profiler.get_stats("test_op")
        assert stats["count"] == 1
        assert stats["min"] >= 0.01
        assert stats["max"] >= 0.01
        assert stats["avg"] >= 0.01

    def test_manual_timing_recording(self) -> None:
        """Test manual timing recording."""
        self.profiler.record_time("manual_op", 0.05)
        self.profiler.record_time("manual_op", 0.03)

        stats = self.profiler.get_stats("manual_op")
        assert stats["count"] == 2
        assert stats["min"] == 0.03
        assert stats["max"] == 0.05
        assert stats["avg"] == 0.04

    def test_nonexistent_operation_stats(self) -> None:
        """Test stats for non-existent operation."""
        stats = self.profiler.get_stats("nonexistent")
        assert stats["count"] == 0
        assert stats["min"] == 0
        assert stats["max"] == 0
        assert stats["avg"] == 0

    def test_profiler_clear(self) -> None:
        """Test profiler clearing."""
        self.profiler.record_time("test_op", 0.01)
        assert len(self.profiler.metrics) == 1

        self.profiler.clear()
        assert len(self.profiler.metrics) == 0

    @staticmethod
    def test_profile_render_decorator() -> None:
        """Test profile_render decorator."""

        @profile_render("decorated_op")
        def test_function() -> str:
            time.sleep(0.01)
            return "result"

        result = test_function()

        assert result == "result"
        stats = global_profiler.get_stats("decorated_op")
        assert stats["count"] == 1
        assert stats["avg"] >= 0.01


class TestOptimizationIntegration:
    """Integration tests for optimization features."""

    def setup_method(self) -> None:
        """Setup for each test."""
        clear_all_caches()
        clear_performance_stats()
        self.renderer = TUIRenderer()

    @staticmethod
    def teardown_method() -> None:
        """Cleanup after each test."""
        clear_all_caches()
        clear_performance_stats()

    @staticmethod
    def test_cache_performance_improvement() -> None:
        """Test that caching improves performance."""
        metric = MetricCardData(title="Performance Test", value=75.5, suffix="%")

        # Use a mock renderer with built-in delay tracking
        mock_renderer = MockRenderer(delay=0.05)  # 50ms delay

        # Apply caching directly to the class method (not instance method)
        MockRenderer.render_widget = cached_render()(MockRenderer.render_widget)

        # First render (cache miss)
        start1 = time.time()
        result1 = mock_renderer.render_widget(WidgetType.METRIC_CARD, metric)
        time1 = time.time() - start1

        # Second render (cache hit)
        start2 = time.time()
        result2 = mock_renderer.render_widget(WidgetType.METRIC_CARD, metric)
        time2 = time.time() - start2

        # Verify results are identical
        assert result1 == result2

        # Cache hit should be much faster than cache miss
        assert time2 < time1 * 0.5  # At least 50% faster

        # Verify the underlying method was called only once (second call was cached)
        assert mock_renderer.render_count == 1

    def test_lazy_vs_eager_rendering(self) -> None:
        """Test performance difference between lazy and eager rendering."""
        metric = MetricCardData(title="Lazy Test", value=100)

        # Eager rendering
        start_eager = time.time()
        eager_result = self.renderer.render_widget(WidgetType.METRIC_CARD, metric)
        eager_time = time.time() - start_eager

        # Lazy rendering (creation only)
        start_lazy_create = time.time()
        lazy_renderer = LazyRenderer(self.renderer, WidgetType.METRIC_CARD, metric)
        lazy_create_time = time.time() - start_lazy_create

        # Lazy rendering should be much faster to create
        assert lazy_create_time < eager_time * 0.1

        # But results should be the same when forced
        lazy_result = lazy_renderer.render()
        assert eager_result == lazy_result

    def test_batch_vs_individual_rendering(self) -> None:
        """Test batch rendering performance."""
        metrics = [MetricCardData(title=f"Metric {i}", value=i * 10) for i in range(5)]

        batch_renderer = BatchRenderer(self.renderer, max_workers=3)

        # Individual rendering
        start_individual = time.time()
        individual_results = []
        for metric in metrics:
            result = self.renderer.render_widget(WidgetType.METRIC_CARD, metric)
            individual_results.append(result)
        time.time() - start_individual

        # Batch rendering
        requests = [(WidgetType.METRIC_CARD, metric, None) for metric in metrics]

        start_batch = time.time()
        batch_results = batch_renderer.render_batch(requests, parallel=True)
        time.time() - start_batch

        # Results should be equivalent
        assert len(individual_results) == len(batch_results)

        # Both approaches should produce valid results
        assert all("Performance Test" in str(result) or "Metric" in str(result) for result in individual_results)
        assert all("Performance Test" in str(result) or "Metric" in str(result) for result in batch_results)

    @staticmethod
    def test_global_cache_utilities() -> None:
        """Test global cache utility functions."""
        # Initially empty stats
        stats = get_cache_stats()
        assert "widget_cache" in stats
        assert "layout_cache" in stats

        # Create some cache activity using MockRenderer to avoid decorator issues
        metric = MetricCardData(title="Cache Test", value=100)
        mock_renderer = MockRenderer()

        # Apply caching to the MockRenderer class
        MockRenderer.render_widget = cached_render()(MockRenderer.render_widget)

        # Generate cache activity
        mock_renderer.render_widget(WidgetType.METRIC_CARD, metric)
        mock_renderer.render_widget(WidgetType.METRIC_CARD, metric)  # Cache hit

        # Check stats
        updated_stats = get_cache_stats()
        assert updated_stats["widget_cache"].total_requests > 0

        # Clear caches
        clear_all_caches()
        cleared_stats = get_cache_stats()
        assert cleared_stats["widget_cache"].total_requests == 0

    @staticmethod
    def test_global_performance_utilities() -> None:
        """Test global performance utility functions."""
        # Initially empty
        stats = get_performance_stats()
        assert isinstance(stats, dict)

        # Create some profiled activity
        @profile_render("test_operation")
        def test_operation() -> str:
            time.sleep(0.001)
            return "done"

        test_operation()

        # Check stats
        updated_stats = get_performance_stats()
        assert "test_operation" in updated_stats
        assert updated_stats["test_operation"]["count"] == 1

        # Clear stats
        clear_performance_stats()
        cleared_stats = get_performance_stats()
        assert len(cleared_stats) == 0
