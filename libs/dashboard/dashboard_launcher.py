"""Dashboard Launcher.

Detects optimal dashboard interface and manages system requirements.
"""

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class InterfaceInfo:
    """Information about a dashboard interface."""

    name: str
    description: str
    requirements: list[str]
    available: bool
    reason: str | None = None
    priority: int = 1  # Lower = higher priority


class DashboardLauncher:
    """Manages dashboard interface detection, dependency checking, and launching.

    Provides intelligent interface selection based on system capabilities,
    user preferences, and environment constraints.
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize the dashboard launcher.

        Args:
            project_root: Path to project root. If None, auto-detects from current file.
        """
        if project_root is None:
            # Auto-detect project root from current file location
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent

        self.project_root = project_root
        self.tauri_path = project_root / "tauri-dashboard"
        self.api_path = project_root / "api"

        # Interface configuration
        self._interface_configs = {
            "tui": InterfaceInfo(
                name="Terminal User Interface",
                description="Rich-based terminal dashboard with live updates",
                requirements=["rich", "python"],
                available=True,  # Always available
                priority=2,
            ),
            "web": InterfaceInfo(
                name="Web Interface",
                description="Browser-based dashboard with REST API",
                requirements=["fastapi", "uvicorn", "python"],
                available=True,  # Fallback HTML always available
                priority=3,
            ),
            "tauri": InterfaceInfo(
                name="Desktop Application",
                description="Native desktop app with Svelte frontend",
                requirements=["node", "npm", "tauri"],
                available=False,  # Needs checking
                priority=1,
            ),
        }

    def detect_best_interface(self) -> str:
        """Automatically detect the best dashboard interface for current environment.

        Returns:
            Interface name (tui/web/tauri)
        """
        # Update interface availability
        self._update_interface_availability()

        # Environment-based detection logic
        if self._is_ssh_session():
            return "tui"

        # Check for GUI availability
        if self._is_gui_available():
            # Prefer Tauri if available
            if self._interface_configs["tauri"].available:
                return "tauri"
            # Fall back to web if terminal not capable
            elif not self._is_terminal_capable():
                return "web"
            else:
                return "tui"

        # Default based on terminal capability
        if self._is_terminal_capable():
            return "tui"
        else:
            return "web"

    def get_available_interfaces(self) -> dict[str, InterfaceInfo]:
        """Get information about all available interfaces.

        Returns:
            Dictionary of interface name to InterfaceInfo
        """
        self._update_interface_availability()
        return self._interface_configs.copy()

    def get_interface_info(self, interface: str) -> InterfaceInfo:
        """Get detailed information about a specific interface.

        Args:
            interface: Interface name (tui/web/tauri)

        Returns:
            InterfaceInfo object with availability and requirements

        Raises:
            ValueError: If interface is not recognized
        """
        if interface not in self._interface_configs:
            raise ValueError(f"Unknown interface: {interface}")

        self._update_interface_availability()
        return self._interface_configs[interface]

    def check_system_requirements(self) -> dict[str, dict[str, Any]]:
        """Check system requirements for all interfaces.

        Returns:
            Dictionary with requirement status for each interface
        """
        results: dict[str, dict[str, Any]] = {}

        for interface, config in self._interface_configs.items():
            results[interface] = {
                "available": config.available,
                "reason": config.reason,
                "requirements": {},
                "missing": [],
            }

            # Check individual requirements
            for req in config.requirements:
                status, details = self._check_requirement(req)
                results[interface]["requirements"][req] = {
                    "status": status,
                    "details": details,
                }

                if not status:
                    results[interface]["missing"].append(req)

        return results

    def install_dependencies(self, interface: str) -> bool:
        """Attempt to install missing dependencies for an interface.

        Args:
            interface: Interface name to install dependencies for

        Returns:
            True if installation succeeded, False otherwise
        """
        if interface not in self._interface_configs:
            return False

        config = self._interface_configs[interface]

        try:
            if interface == "web":
                # Install Python dependencies
                self._install_python_packages(["fastapi", "uvicorn"])

            elif interface == "tauri":
                # Check and install Node.js dependencies
                if not self._is_node_available():
                    print("❌ Node.js not found. Please install Node.js manually.")
                    return False

                # Install npm dependencies in Tauri directory
                if self.tauri_path.exists():
                    os.chdir(self.tauri_path)
                    subprocess.run(["npm", "install"], check=True)
                    os.chdir(self.project_root)
                else:
                    print(f"❌ Tauri directory not found: {self.tauri_path}")
                    return False

            # Recheck availability
            self._update_interface_availability()
            return self._interface_configs[interface].available

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False

    # Private methods for environment detection

    def _is_gui_available(self) -> bool:
        """Check if GUI environment is available."""
        if platform.system() == "Darwin" or platform.system() == "Windows":  # macOS
            return True
        else:  # Linux/Unix
            return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    def _is_ssh_session(self) -> bool:
        """Check if running in SSH session."""
        return bool(os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"))

    def _is_terminal_capable(self) -> bool:
        """Check if terminal supports rich output."""
        return sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"

    def _is_tauri_available(self) -> bool:
        """Check if Tauri desktop app is available."""
        # Check if tauri directory exists
        if not self.tauri_path.exists():
            return False

        # Check if package.json exists
        if not (self.tauri_path / "package.json").exists():
            return False

        # Check if npm is available
        return self._is_node_available()

    def _is_node_available(self) -> bool:
        """Check if Node.js and npm are available."""
        return shutil.which("node") is not None and shutil.which("npm") is not None

    def _is_python_package_available(self, package: str) -> bool:
        """Check if a Python package is available."""
        try:
            __import__(package)
            return True
        except ImportError:
            return False

    def _update_interface_availability(self) -> None:
        """Update availability status for all interfaces."""
        # TUI - always available (uses rich which is a core dependency)
        self._interface_configs["tui"].available = True
        self._interface_configs["tui"].reason = None

        # Web - check FastAPI/uvicorn availability
        web_available = True
        web_reason = None

        if not self._is_python_package_available("fastapi"):
            web_available = False
            web_reason = "FastAPI not installed (fallback HTML available)"
        elif not self._is_python_package_available("uvicorn"):
            web_available = False
            web_reason = "Uvicorn not installed (fallback HTML available)"

        self._interface_configs["web"].available = web_available
        self._interface_configs["web"].reason = web_reason

        # Tauri - comprehensive check
        tauri_available = True
        tauri_reason = None

        if not self.tauri_path.exists():
            tauri_available = False
            tauri_reason = f"Tauri directory not found: {self.tauri_path}"
        elif not (self.tauri_path / "package.json").exists():
            tauri_available = False
            tauri_reason = "package.json not found in Tauri directory"
        elif not self._is_node_available():
            tauri_available = False
            tauri_reason = "Node.js or npm not installed"

        self._interface_configs["tauri"].available = tauri_available
        self._interface_configs["tauri"].reason = tauri_reason

    def _check_requirement(self, requirement: str) -> tuple[bool, str]:
        """Check if a specific requirement is met.

        Args:
            requirement: Requirement name to check

        Returns:
            Tuple of (status, details)
        """
        if requirement == "python":
            return True, f"Python {sys.version.split()[0]}"

        elif requirement == "rich":
            try:
                import rich

                # Rich might not have __version__ in older versions
                version = getattr(rich, "__version__", "unknown")
                return True, f"Rich {version}"
            except ImportError:
                return False, "Rich not installed"

        elif requirement == "fastapi":
            try:
                import fastapi

                return True, f"FastAPI {fastapi.__version__}"
            except ImportError:
                return False, "FastAPI not installed"

        elif requirement == "uvicorn":
            try:
                import uvicorn

                return True, f"Uvicorn {uvicorn.__version__}"
            except ImportError:
                return False, "Uvicorn not installed"

        elif requirement == "node":
            node_path = shutil.which("node")
            if node_path:
                try:
                    result = subprocess.run(
                        ["node", "--version"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    return True, f"Node.js {result.stdout.strip()}"
                except subprocess.CalledProcessError:
                    return False, "Node.js not working"
            else:
                return False, "Node.js not installed"

        elif requirement == "npm":
            npm_path = shutil.which("npm")
            if npm_path:
                try:
                    result = subprocess.run(
                        ["npm", "--version"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    return True, f"npm {result.stdout.strip()}"
                except subprocess.CalledProcessError:
                    return False, "npm not working"
            else:
                return False, "npm not installed"

        elif requirement == "tauri":
            tauri_available = self._is_tauri_available()
            if tauri_available:
                return True, "Tauri project configured"
            else:
                return False, "Tauri not available"

        else:
            return False, f"Unknown requirement: {requirement}"

    def _install_python_packages(self, packages: list[str]) -> None:
        """Install Python packages using pip."""
        for package in packages:
            if not self._is_python_package_available(package):
                print(f"📦 Installing {package}...")
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        package,
                    ],
                    check=True,
                )
