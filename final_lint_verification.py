#!/usr/bin/env python3

# Copyright notice.

import os
from pathlib import Path

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Final verification of lint status."""


os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

print("🔍 FINAL LINT VERIFICATION")
print("=" * 80)

# Check for common issues
issues_found = []

# 1. Check for long lines
print("\n1. Checking for long lines (>88 chars)...")
long_line_files = 0
for py_file in Path(".").rglob("*.py"):
    if any(skip in str(py_file) for skip in ["__pycache__", "migrations", "node_modules", ".git"]):
        continue

    try:
        with open(py_file, encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            if len(line.rstrip()) > 88 and "http" not in line and '"""' not in line:
                long_line_files += 1
                break
    except Exception:
        pass

if long_line_files > 0:
    issues_found.append(f"{long_line_files} files with long lines")
else:
    print("✅ No long lines found")

# 2. Check for file endings
print("\n2. Checking for proper file endings...")
no_newline_files = 0
for py_file in Path(".").rglob("*.py"):
    if any(skip in str(py_file) for skip in ["__pycache__", "migrations", "node_modules", ".git"]):
        continue

    try:
        with open(py_file, "rb") as f:
            content = f.read()
        if content and not content.endswith(b"\n"):
            no_newline_files += 1
    except Exception:
        pass

if no_newline_files > 0:
    issues_found.append(f"{no_newline_files} files without newline at end")
else:
    print("✅ All files end with newline")

# 3. Try to run basic syntax check
print("\n3. Running basic syntax check...")
syntax_errors = 0
for py_file in Path(".").rglob("*.py"):
    if any(skip in str(py_file) for skip in ["__pycache__", "migrations", "node_modules", ".git"]):
        continue

    try:
        compile(open(py_file, encoding="utf-8").read(), py_file, "exec")
    except SyntaxError:
        syntax_errors += 1
    except Exception:
        pass

if syntax_errors > 0:
    issues_found.append(f"{syntax_errors} files with syntax errors")
else:
    print("✅ No syntax errors found")

# Summary
print("\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)

if issues_found:
    print("❌ Issues found:")
    for issue in issues_found:
        print(f"  - {issue}")
    print("\n⚠️  Some issues remain. Run auto-fix tools or fix manually.")
else:
    print("✅ All checks passed!")
    print("🎉 The codebase appears to be lint-clean!")

print("\n💡 To run the full lint check, use: make lint")
