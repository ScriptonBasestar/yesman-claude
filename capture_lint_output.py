#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Capture lint output by running commands manually."""

import os
import subprocess
from pathlib import Path


def run_command_safely(cmd, description, cwd=None):
    """Run a command and capture output safely."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'=' * 60}")

    try:
        # nosec B602 - shell=True is intentional for this debug script
        result = subprocess.run(
            cmd,
            check=False,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = []
        output.append(f"Exit Code: {result.returncode}")

        if result.stdout:
            output.append("\nSTDOUT:")
            output.append(result.stdout)

        if result.stderr:
            output.append("\nSTDERR:")
            output.append(result.stderr)

        print("\n".join(output))
        return result.returncode == 0, "\n".join(output)

    except subprocess.TimeoutExpired:
        msg = "Command timed out after 60 seconds"
        print(msg)
        return False, msg
    except Exception as e:
        msg = f"Error running command: {e}"
        print(msg)
        return False, msg


def main():
    """Main function to capture lint output."""
    project_path = "/Users/archmagece/myopen/scripton/yesman-claude"
    os.chdir(project_path)

    all_output = []

    # Check if tools are available
    print("Checking lint tools availability...")

    # Check ruff
    success, output = run_command_safely("python -m ruff --version", "Check ruff version")
    all_output.append(output)

    if success:
        # Try to run ruff check on individual directories
        success, output = run_command_safely("python -m ruff check libs --config pyproject.toml", "Ruff check libs")
        all_output.append(output)

        success, output = run_command_safely(
            "python -m ruff check commands --config pyproject.toml",
            "Ruff check commands",
        )
        all_output.append(output)

    # Check mypy
    success, output = run_command_safely("python -m mypy --version", "Check mypy version")
    all_output.append(output)

    if success:
        # Try to run mypy
        success, output = run_command_safely("python -m mypy libs --config-file pyproject.toml", "MyPy check libs")
        all_output.append(output)

        success, output = run_command_safely(
            "python -m mypy commands --config-file pyproject.toml",
            "MyPy check commands",
        )
        all_output.append(output)

    # Check bandit
    success, output = run_command_safely("python -m bandit --version", "Check bandit version")
    all_output.append(output)

    if success:
        # Try to run bandit
        success, output = run_command_safely(
            "python -m bandit -r libs --skip B101,B404,B603,B607,B602 --severity-level medium",
            "Bandit check libs",
        )
        all_output.append(output)

        success, output = run_command_safely(
            "python -m bandit -r commands --skip B101,B404,B603,B607,B602 --severity-level medium",
            "Bandit check commands",
        )
        all_output.append(output)

    # Save all output to file
    output_file = Path(project_path) / "lint_output.txt"
    with open(output_file, "w") as f:
        f.write("LINT OUTPUT CAPTURE\n")
        f.write("=" * 80 + "\n\n")
        f.write("\n".join(all_output))

    print(f"\nAll output saved to: {output_file}")
    print("You can now read the lint_output.txt file to see all lint errors.")


if __name__ == "__main__":
    main()
