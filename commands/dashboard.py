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
    
    # Set environment variables to suppress WebKit warnings
    env = os.environ.copy()
    env['G_MESSAGES_DEBUG'] = ''  # Suppress GLib debug messages
    env['WEBKIT_DISABLE_COMPOSITING_MODE'] = '1'  # Suppress WebKit warnings
    env['GST_DEBUG'] = '0'  # Suppress GStreamer debug output
    # Redirect stderr to suppress deprecation warnings
    env['PYTHONWARNINGS'] = 'ignore'
    
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
            
            # Find the executable (platform dependent)
            app_bundle = None
            executable = None
            
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
            
            # Check if we have a valid executable or app bundle
            if executable and executable.exists():
                cmd = [str(executable)]
            elif app_bundle and app_bundle.exists():
                cmd = ["open", str(app_bundle)]
            else:
                click.echo("Built executable not found. Running in dev mode instead...")
                cmd = ["npm", "run", "tauri", "dev"]
        
        # Run the command and suppress WebKit warnings
        with open(os.devnull, 'w') as devnull:
            subprocess.run(cmd, env=env, stderr=subprocess.PIPE, check=True)
        
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