# Mixed Configuration Example

projects.yaml과 sessions/*.yaml 파일을 함께 사용하는 예시입니다.

## 구조

```
~/.scripton/yesman/
├── projects.yaml         # 공통 프로젝트 정의
├── sessions/            # 개별 세션 파일들
│   ├── dev-frontend.yaml
│   ├── dev-backend.yaml
│   └── prod-monitor.yaml
└── templates/
    └── base.yaml
```

## projects.yaml - 공통 프로젝트 정의

```yaml
# 템플릿 기반 세션들
sessions:
  # 기본 개발 환경
  dev-workspace:
    template_name: "base"
    override:
      session_name: "workspace"
      start_directory: "~/workspace"
      
  # 프로덕션 모니터링 (sessions/prod-monitor.yaml에서 오버라이드됨)
  prod-monitor:
    template_name: "monitoring"
    override:
      session_name: "prod-mon"
      start_directory: "/var/log"
```

## sessions/dev-frontend.yaml - 개별 세션 파일

```yaml
# 이 파일은 projects.yaml에 없는 새로운 세션을 추가
template_name: "react"
override:
  session_name: "dev-frontend"
  start_directory: "~/projects/frontend"
  windows:
    - window_name: "main"
      panes:
        - claude
        - npm run dev
```

## sessions/prod-monitor.yaml - projects.yaml 오버라이드

```yaml
# projects.yaml의 prod-monitor를 완전히 오버라이드
session_name: "prod-monitor"  # 다른 이름 사용
start_directory: "/var/log/production"
environment:
  ALERT_LEVEL: "critical"
windows:
  - window_name: "alerts"
    panes:
      - tail -f /var/log/nginx/error.log
      - tail -f /var/log/app/error.log
```

## 최종 결과

```bash
yesman ls
# 출력:
# - workspace (from projects.yaml)
# - dev-frontend (from sessions/dev-frontend.yaml)
# - prod-monitor (from sessions/prod-monitor.yaml - overrides projects.yaml)
```