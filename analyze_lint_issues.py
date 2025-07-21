#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Analyze common lint issues by examining the codebase."""

import ast
import re
from pathlib import Path
from typing import Any

# Constants for lint analysis
MAX_LINE_LENGTH = 88  # ruff default
MAX_ISSUES_TO_DISPLAY = 5


class LintAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues = []

    @staticmethod
    def analyze_file( file_path: Path) -> list[dict[str, Any]]:
        """Analyze a single Python file for common lint issues."""
        issues = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            return [
                {
                    "file": str(file_path),
                    "line": 0,
                    "type": "read_error",
                    "message": "Could not read file",
                }
            ]

        lines = content.splitlines()

        # 1. Check for syntax errors
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(
                {
                    "file": str(file_path),
                    "line": e.lineno or 0,
                    "type": "syntax_error",
                    "message": f"Syntax error: {e.msg}",
                    "code": "E999",
                }
            )
            return issues

        # 2. Check imports
        imports_used = set()
        imports_defined = {}

        for line_num, line in enumerate(lines, 1):
            # Track imports
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                # Parse import
                if line.strip().startswith("import "):
                    import_match = re.match(r"import\s+(\w+)", line.strip())
                    if import_match:
                        module_name = import_match.group(1)
                        imports_defined[module_name] = line_num
                elif line.strip().startswith("from "):
                    from_match = re.match(r"from\s+[\w.]+\s+import\s+(.+)", line.strip())
                    if from_match:
                        imports_str = from_match.group(1)
                        # Handle multiple imports
                        for imp_name in imports_str.split(","):
                            imp = imp_name.strip().split(" as ")[0]
                            if imp and imp != "*":
                                imports_defined[imp] = line_num

            # Track usage
            words = re.findall(r"\b\w+\b", line)
            imports_used.update(words)

        # Check for unused imports
        for import_name, line_num in imports_defined.items():
            if import_name not in imports_used:
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "type": "unused_import",
                        "message": f"'{import_name}' imported but unused",
                        "code": "F401",
                    }
                )

        # 3. Check line length
        for line_num, line in enumerate(lines, 1):
            if len(line) > MAX_LINE_LENGTH:  # ruff default
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "type": "line_too_long",
                        "message": f"Line too long ({len(line)} > 88 characters)",
                        "code": "E501",
                    }
                )

        # 4. Check for missing docstrings
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                if not ast.get_docstring(node):
                    issues.append(
                        {
                            "file": str(file_path),
                            "line": node.lineno,
                            "type": "missing_docstring",
                            "message": (f"Missing docstring in {node.__class__.__name__.lower()} '{node.name}'"),
                            "code": "D100",
                        }
                    )

        # 5. Check for trailing whitespace
        for line_num, line in enumerate(lines, 1):
            if line.rstrip() != line and line.strip():
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "type": "trailing_whitespace",
                        "message": "Trailing whitespace",
                        "code": "W291",
                    }
                )

        # 6. Check for undefined names (basic check)
        for line_num, line in enumerate(lines, 1):
            # Look for common undefined name patterns
            if "NameError" in line or "undefined" in line.lower():
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "type": "undefined_name",
                        "message": "Potential undefined name",
                        "code": "F821",
                    }
                )

        return issues

    def analyze_directory(self, directory: Path) -> list[dict[str, Any]]:
        """Analyze all Python files in a directory."""
        all_issues = []

        for file_path in directory.rglob("*.py"):
            # Skip certain directories
            if any(
                part in file_path.parts
                for part in [
                    "__pycache__",
                    ".git",
                    "node_modules",
                    ".tox",
                    ".pytest_cache",
                    "build",
                    "dist",
                    "venv",
                    ".venv",
                    "env",
                    ".env",
                ]
            ):
                continue

            issues = self.analyze_file(file_path)
            all_issues.extend(issues)

        return all_issues

    def run_analysis(self) -> dict[str, Any]:
        """Run complete analysis."""
        # Analyze libs directory
        libs_issues = []
        libs_dir = self.project_path / "libs"
        if libs_dir.exists():
            libs_issues = self.analyze_directory(libs_dir)

        # Analyze commands directory
        commands_issues = []
        commands_dir = self.project_path / "commands"
        if commands_dir.exists():
            commands_issues = self.analyze_directory(commands_dir)

        # Analyze api directory
        api_issues = []
        api_dir = self.project_path / "api"
        if api_dir.exists():
            api_issues = self.analyze_directory(api_dir)

        all_issues = libs_issues + commands_issues + api_issues

        # Group issues by type
        issue_types = {}
        for issue in all_issues:
            issue_type = issue["type"]
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)

        return {
            "total_issues": len(all_issues),
            "libs_issues": len(libs_issues),
            "commands_issues": len(commands_issues),
            "api_issues": len(api_issues),
            "issue_types": issue_types,
            "all_issues": all_issues,
        }


def main():
    """Main function."""
    project_path = "/Users/archmagece/myopen/scripton/yesman-claude"
    analyzer = LintAnalyzer(project_path)

    print("=" * 80)
    print("LINT ANALYSIS RESULTS")
    print("=" * 80)

    results = analyzer.run_analysis()

    print("\nSUMMARY:")
    print(f"Total issues found: {results['total_issues']}")
    print(f"libs/ issues: {results['libs_issues']}")
    print(f"commands/ issues: {results['commands_issues']}")
    print(f"api/ issues: {results['api_issues']}")

    print("\nISSUES BY TYPE:")
    for issue_type, issues in results["issue_types"].items():
        print(f"{issue_type}: {len(issues)} issues")

        # Show first few examples
        for i, issue in enumerate(issues[:5]):
            relative_path = issue["file"].replace(project_path + "/", "")
            print(f"  {relative_path}:{issue['line']} - {issue['message']}")

        if len(issues) > MAX_ISSUES_TO_DISPLAY:
            print(f"  ... and {len(issues) - 5} more")
        print()

    # Save detailed results
    with open(f"{project_path}/lint_analysis_results.txt", "w") as f:
        f.write("LINT ANALYSIS RESULTS\n")
        f.write("=" * 80 + "\n\n")

        f.write("SUMMARY:\n")
        f.write(f"Total issues found: {results['total_issues']}\n")
        f.write(f"libs/ issues: {results['libs_issues']}\n")
        f.write(f"commands/ issues: {results['commands_issues']}\n")
        f.write(f"api/ issues: {results['api_issues']}\n\n")

        f.write("DETAILED ISSUES:\n")
        f.write("-" * 50 + "\n")

        for issue in results["all_issues"]:
            relative_path = issue["file"].replace(project_path + "/", "")
            f.write(f"{relative_path}:{issue['line']} [{issue['code']}] {issue['message']}\n")

    print("Detailed results saved to lint_analysis_results.txt")


if __name__ == "__main__":
    main()
