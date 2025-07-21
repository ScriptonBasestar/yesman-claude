#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Check for lines longer than 88 characters."""

from pathlib import Path


def check_file_line_lengths(file_path, max_length=88):
    """Check a file for lines exceeding max_length."""
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        long_lines = []
        for i, line in enumerate(lines, 1):
            line_content = line.rstrip("\n\r")
            if len(line_content) > max_length:
                long_lines.append((i, len(line_content), line_content[:100] + "..." if len(line_content) > 100 else line_content))

        return long_lines
    except Exception as e:
        return f"Error reading {file_path}: {e}"


def main():
    """Check key Python files for long lines."""
    base_path = Path("/Users/archmagece/myopen/scripton/yesman-claude")

    # Key files to check
    check_files = [
        "api/routers/controllers.py",
        "api/background_tasks.py",
        "api/middleware/error_handler.py",
        "api/routers/dashboard.py",
        "api/tests/test_background_tasks.py",
        "commands/multi_agent.py",
        "analyze_lint_issues.py",
    ]

    total_long_lines = 0

    for file_path in check_files:
        full_path = base_path / file_path
        if full_path.exists():
            long_lines = check_file_line_lengths(full_path)
            if long_lines:
                print(f"\n📁 {file_path}:")
                for line_num, length, content in long_lines:
                    print(f"  Line {line_num}: {length} chars - {content}")
                total_long_lines += len(long_lines)
            else:
                print(f"✅ {file_path}: No long lines")
        else:
            print(f"❌ {file_path}: File not found")

    print(f"\n📊 Total long lines found: {total_long_lines}")


if __name__ == "__main__":
    main()
