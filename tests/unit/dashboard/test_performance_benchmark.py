# Copyright notice.

import time

from libs.dashboard.renderers import RendererFactory, RenderFormat
from libs.dashboard.renderers.widget_models import SessionData, SessionStatus

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


class TestPerformanceBenchmark:
    """Tests for basic performance benchmark."""

    @staticmethod
    def test_performance_benchmark() -> None:
        """Test 16: Basic performance benchmark."""
        factory = RendererFactory()
        renderer = factory.create_renderer(RenderFormat.TUI)

        # Prepare test data
        sessions = [SessionData(
                    name=f"benchmark-session-{i}",
                    status=SessionStatus.ACTIVE,
                    uptime=i * 60,
                ) for i in range(100)]

        # Measure rendering time
        start_time = time.perf_counter()

        result = renderer.render_widget(RenderFormat.TUI, sessions)

        end_time = time.perf_counter()
        render_time = end_time - start_time

        # Verify result
        assert result is not None

        # Performance target: 100 sessions should render within 50ms
        assert (
            render_time < 0.05
        ), f"Rendering took {render_time:.3f}s, expected < 0.05s"
