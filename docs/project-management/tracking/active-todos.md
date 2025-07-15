# TODO.md

🛠 기술 스택 제안 구성 요소 역할 예시 도구 백엔드 언어 TUI 실행 + 자동 응답 로직 Python + pexpect 웹 프레임워크 WebSocket 서버 FastAPI, Flask-SocketIO 등 프론트엔드
구성 터미널 UI 화면 렌더링 xterm.js, webtty

✅ 다음 단계 제안 간단한 pexpect 테스트로 TUI 실행하고, 자동 응답 및 출력을 캡처하는지 확인

WebSocket → xterm.js 연결 데모 구현

yesman-claude 자동 응답 로직을 해당 구조에 통합

## IMPROVE-003: 인터랙티브 세션 브라우저 (UX)

**우선순위**: HIGH

\[ \] 세션 상태 히트맵 렌더링 (activity level 시각화)

- 관련 ISSUE: 프로젝트별 활성도 한눈에 파악
- 위치: libs/dashboard/widgets/activity_heatmap.py

\[ \] 키보드 네비게이션 지원 (방향키, Enter, ESC)

- 관련 ISSUE: 마우스 없이도 빠른 탐색 가능
- 위치: libs/dashboard/widgets/session_browser.py

## IMPROVE-010: 학습하는 자동응답 시스템 (ML/AI)

**우선순위**: HIGH

\[ \] 사용자 응답 패턴 수집 시스템 구현

- 관련 ISSUE: 현재 고정된 "1", "yes" 응답의 정확도 개선
- 위치: libs/dashboard/claude_manager.py

\[ \] 응답 히스토리 분석 엔진 구현 (패턴 인식 및 학습)

- 관련 ISSUE: 컨텍스트별 최적 응답 예측 필요
- 위치: libs/ai/response_analyzer.py

\[ \] 컨텍스트 기반 응답 예측 모델 구현

- 관련 ISSUE: 프롬프트 타입과 상황에 따른 지능적 선택
- 위치: libs/ai/adaptive_response.py

\[ \] 프로젝트별 학습 모델 분리 및 개인화

- 관련 ISSUE: 프로젝트 특성에 맞는 맞춤 설정
- 위치: libs/ai/personal_preferences.py

\[ \] 실수 패턴 감지 및 자동 개선 로직

- 관련 ISSUE: 잘못된 응답 후 학습 및 보정
- 위치: libs/ai/error_correction.py

\[ \] 학습 데이터 백업 및 복원 시스템

- 관련 ISSUE: 사용자 패턴 데이터 유실 방지
- 위치: libs/ai/learning_persistence.py

## IMPROVE-006: 상황 인식 자동 작업 체인 (Automation)

**우선순위**: MEDIUM

\[ \] 워크플로우 컨텍스트 감지 시스템 설계

- 관련 ISSUE: git commit, test failure 등 상황별 자동화 필요
- 위치: libs/automation/context_detector.py

\[ \] 작업 체인 정의 및 실행 엔진 구현

- 관련 ISSUE: 연쇄 작업 자동 실행 (test → build → deploy)
- 위치: libs/automation/workflow_engine.py

\[ \] 사용자 확인 시스템 구현 (자동/수동 모드 선택)

- 관련 ISSUE: 중요한 작업은 사용자 승인 후 실행
- 위치: libs/automation/confirmation_system.py

\[ \] 작업 실패시 rollback 및 복구 로직

- 관련 ISSUE: 자동화 중 오류 발생시 안전한 복구
- 위치: libs/automation/recovery_manager.py

\[ \] 워크플로우 템플릿 시스템 구현

- 관련 ISSUE: 프로젝트별 자동화 시나리오 커스터마이징
- 위치: libs/automation/workflow_templates.py

## IMPROVE-005: 프로젝트 상태 시각화 대시보드 (Visualization)

**우선순위**: MEDIUM

\[ \] Health Score 계산 알고리즘 정의 (빌드, 테스트, 의존성, 성능 지표)

- 관련 ISSUE: 프로젝트 전체 건강도 정량화 필요
- 위치: libs/dashboard/health_calculator.py

\[ \] 실시간 상태 위젯 UI 컴포넌트 구현

- 관련 ISSUE: 프로젝트 상태를 한눈에 보는 시각화
- 위치: libs/dashboard/widgets/project_health.py

\[ \] TODO 진행률 시각화 및 트래킹

- 관련 ISSUE: 일일 진행상황 및 완료율 표시
- 위치: libs/dashboard/widgets/progress_tracker.py

\[ \] Git 활동 그래프 및 커밋 메트릭 수집

- 관련 ISSUE: 개발 활동 패턴 시각화
- 위치: libs/dashboard/widgets/git_activity.py

\[ \] 리소스 사용량 트렌드 분석 (CPU, 메모리, 디스크)

- 관련 ISSUE: 시스템 부하 모니터링
- 위치: libs/dashboard/widgets/resource_monitor.py

\[ \] 프로젝트 간 성과 비교 대시보드

- 관련 ISSUE: 여러 프로젝트 효율성 벤치마킹
- 위치: libs/dashboard/widgets/project_comparison.py

## IMPROVE-002: 비동기 로그 처리 (Performance)

**우선순위**: MEDIUM

\[ \] AsyncLogger 클래스 설계 및 큐 기반 로그 시스템

- 관련 ISSUE: 동기식 로그 쓰기로 인한 성능 저하
- 위치: libs/logging/async_logger.py

\[ \] 배치 로그 처리 및 I/O 최적화 구현

- 관련 ISSUE: 로그 쓰기 작업을 배치로 처리하여 효율성 향상
- 위치: libs/logging/batch_processor.py

\[ \] 로그 레벨별 필터링 및 우선순위 처리

- 관련 ISSUE: 중요한 로그 우선 처리 및 불필요한 로그 제거
- 위치: libs/logging/log_filter.py

\[ \] 로그 큐 크기 제한 및 메모리 관리

- 관련 ISSUE: 메모리 오버플로우 방지 및 안정성 확보
- 위치: libs/logging/queue_manager.py

\[ \] 기존 로깅 시스템과의 호환성 보장

- 관련 ISSUE: 현재 사용 중인 로거들과 seamless 통합
- 위치: libs/utils.py, libs/dashboard/\*.py

## IMPROVE-004: AI 기반 자동 문제 해결 (AI/Automation)

**우선순위**: LOW

\[ \] 공통 이슈 패턴 감지 시스템 구현

- 관련 ISSUE: compilation error, port conflict 등 자동 감지
- 위치: libs/ai/issue_detector.py

\[ \] 솔루션 제안 엔진 및 자동 실행 옵션

- 관련 ISSUE: 감지된 문제에 대한 자동 해결책 제시
- 위치: libs/ai/solution_engine.py

\[ \] Claude 연동 오류 보고 시스템

- 관련 ISSUE: 복잡한 문제는 Claude에게 자동 보고 및 상담
- 위치: libs/ai/claude_integration.py

\[ \] 학습된 패턴 기반 예방적 조치 시스템

- 관련 ISSUE: 반복되는 문제 사전 방지
- 위치: libs/ai/preventive_system.py

## IMPROVE-008: 코드 생성 자동화 (DX)

**우선순위**: LOW

\[ \] TODO 항목 분석 및 코드 템플릿 매칭 시스템

- 관련 ISSUE: TODO에서 자동으로 보일러플레이트 생성
- 위치: libs/codegen/todo_analyzer.py

\[ \] 프로젝트 패턴 학습 엔진 (naming, structure, imports)

- 관련 ISSUE: 기존 코드 스타일에 맞는 일관성 있는 생성
- 위치: libs/codegen/pattern_learner.py

\[ \] API 엔드포인트, 테스트, 컴포넌트 템플릿 생성기

- 관련 ISSUE: 자주 사용되는 코드 패턴 자동 생성
- 위치: libs/codegen/template_generators.py

\[ \] 생성된 코드 검증 및 품질 체크

- 관련 ISSUE: 자동 생성 코드의 품질 보장
- 위치: libs/codegen/code_validator.py
