# Copyright notice.

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from libs.dashboard.dashboard_launcher import DashboardLauncher, InterfaceInfo

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Tests for DashboardLauncher.

Comprehensive testing of dashboard interface detection, dependency checking,
and environment analysis.
"""


class TestDashboardLauncher:
    """Test suite for DashboardLauncher functionality."""

    @pytest.fixture
    @staticmethod
    def temp_project_root() -> Iterator[Path]:
        """Create a temporary project directory structure.

        Returns:
        object: Description of return value.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create tauri-dashboard directory with package.json
            tauri_dir = project_root / "tauri-dashboard"
            tauri_dir.mkdir()
            (tauri_dir / "package.json").write_text('{"name": "test-dashboard"}')

            # Create api directory
            api_dir = project_root / "api"
            api_dir.mkdir()

            yield project_root

    @pytest.fixture
    @staticmethod
    def launcher(temp_project_root: Path) -> DashboardLauncher:
        """Create DashboardLauncher instance with temp project root.

        Returns:
        DashboardLauncher: Description of return value.
        """
        return DashboardLauncher(project_root=temp_project_root)

    @staticmethod
    def test_init_with_project_root(temp_project_root: Path) -> None:
        """Test launcher initialization with explicit project root."""
        launcher = DashboardLauncher(project_root=temp_project_root)

        assert launcher.project_root == temp_project_root
        assert launcher.tauri_path == temp_project_root / "tauri-dashboard"
        assert launcher.api_path == temp_project_root / "api"

    @staticmethod
    def test_init_without_project_root() -> None:
        """Test launcher initialization with auto-detected project root."""
        launcher = DashboardLauncher()

        # Should auto-detect from current file location
        expected_root = Path(__file__).resolve().parent.parent
        assert launcher.project_root == expected_root

    @staticmethod
    def test_interface_configs_structure(launcher: DashboardLauncher) -> None:
        """Test that interface configurations are properly structured."""
        configs = launcher._interface_configs

        # Check all expected interfaces exist
        assert "tui" in configs
        assert "web" in configs
        assert "tauri" in configs

        # Check InterfaceInfo structure
        for config in configs.values():
            assert isinstance(config, InterfaceInfo)
            assert config.name
            assert config.description
            assert isinstance(config.requirements, list)
            assert isinstance(config.available, bool)
            assert isinstance(config.priority, int)

    @patch("libs.dashboard.dashboard_launcher.platform.system")
    def test_is_gui_available_macos(self, mock_platform: Mock, launcher: DashboardLauncher) -> None:
        """Test GUI detection on macOS."""
        mock_platform.return_value = "Darwin"
        assert launcher._is_gui_available() is True

    @patch("libs.dashboard.dashboard_launcher.platform.system")
    def test_is_gui_available_windows(self, mock_platform: Mock, launcher: DashboardLauncher) -> None:
        """Test GUI detection on Windows."""
        mock_platform.return_value = "Windows"
        assert launcher._is_gui_available() is True

    @patch("libs.dashboard.dashboard_launcher.platform.system")
    @patch.dict(os.environ, {"DISPLAY": ":0"})
    def test_is_gui_available_linux_with_display(self, mock_platform: Mock, launcher: DashboardLauncher) -> None:
        """Test GUI detection on Linux with DISPLAY."""
        mock_platform.return_value = "Linux"
        assert launcher._is_gui_available() is True

    @patch("libs.dashboard.dashboard_launcher.platform.system")
    @patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"})
    def test_is_gui_available_linux_with_wayland(self, mock_platform: Mock, launcher: DashboardLauncher) -> None:
        """Test GUI detection on Linux with Wayland."""
        mock_platform.return_value = "Linux"
        assert launcher._is_gui_available() is True

    @patch("libs.dashboard.dashboard_launcher.platform.system")
    @patch.dict(os.environ, {}, clear=True)
    def test_is_gui_available_linux_without_display(self, mock_platform: Mock, launcher: DashboardLauncher) -> None:
        """Test GUI detection on Linux without display."""
        mock_platform.return_value = "Linux"
        assert launcher._is_gui_available() is False

    @patch.dict(os.environ, {"SSH_CLIENT": "192.168.1.1 12345"})
    @staticmethod
    def test_is_ssh_session_with_ssh_client(launcher: DashboardLauncher) -> None:
        """Test SSH detection with SSH_CLIENT."""
        assert launcher._is_ssh_session() is True

    @patch.dict(os.environ, {"SSH_TTY": "/dev/pts/0"})
    @staticmethod
    def test_is_ssh_session_with_ssh_tty(launcher: DashboardLauncher) -> None:
        """Test SSH detection with SSH_TTY."""
        assert launcher._is_ssh_session() is True

    @patch.dict(os.environ, {}, clear=True)
    @staticmethod
    def test_is_ssh_session_without_ssh(launcher: DashboardLauncher) -> None:
        """Test SSH detection without SSH environment."""
        assert launcher._is_ssh_session() is False

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM": "xterm-256color"})
    def test_is_terminal_capable_with_tty(self, mock_isatty: Mock, launcher: DashboardLauncher) -> None:
        """Test terminal capability with TTY."""
        mock_isatty.return_value = True
        assert launcher._is_terminal_capable() is True

    @patch("sys.stdout.isatty")
    @patch.dict(os.environ, {"TERM": "dumb"})
    def test_is_terminal_capable_with_dumb_term(self, mock_isatty: Mock, launcher: DashboardLauncher) -> None:
        """Test terminal capability with dumb terminal."""
        mock_isatty.return_value = True
        assert launcher._is_terminal_capable() is False

    @patch("sys.stdout.isatty")
    def test_is_terminal_capable_without_tty(self, mock_isatty: Mock, launcher: DashboardLauncher) -> None:
        """Test terminal capability without TTY."""
        mock_isatty.return_value = False
        assert launcher._is_terminal_capable() is False

    @patch("libs.dashboard.dashboard_launcher.shutil.which")
    def test_is_node_available_with_both(self, mock_which: Mock, launcher: DashboardLauncher) -> None:
        """Test Node.js availability with both node and npm."""
        mock_which.side_effect = lambda cmd: ("/usr/bin/" + cmd if cmd in {"node", "npm"} else None)
        assert launcher._is_node_available() is True

    @patch("libs.dashboard.dashboard_launcher.shutil.which")
    def test_is_node_available_missing_node(self, mock_which: Mock, launcher: DashboardLauncher) -> None:
        """Test Node.js availability with missing node."""
        mock_which.side_effect = lambda cmd: "/usr/bin/npm" if cmd == "npm" else None
        assert launcher._is_node_available() is False

    @patch("libs.dashboard.dashboard_launcher.shutil.which")
    def test_is_node_available_missing_npm(self, mock_which: Mock, launcher: DashboardLauncher) -> None:
        """Test Node.js availability with missing npm."""
        mock_which.side_effect = lambda cmd: "/usr/bin/node" if cmd == "node" else None
        assert launcher._is_node_available() is False

    @staticmethod
    def test_is_tauri_available_with_complete_setup(
        launcher: DashboardLauncher,
    ) -> None:
        """Test Tauri availability with complete setup."""
        with patch.object(launcher, "_is_node_available", return_value=True):
            assert launcher._is_tauri_available() is True

    @staticmethod
    def test_is_tauri_available_missing_directory(temp_project_root: Path) -> None:
        """Test Tauri availability with missing directory."""
        # Remove the tauri directory
        shutil.rmtree(temp_project_root / "tauri-dashboard")

        launcher = DashboardLauncher(project_root=temp_project_root)
        assert launcher._is_tauri_available() is False

    @staticmethod
    def test_is_tauri_available_missing_package_json(
        launcher: DashboardLauncher,
    ) -> None:
        """Test Tauri availability with missing package.json."""
        # Remove package.json
        (launcher.tauri_path / "package.json").unlink()

        assert launcher._is_tauri_available() is False

    @staticmethod
    def test_is_tauri_available_missing_node(launcher: DashboardLauncher) -> None:
        """Test Tauri availability with missing Node.js."""
        with patch.object(launcher, "_is_node_available", return_value=False):
            assert launcher._is_tauri_available() is False

    @staticmethod
    def test_is_python_package_available_existing(launcher: DashboardLauncher) -> None:
        """Test Python package availability for existing package."""
        assert launcher._is_python_package_available("sys") is True

    @staticmethod
    def test_is_python_package_available_missing(launcher: DashboardLauncher) -> None:
        """Test Python package availability for missing package."""
        assert launcher._is_python_package_available("nonexistent_package_12345") is False

    @staticmethod
    def test_get_interface_info_valid(launcher: DashboardLauncher) -> None:
        """Test getting interface info for valid interface."""
        info = launcher.get_interface_info("tui")

        assert isinstance(info, InterfaceInfo)
        assert info.name == "Terminal User Interface"
        assert "rich" in info.requirements

    @staticmethod
    def test_get_interface_info_invalid(launcher: DashboardLauncher) -> None:
        """Test getting interface info for invalid interface."""
        with pytest.raises(ValueError, match="Unknown interface: invalid"):
            launcher.get_interface_info("invalid")

    @staticmethod
    def test_get_available_interfaces(launcher: DashboardLauncher) -> None:
        """Test getting all available interfaces."""
        interfaces = launcher.get_available_interfaces()

        assert len(interfaces) == 3
        assert "tui" in interfaces
        assert "web" in interfaces
        assert "tauri" in interfaces

        for info in interfaces.values():
            assert isinstance(info, InterfaceInfo)

    @patch.object(DashboardLauncher, "_is_ssh_session")
    def test_detect_best_interface_ssh(self, mock_ssh: Mock, launcher: DashboardLauncher) -> None:
        """Test interface detection in SSH environment."""
        mock_ssh.return_value = True

        result = launcher.detect_best_interface()
        assert result == "tui"

    @patch.object(DashboardLauncher, "_is_gui_available")
    @patch.object(DashboardLauncher, "_is_ssh_session")
    def test_detect_best_interface_gui_with_tauri(self, mock_ssh: Mock, mock_gui: Mock, launcher: DashboardLauncher) -> None:
        """Test interface detection with GUI and Tauri available."""
        mock_ssh.return_value = False
        mock_gui.return_value = True

        # Mock tauri as available
        launcher._interface_configs["tauri"].available = True

        result = launcher.detect_best_interface()
        assert result == "tauri"

    @patch.object(DashboardLauncher, "_is_node_available")
    @patch.object(DashboardLauncher, "_is_terminal_capable")
    @patch.object(DashboardLauncher, "_is_gui_available")
    @patch.object(DashboardLauncher, "_is_ssh_session")
    def test_detect_best_interface_gui_without_tauri_no_terminal(self, mock_ssh: Mock, mock_gui: Mock, mock_term: Mock, mock_node: Mock, launcher: DashboardLauncher) -> None:
        """Test interface detection with GUI but no Tauri and no terminal
        capability.
        """
        mock_ssh.return_value = False
        mock_gui.return_value = True
        mock_term.return_value = False
        mock_node.return_value = False  # This will make tauri unavailable

        result = launcher.detect_best_interface()
        assert result == "web"

    @patch.object(DashboardLauncher, "_is_terminal_capable")
    @patch.object(DashboardLauncher, "_is_ssh_session")
    def test_detect_best_interface_terminal_capable(self, mock_ssh: Mock, mock_term: Mock, launcher: DashboardLauncher) -> None:
        """Test interface detection with terminal capability."""
        mock_ssh.return_value = False
        mock_term.return_value = True

        result = launcher.detect_best_interface()
        assert result == "tui"

    @patch.object(DashboardLauncher, "_is_terminal_capable")
    @patch.object(DashboardLauncher, "_is_ssh_session")
    def test_detect_best_interface_fallback_to_web(self, mock_ssh: Mock, mock_term: Mock, launcher: DashboardLauncher) -> None:
        """Test interface detection fallback to web."""
        mock_ssh.return_value = False
        mock_term.return_value = False

        result = launcher.detect_best_interface()
        assert result == "web"

    @staticmethod
    def test_check_system_requirements_structure(launcher: DashboardLauncher) -> None:
        """Test system requirements check structure."""
        reqs = launcher.check_system_requirements()

        assert "tui" in reqs
        assert "web" in reqs
        assert "tauri" in reqs

        for req_info in reqs.values():
            assert "available" in req_info
            assert "reason" in req_info
            assert "requirements" in req_info
            assert "missing" in req_info
            assert isinstance(req_info["requirements"], dict)
            assert isinstance(req_info["missing"], list)

    @patch("subprocess.run")
    def test_check_requirement_node_success(self, mock_run: Mock, launcher: DashboardLauncher) -> None:
        """Test checking Node.js requirement successfully."""
        mock_run.return_value = MagicMock(stdout="v18.0.0\\n")

        with patch(
            "libs.dashboard.dashboard_launcher.shutil.which",
            return_value="/usr/bin/node",
        ):
            status, details = launcher._check_requirement("node")

            assert status is True
            assert "v18.0.0" in details

    @patch("subprocess.run")
    def test_check_requirement_node_failure(self, mock_run: Mock, launcher: DashboardLauncher) -> None:
        """Test checking Node.js requirement with failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["node"])

        with patch(
            "libs.dashboard.dashboard_launcher.shutil.which",
            return_value="/usr/bin/node",
        ):
            status, details = launcher._check_requirement("node")

            assert status is False
            assert "not working" in details

    @staticmethod
    def test_check_requirement_node_missing(launcher: DashboardLauncher) -> None:
        """Test checking Node.js requirement when missing."""
        with patch("libs.dashboard.dashboard_launcher.shutil.which", return_value=None):
            status, details = launcher._check_requirement("node")

            assert status is False
            assert "not installed" in details

    @staticmethod
    def test_check_requirement_python(launcher: DashboardLauncher) -> None:
        """Test checking Python requirement."""
        status, details = launcher._check_requirement("python")

        assert status is True
        assert "Python" in details
        assert sys.version.split()[0] in details

    @staticmethod
    def test_check_requirement_unknown(launcher: DashboardLauncher) -> None:
        """Test checking unknown requirement."""
        status, details = launcher._check_requirement("unknown_requirement")

        assert status is False
        assert "Unknown requirement" in details

    @patch("subprocess.run")
    @patch.object(DashboardLauncher, "_is_python_package_available")
    def test_install_dependencies_web_success(self, mock_available: Mock, mock_run: Mock, launcher: DashboardLauncher) -> None:
        """Test installing web dependencies successfully."""
        mock_available.side_effect = [False, False]  # fastapi and uvicorn not available
        mock_run.return_value = MagicMock()

        launcher.install_dependencies("web")

        # Should call pip install for both packages
        assert mock_run.call_count == 2

    @staticmethod
    def test_install_dependencies_invalid_interface(
        launcher: DashboardLauncher,
    ) -> None:
        """Test installing dependencies for invalid interface."""
        result = launcher.install_dependencies("invalid")
        assert result is False

    @patch("subprocess.run")
    @patch.object(DashboardLauncher, "_is_node_available")
    @patch("os.chdir")
    def test_install_dependencies_tauri_success(self, mock_chdir: Mock, mock_node: Mock, mock_run: Mock, launcher: DashboardLauncher) -> None:
        """Test installing Tauri dependencies successfully."""
        mock_node.return_value = True
        mock_run.return_value = MagicMock()

        launcher.install_dependencies("tauri")

        # Should change directory and run npm install
        assert mock_chdir.call_count >= 1
        mock_run.assert_called_with(["npm", "install"], check=True)

    @patch.object(DashboardLauncher, "_is_node_available")
    def test_install_dependencies_tauri_no_node(self, mock_node: Mock, launcher: DashboardLauncher) -> None:
        """Test installing Tauri dependencies without Node.js."""
        mock_node.return_value = False

        result = launcher.install_dependencies("tauri")
        assert result is False

    @staticmethod
    def test_install_dependencies_tauri_no_directory(temp_project_root: Path) -> None:
        """Test installing Tauri dependencies without Tauri directory."""
        # Remove tauri directory
        shutil.rmtree(temp_project_root / "tauri-dashboard")

        launcher = DashboardLauncher(project_root=temp_project_root)
        result = launcher.install_dependencies("tauri")
        assert result is False


class TestInterfaceInfo:
    """Test suite for InterfaceInfo dataclass."""

    @staticmethod
    def test_interface_info_creation() -> None:
        """Test creating InterfaceInfo instance."""
        info = InterfaceInfo(
            name="Test Interface",
            description="Test description",
            requirements=["req1", "req2"],
            available=True,
            reason="Test reason",
            priority=2,
        )

        assert info.name == "Test Interface"
        assert info.description == "Test description"
        assert info.requirements == ["req1", "req2"]
        assert info.available is True
        assert info.reason == "Test reason"
        assert info.priority == 2

    @staticmethod
    def test_interface_info_defaults() -> None:
        """Test InterfaceInfo with default values."""
        info = InterfaceInfo(
            name="Test Interface",
            description="Test description",
            requirements=["req1"],
            available=False,
        )

        assert info.reason is None
        assert info.priority == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
