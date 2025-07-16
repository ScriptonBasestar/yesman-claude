---
phase: 2
order: 3
source_plan: /tasks/plan/05-code-structure-refactoring.md
priority: medium
tags: [refactoring, validation, utilities]
---

# 📌 작업: 검증 유틸리티 모듈 생성

## Phase: 2 - Extract Common Patterns

## 순서: 3

### 작업 내용

libs/utils/validation.py 파일을 생성하여 프로젝트 전반에서 사용되는 검증 로직을 중앙화합니다.

### 구현할 검증 함수

```python
def validate_session_name(name: str) -> bool:
    """Validate tmux session name"""
    # tmux 세션 이름 규칙 검증
    # - 영문자, 숫자, 언더스코어, 하이픈만 허용
    # - 첫 글자는 영문자
    # - 최대 길이 제한
    pass

def validate_project_name(name: str) -> bool:
    """Validate project name"""
    # 프로젝트 이름 규칙 검증
    pass

def validate_template_exists(template: str) -> bool:
    """Check if template exists"""
    # 템플릿 파일 존재 여부 확인
    pass
```

### 실행 단계

```yaml
- name: 검증 유틸리티 파일 생성
  file: libs/utils/validation.py
  action: create

- name: 기존 검증 로직 수집
  sources:
    - SessionValidator 클래스에서 검증 규칙 추출
    - 각 명령어에서 사용하는 검증 로직 확인
    - API 엔드포인트의 검증 로직 확인

- name: 통합 검증 함수 구현
  functions:
    - validate_session_name: tmux 세션 이름 규칙
    - validate_project_name: 프로젝트 이름 규칙
    - validate_template_exists: 템플릿 존재 확인
    - validate_window_name: 윈도우 이름 규칙
    - validate_pane_command: 명령어 검증
```

### 검증 조건

- [ ] 모든 검증 함수가 구현됨
- [ ] 기존 검증 로직과 동일한 동작 보장
- [ ] 명확한 오류 메시지 제공
- [ ] 유닛 테스트 작성

### 영향받는 모듈

- libs/core/session_validator.py
- commands/setup.py
- commands/enter.py
- api/routers/sessions.py

### 추가 고려사항

- 검증 실패 시 구체적인 오류 이유 반환
- 설정 파일에서 검증 규칙 커스터마이징 가능하도록 구현
