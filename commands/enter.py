import click
import subprocess
import libtmux
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager

@click.command()
@click.argument('session_name', required=False)
@click.option('--list', '-l', 'list_sessions', is_flag=True, help='List available sessions')
def enter(session_name, list_sessions):
    """Enter (attach to) a tmux session"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    server = libtmux.Server()
    
    if list_sessions:
        # Show available sessions
        tmux_manager.list_running_sessions()
        return
    
    # If no session name provided, show available sessions and prompt
    if not session_name:
        # Get all running sessions
        running_sessions = []
        projects = tmux_manager.load_projects().get("sessions", {})
        
        for project_name, project_conf in projects.items():
            override = project_conf.get("override", {})
            actual_session_name = override.get("session_name", project_name)
            
            # Check if session exists
            if server.find_where({"session_name": actual_session_name}):
                running_sessions.append({
                    'project': project_name,
                    'session': actual_session_name
                })
        
        if not running_sessions:
            click.echo("No running yesman sessions found.")
            click.echo("Run 'yesman setup' to create sessions.")
            return
        
        # Display available sessions
        click.echo("Available sessions:")
        for i, sess in enumerate(running_sessions, 1):
            click.echo(f"  [{i}] {sess['project']} (session: {sess['session']})")
        
        # Prompt for selection
        choice = click.prompt("Select session number", type=int)
        if 1 <= choice <= len(running_sessions):
            session_name = running_sessions[choice - 1]['session']
        else:
            click.echo("Invalid selection")
            return
    
    # Check if the session exists
    if not server.find_where({"session_name": session_name}):
        # Try to find by project name
        projects = tmux_manager.load_projects().get("sessions", {})
        actual_session_name = None
        
        for project_name, project_conf in projects.items():
            if project_name == session_name:
                override = project_conf.get("override", {})
                actual_session_name = override.get("session_name", project_name)
                break
        
        if actual_session_name and server.find_where({"session_name": actual_session_name}):
            session_name = actual_session_name
        else:
            click.echo(f"Session '{session_name}' not found.")
            click.echo("Available sessions:")
            tmux_manager.list_running_sessions()
            return
    
    # Attach to the session
    click.echo(f"Attaching to session: {session_name}")
    
    # Check if we're already in a tmux session
    if 'TMUX' in subprocess.os.environ:
        # Switch to the session
        subprocess.run(["tmux", "switch-client", "-t", session_name])
    else:
        # Attach to the session
        subprocess.run(["tmux", "attach-session", "-t", session_name])