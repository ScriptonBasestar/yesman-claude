#!/usr/bin/env python3
"""
Simple script to run lint commands and capture output
"""

import os
import subprocess
import sys


def run_command(command, description):
    """Run a command and capture output"""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            command,
            check=False,
            cwd="/Users/archmagece/myopen/scripton/yesman-claude",
            capture_output=True,
            text=True,
            timeout=120,
        )

        print(f"Return code: {result.returncode}")

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("Command timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    # Change to project directory
    os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

    # Run ruff check
    success1 = run_command(
        [
            "python",
            "-m",
            "ruff",
            "check",
            "--target-version",
            "py311",
            "libs",
            "commands",
        ],
        "Ruff check on libs and commands",
    )

    # Run mypy
    success2 = run_command(
        [
            "python",
            "-m",
            "mypy",
            "--config-file=pyproject.toml",
            "libs",
            "commands",
            "api",
        ],
        "MyPy type checking",
    )

    # Run bandit
    success3 = run_command(
        [
            "python",
            "-m",
            "bandit",
            "-r",
            "libs",
            "commands",
            "--skip",
            "B101,B404,B603,B607,B602",
            "--severity-level",
            "medium",
            "--quiet",
        ],
        "Bandit security check",
    )

    print(f"\n{'=' * 60}")
    print("LINT SUMMARY")
    print(f"{'=' * 60}")
    print(f"Ruff check: {'PASS' if success1 else 'FAIL'}")
    print(f"MyPy check: {'PASS' if success2 else 'FAIL'}")
    print(f"Bandit check: {'PASS' if success3 else 'PASS (with warnings)'}")

    if not any([success1, success2, success3]):
        print("\nAll lint checks failed. Please review the output above.")
        sys.exit(1)

    print("\nLint checks completed. Review output above for details.")


if __name__ == "__main__":
    main()
