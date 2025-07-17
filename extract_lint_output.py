#!/usr/bin/env python3
"""Script to extract lint output by running each command individually"""

import os
import subprocess
import sys


def run_and_capture(cmd_list, description):
    """Run command and return output"""
    try:
        result = subprocess.run(
            cmd_list,
            check=False,
            cwd="/Users/archmagece/myopen/scripton/yesman-claude",
            capture_output=True,
            text=True,
            timeout=180,
        )

        return {
            "description": description,
            "command": " ".join(cmd_list),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except Exception as e:
        return {
            "description": description,
            "command": " ".join(cmd_list),
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
        }


# Change to project directory
os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

# Run each lint command
commands = [
    (
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--target-version",
            "py311",
            "libs",
            "commands",
        ],
        "Ruff Check",
    ),
    (
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file=pyproject.toml",
            "libs",
            "commands",
            "api",
        ],
        "MyPy Check",
    ),
    (
        [
            sys.executable,
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
        "Bandit Security Check",
    ),
]

output_lines = []
for cmd_list, description in commands:
    result = run_and_capture(cmd_list, description)

    output_lines.append(f"\n{'=' * 60}")
    output_lines.append(f"COMMAND: {description}")
    output_lines.append(f"{'=' * 60}")
    output_lines.append(f"Command: {result['command']}")
    output_lines.append(f"Return Code: {result['returncode']}")

    if result["stdout"]:
        output_lines.append("\nSTDOUT:")
        output_lines.append(result["stdout"])

    if result["stderr"]:
        output_lines.append("\nSTDERR:")
        output_lines.append(result["stderr"])

    output_lines.append("")

# Write to file
with open("lint_output.txt", "w") as f:
    f.write("\n".join(output_lines))

print("Lint output saved to lint_output.txt")
