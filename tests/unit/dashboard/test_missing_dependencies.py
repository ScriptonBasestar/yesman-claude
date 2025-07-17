from libs.dashboard.renderers import RendererFactory, RenderFormat


class TestMissingDependencies:
    """Tests for behavior with missing optional dependencies."""

    def test_missing_dependencies(self):
        """Test behavior with missing optional dependencies."""
        # This would test graceful degradation when optional deps are missing
        # For now, we just verify core functionality works
        factory = RendererFactory()
        renderer = factory.create_renderer(RenderFormat.TUI)
        assert renderer is not None
