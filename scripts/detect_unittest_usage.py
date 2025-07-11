#!/usr/bin/env python3
"""
Detect unittest usage in test files.

This script is used as a pre-commit hook to detect when new test files
are using unittest instead of pytest, and suggests migration.
"""

import sys
import re
from pathlib import Path


def check_unittest_usage(file_path: Path) -> bool:
    """
    Check if a test file uses unittest patterns.
    
    Returns:
        True if unittest usage is detected, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patterns that indicate unittest usage
        unittest_patterns = [
            r'import unittest',
            r'from unittest import TestCase',
            r'class \w+\(unittest\.TestCase\)',
            r'class \w+\(TestCase\)',
            r'self\.assert\w+\(',
            r'def setUp\(self\)',
            r'def tearDown\(self\)',
        ]
        
        violations = []
        for pattern in unittest_patterns:
            if re.search(pattern, content):
                violations.append(pattern)
        
        if violations:
            print(f"❌ {file_path}: Found unittest patterns:")
            for violation in violations:
                print(f"   • {violation}")
            print(f"   💡 Consider using pytest instead. Run: python scripts/unittest_to_pytest_migrator.py {file_path}")
            return True
            
        return False
        
    except Exception as e:
        print(f"❌ Error checking {file_path}: {e}")
        return True  # Fail safe - block commit on errors


def main():
    """Main entry point for pre-commit hook."""
    if len(sys.argv) < 2:
        print("Usage: detect_unittest_usage.py <file1> [file2] ...")
        sys.exit(1)
    
    files_with_unittest = []
    
    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)
        
        if file_path.suffix == '.py' and file_path.name.startswith('test_'):
            if check_unittest_usage(file_path):
                files_with_unittest.append(file_path)
    
    if files_with_unittest:
        print(f"\n🚨 Found unittest usage in {len(files_with_unittest)} test files")
        print("📝 To maintain consistency, please use pytest for new tests")
        print("🔧 Run the migration tool to convert existing unittest files:")
        print("   python scripts/unittest_to_pytest_migrator.py <file_path>")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()