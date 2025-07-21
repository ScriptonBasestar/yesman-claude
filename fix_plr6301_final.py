#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""
PLR6301 자동 수정 스크립트: self를 사용하지 않는 메소드를 @staticmethod로 변경 (최종 버전)
"""

import os
import re
from typing import List, Tuple


class PLR6301Fixer:
    def __init__(self):
        self.fixed_count = 0
        
    @staticmethod
    def get_project_files() -> List[str]:
        """프로젝트 Python 파일들만 찾습니다."""
        python_files = []
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'env', 'node_modules', '.mypy_cache'}
        
        for root, dirs, files in os.walk('.'):
            # 제외 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # virtual environment 경로 제외
            if any(excluded in root for excluded in ['.venv', '/venv/', 'site-packages']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    # 가상환경 파일 제외
                    if 'site-packages' not in file_path and '.venv' not in file_path:
                        python_files.append(file_path)
                        
        return python_files
    
    @staticmethod
    def uses_self(method_content: str) -> bool:
        """메소드 본문에서 self를 사용하는지 확인합니다."""
        # self 사용 패턴들
        patterns = [
            r'\bself\.',        # self.attribute, self.method()
            r'\bself\[',        # self[key]
            r'=\s*self\b',      # var = self
            r'\bself\s*=',      # self = something
            r'return\s+self\b', # return self
            r'\(\s*self\s*\)',  # function(self)
            r',\s*self\b',      # function(arg, self)
            r'\bself\s*,',      # function(self, arg)
        ]
        
        for pattern in patterns:
            if re.search(pattern, method_content):
                return True
        return False
    
    @staticmethod
    def extract_method_content(lines: List[str], start_idx: int) -> Tuple[str, int]:
        """메소드의 전체 내용을 추출합니다."""
        method_lines = [lines[start_idx]]
        current_line = lines[start_idx]
        
        # 메소드 정의 라인의 인덴트 계산
        base_indent = len(current_line) - len(current_line.lstrip())
        
        i = start_idx + 1
        while i < len(lines):
            line = lines[i]
            
            # 빈 줄은 계속 포함
            if line.strip() == '':
                method_lines.append(line)
                i += 1
                continue
            
            # 현재 라인의 인덴트
            current_indent = len(line) - len(line.lstrip())
            
            # 메소드 본문보다 인덴트가 적거나 같으면 메소드 끝
            if current_indent <= base_indent:
                break
                
            method_lines.append(line)
            i += 1
        
        return '\n'.join(method_lines), i - 1
    
    def fix_file(self, file_path: str) -> bool:
        """파일의 PLR6301 에러를 수정합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            modified = False
            
            # 뒤에서부터 처리해서 인덱스 문제 방지
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i]
                
                # 메소드 정의 패턴 찾기
                method_match = re.match(r'^(\s+)def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*self(?:\s*,.*?)?\)\s*:', line)
                if not method_match:
                    continue
                
                indent = method_match.group(1)
                method_name = method_match.group(2)
                
                # 특수 메소드 제외
                if method_name.startswith('__') or method_name in ['setUp', 'tearDown']:
                    continue
                
                # 이미 데코레이터가 있는지 확인
                has_decorator = False
                for j in range(max(0, i-5), i):
                    if lines[j].strip().startswith('@'):
                        decorator_indent = len(lines[j]) - len(lines[j].lstrip())
                        if decorator_indent == len(indent):
                            has_decorator = True
                            break
                
                if has_decorator:
                    continue
                
                # 메소드 내용 추출
                method_content, end_idx = self.extract_method_content(lines, i)
                
                # self 사용 여부 확인 (메소드 정의 라인 제외)
                body_content = '\n'.join(method_content.split('\n')[1:])
                
                if not self.uses_self(body_content):
                    # @staticmethod 데코레이터 추가
                    lines.insert(i, f"{indent}@staticmethod")
                    
                    # self 파라미터 제거
                    method_line = lines[i + 1]
                    
                    # 다양한 self 패턴 처리
                    if f'(self):' in method_line:
                        lines[i + 1] = method_line.replace('(self):', '():')
                    elif f'(self,' in method_line:
                        lines[i + 1] = method_line.replace('(self,', '(')
                    elif f'( self,' in method_line:
                        lines[i + 1] = method_line.replace('( self,', '(')
                    elif f'(self ,' in method_line:
                        lines[i + 1] = method_line.replace('(self ,', '(')
                    elif f'( self ):' in method_line:
                        lines[i + 1] = method_line.replace('( self ):', '():')
                    
                    modified = True
                    self.fixed_count += 1
                    print(f"✓ Fixed {method_name} in {file_path}")
            
            # 수정 사항 저장
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                return True
                
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            
        return False
    
    def run(self):
        """PLR6301 에러 수정 실행"""
        print("🚀 PLR6301 @staticmethod 자동 수정 시작...")
        
        files = self.get_project_files()
        print(f"📁 처리할 파일: {len(files)}개")
        
        for file_path in files:
            self.fix_file(file_path)
        
        print(f"\n✅ 완료: {self.fixed_count}개 메소드를 @staticmethod로 변경했습니다.")


if __name__ == "__main__":
    fixer = PLR6301Fixer()
    fixer.run()
