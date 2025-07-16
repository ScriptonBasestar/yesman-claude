---
phase: 2
order: 1
source_plan: /tasks/plan/05-code-structure-refactoring.md
priority: high
tags: [refactoring, mixins, patterns]
---

# 📌 작업: 공통 Mixin 클래스 생성

## Phase: 2 - Extract Common Patterns

## 순서: 1

### 작업 내용

libs/core/mixins.py 파일을 생성하여 공통 패턴을 위한 mixin 클래스들을 구현합니다.

### 구현할 Mixin 클래스

1. **StatisticsProviderMixin**

   - 통계 정보를 제공하는 클래스를 위한 mixin
   - `get_statistics()` 메서드 정의

1. **StatusManagerMixin**

   - 상태 및 활동 관리를 위한 mixin
   - `update_status()`, `update_activity()` 메서드 정의

1. **LayoutManagerMixin**

   - 레이아웃 관리를 위한 mixin
   - `create_layout()`, `update_layout()` 메서드 정의

### 실행 단계

```yaml
- name: Mixin 파일 생성
  file: libs/core/mixins.py
  action: create
  
- name: StatisticsProviderMixin 구현
  methods:
    - get_statistics() -> dict[str, Any]
  
- name: StatusManagerMixin 구현
  methods:
    - update_status(status: str) -> None
    - update_activity(activity: str) -> None
    
- name: LayoutManagerMixin 구현
  methods:
    - create_layout() -> Any
    - update_layout(layout: Any) -> None
```

### 검증 조건

- [x] mixins.py 파일이 생성됨
- [x] 모든 mixin 클래스가 정의됨
- [x] 타입 힌트가 올바르게 적용됨
- [x] import 오류가 없음

### 영향받는 파일들

다음 파일들이 이 mixin을 사용하도록 리팩토링 필요:

- libs/logging/async_logger.py
- libs/logging/batch_processor.py
- api/utils/batch_processor.py
- libs/ai/response_analyzer.py
- commands/status.py
- commands/browse.py
- libs/dashboard/tui_dashboard.py
