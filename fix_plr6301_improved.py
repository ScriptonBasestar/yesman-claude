#!/usr/bin/env python3

# Copyright notice.

import os
import re

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""
PLR6301 자동 수정 스크립트: self를 사용하지 않는 메소드를 @staticmethod로 변경 (개선된 버전)
"""


class StaticMethodFixerImproved:
    def __init__(self) -> None:
        self.fixed_count = 0

    @staticmethod
    def find_project_python_files() -> list[str]:
        """프로젝트의 Python 파일들만 찾습니다.

        Returns:
        object: Description of return value.
        """
        python_files = []
        exclude_dirs = {".git", "__pycache__", ".pytest_cache", "venv", ".venv", "env", "node_modules", ".mypy_cache"}

        for root, dirs, files in os.walk("."):
            # 제외할 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]

            # .venv나 venv가 포함된 경로 제외
            if any(excluded in root for excluded in [".venv", "venv", "site-packages"]):
                continue

            for file in files:
                if file.endswith(".py") and not file.startswith("."):
                    file_path = os.path.join(root, file)
                    # 상대 경로로 변환
                    rel_path = os.path.relpath(file_path, ".")
                    if not any(excluded in rel_path for excluded in ["venv", ".venv", "site-packages"]):
                        python_files.append(file_path)

        return python_files

    @staticmethod
    def analyze_method_self_usage(method_lines: list[str], method_name: str) -> bool:
        """메소드에서 self 사용 여부를 분석합니다.

        Returns:
        bool: Description of return value.
        """
        # 메소드 정의 라인을 제외하고 본문만 분석
        body_lines = []
        found_def = False

        for line in method_lines:
            if f"def {method_name}(" in line:
                found_def = True
                continue
            if found_def:
                body_lines.append(line)

        if not body_lines:
            return False

        method_body = "\n".join(body_lines)

        # self 사용 패턴들
        self_patterns = [
            r"\bself\.",           # self.attribute or self.method()
            r"\bself\[",           # self[key]
            r"=\s*self\b",         # = self
            r"\bself\s*=",         # self =
            r"return\s+self\b",    # return self
            r"\(self\)",           # function(self)
            r",\s*self\b",         # , self
            r"\bself\s*,",         # self,
        ]

        for pattern in self_patterns:
            if re.search(pattern, method_body):
                return True

        return False

    def fix_file(self, file_path: str) -> bool:
        """파일의 PLR6301 에러를 수정합니다.

        Returns:
        bool: Description of return value.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            modified = False
            i = 0

            while i < len(lines):
                line = lines[i]

                # 메소드 정의 찾기 (클래스 안의 메소드만)
                method_match = re.match(r"^(\s+)def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*self(?:\s*,.*?)?\)\s*:", line)
                if method_match:
                    indent = method_match.group(1)
                    method_name = method_match.group(2)

                    # 특수 메소드나 이미 데코레이트된 메소드 제외
                    if (method_name.startswith("__") or method_name in {"setUp", "tearDown"} or
                        any(decorator_line.strip().startswith("@") for decorator_line in lines[max(0, i - 3):i])):
                        i += 1
                        continue

                    # 메소드 본문 추출
                    method_lines = [line]
                    j = i + 1
                    base_indent_len = len(indent)

                    # 메소드 본문 끝까지 찾기
                    while j < len(lines):
                        current_line = lines[j]

                        # 빈 줄은 계속 포함
                        if current_line.strip() == "":
                            method_lines.append(current_line)
                            j += 1
                            continue

                        # 현재 라인의 인덴트 확인
                        current_indent = len(current_line) - len(current_line.lstrip())

                        # 메소드와 같은 레벨이거나 더 적은 인덴트면 메소드 끝
                        if current_indent <= base_indent_len and current_line.strip():
                            break

                        method_lines.append(current_line)
                        j += 1

                    # self 사용 여부 확인
                    if not self.analyze_method_self_usage(method_lines, method_name):
                        # @staticmethod 데코레이터 추가
                        lines.insert(i, f"{indent}@staticmethod")

                        # self 파라미터 제거
                        def_line = lines[i + 1]
                        # self만 있는 경우
                        if f"def {method_name}(self):" in def_line:
                            lines[i + 1] = def_line.replace(f"def {method_name}(self):", f"def {method_name}():")
                        # self와 다른 파라미터가 있는 경우
                        elif f"def {method_name}(self," in def_line:
                            lines[i + 1] = def_line.replace(f"def {method_name}(self,", f"def {method_name}(")

                        modified = True
                        self.fixed_count += 1
                        print(f"✓ Fixed {method_name} in {file_path}")

                        # 인덱스 조정 (데코레이터 추가로 인한)
                        i = j + 1
                    else:
                        i = j
                else:
                    i += 1

            # 수정된 내용 저장
            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
                return True

        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")

        return False

    def run(self) -> None:
        """PLR6301 에러 수정을 실행합니다."""
        print("🚀 PLR6301 자동 수정 시작...")

        python_files = self.find_project_python_files()
        print(f"📁 프로젝트 Python 파일: {len(python_files)}개")

        for file_path in python_files:
            if self.fix_file(file_path):
                pass  # 이미 출력됨

        print(f"\n✅ PLR6301 수정 완료: {self.fixed_count}개 메소드가 @staticmethod로 변경됨")


if __name__ == "__main__":
    fixer = StaticMethodFixerImproved()
    fixer.run()
