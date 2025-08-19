# Getting Started with Yesman-Claude

Yesman-Claude 시작 가이드 - 설치부터 기본 사용법까지 모든 것을 다룹니다.

## 📚 목차

1. [빠른 시작](#%EB%B9%A0%EB%A5%B8-%EC%8B%9C%EC%9E%91)
1. [대시보드 인터페이스](#%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C-%EC%9D%B8%ED%84%B0%ED%8E%98%EC%9D%B4%EC%8A%A4)
1. [세션 관리](#%EC%84%B8%EC%85%98-%EA%B4%80%EB%A6%AC)
1. [키보드 단축키](#%ED%82%A4%EB%B3%B4%EB%93%9C-%EB%8B%A8%EC%B6%95%ED%82%A4)
1. [테마 커스터마이징](#%ED%85%8C%EB%A7%88-%EC%BB%A4%EC%8A%A4%ED%84%B0%EB%A7%88%EC%9D%B4%EC%A7%95)
1. [AI 학습 시스템](#ai-%ED%95%99%EC%8A%B5-%EC%8B%9C%EC%8A%A4%ED%85%9C)
1. [성능 최적화](#%EC%84%B1%EB%8A%A5-%EC%B5%9C%EC%A0%81%ED%99%94)
1. [문제 해결](#%EB%AC%B8%EC%A0%9C-%ED%95%B4%EA%B2%B0)

## 🚀 빠른 시작

### 설치

1. **저장소 클론**:

   ```bash
   git clone <repository-url>
   cd yesman-agent
   ```

1. **의존성 설치**:

   ```bash
   # 개발 설치 (권장)
   make dev-install

   # 또는 uv 사용 (가장 빠름)
   uv sync
   ```

1. **설정 생성**:

   ```bash
   mkdir -p ~/.scripton/yesman
   cp examples/global-yesman/* ~/.scripton/yesman/
   ```

1. **설치 테스트**:

   ```bash
   uv run ./yesman.py --help
   ```

### 첫 번째 단계

1. **사용 가능한 템플릿 확인**:

   ```bash
   uv run ./yesman.py ls
   ```

1. **첫 번째 세션 생성**:

   ```bash
   uv run ./yesman.py setup
   ```

1. **대시보드 열기**:

   ```bash
   uv run ./yesman.py dashboard run
   ```

## 📊 대시보드 인터페이스

Yesman-Claude는 세 가지 대시보드 인터페이스를 제공하며, 각각 다른 사용 사례에 최적화되어 있습니다.

### 터미널 사용자 인터페이스 (TUI)

TUI는 실시간 업데이트와 완전한 키보드 탐색 기능을 갖춘 풍부한 터미널 기반 대시보드를 제공합니다.

**TUI 실행**:

```bash
uv run ./yesman.py dashboard run --interface tui
```

**기능**:

- 실시간 세션 모니터링
- 활동 히트맵
- 프로젝트 건강 지표
- 키보드 전용 탐색
- 낮은 리소스 사용량
- SSH 친화적

**적합한 용도**: SSH 세션, 헤드리스 서버, 최소 환경

### 웹 인터페이스

웹 인터페이스는 REST API 백엔드와 함께 브라우저 기반 대시보드를 제공합니다.

**웹 인터페이스 실행**:

```bash
# 기본 포트 (8000)
uv run ./yesman.py dash web

# 커스텀 포트
uv run ./yesman.py dash web --port 3000

# 브라우저 자동 열기
uv run ./yesman.py dash web --open
```

**기능**:

- 크로스 플랫폼 호환성
- 원격 접속 기능
- 풍부한 인터랙티브 위젯
- WebSocket 실시간 업데이트
- 모바일 반응형 디자인
- 팀 협업

**적합한 용도**: 원격 모니터링, 팀 환경, 모바일 접속

### 데스크톱 애플리케이션 (Tauri)

데스크톱 애플리케이션은 시스템 통합과 함께 네이티브 경험을 제공합니다.

**데스크톱 앱 실행**:

```bash
# 개발 모드
uv run ./yesman.py dash tauri --dev

# 프로덕션 모드
uv run ./yesman.py dash tauri
```

**기능**:

- 네이티브 성능
- 시스템 트레이 통합
- 네이티브 알림
- 파일 시스템 접근
- 오프라인 기능
- OS별 특화 기능

**적합한 용도**: 일일 개발, 최고의 UX, 데스크톱 통합

## 🎮 세션 관리

### 세션 생성

세션은 `~/.scripton/yesman/sessions/` 하위의 개별 YAML 파일로 정의됩니다:

```yaml
sessions:
  my_project:
    template_name: django
    override:
      session_name: my-django-app
      start_directory: ~/projects/my-app
      environment:
        DEBUG: "1"
        DATABASE_URL: "sqlite:///db.sqlite3"
```

**명령어**:

```bash
# 모든 세션 생성
uv run ./yesman.py up

# 특정 세션 생성
uv run ./yesman.py up my_project

# 실행 중인 세션 표시
uv run ./yesman.py show

# 인터랙티브 세션 브라우저
uv run ./yesman.py browse
```

### 세션 템플릿

템플릿은 `~/.scripton/yesman/templates/`에 저장된 재사용 가능한 세션 구성입니다.

**템플릿 예시** (`~/.scripton/yesman/templates/django.yaml`):

```yaml
session_name: "{{ session_name }}"
start_directory: "{{ start_directory }}"
before_script: uv sync
windows:
  - window_name: django server
    layout: even-horizontal
    panes:
      - claude --dangerously-skip-permissions
      - uv run ./manage.py runserver
      - htop
```

**스마트 템플릿**은 조건부 명령을 지원합니다:

```yaml
panes:
  - shell_command: |
      if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
      fi
      npm run dev
```

### 세션 생명주기

```bash
# 세션 생성
uv run ./yesman.py up

# 세션 모니터링
uv run ./yesman.py status

# 특정 세션 접속
uv run ./yesman.py enter my_project

# 세션 해제
uv run ./yesman.py down
```

## ⌨️ 키보드 단축키

### TUI 대시보드 단축키

| 키          | 동작              | 컨텍스트 |
| ----------- | ----------------- | -------- |
| `q`         | 애플리케이션 종료 | 전역     |
| `h`         | 도움말 표시       | 전역     |
| `r`         | 데이터 새로고침   | 전역     |
| `d`         | 다크 모드 토글    | 전역     |
| `1-5`       | 뷰 전환           | 전역     |
| `↑/↓`       | 항목 탐색         | 리스트   |
| `←/→`       | 패널 탐색         | 수평     |
| `Enter`     | 선택/활성화       | 리스트   |
| `Tab`       | 다음 포커스       | 폼       |
| `Shift+Tab` | 이전 포커스       | 폼       |

### 탐색 컨텍스트

다양한 컨텍스트에서 특화된 키보드 단축키를 제공합니다:

**대시보드 컨텍스트**:

- `s` - 세션 브라우저
- `h` - 건강 모니터
- `a` - 활동 추적기
- `l` - 로그 뷰어
- `p` - 성능 모니터

**세션 브라우저 컨텍스트**:

- `c` - 세션 생성
- `d` - 세션 삭제
- `r` - 세션 재시작
- `e` - 세션 접속

**건강 모니터 컨텍스트**:

- `t` - 테스트 실행
- `b` - 프로젝트 빌드
- `g` - Git 상태

### 커스텀 단축키

커스텀 키보드 단축키를 등록할 수 있습니다:

```python
from libs.dashboard import get_keyboard_manager

keyboard_manager = get_keyboard_manager()

def custom_action():
    print("Custom action triggered!")

keyboard_manager.register_action("custom", custom_action)
keyboard_manager.register_binding("c", [KeyModifier.CTRL], "custom", "Custom action")
```

## 🎨 테마 커스터마이징

### 내장 테마

Yesman-Claude는 여러 내장 테마를 포함합니다:

- **Default Light**: 깔끔한 라이트 테마
- **Default Dark**: 어두운 환경에 최적화된 다크 테마
- **High Contrast**: 접근성 중심 테마
- **Cyberpunk**: 미래적 네온 테마
- **Ocean**: 파란색 기반 차분한 테마
- **Forest**: 녹색 자연 영감 테마

### 테마 전환

**명령줄 통해**:

```bash
# 사용 가능한 테마 목록
uv run ./yesman.py dash --theme-list

# 특정 테마 사용
uv run ./yesman.py dash tui --theme dark

# 시스템 테마 감지 설정
uv run ./yesman.py dash tui --theme auto
```

**API 통해**:

```python
from libs.dashboard import get_theme_manager

theme_manager = get_theme_manager()

# 다크 테마로 전환
theme_manager.set_mode(ThemeMode.DARK)

# 모든 테마 목록
themes = theme_manager.get_all_themes()
```

### 커스텀 테마 생성

커스텀 테마 파일을 생성할 수 있습니다:

```python
# docs/examples/custom-theme.py
from libs.dashboard.theme_system import Theme, ThemeMode, ColorPalette, Typography, Spacing

custom_theme = Theme(
    name="My Custom Theme",
    mode=ThemeMode.CUSTOM,
    colors=ColorPalette(
        primary="#ff6b6b",
        secondary="#4ecdc4", 
        background="#2c3e50",
        surface="#34495e",
        text="#ecf0f1",
        text_secondary="#bdc3c7"
    ),
    typography=Typography(
        primary_font="JetBrains Mono",
        secondary_font="Inter",
        size_small="12px",
        size_normal="14px",
        size_large="16px"
    ),
    spacing=Spacing(
        small="4px",
        medium="8px", 
        large="16px",
        extra_large="24px"
    )
)

# 테마 저장
from libs.dashboard import get_theme_manager
theme_manager = get_theme_manager()
theme_manager.save_theme("my_custom", custom_theme)
```

## 🤖 AI 학습 시스템

AI 학습 시스템은 사용자 행동 패턴을 학습하여 시간이 지남에 따라 응답 정확도를 자동으로 향상시킵니다.

### 설정

```bash
# 현재 AI 상태 확인
uv run ./yesman.py ai status

# 신뢰도 임계값 설정
uv run ./yesman.py ai config --threshold 0.8

# 학습 활성화/비활성화
uv run ./yesman.py ai config --learning

# 자동 응답 활성화/비활성화
uv run ./yesman.py ai config --auto-response
```

### 학습 분석

```bash
# 응답 히스토리 확인
uv run ./yesman.py ai history

# 응답 예측 테스트
uv run ./yesman.py ai predict "Continue with the operation?"

# 학습 데이터 내보내기
uv run ./yesman.py ai export --format json
```

### 응답 패턴

AI 시스템은 다양한 프롬프트 패턴을 인식합니다:

- **Yes/No 프롬프트**: 이진 확인 대화상자
- **번호 선택**: 다중 선택 메뉴 (1, 2, 3...)
- **이진 선택**: 간단한 A/B 결정
- **신뢰 프롬프트**: Claude Code 권한 요청

### 수동 훈련

```bash
# 훈련 데이터 추가
uv run ./yesman.py ai train --pattern "Continue?" --response "y"

# 훈련 데이터 가져오기
uv run ./yesman.py ai import --file training_data.json

# 학습 데이터 리셋
uv run ./yesman.py ai reset --confirm
```

## ⚡ 성능 최적화

### 최적화 레벨

성능 최적화기는 5가지 최적화 레벨을 제공합니다:

1. **None**: 최적화 없음
1. **Low**: 기본 최적화
1. **Medium**: 균형잡힌 성능/기능
1. **High**: 적극적 최적화
1. **Aggressive**: 최대 성능

### 설정

```bash
# 성능 상태 확인
uv run ./yesman.py status --performance

# 최적화 레벨 설정
uv run ./yesman.py config --optimization medium

# 성능 모니터링 활성화
uv run ./yesman.py monitor --performance
```

### 수동 최적화

```python
from libs.dashboard import get_performance_optimizer

optimizer = get_performance_optimizer()

# 최적화 레벨 설정
optimizer.set_optimization_level(OptimizationLevel.HIGH)

# 성능 보고서 확인
report = optimizer.get_performance_report()

# 모니터링 시작
optimizer.start_monitoring()
```

### 성능 지표

주요 성능 지표를 모니터링합니다:

- **CPU 사용량**: 프로세스 CPU 활용도
- **메모리 사용량**: RAM 소비량
- **렌더 시간**: 대시보드 렌더 성능
- **응답 시간**: 시스템 반응성
- **캐시 적중률**: 캐싱 효율성

## 🔧 문제 해결

### 일반적인 문제

#### 대시보드가 시작되지 않음

**문제**: 대시보드 인터페이스 실행 실패

**해결책**:

1. 시스템 요구사항 확인:

   ```bash
   uv run ./yesman.py dash --check-requirements
   ```

1. 누락된 의존성 설치:

   ```bash
   uv run ./yesman.py dash --install-deps
   ```

1. 대체 인터페이스 시도:

   ```bash
   uv run ./yesman.py dash tui  # 항상 작동함
   ```

#### 성능 저하

**문제**: 대시보드가 느리거나 반응하지 않음

**해결책**:

1. 성능 최적화 활성화:

   ```bash
   uv run ./yesman.py config --optimization high
   ```

1. 업데이트 빈도 줄이기:

   ```bash
   uv run ./yesman.py dash --interval 2.0
   ```

1. 캐시 정리:

   ```bash
   uv run ./yesman.py cache --clear
   ```

#### 테마 문제

**문제**: 테마가 올바르게 적용되지 않음

**해결책**:

1. 기본 테마로 리셋:

   ```bash
   uv run ./yesman.py dash --theme default
   ```

1. 테마 캐시 정리:

   ```bash
   rm -rf ~/.scripton/yesman/cache/themes/
   ```

1. 테마 파일 문법 확인:

   ```bash
   uv run ./yesman.py theme --validate my_theme
   ```

#### AI 학습 문제

**문제**: AI 응답이 부정확함

**해결책**:

1. 학습 데이터 리셋:

   ```bash
   uv run ./yesman.py ai reset --confirm
   ```

1. 신뢰도 임계값 조정:

   ```bash
   uv run ./yesman.py ai config --threshold 0.9
   ```

1. 수동 훈련 데이터 추가:

   ```bash
   uv run ./yesman.py ai train --interactive
   ```

### 디버그 모드

문제 해결을 위해 디버그 로깅을 활성화할 수 있습니다:

```bash
# 디버그 모드 활성화
export YESMAN_DEBUG=1
uv run ./yesman.py dash tui

# 디버그 로그 확인
tail -f ~/.scripton/yesman/logs/debug.log
```

### 도움말

1. **내장 도움말**:

   ```bash
   uv run ./yesman.py --help
   uv run ./yesman.py dash --help
   ```

1. **상태 확인**:

   ```bash
   uv run ./yesman.py status --verbose
   ```

1. **이슈 신고**: 디버그 로그와 시스템 정보와 함께 이슈 생성

### 시스템 정보

버그 리포트를 위한 시스템 정보 수집:

```bash
# 시스템 진단
uv run ./yesman.py diagnose --full

# 설정 내보내기
uv run ./yesman.py config --export > config_backup.yaml
```

## 📖 추가 리소스

- [API 레퍼런스](../20-api/21-rest-api-reference.md)
- [설정 가이드](32-configuration.md)
- [예제 디렉토리](../../examples/)
- [템플릿 갤러리](33-templates.md)
- [기여 가이드](../../CONTRIBUTING.md)

______________________________________________________________________

더 고급 사용법과 API 문서는 [API Reference](../20-api/21-rest-api-reference.md)를 참조하세요.

## 📝 글로벌 설정

글로벌 설정 파일은 다음 경로에 위치합니다:

```bash
$HOME/.scripton/yesman/yesman.yaml
$HOME/.scripton/yesman/projects.yaml
```

파일 구조는 examples/ 참고하세요.
