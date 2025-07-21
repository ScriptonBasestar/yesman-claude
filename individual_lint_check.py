from typing import Any
import os
import subprocess


# !/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Individual lint tool checks."""


# Change to project directory
os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")


def run_command(cmd, description) -> object:
    """Run a command and capture output.

    Returns:
        object: Description of return value.
    """
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60)
        print(f"Exit code: {result.returncode}")

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False, "", "Command timed out"
    except Exception as e:
        print(f"Error: {e}")
        return False, "", str(e)


def main() -> None:
    """Run all lint checks individually."""
    # 1. Ruff check
    success1, stdout1, stderr1 = run_command(
        ["python", "-m", "ruff", "check", "libs", "commands", "api", "tests", "--diff", "--exclude", "migrations", "--exclude", "node_modules", "--exclude", "examples"], "Ruff check with diff"
    )

    # 2. MyPy check
    success2, stdout2, stderr2 = run_command(
        ["python", "-m", "mypy", "libs", "commands", "api", "--ignore-missing-imports", "--exclude", "migrations", "--exclude", "node_modules", "--exclude", "examples"], "MyPy type checking"
    )

    # 3. Bandit security check
    success3, stdout3, stderr3 = run_command(
        [
            "python",
            "-m",
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
    )

    # 4. MDFormat check
    success4, stdout4, stderr4 = run_command(["python", "-m", "mdformat", "--check", "--diff", "*.md", "--wrap", "120"], "MDFormat check")

    # Write comprehensive output
    with open("lint-output.txt", "w", encoding="utf-8") as f:
        f.write("=== COMPREHENSIVE LINT CHECK RESULTS ===\n\n")

        f.write("1. RUFF CHECK\n")
        f.write(f"Success: {success1}\n")
        f.write(f"STDOUT:\n{stdout1}\n")
        f.write(f"STDERR:\n{stderr1}\n\n")

        f.write("2. MYPY CHECK\n")
        f.write(f"Success: {success2}\n")
        f.write(f"STDOUT:\n{stdout2}\n")
        f.write(f"STDERR:\n{stderr2}\n\n")

        f.write("3. BANDIT CHECK\n")
        f.write(f"Success: {success3}\n")
        f.write(f"STDOUT:\n{stdout3}\n")
        f.write(f"STDERR:\n{stderr3}\n\n")

        f.write("4. MDFORMAT CHECK\n")
        f.write(f"Success: {success4}\n")
        f.write(f"STDOUT:\n{stdout4}\n")
        f.write(f"STDERR:\n{stderr4}\n\n")

        f.write(f"OVERALL SUCCESS: {all([success1, success2, success3, success4])}\n")

    print("\nComprehensive results saved to lint-output.txt")
    print(f"Overall success: {all([success1, success2, success3, success4])}")


if __name__ == "__main__":
    main()
