# FEATURES

이 문서는 `yesman` 프로젝트에서 지원하거나 계획 중인 기능을 정리한 문서입니다. 여기에 기반해 TODO를 생성합니다.

---

## 설정파일

### 글로벌 설정

```bash
$HOME/.yesman/yesman.yaml
$HOME/.yesman/projects.yaml
```

```yaml
# yesman.yaml
log_level: debug
log_path: ~/tmp/logs/yesman/

choise:
  yn: yes
  '123': 1
  '12': 1
```

```yaml
# projects.yaml
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

### 프로젝트 설정

```bash
$PROJ_DIR/.yesman/yesman.yaml
```

```yaml
# yesman.yaml

log_level: debug
log_path: ~/tmp/logs/yesman/

mode: merge 

choise:
  yn: yes
  '123': 1
  '12': 1
```

#### 설정 병합 로직

```yaml
mode: merge  # (기본값) 글로벌 설정과 병합, 로컬 설정이 우선함
mode: local  # 로컬 설정만 사용, 누락된 값은 오류 발생
```

#### 선택 기본값 지정 예시

```yaml
choise:
  yn: yes
  '123': 1
  '12': 1
```

---

## 실행

```bash
yesman claude
```

- 실행 시 `projects.yaml`에 따라 프로젝트 세션 로딩

#### 예시 설정 (`projects.yaml`)

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

#### 세션 분할 구조

- `homepage` 세션은 2개 리포지터리 → 세로 2분할
- 각 리포지터리 영역에서 다시 좌우 분할
  - 왼쪽: 해당 경로에서 `claude` 실행
  - 오른쪽: 일반 터미널 실행

---

## 자동입력 시스템

### 자동입력 패턴 기반

- 선택지 출현 여부를 감지하기 위해 다음 디렉토리의 텍스트 패턴 사용:

```bash
$HOME/.yesman/pattern/
├── yn/       # yes/no 선택
├── 123/      # 1,2,3 선택
├── 12/       # 1,2 선택
```

- 각 디렉토리에 `.txt` 파일을 추가하여 특정 상황에 대응
- 예: `Do you want to make this edit to CLAUDE.md?` 텍스트가 등장하면 자동으로 `1` 입력

### 선택 타이밍 인식

- Claude code에서 출력이 **1초 이상 정지**하면 **선택 대기 상태**로 간주
- 이 시점에서 출력에 포함된 패턴을 확인하여 자동 입력 여부 판단

---

## 디버그 모드

```yaml
debug: true
```

- 내부적으로 어떤 패턴이 매칭되었는지, 어떤 입력이 자동 실행되었는지 로그로 출력

---

## 향후 추가 예정 기능 (WIP)

- 결과 판단을 LLM으로 처리
- Claude 외 다른 LLM 연동
- 자동입력 외에 후처리 자동화 스크립트 연동
- Claude 세션 대시보드 (진행 상태, 사용량 모니터링)
- GUI 기반 프로젝트/세션 선택기
- 선택지 입력을 사용자 설정 우선순위로 분기 처리
