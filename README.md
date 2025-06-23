# Yesman Claude

Yesman Claude는 다양한 프로젝트 설정을 관리하고 자동화된 세션을 생성하는 도구입니다.

## 기능

- **설정 파일 관리**: 글로벌 및 프로젝트별 설정 파일을 통해 다양한 환경을 관리할 수 있습니다.
- **자동 세션 생성**: 프로젝트 설정에 따라 tmux 세션을 자동으로 생성하여 작업 환경을 구성합니다.
- **반복 사용 프롬프트 공유**: 자주 사용하는 프롬프트를 쉽게 공유하고 관리할 수 있습니다.

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

## 실행 방법

Yesman Claude를 실행하려면 다음 명령어를 사용하세요:

```bash
yesman claude
```

이 명령어는 프로젝트 설정에 따라 자동으로 프로젝트를 로딩합니다.

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
