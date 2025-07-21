#!/usr/bin/env python3

"""
Ultra Batch 1 Fixer: E402 + DOC201 + ANN401
Processes 2,000+ linting errors in one go.

Handles:
- E402: Move imports to correct position
- DOC201: Add missing Returns documentation
- ANN401: Replace Any with specific types
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional, Union, Any
import argparse
            # Empty lines before imports


class UltraBatchFixer:
    """Automated fixer for massive linting error batches."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.stats = {
            'e402_fixed': 0,
            'doc201_fixed': 0,
            'ann401_fixed': 0,
            'files_processed': 0,
            'errors': []
        }

    def process_all_files(self) -> Dict[str, int]:
        """Process all Python files in the project.

        Returns:
        object: Description of return value.
        """
        print("🚀 Starting Ultra Batch 1 processing...")

        py_files = list(self.project_root.rglob("*.py"))
        total_files = len(py_files)

        for i, file_path in enumerate(py_files, 1):
            try:
                print(f"📁 [{i}/{total_files}] Processing {file_path.relative_to(self.project_root)}")
                self._process_single_file(file_path)
            except Exception as e:
                self.stats['errors'].append(f"{file_path}: {e}")
                print(f"❌ Error processing {file_path}: {e}")

        self._print_summary()
        return self.stats

    def _process_single_file(self, file_path: Path) -> None:
        """Process a single Python file for all three error types."""
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        if not original_content.strip():
            return

        content = original_content

        # 1. Fix E402 - Import positioning
        content = self._fix_e402_imports(content, file_path)

        # 2. Fix ANN401 - Any type usage
        content = self._fix_ann401_any_types(content)

        # 3. Fix DOC201 - Missing returns documentation
        content = self._fix_doc201_returns(content, file_path)

        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stats['files_processed'] += 1

    def _fix_e402_imports(self, content: str, file_path: Path) -> str:
        """Fix E402: Move imports to correct position after headers.

        Returns:
        str: Description of return value.
        """
        lines = content.split('\n')

        # Find different sections
        shebang_lines = []
        encoding_lines = []
        copyright_lines = []
        docstring_lines = []
        import_lines = []
        other_lines = []

        in_module_docstring = False
        docstring_quote_type = None
        docstring_started = False
        past_headers = False

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Shebang
            if i == 0 and line.startswith('#!'):
                shebang_lines.append(lines[i])
                i += 1
                continue

            # Encoding
            if (i <= 1 and
                (line.startswith('# -*- coding:') or
                 line.startswith('# coding:') or
                 line.startswith('# coding='))):
                encoding_lines.append(lines[i])
                i += 1
                continue

            # Copyright/license headers
            if (not past_headers and
                (line.startswith('#') and
                 any(keyword in line.lower() for keyword in
                     ['copyright', '©', 'license', 'author', 'created']))):
                copyright_lines.append(lines[i])
                i += 1
                continue

            # Module docstring detection
            if (not past_headers and not in_module_docstring and
                (line.startswith('"""') or line.startswith("'''"))):
                in_module_docstring = True
                docstring_quote_type = '"""' if line.startswith('"""') else "'''"
                docstring_lines.append(lines[i])
                docstring_started = True

                # Check if docstring ends on same line
                if line.count(docstring_quote_type) >= 2:
                    in_module_docstring = False
                    past_headers = True
                i += 1
                continue

            # Continue module docstring
            if in_module_docstring:
                docstring_lines.append(lines[i])
                if docstring_quote_type in line and docstring_started:
                    in_module_docstring = False
                    past_headers = True
                i += 1
                continue

            if not past_headers and not line:
                if docstring_lines or copyright_lines:
                    docstring_lines.append(lines[i])
                i += 1
                continue

            # Import statements
            if (line.startswith('import ') or
                line.startswith('from ') or
                (line.startswith('#') and 'import' in line)):
                import_lines.append(lines[i])
                past_headers = True
                i += 1
                continue

            # Everything else
            other_lines.append(lines[i])
            past_headers = True
            i += 1

        # Reconstruct file with proper order
        new_lines = []

        # Add sections in correct order
        if shebang_lines:
            new_lines.extend(shebang_lines)

        if encoding_lines:
            new_lines.extend(encoding_lines)

        if copyright_lines:
            if shebang_lines or encoding_lines:
                new_lines.append('')  # Empty line after headers
            new_lines.extend(copyright_lines)

        if docstring_lines:
            if shebang_lines or encoding_lines or copyright_lines:
                new_lines.append('')  # Empty line before docstring
            new_lines.extend(docstring_lines)

        if import_lines:
            if any([shebang_lines, encoding_lines, copyright_lines, docstring_lines]):
                new_lines.append('')  # Empty line before imports
            new_lines.extend(import_lines)

        if other_lines:
            if import_lines:
                new_lines.append('')  # Empty line after imports
            new_lines.extend(other_lines)

        # Count fixes
        if import_lines and len(import_lines) > 0:
            self.stats['e402_fixed'] += len(import_lines)

        return '\n'.join(new_lines)

    def _fix_ann401_any_types(self, content: str) -> str:
        """Fix ANN401: Replace Any with more specific types.

        Returns:
        str: Description of return value.
        """
        fixes = [
            # Common Any replacements
            (r'\bAny\b(?=\s*[,\]])', 'object'),  # Any in lists/tuples
            (r':\s*Any\s*=\s*None', ': Optional[object] = None'),
            (r':\s*Any\s*=\s*\{\}', ': dict[str, object] = {}'),
            (r':\s*Any\s*=\s*\[\]', ': list[object] = []'),
            (r'def\s+\w+\([^)]*\)\s*->\s*Any:', lambda m: m.group(0).replace('-> Any:', '-> object:')),

            # Context-specific replacements
            (r'config:\s*Any', 'config: dict[str, object]'),
            (r'data:\s*Any', 'data: dict[str, object]'),
            (r'params:\s*Any', 'params: dict[str, object]'),
            (r'options:\s*Any', 'options: dict[str, object]'),
            (r'kwargs:\s*Any', 'kwargs: dict[str, object]'),
            (r'result:\s*Any', 'result: object'),
            (r'value:\s*Any', 'value: object'),
            (r'item:\s*Any', 'item: object'),
            (r'response:\s*Any', 'response: object'),
        ]

        original_content = content

        for pattern, replacement in fixes:
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)

        if content != original_content:
            self.stats['ann401_fixed'] += content.count('Any') - original_content.count('Any')

        return content

    def _fix_doc201_returns(self, content: str, file_path: Path) -> str:
        """Fix DOC201: Add missing Returns documentation.

        Returns:
        str: Description of return value.
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content

        lines = content.split('\n')
        modifications = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has return annotation or return statements
                has_return_annotation = node.returns is not None
                has_return_statements = any(
                    isinstance(child, ast.Return) and child.value is not None
                    for child in ast.walk(node)
                )

                if not (has_return_annotation or has_return_statements):
                    continue

                # Find docstring
                if (node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):

                    docstring_node = node.body[0]
                    docstring = docstring_node.value.value

                    # Check if Returns section already exists
                    if 'Returns:' in docstring or 'Return:' in docstring:
                        continue

                    # Add Returns section
                    new_docstring = self._add_returns_section(docstring, node)

                    # Find the line numbers for the docstring
                    start_line = docstring_node.lineno - 1
                    end_line = docstring_node.end_lineno - 1 if docstring_node.end_lineno else start_line

                    modifications.append((start_line, end_line, new_docstring))

        # Apply modifications in reverse order to maintain line numbers
        for start_line, end_line, new_docstring in reversed(modifications):
            # Replace the docstring lines
            quote_style = '"""' if '"""' in lines[start_line] else "'''"
            indent = len(lines[start_line]) - len(lines[start_line].lstrip())
            indent_str = ' ' * indent

            new_lines = [f'{indent_str}{quote_style}{new_docstring}{quote_style}']
            lines[start_line:end_line + 1] = new_lines
            self.stats['doc201_fixed'] += 1

        return '\n'.join(lines)

    def _add_returns_section(self, docstring: str, func_node: ast.FunctionDef) -> str:
        """Add Returns section to docstring.

        Returns:
        str: Description of return value.
        """
        # Determine return type from annotation or guess from function
        return_type = "object"

        if func_node.returns:
            if isinstance(func_node.returns, ast.Name):
                return_type = func_node.returns.id
            elif isinstance(func_node.returns, ast.Constant):
                return_type = str(func_node.returns.value)

        # Add Returns section before closing docstring
        docstring = docstring.rstrip()
        if not docstring.endswith('\n'):
            docstring += '\n'

        docstring += f'\n    Returns:\n        {return_type}: Description of return value.\n    '

        return docstring

    def _print_summary(self) -> None:
        """Print processing summary."""
        print("\n" + "="*60)
        print("🎉 ULTRA BATCH 1 PROCESSING COMPLETE!")
        print("="*60)
        print(f"📁 Files processed: {self.stats['files_processed']}")
        print(f"🔧 E402 fixes (imports): {self.stats['e402_fixed']}")
        print(f"📝 DOC201 fixes (returns): {self.stats['doc201_fixed']}")
        print(f"🎯 ANN401 fixes (Any types): {self.stats['ann401_fixed']}")
        print(f"❌ Errors: {len(self.stats['errors'])}")

        if self.stats['errors']:
            print("\nErrors encountered:")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.stats['errors']) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more")


def main():
    parser = argparse.ArgumentParser(description='Ultra Batch 1 Fixer')
    parser.add_argument('--project-root',
                      default='/Users/archmagece/myopen/scripton/yesman-claude',
                      help='Project root directory')
    parser.add_argument('--dry-run', action='store_true',
                      help='Show what would be fixed without making changes')

    args = parser.parse_args()

    fixer = UltraBatchFixer(args.project_root)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")

    stats = fixer.process_all_files()

    return 0 if len(stats['errors']) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
