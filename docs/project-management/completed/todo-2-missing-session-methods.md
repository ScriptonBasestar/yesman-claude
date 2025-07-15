# 이슈: `SessionManager`에 세션 생성/삭제 메서드 누락

## 문제 발생 단계

- **계획 파일:** `02-migrate-session-logic.md`
- **작업:** `api/routers/sessions.py`에 세션 관리 엔드포인트 구현

## 현상

`SessionManager` 클래스에는 세션을 설정(`setup`)하거나 제거(`teardown`)하는 메서드가 존재하지 않습니다. 따라서 `setup_tmux_session`과
`teardown_all_sessions` API 엔드포인트를 계획대로 구현할 수 없습니다.

## 원인 분석

- `SessionManager`는 이름 그대로 이미 실행 중인 세션의 \*\*상태를 관리(manage)\*\*하고 조회하는 역할에만 집중되어 있습니다.
- 실제 tmux 세션을 생성, 제어, 삭제하는 로직은 `TmuxManager` 클래스가 담당할 것으로 보입니다.
- 초기 분석 단계에서 두 클래스의 역할을 명확히 구분하지 못하여 잘못된 계획을 수립했습니다.

## 해결 방안

1. **`sessions.py` 수정:** 현재 구현 가능한 `get_all_sessions` 엔드포인트만 남기고, `setup` 및 `teardown` 관련 엔드포인트 코드는 주석 처리하거나 임시로 제거합니다.
1. **계획 수정:** 2단계 계획을 "세션 **조회** 로직 이전"으로 축소하고, 세션 **생성/삭제** 기능은 `TmuxManager`를 분석한 후 별도의 단계(예: 2.5단계)에서 다시 다루도록 계획을
   수정해야 합니다.

## 후속 조치

- `api/routers/sessions.py` 파일에서 구현 불가능한 엔드포인트를 제거합니다.
- `TmuxManager`의 코드를 분석하여 실제 세션 생성/삭제 로직을 파악하고, 이를 기반으로 새로운 API 엔드포인트를 설계합니다.
