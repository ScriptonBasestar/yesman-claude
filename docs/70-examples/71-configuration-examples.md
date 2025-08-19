# 설정 예제 및 템플릿

Yesman-Agent의 다양한 사용 사례별 설정 예제와 템플릿을 제공합니다.

## 📚 목차

1. [기본 설정](#%EA%B8%B0%EB%B3%B8-%EC%84%A4%EC%A0%95)
1. [개발 환경별 설정](#%EA%B0%9C%EB%B0%9C-%ED%99%98%EA%B2%BD%EB%B3%84-%EC%84%A4%EC%A0%95)
1. [고급 설정](#%EA%B3%A0%EA%B8%89-%EC%84%A4%EC%A0%95)
1. [팀 협업 설정](#%ED%8C%80-%ED%98%91%EC%97%85-%EC%84%A4%EC%A0%95)
1. [문제 해결 시나리오](#%EB%AC%B8%EC%A0%9C-%ED%95%B4%EA%B2%B0-%EC%8B%9C%EB%82%98%EB%A6%AC%EC%98%A4)

## 🔧 기본 설정

### 최소 설정 (Minimal Setup)

가장 간단한 설정으로 빠르게 시작할 수 있습니다.

#### `~/.scripton/yesman/yesman.yaml`

```yaml
# 최소 설정 - 기본값 사용
logging:
  level: "INFO"
  directory: "~/tmp/logs/yesman"

defaults:
  auto_response: true
  session_timeout: 300
```

#### `~/.scripton/yesman/sessions/my-project.yaml`

```yaml
session_name: my-project
start_directory: "~/projects/my-project"

windows:
  - window_name: main
    panes:
      - shell_command: ["cd ~/projects/my-project", "claude"]
```

### 기본 개발 환경

웹 개발을 위한 표준 설정입니다.

#### `~/.scripton/yesman/sessions/web-development.yaml`

```yaml
session_name: web-dev
start_directory: "~/projects/my-website"

windows:
  - window_name: editor
    layout: main-vertical
    panes:
      - shell_command: ["cd ~/projects/my-website", "nvim ."]
      - shell_command: ["cd ~/projects/my-website", "npm run dev"]

  - window_name: server
    panes:
      - shell_command: ["cd ~/projects/my-website", "npm run start"]
      - shell_command: ["cd ~/projects/my-website", "npm run test:watch"]

  - window_name: tools
    layout: tiled
    panes:
      - shell_command: ["cd ~/projects/my-website", "git status"]
      - shell_command: ["cd ~/projects/my-website", "claude"]
      - shell_command: ["htop"]
      - shell_command: ["cd ~/projects/my-website", "npm run lint"]
```

## 🌐 개발 환경별 설정

### Python/Django 프로젝트

Django 개발을 위한 완전한 설정입니다.

#### `~/.scripton/yesman/templates/django.yaml`

```yaml
session_name: "{{ project_name }}-django"
start_directory: "{{ project_path }}"

before_script:
  - "source venv/bin/activate"

windows:
  - window_name: editor
    layout: main-vertical
    options:
      main-pane-width: 70%
    panes:
      - shell_command: 
          - "cd {{ project_path }}"
          - "source venv/bin/activate"
          - "nvim ."
      - shell_command:
          - "cd {{ project_path }}"
          - "source venv/bin/activate"
          - "python manage.py shell"

  - window_name: server
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "source venv/bin/activate"
          - "python manage.py runserver"

  - window_name: database
    layout: even-horizontal
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "source venv/bin/activate"
          - "python manage.py dbshell"
      - shell_command:
          - "cd {{ project_path }}"
          - "source venv/bin/activate"
          - "python manage.py migrate"

  - window_name: testing
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "source venv/bin/activate"
          - "python manage.py test --keepdb"

  - window_name: claude
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "claude"
```

### React/Node.js 프로젝트

React 개발을 위한 프론트엔드 중심 설정입니다.

#### `~/.scripton/yesman/templates/react.yaml`

```yaml
session_name: "{{ project_name }}-react"
start_directory: "{{ project_path }}"

windows:
  - window_name: development
    layout: main-vertical
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "npm run dev"
      - shell_command:
          - "cd {{ project_path }}"
          - "npm run storybook"

  - window_name: testing
    layout: even-horizontal
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "npm run test:watch"
      - shell_command:
          - "cd {{ project_path }}"
          - "npm run test:e2e"

  - window_name: build
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "npm run build:watch"

  - window_name: editor
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "code ."

  - window_name: claude
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "claude"
```

### 데이터 사이언스 환경

Python 데이터 분석을 위한 설정입니다.

#### `~/.scripton/yesman/templates/data-science.yaml`

```yaml
session_name: "{{ project_name }}-ds"
start_directory: "{{ project_path }}"

windows:
  - window_name: jupyter
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "conda activate {{ env_name | default('base') }}"
          - "jupyter lab --port=8888"

  - window_name: analysis
    layout: main-vertical
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "conda activate {{ env_name | default('base') }}"
          - "ipython"
      - shell_command:
          - "cd {{ project_path }}"
          - "conda activate {{ env_name | default('base') }}"
          - "python -m http.server 8000"

  - window_name: monitoring
    layout: even-horizontal
    panes:
      - shell_command: ["htop"]
      - shell_command: ["nvidia-smi -l 1"]

  - window_name: claude
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "conda activate {{ env_name | default('base') }}"
          - "claude"
```

## 🚀 고급 설정

### 마이크로서비스 개발

여러 서비스를 동시에 개발하는 환경입니다.

#### `~/.scripton/yesman/sessions/microservices.yaml`

```yaml
session_name: microservices-dev
start_directory: "~/projects/microservices"

windows:
  - window_name: api-gateway
    panes:
      - shell_command:
          - "cd ~/projects/microservices/gateway"
          - "npm run dev"

  - window_name: user-service
    layout: even-horizontal
    panes:
      - shell_command:
          - "cd ~/projects/microservices/user-service"
          - "python app.py"
      - shell_command:
          - "cd ~/projects/microservices/user-service"
          - "python -m pytest -xvs"

  - window_name: order-service
    layout: even-horizontal
    panes:
      - shell_command:
          - "cd ~/projects/microservices/order-service"
          - "go run main.go"
      - shell_command:
          - "cd ~/projects/microservices/order-service"
          - "go test -v ./..."

  - window_name: infrastructure
    layout: tiled
    panes:
      - shell_command: ["docker-compose up -d redis postgres"]
      - shell_command: ["kubectl get pods -w"]
      - shell_command: ["consul agent -dev"]
      - shell_command: ["jaeger-all-in-one"]

  - window_name: monitoring
    layout: even-horizontal
    panes:
      - shell_command: ["curl -s http://localhost:8080/health"]
      - shell_command: ["tail -f ~/logs/microservices.log"]

  - window_name: claude
    panes:
      - shell_command:
          - "cd ~/projects/microservices"
          - "claude"
```

### 환경별 설정 관리

개발/스테이징/프로덕션 환경별 설정입니다.

#### `~/.scripton/yesman/sessions/environment-specific.yaml`

```yaml
session_name: "{{ project_name }}-{{ environment }}"
start_directory: "{{ project_path }}"

# 환경별 변수 설정
environment_variables:
  development:
    DEBUG: "true"
    LOG_LEVEL: "debug"
    API_URL: "http://localhost:3000"
  
  staging:
    DEBUG: "false"
    LOG_LEVEL: "info"
    API_URL: "https://api-staging.example.com"
  
  production:
    DEBUG: "false"
    LOG_LEVEL: "warning"
    API_URL: "https://api.example.com"

windows:
  - window_name: application
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "export DEBUG={{ environment_variables[environment].DEBUG }}"
          - "export LOG_LEVEL={{ environment_variables[environment].LOG_LEVEL }}"
          - "export API_URL={{ environment_variables[environment].API_URL }}"
          - "npm run start:{{ environment }}"

  - window_name: monitoring
    panes:
      - shell_command:
          - "watch 'curl -s {{ environment_variables[environment].API_URL }}/health | jq'"

  - window_name: logs
    panes:
      - shell_command:
          - "tail -f ~/logs/{{ project_name }}-{{ environment }}.log"
```

## 👥 팀 협업 설정

### 팀 공유 설정

팀원들이 공유하는 표준 설정입니다.

#### `~/.scripton/yesman/yesman.yaml` (팀 표준)

```yaml
# 팀 표준 설정
logging:
  level: "INFO"
  directory: "~/tmp/logs/yesman"
  
  # 팀별 로그 형식 통일
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"

defaults:
  auto_response: true
  session_timeout: 600  # 10분
  
  # 팀 규칙
  claude_trust_level: "medium"
  auto_start_claude: false  # 수동 시작 선호

# 팀 공통 응답 패턴
response_patterns:
  trust_prompts:
    - pattern: "Allow.*access"
      response: "1"
      confidence: 0.9
  
  confirmation_prompts:
    - pattern: "Do you want to continue"
      response: "yes"
      confidence: 0.8

# 성능 설정 (팀 표준)
performance:
  cache_ttl: 300  # 5분
  max_sessions: 10
  optimization_level: "medium"

# 보안 설정
security:
  sensitive_patterns:
    - "password"
    - "api_key"
    - "secret"
    - "token"
  
  log_filtering: true
```

### 역할별 설정

팀 내 역할에 따른 전용 설정입니다.

#### 프론트엔드 개발자용

```yaml
# ~/.scripton/yesman/roles/frontend.yaml
session_name: "{{ project_name }}-frontend"
start_directory: "{{ project_path }}/frontend"

windows:
  - window_name: development
    layout: main-vertical
    options:
      main-pane-width: 70%
    panes:
      - shell_command:
          - "cd {{ project_path }}/frontend"
          - "npm run dev"
      - shell_command:
          - "cd {{ project_path }}/frontend"
          - "npm run test:watch"

  - window_name: design-system
    panes:
      - shell_command:
          - "cd {{ project_path }}/frontend"
          - "npm run storybook"

  - window_name: browser-testing
    layout: even-horizontal
    panes:
      - shell_command:
          - "cd {{ project_path }}/frontend"
          - "npm run cypress:open"
      - shell_command:
          - "cd {{ project_path }}/frontend"
          - "npm run lighthouse"

  - window_name: claude
    panes:
      - shell_command:
          - "cd {{ project_path }}/frontend"
          - "claude"
```

#### 백엔드 개발자용

```yaml
# ~/.scripton/yesman/roles/backend.yaml
session_name: "{{ project_name }}-backend"
start_directory: "{{ project_path }}/backend"

windows:
  - window_name: api-server
    panes:
      - shell_command:
          - "cd {{ project_path }}/backend"
          - "python manage.py runserver"

  - window_name: database
    layout: even-horizontal
    panes:
      - shell_command:
          - "cd {{ project_path }}/backend"
          - "python manage.py dbshell"
      - shell_command:
          - "cd {{ project_path }}/backend"
          - "redis-cli"

  - window_name: testing
    layout: main-vertical
    panes:
      - shell_command:
          - "cd {{ project_path }}/backend"
          - "python -m pytest -xvs"
      - shell_command:
          - "cd {{ project_path }}/backend"
          - "coverage run -m pytest && coverage report"

  - window_name: monitoring
    layout: tiled
    panes:
      - shell_command: ["htop"]
      - shell_command: ["tail -f ~/logs/django.log"]
      - shell_command: ["watch 'docker ps'"]
      - shell_command: ["curl -s http://localhost:8000/health"]

  - window_name: claude
    panes:
      - shell_command:
          - "cd {{ project_path }}/backend"
          - "claude"
```

## 🔍 문제 해결 시나리오

### 네트워크 연결 문제

네트워크 이슈 발생 시 사용하는 진단 설정입니다.

#### `~/.scripton/yesman/troubleshooting/network-debug.yaml`

```yaml
session_name: network-debug
start_directory: "~"

windows:
  - window_name: connectivity
    layout: tiled
    panes:
      - shell_command: ["ping -c 5 google.com"]
      - shell_command: ["nslookup google.com"]
      - shell_command: ["traceroute google.com"]
      - shell_command: ["netstat -tuln"]

  - window_name: local-services
    layout: even-horizontal
    panes:
      - shell_command: ["ss -tlnp | grep :80"]
      - shell_command: ["curl -I http://localhost:8000"]

  - window_name: system-info
    panes:
      - shell_command: ["ip addr show"]
      - shell_command: ["route -n"]

  - window_name: monitoring
    panes:
      - shell_command: ["watch 'ss -s'"]
```

### 성능 디버깅

성능 이슈 분석을 위한 설정입니다.

#### `~/.scripton/yesman/troubleshooting/performance-debug.yaml`

```yaml
session_name: performance-debug
start_directory: "{{ project_path }}"

windows:
  - window_name: system-monitor
    layout: tiled
    panes:
      - shell_command: ["htop"]
      - shell_command: ["iotop"]
      - shell_command: ["watch 'free -h'"]
      - shell_command: ["watch 'df -h'"]

  - window_name: application-profiling
    layout: main-vertical
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "python -m cProfile -o profile.stats app.py"
      - shell_command:
          - "cd {{ project_path }}"
          - "py-spy top --pid $(pgrep python)"

  - window_name: network-analysis
    layout: even-horizontal
    panes:
      - shell_command: ["tcpdump -i any port 80"]
      - shell_command: ["watch 'ss -i'"]

  - window_name: logs-analysis
    panes:
      - shell_command:
          - "cd {{ project_path }}/logs"
          - "tail -f *.log | grep -E '(ERROR|WARN|slow)'"
```

### 개발 환경 복구

개발 환경이 깨진 경우 복구용 설정입니다.

#### `~/.scripton/yesman/troubleshooting/environment-recovery.yaml`

```yaml
session_name: env-recovery
start_directory: "{{ project_path }}"

windows:
  - window_name: git-status
    layout: main-vertical
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "git status"
          - "git log --oneline -10"
      - shell_command:
          - "cd {{ project_path }}"
          - "git stash list"
          - "git branch -a"

  - window_name: dependencies
    layout: even-horizontal
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "npm install"
          - "npm audit fix"
      - shell_command:
          - "cd {{ project_path }}"
          - "pip install -r requirements.txt"

  - window_name: cleanup
    layout: tiled
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "rm -rf node_modules package-lock.json"
          - "npm install"
      - shell_command:
          - "cd {{ project_path }}"
          - "docker system prune -f"
      - shell_command:
          - "cd {{ project_path }}"
          - "git clean -fd"
      - shell_command:
          - "cd {{ project_path }}"
          - "./scripts/reset_database.sh"

  - window_name: verification
    panes:
      - shell_command:
          - "cd {{ project_path }}"
          - "npm run test"
          - "npm run build"
```

## 📋 설정 템플릿 사용법

### 기본 사용법

```bash
# 기본 세션 생성
./yesman.py setup my-project

# 템플릿 기반 세션 생성
./yesman.py setup --template=django my-django-app

# 환경별 세션 생성
./yesman.py setup --template=environment-specific \
  --var environment=development \
  --var project_name=myapp \
  my-dev-session
```

### 변수 치환

템플릿에서 사용 가능한 변수들:

- `{{ project_name }}`: 프로젝트 이름
- `{{ project_path }}`: 프로젝트 경로
- `{{ environment }}`: 환경 (dev/staging/prod)
- `{{ user_name }}`: 사용자 이름
- `{{ timestamp }}`: 현재 시간

### 조건부 설정

```yaml
# 환경별 조건부 설정
{% if environment == "development" %}
debug_mode: true
log_level: "DEBUG"
{% else %}
debug_mode: false
log_level: "INFO"
{% endif %}

# 파일 존재 확인
{% if file_exists(project_path + "/docker-compose.yml") %}
- shell_command: ["docker-compose up -d"]
{% endif %}
```

______________________________________________________________________

**마지막 업데이트**: 2025-08-19\
**템플릿 버전**: v2.0\
**지원 형식**: YAML, Jinja2
