#!/usr/bin/env python3

# Copyright notice.

import ast
import re
from pathlib import Path
    # Check for potential circular imports
    # 6. Unused imports (simple check)
                            # Simple check for unused imports

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Extract common lint errors from code analysis."""


def analyze_common_issues() -> None:
    """Analyze common lint issues in the codebase."""
    project_path = Path("/Users/archmagece/myopen/scripton/yesman-claude")

    print("LINT ANALYSIS REPORT")
    print("=" * 80)

    # 1. Makefile issues
    print("\n1. MAKEFILE ISSUES:")
    print("-" * 30)
    makefile_path = project_path / "Makefile"
    if makefile_path.exists():
        makefile_content = makefile_path.read_text()
        # Check for duplicate targets
        lines = makefile_content.split("\n")
        targets = []
        for line in lines:
            if line and not line.startswith("\t") and not line.startswith("#") and ":" in line:
                target = line.split(":")[0].strip()
                if target:
                    targets.append(target)

        # Find duplicates
        seen = set()
        duplicates = []
        for target in targets:
            if target in seen:
                duplicates.append(target)
            seen.add(target)

        if duplicates:
            print(f"  • Duplicate targets found: {', '.join(duplicates)}")
        else:
            print("  • No duplicate targets found")

        # Check for inconsistent references
        if "sbkube" in makefile_content:
            print("  • Found 'sbkube' references in Makefile (should be 'libs commands')")

    # 2. Configuration conflicts
    print("\n2. CONFIGURATION CONFLICTS:")
    print("-" * 30)

    # Check pyproject.toml vs ruff.toml
    pyproject_path = project_path / "pyproject.toml"
    ruff_path = project_path / "ruff.toml"

    if pyproject_path.exists() and ruff_path.exists():
        pyproject_content = pyproject_path.read_text()
        ruff_content = ruff_path.read_text()

        # Check line length settings
        pyproject_line_length = None
        ruff_line_length = None

        if "line-length = 88" in pyproject_content:
            pyproject_line_length = 88
        if "line-length = 200" in ruff_content:
            ruff_line_length = 200

        if pyproject_line_length and ruff_line_length and pyproject_line_length != ruff_line_length:
            print(f"  • Line length mismatch: pyproject.toml={pyproject_line_length}, ruff.toml={ruff_line_length}")

        # Check target version
        if 'target-version = "py311"' in pyproject_content and 'target-version = "py38"' in ruff_content:
            print("  • Target version mismatch: pyproject.toml=py311, ruff.toml=py38")

    # 3. Import issues
    print("\n3. IMPORT ISSUES:")
    print("-" * 30)

    commands_dir = project_path / "commands"
    if commands_dir.exists():
        for py_file in commands_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                content = py_file.read_text()
                if "from commands.multi_agent" in content:
                    print(f"  • Potential circular import in {py_file.name}")
            except Exception:
                pass

    # 4. Long lines
    print("\n4. LONG LINES (>88 characters):")
    print("-" * 30)

    long_line_count = 0
    for directory in ["commands", "libs"]:
        dir_path = project_path / directory
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                try:
                    lines = py_file.read_text().split("\n")
                    for i, line in enumerate(lines, 1):
                        if len(line) > 88:
                            long_line_count += 1
                            if long_line_count <= 10:  # Show first 10
                                relative_path = py_file.relative_to(project_path)
                                print(f"  • {relative_path}:{i} - {len(line)} chars")
                except Exception:
                    pass

    if long_line_count > 10:
        print(f"  • ... and {long_line_count - 10} more long lines")

    # 5. Missing type hints
    print("\n5. MISSING TYPE HINTS:")
    print("-" * 30)

    missing_hints_count = 0
    for directory in ["commands", "libs"]:
        dir_path = project_path / directory
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            # Check if function has return type hint
                            if not node.returns and node.name not in {
                                "__init__",
                                "__str__",
                                "__repr__",
                            }:
                                missing_hints_count += 1
                                if missing_hints_count <= 10:
                                    relative_path = py_file.relative_to(project_path)
                                    print(f"  • {relative_path}:{node.lineno} - Function '{node.name}' missing return type")
                except Exception:
                    pass

    if missing_hints_count > 10:
        print(f"  • ... and {missing_hints_count - 10} more missing type hints")

    print("\n6. POTENTIAL UNUSED IMPORTS:")
    print("-" * 30)

    unused_count = 0
    for directory in ["commands", "libs"]:
        dir_path = project_path / directory
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    lines = content.split("\n")

                    for i, line in enumerate(lines, 1):
                        if line.strip().startswith("import "):
                            import_match = re.match(r"import\s+(\w+)", line.strip())
                            if import_match:
                                module_name = import_match.group(1)
                                # Check if module is used elsewhere in the file
                                if lines.count(module_name) == 1:  # Only appears in import line
                                    unused_count += 1
                                    if unused_count <= 10:
                                        relative_path = py_file.relative_to(project_path)
                                        print(f"  • {relative_path}:{i} - Potentially unused import '{module_name}'")
                except Exception:
                    pass

    if unused_count > 10:
        print(f"  • ... and {unused_count - 10} more potential unused imports")

    # 7. Security issues
    print("\n7. POTENTIAL SECURITY ISSUES:")
    print("-" * 30)

    security_issues = 0
    for directory in ["commands", "libs"]:
        dir_path = project_path / directory
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    lines = content.split("\n")

                    for i, line in enumerate(lines, 1):
                        # Check for subprocess with shell=True
                        if "subprocess" in line and "shell=True" in line:
                            security_issues += 1
                            if security_issues <= 5:
                                relative_path = py_file.relative_to(project_path)
                                print(f"  • {relative_path}:{i} - subprocess with shell=True")

                        # Check for eval/exec
                        if "eval(" in line or "exec(" in line:
                            security_issues += 1
                            if security_issues <= 5:
                                relative_path = py_file.relative_to(project_path)
                                print(f"  • {relative_path}:{i} - Use of eval/exec")
                except Exception:
                    pass

    if security_issues > 5:
        print(f"  • ... and {security_issues - 5} more security issues")

    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("This analysis found several categories of issues that would be")
    print("flagged by ruff, mypy, and bandit linters.")
    print("=" * 80)


if __name__ == "__main__":
    analyze_common_issues()
