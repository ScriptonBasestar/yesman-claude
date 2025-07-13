#!/usr/bin/env python3
"""
Automated unittest to pytest migration script.

This script converts unittest test files to pytest format, including:
- Class inheritance changes
- setUp/tearDown → pytest fixtures
- Assertion method conversions
- Import statement updates
- Basic naming convention improvements
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class UnittestToPytestMigrator:
    """Migrates unittest test files to pytest format."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.patterns = self._get_conversion_patterns()
        self.import_replacements = {
            "import unittest": "import pytest",
            "from unittest import TestCase": "",  # Remove this import
            "from unittest.mock import": "from unittest.mock import",  # Keep mock imports
        }

    def _get_conversion_patterns(self) -> List[Tuple[str, str]]:
        """Get regex patterns for converting unittest to pytest."""
        return [
            # Assertion conversions
            (r"self\.assertTrue\((.+?)\)", r"assert \1"),
            (r"self\.assertFalse\((.+?)\)", r"assert not \1"),
            (r"self\.assertEqual\((.+?), (.+?)\)", r"assert \1 == \2"),
            (r"self\.assertNotEqual\((.+?), (.+?)\)", r"assert \1 != \2"),
            (r"self\.assertIn\((.+?), (.+?)\)", r"assert \1 in \2"),
            (r"self\.assertNotIn\((.+?), (.+?)\)", r"assert \1 not in \2"),
            (r"self\.assertIsNone\((.+?)\)", r"assert \1 is None"),
            (r"self\.assertIsNotNone\((.+?)\)", r"assert \1 is not None"),
            (r"self\.assertIs\((.+?), (.+?)\)", r"assert \1 is \2"),
            (r"self\.assertIsNot\((.+?), (.+?)\)", r"assert \1 is not \2"),
            (r"self\.assertGreater\((.+?), (.+?)\)", r"assert \1 > \2"),
            (r"self\.assertLess\((.+?), (.+?)\)", r"assert \1 < \2"),
            (r"self\.assertGreaterEqual\((.+?), (.+?)\)", r"assert \1 >= \2"),
            (r"self\.assertLessEqual\((.+?), (.+?)\)", r"assert \1 <= \2"),
            # Exception testing (requires manual review)
            (r"self\.assertRaises\((.+?)\)", r"pytest.raises(\1)"),
            (r"self\.assertRaisesRegex\((.+?), (.+?)\)", r"pytest.raises(\1, match=\2)"),
            # Class inheritance
            (r"class (.+?)\(unittest\.TestCase\):", r"class \1:"),
            (r"class (.+?)\(TestCase\):", r"class \1:"),
        ]

    def migrate_file(self, file_path: Path) -> Dict[str, any]:
        """
        Migrate a single test file from unittest to pytest.

        Returns:
            Dictionary with migration results and statistics
        """
        print(f"🔄 Processing {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content
            stats = {
                "file": str(file_path),
                "assertions_converted": 0,
                "classes_converted": 0,
                "imports_updated": 0,
                "setUp_converted": 0,
                "tearDown_converted": 0,
                "manual_review_needed": [],
            }

            # Update imports
            content, import_changes = self._update_imports(content)
            stats["imports_updated"] = import_changes

            # Convert assertions
            content, assertion_changes = self._convert_assertions(content)
            stats["assertions_converted"] = assertion_changes

            # Convert class inheritance
            content, class_changes = self._convert_class_inheritance(content)
            stats["classes_converted"] = class_changes

            # Convert setUp/tearDown to fixtures
            content, setup_changes, manual_items = self._convert_setup_teardown(content)
            stats["setUp_converted"] = setup_changes[0]
            stats["tearDown_converted"] = setup_changes[1]
            stats["manual_review_needed"].extend(manual_items)

            # Improve test naming if basic pattern detected
            content, naming_improvements = self._improve_test_naming(content)

            if content != original_content:
                if not self.dry_run:
                    # Create backup
                    backup_path = file_path.with_suffix(".py.unittest_backup")
                    with open(backup_path, "w", encoding="utf-8") as f:
                        f.write(original_content)

                    # Write migrated content
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    print(f"✅ Migrated {file_path} (backup saved to {backup_path})")
                else:
                    print(f"🔍 [DRY RUN] Would migrate {file_path}")

                stats["migrated"] = True
            else:
                print(f"ℹ️  No changes needed for {file_path}")
                stats["migrated"] = False

            return stats

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return {
                "file": str(file_path),
                "error": str(e),
                "migrated": False,
            }

    def _update_imports(self, content: str) -> Tuple[str, int]:
        """Update import statements."""
        changes = 0
        for old_import, new_import in self.import_replacements.items():
            if old_import in content:
                if new_import:  # Replace
                    content = content.replace(old_import, new_import)
                else:  # Remove
                    content = re.sub(rf"^{re.escape(old_import)}$", "", content, flags=re.MULTILINE)
                changes += 1

        # Add pytest import if not present and assertions were found
        if "assert" in content and "import pytest" not in content:
            # Find the first import line and add pytest import after it
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith("from "):
                    lines.insert(i + 1, "import pytest")
                    content = "\n".join(lines)
                    changes += 1
                    break

        return content, changes

    def _convert_assertions(self, content: str) -> Tuple[str, int]:
        """Convert unittest assertions to pytest assertions."""
        changes = 0
        for pattern, replacement in self.patterns:
            if pattern.startswith("self.assert"):
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    changes += len(matches)
        return content, changes

    def _convert_class_inheritance(self, content: str) -> Tuple[str, int]:
        """Convert unittest.TestCase inheritance."""
        changes = 0
        for pattern, replacement in self.patterns:
            if "TestCase" in pattern:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    changes += len(matches)
        return content, changes

    def _convert_setup_teardown(self, content: str) -> Tuple[str, Tuple[int, int], List[str]]:
        """Convert setUp/tearDown methods to pytest fixtures."""
        setup_changes = 0
        teardown_changes = 0
        manual_review = []

        # Find setUp methods
        setup_pattern = r"def setUp\(self\):(.*?)(?=def|\n\n|\Z)"
        setup_matches = re.findall(setup_pattern, content, re.DOTALL)

        if setup_matches:
            # This requires manual review - add comment
            manual_review.append("setUp method found - manual conversion to @pytest.fixture needed")
            setup_changes = len(setup_matches)

            # Add a comment for manual review
            content = re.sub(
                r"def setUp\(self\):",
                "# TODO: Convert to @pytest.fixture\n    def setUp(self):",
                content,
            )

        # Find tearDown methods
        teardown_pattern = r"def tearDown\(self\):(.*?)(?=def|\n\n|\Z)"
        teardown_matches = re.findall(teardown_pattern, content, re.DOTALL)

        if teardown_matches:
            manual_review.append("tearDown method found - manual conversion to fixture cleanup needed")
            teardown_changes = len(teardown_matches)

            # Add a comment for manual review
            content = re.sub(
                r"def tearDown\(self\):",
                "# TODO: Convert to fixture with yield/cleanup\n    def tearDown(self):",
                content,
            )

        return content, (setup_changes, teardown_changes), manual_review

    def _improve_test_naming(self, content: str) -> Tuple[str, int]:
        """Apply basic test naming improvements."""
        changes = 0

        # Find test methods with very basic names and suggest improvements
        basic_test_pattern = r"def (test_\w{1,10})\(self"
        matches = re.findall(basic_test_pattern, content)

        for match in matches:
            if len(match) <= 10:  # Very short test names
                # Add a comment suggesting better naming
                old_def = f"def {match}(self"
                new_def = f"# TODO: Consider more descriptive name like test_{match[5:]}_with_condition_should_result\n    def {match}(self"
                content = content.replace(old_def, new_def)
                changes += 1

        return content, changes

    def migrate_directory(self, directory: Path, pattern: str = "test_*.py") -> Dict[str, any]:
        """Migrate all test files in a directory."""
        if not directory.exists():
            raise FileNotFoundError(f"Directory {directory} does not exist")

        test_files = list(directory.glob(pattern))
        if not test_files:
            print(f"No test files found in {directory} matching pattern {pattern}")
            return {"files_processed": 0, "files_migrated": 0, "errors": []}

        results = {
            "files_processed": 0,
            "files_migrated": 0,
            "total_assertions_converted": 0,
            "total_classes_converted": 0,
            "errors": [],
            "manual_review_items": [],
            "file_details": [],
        }

        for file_path in test_files:
            if file_path.suffix == ".py":
                file_result = self.migrate_file(file_path)
                results["files_processed"] += 1
                results["file_details"].append(file_result)

                if file_result.get("migrated", False):
                    results["files_migrated"] += 1
                    results["total_assertions_converted"] += file_result.get("assertions_converted", 0)
                    results["total_classes_converted"] += file_result.get("classes_converted", 0)
                    results["manual_review_items"].extend(file_result.get("manual_review_needed", []))

                if "error" in file_result:
                    results["errors"].append(file_result)

        return results

    def generate_report(self, results: Dict[str, any]) -> str:
        """Generate a migration report."""
        report = []
        report.append("=" * 60)
        report.append("📊 UNITTEST TO PYTEST MIGRATION REPORT")
        report.append("=" * 60)
        report.append(f"Files processed: {results['files_processed']}")
        report.append(f"Files migrated: {results['files_migrated']}")
        report.append(f"Total assertions converted: {results['total_assertions_converted']}")
        report.append(f"Total classes converted: {results['total_classes_converted']}")
        report.append(f"Errors encountered: {len(results['errors'])}")
        report.append("")

        if results["manual_review_items"]:
            report.append("🔍 MANUAL REVIEW REQUIRED:")
            report.append("-" * 30)
            for item in set(results["manual_review_items"]):  # Remove duplicates
                report.append(f"• {item}")
            report.append("")

        if results["errors"]:
            report.append("❌ ERRORS:")
            report.append("-" * 30)
            for error in results["errors"]:
                report.append(f"• {error['file']}: {error['error']}")
            report.append("")

        report.append("📝 NEXT STEPS:")
        report.append("-" * 30)
        report.append("1. Review files marked for manual review")
        report.append("2. Run tests to ensure functionality is preserved")
        report.append("3. Apply naming convention improvements")
        report.append("4. Update imports and fixtures as needed")

        return "\n".join(report)


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description="Migrate unittest tests to pytest")
    parser.add_argument("path", help="Path to test file or directory to migrate")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--pattern", default="test_*.py", help="File pattern for directory migration")
    parser.add_argument("--report", help="Path to save migration report")

    args = parser.parse_args()

    migrator = UnittestToPytestMigrator(dry_run=args.dry_run)
    path = Path(args.path)

    if path.is_file():
        # Migrate single file
        result = migrator.migrate_file(path)
        print("\n" + "=" * 50)
        print(f"File: {result['file']}")
        print(f"Assertions converted: {result.get('assertions_converted', 0)}")
        print(f"Classes converted: {result.get('classes_converted', 0)}")
        if result.get("manual_review_needed"):
            print("Manual review needed for:")
            for item in result["manual_review_needed"]:
                print(f"  • {item}")

    elif path.is_dir():
        # Migrate directory
        results = migrator.migrate_directory(path, args.pattern)
        report = migrator.generate_report(results)
        print(report)

        if args.report:
            with open(args.report, "w") as f:
                f.write(report)
            print(f"\n📄 Report saved to {args.report}")

    else:
        print(f"❌ Error: {path} is not a valid file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
