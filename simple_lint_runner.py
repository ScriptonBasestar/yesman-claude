#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Simple lint runner to check for issues."""

import os
import subprocess

os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")


def run_single_command(cmd, description):
    """Run a single command and capture output."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"{'=' * 60}")

    try:
        # nosec B602 - shell=True is intentional for this debug script
        result = subprocess.run(cmd, check=False, shell=True, capture_output=True, text=True, timeout=60)
        print(f"Exit code: {result.returncode}")

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


# Run ruff check
print("Running individual lint commands...")

# Try to run ruff check
success1 = run_single_command("python -m ruff check --version", "Check ruff version")
success2 = run_single_command("python -m ruff check libs/ --config pyproject.toml", "Ruff check on libs")
success3 = run_single_command("python -m ruff check commands/ --config pyproject.toml", "Ruff check on commands")

print(f"\nRuff version check: {'PASS' if success1 else 'FAIL'}")
print(f"Ruff libs check: {'PASS' if success2 else 'FAIL'}")
print(f"Ruff commands check: {'PASS' if success3 else 'FAIL'}")
