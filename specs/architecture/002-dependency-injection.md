# ADR-002: 의존성 주입 컨테이너 도입

## 상태

승인됨

## 날짜

2025-07-17

## 컨텍스트

Yesman Claude 프로젝트에서 다음과 같은 의존성 관리 문제들이 발생했습니다:

1. **전역 싱글톤**: 여러 모듈에서 전역 인스턴스에 직접 의존
1. **테스트 어려움**: 의존성을 모킹하기 어려워 단위 테스트 작성이 복잡
1. **순환 의존성**: 모듈 간 상호 참조로 인한 import 문제
1. **설정 관리**: 설정 인스턴스가 여러 곳에서 중복 생성

### 기존 문제 사례

```python
# API 라우터에서 전역 인스턴스 사용
tm = TmuxManager()  # 매번 새로 생성
config = YesmanConfig()  # 매번 새로 생성

# 테스트 시 모킹 어려움
def test_session_creation():
    # TmuxManager를 어떻게 모킹할 것인가?
    pass
```

## 결정

**타입 안전한 DI 컨테이너**를 구현하여 의존성 관리를 중앙화합니다.

### 핵심 설계 원칙

1. **타입 안전성**: TypeVar를 사용한 타입 안전한 서비스 해결
1. **생명주기 관리**: Singleton, Factory, Transient 지원
1. **순환 의존성 감지**: 자동 감지 및 오류 보고
1. **테스트 지원**: 쉬운 모킹과 의존성 교체

### DI 컨테이너 구현

```python
class DIContainer:
    def register_singleton(self, service_type: type[T], instance: T) -> None:
        """싱글톤 인스턴스 등록"""
        
    def register_factory(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """팩토리 함수 등록 (lazy singleton)"""
        
    def register_transient(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """매번 새 인스턴스 생성"""
        
    def resolve(self, service_type: type[T]) -> T:
        """타입 안전한 서비스 해결"""
```

### 서비스 등록 전략

1. **핵심 서비스**: YesmanConfig, TmuxManager는 팩토리로 등록
1. **자동 초기화**: 모듈 import 시 자동으로 서비스 등록
1. **테스트 모드**: 테스트용 모킹 서비스 등록 지원

## 대안 검토

### 1. 전역 싱글톤 유지

- **장점**: 단순함, 기존 코드 변경 불필요
- **단점**: 테스트 어려움, 의존성 관리 복잡

### 2. 외부 DI 라이브러리 (dependency-injector, pinject)

- **장점**: 검증된 솔루션, 풍부한 기능
- **단점**: 외부 의존성 추가, 프로젝트 복잡성 증가

### 3. 함수 인자 전달

- **장점**: 명시적 의존성, 테스트 용이
- **단점**: 보일러플레이트 코드 증가, 깊은 의존성 체인

## 구현 세부사항

### 1. 컨테이너 구조

```python
# libs/core/container.py
class DIContainer:
    def __init__(self):
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, Callable] = {}
        self._services: dict[type, Callable] = {}
        self._resolving: set = set()  # 순환 의존성 감지
```

### 2. 서비스 등록

```python
# libs/core/services.py
def register_core_services() -> None:
    container.register_factory(YesmanConfig, lambda: YesmanConfig())
    container.register_factory(
        TmuxManager, 
        lambda: TmuxManager(container.resolve(YesmanConfig))
    )
```

### 3. BaseCommand 통합

```python
class BaseCommand(ABC):
    def __init__(self, config=None, tmux_manager=None, claude_manager=None):
        # DI 컨테이너에서 해결하거나 주입된 인스턴스 사용
        self.config = config or self._resolve_config()
        self.tmux_manager = tmux_manager or self._resolve_tmux_manager()
```

## 결과

### 긍정적 영향

1. **테스트 용이성**: 의존성을 쉽게 모킹 가능
1. **성능 향상**: 싱글톤으로 인스턴스 재사용
1. **일관성**: 모든 서비스가 동일한 방식으로 관리
1. **순환 의존성 방지**: 자동 감지 및 오류 보고

### 측정 가능한 개선

- **인스턴스 생성 최적화**: YesmanConfig가 매번 생성되던 것을 싱글톤으로 변경
- **테스트 커버리지**: 의존성 주입으로 단위 테스트 작성 용이
- **메모리 사용량**: 중복 인스턴스 생성 방지

### 부정적 영향

1. **초기 복잡성**: DI 컨테이너 구현 및 이해 필요
1. **디버깅**: 의존성 해결 과정이 숨겨져 디버깅 어려움
1. **마이그레이션**: 기존 코드의 점진적 마이그레이션 필요

## 구현 상태

- ✅ DIContainer 클래스 구현 완료
- ✅ 서비스 등록 모듈 구현 완료
- ✅ BaseCommand DI 통합 완료
- ✅ API 라우터 DI 적용 완료
- ✅ 단위 테스트 작성 완료

## 사용 예시

### 기본 사용법

```python
from libs.core.services import get_config, get_tmux_manager

# 서비스 사용
config = get_config()
tmux_manager = get_tmux_manager()
```

### 테스트에서 모킹

```python
def test_command_with_mock():
    mock_config = MagicMock()
    mock_tmux = MagicMock()
    
    register_test_services(config=mock_config, tmux_manager=mock_tmux)
    
    command = MyCommand()
    result = command.execute()
    
    assert result.success
```

## 관련 ADR

- [ADR-001: Command Pattern](./001-command-pattern.md)
- [ADR-003: Configuration Management](./003-configuration-management.md)
