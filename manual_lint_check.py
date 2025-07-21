#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Manual lint check script to analyze files for common issues."""

import ast
from pathlib import Path
from typing import Any


def check_file_for_issues(file_path: Path) -> list[dict[str, Any]]:
    """Check a single Python file for common lint issues."""
    issues = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check for syntax errors
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(
                {
                    "type": "syntax",
                    "line": e.lineno,
                    "message": f"Syntax error: {e.msg}",
                    "file": str(file_path),
                }
            )
            return issues

        lines = content.split("\n")

        # Check for common issues
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 88:
                issues.append(
                    {
                        "type": "line_length",
                        "line": i,
                        "message": f"Line too long ({len(line)} > 88 characters)",
                        "file": str(file_path),
                    }
                )

            # Unused imports (simple check)
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                import_name = line.strip().split()[1].split(".")[0]
                if import_name not in content:
                    issues.append(
                        {
                            "type": "unused_import",
                            "line": i,
                            "message": f"Unused import: {import_name}",
                            "file": str(file_path),
                        }
                    )

            # Missing docstrings for functions/classes
            if line.strip().startswith("def ") or line.strip().startswith("class "):
                # Check if next few lines have docstring
                has_docstring = False
                for j in range(i, min(i + 5, len(lines))):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        has_docstring = True
                        break
                if not has_docstring:
                    issues.append(
                        {
                            "type": "missing_docstring",
                            "line": i,
                            "message": f"Missing docstring for {line.strip()}",
                            "file": str(file_path),
                        }
                    )

            # Trailing whitespace
            if line.rstrip() != line:
                issues.append(
                    {
                        "type": "trailing_whitespace",
                        "line": i,
                        "message": "Trailing whitespace",
                        "file": str(file_path),
                    }
                )

    except Exception as e:
        issues.append(
            {
                "type": "read_error",
                "line": 0,
                "message": f"Error reading file: {e}",
                "file": str(file_path),
            }
        )

    return issues


def scan_directory(directory: Path) -> list[dict[str, Any]]:
    """Scan directory for Python files and check for issues."""
    all_issues = []

    for file_path in directory.rglob("*.py"):
        # Skip certain directories
        if any(
            part in str(file_path)
            for part in [
                "__pycache__",
                ".git",
                "node_modules",
                "venv",
                "env",
                ".tox",
                ".pytest_cache",
                "build",
                "dist",
            ]
        ):
            continue

        issues = check_file_for_issues(file_path)
        all_issues.extend(issues)

    return all_issues


def main():
    """Main function to run lint check."""
    project_root = Path("/Users/archmagece/myopen/scripton/yesman-claude")

    print("Manual Lint Check Results")
    print("=" * 60)

    # Check libs directory
    libs_dir = project_root / "libs"
    if libs_dir.exists():
        print(f"\nChecking {libs_dir}...")
        libs_issues = scan_directory(libs_dir)
        print(f"Found {len(libs_issues)} issues in libs/")

        # Group issues by type
        issue_types = {}
        for issue in libs_issues:
            issue_type = issue["type"]
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)

        for issue_type, issues in issue_types.items():
            print(f"\n{issue_type.upper()} ({len(issues)} issues):")
            for issue in issues[:10]:  # Show first 10 of each type
                print(f"  {issue['file']}:{issue['line']} - {issue['message']}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")

    # Check commands directory
    commands_dir = project_root / "commands"
    if commands_dir.exists():
        print(f"\nChecking {commands_dir}...")
        commands_issues = scan_directory(commands_dir)
        print(f"Found {len(commands_issues)} issues in commands/")

        # Group issues by type
        issue_types = {}
        for issue in commands_issues:
            issue_type = issue["type"]
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)

        for issue_type, issues in issue_types.items():
            print(f"\n{issue_type.upper()} ({len(issues)} issues):")
            for issue in issues[:10]:  # Show first 10 of each type
                print(f"  {issue['file']}:{issue['line']} - {issue['message']}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")


if __name__ == "__main__":
    main()
