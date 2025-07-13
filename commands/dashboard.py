"""Dashboard interface management commands."""

import os
import platform
import shutil
import subprocess  # nosec
import sys
import time
import webbrowser
from pathlib import Path
from typing import Dict, Optional

import click


class DashboardEnvironment:
    """Detects and manages dashboard environment capabilities.""" ""

    @staticmethod
    def is_gui_available() -> bool:
        """Check if GUI environment is available.""" ""
        if platform.system() == "Darwin":  # macOS
            return True
        elif platform.system() == "Windows":
            return True
        else:  # Linux/Unix
            return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    @staticmethod
    def is_ssh_session() -> bool:
        """Check if running in SSH session.""" ""
        return bool(os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"))

    @staticmethod
    def is_terminal_capable() -> bool:
        """Check if terminal supports rich output.""" ""
        return sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"

    @staticmethod
    def get_recommended_interface() -> str:
        """Get recommended interface based on environment.""" ""
        if DashboardEnvironment.is_ssh_session():
            return "tui"
        elif DashboardEnvironment.is_gui_available():
            return "tauri"
        elif DashboardEnvironment.is_terminal_capable():
            return "tui"
        else:
            return "web"


def check_dependencies(interface: str) -> Dict[str, bool]:
    """Check if required dependencies are available for interface.""" ""
    deps = {
        "tui": True,  # Always available (uses rich)
        "web": True,  # Uses built-in server
        "tauri": False,
    }

    if interface == "tauri":
        dashboard_path = Path(__file__).parent.parent / "tauri-dashboard"
        deps["tauri"] = (
            dashboard_path.exists()
            and (dashboard_path / "package.json").exists()
            and shutil.which("npm") is not None
        )

    return deps


def launch_tui_dashboard(theme: Optional[str] = None, dev: bool = False) -> None:
    """Launch TUI-based dashboard interface.""" ""
    click.echo("🖥️  Starting TUI Dashboard...")

    try:
        # Import rich for TUI interface
        from rich.console import Console
        from rich.layout import Layout
        from rich.live import Live
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        # Create sample dashboard layout
        def create_dashboard_layout():
            layout = Layout()

            # Create header
            header = Panel(
                "[bold blue]Yesman Claude TUI Dashboard[/bold blue]\n"
                "[dim]Real-time session monitoring and management[/dim]",
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
        click.echo(f"TUI dependencies not available: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"TUI dashboard error: {e}", err=True)
        sys.exit(1)


def launch_web_dashboard(
    host: str = "localhost",
    port: int = 8080,
    theme: Optional[str] = None,
    dev: bool = False,
    detach: bool = False,
) -> None:
    """Launch web-based dashboard interface.""" ""
    click.echo(f"🌐 Starting Web Dashboard on http://{host}:{port}...")

    try:
        # Check if port is available
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            click.echo(
                f"Port {port} is already in use. Try a different port with -p option.",
                err=True,
            )
            sys.exit(1)

        # Start FastAPI server
        api_path = Path(__file__).parent.parent / "api"
        if not api_path.exists():
            click.echo(
                "Web dashboard API not found. Creating simple HTML interface...",
                err=True,
            )

            # Create simple HTML dashboard
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Yesman Claude Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: #2563eb;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2563eb;
        }}
        .status {{
            margin-top: 20px;
            padding: 15px;
            background: #f0f9ff;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Yesman Claude Web Dashboard</h1>
            <p>Real-time session monitoring and management</p>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <h3>Active Sessions</h3>
                <div class="metric-value">3</div>
                <div>🟢 All systems operational</div>
            </div>

            <div class="metric-card">
                <h3>CPU Usage</h3>
                <div class="metric-value">25%</div>
                <div>🟢 Low usage</div>
            </div>

            <div class="metric-card">
                <h3>Memory Usage</h3>
                <div class="metric-value">45%</div>
                <div>🟡 Moderate usage</div>
            </div>

            <div class="metric-card">
                <h3>Claude Instances</h3>
                <div class="metric-value">2</div>
                <div>🟢 Active and responding</div>
            </div>
        </div>

        <div class="status">
            <h3>📊 Dashboard Status</h3>
            <p><strong>Interface:</strong> Web Dashboard</p>
            <p><strong>Host:</strong> {host}:{port}</p>
            <p><strong>Theme:</strong> {theme or 'default'}</p>
            <p><strong>Mode:</strong> {'Development' if dev else 'Production'}</p>
        </div>
    </div>

    <script>
        // Auto-refresh every 5 seconds
        setTimeout(() => location.reload(), 5000);
    </script>
</body>
</html>
"""

            # Start simple HTTP server
            import http.server
            import socketserver
            import threading

            class DashboardHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(html_content.encode())

            def run_server():
                with socketserver.TCPServer((host, port), DashboardHandler) as httpd:
                    httpd.serve_forever()

            if detach:
                # Run in background
                server_thread = threading.Thread(target=run_server, daemon=True)
                server_thread.start()
                click.echo(
                    f"Web dashboard started in background at http://{host}:{port}"
                )

                # Open browser
                webbrowser.open(f"http://{host}:{port}")

                # Keep main thread alive
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    click.echo("Shutting down web dashboard...")
            else:
                click.echo(f"Web dashboard running at http://{host}:{port}")
                click.echo("Press Ctrl+C to stop")

                # Open browser
                webbrowser.open(f"http://{host}:{port}")

                try:
                    run_server()
                except KeyboardInterrupt:
                    click.echo("\nShutting down web dashboard...")
        else:
            # Use FastAPI server
            try:
                import threading
                import time

                import uvicorn

                # Show the URL before starting
                dashboard_url = f"http://{host}:{port}"
                click.echo(f"🌐 FastAPI server starting at {dashboard_url}")
                click.echo("📊 Dashboard will be available at the URL above")

                if not detach:
                    # Open browser after a short delay in a separate thread
                    def open_browser():
                        time.sleep(2)  # Wait for server to start
                        try:
                            webbrowser.open(dashboard_url)
                            click.echo(f"🔗 Opening browser to {dashboard_url}")
                        except Exception as e:
                            click.echo(f"Could not open browser automatically: {e}")
                            click.echo(
                                f"Please open {dashboard_url} manually in your browser"
                            )

                    threading.Thread(target=open_browser, daemon=True).start()

                uvicorn.run("api.main:app", host=host, port=port, reload=dev)

            except ImportError:
                click.echo(
                    "FastAPI/uvicorn not available. "
                    "Install with: uv add fastapi uvicorn",
                    err=True,
                )
                sys.exit(1)

    except Exception as e:
        click.echo(f"Web dashboard error: {e}", err=True)
        sys.exit(1)


def launch_tauri_dashboard(
    theme: Optional[str] = None, dev: bool = False, detach: bool = False
) -> None:
    """Launch Tauri-based desktop dashboard interface.""" ""
    click.echo("🖥️  Starting Tauri Desktop Dashboard...")

    # Get the tauri dashboard path
    dashboard_path = Path(__file__).parent.parent / "tauri-dashboard"

    if not dashboard_path.exists():
        click.echo(f"Tauri dashboard not found at: {dashboard_path}", err=True)
        click.echo(
            "Make sure the tauri-dashboard directory exists and is properly set up."
        )
        sys.exit(1)

    # Check npm availability
    if not shutil.which("npm"):
        click.echo("npm not found. Please install Node.js and npm.", err=True)
        sys.exit(1)

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
            click.echo("Starting Tauri dashboard in development mode...")
            cmd = ["npm", "run", "tauri", "dev"]
        else:
            click.echo("Starting Tauri dashboard...")
            # Check if built app exists
            build_dir = dashboard_path / "src-tauri" / "target" / "release"

            if not build_dir.exists():
                click.echo(
                    "⚠️  Release build not found. Switching to development mode..."
                )
                click.echo("Starting Tauri dashboard in development mode...")
                cmd = ["npm", "run", "tauri", "dev"]
            else:
                # Find the executable (platform dependent)
                if sys.platform == "darwin":  # macOS
                    app_bundle = build_dir / "bundle" / "macos" / "Yesman Dashboard.app"
                    if app_bundle.exists():
                        cmd = ["open", str(app_bundle)]
                    else:
                        cmd = [str(build_dir / "Yesman Dashboard")]
                elif sys.platform == "win32":  # Windows
                    cmd = [str(build_dir / "Yesman Dashboard.exe")]
                else:  # Linux
                    cmd = [str(build_dir / "yesman-tauri-dashboard")]

        # Run the command
        if detach:
            # Run in background
            process = subprocess.Popen(  # nosec
                cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            click.echo(f"Tauri dashboard started in background (PID: {process.pid})")
            return
        else:
            with open(os.devnull, "w"):
                subprocess.run(  # nosec
                    cmd, env=env, stderr=subprocess.PIPE, check=True
                )

    except subprocess.CalledProcessError as e:
        click.echo(f"Tauri dashboard error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nShutting down Tauri dashboard...")
    except Exception as e:
        click.echo(f"Tauri dashboard error: {e}", err=True)
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


@click.group(name="dashboard")
def dashboard_group():
    """Dashboard interface management commands.""" ""
    pass


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
    "--port", "-p", default=8080, type=int, help="Web dashboard port (web only)"
)
@click.option("--theme", "-t", help="Dashboard theme")
@click.option("--dev", is_flag=True, default=False, help="Run in development mode")
@click.option("--detach", "-d", is_flag=True, default=False, help="Run in background")
def run(interface, host, port, theme, dev, detach):
    """Run the dashboard with specified interface."""
    # Auto-detect interface if needed
    if interface == "auto":
        interface = DashboardEnvironment.get_recommended_interface()
        click.echo(f"🔍 Auto-detected interface: {interface}")

    # Check dependencies
    deps = check_dependencies(interface)
    if not deps.get(interface, False) and interface == "tauri":
        click.echo(f"❌ Dependencies not available for {interface} interface", err=True)
        click.echo("Available interfaces:")
        for iface, available in deps.items():
            status = "✅" if available else "❌"
            click.echo(f"  {status} {iface}")

        # Fallback to TUI if auto-detection
        if interface == DashboardEnvironment.get_recommended_interface():
            click.echo("Falling back to TUI interface...")
            interface = "tui"
        else:
            sys.exit(1)

    # Launch appropriate interface
    try:
        if interface == "tui":
            launch_tui_dashboard(theme=theme, dev=dev)
        elif interface == "web":
            launch_web_dashboard(
                host=host, port=port, theme=theme, dev=dev, detach=detach
            )
        elif interface == "tauri":
            launch_tauri_dashboard(theme=theme, dev=dev, detach=detach)
        else:
            click.echo(f"Unknown interface: {interface}", err=True)
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n👋 Dashboard shutdown complete")


@dashboard_group.command()
def list_interfaces():
    """List available dashboard interfaces and their status.""" ""
    click.echo("📋 Available Dashboard Interfaces:\n")

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
        click.echo(
            f"  {iface.upper():<6} | {name:<20} | " f"{description:<40} | {status}"
        )

    click.echo(
        "\n🔍 Recommended interface: "
        f"{DashboardEnvironment.get_recommended_interface()}"
    )

    # Environment info
    click.echo("\n🖥️  Environment Detection:")
    click.echo(
        "  GUI Available:     "
        f"{'Yes' if DashboardEnvironment.is_gui_available() else 'No'}"
    )
    click.echo(
        "  SSH Session:       "
        f"{'Yes' if DashboardEnvironment.is_ssh_session() else 'No'}"
    )
    click.echo(
        "  Terminal Capable:  "
        f"{'Yes' if DashboardEnvironment.is_terminal_capable() else 'No'}"
    )


# Add ls as an alias for list-interfaces
@dashboard_group.command()
def ls():
    """Alias for 'list-interfaces' command.""" ""
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
def build(interface):
    """Build dashboard for production deployment.""" ""
    click.echo(f"🔨 Building {interface} dashboard for production...")

    if interface == "tauri":
        dashboard_path = Path(__file__).parent.parent / "tauri-dashboard"

        if not dashboard_path.exists():
            click.echo(f"Tauri dashboard not found at: {dashboard_path}", err=True)
            sys.exit(1)

        original_cwd = os.getcwd()
        os.chdir(dashboard_path)

        try:
            click.echo("Building Tauri application...")
            subprocess.run(["npm", "run", "tauri", "build"], check=True)  # nosec
            click.echo("✅ Tauri build completed successfully!")

            # Show build output location
            build_dir = dashboard_path / "src-tauri" / "target" / "release"
            if build_dir.exists():
                click.echo(f"📁 Build output: {build_dir}")

        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Build failed: {e}", err=True)
            sys.exit(1)
        finally:
            os.chdir(original_cwd)

    elif interface == "web":
        click.echo("Web dashboard uses runtime generation - no build required")
        click.echo("✅ Web interface is ready for deployment")

    else:
        click.echo(f"Unknown interface: {interface}", err=True)
        sys.exit(1)


# Backward compatibility: keep the original dashboard command
@click.command()
@click.option("--port", "-p", default=1420, type=int, help="Port for Tauri dev server")
@click.option("--dev", is_flag=True, default=False, help="Run in development mode")
def dashboard(port, dev):
    """Legacy dashboard command (launches Tauri interface).""" ""
    click.echo(
        "⚠️  Using legacy dashboard command. "
        "Consider using 'yesman dashboard run' for more options."
    )
    launch_tauri_dashboard(dev=dev)


# Export both the group and legacy command
__all__ = ["dashboard_group", "dashboard"]
