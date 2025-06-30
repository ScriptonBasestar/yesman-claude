import click
import sys
import subprocess
from pathlib import Path

@click.command()
@click.option('--port', '-p', default=8501, type=int, help='Port for web dashboard (default: 8501)')
@click.option('--host', default='localhost', help='Host for web dashboard (default: localhost)')
def dashboard(port, host):
    """Run Streamlit web dashboard to monitor all yesman sessions"""
    # Check if Streamlit is available
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