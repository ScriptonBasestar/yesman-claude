# Copyright notice.

import asyncio

import pytest

from libs.dashboard.renderers import RendererFactory, RenderFormat, WidgetType
from libs.dashboard.renderers.widget_models import SessionData, SessionStatus

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


class TestConcurrentRendering:
    """Tests for concurrent rendering operations."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_concurrent_rendering() -> None:
        """Test 7: Concurrent rendering operations."""
        factory = RendererFactory()

        # Test data
        session_data = SessionData(
            name="concurrent-session",
            status=SessionStatus.ACTIVE,
            uptime=1800,
        )

        async def render_widget_async(
            format_type: RenderFormat, widget_type: WidgetType, data: object
        ) -> object:
            """Async wrapper for rendering."""
            renderer = factory.create_renderer(format_type)
            return renderer.render_widget(widget_type, data)

        # Create multiple concurrent rendering tasks
        tasks = []
        for i in range(10):
            for format_type in [RenderFormat.TUI, RenderFormat.WEB, RenderFormat.TAURI]:
                task = render_widget_async(
                    format_type,
                    WidgetType.SESSION_BROWSER,
                    [session_data],
                )
                tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all rendered successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None
            assert isinstance(result, dict)
