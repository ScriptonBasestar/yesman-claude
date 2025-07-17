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

- [x] 모든 명령어가 BaseCommand 상속 ✅ (100% compliance verified)
- [x] 일관된 에러 처리 ✅ (CommandError throughout)
- [x] 표준화된 로깅 ✅ (BaseCommand logging methods)
- [x] 기존 기능 유지 ✅ (All CLI interfaces preserved)

### 주의사항

- 기능 변경 없이 구조만 변경
- 각 명령어의 고유 옵션 유지
- 테스트 케이스 업데이트 필요

### 예상 이점

- 일관된 명령어 구조 ✅ (All commands follow BaseCommand pattern)
- 공통 기능 재사용 ✅ (Mixins used throughout)
- 향상된 테스트 가능성 ✅ (DI container supports mocking)
- 쉬운 유지보수 ✅ (Centralized error handling and logging)

## 완료 상태 (2025-07-17)

✅ **작업 완료됨** - 모든 17개 명령어파일이 BaseCommand 패턴을 사용하여 리팩토링 완료

### 최종 통계

- **전체 분석된 명령어 파일**: 17개
- **BaseCommand 패턴 사용**: 17개 (100%)
- **BaseCommand 패턴 미사용**: 0개 (0%)
- **전체 준수율**: 100% ✅

### 주요 성과

1. **완전한 아키텍처 통합**: 모든 명령어가 일관된 패턴 사용
1. **중앙화된 에러 처리**: CommandError 및 YesmanError 시스템 적용
1. **표준화된 로깅**: BaseCommand의 로깅 메서드 전사용
1. **믹스인 활용**: SessionCommandMixin, ConfigCommandMixin 등 재사용 가능한 컴포넌트
1. **의존성 주입**: DI 컨테이너를 통한 테스트 가능한 구조
