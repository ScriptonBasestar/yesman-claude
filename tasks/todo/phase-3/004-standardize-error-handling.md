---
phase: 3
order: 4
source_plan: /tasks/plan/05-code-structure-refactoring.md
priority: medium
tags: [refactoring, error-handling, architecture]
---

# 📌 작업: 에러 처리 표준화

## Phase: 3 - Standardize Architecture

## 순서: 4

### 작업 내용

프로젝트 전반의 에러 처리를 표준화하고 일관된 에러 응답 형식을 구현합니다.

### 구현 사항

#### 1. 에러 계층 구조 확장

**libs/core/error_handling.py (확장)**

```python
from enum import Enum
from typing import Optional, Dict, Any

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class YesmanError(Exception):
    """Base exception with enhanced features"""
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_hint: Optional[str] = None
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.cause = cause
        self.context = context or {}
        self.recovery_hint = recovery_hint
        
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        pass

# Specific error types
class ConfigurationError(YesmanError):
    """Configuration related errors"""
    
class SessionError(YesmanError):
    """Session management errors"""
    
class ValidationError(YesmanError):
    """Validation errors"""
```

#### 2. 글로벌 에러 핸들러

**api/middleware/error_handler.py**

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse

async def global_error_handler(request: Request, exc: Exception):
    """Global error handler for API"""
    if isinstance(exc, YesmanError):
        return JSONResponse(
            status_code=error_to_status_code(exc),
            content={
                "error": exc.to_dict(),
                "request_id": request.state.request_id
            }
        )
    # Handle unexpected errors
```

#### 3. 명령어 에러 처리 표준화

**libs/core/base_command.py (확장)**

```python
def run(self, **kwargs):
    """Run command with standardized error handling"""
    try:
        self.validate_preconditions()
        result = self.execute(**kwargs)
        self.handle_success(result)
    except YesmanError as e:
        self.handle_yesman_error(e)
    except Exception as e:
        self.handle_unexpected_error(e)
```

### 실행 단계

```yaml
- name: 에러 클래스 계층 구조 확장
  file: libs/core/error_handling.py
  features:
    - 심각도 레벨 추가
    - 복구 힌트 추가
    - 컨텍스트 정보 추가
    - 직렬화 메서드

- name: API 에러 미들웨어 구현
  file: api/middleware/error_handler.py
  action: 글로벌 에러 핸들러 구현

- name: 기존 에러 처리 마이그레이션
  targets:
    - 모든 print() 기반 에러를 로깅으로
    - 모든 일반 Exception을 YesmanError로
    - API 응답 표준화

- name: 에러 복구 가이드 작성
  file: docs/error-recovery.md
  content: 각 에러 타입별 복구 방법
```

### 검증 조건

- [ ] 모든 에러가 적절한 카테고리로 분류됨
- [ ] API 에러 응답이 일관된 형식
- [ ] 로그에 충분한 디버그 정보 포함
- [ ] 사용자에게 명확한 에러 메시지 제공

### 에러 응답 형식

```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session 'my-session' not found",
    "category": "validation",
    "severity": "medium",
    "recovery_hint": "Check if the session exists using 'yesman ls'",
    "context": {
      "session_name": "my-session"
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 예상 이점

- 일관된 에러 처리
- 향상된 디버깅 능력
- 사용자 친화적인 에러 메시지
- 자동화된 에러 추적
