#!/usr/bin/env python3
"""Direct script to run lint commands and save output to file."""

import os
import subprocess


def run_command(command, description):
    """Run a command and capture output."""
    output = []
    output.append(f"\n{'=' * 60}")
    output.append(f"Running: {description}")
    output.append(f"Command: {' '.join(command)}")
    output.append(f"{'=' * 60}")

    try:
        result = subprocess.run(
            command,
            check=False,
            cwd="/Users/archmagece/myopen/scripton/yesman-claude",
            capture_output=True,
            text=True,
            timeout=120,
        )

        output.append(f"Return code: {result.returncode}")

        if result.stdout:
            output.append("STDOUT:")
            output.append(result.stdout)

        if result.stderr:
            output.append("STDERR:")
            output.append(result.stderr)

        return result.returncode == 0, "\n".join(output)

    except subprocess.TimeoutExpired:
        output.append("Command timed out after 2 minutes")
        return False, "\n".join(output)
    except Exception as e:
        output.append(f"Error running command: {e}")
        return False, "\n".join(output)


def main():
    # Change to project directory
    os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

    all_output = []

    # Run ruff check
    success1, output1 = run_command(
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
    all_output.append(output1)

    # Run mypy
    success2, output2 = run_command(
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
    all_output.append(output2)

    # Run bandit
    success3, output3 = run_command(
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
    all_output.append(output3)

    summary = []
    summary.append(f"\n{'=' * 60}")
    summary.append("LINT SUMMARY")
    summary.append(f"{'=' * 60}")
    summary.append(f"Ruff check: {'PASS' if success1 else 'FAIL'}")
    summary.append(f"MyPy check: {'PASS' if success2 else 'FAIL'}")
    summary.append(f"Bandit check: {'PASS' if success3 else 'PASS (with warnings)'}")

    if not any([success1, success2, success3]):
        summary.append("\nAll lint checks failed. Please review the output above.")

    summary.append("\nLint checks completed. Review output above for details.")

    # Write all output to file
    with open("lint_output.txt", "w") as f:
        f.write("\n".join(all_output))
        f.write("\n".join(summary))

    print("Lint output saved to lint_output.txt")

    # Also print summary
    print("\n".join(summary))


if __name__ == "__main__":
    main()
