#!/usr/bin/env python3

# Copyright notice.

import os
import subprocess
import sys

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Run make lint and capture output."""


os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

try:
    result = subprocess.run(["make", "lint"], check=False, capture_output=True, text=True, timeout=120)

    # Write to file
    with open("lint-output.txt", "w", encoding="utf-8") as f:
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
