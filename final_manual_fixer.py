#!/usr/bin/env python3
"""Final manual fixer for remaining COM818 and syntax errors."""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class FinalManualFixer:
    """Manual fixer for complex syntax and COM818 issues."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.stats = {
            'com818_fixed': 0,
            'syntax_fixed': 0,
            'files_processed': 0,
            'files_skipped': 0
        }

    def fix_file(self, file_path: Path) -> bool:
        """Fix a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix broken import structures
            content = self.fix_broken_imports(content)

            # Fix COM818 trailing comma issues
            content = self.fix_com818_issues(content)

            # Fix malformed file structures
            content = self.fix_file_structure(content)

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Fixed {file_path}")
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            return False

    def fix_broken_imports(self, content: str) -> str:
        """Fix broken import statements."""
        lines = content.split('\n')
        fixed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Handle broken multi-line imports
            if re.match(r'^from .+ import \(', line) and not line.strip().endswith(')'):
                # This is a broken import - try to collect all related lines
                import_lines = [line]
                i += 1

                # Look for the actual import items
                while i < len(lines):
                    next_line = lines[i]

                    # If we find another 'from ... import (' pattern, this import is broken
                    if re.match(r'^from .+ import \(', next_line):
                        # Previous import was broken, skip it
                        break

                    # If we find import items, collect them
                    if re.match(r'^\s+[A-Za-z_]', next_line) or next_line.strip() == ')':
                        import_lines.append(next_line)
                        if next_line.strip() == ')':
                            i += 1
                            break

                    # If we find content that's not import-related, break
                    if next_line.strip() and not re.match(r'^\s*[#]', next_line):
                        break

                    import_lines.append(next_line)
                    i += 1

                # Try to reconstruct a valid import
                if len(import_lines) > 1:
                    # Extract module name from first line
                    first_match = re.match(r'^from (.+) import \(', import_lines[0])
                    if first_match:
                        module_name = first_match.group(1)

                        # Collect import items
                        items = []
                        for import_line in import_lines[1:]:
                            if import_line.strip() and import_line.strip() != ')':
                                # Extract item names
                                item_match = re.search(r'([A-Za-z_][A-Za-z0-9_]*)', import_line)
                                if item_match:
                                    items.append(item_match.group(1))

                        # Reconstruct import
                        if items:
                            if len(items) == 1:
                                fixed_lines.append(f"from {module_name} import {items[0]}")
                            else:
                                fixed_lines.append(f"from {module_name} import (")
                                for item in items[:-1]:
                                    fixed_lines.append(f"    {item},")
                                fixed_lines.append(f"    {items[-1]},")
                                fixed_lines.append(")")
                        else:
                            # Skip broken import
                            pass
                    else:
                        # Keep original broken lines
                        fixed_lines.extend(import_lines)
                else:
                    # Single line import
                    fixed_lines.append(line)
                continue

            fixed_lines.append(line)
            i += 1

        return '\n'.join(fixed_lines)

    def fix_com818_issues(self, content: str) -> str:
        """Fix COM818 trailing comma issues."""
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            # Fix single-item imports with trailing comma
            # Pattern: from module import (item,)
            pattern1 = r'^(\s*from\s+[\w\.]+\s+import\s+)\(([^,\(\)]+),\)(.*)$'
            match = re.match(pattern1, line)
            if match:
                prefix, item, suffix = match.groups()
                fixed_line = f"{prefix}{item.strip()}{suffix}"
                fixed_lines.append(fixed_line)
                self.stats['com818_fixed'] += 1
                continue

            # Fix trailing commas in single-line imports
            if line.strip().endswith(',') and 'import' in line and '(' not in line:
                if line.count(',') == 1:
                    fixed_line = line.rstrip(' ,')
                    fixed_lines.append(fixed_line)
                    self.stats['com818_fixed'] += 1
                    continue

            # Fix trailing commas in parameter lists (single item)
            pattern2 = r'^(\s*[^#]*)\(([^,\(\)]+),\)(.*)$'
            match = re.match(pattern2, line)
            if match and 'import' not in line:
                prefix, item, suffix = match.groups()
                if '=' not in item and not item.strip().startswith('"'):  # Avoid string literals
                    fixed_line = f"{prefix}({item.strip()}){suffix}"
                    fixed_lines.append(fixed_line)
                    self.stats['com818_fixed'] += 1
                    continue

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_file_structure(self, content: str) -> str:
        """Fix malformed file structures."""
        lines = content.split('\n')
        fixed_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Fix misplaced copyright notices in imports
            if 'Copyright' in line and i > 0:
                prev_line = lines[i-1] if i > 0 else ''
                if 'import' in prev_line or 'from' in prev_line:
                    # Move copyright to after imports
                    copyright_lines = []
                    while i < len(lines) and ('Copyright' in lines[i] or 'Licensed' in lines[i] or lines[i].strip().startswith('#')):
                        copyright_lines.append(lines[i])
                        i += 1

                    # Look for end of imports
                    import_end = len(fixed_lines)
                    while import_end > 0 and ('import' in fixed_lines[import_end-1] or 'from' in fixed_lines[import_end-1]):
                        import_end -= 1

                    # Insert copyright after imports
                    if copyright_lines:
                        fixed_lines.append('')
                        fixed_lines.extend(copyright_lines)
                        fixed_lines.append('')
                    continue

            # Skip duplicate copyright notices
            if 'Copyright' in line:
                # Check if we already have copyright
                has_copyright = any('Copyright' in existing for existing in fixed_lines)
                if has_copyright:
                    i += 1
                    continue

            fixed_lines.append(line)
            i += 1

        return '\n'.join(fixed_lines)

    def get_problem_files(self) -> List[Path]:
        """Get list of files with syntax errors or COM818 issues."""
        problem_files = []

        # Look for specific problem files mentioned in ruff output
        problem_patterns = [
            'commands/multi_agent/cli.py',
            'tests/unit/dashboard/renderers/test_*.py',
            'tests/unit/utils/test_validation.py'
        ]

        for pattern in problem_patterns:
            if '*' in pattern:
                # Handle glob patterns
                for file_path in self.project_root.glob(pattern):
                    if file_path.suffix == '.py':
                        problem_files.append(file_path)
            else:
                file_path = self.project_root / pattern
                if file_path.exists():
                    problem_files.append(file_path)

        # Also find files with many COM818 errors
        try:
            import subprocess
            result = subprocess.run([
                'ruff', 'check', '--select', 'COM818', '--format', 'json'
            ], capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                import json
                errors = json.loads(result.stdout)
                file_counts = {}
                for error in errors:
                    filename = error.get('filename', '')
                    file_counts[filename] = file_counts.get(filename, 0) + 1

                # Add files with many COM818 errors
                for filename, count in file_counts.items():
                    if count >= 3:  # Files with 3+ COM818 errors
                        problem_files.append(Path(filename))
        except:
            pass

        return list(set(problem_files))  # Remove duplicates

    def run(self) -> None:
        """Run the manual fixer."""
        print("🔧 FINAL MANUAL FIXER: Syntax and COM818 Issues")
        print("=" * 60)

        problem_files = self.get_problem_files()
        print(f"📁 Found {len(problem_files)} problem files")

        for file_path in problem_files:
            if self.fix_file(file_path):
                self.stats['files_processed'] += 1
            else:
                self.stats['files_skipped'] += 1

        self.print_summary()

    def print_summary(self) -> None:
        """Print summary of fixes."""
        print("\n" + "="*60)
        print("🎉 FINAL MANUAL FIXES COMPLETE!")
        print("="*60)
        print(f"📁 Files processed: {self.stats['files_processed']}")
        print(f"⚠️  Files skipped: {self.stats['files_skipped']}")
        print(f"🔧 COM818 fixes: {self.stats['com818_fixed']}")
        print(f"🔨 Syntax fixes: {self.stats['syntax_fixed']}")
        print("="*60)


def main():
    """Main function."""
    project_path = "/Users/archmagece/myopen/scripton/yesman-claude"

    if len(sys.argv) > 1:
        project_path = sys.argv[1]

    fixer = FinalManualFixer(project_path)
    fixer.run()


if __name__ == "__main__":
    main()
