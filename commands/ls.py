import click
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager

@click.command()
def ls():
    """List all available projects"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    
    # List templates
    click.echo("Available session templates:")
    templates = tmux_manager.get_templates()
    
    if not templates:
        click.echo("No session templates found in ~/.yesman/templates/")
        return
    
    for template_name in templates:
        click.echo(f"  - {template_name}")
    
    # List projects
    projects = tmux_manager.load_projects().get("sessions", {})
    if projects:
        click.echo("Configured projects:")
        for project_name, project_conf in projects.items():
            template = project_conf.get("template_name", "N/A")
            override = project_conf.get("override", {})
            session_name = override.get("session_name", project_name)
            click.echo(f"  - {project_name} (template: {template}, session: {session_name})")
