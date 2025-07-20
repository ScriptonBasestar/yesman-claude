#!/usr/bin/env python3
"""Run make lint and capture output."""

import os
import subprocess
import sys

os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

try:
    result = subprocess.run(["make", "lint"], check=False, capture_output=True, text=True, timeout=120)

    # Write to file
    with open("lint-output.txt", "w") as f:
        f.write(f"Exit code: {result.returncode}\n")
        f.write("\n=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n\n=== STDERR ===\n")
        f.write(result.stderr)

    # Print to console
    print(f"Exit code: {result.returncode}")
    print("\n=== STDOUT ===")
    print(result.stdout)
    if result.stderr:
        print("\n=== STDERR ===")
        print(result.stderr)

    sys.exit(result.returncode)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
