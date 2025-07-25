# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

import tempfile
from pathlib import Path

import pytest

from libs.dashboard import OptimizationLevel, PerformanceOptimizer, ThemeManager

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


class TestPerformanceThemeIntegration:
    """Tests for performance optimization affecting theme rendering."""

    @pytest.fixture
    @staticmethod
    def performance_optimizer() -> object:
        """Create PerformanceOptimizer instance.

        Yields:
            PerformanceOptimizer: Configured performance optimizer instance.
        """
        optimizer = PerformanceOptimizer()
        yield optimizer
        # Cleanup
        if optimizer.monitoring:
            optimizer.stop_monitoring()

    @pytest.fixture
    @staticmethod
    def theme_manager() -> object:
        """Create ThemeManager instance.

        Yields:
            ThemeManager: Configured theme manager instance.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ThemeManager(config_dir=Path(temp_dir))

    @staticmethod
    def test_performance_theme_integration(
        performance_optimizer: object, theme_manager: object
    ) -> None:
        """Test 9: Performance optimization affects theme rendering."""
        # Set aggressive optimization
        performance_optimizer.set_optimization_level(OptimizationLevel.AGGRESSIVE)

        # Verify optimization applied
        assert (
            performance_optimizer.current_optimization_level
            == OptimizationLevel.AGGRESSIVE
        )
        assert "animations" in performance_optimizer.applied_optimizations

        # Test theme rendering still works
        css = theme_manager.export_css()
        assert css is not None
        assert len(css) > 0
