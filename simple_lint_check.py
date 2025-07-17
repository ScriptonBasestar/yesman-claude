#!/usr/bin/env python3

import os
import subprocess
import sys

# Change to the correct directory
os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")


def run_ruff_check():
    """Run ruff check command"""
    try:
        cmd = [
            "uv",
            "run",
            "ruff",
            "check",
            "libs",
            "commands",
            "api",
            "tests",
            "--diff",
        ]

        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, timeout=60
        )

        print("=== RUFF CHECK RESULTS ===")
        print(f"Return code: {result.returncode}")

        if result.stdout:
            print("\n--- STDOUT ---")
            print(result.stdout)

        if result.stderr:
            print("\n--- STDERR ---")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running ruff: {e}")
        return False


def run_mypy_check():
    """Run mypy check command"""
    try:
        cmd = [
            "uv",
            "run",
            "mypy",
            "libs",
            "commands",
            "api",
            "--ignore-missing-imports",
        ]

        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, timeout=60
        )

        print("\n=== MYPY CHECK RESULTS ===")
        print(f"Return code: {result.returncode}")

        if result.stdout:
            print("\n--- STDOUT ---")
            print(result.stdout)

        if result.stderr:
            print("\n--- STDERR ---")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ MyPy timed out")
        return False
    except Exception as e:
        print(f"❌ Error running mypy: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Running lint checks...")

    ruff_passed = run_ruff_check()
    mypy_passed = run_mypy_check()

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    if ruff_passed and mypy_passed:
        print("✅ All lint checks passed!")
        sys.exit(0)
    else:
        print("❌ Some lint checks failed!")
        print(f"  Ruff: {'✅ PASSED' if ruff_passed else '❌ FAILED'}")
        print(f"  MyPy: {'✅ PASSED' if mypy_passed else '❌ FAILED'}")
        sys.exit(1)
