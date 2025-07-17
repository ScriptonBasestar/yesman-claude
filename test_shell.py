#!/usr/bin/env python3

import os
import subprocess

os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

# Test basic commands
commands = [["ls", "-la"], ["uv", "--version"], ["uv", "run", "python", "--version"]]

for cmd in commands:
    try:
        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, timeout=10
        )
        print(f"Command: {' '.join(cmd)}")
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Error: {result.stderr.strip()}")
        print("-" * 40)
    except Exception as e:
        print(f"Failed to run {cmd}: {e}")
        print("-" * 40)
