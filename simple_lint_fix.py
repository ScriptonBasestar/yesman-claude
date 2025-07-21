#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Simple lint fix runner without subprocess."""

import os
import sys


def main():
    # Change to project directory
    os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

    # Import ruff and run directly
    try:
        from ruff.__main__ import main as ruff_main

        print("Running ruff check with auto-fix...")
        sys.argv = [
            "ruff",
            "check",
            "libs",
            "commands",
            "api",
            "tests",
            "--select",
            "I",
            "--fix",
            "--exclude",
            "migrations",
            "--exclude",
            "node_modules",
            "--exclude",
            "examples",
        ]
        ruff_main()

        print("\nRunning ruff format...")
        sys.argv = [
            "ruff",
            "format",
            "libs",
            "commands",
            "api",
            "tests",
            "--exclude",
            "migrations",
            "--exclude",
            "node_modules",
            "--exclude",
            "examples",
        ]
        ruff_main()

    except ImportError:
        print("Ruff not available, trying with sys.executable")
        import subprocess

        # Try with python -m
        commands = [
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "libs",
                "commands",
                "api",
                "tests",
                "--select",
                "I",
                "--fix",
                "--exclude",
                "migrations",
                "--exclude",
                "node_modules",
                "--exclude",
                "examples",
            ],
            [
                sys.executable,
                "-m",
                "ruff",
                "format",
                "libs",
                "commands",
                "api",
                "tests",
                "--exclude",
                "migrations",
                "--exclude",
                "node_modules",
                "--exclude",
                "examples",
            ],
        ]

        for cmd in commands:
            try:
                print(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=False, capture_output=True, text=True)
                print(f"Return code: {result.returncode}")
                if result.stdout:
                    print(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    print(f"STDERR:\n{result.stderr}")
            except Exception as e:
                print(f"Error: {e}")

    print("Lint fix completed!")


if __name__ == "__main__":
    main()
