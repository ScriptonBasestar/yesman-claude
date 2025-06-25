# ✅ TODO.md (MVP 필수 기능)

| 카테고리 | 작업 내용 |
|----------|-----------|
| 설정     | 글로벌 설정 파일 로딩 (`~/.yesman/yesman.yaml`) |
| 설정     | 프로젝트 설정 파일 로딩 (`./.yesman/yesman.yaml`) |
| 실행     | `projects.yaml` 기반 `tmux` 세션 및 패널 분할 구조 생성 |
| 자동입력 | 패턴 디렉토리에서 텍스트 로딩 및 일치 검사 |
| 자동입력   | 패턴 종류에 따라 선택 입력값 다르게 처리 (`yes`, `2` 등) |
| 자동입력   | 선택지 응답 히스토리 기록 및 캐시 |
| 자동입력   | 선택지 입력 후 대기 시간 조정 옵션 추가 |
| 성능       | 패턴 매칭 속도 개선 (캐시, 슬라이딩 버퍼 구조 도입) |
| 설정       | 선택 timeout 등 고급 설정 지원 (`yesman.yaml`에 추가) |
| 모니터링   | Claude 작업 진행률 / 사용량 대시보드 구현 |

## 나중에
- 브랜치 자동분할 멀티 agent 구동기능
- LLM으로 출력 판단하여 선택 자동 결정<br>참고: `FEATURES.md` - 향후기능

ProjectPanel에서 tree항목에서 세션이 focus되면 우측의 ControllerPanel에 자동으로 현재 세션에 대한 컨트롤러가 표시되도록.
- 세션이름
- claude pane 재시작
- model선택(default, opus, sonnet)
- auto next