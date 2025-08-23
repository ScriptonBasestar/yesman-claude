# Yesman 명령어 개발 가이드

## 개요

이 가이드는 Yesman 프로젝트에서 새로운 명령어를 개발할 때 따라야 할 표준화된 방식을 설명합니다. BaseCommand 패턴을 사용하여 일관성 있고 유지보수가 용이한 명령어를 작성할 수 있습니다.

## BaseCommand 패턴 개요

모든 Yesman 명령어는 `BaseCommand` 클래스를 상속받아 구현됩니다. 이 패턴은 다음과 같은 장점을 제공합니다:

- **일관된 에러 처리**: 표준화된 예외 처리 및 복구 힌트
- **의존성 주입**: DI 컨테이너를 통한 서비스 해결
- **공통 기능**: 로깅, 설정 관리, 출력 포맷팅 등
- **테스트 용이성**: 모킹과 단위 테스트가 쉬움

## 새 명령어 작성하기

### 1. 기본 구조

```python
#!/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""새 명령어에 대한 설명."""

from typing import Any

import click

from libs.core.base_command import BaseCommand, CommandError


class MyNewCommand(BaseCommand):
    """새 명령어에 대한 설명."""

    def execute(self, **kwargs: Any) -> dict:
        """명령어 실행 로직.

        Args:
            **kwargs: 명령어 인자들

        Returns:
            dict: 실행 결과
        """
        # 명령어 로직 구현
        result = self._do_something()
        
        return {"success": True, "result": result}

    def _do_something(self) -> str:
        """실제 작업을 수행하는 private 메서드."""
        return "작업 완료"


@click.command()
@click.option("--option", help="옵션 설명")
@click.argument("argument", required=False)
def my_new_command(option: str | None, argument: str | None) -> None:
    """CLI 명령어 설명."""
    command = MyNewCommand()
    command.run(option=option, argument=argument)


if __name__ == "__main__":
    my_new_command()
```

### 2. 믹스인 사용하기

공통 기능이 필요한 경우 적절한 믹스인을 사용하세요:

```python
from libs.core.base_command import (
    BaseCommand,
    SessionCommandMixin,      # 세션 관련 기능
    ConfigCommandMixin,       # 설정 관리 기능
    OutputFormatterMixin      # 출력 포맷팅 기능
)


class MySessionCommand(BaseCommand, SessionCommandMixin, OutputFormatterMixin):
    """세션을 다루는 명령어."""

    def execute(self, **kwargs: Any) -> dict:
        # 세션 목록 가져오기 (SessionCommandMixin에서 제공)
        sessions = self.get_session_list()
        
        # 테이블 형태로 출력 (OutputFormatterMixin에서 제공)
        table_data = [{"name": name, "status": "running"} for name in sessions]
        table = self.format_table(table_data, ["name", "status"])
        click.echo(table)
        
        return {"sessions": sessions}
```

### 3. 에러 처리

명령어에서 발생할 수 있는 에러를 적절히 처리하세요:

```python
def execute(self, **kwargs: Any) -> dict:
    try:
        # 위험한 작업
        result = self._risky_operation()
        return {"success": True, "result": result}
    except SomeSpecificError as e:
        # 구체적인 에러에 대한 복구 힌트 제공
        raise CommandError(
            f"작업 실패: {e}",
            recovery_hint="설정 파일을 확인하고 다시 시도하세요"
        ) from e
    except Exception as e:
        # 예상치 못한 에러
        raise CommandError(f"예상치 못한 오류: {e}") from e
```

### 4. 전제 조건 검증

명령어 실행 전에 확인해야 할 조건이 있다면 `validate_preconditions`를 오버라이드하세요:

```python
def validate_preconditions(self) -> None:
    """명령어 전제 조건 검증."""
    super().validate_preconditions()  # 기본 검증 실행
    
    # 추가 검증
    if not self._check_custom_requirement():
        raise CommandError("사용자 정의 요구사항이 충족되지 않음")

def _check_custom_requirement(self) -> bool:
    """사용자 정의 요구사항 검증."""
    return True  # 실제 검증 로직 구현
```

## 비동기 명령어

비동기 작업이 필요한 명령어는 `AsyncBaseCommand`를 상속받으세요:

```python
from libs.core.async_base_command import AsyncMonitoringCommand


class MyAsyncCommand(AsyncMonitoringCommand):
    """비동기 명령어."""

    async def execute_async(self, **kwargs: Any) -> dict:
        """비동기 실행 로직."""
        result = await self._async_operation()
        return {"success": True, "result": result}

    async def _async_operation(self) -> str:
        """비동기 작업."""
        await asyncio.sleep(1)  # 예시
        return "비동기 작업 완료"
```

## 테스트 작성하기

모든 새 명령어에는 단위 테스트를 작성해야 합니다:

```python
# tests/unit/commands/test_my_new_command.py
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from commands.my_new_command import MyNewCommand, my_new_command
from libs.core.base_command import BaseCommand


class TestMyNewCommand:
    """MyNewCommand 테스트."""

    def setup_method(self) -> None:
        """테스트 환경 설정."""
        self.runner = CliRunner()

    def test_command_inheritance(self) -> None:
        """BaseCommand 상속 확인."""
        assert issubclass(MyNewCommand, BaseCommand)

    @patch("commands.my_new_command.MyNewCommand")
    def test_cli_command(self, mock_command_class: MagicMock) -> None:
        """CLI 명령어 테스트."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command
        result = self.runner.invoke(my_new_command, ["--option", "test"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(option="test", argument=None)

    def test_execute_success(self) -> None:
        """성공적인 실행 테스트."""
        with patch.object(MyNewCommand, '__init__', lambda x: None):
            command = MyNewCommand()
            result = command.execute()
            
            assert result["success"] is True
```

## 명령어 등록하기

새 명령어를 프로젝트에 등록하려면:

1. **파일 위치**: `commands/` 디렉토리에 새 파일 생성
2. **명명 규칙**: `{command_name}.py` 형식으로 파일명 지정
3. **메인 CLI 등록**: `yesman.py`의 메인 CLI에 명령어 추가

```python
# yesman.py에서
from commands.my_new_command import my_new_command

@click.group()
def cli():
    """Yesman CLI."""

# 명령어 추가
cli.add_command(my_new_command)
```

## 출력 메시지 가이드라인

명령어의 출력은 사용자 친화적이어야 합니다:

```python
def execute(self, **kwargs: Any) -> dict:
    # 성공 메시지 - 녹색 체크마크
    self.print_success("작업이 성공적으로 완료되었습니다")
    
    # 경고 메시지 - 노란색 경고 표시
    self.print_warning("주의: 일부 파일이 누락되었습니다")
    
    # 에러 메시지 - 빨간색 X 표시
    self.print_error("작업 중 오류가 발생했습니다")
    
    # 정보 메시지 - 파란색 정보 표시
    self.print_info("참고: 추가 설정이 필요할 수 있습니다")
```

## CLI 옵션과 인자

명령어 인터페이스는 일관성을 유지해야 합니다:

```python
@click.command()
@click.option("--format", "-f", 
              type=click.Choice(["table", "json", "yaml"]), 
              default="table",
              help="출력 형식")
@click.option("--verbose", "-v", 
              is_flag=True, 
              help="상세한 출력")
@click.option("--dry-run", 
              is_flag=True, 
              help="실제 실행 없이 계획만 보기")
@click.argument("target", required=False)
def my_command(format: str, verbose: bool, dry_run: bool, target: str | None) -> None:
    """명령어 설명."""
    command = MyCommand()
    command.run(format=format, verbose=verbose, dry_run=dry_run, target=target)
```

## 성능 고려사항

- **지연 로딩**: 무거운 의존성은 필요할 때만 로드
- **캐싱**: 반복적인 작업 결과는 캐시 활용
- **진행 표시**: 오래 걸리는 작업은 진행률 표시

```python
from libs.core.progress_indicators import with_startup_progress

def execute(self, **kwargs: Any) -> dict:
    with with_startup_progress("작업 진행 중...") as update:
        update("1단계 완료")
        self._step_one()
        
        update("2단계 완료") 
        self._step_two()
        
        update("작업 완료")
```

## 모범 사례

1. **단일 책임**: 각 명령어는 하나의 명확한 목적을 가져야 함
2. **멱등성**: 같은 입력에 대해 같은 결과를 보장
3. **사용자 경험**: 명확한 메시지와 도움말 제공
4. **에러 복구**: 실패 시 복구 방법 안내
5. **테스트 커버리지**: 모든 주요 코드 경로에 대한 테스트

## 참고 자료

- [BaseCommand 클래스](../libs/core/base_command.py)
- [믹스인 클래스들](../libs/core/base_command.py#L323)
- [기존 명령어 예제](../commands/)
- [테스트 예제](../tests/unit/commands/)

## 문제 해결

**Q: 의존성 주입이 작동하지 않음**
A: `initialize_services()`가 호출되었는지 확인하고, DI 컨테이너에 서비스가 등록되었는지 확인하세요.

**Q: 테스트에서 명령어가 실제 실행됨**
A: `patch.object(Command, '__init__', lambda x: None)`을 사용하여 초기화를 모킹하세요.

**Q: 비동기 명령어에서 에러 발생**
A: 모든 외부 의존성이 올바르게 모킹되었는지 확인하고, `AsyncMonitoringCommand`를 상속받았는지 확인하세요.