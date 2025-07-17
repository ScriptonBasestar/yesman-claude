#!/usr/bin/env python3
"""
Script to fix lint issues using ruff
"""

import os
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and print its output"""
    print(f"\n{'=' * 50}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'=' * 50}")

    try:
        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, cwd=os.getcwd()
        )

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"Return code: {result.returncode}")
        return result.returncode == 0

    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Main function to run lint fixes"""

    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("Error: pyproject.toml not found. Please run from project root.")
        sys.exit(1)

    print("Starting lint fixes...")

    # Step 1: Fix import ordering
    success1 = run_command(
        [
            "uv",
            "run",
            "ruff",
            "check",
            "libs",
            "commands",
            "api",
            "tests",
            "--select",
            "I",
            "--fix",
            "--exclude",
            "migrations",
            "--exclude",
            "node_modules",
            "--exclude",
            "examples",
        ],
        "Fix import ordering and other auto-fixable issues",
    )

    # Step 2: Format code
    success2 = run_command(
        [
            "uv",
            "run",
            "ruff",
            "format",
            "libs",
            "commands",
            "api",
            "tests",
            "--exclude",
            "migrations",
            "--exclude",
            "node_modules",
            "--exclude",
            "examples",
        ],
        "Format code with ruff",
    )

    # Step 3: Check remaining issues
    success3 = run_command(
        [
            "uv",
            "run",
            "ruff",
            "check",
            "libs",
            "commands",
            "api",
            "tests",
            "--exclude",
            "migrations",
            "--exclude",
            "node_modules",
            "--exclude",
            "examples",
        ],
        "Check remaining lint issues",
    )

    print(f"\n{'=' * 50}")
    print("SUMMARY:")
    print(f"Import fixes: {'✓' if success1 else '✗'}")
    print(f"Formatting: {'✓' if success2 else '✗'}")
    print(f"Final check: {'✓' if success3 else '✗'}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
