#!/usr/bin/env python3
"""Test script to verify lint fixes are working"""

import os
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and return results"""
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
            timeout=60,
        )

        print(f"Return code: {result.returncode}")

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False, "", "Command timed out"
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False, "", str(e)


def main():
    """Main test function"""
    print("🔍 Testing lint fixes...")

    # Change to project directory
    os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

    # Test 1: Ruff check
    print("\n1. Testing ruff check...")
    success1, stdout1, stderr1 = run_command(
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
        "Ruff check on libs and commands",
    )

    # Test 2: MyPy check (if available)
    print("\n2. Testing mypy...")
    success2, stdout2, stderr2 = run_command(
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file=pyproject.toml",
            "libs",
            "commands",
            "api",
        ],
        "MyPy type checking",
    )

    # Test 3: Bandit security check
    print("\n3. Testing bandit security check...")
    success3, stdout3, stderr3 = run_command(
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
        "Bandit security check",
    )

    # Test 4: Pre-commit if available
    print("\n4. Testing pre-commit...")
    success4, stdout4, stderr4 = run_command([sys.executable, "-m", "pre_commit", "run", "--all-files"], "Pre-commit hooks")

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 LINT TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"✅ Ruff check: {'PASS' if success1 else 'FAIL'}")
    print(f"✅ MyPy check: {'PASS' if success2 else 'FAIL'}")
    print(f"✅ Bandit check: {'PASS' if success3 else 'FAIL'}")
    print(f"✅ Pre-commit: {'PASS' if success4 else 'FAIL'}")

    # Overall result
    if success1:
        print("\n🎉 Ruff check passed! Main lint fixes are working.")
    else:
        print("\n❌ Ruff check failed. Please review the output above.")

    if success2:
        print("🎉 MyPy check passed! Type checking is working.")
    else:
        print("⚠️  MyPy check failed or not available.")

    if success3:
        print("🎉 Bandit check passed! Security checks are working.")
    else:
        print("⚠️  Bandit check failed or not available.")

    return success1  # Return True if at least ruff passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
