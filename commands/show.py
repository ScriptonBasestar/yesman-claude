import click

from libs.core.base_command import BaseCommand, SessionCommandMixin


class ShowCommand(BaseCommand, SessionCommandMixin):
    """List all running tmux sessions"""

    def execute(self, **kwargs) -> dict:
        """Execute the show command"""
        self.tmux_manager.list_running_sessions()
        return {"success": True, "action": "list_sessions"}


@click.command()
def show():
    """List all running tmux sessions"""
    command = ShowCommand()
    command.run()
