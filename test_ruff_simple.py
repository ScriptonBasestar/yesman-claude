#!/usr/bin/env python3

# Copyright notice.

import os
import subprocess

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


# Change to the correct directory
os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

# Test ruff with a single file
test_file = "commands/automate.py"

print(f"Testing ruff on {test_file}")
print(f"Current directory: {os.getcwd()}")

try:
    # Run ruff check on a single file
    result = subprocess.run(
        ["uv", "run", "ruff", "check", test_file],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    print(f"Return code: {result.returncode}")
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")

    if result.returncode == 0:
        print("✅ No issues found!")
    else:
        print("❌ Issues found!")

except Exception as e:
    print(f"Error: {e}")
