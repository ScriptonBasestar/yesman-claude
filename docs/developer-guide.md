# Yesman Claude 개발자 가이드

## 📋 목차

1. [아키텍처 개요](#%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98-%EA%B0%9C%EC%9A%94)
1. [개발 환경 설정](#%EA%B0%9C%EB%B0%9C-%ED%99%98%EA%B2%BD-%EC%84%A4%EC%A0%95)
1. [새로운 명령어 추가](#%EC%83%88%EB%A1%9C%EC%9A%B4-%EB%AA%85%EB%A0%B9%EC%96%B4-%EC%B6%94%EA%B0%80)
1. [API 엔드포인트 추가](#api-%EC%97%94%EB%93%9C%ED%8F%AC%EC%9D%B8%ED%8A%B8-%EC%B6%94%EA%B0%80)
1. [설정 관리](#%EC%84%A4%EC%A0%95-%EA%B4%80%EB%A6%AC)
1. [에러 처리](#%EC%97%90%EB%9F%AC-%EC%B2%98%EB%A6%AC)
1. [테스트 가이드](#%ED%85%8C%EC%8A%A4%ED%8A%B8-%EA%B0%80%EC%9D%B4%EB%93%9C)
1. [배포 가이드](#%EB%B0%B0%ED%8F%AC-%EA%B0%80%EC%9D%B4%EB%93%9C)

## 🏗️ 아키텍처 개요

Yesman Claude는 다음과 같은 핵심 패턴들을 사용합니다:

### Command Pattern

모든 CLI 명령어는 `BaseCommand`를 상속받아 표준화된 방식으로 구현됩니다.

```python
from libs.core.base_command import BaseCommand

class MyCommand(BaseCommand):
    def execute(self, **kwargs) -> dict:
        # 명령어 실행 로직
        return {"success": True, "message": "작업 완료"}
```

### Dependency Injection

서비스들은 DI 컨테이너를 통해 관리되며, 테스트와 유지보수를 용이하게 합니다.

```python
from libs.core.services import get_config, get_tmux_manager

config = get_config()           # YesmanConfig 인스턴스
tmux_manager = get_tmux_manager()  # TmuxManager 인스턴스
```

### Configuration Management

Pydantic 스키마 기반의 타입 안전한 설정 관리를 제공합니다.

```python
# 타입 안전한 설정 접근
log_level = config.schema.logging.level
tmux_shell = config.schema.tmux.default_shell
```

### Error Handling

중앙화된 에러 처리 시스템으로 일관된 에러 응답을 제공합니다.

```python
from libs.core.error_handling import SessionError

raise SessionError(
    "세션을 찾을 수 없습니다",
    session_name="myproject",
    recovery_hint="'yesman show'로 세션 목록을 확인하세요"
)
```

## 🛠️ 개발 환경 설정

### 요구 사항

- Python 3.11+
- tmux
- Git

### 설치

```bash
# 저장소 클론
git clone <repository-url>
cd yesman-claude

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 의존성 설치
pip install -e .

# 개발 의존성 설치
pip install pytest pytest-cov ruff mypy pre-commit
```

### 개발 환경 설정

```bash
# 개발 환경 설정
export YESMAN_ENV=development

# 설정 파일 생성 (선택적)
mkdir -p ~/.scripton/yesman
cp config/development.yaml ~/.scripton/yesman/yesman.yaml

# Git hooks 설치 (권장)
make hooks-install

# 코드 품질 검사
make lint
make format
```

## ➕ 새로운 명령어 추가

### 1. 명령어 클래스 생성

새로운 명령어를 `commands/` 디렉토리에 생성합니다:

```python
# commands/example.py
"""Example command implementation"""

import click
from libs.core.base_command import BaseCommand
from libs.core.error_handling import ValidationError


class ExampleCommand(BaseCommand):
    """예시 명령어 클래스"""

    def execute(self, name: str = None, **kwargs) -> dict:
        """
        명령어 실행 로직
        
        Args:
            name: 예시 매개변수
            **kwargs: 추가 매개변수들
            
        Returns:
            실행 결과 딕셔너리
            
        Raises:
            ValidationError: 잘못된 입력값
        """
        if not name:
            raise ValidationError(
                "이름이 필요합니다",
                field_name="name",
                recovery_hint="--name 옵션으로 이름을 지정하세요"
            )
        
        # 실제 명령어 로직
        self.print_info(f"안녕하세요, {name}님!")
        
        return {
            "success": True,
            "message": f"{name}님에게 인사했습니다",
            "data": {"name": name}
        }


@click.command()
@click.option("--name", help="인사할 대상의 이름")
def example(name):
    """예시 명령어"""
    command = ExampleCommand()
    command.run(name=name)
```

### 2. yesman.py에 명령어 등록

```python
# yesman.py
from commands.example import example

@cli.command()
def example_cmd():
    """예시 명령어"""
    example()
```

### 3. 명령어 믹스인 사용

공통 기능이 필요한 경우 믹스인을 사용합니다:

```python
from libs.core.base_command import BaseCommand, SessionCommandMixin

class SessionExampleCommand(BaseCommand, SessionCommandMixin):
    """세션 관련 예시 명령어"""
    
    def execute(self, session_name: str, **kwargs) -> dict:
        # 세션 관련 기능 사용
        session = self.get_session(session_name)
        if not session:
            raise SessionError(f"세션 '{session_name}'을 찾을 수 없습니다")
        
        # 세션 작업 수행
        return {"success": True}
```

## 🌐 API 엔드포인트 추가

### 1. 라우터 생성

```python
# api/routers/example.py
"""Example API endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from libs.core.services import get_config
from libs.core.error_handling import ValidationError

router = APIRouter()


class ExampleRequest(BaseModel):
    name: str
    message: str | None = None


class ExampleResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


@router.post("/example", response_model=ExampleResponse)
async def create_example(request: ExampleRequest):
    """예시 API 엔드포인트"""
    try:
        # DI를 통한 서비스 접근
        config = get_config()
        
        # 비즈니스 로직
        result = process_example(request.name, request.message)
        
        return ExampleResponse(
            success=True,
            message="처리 완료",
            data=result
        )
    except ValidationError as e:
        # YesmanError는 자동으로 적절한 HTTP 상태코드로 변환됩니다
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def process_example(name: str, message: str | None) -> dict:
    """비즈니스 로직 함수"""
    if not name.strip():
        raise ValidationError("이름은 필수입니다", field_name="name")
    
    return {"processed_name": name.upper(), "processed_message": message}
```

### 2. main.py에 라우터 등록

```python
# api/main.py
from api.routers import example

app.include_router(example.router, prefix="/api", tags=["example"])
```

### 3. API 테스트

```python
# tests/test_example_api.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_example_endpoint():
    """예시 API 테스트"""
    response = client.post(
        "/api/example",
        json={"name": "테스트", "message": "안녕하세요"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["processed_name"] == "테스트"
```

## ⚙️ 설정 관리

### 환경별 설정

```yaml
# config/development.yaml
logging:
  level: DEBUG
  
confidence_threshold: 0.5
auto_cleanup_days: 7

# config/production.yaml
logging:
  level: WARNING
  max_size: 52428800  # 50MB
  
confidence_threshold: 0.9
auto_cleanup_days: 30
```

### 환경변수 사용

```bash
# 특정 설정을 환경변수로 오버라이드
export YESMAN_LOGGING_LEVEL=ERROR
export YESMAN_TMUX_DEFAULT_SHELL=/bin/zsh
export YESMAN_CONFIDENCE_THRESHOLD=0.95
```

### 프로그래매틱 설정

```python
from libs.core.config_loader import ConfigLoader, DictSource

# 테스트용 설정
loader = ConfigLoader()
loader.add_source(DictSource({
    "logging": {"level": "ERROR"},
    "test_mode": True
}))

config = YesmanConfig(config_loader=loader)
```

## 🚨 에러 처리

### 표준 에러 클래스 사용

```python
from libs.core.error_handling import (
    ConfigurationError,
    SessionError,
    ValidationError,
    NetworkError
)

# 설정 관련 에러
raise ConfigurationError(
    "설정 파일을 찾을 수 없습니다",
    config_file="/path/to/config.yaml"
)

# 세션 관련 에러
raise SessionError(
    "세션이 이미 존재합니다",
    session_name="myproject",
    recovery_hint="다른 이름을 사용하거나 기존 세션을 종료하세요"
)

# 검증 에러
raise ValidationError(
    "포트 번호가 유효하지 않습니다",
    field_name="port",
    recovery_hint="1-65535 범위의 포트 번호를 입력하세요"
)
```

### 커스텀 에러 코드

```python
from libs.core.error_handling import YesmanError, ErrorCategory, ErrorSeverity

class CustomError(YesmanError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.LOW,
            error_code="CUSTOM_001",
            recovery_hint="커스텀 에러 해결 방법",
            **kwargs
        )
```

## 🧪 테스트 가이드

### 유닛 테스트

```python
# tests/test_example_command.py
import pytest
from unittest.mock import MagicMock
from commands.example import ExampleCommand
from libs.core.services import register_test_services


def test_example_command_success():
    """성공 케이스 테스트"""
    # 테스트용 서비스 등록
    mock_config = MagicMock()
    register_test_services(config=mock_config)
    
    command = ExampleCommand()
    result = command.execute(name="테스트")
    
    assert result["success"] is True
    assert "테스트" in result["message"]


def test_example_command_validation_error():
    """검증 에러 테스트"""
    command = ExampleCommand()
    
    with pytest.raises(ValidationError) as exc_info:
        command.execute(name="")
    
    assert "이름이 필요합니다" in str(exc_info.value)
```

### 통합 테스트

```python
# tests/integration/test_command_integration.py
import subprocess
import pytest


def test_example_command_cli():
    """CLI 통합 테스트"""
    result = subprocess.run(
        ["python", "-m", "yesman", "example", "--name", "통합테스트"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "통합테스트" in result.stdout
```

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_example_command.py

# 커버리지 포함 실행
pytest --cov=libs --cov=commands

# 특정 마커 테스트만 실행
pytest -m unit
pytest -m integration
```

## 🚀 배포 가이드

### 개발 모드 실행

```bash
# CLI 개발 모드
export YESMAN_ENV=development
python -m yesman --help

# API 서버 개발 모드
export YESMAN_ENV=development
uvicorn api.main:app --reload --port 8000
```

### 프로덕션 배포

```bash
# 환경 설정
export YESMAN_ENV=production
export YESMAN_LOGGING_LEVEL=WARNING

# Python 패키지 빌드
make build

# API 서버 실행
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# 또는 Makefile 사용
make build-all  # 전체 프로젝트 빌드
```

### Docker 배포

```bash
# Docker 이미지 빌드
make docker-build

# Docker 컨테이너 실행
make docker-run

# Docker 상태 확인
make docker-status
```

Dockerfile 예시:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

ENV YESMAN_ENV=production
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 코딩 가이드라인

### 코드 스타일

프로젝트는 Ruff를 사용하여 일관된 코드 스타일을 유지합니다:

```bash
# 코드 포맷팅 (Ruff 사용)
make format

# 린팅 검사
make lint

# 자동 수정 포함 린팅
make lint-fix

# 타입 체킹
make type-check

# 전체 품질 검사
make full
```

자세한 내용은 [Code Quality Guide](/docs/development/code-quality-guide.md)를 참조하세요.

### 커밋 메시지

```
feat(commands): add example command
fix(api): resolve session creation error
docs(adr): add configuration management decision
test(integration): add API endpoint tests
refactor(core): improve error handling
```

### 브랜치 전략

- `main`: 안정된 프로덕션 코드
- `develop`: 개발 브랜치
- `feature/task-name`: 기능 개발
- `hotfix/issue-name`: 긴급 수정

## 🔍 디버깅 팁

### 로깅 설정

```python
# 개발 시 상세 로깅
export YESMAN_LOGGING_LEVEL=DEBUG

# 특정 모듈만 로깅
import logging
logging.getLogger("yesman.tmux_manager").setLevel(logging.DEBUG)
```

### 에러 추적

```python
# 에러 컨텍스트 확인
try:
    command.execute()
except YesmanError as e:
    print(f"에러 코드: {e.error_code}")
    print(f"복구 힌트: {e.recovery_hint}")
    print(f"컨텍스트: {e.context}")
```

### DI 컨테이너 디버깅

```python
from libs.core.services import container

# 등록된 서비스 확인
print(container.get_registered_services())

# 특정 서비스 존재 확인
print(container.is_registered(YesmanConfig))
```

## 📚 추가 리소스

- [ADR (Architecture Decision Records)](./adr/)
- [API 문서](http://localhost:8000/docs) (서버 실행 시)
- [설정 스키마](../libs/core/config_schema.py)
- [에러 처리](../libs/core/error_handling.py)

## 🤝 기여하기

1. 이슈 생성 또는 기존 이슈 확인
1. 기능 브랜치 생성: `git checkout -b feature/my-feature`
1. 변경사항 커밋: `git commit -m 'feat: add my feature'`
1. 브랜치 푸시: `git push origin feature/my-feature`
1. Pull Request 생성

### PR 체크리스트

- [ ] 테스트가 모두 통과하는가?
- [ ] 코드 스타일 가이드를 따르는가?
- [ ] 문서가 업데이트되었는가?
- [ ] 새로운 기능에 대한 테스트가 추가되었는가?
- [ ] CHANGELOG가 업데이트되었는가?
