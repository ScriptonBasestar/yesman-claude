#!/usr/bin/env python3
"""Ultra Batch 4 Fixer: COM818 + D200 + E303 - 1,210개 에러 일괄 처리.

COM818: Trailing comma on bare tuple 금지 (608개)
D200: 한줄 독스트링이 한줄에 맞지 않음 (390개)  
E303: 너무 많은 빈 줄 (212개)
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class UltraBatch4Fixer:
    """COM818, D200, E303 에러 대량 수정기."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.stats = {
            'com818_fixed': 0,
            'd200_fixed': 0,
            'e303_fixed': 0,
            'files_processed': 0,
            'skipped_files': 0
        }
        self.processed_files: Set[Path] = set()
        
    def is_syntax_safe(self, file_path: Path) -> bool:
        """파일이 syntax 안전한지 확인."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic syntax validation
            compile(content, str(file_path), 'exec')
            return True
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            return False
    
    def fix_com818_trailing_comma(self, content: str) -> Tuple[str, int]:
        """COM818: 단일 import의 trailing comma 제거."""
        fixes = 0
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            original_line = line
            
            # Pattern 1: from module import (item,) -> from module import item
            pattern1 = r'^(\s*from\s+[\w\.]+\s+import\s+)\(([^,\(\)]+),\)(.*)$'
            match = re.match(pattern1, line)
            if match:
                prefix, item, suffix = match.groups()
                line = f"{prefix}{item.strip()}{suffix}"
                fixes += 1
            
            # Pattern 2: Multi-line imports with trailing commas
            if line.strip().endswith(',') and '(' in content and ')' in content:
                # Check if this is a single item in parentheses
                if re.search(r'^\s*[^,\(\)]+,$', line.strip()):
                    line = line.rstrip(' ,')
                    fixes += 1
            
            # Pattern 3: Simple trailing comma in imports
            if line.strip().endswith(',') and 'import' in line and '(' not in line:
                # Single line import with trailing comma
                if line.count(',') == 1 and line.strip().endswith(','):
                    line = line.rstrip(' ,')
                    fixes += 1
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), fixes
    
    def fix_d200_multiline_docstring(self, content: str) -> Tuple[str, int]:
        """D200: 한줄 독스트링을 한줄로 병합."""
        fixes = 0
        
        # Pattern: """Text\n\n    """를 """Text."""로 변경
        pattern = r'(\s+)"""([^"]+?)\n\s*\n\s*"""'
        
        def replace_func(match):
            nonlocal fixes
            indent, text = match.groups()
            # Clean the text and make it a one-liner
            clean_text = text.strip()
            if clean_text and not clean_text.endswith('.'):
                clean_text += '.'
            fixes += 1
            return f'{indent}"""{clean_text}"""'
        
        content = re.sub(pattern, replace_func, content, flags=re.MULTILINE)
        
        # Also handle triple-quoted strings at start of line
        pattern2 = r'^(\s*)"""([^"]+?)\n\s*\n\s*"""'
        content = re.sub(pattern2, replace_func, content, flags=re.MULTILINE)
        
        return content, fixes
    
    def fix_e303_blank_lines(self, content: str) -> Tuple[str, int]:
        """E303: 과도한 빈 줄 제거."""
        fixes = 0
        lines = content.split('\n')
        fixed_lines = []
        blank_count = 0
        
        for i, line in enumerate(lines):
            if line.strip() == '':
                blank_count += 1
            else:
                # Check if we need to reduce blank lines
                if blank_count > 2:
                    # Too many blank lines before non-blank line
                    if i > 0:
                        # Add at most 2 blank lines
                        for _ in range(min(2, blank_count)):
                            fixed_lines.append('')
                        fixes += blank_count - 2
                    blank_count = 0
                else:
                    # Add the collected blank lines
                    for _ in range(blank_count):
                        fixed_lines.append('')
                    blank_count = 0
                
                fixed_lines.append(line)
        
        # Handle trailing blank lines
        if blank_count > 1:
            fixed_lines.append('')
            fixes += blank_count - 1
        elif blank_count == 1:
            fixed_lines.append('')
        
        return '\n'.join(fixed_lines), fixes
    
    def process_file(self, file_path: Path) -> bool:
        """단일 파일 처리."""
        if file_path in self.processed_files:
            return True
            
        try:
            # Check if file is syntax safe first
            if not self.is_syntax_safe(file_path):
                print(f"⚠️  Skipping {file_path} (syntax issues)")
                self.stats['skipped_files'] += 1
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            content = original_content
            total_fixes = 0
            
            # Fix COM818: Trailing comma issues
            content, com818_fixes = self.fix_com818_trailing_comma(content)
            total_fixes += com818_fixes
            self.stats['com818_fixed'] += com818_fixes
            
            # Fix D200: Multiline docstrings
            content, d200_fixes = self.fix_d200_multiline_docstring(content)
            total_fixes += d200_fixes
            self.stats['d200_fixed'] += d200_fixes
            
            # Fix E303: Too many blank lines
            content, e303_fixes = self.fix_e303_blank_lines(content)
            total_fixes += e303_fixes
            self.stats['e303_fixed'] += e303_fixes
            
            # Write changes if any fixes were made
            if total_fixes > 0 and content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ {file_path}: {total_fixes} fixes (COM818: {com818_fixes}, D200: {d200_fixes}, E303: {e303_fixes})")
            
            self.processed_files.add(file_path)
            self.stats['files_processed'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            self.stats['skipped_files'] += 1
            return False
    
    def find_python_files(self) -> List[Path]:
        """Python 파일들 찾기."""
        python_files = []
        
        for pattern in ['**/*.py']:
            python_files.extend(self.project_root.glob(pattern))
        
        # Filter out some directories and files
        excluded_patterns = {
            'venv', '.venv', '__pycache__', '.git', 'node_modules',
            '.pytest_cache', '.tox', 'build', 'dist', '.mypy_cache'
        }
        
        filtered_files = []
        for file_path in python_files:
            # Check if any part of the path contains excluded patterns
            if not any(pattern in str(file_path) for pattern in excluded_patterns):
                filtered_files.append(file_path)
        
        return sorted(filtered_files)
    
    def run(self) -> None:
        """메인 실행 함수."""
        print("🚀 ULTRA BATCH 4 FIXER: COM818 + D200 + E303")
        print("=" * 60)
        
        python_files = self.find_python_files()
        print(f"📁 Found {len(python_files)} Python files")
        
        # Process all files
        for file_path in python_files:
            self.process_file(file_path)
        
        self.print_summary()
    
    def print_summary(self) -> None:
        """처리 결과 요약 출력."""
        print("\n" + "="*60)
        print("🎉 ULTRA BATCH 4 PROCESSING COMPLETE!")
        print("="*60)
        print(f"📁 Files processed: {self.stats['files_processed']}")
        print(f"⚠️  Files skipped: {self.stats['skipped_files']}")
        print(f"🔧 COM818 fixes (trailing comma): {self.stats['com818_fixed']}")
        print(f"📝 D200 fixes (docstring): {self.stats['d200_fixed']}")
        print(f"📏 E303 fixes (blank lines): {self.stats['e303_fixed']}")
        print(f"✨ Total fixes: {sum([self.stats['com818_fixed'], self.stats['d200_fixed'], self.stats['e303_fixed']])}")
        print("="*60)


def main():
    """메인 함수."""
    project_path = "/Users/archmagece/myopen/scripton/yesman-claude"
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    
    fixer = UltraBatch4Fixer(project_path)
    fixer.run()


if __name__ == "__main__":
    main()