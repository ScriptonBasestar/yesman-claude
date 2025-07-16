---
phase: 3
order: 2
source_plan: /tasks/plan/05-code-structure-refactoring.md
priority: high
tags: [refactoring, dependency-injection, architecture]
---

# 📌 작업: 의존성 주입 컨테이너 구현

## Phase: 3 - Standardize Architecture

## 순서: 2

### 작업 내용

프로젝트 전반에서 사용할 의존성 주입(DI) 컨테이너를 구현하고 싱글톤 관리를 표준화합니다.

### 구현 사항

**libs/core/container.py**

```python
from typing import TypeVar, Type, Callable, Dict, Any

T = TypeVar('T')

class DIContainer:
    """Dependency Injection Container"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register a singleton instance"""
        pass
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function"""
        pass
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service"""
        pass
    
    def clear(self) -> None:
        """Clear all registrations"""
        pass

# Global container instance
container = DIContainer()
```

### 적용 대상

#### API Routers

- api/routers/sessions.py
- api/routers/controllers.py
- api/routers/config.py
- api/routers/logs.py

#### Core Services

- YesmanConfig
- TmuxManager
- SessionManager
- LoggingManager

### 실행 단계

```yaml
- name: DI Container 구현
  file: libs/core/container.py
  features:
    - 타입 안전 서비스 등록/해결
    - 싱글톤 패턴 지원
    - 팩토리 패턴 지원
    - 생명주기 관리

- name: 서비스 등록 모듈 생성
  file: libs/core/services.py
  action: 모든 핵심 서비스 등록

- name: API Router 리팩토링
  action: 글로벌 인스턴스 대신 DI 사용

- name: 명령어 리팩토링
  action: DI를 통한 서비스 주입
```

### 사용 예시

```python
# 서비스 등록
from libs.core.container import container
from libs.yesman_config import YesmanConfig

container.register_factory(YesmanConfig, lambda: YesmanConfig())
container.register_singleton(TmuxManager, TmuxManager(container.resolve(YesmanConfig)))

# 서비스 사용
@router.get("/sessions")
def get_sessions():
    tmux_manager = container.resolve(TmuxManager)
    return tmux_manager.get_all_sessions()
```

### 검증 조건

- [x] 타입 안전성 보장
- [x] 순환 의존성 방지
- [x] 싱글톤 인스턴스 관리
- [x] 테스트 시 mock 주입 가능

### 예상 이점

- 명확한 의존성 관리
- 테스트 용이성 향상
- 싱글톤 패턴 표준화
- 설정 변경 용이
