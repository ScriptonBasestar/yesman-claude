"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

from pathlib import Path
from typing import object

import pytest

from libs.dashboard import DashboardLauncher


class TestInterfaceDetection:
    """Tests for dashboard interface detection and availability."""

    @pytest.fixture
    @staticmethod
    def temp_project_root():
        """Create temporary project directory."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create tauri-dashboard directory with package.json
            tauri_dir = project_root / "tauri-dashboard"
            tauri_dir.mkdir()
            (tauri_dir / "package.json").write_text('{"name": "test-dashboard"}')

            yield project_root

    @pytest.fixture
    @staticmethod
    def launcher(temp_project_root: object):
        """Create DashboardLauncher with temp project root."""
        return DashboardLauncher(project_root=temp_project_root)

    @staticmethod
    def test_interface_detection(launcher: object) -> None:
        """Test 1: Interface detection and availability checking."""
        # Test auto-detection
        best_interface = launcher.detect_best_interface()
        assert best_interface in ["tui", "web", "tauri"]

        # Test interface availability
        interfaces = launcher.get_available_interfaces()
        assert len(interfaces) == 3
        assert "tui" in interfaces
        assert "web" in interfaces
        assert "tauri" in interfaces

        # Test TUI always available
        assert interfaces["tui"].available is True

        # Test system requirements
        requirements = launcher.check_system_requirements()
        assert "tui" in requirements
        assert "web" in requirements
        assert "tauri" in requirements
