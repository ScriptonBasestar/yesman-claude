#!/usr/bin/env python3
"""Run manual lint check and save results to file"""

import os
import subprocess
import sys

os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

try:
    result = subprocess.run(
        [sys.executable, "manual_lint_check.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    with open("manual_lint_results.txt", "w") as f:
        f.write("MANUAL LINT CHECK RESULTS\n")
        f.write("=" * 60 + "\n\n")
        f.write("Return Code: " + str(result.returncode) + "\n\n")

        if result.stdout:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n\n")

        if result.stderr:
            f.write("STDERR:\n")
            f.write(result.stderr)
            f.write("\n\n")

    print("Manual lint check completed. Results saved to manual_lint_results.txt")

except Exception as e:
    print(f"Error running manual lint check: {e}")
