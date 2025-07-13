#!/usr/bin/env python3
"""
Test naming convention validation script.

This script validates that test files follow the established naming conventions:
- File names: test_<module>_<feature>.py
- Class names: Test<Module><Feature>
- Function names: test_<action>_<condition>_<expected_result>
- Docstring presence and format
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class TestNamingValidator:
    """Validates test files against naming conventions."""

    def __init__(self):
        self.file_pattern = re.compile(r"^test_[a-z_]+\.py$")
        self.class_pattern = re.compile(r"^Test[A-Z][a-zA-Z]*$")
        self.function_pattern = re.compile(r"^test_[a-z_]+_should_[a-z_]+$|^test_[a-z_]+_when_[a-z_]+_should_[a-z_]+$")
        self.short_function_pattern = re.compile(r"^test_\w{1,10}$")

    def validate_file(self, file_path: Path) -> Dict[str, any]:
        """
        Validate a single test file.

        Returns:
            Dictionary with validation results
        """
        violations = []
        suggestions = []
        stats = {
            "file": str(file_path),
            "violations": [],
            "suggestions": [],
            "test_functions": 0,
            "test_classes": 0,
            "docstring_coverage": 0,
            "score": 0,
        }

        # Validate file name
        file_violations = self._validate_file_name(file_path)
        violations.extend(file_violations)

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST for detailed analysis
            tree = ast.parse(content)

            # Validate classes and functions
            class_violations, class_suggestions, class_count = self._validate_classes(tree)
            function_violations, function_suggestions, function_count, docstring_count = self._validate_functions(tree)

            violations.extend(class_violations)
            violations.extend(function_violations)
            suggestions.extend(class_suggestions)
            suggestions.extend(function_suggestions)

            stats["violations"] = violations
            stats["suggestions"] = suggestions
            stats["test_functions"] = function_count
            stats["test_classes"] = class_count
            stats["docstring_coverage"] = (docstring_count / function_count * 100) if function_count > 0 else 0
            stats["score"] = self._calculate_score(violations, suggestions, stats)

        except Exception as e:
            stats["error"] = str(e)
            stats["score"] = 0

        return stats

    def _validate_file_name(self, file_path: Path) -> List[str]:
        """Validate file naming convention."""
        violations = []

        if not self.file_pattern.match(file_path.name):
            violations.append(f"File name '{file_path.name}' doesn't follow pattern 'test_<module>_<feature>.py'")

        # Check for common anti-patterns
        if file_path.name == "test.py":
            violations.append("File name 'test.py' is too generic. Use 'test_<module>_<feature>.py'")

        if file_path.name.startswith("test_test_"):
            violations.append("File name has redundant 'test_' prefix")

        return violations

    def _validate_classes(self, tree: ast.AST) -> Tuple[List[str], List[str], int]:
        """Validate test class naming."""
        violations = []
        suggestions = []
        class_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and (node.name.startswith("Test") or "test" in node.name.lower()):
                class_count += 1

                if not self.class_pattern.match(node.name):
                    violations.append(f"Class '{node.name}' doesn't follow pattern 'Test<Module><Feature>'")

                    # Suggest improvements
                    if node.name.startswith("Test") and "_" in node.name:
                        suggested = node.name.replace("_", "")
                        suggestions.append(f"Consider renaming '{node.name}' to '{suggested}'")
                    elif not node.name.startswith("Test"):
                        suggested = f"Test{node.name}"
                        suggestions.append(f"Consider renaming '{node.name}' to '{suggested}'")

                # Check if class has docstring
                if not ast.get_docstring(node):
                    suggestions.append(f"Class '{node.name}' should have a docstring describing its purpose")

        return violations, suggestions, class_count

    def _validate_functions(self, tree: ast.AST) -> Tuple[List[str], List[str], int, int]:
        """Validate test function naming and documentation."""
        violations = []
        suggestions = []
        function_count = 0
        docstring_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                function_count += 1

                # Check docstring presence
                if ast.get_docstring(node):
                    docstring_count += 1
                else:
                    suggestions.append(f"Function '{node.name}' should have a docstring")

                # Validate naming pattern
                if self.short_function_pattern.match(node.name):
                    violations.append(f"Function '{node.name}' name is too short and not descriptive")
                    suggestions.append(f"Consider renaming '{node.name}' to follow pattern 'test_<action>_<condition>_should_<result>'")
                elif not self._is_acceptable_function_name(node.name):
                    suggestions.append(f"Function '{node.name}' could be more descriptive. Consider pattern 'test_<action>_<condition>_should_<result>'")

                # Check for common anti-patterns
                if node.name == "test_function":
                    violations.append(f"Function name '{node.name}' is too generic")

                if node.name.count("_") < 2:  # test_ + at least one more _
                    suggestions.append(f"Function '{node.name}' could be more descriptive with additional context")

        return violations, suggestions, function_count, docstring_count

    def _is_acceptable_function_name(self, name: str) -> bool:
        """Check if function name meets acceptable standards."""
        # Must have reasonable length
        if len(name) < 10:
            return False

        # Should have descriptive parts
        parts = name.split("_")[1:]  # Remove 'test' prefix
        if len(parts) < 2:
            return False

        # Check for descriptive keywords
        descriptive_keywords = [
            "should",
            "when",
            "with",
            "without",
            "given",
            "if",
            "returns",
            "raises",
            "creates",
            "updates",
            "deletes",
            "validates",
            "processes",
        ]

        return any(keyword in name for keyword in descriptive_keywords)

    def _calculate_score(self, violations: List[str], suggestions: List[str], stats: Dict) -> int:
        """Calculate a quality score from 0-100."""
        base_score = 100

        # Deduct points for violations (major issues)
        base_score -= len(violations) * 15

        # Deduct points for suggestions (minor issues)
        base_score -= len(suggestions) * 5

        # Bonus for good docstring coverage
        if stats["docstring_coverage"] > 80:
            base_score += 10
        elif stats["docstring_coverage"] > 50:
            base_score += 5

        # Ensure score doesn't go below 0
        return max(0, base_score)

    def validate_directory(self, directory: Path, pattern: str = "test_*.py") -> Dict[str, any]:
        """Validate all test files in a directory."""
        if not directory.exists():
            raise FileNotFoundError(f"Directory {directory} does not exist")

        test_files = list(directory.rglob(pattern))
        if not test_files:
            return {
                "files_processed": 0,
                "total_violations": 0,
                "total_suggestions": 0,
                "average_score": 0,
                "file_details": [],
            }

        results = {
            "files_processed": 0,
            "total_violations": 0,
            "total_suggestions": 0,
            "total_functions": 0,
            "total_classes": 0,
            "average_docstring_coverage": 0,
            "average_score": 0,
            "file_details": [],
        }

        total_score = 0
        total_docstring_coverage = 0

        for file_path in test_files:
            if file_path.suffix == ".py":
                file_result = self.validate_file(file_path)
                results["files_processed"] += 1
                results["file_details"].append(file_result)

                results["total_violations"] += len(file_result.get("violations", []))
                results["total_suggestions"] += len(file_result.get("suggestions", []))
                results["total_functions"] += file_result.get("test_functions", 0)
                results["total_classes"] += file_result.get("test_classes", 0)

                total_score += file_result.get("score", 0)
                total_docstring_coverage += file_result.get("docstring_coverage", 0)

        if results["files_processed"] > 0:
            results["average_score"] = total_score / results["files_processed"]
            results["average_docstring_coverage"] = total_docstring_coverage / results["files_processed"]

        return results

    def generate_report(self, results: Dict[str, any], detailed: bool = False) -> str:
        """Generate a validation report."""
        report = []
        report.append("=" * 60)
        report.append("📊 TEST NAMING VALIDATION REPORT")
        report.append("=" * 60)

        # Summary statistics
        report.append(f"Files processed: {results['files_processed']}")
        report.append(f"Total violations: {results['total_violations']}")
        report.append(f"Total suggestions: {results['total_suggestions']}")
        report.append(f"Total test functions: {results['total_functions']}")
        report.append(f"Total test classes: {results['total_classes']}")
        report.append(f"Average score: {results['average_score']:.1f}/100")
        report.append(f"Average docstring coverage: {results['average_docstring_coverage']:.1f}%")
        report.append("")

        # Quality assessment
        avg_score = results["average_score"]
        if avg_score >= 90:
            grade = "🌟 Excellent"
        elif avg_score >= 80:
            grade = "✅ Good"
        elif avg_score >= 70:
            grade = "⚠️  Needs Improvement"
        else:
            grade = "❌ Poor"

        report.append(f"Overall Quality: {grade}")
        report.append("")

        # Top issues summary
        all_violations = []
        all_suggestions = []

        for file_detail in results["file_details"]:
            all_violations.extend(file_detail.get("violations", []))
            all_suggestions.extend(file_detail.get("suggestions", []))

        if all_violations:
            report.append("🚨 TOP VIOLATIONS:")
            report.append("-" * 30)
            violation_counts = {}
            for violation in all_violations:
                # Extract the type of violation
                violation_type = violation.split("'")[0] if "'" in violation else violation
                violation_counts[violation_type] = violation_counts.get(violation_type, 0) + 1

            for violation_type, count in sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                report.append(f"• {violation_type} ({count} files)")
            report.append("")

        if detailed:
            # Detailed file-by-file results
            report.append("📁 DETAILED RESULTS:")
            report.append("-" * 30)

            # Sort files by score (worst first)
            sorted_files = sorted(results["file_details"], key=lambda x: x.get("score", 0))

            for file_detail in sorted_files:
                score = file_detail.get("score", 0)
                file_name = Path(file_detail["file"]).name

                if score < 80:  # Only show problematic files in detailed view
                    report.append(f"\n📄 {file_name} (Score: {score}/100)")

                    violations = file_detail.get("violations", [])
                    if violations:
                        report.append("  Violations:")
                        for violation in violations:
                            report.append(f"    ❌ {violation}")

                    suggestions = file_detail.get("suggestions", [])
                    if suggestions:
                        report.append("  Suggestions:")
                        for suggestion in suggestions[:3]:  # Show only top 3 suggestions
                            report.append(f"    💡 {suggestion}")
                        if len(suggestions) > 3:
                            report.append(f"    ... and {len(suggestions) - 3} more")

        report.append("\n📝 RECOMMENDED ACTIONS:")
        report.append("-" * 30)

        if results["total_violations"] > 0:
            report.append("1. Fix all naming violations (required)")
        if results["average_docstring_coverage"] < 70:
            report.append("2. Add docstrings to test functions")
        if results["average_score"] < 80:
            report.append("3. Improve test function naming to be more descriptive")
        if results["total_suggestions"] > results["files_processed"] * 2:
            report.append("4. Review and apply naming suggestions")

        report.append("\n💡 NAMING TIPS:")
        report.append("-" * 30)
        report.append("• Use pattern: test_<action>_<condition>_should_<result>")
        report.append("• Examples: test_create_session_with_valid_config_should_succeed")
        report.append("• Add docstrings explaining test purpose")
        report.append("• Keep class names as Test<Module><Feature>")

        return "\n".join(report)

    def fix_suggestions(self, file_path: Path, dry_run: bool = True) -> Dict[str, any]:
        """Apply automatic fixes for common naming issues."""
        print(f"🔧 Analyzing {file_path} for automatic fixes...")

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content
        fixes_applied = []

        # Fix common patterns
        fixes = [
            # Add basic docstrings to functions without them
            (r"(def test_\w+\([^)]*\):)\n( +)", r'\1\n\2"""\n\2Test \1 functionality.\n\2"""\n\2'),
            # Suggest better names for very short test functions (as comments)
            (r"def (test_\w{1,8})\(", r"# TODO: Consider more descriptive name\n    def \1("),
        ]

        for pattern, replacement in fixes:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                fixes_applied.append(f"Applied pattern: {pattern[:30]}...")

        result = {
            "file": str(file_path),
            "fixes_applied": len(fixes_applied),
            "fixes_list": fixes_applied,
            "changed": content != original_content,
        }

        if not dry_run and result["changed"]:
            # Create backup
            backup_path = file_path.with_suffix(".py.naming_backup")
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original_content)

            # Write fixed content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Applied fixes to {file_path} (backup: {backup_path})")
        elif result["changed"]:
            print(f"🔍 [DRY RUN] Would apply {len(fixes_applied)} fixes to {file_path}")
        else:
            print(f"ℹ️  No automatic fixes available for {file_path}")

        return result


def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(description="Validate test naming conventions")
    parser.add_argument("path", help="Path to test file or directory to validate")
    parser.add_argument("--detailed", action="store_true", help="Show detailed per-file results")
    parser.add_argument("--fix", action="store_true", help="Apply automatic fixes where possible")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    parser.add_argument("--pattern", default="test_*.py", help="File pattern for directory validation")
    parser.add_argument("--report", help="Path to save validation report")
    parser.add_argument("--min-score", type=int, default=70, help="Minimum acceptable score")

    args = parser.parse_args()

    validator = TestNamingValidator()
    path = Path(args.path)

    if path.is_file():
        # Validate single file
        result = validator.validate_file(path)

        print(f"\n📄 {path.name}")
        print(f"Score: {result['score']}/100")
        print(f"Test functions: {result['test_functions']}")
        print(f"Docstring coverage: {result['docstring_coverage']:.1f}%")

        if result["violations"]:
            print("\n❌ Violations:")
            for violation in result["violations"]:
                print(f"  • {violation}")

        if result["suggestions"]:
            print("\n💡 Suggestions:")
            for suggestion in result["suggestions"]:
                print(f"  • {suggestion}")

        if args.fix:
            fix_result = validator.fix_suggestions(path, dry_run=args.dry_run)
            if fix_result["fixes_applied"] > 0:
                print(f"\n🔧 Applied {fix_result['fixes_applied']} automatic fixes")

        # Exit with error code if score is below minimum
        if result["score"] < args.min_score:
            print(f"\n❌ Score {result['score']} is below minimum {args.min_score}")
            sys.exit(1)

    elif path.is_dir():
        # Validate directory
        results = validator.validate_directory(path, args.pattern)
        report = validator.generate_report(results, detailed=args.detailed)
        print(report)

        if args.report:
            with open(args.report, "w") as f:
                f.write(report)
            print(f"\n📄 Report saved to {args.report}")

        # Exit with error code if average score is below minimum
        if results["average_score"] < args.min_score:
            print(f"\n❌ Average score {results['average_score']:.1f} is below minimum {args.min_score}")
            sys.exit(1)

    else:
        print(f"❌ Error: {path} is not a valid file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
