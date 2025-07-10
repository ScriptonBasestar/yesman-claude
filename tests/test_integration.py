"""
Integration Tests for Dashboard System

Comprehensive integration tests covering all dashboard components
including interfaces, rendering, themes, navigation, and performance.
"""

import asyncio
import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Dashboard imports
from libs.dashboard import (
    DashboardLauncher, TUIDashboard, ThemeManager, KeyboardNavigationManager,
    PerformanceOptimizer, ThemeMode, OptimizationLevel, NavigationContext
)
from libs.dashboard.renderers import (
    TUIRenderer, WebRenderer, TauriRenderer, RendererFactory, 
    RenderFormat, WidgetType
)
from libs.dashboard.renderers.widget_models import (
    SessionData, HealthData, ActivityData, SessionStatus, HealthLevel
)


class TestDashboardIntegration:
    """Comprehensive integration tests for dashboard system"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create temporary project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create tauri-dashboard directory with package.json
            tauri_dir = project_root / "tauri-dashboard"
            tauri_dir.mkdir()
            (tauri_dir / "package.json").write_text('{"name": "test-dashboard"}')
            
            yield project_root
    
    @pytest.fixture
    def launcher(self, temp_project_root):
        """Create DashboardLauncher with temp project root"""
        return DashboardLauncher(project_root=temp_project_root)
    
    @pytest.fixture
    def theme_manager(self):
        """Create ThemeManager instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ThemeManager(config_dir=Path(temp_dir))
    
    @pytest.fixture
    def keyboard_manager(self):
        """Create KeyboardNavigationManager instance"""
        manager = KeyboardNavigationManager()
        yield manager
        # Cleanup
        manager.actions.clear()
        manager.bindings.clear()
    
    @pytest.fixture
    def performance_optimizer(self):
        """Create PerformanceOptimizer instance"""
        optimizer = PerformanceOptimizer()
        yield optimizer
        # Cleanup
        if optimizer.monitoring:
            optimizer.stop_monitoring()
    
    def test_interface_detection(self, launcher):
        """Test 1: Interface detection and availability checking"""
        # Test auto-detection
        best_interface = launcher.detect_best_interface()
        assert best_interface in ['tui', 'web', 'tauri']
        
        # Test interface availability
        interfaces = launcher.get_available_interfaces()
        assert len(interfaces) == 3
        assert 'tui' in interfaces
        assert 'web' in interfaces
        assert 'tauri' in interfaces
        
        # Test TUI always available
        assert interfaces['tui'].available is True
        
        # Test system requirements
        requirements = launcher.check_system_requirements()
        assert 'tui' in requirements
        assert 'web' in requirements
        assert 'tauri' in requirements
    
    def test_multi_format_rendering(self):
        """Test 2: Multi-format rendering across all interfaces"""
        factory = RendererFactory()
        
        # Test data
        session_data = SessionData(
            name="test-session",
            status=SessionStatus.ACTIVE,
            uptime=3600,
            windows=2
        )
        
        health_data = HealthData(
            overall_score=85,
            overall_level=HealthLevel.GOOD,
            categories={"build": 90, "tests": 80}
        )
        
        # Test all formats
        formats = [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]
        widgets = [WidgetType.SESSION_BROWSER, WidgetType.PROJECT_HEALTH]
        
        for format_type in formats:
            renderer = factory.create_renderer(format_type)
            assert renderer is not None
            
            for widget_type in widgets:
                if widget_type == WidgetType.SESSION_BROWSER:
                    result = renderer.render_widget(widget_type, [session_data])
                else:
                    result = renderer.render_widget(widget_type, health_data)
                
                assert result is not None
                assert isinstance(result, dict)
                assert 'content' in result or 'data' in result
    
    def test_theme_switching(self, theme_manager):
        """Test 3: Theme switching and CSS generation"""
        # Test built-in themes
        themes = theme_manager.get_all_themes()
        assert len(themes) >= 3
        
        # Test theme switching
        assert theme_manager.set_theme("default_dark") is True
        assert theme_manager.current_theme.name == "Default Dark"
        
        assert theme_manager.set_mode(ThemeMode.LIGHT) is True
        assert theme_manager.current_theme.name == "Default Light"
        
        # Test CSS export
        css = theme_manager.export_css()
        assert ":root {" in css
        assert "--color-primary:" in css
        assert "--font-family-primary:" in css
        
        # Test Rich theme export
        rich_theme = theme_manager.export_rich_theme()
        assert isinstance(rich_theme, dict)
        assert "primary" in rich_theme
        assert "background" in rich_theme
        
        # Test Textual CSS export
        textual_css = theme_manager.export_textual_css()
        assert "App {" in textual_css
        assert "background:" in textual_css
    
    def test_keyboard_navigation(self, keyboard_manager):
        """Test 4: Keyboard navigation system"""
        # Test action registration
        test_called = False
        
        def test_action():
            nonlocal test_called
            test_called = True
        
        keyboard_manager.register_action("test_action", test_action)
        assert "test_action" in keyboard_manager.actions
        
        # Test key binding
        from libs.dashboard.keyboard_navigation import KeyModifier
        keyboard_manager.register_binding(
            "t", [KeyModifier.CTRL], "test_action", "Test action"
        )
        
        # Test key event handling
        handled = keyboard_manager.handle_key_event("t", [KeyModifier.CTRL])
        assert handled is True
        assert test_called is True
        
        # Test focus management
        keyboard_manager.add_focusable_element("element1", "button", 0)
        keyboard_manager.add_focusable_element("element2", "input", 1)
        
        assert len(keyboard_manager.focusable_elements) == 2
        
        # Test context switching
        keyboard_manager.set_context(NavigationContext.DASHBOARD)
        assert keyboard_manager.current_context == NavigationContext.DASHBOARD
    
    def test_performance_monitoring(self, performance_optimizer):
        """Test 5: Performance monitoring and optimization"""
        # Test metrics collection
        metrics = performance_optimizer._collect_metrics()
        assert metrics is not None
        assert hasattr(metrics, 'cpu_usage')
        assert hasattr(metrics, 'memory_usage')
        
        # Test profiler
        profiler = performance_optimizer.profiler
        
        with profiler.measure("test_operation"):
            time.sleep(0.01)  # 10ms operation
        
        stats = profiler.get_stats("test_operation")
        assert stats['count'] == 1
        assert stats['avg'] > 0
        
        # Test optimization strategies
        strategies = performance_optimizer.optimization_strategies
        assert len(strategies) == 5  # None, Low, Medium, High, Aggressive
        
        # Test optimization application
        performance_optimizer.set_optimization_level(OptimizationLevel.MEDIUM)
        assert performance_optimizer.current_optimization_level == OptimizationLevel.MEDIUM
        
        # Test performance report
        report = performance_optimizer.get_performance_report()
        assert isinstance(report, dict)
        assert 'current' in report
        assert 'optimization' in report
        assert 'recommendations' in report
    
    def test_end_to_end_dashboard_launch(self, launcher, temp_project_root):
        """Test 6: End-to-end dashboard launch process"""
        # 1. Interface detection
        interface = launcher.detect_best_interface()
        assert interface in ['tui', 'web', 'tauri']
        
        # 2. Check dependencies
        requirements = launcher.check_system_requirements()
        assert interface in requirements
        
        # 3. Get interface info
        interface_info = launcher.get_interface_info(interface)
        assert interface_info is not None
        assert interface_info.name
        assert interface_info.description
        
        # 4. Verify interface can be created
        if interface == 'tui':
            # TUI should always work
            assert interface_info.available is True
        elif interface == 'tauri':
            # Tauri depends on directory structure
            expected_available = (temp_project_root / "tauri-dashboard").exists()
            assert interface_info.available == expected_available
    
    @pytest.mark.asyncio
    async def test_concurrent_rendering(self):
        """Test 7: Concurrent rendering operations"""
        factory = RendererFactory()
        
        # Test data
        session_data = SessionData(
            name="concurrent-session",
            status=SessionStatus.ACTIVE,
            uptime=1800
        )
        
        async def render_widget_async(format_type, widget_type, data):
            """Async wrapper for rendering"""
            renderer = factory.create_renderer(format_type)
            return renderer.render_widget(widget_type, data)
        
        # Create multiple concurrent rendering tasks
        tasks = []
        for i in range(10):
            for format_type in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]:
                task = render_widget_async(
                    format_type, 
                    WidgetType.SESSION_BROWSER, 
                    [session_data]
                )
                tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all rendered successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None
            assert isinstance(result, dict)
    
    def test_theme_renderer_integration(self, theme_manager):
        """Test 8: Theme and renderer integration"""
        factory = RendererFactory()
        
        # Test theme switching affects renderers
        theme_manager.set_mode(ThemeMode.DARK)
        dark_theme = theme_manager.current_theme
        
        # Create renderer with dark theme
        renderer = factory.create_renderer(RenderFormat.TUI, theme=dark_theme.colors.to_dict())
        
        # Test rendering with theme
        health_data = HealthData(
            overall_score=75,
            overall_level=HealthLevel.GOOD,
            categories={"security": 80}
        )
        
        result = renderer.render_widget(WidgetType.PROJECT_HEALTH, health_data)
        assert result is not None
        
        # Switch to light theme
        theme_manager.set_mode(ThemeMode.LIGHT)
        light_theme = theme_manager.current_theme
        
        # Verify theme changed
        assert light_theme.name != dark_theme.name
    
    def test_performance_theme_integration(self, performance_optimizer, theme_manager):
        """Test 9: Performance optimization affects theme rendering"""
        # Set aggressive optimization
        performance_optimizer.set_optimization_level(OptimizationLevel.AGGRESSIVE)
        
        # Verify optimization applied
        assert performance_optimizer.current_optimization_level == OptimizationLevel.AGGRESSIVE
        assert "animations" in performance_optimizer.applied_optimizations
        
        # Test theme rendering still works
        css = theme_manager.export_css()
        assert css is not None
        assert len(css) > 0
    
    def test_keyboard_theme_integration(self, keyboard_manager, theme_manager):
        """Test 10: Keyboard navigation with theme switching"""
        # Register theme switching action
        def switch_to_dark():
            theme_manager.set_mode(ThemeMode.DARK)
        
        keyboard_manager.register_action("switch_theme_dark", switch_to_dark)
        
        from libs.dashboard.keyboard_navigation import KeyModifier
        keyboard_manager.register_binding(
            "d", [KeyModifier.CTRL], "switch_theme_dark", "Switch to dark theme"
        )
        
        # Test theme switching via keyboard
        initial_theme = theme_manager.current_theme.name
        keyboard_manager.handle_key_event("d", [KeyModifier.CTRL])
        
        # Verify theme changed
        assert theme_manager.current_theme.name != initial_theme
        assert theme_manager.current_theme.mode == ThemeMode.DARK
    
    def test_factory_integration(self):
        """Test 11: Renderer factory with all formats"""
        factory = RendererFactory()
        
        # Test factory creates all renderer types
        tui_renderer = factory.create_renderer(RenderFormat.TUI)
        web_renderer = factory.create_renderer(RenderFormat.WEB)
        tauri_renderer = factory.create_renderer(RenderFormat.TAURI)
        
        assert tui_renderer is not None
        assert web_renderer is not None
        assert tauri_renderer is not None
        
        # Test batch rendering
        data = HealthData(overall_score=90, overall_level=HealthLevel.EXCELLENT)
        
        results = factory.render_all_formats(WidgetType.PROJECT_HEALTH, data)
        assert len(results) == 3
        assert RenderFormat.TUI in results
        assert RenderFormat.WEB in results
        assert RenderFormat.TAURI in results
    
    def test_cache_integration(self):
        """Test 12: Cache integration across components"""
        from libs.dashboard.renderers.optimizations import RenderCache
        
        cache = RenderCache(max_size=100, ttl=60.0)
        
        # Test cache with different data
        test_data = {"test": "data"}
        cache_key = "test_key"
        
        # Cache miss
        result = cache.get(cache_key)
        assert result is None
        
        # Cache set
        cache.set(cache_key, test_data)
        
        # Cache hit
        result = cache.get(cache_key)
        assert result == test_data
        
        # Test cache stats
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
    
    def test_error_handling_integration(self):
        """Test 13: Error handling across components"""
        factory = RendererFactory()
        
        # Test invalid widget type
        renderer = factory.create_renderer(RenderFormat.TUI)
        
        # This should handle gracefully
        try:
            result = renderer.render_widget(WidgetType.SESSION_BROWSER, None)
            # Should return some error indication or empty result
            assert result is not None
        except Exception as e:
            # If exception is raised, it should be a known type
            assert isinstance(e, (ValueError, TypeError))
    
    def test_memory_stability(self):
        """Test 14: Memory stability during intensive operations"""
        import gc
        
        factory = RendererFactory()
        initial_objects = len(gc.get_objects())
        
        # Perform many rendering operations
        for i in range(100):
            renderer = factory.create_renderer(RenderFormat.TUI)
            data = SessionData(
                name=f"session-{i}",
                status=SessionStatus.ACTIVE,
                uptime=i * 10
            )
            result = renderer.render_widget(WidgetType.SESSION_BROWSER, [data])
            assert result is not None
        
        # Force garbage collection
        gc.collect()
        
        # Check for memory leaks (allow some growth but not excessive)
        final_objects = len(gc.get_objects())
        growth = final_objects - initial_objects
        
        # Allow up to 50% growth (this is quite generous)
        assert growth < initial_objects * 0.5
    
    def test_thread_safety(self):
        """Test 15: Thread safety of components"""
        factory = RendererFactory()
        results = []
        errors = []
        
        def render_in_thread(thread_id):
            try:
                renderer = factory.create_renderer(RenderFormat.TUI)
                data = SessionData(
                    name=f"thread-{thread_id}",
                    status=SessionStatus.ACTIVE,
                    uptime=thread_id * 100
                )
                result = renderer.render_widget(WidgetType.SESSION_BROWSER, [data])
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=render_in_thread, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 10
        
        # Verify all results are valid
        for thread_id, result in results:
            assert result is not None
            assert isinstance(result, dict)
    
    def test_performance_benchmark(self):
        """Test 16: Basic performance benchmark"""
        factory = RendererFactory()
        renderer = factory.create_renderer(RenderFormat.TUI)
        
        # Prepare test data
        sessions = []
        for i in range(100):
            sessions.append(SessionData(
                name=f"benchmark-session-{i}",
                status=SessionStatus.ACTIVE,
                uptime=i * 60
            ))
        
        # Measure rendering time
        start_time = time.perf_counter()
        
        result = renderer.render_widget(WidgetType.SESSION_BROWSER, sessions)
        
        end_time = time.perf_counter()
        render_time = end_time - start_time
        
        # Verify result
        assert result is not None
        
        # Performance target: 100 sessions should render within 50ms
        assert render_time < 0.05, f"Rendering took {render_time:.3f}s, expected < 0.05s"
    
    @pytest.mark.asyncio
    async def test_async_performance_optimizer(self):
        """Test 17: Async performance optimizer"""
        from libs.dashboard.performance_optimizer import AsyncPerformanceOptimizer
        
        async_optimizer = AsyncPerformanceOptimizer(monitoring_interval=0.1)
        
        # Start monitoring
        started = await async_optimizer.start_monitoring()
        assert started is True
        
        # Let it run briefly
        await asyncio.sleep(0.3)
        
        # Get performance report
        report = await async_optimizer.get_performance_report()
        assert isinstance(report, dict)
        assert 'current' in report
        
        # Stop monitoring
        stopped = await async_optimizer.stop_monitoring()
        assert stopped is True


class TestSystemCompatibility:
    """Test system compatibility and edge cases"""
    
    def test_missing_dependencies(self):
        """Test behavior with missing optional dependencies"""
        # This would test graceful degradation when optional deps are missing
        # For now, we just verify core functionality works
        factory = RendererFactory()
        renderer = factory.create_renderer(RenderFormat.TUI)
        assert renderer is not None
    
    @pytest.mark.skipif(not os.path.exists("/proc"), reason="Linux-specific test")
    def test_linux_specific_features(self):
        """Test Linux-specific functionality"""
        from libs.dashboard.theme_system import SystemThemeDetector
        
        # This should not crash on Linux
        theme_mode = SystemThemeDetector.get_system_theme()
        assert theme_mode is not None
    
    def test_configuration_isolation(self):
        """Test configuration isolation between instances"""
        with tempfile.TemporaryDirectory() as temp_dir1, \
             tempfile.TemporaryDirectory() as temp_dir2:
            
            theme_manager1 = ThemeManager(config_dir=Path(temp_dir1))
            theme_manager2 = ThemeManager(config_dir=Path(temp_dir2))
            
            # Create custom theme in first manager
            from libs.dashboard.theme_system import Theme, ThemeMode, ColorPalette
            custom_theme = Theme(
                name="Custom Test",
                mode=ThemeMode.CUSTOM,
                colors=ColorPalette(primary="#ff0000")
            )
            
            theme_manager1.save_theme("custom", custom_theme)
            
            # Verify isolation
            theme1_themes = theme_manager1.get_all_themes()
            theme2_themes = theme_manager2.get_all_themes()
            
            assert "custom" in theme1_themes
            assert "custom" not in theme2_themes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])