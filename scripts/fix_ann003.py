#!/usr/bin/env python3
"""Script to systematically fix ANN003 (missing-type-kwargs) errors.

This script:
1. Finds all ANN003 errors using ruff
2. Reads each file and fixes the **kwargs type annotations
3. Adds necessary imports (typing.Any)
4. Creates backups and validates fixes
5. Reports results

Usage:
    python scripts/fix_ann003.py [--dry-run] [--backup-dir DIR]
"""

import argparse
import re
import subprocess
from pathlib import Path


class KwargsTypeFixer:
    """Fixes missing type annotations for **kwargs parameters."""

    def __init__(self, backup_dir: Path | None = None) -> None:
        self.backup_dir = backup_dir
        self.fixed_files: set[Path] = set()
        self.failed_files: set[Path] = set()
        self.stats = {"files_processed": 0, "fixes_applied": 0, "imports_added": 0, "errors": 0}

    def get_ann003_errors(self) -> dict[Path, list[tuple[int, str]]]:
        """Get all ANN003 errors from ruff."""
        try:
            result = subprocess.run(["ruff", "check", "--select", "ANN003", "--exclude", ".backups", ".", "--output-format", "json"], capture_output=True, text=True, cwd=Path.cwd(), check=False)

            if result.returncode not in {0, 1}:  # 0 = no issues, 1 = issues found
                print(f"Error running ruff: {result.stderr}")
                return {}

            if not result.stdout.strip():
                return {}

            import json

            errors = json.loads(result.stdout)

            # Group by file
            file_errors: dict[Path, list[tuple[int, str]]] = {}
            for error in errors:
                if error.get("code") == "ANN003":
                    file_path = Path(error["filename"])
                    line_num = error["location"]["row"]
                    message = error["message"]

                    if file_path not in file_errors:
                        file_errors[file_path] = []
                    file_errors[file_path].append((line_num, message))

            return file_errors

        except Exception as e:
            print(f"Failed to get ANN003 errors: {e}")
            return {}

    def needs_any_import(self, content: str) -> bool:
        """Check if file needs 'from typing import Any' added."""
        # Check if Any is already imported
        if re.search(r"from typing import.*\bAny\b", content):
            return False
        if re.search(r"import typing", content) and re.search(r"typing\.Any", content):
            return False
        return not re.search(r"from typing_extensions import.*\bAny\b", content)

    def add_any_import(self, content: str) -> str:
        """Add 'Any' to typing imports or create new import."""
        lines = content.split("\n")

        # Look for existing typing imports to extend
        for i, line in enumerate(lines):
            if re.match(r"^from typing import ", line):
                if "Any" not in line:
                    # Add Any to existing import
                    if line.endswith(")"):
                        # Multi-line import
                        lines[i] = line.replace(")", ", Any)")
                    else:
                        # Single line import
                        lines[i] = line + ", Any"
                    self.stats["imports_added"] += 1
                    return "\n".join(lines)

        # Find best place to insert new import
        insert_pos = 0
        in_docstring = False
        docstring_quotes = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Handle docstrings
            if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                docstring_quotes = stripped[:3]
                if stripped.count(docstring_quotes) == 2:
                    # Single line docstring
                    insert_pos = i + 1
                else:
                    in_docstring = True
            elif in_docstring and docstring_quotes and stripped.endswith(docstring_quotes):
                in_docstring = False
                insert_pos = i + 1
            elif not in_docstring and stripped.startswith("#"):
                # Comment at top
                insert_pos = i + 1
            elif not in_docstring and stripped.startswith("import "):
                # Regular import
                insert_pos = i + 1
            elif not in_docstring and stripped.startswith("from ") and " import " in stripped:
                # From import
                insert_pos = i + 1
            elif not in_docstring and stripped and not stripped.startswith("#"):
                # First non-import, non-comment line
                break

        # Insert the import
        lines.insert(insert_pos, "from typing import Any")
        if insert_pos > 0 and lines[insert_pos - 1].strip():
            # Add blank line before if previous line isn't blank
            lines.insert(insert_pos, "")

        self.stats["imports_added"] += 1
        return "\n".join(lines)

    def fix_kwargs_line(self, line: str) -> str:
        """Fix a single line containing **kwargs."""
        # Pattern: **kwargs without type annotation
        pattern = r"(\*\*kwargs)(?!\s*:)"

        # Replace with typed version
        fixed_line = re.sub(pattern, r"\1: Any", line)

        if fixed_line != line:
            self.stats["fixes_applied"] += 1

        return fixed_line

    def fix_file(self, file_path: Path, error_lines: list[int], dry_run: bool = False) -> bool:
        """Fix ANN003 errors in a specific file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Create backup if not dry run
            if not dry_run and self.backup_dir:
                backup_path = self.backup_dir / file_path.name
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.write_text(content, encoding="utf-8")

            lines = content.split("\n")
            modified = False

            # Fix each error line
            for line_num in error_lines:
                if line_num <= len(lines):
                    original_line = lines[line_num - 1]
                    fixed_line = self.fix_kwargs_line(original_line)

                    if fixed_line != original_line:
                        lines[line_num - 1] = fixed_line
                        modified = True
                        print(f"  Line {line_num}: {original_line.strip()} -> {fixed_line.strip()}")

            if not modified:
                return True

            content = "\n".join(lines)

            # Add Any import if needed
            if self.needs_any_import(content):
                content = self.add_any_import(content)
                print("  Added 'from typing import Any'")

            if not dry_run:
                file_path.write_text(content, encoding="utf-8")

                # Verify the fix with ruff
                result = subprocess.run(["ruff", "check", "--select", "ANN003", "--exclude", ".backups", str(file_path)], capture_output=True, text=True, check=False)

                if result.returncode != 0:
                    print("  Warning: Ruff still reports issues after fix")
                    # Restore original content
                    file_path.write_text(original_content, encoding="utf-8")
                    return False

            self.stats["files_processed"] += 1
            self.fixed_files.add(file_path)
            return True

        except Exception as e:
            print(f"  Error fixing {file_path}: {e}")
            self.stats["errors"] += 1
            self.failed_files.add(file_path)
            return False

    def run(self, dry_run: bool = False) -> None:
        """Run the fixer on all files with ANN003 errors."""
        print("Scanning for ANN003 errors...")

        file_errors = self.get_ann003_errors()

        if not file_errors:
            print("No ANN003 errors found!")
            return

        print(f"Found ANN003 errors in {len(file_errors)} files")

        if dry_run:
            print("\n=== DRY RUN MODE ===")

        for file_path, errors in file_errors.items():
            print(f"\nProcessing {file_path} ({len(errors)} errors):")
            error_lines = [line_num for line_num, _ in errors]
            self.fix_file(file_path, error_lines, dry_run)

        # Print summary
        print("\n=== SUMMARY ===")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Fixes applied: {self.stats['fixes_applied']}")
        print(f"Imports added: {self.stats['imports_added']}")
        print(f"Errors: {self.stats['errors']}")

        if self.failed_files:
            print(f"Failed files: {len(self.failed_files)}")
            for file_path in sorted(self.failed_files):
                print(f"  {file_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix ANN003 missing-type-kwargs errors")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    parser.add_argument("--backup-dir", type=Path, default=Path(".backups/ann003"), help="Directory to store backup files")

    args = parser.parse_args()

    if not args.dry_run:
        args.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"Backups will be stored in: {args.backup_dir}")

    fixer = KwargsTypeFixer(args.backup_dir if not args.dry_run else None)
    fixer.run(args.dry_run)


if __name__ == "__main__":
    main()
