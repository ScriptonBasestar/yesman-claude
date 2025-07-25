import gc
import os
import threading
import time
from datetime import UTC, datetime
from typing import Any, cast

import psutil
import pytest

from libs.dashboard.renderers import (
    BatchRenderer,
    LazyRenderer,
    RenderCache,
    RendererFactory,
    RenderFormat,
    TUIRenderer,
    WebRenderer,
    WidgetType,
    clear_all_caches,
    render_all_formats,
    render_widget,
)
from libs.dashboard.renderers.optimizations import cached_render
from libs.dashboard.renderers.widget_models import (
    ActivityData,
    ActivityEntry,
    ActivityType,
    ChartData,
    ChartDataPoint,
    HealthCategoryData,
    HealthData,
    HealthLevel,
    MetricCardData,
    ProgressData,
    ProgressPhase,
    SessionData,
    SessionStatus,
    StatusIndicatorData,
    WindowData,
)

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Comprehensive Renderer System Integration Tests
Testing the complete renderer ecosystem with cross-format compatibility,
performance benchmarks, and memory stability.
"""


class TestRendererSystemIntegration:
    """Integration tests for the complete renderer system."""

    def setup_method(self) -> None:
        """Setup for each test."""
        clear_all_caches()
        RendererFactory.reset()
        self.test_data = self._create_comprehensive_test_data()

    @staticmethod
    def teardown_method() -> None:
        """Cleanup after each test."""
        clear_all_caches()
        RendererFactory.reset()
        gc.collect()

    @staticmethod
    def _create_comprehensive_test_data() -> dict[str, Any]:
        """Create comprehensive test data covering all widget types."""
        now = datetime.now(UTC)

        return {
            "session": SessionData(
                name="integration-test-session",
                id="session-int-123",
                status=SessionStatus.ACTIVE,
                created_at=now,
                windows=[
                    WindowData(id="1", name="editor", active=True, panes=3),
                    WindowData(id="2", name="terminal", active=False, panes=1),
                ],
                panes=4,
                claude_active=True,
                cpu_usage=25.5,
                memory_usage=45.2,
            ),
            "health": HealthData(
                overall_score=85,
                overall_level=HealthLevel.GOOD,
                categories=[
                    HealthCategoryData(
                        category="build",
                        score=90,
                        level=HealthLevel.EXCELLENT,
                        message="All tests passing",
                    ),
                    HealthCategoryData(
                        category="dependencies",
                        score=80,
                        level=HealthLevel.GOOD,
                        message="Most dependencies up to date",
                    ),
                ],
                last_updated=now,
            ),
            "activity": ActivityData(
                entries=[
                    ActivityEntry(
                        timestamp=now,
                        activity_type=ActivityType.FILE_CREATED,
                        description="Created integration test",
                    ),
                ],
                total_activities=50,
                active_days=7,
                activity_rate=85.0,
                current_streak=5,
                longest_streak=12,
                avg_per_day=7.1,
            ),
            "progress": ProgressData(
                phase=ProgressPhase.IMPLEMENTING,
                phase_progress=75.0,
                overall_progress=60.0,
                files_created=15,
                files_modified=25,
                commands_executed=50,
                commands_succeeded=47,
                commands_failed=3,
                start_time=now,
                todos_identified=20,
                todos_completed=15,
            ),
            "metric": MetricCardData(
                title="System Performance",
                value=92.5,
                suffix="%",
                trend=2.3,
                color="success",
                icon="⚡",
                comparison="vs last hour",
            ),
            "status": StatusIndicatorData(
                status="operational",
                label="System Status",
                color="success",
                icon="✅",
                pulse=True,
            ),
            "chart": ChartData(
                title="Performance Trends",
                chart_type="line",
                data_points=[
                    ChartDataPoint(x=1, y=80),
                    ChartDataPoint(x=2, y=85),
                    ChartDataPoint(x=3, y=92),
                ],
                x_label="Time",
                y_label="Performance %",
            ),
            "logs": {
                "logs": [
                    {
                        "timestamp": "2023-01-01T10:00:00",
                        "level": "INFO",
                        "message": "System started",
                    },
                    {
                        "timestamp": "2023-01-01T10:01:00",
                        "level": "WARNING",
                        "message": "High memory usage detected",
                    },
                ],
            },
            "table": {
                "headers": ["Component", "Status", "Load"],
                "rows": [
                    ["CPU", "Normal", "25%"],
                    ["Memory", "Warning", "85%"],
                    ["Disk", "Normal", "45%"],
                ],
            },
        }

    def test_all_formats_render_all_widgets(self) -> None:
        """Test that all formats can render all widget types."""
        widget_tests = [
            (
                WidgetType.SESSION_BROWSER,
                [cast(SessionData, self.test_data["session"])],
            ),
            (WidgetType.HEALTH_METER, cast(HealthData, self.test_data["health"])),
            (
                WidgetType.ACTIVITY_HEATMAP,
                cast(ActivityData, self.test_data["activity"]),
            ),
            (
                WidgetType.PROGRESS_TRACKER,
                cast(ProgressData, self.test_data["progress"]),
            ),
            (WidgetType.METRIC_CARD, cast(MetricCardData, self.test_data["metric"])),
            (
                WidgetType.STATUS_INDICATOR,
                cast(StatusIndicatorData, self.test_data["status"]),
            ),
            (WidgetType.CHART, cast(ChartData, self.test_data["chart"])),
            (WidgetType.LOG_VIEWER, cast(list, self.test_data["logs"])),
            (WidgetType.TABLE, cast(dict, self.test_data["table"])),
        ]

        formats = [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]

        for widget_type, data in widget_tests:
            for render_format in formats:
                try:
                    result = render_widget(widget_type, cast(Any, data), render_format)
                    assert result is not None

                    # Format-specific validations
                    if render_format == RenderFormat.TUI:
                        assert isinstance(result, str)
                        assert len(result) > 0
                    elif render_format == RenderFormat.WEB:
                        assert isinstance(result, str)
                        assert "<div" in result or "<table" in result
                    elif render_format == RenderFormat.TAURI:
                        assert isinstance(result, dict)
                        assert "widget_type" in result
                        assert "data" in result

                except (ValueError, TypeError, AttributeError, KeyError) as e:
                    pytest.fail(
                        f"Failed to render {widget_type.value} with {render_format.value}: {e}"
                    )

    def test_cross_format_consistency(self) -> None:
        """Test that different formats produce consistent data structures."""
        metric = cast(MetricCardData, self.test_data["metric"])

        results = render_all_formats(WidgetType.METRIC_CARD, cast(Any, metric))

        assert len(results) == 3
        assert RenderFormat.TUI in results
        assert RenderFormat.WEB in results
        assert RenderFormat.TAURI in results

        # All should contain the metric title
        tui_result = results[RenderFormat.TUI]
        web_result = results[RenderFormat.WEB]
        tauri_result = results[RenderFormat.TAURI]

        assert "System Performance" in tui_result
        assert "System Performance" in web_result
        assert cast(dict, tauri_result)["data"]["title"] == "System Performance"

        # All should reflect the value
        assert "92.5" in tui_result or "92.50" in tui_result
        assert "92.5" in web_result or "92.50" in web_result
        assert cast(dict, tauri_result)["data"]["value"] == 92.5

    @staticmethod
    def test_data_transformation_pipeline() -> None:
        """Test complete data transformation from models to rendered output."""
        # Start with raw data
        raw_health_data = {
            "overall_score": 75,
            "categories": [
                {"category": "build", "score": 80, "message": "Good"},
            ],
        }

        # Convert to model
        health_data = HealthData.from_dict(raw_health_data)

        # Render with all formats
        results = render_all_formats(WidgetType.HEALTH_METER, cast(Any, health_data))

        # Verify transformation preserved data
        for format_type, result in results.items():
            if format_type == RenderFormat.TAURI:
                result_dict = cast(dict, result)
                assert result_dict["data"]["overall_score"] == 75
                assert len(result_dict["data"]["categories"]) == 1
                assert result_dict["data"]["categories"][0]["category"] == "build"
            else:
                assert "75" in str(result)
                assert "build" in str(result).lower()

    @staticmethod
    def test_error_handling_scenarios() -> None:
        """Test error handling across different scenarios."""
        # Test with None data
        for render_format in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]:
            try:
                result = render_widget(WidgetType.METRIC_CARD, None, render_format)
                # Should either handle gracefully or provide error info
                assert result is not None
            except (ValueError, TypeError, AttributeError, KeyError):
                # Exceptions are acceptable for invalid data
                pass

        # Test with invalid data type
        for render_format in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]:
            try:
                result = render_widget(
                    WidgetType.HEALTH_METER, cast(Any, "invalid"), render_format
                )
                if render_format == RenderFormat.TAURI:
                    assert "error" in cast(dict, result).get("data", {})
                # Other formats should handle gracefully
            except (ValueError, TypeError, AttributeError, KeyError):
                # Exceptions are acceptable for invalid data
                pass

        # Test with missing required fields
        incomplete_session = SessionData(
            name="incomplete",
            id="inc-123",
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(UTC),
            windows=[],  # Minimal required fields
        )

        # Should render without crashing
        for render_format in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]:
            result = render_widget(
                WidgetType.SESSION_BROWSER,
                cast(Any, [incomplete_session]),
                render_format,
            )
            assert result is not None

    @staticmethod
    def test_edge_cases_and_boundaries() -> None:
        """Test edge cases and boundary conditions."""
        # Empty collections
        empty_sessions: list[Any] = []
        empty_logs: dict[str, Any] = {"logs": []}
        empty_table: dict[str, Any] = {"headers": [], "rows": []}

        edge_cases = [
            (WidgetType.SESSION_BROWSER, empty_sessions),
            (WidgetType.LOG_VIEWER, empty_logs),
            (WidgetType.TABLE, empty_table),
        ]

        for widget_type, data in edge_cases:
            for render_format in [
                RenderFormat.TUI,
                RenderFormat.WEB,
                RenderFormat.TAURI,
            ]:
                result = render_widget(widget_type, cast(Any, data), render_format)
                assert result is not None

                if render_format == RenderFormat.TAURI:
                    assert isinstance(result, dict)
                    assert "data" in result

        # Extreme values
        extreme_metric = MetricCardData(
            title="Extreme Test",
            value=999999.99,
            suffix="%",
            trend=-50.0,
        )

        for render_format in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]:
            result = render_widget(
                WidgetType.METRIC_CARD, cast(Any, extreme_metric), render_format
            )
            assert result is not None

            if render_format == RenderFormat.TAURI:
                result_dict = cast(dict, result)
                assert result_dict["data"]["value"] == 999999.99
                assert result_dict["data"]["trend"] == -50.0

    @staticmethod
    def test_concurrent_rendering() -> None:
        """Test concurrent rendering across multiple threads."""
        results = []
        errors = []

        def render_worker(worker_id: int) -> None:
            try:
                metric = MetricCardData(
                    title=f"Worker {worker_id}",
                    value=worker_id * 10,
                )

                # Render with different formats
                for render_format in [
                    RenderFormat.TUI,
                    RenderFormat.WEB,
                    RenderFormat.TAURI,
                ]:
                    result = render_widget(
                        WidgetType.METRIC_CARD, cast(Any, metric), render_format
                    )
                    results.append((worker_id, render_format, result))

            except (ValueError, TypeError, AttributeError, KeyError, RuntimeError) as e:
                errors.append((worker_id, str(e)))

        # Run 10 workers concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=render_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Concurrent rendering errors: {errors}"
        assert len(results) == 30  # 10 workers * 3 formats

        # Verify each worker produced valid results
        worker_results: dict[int, dict[RenderFormat, Any]] = {}
        for worker_id, render_format, result in results:
            if worker_id not in worker_results:
                worker_results[worker_id] = {}
            worker_results[worker_id][render_format] = result

        assert len(worker_results) == 10

        for worker_id, format_results in worker_results.items():
            assert len(format_results) == 3

            # Check worker ID appears in results
            for render_format, result in format_results.items():
                if render_format == RenderFormat.TAURI:
                    result_dict = cast(dict, result)
                    assert f"Worker {worker_id}" in result_dict["data"]["title"]
                else:
                    assert f"Worker {worker_id}" in str(result)


class TestRendererPerformance:
    """Performance and benchmark tests for renderer system."""

    def setup_method(self) -> None:
        """Setup for performance tests."""
        clear_all_caches()
        self.metric = MetricCardData(
            title="Performance Test",
            value=75.5,
            suffix="%",
        )

    @staticmethod
    def teardown_method() -> None:
        """Cleanup after performance tests."""
        clear_all_caches()

    def test_single_widget_render_performance(self) -> None:
        """Test single widget rendering performance."""

        def render_single() -> object:
            return render_widget(
                WidgetType.METRIC_CARD, cast(Any, self.metric), RenderFormat.TUI
            )

        # Time the operation
        start_time = time.time()
        for _ in range(10):
            result = render_single()
        avg_time = (time.time() - start_time) / 10

        # Verify result
        assert result is not None
        assert "Performance Test" in cast(str, result)

        # Performance assertions (50ms threshold)
        assert (
            avg_time < 0.05
        ), f"Average render time {avg_time:.4f}s exceeds 50ms threshold"

    def test_multi_format_render_performance(self) -> None:
        """Test multi-format rendering performance."""

        def render_all() -> object:
            return render_all_formats(WidgetType.METRIC_CARD, cast(Any, self.metric))

        # Time the operation
        start_time = time.time()
        for _ in range(5):
            results = render_all()
        avg_time = (time.time() - start_time) / 5

        # Verify results
        results_dict = cast(dict, results)
        assert len(results_dict) == 3
        assert all(result is not None for result in results_dict.values())

        # Performance assertions (150ms threshold for 3 formats)
        assert (
            avg_time < 0.15
        ), f"Average multi-format render time {avg_time:.4f}s exceeds 150ms threshold"

    @staticmethod
    def test_batch_rendering_performance() -> None:
        """Test batch rendering performance vs individual rendering."""
        metrics = [
            MetricCardData(title=f"Batch Test {i}", value=i * 10) for i in range(20)
        ]

        renderer = TUIRenderer()
        batch_renderer = BatchRenderer(renderer, max_workers=4)

        # Individual rendering
        start_individual = time.time()
        individual_results = []
        for metric in metrics:
            result = renderer.render_widget(WidgetType.METRIC_CARD, cast(Any, metric))
            individual_results.append(result)
        individual_time = time.time() - start_individual

        # Batch rendering (parallel)
        requests = [
            (WidgetType.METRIC_CARD, cast(Any, metric), cast(dict[str, Any], {}))
            for metric in metrics
        ]

        start_batch = time.time()
        batch_results = batch_renderer.render_batch(cast(Any, requests), parallel=True)
        batch_time = time.time() - start_batch

        # Verify results are equivalent
        assert len(individual_results) == len(batch_results)

        # Batch should be faster or comparable (overhead might make it slower for small sets)
        assert batch_time < individual_time * 2  # Allow some overhead

    def test_caching_performance_improvement(self) -> None:
        """Test that caching significantly improves performance."""
        cache = RenderCache(max_size=100)

        # Create renderer with caching
        renderer = TUIRenderer()
        cached_method = cached_render(cache)(renderer.render_widget)
        cast(Any, renderer).render_widget = cached_method

        # First render (cache miss)
        start1 = time.time()
        result1 = renderer.render_widget(WidgetType.METRIC_CARD, cast(Any, self.metric))
        time1 = time.time() - start1

        # Second render (cache hit)
        start2 = time.time()
        result2 = renderer.render_widget(WidgetType.METRIC_CARD, cast(Any, self.metric))
        time2 = time.time() - start2

        # Results should be identical
        assert result1 == result2

        # Cache hit should be much faster
        assert (
            time2 < time1 * 0.5
        ), f"Cache hit ({time2:.4f}s) not significantly faster than miss ({time1:.4f}s)"

        # Verify cache stats
        stats = cache.get_stats()
        assert stats.hits >= 1
        assert stats.misses >= 1
        assert stats.hit_rate > 0


class TestRendererMemoryStability:
    """Memory usage and stability tests."""

    def setup_method(self) -> None:
        """Setup for memory tests."""
        clear_all_caches()
        gc.collect()
        self.initial_memory = self._get_memory_usage()

    @staticmethod
    def teardown_method() -> None:
        """Cleanup for memory tests."""
        clear_all_caches()
        gc.collect()

    @staticmethod
    def _get_memory_usage() -> object:
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def test_memory_usage_large_dataset(self) -> None:
        """Test memory usage with large datasets."""
        initial_memory = self._get_memory_usage()

        # Create large dataset
        large_sessions = []
        for i in range(1000):
            session = SessionData(
                name=f"session-{i}",
                id=f"id-{i}",
                status=SessionStatus.ACTIVE,
                created_at=datetime.now(UTC),
                windows=[
                    WindowData(
                        id=f"{i}-{j}", name=f"window-{j}", active=j == 0, panes=3
                    )
                    for j in range(5)
                ],
                panes=15,
                claude_active=i % 2 == 0,
            )
            large_sessions.append(session)

        # Render large dataset
        result = render_widget(
            WidgetType.SESSION_BROWSER,
            cast(Any, large_sessions),
            RenderFormat.TAURI,
        )

        # Verify result
        assert result is not None
        assert isinstance(result, dict)
        result_dict = cast(dict, result)
        assert len(result_dict["data"]["sessions"]) == 1000

        # Check memory usage
        peak_memory = self._get_memory_usage()
        memory_increase = cast(float, peak_memory) - cast(float, initial_memory)

        # Memory increase should be reasonable (less than 100MB for this test)
        assert (
            memory_increase < 100
        ), f"Memory increase {memory_increase:.2f}MB too high"

        # Clean up
        del large_sessions
        del result
        gc.collect()

        # Memory should be released
        final_memory = self._get_memory_usage()
        memory_after_cleanup = cast(float, final_memory) - cast(float, initial_memory)

        # Most memory should be released (allow some overhead)
        assert (
            memory_after_cleanup < memory_increase * 0.5
        ), f"Memory not properly released: {memory_after_cleanup:.2f}MB remaining"

    @staticmethod
    def test_cache_memory_limits() -> None:
        """Test that cache respects memory limits."""
        # Create small cache
        cache = RenderCache(max_size=10, ttl=None)

        # Fill cache beyond capacity
        for i in range(20):
            metric = MetricCardData(title=f"Cache Test {i}", value=i)
            cache_key = cast(Any, cache)._generate_cache_key(
                WidgetType.METRIC_CARD, cast(Any, metric), None, RenderFormat.TUI
            )
            cache.set(cache_key, f"result-{i}")

        # Cache should not exceed max size
        assert cache.get_size() <= 10

        # Verify LRU eviction worked
        stats = cache.get_stats()
        assert stats.evictions > 0

    def test_memory_leak_prevention(self) -> None:
        """Test for memory leaks in repeated rendering."""
        initial_memory = self._get_memory_usage()

        # Perform many render operations
        for i in range(100):
            metric = MetricCardData(title=f"Leak Test {i}", value=i)

            # Render with all formats
            results = render_all_formats(WidgetType.METRIC_CARD, cast(Any, metric))

            # Create and use lazy renderer
            lazy_renderer = LazyRenderer(
                TUIRenderer(), WidgetType.METRIC_CARD, cast(Any, metric)
            )
            lazy_result = lazy_renderer.render()

            # Use batch renderer
            batch_renderer = BatchRenderer(WebRenderer())
            batch_results = batch_renderer.render_batch(
                cast(
                    Any,
                    [
                        (
                            WidgetType.METRIC_CARD,
                            cast(Any, metric),
                            cast(dict[str, Any], {}),
                        )
                    ],
                )
            )

            # Clean up explicitly
            del results, lazy_renderer, lazy_result, batch_results

            # Periodic garbage collection
            if i % 10 == 0:
                gc.collect()

        # Final cleanup
        clear_all_caches()
        gc.collect()

        # Check final memory usage
        final_memory = self._get_memory_usage()
        memory_increase = cast(float, final_memory) - cast(float, initial_memory)

        # Memory increase should be minimal (less than 20MB)
        assert (
            memory_increase < 20
        ), f"Potential memory leak detected: {memory_increase:.2f}MB increase"


class TestRendererCompatibility:
    """Compatibility tests for different data formats and edge cases."""

    @staticmethod
    def test_data_format_compatibility() -> None:
        """Test compatibility with different data input formats."""
        # Test with dataclass instance
        metric_dataclass = MetricCardData(title="Dataclass Test", value=100)
        result1 = render_widget(
            WidgetType.METRIC_CARD, metric_dataclass, RenderFormat.TAURI
        )
        assert result1["data"]["title"] == "Dataclass Test"

        # Test with dictionary (if supported)
        metric_dict = {"title": "Dict Test", "value": 100, "suffix": ""}
        try:
            result2 = render_widget(
                WidgetType.METRIC_CARD, metric_dict, RenderFormat.TAURI
            )
            # If supported, should work
            assert result2 is not None
        except (ValueError, TypeError, AttributeError, KeyError):
            # If not supported, that's acceptable
            pass

        # Test with mixed data types
        mixed_table = {
            "headers": ["String", "Number", "Boolean"],
            "rows": [
                ["text", 42, True],
                [None, 0, False],
                ["", -1, None],
            ],
        }

        result3 = render_widget(WidgetType.TABLE, mixed_table, RenderFormat.TAURI)
        assert result3["data"]["headers"] == ["String", "Number", "Boolean"]
        assert len(result3["data"]["rows"]) == 3

    @staticmethod
    def test_unicode_and_special_characters() -> None:
        """Test handling of unicode and special characters."""
        # Unicode characters
        unicode_metric = MetricCardData(
            title="测试 🚀 Тест",
            value=100,
            suffix="‰",
            comparison="vs 上个小时",
        )

        for render_format in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]:
            result = render_widget(
                WidgetType.METRIC_CARD, unicode_metric, render_format
            )
            assert result is not None

            if render_format == RenderFormat.TAURI:
                assert "测试 🚀 Тест" in result["data"]["title"]
            else:
                # String formats should handle unicode
                result_str = str(result)
                assert (
                    "测试" in result_str or "🚀" in result_str or "Тест" in result_str
                )

        # Special HTML/XML characters
        special_chars_metric = MetricCardData(
            title="<script>alert('test')</script>",
            value=100,
            comparison="A & B > C",
        )

        web_result = render_widget(
            WidgetType.METRIC_CARD, special_chars_metric, RenderFormat.WEB
        )
        # Web format should escape dangerous characters
        assert "<script>" not in web_result or "&lt;script&gt;" in web_result

    @staticmethod
    def test_timezone_and_datetime_handling() -> None:
        """Test handling of different datetime formats and timezones."""
        # Different datetime objects
        now = datetime.now(UTC)

        session_with_times = SessionData(
            name="time-test",
            id="time-123",
            status=SessionStatus.ACTIVE,
            created_at=now,
            last_activity=now,
            windows=[],
        )

        for render_format in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]:
            result = render_widget(
                WidgetType.SESSION_BROWSER, [session_with_times], render_format
            )
            assert result is not None

            if render_format == RenderFormat.TAURI:
                session_data = result["data"]["sessions"][0]
                assert "created_at" in session_data
                # Should be ISO format string
                assert isinstance(session_data["created_at"], str)

    @staticmethod
    def test_empty_and_null_data_handling() -> None:
        """Test handling of empty and null data."""
        empty_data_tests = [
            # Empty strings
            (WidgetType.METRIC_CARD, MetricCardData(title="", value=0)),
            # Zero values
            (
                WidgetType.METRIC_CARD,
                MetricCardData(title="Zero Test", value=0, trend=0),
            ),
            # None values where allowed
            (
                WidgetType.METRIC_CARD,
                MetricCardData(title="None Test", value=100, trend=None),
            ),
            # Empty collections
            (WidgetType.SESSION_BROWSER, []),
            (WidgetType.TABLE, {"headers": [], "rows": []}),
            (WidgetType.LOG_VIEWER, {"logs": []}),
        ]

        for widget_type, data in empty_data_tests:
            for render_format in [
                RenderFormat.TUI,
                RenderFormat.WEB,
                RenderFormat.TAURI,
            ]:
                try:
                    result = render_widget(widget_type, data, render_format)
                    assert result is not None

                    # Should produce valid output even with empty data
                    if render_format == RenderFormat.TAURI:
                        assert isinstance(result, dict)
                        assert "data" in result
                    else:
                        assert isinstance(result, str)
                        assert len(result) > 0

                except (ValueError, TypeError, AttributeError, KeyError) as e:
                    # Some empty data might be invalid, that's acceptable
                    assert "invalid" in str(e).lower() or "error" in str(e).lower()


# Mark performance tests to run separately if needed
pytest.mark.performance = pytest.mark.skipif(False, reason="Performance tests")
