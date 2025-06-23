# Yesman Claude

Yesman Claude는 Claude CLI를 자동화하고 여러 프로젝트를 효율적으로 관리하는 도구입니다.

## 주요 기능

- **자동 응답 시스템**: Claude의 선택 프롬프트에 자동으로 응답하여 작업을 중단 없이 진행
- **프로젝트 세션 관리**: tmux를 활용한 멀티 프로젝트 세션 자동 생성 및 관리
- **유연한 설정 관리**: 글로벌/로컬 설정 파일을 통한 맞춤형 환경 구성
- **패턴 기반 자동화**: 사용자 정의 패턴을 통한 지능적인 자동 선택
- **로깅 시스템**: 모든 작업 내역을 추적 가능한 상세 로그 제공

## 설정 파일

### 글로벌 설정

글로벌 설정 파일은 다음 경로에 위치합니다:

```bash
$HOME/.yesman/yesman.yaml
$HOME/.yesman/projects.yaml
```

### 프로젝트 설정

프로젝트별 설정 파일은 프로젝트 디렉토리 내에 위치합니다:

```bash
$PROJ_DIR/.yesman/yesman.yaml
```

예시 설정:

```yaml
choise:
  yn: yes
  '123': 1
  '12': 1
```

## 설치 방법

```bash
# 저장소 클론
git clone https://github.com/yourusername/yesman-claude.git
cd yesman-claude

# 개발 모드로 설치
pip install -e .

# 또는 requirements.txt 사용
pip install -r requirements.txt
```

## 사용 방법

### 프로젝트 세션 실행

```bash
# 사용 가능한 세션 목록 보기
yesman claude

# 특정 세션 실행
yesman claude homepage

# 세션 목록만 보기
yesman list
```

### 자동 응답 설정

`yesman.yaml`에서 자동 응답 패턴을 설정합니다:

```yaml
choise:
  yn: yes     # yes/no 선택 시 자동으로 yes 선택
  '123': 1    # 1,2,3 선택 시 자동으로 1 선택
  '12': 1     # 1,2 선택 시 자동으로 1 선택
```

## 프로젝트 예시

`projects.yaml` 파일을 통해 다양한 프로젝트 세션을 정의할 수 있습니다:

```yaml
sessions:
  homepage:
    - path: ~/workspace/homepage-backend
      name: homepage-backend
    - path: ~/workspace/homepage-frontend
      name: homepage-frontend
  shoppingmall:
    - path: ~/workspace/shoppingmall-backend
      name: shoppingmall-backend
    - path: ~/workspace/shoppingmall-frontend
      name: shoppingmall-frontend
    - path: ~/workspace/shoppingmall-crawler
      name: shoppingmall-crawler
```

이 설정에 따라 tmux 세션이 생성되며, 각 프로젝트에 맞는 환경이 자동으로 구성됩니다.

## 패턴 시스템

Yesman은 Claude의 출력을 모니터링하여 특정 패턴이 감지되면 자동으로 응답합니다.

### 패턴 디렉토리 구조

```
~/.yesman/pattern/
├── yn/          # yes/no 선택 패턴
├── 123/         # 1,2,3 선택 패턴
└── 12/          # 1,2 선택 패턴
```

각 디렉토리에 `.txt` 파일로 패턴을 추가할 수 있습니다:

```bash
# 예시: yn 패턴 추가
echo "Do you want to make this edit to" > ~/.yesman/pattern/yn/edit_confirm.txt
echo "Would you like to continue?" > ~/.yesman/pattern/yn/continue.txt
```

## 로깅

모든 작업은 로그 파일에 기록됩니다:

```yaml
log_level: debug              # 로그 레벨 (debug, info, warning, error)
log_path: ~/tmp/logs/yesman/  # 로그 저장 경로
```

## 요구사항

- Python 3.8+
- tmux
- Claude CLI (`claude` 명령어)

## 문제 해결

- **tmux 세션이 생성되지 않는 경우**: tmux가 설치되어 있는지 확인하세요
- **Claude 명령이 실행되지 않는 경우**: Claude CLI가 설치되어 있고 PATH에 등록되어 있는지 확인하세요
- **패턴이 매칭되지 않는 경우**: 패턴 파일이 올바른 위치에 있고 정확한 텍스트를 포함하는지 확인하세요
