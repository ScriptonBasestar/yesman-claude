from typing import Any
from pathlib import Path


# !/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Check all Python files for long lines."""


def check_long_lines(file_path, max_length=88) -> object:
    """Check file for long lines.

    Returns:
        object: Description of return value.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        long_lines = []
        for i, line in enumerate(lines, 1):
            # Skip lines with URLs or long string literals
            if "http://" in line or "https://" in line:
                continue
            if '"""' in line or "'''" in line:
                continue

            line_content = line.rstrip("\n\r")
            if len(line_content) > max_length:
                long_lines.append((i, len(line_content), line_content[:80] + "..."))

        return long_lines
    except Exception:
        return []


def main() -> None:
    """Check all Python files."""
    base_path = Path("/Users/archmagece/myopen/scripton/yesman-claude")

    # Key directories to check
    dirs_to_check = ["api", "commands", "libs", "tests"]

    all_long_lines = {}

    for dir_name in dirs_to_check:
        dir_path = base_path / dir_name
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                # Skip certain files
                if any(skip in str(py_file) for skip in ["__pycache__", "migrations", "node_modules"]):
                    continue

                long_lines = check_long_lines(py_file)
                if long_lines:
                    rel_path = py_file.relative_to(base_path)
                    all_long_lines[str(rel_path)] = long_lines

    # Print results
    if all_long_lines:
        print("📋 Files with long lines (>88 chars):")
        print("=" * 80)

        total_issues = 0
        for file_path, issues in sorted(all_long_lines.items()):
            print(f"\n{file_path}: {len(issues)} long lines")
            for line_num, length, preview in issues[:3]:  # Show first 3
                print(f"  Line {line_num}: {length} chars - {preview}")
            if len(issues) > 3:
                print(f"  ... and {len(issues) - 3} more")
            total_issues += len(issues)

        print(f"\n📊 Total: {total_issues} long lines in {len(all_long_lines)} files")
    else:
        print("✅ No long lines found!")


if __name__ == "__main__":
    main()
