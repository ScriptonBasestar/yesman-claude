import click
from libs.dashboard import run_dashboard

@click.command()
@click.option('--refresh', '-r', default=2.0, type=float, help='Refresh interval in seconds (default: 2.0)')
def dashboard(refresh):
    """Run dashboard to monitor all yesman sessions"""
    click.echo("Starting yesman dashboard...")
    try:
        run_dashboard()
    except KeyboardInterrupt:
        pass  # Already handled in run_dashboard
    except Exception as e:
        click.echo(f"Dashboard error: {e}", err=True)
        raise click.Exit(1)