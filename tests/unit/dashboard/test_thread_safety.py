# Copyright notice.

import threading

from libs.dashboard.renderers import RendererFactory, RenderFormat
from libs.dashboard.renderers.widget_models import SessionData, SessionStatus

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


class TestThreadSafety:
    """Tests for thread safety of components."""

    @staticmethod
    def test_thread_safety() -> None:
        """Test 15: Thread safety of components."""
        factory = RendererFactory()
        results = []
        errors = []

        def render_in_thread(thread_id: int) -> None:
            try:
                renderer = factory.create_renderer(RenderFormat.TUI)
                data = SessionData(
                    name=f"thread-{thread_id}",
                    status=SessionStatus.ACTIVE,
                    uptime=thread_id * 100,
                )
                result = renderer.render_widget(RenderFormat.TUI, [data])
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
