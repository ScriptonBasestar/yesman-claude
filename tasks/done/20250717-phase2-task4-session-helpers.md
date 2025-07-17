---
phase: 2
order: 4
source_plan: /tasks/plan/05-code-structure-refactoring.md
priority: medium
tags: [refactoring, session, utilities]
---

# 📌 작업: 세션 헬퍼 유틸리티 생성

## Phase: 2 - Extract Common Patterns

## 순서: 4

### 작업 내용

libs/utils/session_helpers.py 파일을 생성하여 세션 관련 공통 기능을 중앙화합니다.

### 구현할 헬퍼 함수

```python
def get_session_info(session_name: str) -> SessionInfo:
    """Get session information"""
    # tmux 세션 정보 조회
    # 윈도우, 패인 정보 포함
    pass

def create_session_windows(session_name: str, template: dict) -> None:
    """Create windows for session from template"""
    # 템플릿 기반 윈도우 생성
    pass

def get_active_pane(session_name: str, window_name: str) -> PaneInfo:
    """Get active pane in window"""
    pass

def send_keys_to_pane(session_name: str, window_index: int, pane_index: int, keys: str) -> None:
    """Send keys to specific pane"""
    pass
```

### 실행 단계

```yaml
- name: 세션 헬퍼 파일 생성
  file: libs/utils/session_helpers.py
  action: create

- name: 기존 세션 관련 코드 분석
  sources:
    - TmuxManager의 세션 관련 메서드
    - SessionManager의 유틸리티 기능
    - 각 명령어에서 반복되는 세션 처리 로직

- name: 통합 헬퍼 함수 구현
  functions:
    - get_session_info: 세션 정보 조회
    - create_session_windows: 템플릿 기반 윈도우 생성
    - get_active_pane: 활성 패인 조회
    - send_keys_to_pane: 패인에 키 전송
    - check_session_exists: 세션 존재 확인
    - list_session_windows: 윈도우 목록 조회
```

### 검증 조건

- [ ] 모든 헬퍼 함수가 구현됨
- [ ] TmuxManager와의 통합 완료
- [ ] 타입 안전성 보장
- [ ] 에러 처리 구현

### 영향받는 모듈

- libs/tmux_manager.py
- libs/core/session_manager.py
- commands/enter.py
- commands/browse.py
- api/routers/sessions.py

### 추가 구현 사항

- SessionInfo, PaneInfo 등 타입 정의
- 세션 관련 예외 클래스 정의
- 로깅 및 디버그 정보 추가
