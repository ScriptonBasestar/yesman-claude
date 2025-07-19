#!/usr/bin/env python3
"""Improved ls command using base command class."""

from typing import Any

import click

from libs.core.base_command import BaseCommand, ConfigCommandMixin, OutputFormatterMixin, SessionCommandMixin


class LsCommand(BaseCommand, ConfigCommandMixin, OutputFormatterMixin, SessionCommandMixin):
    """List all available projects and templates."""

    def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the command."""
        # Extract parameters from kwargs

        output_format = kwargs.get("output_format", "table")
        """Execute the ls command.

        Args:
            output_format: Output format (table, json, yaml)

        Returns:
            Dictionary with templates and projects data
        """
        # Get templates
        templates = self._get_templates()

        # Get projects
        projects = self._get_projects()

        # Format and display output
        result = {
            "templates": templates,
            "projects": projects,
        }

        self._display_output(result, output_format)

        return result

    def _get_templates(self) -> list[str]:
        """Get available session templates."""
        try:
            return self.tmux_manager.get_templates()
        except Exception as e:
            self.logger.error(f"Failed to get templates: {e}")
            return []

    def _get_projects(self) -> list[dict[str, Any]]:
        """Get configured projects with details."""
        try:
            projects_config = self.load_projects_config()
            sessions = projects_config.get("sessions", {})

            projects = []
            for project_name, project_conf in sessions.items():
                template_name = project_conf.get("template_name", "none")
                override = project_conf.get("override", {})
                session_name = override.get("session_name", project_name)

                projects.append(
                    {
                        "name": project_name,
                        "template": template_name,
                        "session": session_name,
                        "windows": len(override.get("windows", [])),
                        "status": self._get_project_status(session_name),
                    }
                )

            return projects

        except Exception as e:
            self.logger.error(f"Failed to get projects: {e}")
            return []

    def _get_project_status(self, session_name: str) -> str:
        """Get the current status of a project session."""
        try:
            if self.session_exists(session_name):
                return "running"
            else:
                return "stopped"
        except Exception:
            return "unknown"

    def _display_output(self, data: dict[str, Any], output_format: str) -> None:
        """Display output in specified format."""
        if output_format == "json":
            click.echo(self.format_json(data))
            return
        elif output_format == "yaml":
            click.echo(self.format_yaml(data))
            return

        # Default table format
        self._display_table_format(data)

    def _display_table_format(self, data: dict[str, Any]) -> None:
        """Display output in table format."""
        templates = data["templates"]
        projects = data["projects"]

        # Display templates
        click.echo("Available session templates:")
        if not templates:
            self.print_warning("No session templates found in ~/.scripton/yesman/templates/")
        else:
            for template_name in templates:
                click.echo(f"  - {template_name}")

        click.echo()

        # Display projects
        click.echo("Configured projects:")
        if not projects:
            self.print_warning("No projects configured in ~/.scripton/yesman/projects.yaml")
        else:
            headers = ["name", "template", "session", "windows", "status"]
            table = self.format_table(projects, headers)
            click.echo(table)


@click.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def ls(output_format: str):
    """List all available projects and templates."""
    command = LsCommand()
    command.run(output_format=output_format)


if __name__ == "__main__":
    ls()
