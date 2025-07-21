# Copyright notice.

from libs.dashboard.renderers import RendererFactory, RenderFormat

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


class TestMissingDependencies:
    """Tests for behavior with missing optional dependencies."""

    @staticmethod
    def test_missing_dependencies() -> None:
        """Test behavior with missing optional dependencies."""
        # This would test graceful degradation when optional deps are missing
        # For now, we just verify core functionality works
        factory = RendererFactory()
        renderer = factory.create_renderer(RenderFormat.TUI)
        assert renderer is not None
