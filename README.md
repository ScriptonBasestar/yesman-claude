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
