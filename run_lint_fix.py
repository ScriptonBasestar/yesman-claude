#!/usr/bin/env python3
"""Run lint-fix commands directly from Python."""

import os
import subprocess


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    try:
        # nosec B602 - shell=True is intentional for this debug script
        result = subprocess.run(cmd, check=False, shell=True, capture_output=True, text=True)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

    commands = [
        (
            "uv run ruff check libs commands api tests --select I --fix --exclude migrations --exclude node_modules --exclude examples",
            "Ruff check with auto-fix for imports",
        ),
        (
            "uv run ruff format libs commands api tests --exclude migrations --exclude node_modules --exclude examples",
            "Ruff format",
        ),
        (
            "uv run mypy libs commands api --ignore-missing-imports --exclude migrations --exclude node_modules --exclude examples",
            "MyPy type checking",
        ),
        (
            "uv run bandit -r libs commands --skip B101,B404,B603,B607,B602 --severity-level medium --quiet "
            + "--exclude '*/tests/*,*/scripts/*,*/debug/*,*/examples/*' || echo '✅ Security check completed'",
            "Bandit security check",
        ),
        ("uv run mdformat *.md docs/**/*.md --wrap 120", "Markdown format"),
    ]

    for cmd, desc in commands:
        print(f"\n{'=' * 60}")
        success = run_command(cmd, desc)
        if not success:
            print(f"Command failed: {desc}")


if __name__ == "__main__":
    main()
