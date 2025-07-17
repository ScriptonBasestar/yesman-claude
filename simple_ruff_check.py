import os
import subprocess
import sys

os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

# Try running ruff check
try:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--target-version",
            "py311",
            "libs/core/base_command.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    print(f"Return code: {result.returncode}")
    print(f"STDOUT:\n{result.stdout}")
    print(f"STDERR:\n{result.stderr}")
except Exception as e:
    print(f"Error: {e}")
