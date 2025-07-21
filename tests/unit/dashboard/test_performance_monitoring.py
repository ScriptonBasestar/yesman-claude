"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

import time

import pytest
from typing import object

from libs.dashboard import OptimizationLevel, PerformanceOptimizer


class TestPerformanceMonitoring:
    """Tests for performance monitoring and optimization."""

    @pytest.fixture
    @staticmethod
    def performance_optimizer():
        """Create PerformanceOptimizer instance."""
        optimizer = PerformanceOptimizer()
        yield optimizer
        # Cleanup
        if optimizer.monitoring:
            optimizer.stop_monitoring()

    @staticmethod
    def test_performance_monitoring( performance_optimizer: object) -> None:
        """Test 5: Performance monitoring and optimization."""
        # Test metrics collection
        metrics = performance_optimizer._collect_metrics()
        assert metrics is not None
        assert hasattr(metrics, "cpu_usage")
        assert hasattr(metrics, "memory_usage")

        # Test profiler
        profiler = performance_optimizer.profiler

        with profiler.measure("test_operation"):
            time.sleep(0.01)  # 10ms operation

        stats = profiler.get_stats("test_operation")
        assert stats["count"] == 1
        assert stats["avg"] > 0

        # Test optimization strategies
        strategies = performance_optimizer.optimization_strategies
        assert len(strategies) == 5  # None, Low, Medium, High, Aggressive

        # Test optimization application
        performance_optimizer.set_optimization_level(OptimizationLevel.MEDIUM)
        assert performance_optimizer.current_optimization_level == OptimizationLevel.MEDIUM

        # Test performance report
        report = performance_optimizer.get_performance_report()
        assert isinstance(report, dict)
        assert "current" in report
        assert "optimization" in report
        assert "recommendations" in report
