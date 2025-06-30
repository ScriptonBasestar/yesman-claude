import click
import sys
import subprocess
from pathlib import Path
from libs.dashboard import run_dashboard

@click.command()
@click.option('--refresh', '-r', default=2.0, type=float, help='Refresh interval in seconds (default: 2.0)')
@click.option('--tui', is_flag=True, help='Use TUI dashboard instead of web dashboard')
@click.option('--port', '-p', default=8501, type=int, help='Port for web dashboard (default: 8501)')
@click.option('--host', default='localhost', help='Host for web dashboard (default: localhost)')
def dashboard(refresh, tui, port, host):
    """Run dashboard to monitor all yesman sessions (Streamlit web by default, --tui for terminal UI)"""
    if tui:
        # Use TUI dashboard
        click.echo("Starting yesman TUI dashboard...")
        try:
            run_dashboard(refresh)
        except KeyboardInterrupt:
            pass  # Already handled in run_dashboard
        except Exception as e:
            click.echo(f"TUI Dashboard error: {e}", err=True)
            sys.exit(1)
    else:
        # Use Streamlit web dashboard
        try:
            import streamlit
        except ImportError:
            click.echo("Streamlit not available. Install with: pip install streamlit", err=True)
            sys.exit(1)
        
        # Get the streamlit app path
        app_path = Path(__file__).parent.parent / "libs" / "streamlit_dashboard" / "app.py"
        
        if not app_path.exists():
            click.echo(f"Streamlit app not found at: {app_path}", err=True)
            sys.exit(1)
        
        click.echo(f"Starting yesman Streamlit dashboard on http://{host}:{port}")
        
        try:
            # Run streamlit with custom config
            cmd = [
                "streamlit", "run", str(app_path),
                "--server.port", str(port),
                "--server.address", host,
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
                "--theme.base", "dark"
            ]
            
            subprocess.run(cmd, check=True)
            
        except subprocess.CalledProcessError as e:
            click.echo(f"Streamlit dashboard error: {e}", err=True)
            sys.exit(1)
        except KeyboardInterrupt:
            click.echo("\nShutting down Streamlit dashboard...")
        except Exception as e:
            click.echo(f"Dashboard error: {e}", err=True)
            sys.exit(1)