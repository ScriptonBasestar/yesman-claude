# Lint 설정 통합 가이드

이 프로젝트의 lint 도구들이 일치하도록 설정을 통합했습니다.

## 🔧 주요 변경사항

### 1. Makefile 업데이트

**새로운 명령어들:**

- `make lint`: 핵심 코드만 체크 (libs, commands)
- `make lint-fix`: 자동 수정 포함 lint
- `make lint-all`: 테스트/예제 파일 포함 전체 체크
- `make validate-hooks`: 모든 hooks 일치성 검증
- `make pre-push-test`: pre-push 단계 테스트
- `make validate-lint-config`: 자동화된 일치성 검증

### 2. Pre-commit 설정 개선

**핵심 변경사항:**

- ruff 검사 범위를 핵심 코드로 제한 (tests, docs/examples 제외)
- pre-push 단계에서 lint + 빠른 테스트 실행
- make lint와 동일한 검사 범위 적용

### 3. 자동 검증 스크립트

`scripts/validate-lint-config.py`:

- make lint, pre-commit, pre-push 일치성 자동 검증
- 실패 시 상세한 오류 정보 제공
- 모든 설정 통합 테스트

## 🚀 사용법

### 기본 개발 워크플로우

```bash
# 1. 코드 작성 후 빠른 체크
make lint

# 2. 자동 수정이 필요한 경우
make lint-fix

# 3. 커밋 전 전체 검증
make validate-hooks

# 4. Push 전 최종 검증
make pre-push-test
```

### 설정 검증

```bash
# lint 설정 일치성 검증
make validate-lint-config

# 또는 직접 실행
python3 scripts/validate-lint-config.py
```

## 📋 각 도구의 검사 범위

| 도구            | 검사 범위                            | 목적                 |
| --------------- | ------------------------------------ | -------------------- |
| `make lint`     | libs, commands                       | 개발 중 빠른 검증    |
| `make lint-all` | libs, commands, tests, docs/examples | 전체 코드베이스 검증 |
| `pre-commit`    | libs, commands                       | 커밋 시 자동 검증    |
| `pre-push`      | libs, commands + 테스트              | 푸시 전 최종 검증    |

## 🔍 문제 해결

### 1. pre-commit 실패 시

```bash
# hooks 재설치
make pre-commit-install

# 전체 파일에 대해 실행
make pre-commit-run
```

### 2. make lint와 pre-commit 결과 다를 때

```bash
# 일치성 검증 실행
make validate-lint-config

# 설정 차이점 확인 후 수정
```

### 3. pre-push 실패 시

```bash
# pre-push 단계 수동 테스트
make pre-push-test

# 문제 파일 개별 수정 후 재시도
```

## ⚙️ 설정 파일 위치

- **Makefile**: `make lint` 등 명령어 정의
- **.pre-commit-config.yaml**: pre-commit hooks 설정
- **pyproject.toml**: ruff, mypy 등 도구별 상세 설정
- **scripts/validate-lint-config.py**: 자동 검증 스크립트

## 🎯 일치된 설정

모든 lint 도구가 다음 설정으로 통일되었습니다:

- **Python 버전**: 3.11
- **검사 범위**: libs, commands (핵심 코드)
- **Ruff 설정**: pyproject.toml 기준
- **MyPy 설정**: pyproject.toml 기준
- **Bandit 보안 검사**: 동일한 skip 규칙 적용

이제 `make lint`, `pre-commit`, `pre-push`가 모두 일치하는 결과를 제공합니다.
