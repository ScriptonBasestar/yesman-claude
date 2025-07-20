# title: Phase 3 아키텍처 표준화 QA 시나리오

## related_tasks

- /tasks/done/phase-3-001-migrate-commands-to-basecommand\_\_DONE_20250717.md
- /tasks/done/phase-3-002-create-dependency-injection\_\_DONE_20250717.md
- /tasks/done/phase-3-003-centralize-configuration\_\_DONE_20250717.md
- /tasks/done/phase-3-004-standardize-error-handling\_\_DONE_20250717.md

## purpose

Phase 3에서 구현한 아키텍처 표준화(BaseCommand 패턴, DI 컨테이너, 설정 관리, 에러 처리)가 전체 시스템에서 일관되게 동작하는지 확인

## scenario

### 1. BaseCommand 패턴 통합 테스트

1. `yesman-claude multi-agent` 명령어 실행
1. validate_preconditions가 세션 검증을 수행하는지 확인
1. CommandError 발생 시 일관된 에러 메시지 출력 확인
1. 17개 명령어 중 무작위 5개 선택하여 BaseCommand 메서드 호출 검증

### 2. DI 컨테이너 생명주기 테스트

1. API 서버 시작 시 DIContainer 초기화 확인
1. 싱글톤 서비스가 요청 간 동일 인스턴스 반환하는지 검증
1. 테스트 모드에서 Mock 서비스 주입 동작 확인
1. 순환 의존성 감지 시 적절한 에러 발생 확인

### 3. 환경별 설정 관리 검증

1. YESMAN_ENV=development로 서버 실행
1. development.yaml 설정이 default.yaml을 오버라이드하는지 확인
1. 환경변수 YESMAN_API_PORT=9999 설정 시 우선순위 확인
1. 잘못된 설정값 입력 시 Pydantic 검증 에러 메시지 확인

### 4. 글로벌 에러 핸들링 E2E 테스트

1. API 엔드포인트에서 의도적 에러 발생
1. 에러 응답이 표준 형식 준수하는지 확인
   ```json
   {
     "error": {
       "code": "COMMAND_ERROR",
       "message": "...",
       "details": {...},
       "recovery_hint": "..."
     }
   }
   ```
1. 서로 다른 에러 타입별 HTTP 상태 코드 매핑 확인
1. 로그에 전체 스택 트레이스 기록되는지 검증

## expected_result

- 모든 명령어가 BaseCommand 패턴을 따르며 일관된 동작
- DI 컨테이너가 의존성을 올바르게 관리하고 테스트 가능
- 환경별 설정이 계층적으로 적용되고 검증됨
- 에러가 사용자 친화적이고 일관된 형식으로 표시됨
- 시스템 전체의 아키텍처 일관성 확보

## tags

[qa], [e2e], [integration], [architecture], [phase-3]
