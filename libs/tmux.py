"""Tmux session template generation utilities.

This module provides utilities for generating tmux session configurations
from templates using Jinja2 template rendering.
"""

from pathlib import Path

import tmuxp
import yaml
from jinja2 import Template


def generate(session_name: str, start_directory: str):
    """Generate a tmux session configuration from a template.

    Args:
        session_name: Name for the tmux session
        start_directory: Starting directory for the session

    Returns:
        dict: Generated tmux session configuration
    """
    template_path = Path(__file__).parent / "session_template.yaml"
    with open(template_path, encoding="utf-8") as f:
        raw = f.read()

    # 템플릿 렌더링
    rendered = Template(raw).render(
        session_name=session_name,
        start_directory=start_directory,
    )

    # YAML → dict
    return yaml.safe_load(rendered)


if __name__ == "__main__":
    config = generate(session_name="my-uv-project", start_directory="~/workspace/uv")
    tmuxp.cli.load_workspace(config)
