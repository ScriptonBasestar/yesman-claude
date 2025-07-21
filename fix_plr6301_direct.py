#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""
PLR6301 직접 수정: ruff 출력을 기반으로 정확한 위치의 메소드를 @staticmethod로 변경
"""

import subprocess
import re
import os
from typing import List, Tuple


def get_plr6301_errors() -> List[Tuple[str, int, str]]:
    """ruff로 PLR6301 에러 목록을 가져옵니다."""
    try:
        result = subprocess.run(
            ['ruff', 'check', '--select', 'PLR6301', '--output-format', 'concise'],
            capture_output=True,
            text=True
        )
        
        errors = []
        for line in result.stdout.strip().split('\n'):
            if line and 'PLR6301' in line:
                # 파일명:라인번호:컬럼번호: 에러코드 메시지
                match = re.match(r'^([^:]+):(\d+):\d+:\s+PLR6301\s+Method\s+`([^`]+)`', line)
                if match:
                    file_path = match.group(1)
                    line_num = int(match.group(2))
                    method_name = match.group(3)
                    errors.append((file_path, line_num, method_name))
                    
        return errors
    except Exception as e:
        print(f"Error getting PLR6301 errors: {e}")
        return []


def fix_method_in_file(file_path: str, line_num: int, method_name: str) -> bool:
    """파일의 특정 라인에 있는 메소드를 @staticmethod로 변경합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 라인 번호는 1부터 시작하므로 인덱스는 -1
        target_line_idx = line_num - 1
        
        if target_line_idx >= len(lines):
            print(f"✗ Line {line_num} not found in {file_path}")
            return False
        
        target_line = lines[target_line_idx]
        
        # 메소드 정의 라인 확인
        if f'def {method_name}(' not in target_line:
            print(f"✗ Method {method_name} not found at line {line_num} in {file_path}")
            return False
        
        # 인덴트 계산
        indent = len(target_line) - len(target_line.lstrip())
        indent_str = ' ' * indent
        
        # 이미 @staticmethod가 있는지 확인
        for i in range(max(0, target_line_idx - 5), target_line_idx):
            if lines[i].strip() == '@staticmethod':
                print(f"✓ {method_name} already has @staticmethod in {file_path}")
                return False
        
        # @staticmethod 데코레이터 추가
        lines.insert(target_line_idx, f"{indent_str}@staticmethod\n")
        
        # self 파라미터 제거 (다음 라인이 메소드 정의 라인)
        method_line_idx = target_line_idx + 1
        method_line = lines[method_line_idx]
        
        # self 파라미터 패턴들 처리
        if '(self):' in method_line:
            lines[method_line_idx] = method_line.replace('(self):', '():')
        elif '(self,' in method_line:
            lines[method_line_idx] = method_line.replace('(self,', '(')
        elif '( self,' in method_line:
            lines[method_line_idx] = method_line.replace('( self,', '(')
        elif '(self ,' in method_line:
            lines[method_line_idx] = method_line.replace('(self ,', '(')
        elif '( self ):' in method_line:
            lines[method_line_idx] = method_line.replace('( self ):', '():')
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✓ Fixed {method_name} in {file_path}:{line_num}")
        return True
        
    except Exception as e:
        print(f"✗ Error fixing {method_name} in {file_path}: {e}")
        return False


def main():
    """PLR6301 에러들을 자동으로 수정합니다."""
    print("🚀 PLR6301 자동 수정 시작...")
    
    # PLR6301 에러 목록 가져오기
    errors = get_plr6301_errors()
    print(f"📋 발견된 PLR6301 에러: {len(errors)}개")
    
    if not errors:
        print("✅ PLR6301 에러가 없습니다!")
        return
    
    fixed_count = 0
    
    # 각 에러 수정
    for file_path, line_num, method_name in errors:
        if fix_method_in_file(file_path, line_num, method_name):
            fixed_count += 1
    
    print(f"\n✅ PLR6301 수정 완료: {fixed_count}/{len(errors)}개 수정됨")
    
    # 남은 에러 확인
    remaining_errors = get_plr6301_errors()
    if remaining_errors:
        print(f"⚠️  남은 PLR6301 에러: {len(remaining_errors)}개")
    else:
        print("🎉 모든 PLR6301 에러가 수정되었습니다!")


if __name__ == "__main__":
    main()