from typing import Optional
import click
import sys
from libs.controller import run_controller

@click.command()
@click.argument('session_name')
@click.option('--pane-id', help='Specific pane ID to monitor (optional)')
def controller(session_name: str, pane_id: Optional[str] = None):
    """Run controller for a specific session to monitor and control Claude"""
    click.echo(f"Starting controller for session: {session_name}")
    try:
        run_controller(session_name, pane_id)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nController stopped.")
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)