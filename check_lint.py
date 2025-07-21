#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


import os
import subprocess
import sys

# Change to the project directory
os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")


def run_command(cmd, description):
    """Run a command and capture output."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=120)

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    # Commands to run for linting
    commands = [
        (
            [
                "uv",
                "run",
                "ruff",
                "check",
                "libs",
                "commands",
                "api",
                "tests",
                "--diff",
                "--exclude",
                "migrations",
                "--exclude",
                "node_modules",
                "--exclude",
                "examples",
            ],
            "Ruff check",
        ),
        (
            [
                "uv",
                "run",
                "mypy",
                "libs",
                "commands",
                "api",
                "--ignore-missing-imports",
                "--exclude",
                "migrations",
                "--exclude",
                "node_modules",
                "--exclude",
                "examples",
            ],
            "MyPy type checking",
        ),
        (
            [
                "uv",
                "run",
                "bandit",
                "-r",
                "libs",
                "commands",
                "api",
                "--skip",
                "B101,B404,B603,B607,B602",
                "--severity-level",
                "medium",
                "--quiet",
                "--exclude",
                "*/tests/*,*/scripts/*,*/debug/*,*/examples/*",
            ],
            "Bandit security check",
        ),
    ]

    all_passed = True

    for cmd, description in commands:
        success = run_command(cmd, description)
        if not success:
            all_passed = False

    print(f"\n{'=' * 60}")
    print("LINT SUMMARY")
    print(f"{'=' * 60}")

    if all_passed:
        print("✅ All lint checks passed!")
    else:
        print("❌ Some lint checks failed!")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
