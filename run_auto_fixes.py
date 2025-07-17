#!/usr/bin/env python3
"""Run auto-fixes for lint issues"""

import os
import subprocess

os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")


def run_command(cmd, description):
    """Run command and show results"""
    print(f"\n{'=' * 60}")
    print(f"{description}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60)
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("Output:")
            print(result.stdout)
        if result.stderr:
            print("Error:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False


# 1. Ruff format (replaces black)
print("1. RUNNING RUFF FORMAT")
run_command(["python", "-m", "ruff", "format", "libs", "commands", "api", "tests"], "Ruff format - code formatting")

# 2. Ruff check with fix
print("\n2. RUNNING RUFF CHECK WITH FIX")
run_command(["python", "-m", "ruff", "check", "--fix", "libs", "commands", "api", "tests", "--exclude", "migrations", "--exclude", "node_modules"], "Ruff check with auto-fix")

# 3. Sort imports with ruff
print("\n3. RUNNING IMPORT SORT")
run_command(["python", "-m", "ruff", "check", "--select", "I", "--fix", "libs", "commands", "api", "tests"], "Ruff import sorting")

print("\n✅ Auto-fixes completed!")
print("\nNOTE: Run 'make lint' to verify all issues are resolved.")
