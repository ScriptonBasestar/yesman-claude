import http.server
import os
import platform
import shutil
import socket
import socketserver
import subprocess  # noqa: S404
import sys
import threading
import time
import time as time_module
import webbrowser
from pathlib import Path
from typing import Any

import click
import uvicorn
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from libs.core.base_command import BaseCommand, CommandError

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Dashboard interface management commands."""

try:
    pass
except ImportError:
    uvicorn = None


class DashboardEnvironment:
    """Detects and manages dashboard environment capabilities."""

    @staticmethod
    def is_gui_available() -> bool:
        """Check if GUI environment is available.

        Returns:
        Boolean indicating.
        """
        if platform.system() == "Darwin" or platform.system() == "Windows":  # macOS
            return True
        # Linux/Unix
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    @staticmethod
    def is_ssh_session() -> bool:
        """Check if running in SSH session.

        Returns:
        Boolean indicating.
        """
        return bool(os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"))

    @staticmethod
    def is_terminal_capable() -> bool:
        """Check if terminal supports rich output.

        Returns:
        Boolean indicating.
        """
        return sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"

    @staticmethod
    def get_recommended_interface() -> str:
        """Get recommended interface based on environment.

        Returns:
        String containing the requested data.
        """
        if DashboardEnvironment.is_ssh_session():
            return "tui"
        if DashboardEnvironment.is_gui_available():
            return "tauri"
        if DashboardEnvironment.is_terminal_capable():
            return "tui"
        return "web"


def check_dependencies(interface: str) -> dict[str, bool]:
    """Check if required dependencies are available for interface.

    Returns:
        Dict containing.
    """
    deps = {
        "tui": True,  # Always available (uses rich)
        "web": True,  # Uses built-in server
        "tauri": False,
    }

    if interface == "tauri":
        dashboard_path = Path(__file__).parent.parent / "tauri-dashboard"
        deps["tauri"] = dashboard_path.exists() and (dashboard_path / "package.json").exists() and shutil.which("npm") is not None

    return deps


class DashboardRunCommand(BaseCommand):
    """Run the dashboard with specified interface."""

    def __init__(self) -> None:
        super().__init__()
        self.env = DashboardEnvironment()

    def execute(
        self,
        interface: str = "auto",
        host: str = "localhost",
        port: int = 8000,
        theme: str | None = None,
        dev: bool = False,  # noqa: FBT001
        detach: bool = False,  # noqa: FBT001
        **kwargs: Any,  # noqa: ARG002
    ) -> dict:
        """Execute the dashboard run command.

        Returns:
        Dict containing.
        """
        # Auto-detect interface if needed
        if interface == "auto":
            interface = self.env.get_recommended_interface()
            self.print_info(f"🔍 Auto-detected interface: {interface}")

        # Check dependencies
        deps = check_dependencies(interface)
        if not deps.get(interface, False) and interface == "tauri":
            self.print_error(f"Dependencies not available for {interface} interface")
            self.print_info("Available interfaces:")
            for iface, available in deps.items():
                status = "✅" if available else "❌"
                self.print_info(f"  {status} {iface}")

            # Fallback to TUI if auto-detection
            if interface == self.env.get_recommended_interface():
                self.print_warning("Falling back to TUI interface...")
                interface = "tui"
            else:
                msg = "Dependencies not available for selected interface"
                raise CommandError(msg)

        # Launch appropriate interface
        try:
            if interface == "tui":
                self._launch_tui_dashboard(theme=theme, dev=dev)
            elif interface == "web":
                self._launch_web_dashboard(
                    host=host,
                    port=port,
                    theme=theme,
                    dev=dev,
                    detach=detach,
                )
            elif interface == "tauri":
                self._launch_tauri_dashboard(theme=theme, dev=dev, detach=detach)
            else:
                msg = f"Unknown interface: {interface}"
                raise CommandError(msg)

            return {"interface": interface, "success": True}

        except KeyboardInterrupt:
            self.print_info("\n👋 Dashboard shutdown complete")
            return {"interface": interface, "success": True, "stopped_by_user": True}
        except Exception as e:
            msg = f"Dashboard error: {e}"
            raise CommandError(msg) from e

    def _launch_tui_dashboard(self, theme: str | None = None, dev: bool = False) -> None:  # noqa: FBT001, ARG002
        """Launch TUI-based dashboard interface.

        Returns:
        None.
        """
        self.print_info("🖥️  Starting TUI Dashboard...")

        try:
            console = Console()

            # Create sample dashboard layout
            def create_dashboard_layout() -> Layout:
                layout = Layout()

                # Create header
                header = Panel(
                    "[bold blue]Yesman Claude TUI Dashboard[/bold blue]\n[dim]Real-time session monitoring and management[/dim]",
                    title="Dashboard",
                    border_style="blue",
                )

                # Create metrics table
                metrics_table = Table(title="System Metrics")
                metrics_table.add_column("Metric", style="cyan")
                metrics_table.add_column("Value", style="green")
                metrics_table.add_column("Status", style="yellow")

                metrics_table.add_row("Active Sessions", "3", "🟢 Normal")
                metrics_table.add_row("CPU Usage", "25%", "🟢 Low")
                metrics_table.add_row("Memory Usage", "45%", "🟡 Medium")
                metrics_table.add_row("Claude Instances", "2", "🟢 Active")

                # Split layout
                layout.split_column(Layout(header, size=4), Layout(metrics_table))

                return layout

            # Display dashboard with live updates
            with Live(create_dashboard_layout(), refresh_per_second=1) as live:
                console.print("\n[bold green]TUI Dashboard is running![/bold green]")
                console.print("[dim]Press Ctrl+C to exit[/dim]\n")

                try:
                    while True:
                        time.sleep(1)
                        # Update dashboard data here
                        live.update(create_dashboard_layout())
                except KeyboardInterrupt:
                    console.print("\n[yellow]Shutting down TUI dashboard...[/yellow]")

        except ImportError as e:
            msg = f"TUI dependencies not available: {e}"
            raise CommandError(msg) from e

    def _launch_web_dashboard(
        self,
        host: str = "localhost",
        port: int = 8000,
        theme: str | None = None,
        dev: bool = False,  # noqa: FBT001
        detach: bool = False,  # noqa: FBT001
    ) -> None:
        """Launch web-based dashboard interface.

        Returns:
        None.
        """
        self.print_info(f"🌐 Starting Web Dashboard on http://{host}:{port}...")

        try:
            # Check if port is available by trying to bind to it
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                sock.close()
            except OSError as e:
                sock.close()
                msg = f"Port {port} is already in use. Try a different port with -p option."
                raise CommandError(msg) from e

            # Start FastAPI server
            api_path = Path(__file__).parent.parent / "api"
            if not api_path.exists():
                self.print_warning("Web dashboard API not found. Creating simple HTML interface...")

                # Create simple HTML dashboard
                template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "web_dashboard.html")
                with open(template_path, encoding="utf-8") as f:
                    html_template = f.read()
                html_content = html_template.format(
                    host=host,
                    port=port,
                    theme=theme or "default",
                    dev="Development" if dev else "Production",
                )

                # Start simple HTTP server
                class DashboardHandler(http.server.SimpleHTTPRequestHandler):
                    def do_GET(self) -> None:
                        self.send_response(200)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        self.wfile.write(html_content.encode())

                def run_server() -> None:
                    with socketserver.TCPServer((host, port), DashboardHandler) as httpd:
                        httpd.serve_forever()

                if detach:
                    # Run in background
                    server_thread = threading.Thread(target=run_server, daemon=True)
                    server_thread.start()
                    self.print_info(f"Web dashboard started in background at http://{host}:{port}")

                    # Open browser
                    webbrowser.open(f"http://{host}:{port}")

                    # Keep main thread alive
                    try:
                        while True:
                            time_module.sleep(1)
                    except KeyboardInterrupt:
                        self.print_info("Shutting down web dashboard...")
                else:
                    self.print_info(f"Web dashboard running at http://{host}:{port}")
                    self.print_info("Press Ctrl+C to stop")

                    # Open browser
                    webbrowser.open(f"http://{host}:{port}")

                    try:
                        run_server()
                    except KeyboardInterrupt:
                        self.print_info("\nShutting down web dashboard...")
            else:
                # Use FastAPI server
                try:
                    if uvicorn is None:
                        msg = "FastAPI/uvicorn not available. Install with: uv add fastapi uvicorn"
                        raise CommandError(msg)

                    # Show the URL before starting
                    dashboard_url = f"http://{host}:{port}"
                    self.print_info(f"🌐 FastAPI server starting at {dashboard_url}")
                    self.print_info("📊 Dashboard will be available at the URL above")

                    if dev:
                        # 개발 모드에서는 Vite 개발 서버도 함께 실행
                        self.print_info("🚀 Starting Vite dev server for hot module replacement...")

                        # Check if port 5173 is available first
                        vite_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        vite_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        try:
                            vite_sock.bind(("localhost", 5173))
                            vite_sock.close()
                        except OSError:
                            vite_sock.close()
                            self.print_warning("Port 5173 is already in use. Vite server may not start properly.")

                        vite_process = subprocess.Popen(
                            ["npm", "run", "dev"],
                            cwd=Path(__file__).parent.parent / "tauri-dashboard",
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )

                        # Check if process started successfully
                        time.sleep(1)  # Give process time to start
                        if vite_process.poll() is not None:
                            self.print_error("Failed to start Vite development server")
                            msg = "Could not start Vite server. Check if dependencies are installed."
                            raise CommandError(msg)

                        # Vite 서버가 시작될 때까지 대기
                        def wait_for_vite_server() -> bool:
                            for i in range(20):  # 최대 20초 대기
                                try:
                                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    result = sock.connect_ex(("localhost", 5173))
                                    sock.close()
                                    if result == 0:  # 포트가 열려있음
                                        return True
                                    time.sleep(1)
                                except Exception:
                                    time.sleep(1)
                            return False

                        vite_ready = wait_for_vite_server()
                        if vite_ready:
                            self.print_success("Vite server is ready!")
                        else:
                            self.print_warning("Vite server may not be ready yet...")

                        self.print_info("📝 Development mode:")
                        self.print_info(f"  - API Server: http://{host}:{port}")
                        self.print_info("  - Frontend (Vite): http://localhost:5173")
                        self.print_info("  - Changes will be reflected automatically!")

                        if not detach:
                            # 개발 모드에서는 Vite 서버로 연결 (서버가 준비된 후)
                            if vite_ready:
                                self.print_info("🔗 Opening browser to Vite dev server...")
                                webbrowser.open("http://localhost:5173")
                            else:
                                self.print_info("")
                                self.print_info("=" * 60)
                                self.print_warning("VITE SERVER NOT READY - MANUAL ACTION REQUIRED")
                                self.print_info("=" * 60)
                                self.print_info("🔗 Please manually open: http://localhost:5173")
                                self.print_info("   (Wait a few seconds if the page doesn't load)")
                                self.print_info("=" * 60)
                                self.print_info("")

                    if not detach and not dev:
                        # Open browser after a short delay in a separate thread
                        def open_browser() -> None:
                            time.sleep(2)  # Wait for server to start
                            try:
                                webbrowser.open(dashboard_url)
                                self.print_info(f"🔗 Opening browser to {dashboard_url}")
                            except Exception as e:
                                self.print_warning(f"Could not open browser automatically: {e}")
                                self.print_info(f"Please open {dashboard_url} manually in your browser")

                        threading.Thread(target=open_browser, daemon=True).start()

                    try:
                        uvicorn.run("api.main:app", host=host, port=port, reload=dev)
                    finally:
                        if dev and "vite_process" in locals():
                            vite_process.terminate()

                except Exception as uvicorn_error:
                    msg = f"FastAPI server error: {uvicorn_error}"
                    raise CommandError(msg) from uvicorn_error

        except Exception as e:
            msg = f"Web dashboard error: {e}"
            raise CommandError(msg) from e

    def _launch_tauri_dashboard(
        self,
        theme: str | None = None,  # noqa: ARG002
        dev: bool = False,  # noqa: FBT001
        detach: bool = False,  # noqa: FBT001
    ) -> None:
        """Launch Tauri-based desktop dashboard interface."""
        self.print_info("🖥️  Starting Tauri Desktop Dashboard...")

        # Get the tauri dashboard path
        dashboard_path = Path(__file__).parent.parent / "tauri-dashboard"

        if not dashboard_path.exists():
            msg = f"Tauri dashboard not found at: {dashboard_path}\nMake sure the tauri-dashboard directory exists and is properly set up."
            raise CommandError(msg)

        # Check npm availability
        if not shutil.which("npm"):
            msg = "npm not found. Please install Node.js and npm."
            raise CommandError(msg)

        # Change to tauri dashboard directory
        original_cwd = os.getcwd()
        os.chdir(dashboard_path)

        # Set environment variables to suppress warnings
        env = os.environ.copy()
        env["G_MESSAGES_DEBUG"] = ""
        env["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"
        env["GST_DEBUG"] = "0"
        env["PYTHONWARNINGS"] = "ignore"

        try:
            if dev:
                self.print_info("Starting Tauri dashboard in development mode...")
                cmd = ["npm", "run", "tauri", "dev"]
            else:
                self.print_info("Starting Tauri dashboard...")
                # Check if built app exists
                build_dir = dashboard_path / "src-tauri" / "target" / "release"

                if not build_dir.exists():
                    self.print_warning("Release build not found. Switching to development mode...")
                    self.print_info("Starting Tauri dashboard in development mode...")
                    cmd = ["npm", "run", "tauri", "dev"]
                # Find the executable (platform dependent)
                elif sys.platform == "darwin":  # macOS
                    app_bundle = build_dir / "bundle" / "macos" / "Yesman Dashboard.app"
                    cmd = ["open", str(app_bundle)] if app_bundle.exists() else [str(build_dir / "Yesman Dashboard")]
                elif sys.platform == "win32":  # Windows
                    cmd = [str(build_dir / "Yesman Dashboard.exe")]
                else:  # Linux
                    cmd = [str(build_dir / "yesman-tauri-dashboard")]

            # Run the command
            if detach:
                # Run in background
                process = subprocess.Popen(  # nosec
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.print_info(f"Tauri dashboard started in background (PID: {process.pid})")
                return
            with open(os.devnull, "w", encoding="utf-8"):
                subprocess.run(  # nosec
                    cmd,
                    env=env,
                    stderr=subprocess.PIPE,
                    check=True,
                )

        except subprocess.CalledProcessError as e:
            msg = f"Tauri dashboard error: {e}"
            raise CommandError(msg) from e
        except KeyboardInterrupt:
            self.print_info("\nShutting down Tauri dashboard...")
        finally:
            os.chdir(original_cwd)


class DashboardListCommand(BaseCommand):
    """List available dashboard interfaces and their status."""

    def __init__(self) -> None:
        super().__init__()
        self.env = DashboardEnvironment()

    def execute(self, **kwargs: Any) -> dict:  # noqa: ARG002, ANN401
        """Execute the list command.

        Returns:
        Dict containing.
        """
        self.print_info("📋 Available Dashboard Interfaces:\n")

        deps = check_dependencies("tauri")

        interfaces = [
            ("tui", "Terminal User Interface", "Rich-based terminal dashboard", True),
            ("web", "Web Interface", "Browser-based dashboard", True),
            (
                "tauri",
                "Desktop Application",
                "Native desktop app with Svelte frontend",
                deps["tauri"],
            ),
        ]

        for iface, name, description, available in interfaces:
            status = "✅ Available" if available else "❌ Not Available"
            self.print_info(f"  {iface.upper():<6} | {name:<20} | {description:<40} | {status}")

        self.print_info(f"\n🔍 Recommended interface: {self.env.get_recommended_interface()}")

        # Environment info
        self.print_info("\n🖥️  Environment Detection:")
        self.print_info(f"  GUI Available:     {'Yes' if self.env.is_gui_available() else 'No'}")
        self.print_info(f"  SSH Session:       {'Yes' if self.env.is_ssh_session() else 'No'}")
        self.print_info(f"  Terminal Capable:  {'Yes' if self.env.is_terminal_capable() else 'No'}")

        return {
            "interfaces": interfaces,
            "recommended": self.env.get_recommended_interface(),
            "environment": {
                "gui_available": self.env.is_gui_available(),
                "ssh_session": self.env.is_ssh_session(),
                "terminal_capable": self.env.is_terminal_capable(),
            },
        }


class DashboardBuildCommand(BaseCommand):
    """Build dashboard for production deployment."""

    def execute(self, interface: str = "tauri", **kwargs: Any) -> dict:  # noqa: ARG002, ANN401
        """Execute the build command.

        Returns:
        Dict containing.
        """
        self.print_info(f"🔨 Building {interface} dashboard for production...")

        if interface == "tauri":
            dashboard_path = Path(__file__).parent.parent / "tauri-dashboard"

            if not dashboard_path.exists():
                msg = f"Tauri dashboard not found at: {dashboard_path}"
                raise CommandError(msg)

            original_cwd = os.getcwd()
            os.chdir(dashboard_path)

            try:
                self.print_info("Building Tauri application...")
                subprocess.run(["npm", "run", "tauri", "build"], check=True)  # nosec
                self.print_success("Tauri build completed successfully!")

                # Show build output location
                build_dir = dashboard_path / "src-tauri" / "target" / "release"
                if build_dir.exists():
                    self.print_info(f"📁 Build output: {build_dir}")

                return {"success": True, "build_dir": str(build_dir)}

            except subprocess.CalledProcessError as e:
                msg = f"Build failed: {e}"
                raise CommandError(msg) from e
            finally:
                os.chdir(original_cwd)

        elif interface == "web":
            self.print_info("Web dashboard uses runtime generation - no build required")
            self.print_success("Web interface is ready for deployment")
            return {"success": True, "ready": True}

        else:
            msg = f"Unknown interface: {interface}"
            raise CommandError(msg)


@click.group(name="dashboard")
def dashboard_group() -> None:
    """Dashboard interface management commands."""


@dashboard_group.command()
@click.option(
    "--interface",
    "-i",
    type=click.Choice(["auto", "tui", "web", "tauri"], case_sensitive=False),
    default="auto",
    help="Dashboard interface to use",
)
@click.option("--host", "-h", default="localhost", help="Web dashboard host (web only)")
@click.option(
    "--port",
    "-p",
    default=8000,
    type=int,
    help="Web dashboard port (web only)",
)
@click.option("--theme", "-t", help="Dashboard theme")
@click.option("--dev", is_flag=True, default=False, help="Run in development mode")
@click.option("--detach", "-d", is_flag=True, default=False, help="Run in background")
def run(interface: str, host: str, port: int, theme: str | None, dev: bool, detach: bool) -> None:  # noqa: FBT001
    """Run the dashboard with specified interface."""
    command = DashboardRunCommand()
    command.run(interface=interface, host=host, port=port, theme=theme, dev=dev, detach=detach)


@dashboard_group.command()
def list_interfaces() -> None:
    """List available dashboard interfaces and their status."""
    command = DashboardListCommand()
    command.run()


# Add ls as an alias for list-interfaces
@dashboard_group.command()
def ls() -> None:
    """Alias for 'list-interfaces' command."""
    ctx = click.get_current_context()
    ctx.invoke(list_interfaces)


@dashboard_group.command()
@click.option(
    "--interface",
    "-i",
    type=click.Choice(["web", "tauri"], case_sensitive=False),
    default="tauri",
    help="Interface to build",
)
def build(interface: str) -> None:
    """Build dashboard for production deployment."""
    command = DashboardBuildCommand()
    command.run(interface=interface)


# Backward compatibility: keep the original dashboard command
@click.command()
@click.option("--port", "-p", default=1420, type=int, help="Port for Tauri dev server")
@click.option("--dev", is_flag=True, default=False, help="Run in development mode")
def dashboard(port: int, dev: bool) -> None:  # noqa: FBT001
    """Legacy dashboard command (launches Tauri interface)."""
    click.echo("⚠️  Using legacy dashboard command. Consider using 'yesman dashboard run' for more options.")
    command = DashboardRunCommand()
    command.run(interface="tauri", port=port, dev=dev)


# Export both the group and legacy command
__all__ = ["dashboard", "dashboard_group"]
