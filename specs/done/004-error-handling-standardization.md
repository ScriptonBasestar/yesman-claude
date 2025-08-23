# ADR-004: 에러 처리 표준화

## 상태

승인됨

## 날짜

2025-07-17

## 컨텍스트

기존 Yesman Claude 프로젝트에서 에러 처리가 각 모듈별로 분산되어 다음과 같은 문제점들이 발생했습니다:

1. **일관성 부족**: 각 명령어마다 다른 에러 처리 방식과 메시지 형식
1. **사용자 경험 저하**: 불친화적인 에러 메시지와 해결 방법 부재
1. **디버깅 어려움**: 에러 컨텍스트 정보 부족으로 문제 추적 곤란
1. **복구 지원 부재**: 에러 발생 시 사용자가 취할 수 있는 조치 안내 없음

### 기존 문제 사례

```python
# 분산된 에러 처리
def some_command():
    try:
        # 작업 수행
        pass
    except Exception as e:
        print(f"Error: {e}")  # 일관성 없는 메시지
        sys.exit(1)          # 획일적 종료 코드
```

## 결정

**중앙화된 에러 처리 시스템**을 구축하여 모든 명령어에서 일관된 에러 처리를 제공합니다.

### 핵심 설계 원칙

1. **계층화된 에러 분류**: 카테고리와 심각도 기반 에러 분류
1. **컨텍스트 보존**: 에러 발생 위치와 상황 정보 보관
1. **복구 힌트**: 사용자가 문제를 해결할 수 있는 구체적 조치 제공
1. **표준화된 처리**: BaseCommand를 통한 일관된 에러 처리 흐름

### 아키텍처 구조

```
libs/core/
├── error_handling.py     # 중앙 에러 시스템
├── base_command.py       # 표준화된 에러 처리 흐름
└── services.py          # 서비스 레벨 에러 처리
```

## 구현 세부사항

### 1. 에러 분류 시스템

```python
class ErrorCategory(Enum):
    """에러 카테고리 분류"""
    CONFIGURATION = "configuration"    # 설정 관련
    VALIDATION = "validation"          # 입력 검증
    SYSTEM = "system"                  # 시스템 자원
    NETWORK = "network"                # 네트워크 연결
    PERMISSION = "permission"          # 권한 문제
    TIMEOUT = "timeout"                # 시간 초과
    USER_INPUT = "user_input"          # 사용자 입력
    EXTERNAL_SERVICE = "external_service"  # 외부 서비스
    UNKNOWN = "unknown"                # 분류 불가

class ErrorSeverity(Enum):
    """에러 심각도 분류"""
    LOW = "low"           # 경고 수준
    MEDIUM = "medium"     # 기본 에러
    HIGH = "high"         # 심각한 에러
    CRITICAL = "critical" # 치명적 에러
```

### 2. 컨텍스트 보존

```python
@dataclass
class ErrorContext:
    """에러 컨텍스트 정보"""
    operation: str                      # 수행 중인 작업
    component: str                      # 에러 발생 컴포넌트
    session_name: str | None = None     # 관련 세션
    file_path: str | None = None        # 관련 파일
    line_number: int | None = None      # 줄 번호
    additional_info: dict | None = None # 추가 정보
```

### 3. BaseCommand 통합

```python
class BaseCommand(ABC):
    def run(self, **kwargs) -> object:
        """표준화된 실행 흐름과 에러 처리"""
        command_name = self.__class__.__name__.replace("Command", "").lower()
        try:
            self.log_command_start(command_name, **kwargs)
            self.validate_preconditions()
            result = self.execute(**kwargs)
            self.log_command_end(command_name, success=True)
            return result
        except YesmanError:
            # 이미 처리된 에러는 재전파
            raise
        except Exception as e:
            # 예상치 못한 에러는 CommandError로 래핑
            self.logger.exception("Unexpected error in command")
            raise CommandError(
                message=f"Command failed: {e}",
                cause=e,
                recovery_hint="Please check logs and try again"
            ) from e
```

## 구현 상태

- ✅ ErrorCategory 및 ErrorSeverity 정의 완료
- ✅ ErrorContext 데이터 클래스 구현 완료
- ✅ YesmanError 기본 예외 클래스 완료
- ✅ BaseCommand 에러 처리 통합 완료
- ✅ CommandError 특화 예외 구현 완료
- ✅ 에러 핸들러 데코레이터 구현 완료

## 관련 ADR

- [ADR-001: Command Pattern](./001-command-pattern.md)
- [ADR-002: 의존성 주입](./002-dependency-injection.md)
- [ADR-003: Configuration Management](./003-configuration-management.md)
