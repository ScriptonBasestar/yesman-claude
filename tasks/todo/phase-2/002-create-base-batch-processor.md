---
phase: 2
order: 2
source_plan: /tasks/plan/05-code-structure-refactoring.md
priority: high
tags: [refactoring, batch-processor, generics]
---

# 📌 작업: Generic 기반 Batch Processor 생성

## Phase: 2 - Extract Common Patterns

## 순서: 2

### 작업 내용

libs/core/base_batch_processor.py 파일을 생성하여 범용 배치 프로세서 기본 클래스를 구현합니다.

### 구현 사항

```python
class BaseBatchProcessor[T]:
    """Generic batch processor for any type of items"""
    def __init__(self, batch_size: int, flush_interval: float):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._batch: list[T] = []
        self._lock = threading.Lock()
    
    def add(self, item: T) -> None:
        """Add item to batch"""
        pass
    
    def flush(self) -> None:
        """Flush current batch"""
        pass
    
    def get_statistics(self) -> dict[str, Any]:
        """Get processor statistics"""
        pass
```

### 실행 단계

```yaml
- name: Base Batch Processor 파일 생성
  file: libs/core/base_batch_processor.py
  action: create

- name: Generic 타입 파라미터 구현
  features:
    - Python 3.12+ generic syntax 사용
    - Thread-safe batch 관리
    - 자동 flush 타이머
    - 통계 수집 기능

- name: 기존 batch processor 통합
  targets:
    - libs/logging/batch_processor.py → LogBatchProcessor
    - api/utils/batch_processor.py → MessageBatchProcessor
```

### 검증 조건

- [x] Generic 타입이 올바르게 동작함
- [x] Thread-safe 동작 보장
- [x] flush 메커니즘이 정상 작동함
- [x] 통계 수집이 정확함

### 리팩토링 대상

- libs/logging/batch_processor.py
- api/utils/batch_processor.py

### 예상 이점

- 코드 중복 제거
- 일관된 배치 처리 로직
- 타입 안전성 향상
- 테스트 용이성 증가
