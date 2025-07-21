#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Lint configuration validation script.
Ensures make lint, pre-commit, and pre-push hooks are consistent.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:  # noqa: FBT001
    """Run a shell command and return the result."""
    print(f"🔍 Running: {cmd}")
    # nosec B602 - shell=True is intentional for this validation script
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)

    if result.returncode != 0 and check:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        return result

    print(f"✅ Command succeeded: {cmd}")
    return result


def validate_lint_consistency():
    """Validate that all lint configurations are consistent."""
    print("🔧 Validating lint configuration consistency...")

    # Test make lint
    print("\n📋 Testing make lint...")
    make_lint_result = run_command("make lint", check=False)

    # Test pre-commit hooks
    print("\n🔨 Testing pre-commit hooks...")
    precommit_result = run_command("uv run pre-commit run --all-files", check=False)

    # Test pre-push hooks
    print("\n🚀 Testing pre-push hooks...")
    prepush_result = run_command("uv run pre-commit run --hook-stage pre-push --all-files", check=False)

    # Summary
    print("\n📊 Validation Summary:")
    print(f"Make lint: {'✅ PASS' if make_lint_result.returncode == 0 else '❌ FAIL'}")
    print(f"Pre-commit: {'✅ PASS' if precommit_result.returncode == 0 else '❌ FAIL'}")
    print(f"Pre-push: {'✅ PASS' if prepush_result.returncode == 0 else '❌ FAIL'}")

    # Check for consistency
    all_passed = all(result.returncode == 0 for result in [make_lint_result, precommit_result, prepush_result])

    if all_passed:
        print("\n🎉 All lint configurations are consistent and passing!")
        return True
    else:
        print("\n💥 Some lint configurations are failing!")

        # Show detailed errors
        if make_lint_result.returncode != 0:
            print(f"\n❌ Make lint errors:\n{make_lint_result.stderr}")
        if precommit_result.returncode != 0:
            print(f"\n❌ Pre-commit errors:\n{precommit_result.stderr}")
        if prepush_result.returncode != 0:
            print(f"\n❌ Pre-push errors:\n{prepush_result.stderr}")

        return False


def install_hooks():
    """Install pre-commit hooks."""
    print("🔗 Installing pre-commit hooks...")
    run_command("uv run pre-commit install")
    run_command("uv run pre-commit install --hook-type pre-push")


def main():
    """Main validation function."""
    print("🏁 Starting lint configuration validation...")

    # Ensure we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    # Install hooks first
    install_hooks()

    # Validate consistency
    if validate_lint_consistency():
        print("\n✨ Validation completed successfully!")
        sys.exit(0)
    else:
        print("\n💀 Validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
