#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""
CPY001 자동 수정: 파일 상단에 저작권 표시 추가
"""

import subprocess
import os
from typing import List, Tuple


def get_cpy001_errors() -> List[Tuple[str, int]]:
    """ruff로 CPY001 에러 목록을 가져옵니다."""
    try:
        result = subprocess.run(
            ['ruff', 'check', '--select', 'CPY001', '--output-format', 'concise'],
            capture_output=True,
            text=True
        )
        
        errors = []
        for line in result.stdout.strip().split('\n'):
            if line and 'CPY001' in line:
                # 파일명:라인번호:컬럼번호: 에러코드 메시지
                parts = line.split(':')
                if len(parts) >= 2:
                    file_path = parts[0]
                    line_num = int(parts[1])
                    errors.append((file_path, line_num))
                    
        return errors
    except Exception as e:
        print(f"Error getting CPY001 errors: {e}")
        return []


def get_python_files() -> List[str]:
    """프로젝트의 Python 파일들을 찾습니다."""
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


def has_copyright_notice(file_path: str) -> bool:
    """파일에 이미 저작권 표시가 있는지 확인합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 파일 상단 10줄 확인
            first_lines = [f.readline() for _ in range(10)]
            content = ''.join(first_lines).lower()
            
        # 저작권 관련 키워드 확인
        copyright_keywords = ['copyright', 'license', 'licensed under', '© ', '(c)']
        return any(keyword in content for keyword in copyright_keywords)
        
    except Exception:
        return False


def add_copyright_header(file_path: str) -> bool:
    """파일에 저작권 헤더를 추가합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 이미 저작권 표시가 있으면 건너뛰기
        if has_copyright_notice(file_path):
            return False
        
        # 저작권 헤더 생성
        copyright_header = '''"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

'''
        
        # 기존 내용이 shebang으로 시작하는지 확인
        lines = content.split('\n')
        if lines and lines[0].startswith('#!'):
            # shebang이 있는 경우, shebang 다음에 추가
            new_content = lines[0] + '\n' + copyright_header + '\n'.join(lines[1:])
        else:
            # shebang이 없는 경우, 파일 시작에 추가
            new_content = copyright_header + content
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Added copyright header to {file_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error adding copyright to {file_path}: {e}")
        return False


def main():
    """CPY001 에러들을 자동으로 수정합니다."""
    print("🚀 CPY001 저작권 표시 자동 추가 시작...")
    
    # 모든 Python 파일 가져오기
    python_files = get_python_files()
    print(f"📁 발견된 Python 파일: {len(python_files)}개")
    
    fixed_count = 0
    skipped_count = 0
    
    # 각 파일에 저작권 헤더 추가
    for file_path in python_files:
        if add_copyright_header(file_path):
            fixed_count += 1
        else:
            skipped_count += 1
    
    print(f"\n✅ CPY001 수정 완료:")
    print(f"   - 추가됨: {fixed_count}개")
    print(f"   - 건너뜀: {skipped_count}개 (이미 저작권 표시 있음)")
    print(f"   - 전체: {len(python_files)}개")
    
    # 남은 에러 확인
    remaining_errors = get_cpy001_errors()
    if remaining_errors:
        print(f"⚠️  남은 CPY001 에러: {len(remaining_errors)}개")
    else:
        print("🎉 모든 CPY001 에러가 수정되었습니다!")


if __name__ == "__main__":
    main()