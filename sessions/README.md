# Sessions Directory Structure

이 디렉토리는 개별 세션 설정 파일들을 포함합니다. `projects.yaml` 대신 이 구조를 사용하면 더 유연하고 관리하기 쉬운 설정을 만들 수 있습니다.

## 왜 sessions/*.yaml을 사용하나요?

### 1. **모듈화된 관리**
- 각 프로젝트/세션을 독립적인 파일로 관리
- 파일 단위로 추가/삭제가 쉬움
- 충돌 없이 여러 사람이 동시에 작업 가능

### 2. **선택적 버전 관리**
```bash
# 특정 세션만 git에 추가
git add sessions/myproject.yaml

# 개인 세션은 제외
echo "sessions/personal-*.yaml" >> .gitignore
```

### 3. **동적 세션 관리**
```bash
# 새 세션 추가
cp sessions/_template.yaml sessions/new-project.yaml

# 임시 세션 생성
echo "session_name: temp-debug" > sessions/temp-debug.yaml

# 세션 제거
rm sessions/old-project.yaml
```

### 4. **조직화된 구조**
```
sessions/
├── _template.yaml           # 템플릿 (언더스코어로 시작하면 무시됨)
├── development/            # 개발 관련 세션들
│   ├── frontend.yaml
│   ├── backend.yaml
│   └── fullstack.yaml
├── production/             # 프로덕션 모니터링
│   ├── monitoring.yaml
│   └── debugging.yaml
├── personal/              # 개인 프로젝트
│   ├── blog.yaml
│   └── dotfiles.yaml
└── clients/               # 클라이언트별 세션
    ├── client-a.yaml
    └── client-b.yaml
```

## 사용 방법

### 1. 모든 세션 확인
```bash
yesman ls
```

### 2. 특정 세션 시작
```bash
yesman up dripter
yesman up familybook
```

### 3. 여러 세션 동시 시작
```bash
yesman up dripter familybook yesman-claude
```

### 4. 디렉토리별 세션 시작
```bash
# development 디렉토리의 모든 세션
yesman up development/*

# 특정 패턴의 세션들
yesman up client-*
```

## 세션 파일 구조

각 세션 파일은 다음과 같은 구조를 가집니다:

```yaml
# 필수 필드
session_name: "my-session"    # tmux 세션 이름

# 선택 필드
start_directory: "~/projects/my-project"
template_name: "default"      # 템플릿 참조
environment:                  # 환경 변수
  KEY: "value"
before_script: |              # 세션 시작 전 실행
  echo "Setting up..."
windows:                      # 윈도우와 페인 설정
  - window_name: "main"
    panes:
      - claude
```

## 마이그레이션 가이드

### projects.yaml에서 마이그레이션

1. **수동 마이그레이션**
   ```bash
   # 기존 projects.yaml의 각 세션을 개별 파일로 분리
   # sessions: 섹션의 각 항목을 sessions/[name].yaml로 저장
   ```

2. **자동 마이그레이션** (스크립트 사용)
   ```bash
   # examples/sessions-only/migrate-projects.sh 실행
   ./examples/sessions-only/migrate-projects.sh
   ```

## 팁과 모범 사례

### 1. 네이밍 컨벤션
- 프로젝트명과 세션 파일명을 일치시키기
- 환경별 접미사 사용: `myapp-dev.yaml`, `myapp-prod.yaml`
- 카테고리별 접두사 사용: `client-abc.yaml`, `personal-blog.yaml`

### 2. 템플릿 활용
```yaml
# _template.yaml을 복사해서 시작
cp sessions/_template.yaml sessions/new-project.yaml
```

### 3. 환경별 분리
```yaml
# sessions/myapp-dev.yaml
session_name: "myapp-dev"
environment:
  API_URL: "http://localhost:8000"

# sessions/myapp-prod.yaml  
session_name: "myapp-prod"
environment:
  API_URL: "https://api.myapp.com"
```

### 4. 공유와 협업
```bash
# 팀 공통 세션
git add sessions/team-*.yaml

# 개인 세션은 gitignore
echo "sessions/personal-*.yaml" >> .gitignore
echo "sessions/*-local.yaml" >> .gitignore
```

## 문제 해결

### 세션이 보이지 않음
```bash
# 파일 권한 확인
ls -la sessions/

# 파일 형식 검증
yesman validate sessions/my-session.yaml
```

### 중복된 세션 이름
- 파일명이 아닌 `session_name` 필드가 실제 세션 이름
- 같은 `session_name`을 가진 파일이 여러 개면 첫 번째 것만 사용됨

### 디버깅
```bash
# 디버그 모드로 실행
YESMAN_LOG_LEVEL=debug yesman up my-session

# 로드된 세션 확인
yesman config --show-sessions
```