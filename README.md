# Yesman Claude

`Claude code` 자동진행 도구

선택프롬프트: regex 또는 외부 LLM을 이용해 자동 처리
완료후 진행: 외부 LLM으로 다음작업 연속진행

## 설정 파일

### 글로벌 설정

글로벌 설정 파일은 다음 경로에 위치합니다:

```bash
$HOME/.yesman/yesman.yaml
$HOME/.yesman/projects.yaml
```

파일 구조 examples/참고

## 템플릿 시스템

Yesman-Claude는 재사용 가능한 tmux 세션 템플릿을 지원합니다. 템플릿을 사용하면 여러 프로젝트에서 일관된 개발 환경을 쉽게 구성할 수 있습니다.

### 템플릿 위치
템플릿 파일은 `~/.yesman/templates/` 디렉터리에 YAML 형식으로 저장됩니다.

### 기본 템플릿 구조
```yaml
session_name: "{{ session_name }}"
start_directory: "{{ start_directory }}"
windows:
  - window_name: main
    layout: even-horizontal
    panes:
      - claude --dangerously-skip-permissions
      - npm run dev
```

### Smart Templates
"스마트 템플릿"은 조건부 명령 실행을 지원합니다:

```yaml
panes:
  - shell_command: |
      # 의존성이 없거나 오래된 경우에만 설치
      if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
        echo "Dependencies missing or outdated, installing..."
        pnpm install
      else
        echo "Dependencies up to date, skipping install"
      fi
      pnpm dev
```

### 템플릿 사용하기
`projects.yaml`에서 템플릿을 참조하고 필요한 값을 오버라이드할 수 있습니다:

```yaml
sessions:
  my_project:
    template_name: django
    override:
      session_name: my_django_app
      start_directory: ~/projects/django-app
```

자세한 내용은 [템플릿 문서](docs/user-guide/templates.md)를 참조하세요.
