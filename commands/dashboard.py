import click
import sys
import subprocess
import os
from pathlib import Path

@click.command()
@click.option('--port', '-p', default=1420, type=int, help='Port for Tauri dev server (default: 1420)')
@click.option('--dev', is_flag=True, default=False, help='Run in development mode')
def dashboard(port, dev):
    """Run Tauri + SvelteKit dashboard to monitor all yesman sessions"""
    
    # Get the tauri dashboard path
    dashboard_path = Path(__file__).parent.parent / "tauri-dashboard"
    
    if not dashboard_path.exists():
        click.echo(f"Tauri dashboard not found at: {dashboard_path}", err=True)
        click.echo("Make sure the tauri-dashboard directory exists and is properly set up.")
        sys.exit(1)
    
    # Change to tauri dashboard directory
    original_cwd = os.getcwd()
    os.chdir(dashboard_path)
    
    try:
        if dev:
            click.echo(f"Starting yesman Tauri dashboard in development mode...")
            # Run tauri dev which starts both frontend and backend
            cmd = ["npm", "run", "tauri", "dev"]
        else:
            click.echo(f"Starting yesman Tauri dashboard...")
            # Check if built app exists, if not build it first
            if not (dashboard_path / "src-tauri" / "target" / "release").exists():
                click.echo("Building Tauri app for first run...")
                subprocess.run(["npm", "run", "tauri", "build"], check=True)
            
            # Run the built executable
            build_dir = dashboard_path / "src-tauri" / "target" / "release"
            executable = None
            
            # Find the executable (platform dependent)
            if sys.platform == "darwin":  # macOS
                app_bundle = build_dir / "bundle" / "macos" / "yesman-claude.app"
                if app_bundle.exists():
                    cmd = ["open", str(app_bundle)]
                else:
                    executable = build_dir / "yesman-claude"
            elif sys.platform == "win32":  # Windows
                executable = build_dir / "yesman-claude.exe"
            else:  # Linux
                executable = build_dir / "yesman-claude"
            
            if executable and executable.exists():
                cmd = [str(executable)]
            elif not app_bundle.exists():
                click.echo("Built executable not found. Running in dev mode instead...")
                cmd = ["npm", "run", "tauri", "dev"]
        
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        click.echo(f"Tauri dashboard error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nShutting down Tauri dashboard...")
    except Exception as e:
        click.echo(f"Dashboard error: {e}", err=True)
        sys.exit(1)
    finally:
        # Restore original working directory
        os.chdir(original_cwd)