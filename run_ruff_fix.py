#!/usr/bin/env python3
"""Simple script to run ruff fix commands."""

import os
import subprocess


def run_ruff_command(args):
    """Run a ruff command with uv."""
    cmd = ["uv", "run", "ruff"] + args
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        print("Output:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False


# Change to project directory
os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

print("1. Fixing import ordering...")
run_ruff_command(
    [
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
    ]
)

print("\n2. Formatting code...")
run_ruff_command(
    [
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
    ]
)

print("\n3. Checking remaining issues...")
run_ruff_command(
    [
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
    ]
)

print("\nDone!")
