# 개발 문제 해결 가이드 (Troubleshooting)

## Python 가상 환경(`venv`) 생성 시 `pip` 실행 파일 누락 문제

### 현상

- `python -m venv .venv` 명령으로 가상 환경을 생성해도, `.venv/bin/` 디렉터리 안에 `pip` 실행 파일이 생성되지 않아 의존성 설치에 실패합니다.

### 원인

- 프로젝트 개발 환경에서 사용하는 Python 인터프리터가 시스템 표준 Python이 아닌, 특정 애플리케이션(예: Cursor 에디터)에 내장된 `AppImage` 버전일 수 있습니다.
- 이러한 비표준 Python 환경에서는 `venv` 모듈이 `pip` 실행 파일을 정상적으로 생성하지 않을 수 있습니다.

### 해결 방안

`pip` 실행 파일을 직접 호출하는 대신, **Python 인터프리터를 통해 `pip` 모듈을 실행**하는 방식을 사용합니다. 이 방법은 실행 파일의 경로에 의존하지 않아 훨씬 안정적입니다.

- **잘못된 명령어:** `.venv/bin/pip install -r requirements.txt`
- **올바른 명령어:** `.venv/bin/python -m pip install -r requirements.txt`

### 권장 사항

이 프로젝트에서는 Python 의존성을 설치할 때 항상 `python -m pip` 방식을 사용하는 것을 표준으로 합니다.
