# Copyright notice.


import pathlib

import pytest

from libs.dashboard.theme_system import SystemThemeDetector

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


class TestLinuxSpecificFeatures:
    """Tests for Linux-specific functionality."""

    @pytest.mark.skipif(not pathlib.Path("/proc").exists(), reason="Linux-specific test")
    @staticmethod
    def test_linux_specific_features() -> None:
        """Test Linux-specific functionality."""
        # This should not crash on Linux
        theme_mode = SystemThemeDetector.get_system_theme()
        assert theme_mode is not None
