---
phase: 2
order: 5
source_plan: /tasks/plan/05-code-structure-refactoring.md
priority: medium
tags: [refactoring, integration]
---

# 📌 작업: 기존 모듈 리팩토링 - 공통 패턴 적용

## Phase: 2 - Extract Common Patterns

## 순서: 5

### 작업 내용

Phase 2에서 생성한 mixin, base class, utility를 기존 모듈에 적용하여 코드 중복을 제거합니다.

### 리팩토링 대상 및 적용 사항

#### 1. Batch Processor 통합

**libs/logging/batch_processor.py**

- BaseBatchProcessor[LogEntry] 상속
- 중복 코드 제거
- 표준화된 통계 수집

**api/utils/batch_processor.py**

- BaseBatchProcessor[Message] 상속
- 중복 코드 제거
- 표준화된 통계 수집

#### 2. Statistics Provider 적용

**적용 대상:**

- libs/logging/async_logger.py
- libs/ai/response_analyzer.py
- libs/logging/batch_processor.py
- api/utils/batch_processor.py

```python
from libs.core.mixins import StatisticsProviderMixin

class AsyncLogger(StatisticsProviderMixin):
    # 기존 get_statistics() 메서드 표준화
```

#### 3. Status/Layout Manager 적용

**적용 대상:**

- commands/status.py
- commands/browse.py
- libs/dashboard/tui_dashboard.py

```python
from libs.core.mixins import StatusManagerMixin, LayoutManagerMixin

class StatusCommand(BaseCommand, StatusManagerMixin, LayoutManagerMixin):
    # 기존 메서드들을 mixin 인터페이스에 맞게 조정
```

#### 4. Validation 통합

**모든 세션/프로젝트 검증 로직을 utils로 이동:**

- libs/core/session_validator.py → validation.py 사용
- 각 명령어의 인라인 검증 → validation.py 사용
- API 엔드포인트 검증 → validation.py 사용

### 실행 단계

```yaml
- name: Batch Processor 리팩토링
  files:
    - libs/logging/batch_processor.py
    - api/utils/batch_processor.py
  action: refactor to use BaseBatchProcessor

- name: Mixin 적용
  targets:
    - StatisticsProviderMixin 적용
    - StatusManagerMixin 적용
    - LayoutManagerMixin 적용

- name: Validation 중앙화
  action: 모든 검증 로직을 validation.py로 이동

- name: Session Helper 적용
  action: 중복된 세션 처리 로직을 session_helpers.py로 이동
```

### 검증 조건

- [ ] 모든 테스트가 통과함
- [ ] 기능 변경 없이 코드 구조만 개선됨
- [ ] 코드 중복이 실제로 감소함
- [ ] import 순환 참조가 없음

### 예상 결과

- 코드 중복 30% 이상 감소
- 일관된 인터페이스
- 향상된 테스트 가능성
- 명확한 책임 분리
