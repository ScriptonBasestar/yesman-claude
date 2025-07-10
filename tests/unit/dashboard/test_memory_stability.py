import pytest
import gc
from libs.dashboard.renderers import RendererFactory, RenderFormat
from libs.dashboard.renderers.widget_models import SessionData, SessionStatus

class TestMemoryStability:
    """Tests for memory stability during intensive operations"""

    def test_memory_stability(self):
        """Test 14: Memory stability during intensive operations"""
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
            result = renderer.render_widget(RenderFormat.TUI, [data])
            assert result is not None
        
        # Force garbage collection
        gc.collect()
        
        # Check for memory leaks (allow some growth but not excessive)
        final_objects = len(gc.get_objects())
        growth = final_objects - initial_objects
        
        # Allow up to 50% growth (this is quite generous)
        assert growth < initial_objects * 0.5
