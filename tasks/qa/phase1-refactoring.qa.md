# title: Phase 1 리팩토링 검증 QA 시나리오

## related_tasks

- /tasks/done/01-phase1-remove-duplicates\_\_DONE_20250716.md

## purpose

Phase 1 리팩토링(중복 제거)이 기존 기능을 손상시키지 않고 정상적으로 완료되었는지 검증

## scenario

### 1. 명령어 기능 검증

1. `yesman ls` 명령어 실행

   - 프로젝트와 템플릿 목록이 정상 출력되는지 확인
   - `--format` 옵션 (table, json, yaml) 동작 확인
   - 프로젝트 상태(running/stopped) 표시 확인

1. `yesman setup [session_name]` 명령어 실행

   - 단일 세션 설정 동작 확인
   - 전체 세션 설정 동작 확인
   - 오류 처리 및 경고 메시지 확인
   - 설정 완료 후 세션 목록 표시 확인

1. `yesman up` 별칭 동작 확인

   - `setup` 명령어와 동일하게 작동하는지 확인

### 2. API 엔드포인트 검증

1. 세션 관리 API 테스트

   ```bash
   # 모든 세션 조회
   curl http://localhost:8000/api/sessions

   # 특정 세션 조회
   curl http://localhost:8000/api/sessions/{session_name}

   # 세션 설정
   curl -X POST http://localhost:8000/api/sessions/{session_name}/setup

   # 모든 세션 설정
   curl -X POST http://localhost:8000/api/sessions/setup-all

   # 세션 삭제
   curl -X DELETE http://localhost:8000/api/sessions/{session_name}

   # 모든 세션 삭제
   curl -X POST http://localhost:8000/api/sessions/teardown-all

   # 세션 시작/중지
   curl -X POST http://localhost:8000/api/sessions/{session_name}/start
   curl -X POST http://localhost:8000/api/sessions/{session_name}/stop

   # 세션 상태 확인
   curl http://localhost:8000/api/sessions/{session_name}/status
   ```

1. 에러 처리 검증

   - 존재하지 않는 세션 조회
   - 이미 존재하는 세션 생성 시도
   - 권한 없는 작업 시도

### 3. 코드 품질 검증

1. import 검증

   ```bash
   # 잘못된 import 참조 확인
   grep -r "ls_improved\|setup_improved\|sessions_improved" --include="*.py" .
   ```

1. 유닛 테스트 실행

   ```bash
   # 명령어 테스트
   python -m pytest tests/unit/commands/test_ls_command.py
   python -m pytest tests/unit/commands/test_setup_command.py

   # API 테스트  
   python -m pytest tests/unit/api/test_sessions.py
   ```

1. 통합 테스트 실행

   ```bash
   cd tests/integration
   ./run_tests.sh
   ```

### 4. 파일 구조 검증

1. 삭제된 파일들이 없는지 확인

   ```bash
   # 중복 파일이 삭제되었는지 확인
   ls commands/ls_improved.py 2>/dev/null && echo "ERROR: File should be deleted"
   ls commands/setup_improved.py 2>/dev/null && echo "ERROR: File should be deleted"
   ls api/routers/sessions_improved.py 2>/dev/null && echo "ERROR: File should be deleted"
   ls -d test-integration 2>/dev/null && echo "ERROR: Directory should be deleted"
   ```

1. 병합된 기능 확인

   - 개선된 버전의 모든 기능이 유지되는지 확인
   - BaseCommand 패턴 적용 확인
   - 의존성 주입 패턴 적용 확인

## expected_result

### 명령어

- `ls` 명령어: 테이블, JSON, YAML 형식으로 프로젝트 목록 출력
- `setup` 명령어: 세션 생성 및 설정 완료 후 실행 중인 세션 목록 표시
- `up` 별칭이 `setup`과 동일하게 작동

### API

- 모든 엔드포인트가 정상 응답 (200/201/204)
- 에러 상황에서 적절한 상태 코드와 메시지 반환
- 배치 작업(setup-all, teardown-all) 정상 동작

### 코드 품질

- 중복 파일 참조 없음
- 모든 테스트 통과
- import 오류 없음
- 기능 누락 없음

## tags

[qa], [refactoring], [integration], [api-test], [command-test]
