#!/usr/bin/env python3
"""Comprehensive COM818 fixer for remaining trailing comma issues."""

import re
import subprocess
import sys
import json
from pathlib import Path


class ComprehensiveCOM818Fixer:
    """Fix all COM818 trailing comma issues."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.stats = {'files_fixed': 0, 'errors_fixed': 0}

    def get_com818_files(self) -> dict:
        """Get files with COM818 errors."""
        try:
            result = subprocess.run([
                'ruff', 'check', '--select', 'COM818', '--format', 'json'
            ], capture_output=True, text=True, cwd=self.project_root)

            if result.stdout:
                errors = json.loads(result.stdout)
                file_errors = {}
                for error in errors:
                    filename = error.get('filename', '')
                    if filename not in file_errors:
                        file_errors[filename] = []
                    file_errors[filename].append(error)
                return file_errors
        except:
            pass
        return {}

    def fix_trailing_commas(self, content: str) -> tuple[str, int]:
        """Fix all trailing comma patterns."""
        fixes = 0
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            original_line = line

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                fixed_lines.append(line)
                continue

            # Pattern 1: Single import with trailing comma in parentheses
            # from module import (item,) -> from module import item
            pattern1 = r'^(\s*from\s+[\w\.]+\s+import\s+)\(([^,\(\)]+),\)(.*)$'
            match = re.match(pattern1, line)
            if match:
                prefix, item, suffix = match.groups()
                line = f"{prefix}{item.strip()}{suffix}"
                fixes += 1

            # Pattern 2: Trailing comma at end of import lists
            elif line.strip().endswith(',') and ('import' in line or any(keyword in line for keyword in ['from', 'import'])):
                # Check if this is inside a parenthetical import
                if i > 0:
                    # Look for opening paren in previous lines
                    has_open_paren = False
                    has_close_paren = False
                    for j in range(max(0, i-10), i+1):
                        if j < len(lines):
                            if '(' in lines[j]:
                                has_open_paren = True
                            if ')' in lines[j]:
                                has_close_paren = True

                    # Look ahead for closing paren
                    for j in range(i+1, min(len(lines), i+5)):
                        if ')' in lines[j]:
                            has_close_paren = True
                            break

                    # If we're in a multi-line import and this is the last item
                    if has_open_paren and not has_close_paren:
                        # Check if next non-empty line has closing paren
                        for j in range(i+1, min(len(lines), i+5)):
                            next_line = lines[j].strip()
                            if next_line:
                                if next_line == ')':
                                    # This is the last item, remove trailing comma
                                    line = line.rstrip(' ,')
                                    fixes += 1
                                break
                    elif not has_open_paren and line.count(',') == 1:
                        # Single line import with trailing comma
                        line = line.rstrip(' ,')
                        fixes += 1

            # Pattern 3: Trailing comma in function/method calls (single argument)
            elif line.strip().endswith(',)') and 'import' not in line:
                # Check if this is a single argument
                paren_content = re.search(r'\(([^)]+),\)', line)
                if paren_content:
                    content_inside = paren_content.group(1)
                    # If it's a single item (no commas except the trailing one)
                    if ',' not in content_inside:
                        line = line.replace(',)', ')')
                        fixes += 1

            # Pattern 4: Trailing comma in single-item tuples/lists where prohibited
            elif ',)' in line or ',]' in line:
                # Fix single-item tuples/lists
                line = re.sub(r'\(([^,)]+),\)', r'(\1)', line)  # (item,) -> (item)
                line = re.sub(r'\[([^,\]]+),\]', r'[\1]', line)  # [item,] -> [item]
                fixes += 1

            fixed_lines.append(line)

        return '\n'.join(fixed_lines), fixes

    def process_file(self, file_path: Path) -> bool:
        """Process a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            fixed_content, fixes = self.fix_trailing_commas(content)

            if fixes > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"✅ Fixed {file_path}: {fixes} trailing commas")
                self.stats['errors_fixed'] += fixes
                return True
            return False

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False

    def run(self) -> None:
        """Run the comprehensive fixer."""
        print("🔧 COMPREHENSIVE COM818 FIXER")
        print("=" * 50)

        # Get all files with COM818 errors
        file_errors = self.get_com818_files()
        print(f"📁 Found {len(file_errors)} files with COM818 errors")

        for file_path_str in file_errors.keys():
            file_path = Path(file_path_str)
            if self.process_file(file_path):
                self.stats['files_fixed'] += 1

        print(f"\n✅ Fixed {self.stats['files_fixed']} files")
        print(f"🔧 Fixed {self.stats['errors_fixed']} trailing comma errors")


def main():
    """Main function."""
    project_path = "/Users/archmagece/myopen/scripton/yesman-claude"

    if len(sys.argv) > 1:
        project_path = sys.argv[1]

    fixer = ComprehensiveCOM818Fixer(project_path)
    fixer.run()


if __name__ == "__main__":
    main()
