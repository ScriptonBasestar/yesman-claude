#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Script to run ruff commands using subprocess directly."""

import subprocess


def run_command(cmd, description=""):
    """Run a command and return success status."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            cmd,
            check=False,
            cwd="/Users/archmagece/myopen/scripton/yesman-claude",
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"Return code: {result.returncode}")
        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("Command timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Main function."""
    print("Starting ruff lint fixes...")

    # 1. Fix import ordering
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
        ],
        "1. Fix import ordering",
    )

    # 2. Format code
    success2 = run_command(
        ["uv", "run", "ruff", "format", "libs", "commands", "api", "tests"],
        "2. Format code",
    )

    # 3. Final check
    success3 = run_command(
        ["uv", "run", "ruff", "check", "libs", "commands", "api", "tests"],
        "3. Final lint check",
    )

    print(f"\n{'=' * 60}")
    print("SUMMARY:")
    print(f"Import fixes: {'✓' if success1 else '✗'}")
    print(f"Formatting: {'✓' if success2 else '✗'}")
    print(f"Final check: {'✓' if success3 else '✗'}")
    print(f"{'=' * 60}")

    if success1 and success2:
        print("\nAll auto-fixes completed successfully!")
        if not success3:
            print("Some lint issues remain and may require manual fixing.")
    else:
        print("\nSome auto-fixes failed. Check the output above for details.")


if __name__ == "__main__":
    main()
