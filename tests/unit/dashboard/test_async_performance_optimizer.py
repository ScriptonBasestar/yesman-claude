# Copyright notice.

import asyncio
import pytest
from libs.dashboard.performance_optimizer import AsyncPerformanceOptimizer

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


class TestAsyncPerformanceOptimizer:
    """Tests for async performance optimizer."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_async_performance_optimizer() -> None:
        """Test 17: Async performance optimizer."""
        async_optimizer = AsyncPerformanceOptimizer(monitoring_interval=0.1)

        # Start monitoring
        started = await async_optimizer.start_monitoring()
        assert started is True

        # Let it run briefly
        await asyncio.sleep(0.3)

        # Get performance report
        report = await async_optimizer.get_performance_report()
        assert isinstance(report, dict)
        assert "current" in report

        # Stop monitoring
        stopped = await async_optimizer.stop_monitoring()
        assert stopped is True
