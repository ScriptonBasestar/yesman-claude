"""
Tests for Renderer Factory
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest

from libs.dashboard.renderers.base_renderer import (
    BaseRenderer,
    RenderFormat,
    WidgetType,
)
from libs.dashboard.renderers.renderer_factory import (
    RendererFactory,
    RendererFactoryError,
    UnsupportedFormatError,
    create_renderer,
    get_renderer,
    render_all_formats,
    render_formats,
    render_widget,
)
from libs.dashboard.renderers.tauri_renderer import TauriRenderer
from libs.dashboard.renderers.tui_renderer import TUIRenderer
from libs.dashboard.renderers.web_renderer import WebRenderer
from libs.dashboard.renderers.widget_models import (
    MetricCardData,
    SessionData,
    SessionStatus,
    WindowData,
)


class MockRenderer(BaseRenderer):
    """Mock renderer for testing"""

    def __init__(self, should_fail=False):
        super().__init__(RenderFormat.TUI)
        self.should_fail = should_fail
        self.render_count = 0

    def render_widget(self, widget_type, data, options=None):
        self.render_count += 1
        if self.should_fail:
            raise Exception("Mock render failure")
        return f"mock-{widget_type.value}-{self.render_count}"

    def render_layout(self, widgets, layout_config=None):
        return f"mock-layout-{len(widgets)}"

    def render_container(self, content, container_config=None):
        return f"mock-container-{type(content).__name__}"

    def supports_feature(self, feature):
        return feature == "mock"


class TestRendererFactory:
    """Test cases for RendererFactory"""

    def setup_method(self):
        """Setup for each test"""
        # Reset factory state
        RendererFactory.reset()

    def teardown_method(self):
        """Cleanup after each test"""
        RendererFactory.reset()

    def test_factory_initialization(self):
        """Test factory initialization"""
        assert not RendererFactory._initialized

        RendererFactory.initialize()

        assert RendererFactory._initialized
        assert len(RendererFactory._renderer_classes) == 3
        assert RenderFormat.TUI in RendererFactory._renderer_classes
        assert RenderFormat.WEB in RendererFactory._renderer_classes
        assert RenderFormat.TAURI in RendererFactory._renderer_classes

    def test_double_initialization(self):
        """Test that double initialization is safe"""
        RendererFactory.initialize()
        RendererFactory.initialize()  # Should not raise

        assert RendererFactory._initialized

    def test_supported_formats(self):
        """Test getting supported formats"""
        formats = RendererFactory.get_supported_formats()

        assert len(formats) == 3
        assert RenderFormat.TUI in formats
        assert RenderFormat.WEB in formats
        assert RenderFormat.TAURI in formats

    def test_format_support_check(self):
        """Test checking if format is supported"""
        assert RendererFactory.is_format_supported(RenderFormat.TUI)
        assert RendererFactory.is_format_supported(RenderFormat.WEB)
        assert RendererFactory.is_format_supported(RenderFormat.TAURI)

    def test_create_renderer(self):
        """Test creating renderer instances"""
        tui_renderer = RendererFactory.create(RenderFormat.TUI)
        web_renderer = RendererFactory.create(RenderFormat.WEB)
        tauri_renderer = RendererFactory.create(RenderFormat.TAURI)

        assert isinstance(tui_renderer, TUIRenderer)
        assert isinstance(web_renderer, WebRenderer)
        assert isinstance(tauri_renderer, TauriRenderer)

        # Each call should create new instance
        tui_renderer2 = RendererFactory.create(RenderFormat.TUI)
        assert tui_renderer is not tui_renderer2

    def test_create_unsupported_format(self):
        """Test creating renderer with unsupported format"""
        # Create fake enum value
        fake_format = type("FakeFormat", (), {"value": "fake"})()

        with pytest.raises(UnsupportedFormatError):
            RendererFactory.create(fake_format)

    def test_singleton_renderer(self):
        """Test singleton renderer instances"""
        renderer1 = RendererFactory.get_singleton(RenderFormat.TUI)
        renderer2 = RendererFactory.get_singleton(RenderFormat.TUI)

        assert renderer1 is renderer2
        assert isinstance(renderer1, TUIRenderer)

        # Different format should return different instance
        web_renderer = RendererFactory.get_singleton(RenderFormat.WEB)
        assert web_renderer is not renderer1
        assert isinstance(web_renderer, WebRenderer)

    def test_register_custom_renderer(self):
        """Test registering custom renderer"""
        # Create fake format
        custom_format = type("CustomFormat", (), {"value": "custom"})()

        RendererFactory.register_renderer(custom_format, MockRenderer)

        assert custom_format in RendererFactory._renderer_classes
        assert RendererFactory.is_format_supported(custom_format)

        # Should be able to create instance
        renderer = RendererFactory.create(custom_format)
        assert isinstance(renderer, MockRenderer)

    def test_render_universal_single_format(self):
        """Test universal rendering with single format"""
        metric = MetricCardData(title="Test", value=100)

        result = RendererFactory.render_universal(
            WidgetType.METRIC_CARD,
            metric,
            RenderFormat.TUI,
        )

        assert isinstance(result, str)  # TUI returns string
        assert "Test" in result

    def test_render_universal_all_formats(self):
        """Test universal rendering with all formats"""
        metric = MetricCardData(title="Test", value=100)

        results = RendererFactory.render_universal(
            WidgetType.METRIC_CARD,
            metric,
        )

        assert isinstance(results, dict)
        assert len(results) == 3
        assert RenderFormat.TUI in results
        assert RenderFormat.WEB in results
        assert RenderFormat.TAURI in results

        # Each should have different format output
        assert isinstance(results[RenderFormat.TUI], str)
        assert isinstance(results[RenderFormat.WEB], str)
        assert isinstance(results[RenderFormat.TAURI], dict)

    def test_render_parallel(self):
        """Test parallel rendering"""
        metric = MetricCardData(title="Test", value=100)

        results = RendererFactory.render_parallel(
            WidgetType.METRIC_CARD,
            metric,
            max_workers=2,
        )

        assert isinstance(results, dict)
        assert len(results) == 3
        assert RenderFormat.TUI in results
        assert RenderFormat.WEB in results
        assert RenderFormat.TAURI in results

    def test_render_parallel_specific_formats(self):
        """Test parallel rendering with specific formats"""
        metric = MetricCardData(title="Test", value=100)
        formats = [RenderFormat.TUI, RenderFormat.WEB]

        results = RendererFactory.render_parallel(
            WidgetType.METRIC_CARD,
            metric,
            formats=formats,
        )

        assert len(results) == 2
        assert RenderFormat.TUI in results
        assert RenderFormat.WEB in results
        assert RenderFormat.TAURI not in results

    def test_thread_safety(self):
        """Test thread safety of factory operations"""
        results = []
        errors = []

        def create_and_render():
            try:
                renderer = RendererFactory.get_singleton(RenderFormat.TUI)
                metric = MetricCardData(title="Thread Test", value=123)
                result = renderer.render_widget(WidgetType.METRIC_CARD, metric)
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_and_render)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert len(results) == 10

        # All should have used same singleton instance
        assert all("Thread Test" in result for result in results)

    def test_error_handling_render_failure(self):
        """Test error handling when rendering fails"""
        # Register failing renderer
        failing_format = type("FailingFormat", (), {"value": "failing"})()
        RendererFactory.register_renderer(failing_format, lambda: MockRenderer(should_fail=True))

        with pytest.raises(RendererFactoryError):
            RendererFactory.render_universal(
                WidgetType.METRIC_CARD,
                MetricCardData(title="Test", value=100),
                failing_format,
            )

    def test_error_handling_all_formats_fail(self):
        """Test error handling when all formats fail"""
        # Replace all renderers with failing ones
        original_classes = RendererFactory._renderer_classes.copy()

        try:
            RendererFactory._renderer_classes = {fmt: lambda: MockRenderer(should_fail=True) for fmt in original_classes.keys()}
            RendererFactory.clear_instances()

            with pytest.raises(RendererFactoryError):
                RendererFactory.render_universal(
                    WidgetType.METRIC_CARD,
                    MetricCardData(title="Test", value=100),
                )
        finally:
            RendererFactory._renderer_classes = original_classes

    def test_clear_instances(self):
        """Test clearing singleton instances"""
        renderer1 = RendererFactory.get_singleton(RenderFormat.TUI)
        assert len(RendererFactory._instances) == 1

        RendererFactory.clear_instances()
        assert len(RendererFactory._instances) == 0

        renderer2 = RendererFactory.get_singleton(RenderFormat.TUI)
        assert renderer1 is not renderer2

    def test_reset_factory(self):
        """Test resetting factory state"""
        RendererFactory.initialize()
        RendererFactory.get_singleton(RenderFormat.TUI)

        assert RendererFactory._initialized
        assert len(RendererFactory._instances) > 0

        RendererFactory.reset()

        assert not RendererFactory._initialized
        assert len(RendererFactory._instances) == 0


class TestConvenienceFunctions:
    """Test convenience functions"""

    def setup_method(self):
        """Setup for each test"""
        RendererFactory.reset()

    def teardown_method(self):
        """Cleanup after each test"""
        RendererFactory.reset()

    def test_render_widget_function(self):
        """Test render_widget convenience function"""
        metric = MetricCardData(title="Test", value=100)

        result = render_widget(
            WidgetType.METRIC_CARD,
            metric,
            RenderFormat.TUI,
        )

        assert isinstance(result, str)
        assert "Test" in result

    def test_render_all_formats_function(self):
        """Test render_all_formats convenience function"""
        metric = MetricCardData(title="Test", value=100)

        results = render_all_formats(WidgetType.METRIC_CARD, metric)

        assert isinstance(results, dict)
        assert len(results) == 3
        assert all(fmt in results for fmt in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI])

    def test_render_formats_function(self):
        """Test render_formats convenience function"""
        metric = MetricCardData(title="Test", value=100)
        formats = [RenderFormat.TUI, RenderFormat.WEB]

        # Sequential rendering
        results_seq = render_formats(WidgetType.METRIC_CARD, metric, formats)
        assert len(results_seq) == 2

        # Parallel rendering
        results_par = render_formats(WidgetType.METRIC_CARD, metric, formats, parallel=True)
        assert len(results_par) == 2

    def test_create_renderer_function(self):
        """Test create_renderer convenience function"""
        renderer = create_renderer(RenderFormat.TUI)

        assert isinstance(renderer, TUIRenderer)

    def test_get_renderer_function(self):
        """Test get_renderer convenience function"""
        renderer1 = get_renderer(RenderFormat.TUI)
        renderer2 = get_renderer(RenderFormat.TUI)

        assert renderer1 is renderer2
        assert isinstance(renderer1, TUIRenderer)


class TestRendererFactoryIntegration:
    """Integration tests for RendererFactory"""

    def setup_method(self):
        """Setup for each test"""
        RendererFactory.reset()

    def teardown_method(self):
        """Cleanup after each test"""
        RendererFactory.reset()

    def test_full_workflow(self):
        """Test complete rendering workflow"""
        # Create sample data
        session = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(),
            windows=[WindowData(id="1", name="window", active=True, panes=2)],
        )

        # Test factory creation and rendering
        factory_result = RendererFactory.render_universal(
            WidgetType.SESSION_BROWSER,
            [session],
            RenderFormat.TAURI,
        )

        # Test convenience function
        convenience_result = render_widget(
            WidgetType.SESSION_BROWSER,
            [session],
            RenderFormat.TAURI,
        )

        # Results should be equivalent
        assert factory_result == convenience_result
        assert isinstance(factory_result, dict)
        assert "data" in factory_result
        assert "sessions" in factory_result["data"]
        assert factory_result["data"]["sessions"][0]["name"] == "test-session"

    def test_multiple_widget_rendering(self):
        """Test rendering multiple different widgets"""
        session = SessionData(
            name="test-session",
            id="session-123",
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(),
            windows=[],
        )

        metric = MetricCardData(title="CPU Usage", value=75.5, suffix="%")

        # Render different widgets
        session_results = render_all_formats(WidgetType.SESSION_BROWSER, [session])
        metric_results = render_all_formats(WidgetType.METRIC_CARD, metric)

        # Check all formats work for both widgets
        assert len(session_results) == 3
        assert len(metric_results) == 3

        for fmt in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]:
            assert fmt in session_results
            assert fmt in metric_results

    def test_performance_comparison(self):
        """Test performance between sequential and parallel rendering"""
        metric = MetricCardData(title="Performance Test", value=100)
        formats = list(RendererFactory.get_supported_formats())

        # Sequential timing
        start_seq = time.time()
        results_seq = render_formats(WidgetType.METRIC_CARD, metric, formats, parallel=False)
        time_seq = time.time() - start_seq

        # Parallel timing
        start_par = time.time()
        results_par = render_formats(WidgetType.METRIC_CARD, metric, formats, parallel=True)
        time_par = time.time() - start_par

        # Results should be equivalent
        assert len(results_seq) == len(results_par)
        assert set(results_seq.keys()) == set(results_par.keys())

        # Both should complete successfully
        assert all(result is not None for result in results_seq.values())
        assert all(result is not None for result in results_par.values())

    def test_stress_testing(self):
        """Test factory under stress conditions"""
        metrics = [MetricCardData(title=f"Metric {i}", value=i * 10) for i in range(50)]

        results = []
        errors = []

        def render_metric(i):
            try:
                result = render_widget(
                    WidgetType.METRIC_CARD,
                    metrics[i],
                    RenderFormat.TUI,
                )
                return i, result
            except Exception as e:
                return i, str(e)

        # Render many widgets concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(render_metric, i) for i in range(50)]

            for future in futures:
                i, result = future.result()
                if isinstance(result, str) and "error" not in result.lower():
                    results.append((i, result))
                else:
                    errors.append((i, result))

        # Most should succeed
        assert len(results) >= 45  # Allow some failures under stress
        assert len(errors) <= 5

        # Check results contain expected content
        for i, result in results:
            assert f"Metric {i}" in result
