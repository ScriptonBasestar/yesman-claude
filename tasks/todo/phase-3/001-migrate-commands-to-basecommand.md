---
phase: 3
order: 1
source_plan: /tasks/plan/05-code-structure-refactoring.md
priority: high
tags: [refactoring, command-pattern, architecture]
---

# 📌 작업: 모든 명령어를 BaseCommand 패턴으로 마이그레이션

## Phase: 3 - Standardize Architecture

## 순서: 1

### 작업 내용

아직 BaseCommand를 사용하지 않는 모든 명령어를 BaseCommand 패턴으로 마이그레이션합니다.

### 마이그레이션 대상 명령어

현재 BaseCommand를 사용하지 않는 명령어들:

- commands/ai.py
- commands/automate.py
- commands/browse.py
- commands/cleanup.py
- commands/dashboard.py
- commands/enter.py
- commands/logs.py
- commands/multi_agent.py
- commands/show.py
- commands/status.py
- commands/task_runner.py
- commands/teardown.py
- commands/validate.py

### 표준 구조

```python
from libs.core.base_command import BaseCommand, ConfigCommandMixin

class XxxCommand(BaseCommand, ConfigCommandMixin):
    """Command description"""
    
    def validate_preconditions(self) -> None:
        """Validate command preconditions"""
        super().validate_preconditions()
        # 추가 검증 로직
    
    def execute(self, **kwargs) -> dict:
        """Execute the command"""
        # 실제 명령어 로직
        return result

@click.command()
@click.option(...)
def xxx(...):
    """Command description"""
    command = XxxCommand()
    command.run(**kwargs)
```

### 실행 단계

```yaml
- name: 각 명령어 분석
  action: 현재 구조와 로직 파악

- name: BaseCommand 상속 구조로 변환
  steps:
    - 클래스 기반 구조로 변환
    - execute() 메서드로 로직 이동
    - validate_preconditions() 구현
    - 적절한 mixin 적용

- name: 에러 처리 표준화
  action: CommandError 예외 사용

- name: 로깅 표준화
  action: BaseCommand의 로깅 메서드 사용
```

### 검증 조건

- [ ] 모든 명령어가 BaseCommand 상속
- [ ] 일관된 에러 처리
- [ ] 표준화된 로깅
- [ ] 기존 기능 유지

### 주의사항

- 기능 변경 없이 구조만 변경
- 각 명령어의 고유 옵션 유지
- 테스트 케이스 업데이트 필요

### 예상 이점

- 일관된 명령어 구조
- 공통 기능 재사용
- 향상된 테스트 가능성
- 쉬운 유지보수
