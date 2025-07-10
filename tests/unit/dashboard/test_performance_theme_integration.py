import pytest
from libs.dashboard import PerformanceOptimizer, ThemeManager, OptimizationLevel

class TestPerformanceThemeIntegration:
    """Tests for performance optimization affecting theme rendering"""

    @pytest.fixture
    def performance_optimizer(self):
        """Create PerformanceOptimizer instance"""
        optimizer = PerformanceOptimizer()
        yield optimizer
        # Cleanup
        if optimizer.monitoring:
            optimizer.stop_monitoring()

    @pytest.fixture
    def theme_manager(self):
        """Create ThemeManager instance"""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ThemeManager(config_dir=Path(temp_dir))

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
