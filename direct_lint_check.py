#!/usr/bin/env python3
"""Direct lint checks without make"""

import os
import subprocess
from pathlib import Path

os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")


def run_command(cmd, description):
    """Run command and return results"""
    print(f"\n{'=' * 60}")
    print(f"{description}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


# 1. Ruff check
print("1. RUFF CHECK")
code1, out1, err1 = run_command(
    ["python", "-m", "ruff", "check", "libs", "commands", "api", "tests", "--exclude", "migrations", "--exclude", "node_modules", "--exclude", "examples"], "Ruff style check"
)
print(f"Exit code: {code1}")
if out1:
    print(f"Output:\n{out1}")
if err1:
    print(f"Error:\n{err1}")

# 2. MyPy check
print("\n2. MYPY CHECK")
code2, out2, err2 = run_command(["python", "-m", "mypy", "libs", "commands", "api", "--ignore-missing-imports", "--exclude", "migrations"], "MyPy type check")
print(f"Exit code: {code2}")
if out2:
    print(f"Output:\n{out2}")
if err2:
    print(f"Error:\n{err2}")

# 3. Check specific files for common issues
print("\n3. CHECKING SPECIFIC FILES")

# Check for long lines
print("\n3.1 Long lines check (>88 chars):")
files_to_check = ["api/routers/controllers.py", "api/background_tasks.py", "commands/multi_agent.py", "analyze_lint_issues.py"]

for file_path in files_to_check:
    if Path(file_path).exists():
        with open(file_path) as f:
            lines = f.readlines()
        long_lines = [(i + 1, len(line.rstrip())) for i, line in enumerate(lines) if len(line.rstrip()) > 88]
        if long_lines:
            print(f"\n{file_path}:")
            for line_num, length in long_lines[:5]:  # Show first 5
                print(f"  Line {line_num}: {length} chars")
    else:
        print(f"\n{file_path}: Not found")

# Summary
print(f"\n{'=' * 60}")
print("SUMMARY")
print(f"{'=' * 60}")
print(f"Ruff: {'PASS' if code1 == 0 else 'FAIL'}")
print(f"MyPy: {'PASS' if code2 == 0 else 'FAIL'}")
print(f"Overall: {'PASS' if code1 == 0 and code2 == 0 else 'FAIL'}")
