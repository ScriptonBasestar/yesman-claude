#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Quick ruff check to see current status."""

import os
import subprocess

os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

# Try ruff check
try:
    result = subprocess.run(
        ["python", "-m", "ruff", "check", "libs", "commands", "api", "--exclude", "migrations", "--exclude", "node_modules", "--exclude", "examples"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    print("=== RUFF CHECK RESULTS ===")
    print(f"Exit code: {result.returncode}")
    print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")

except Exception as e:
    print(f"Error running ruff: {e}")

# Try mypy check on specific problematic file
try:
    result = subprocess.run(["python", "-m", "mypy", "commands/multi_agent.py", "--ignore-missing-imports"], check=False, capture_output=True, text=True, timeout=30)

    print("\n=== MYPY CHECK ON multi_agent.py ===")
    print(f"Exit code: {result.returncode}")
    print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")

except Exception as e:
    print(f"Error running mypy: {e}")
