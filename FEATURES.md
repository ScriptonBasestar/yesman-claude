# FEATURES

생각하고 있는 기능 정리. 여기에 따라서 TODO생성

## 설정파일

### 글로벌 설정

```bash
$HOME/.yesman/yesman.yaml
$HOME/.yesman/projects.yaml
```

### 프로젝트 설정

```bash
$PROJ_DIR/.yesman/yesman.yaml
```

```yaml
choise:
  yn: yes
  '123': 1
  '12': 1
```

## 실행

```bash
yesman claude
```

이렇게 실행시키면 projects의 설정에 따라 프로젝트 로딩

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

이 설정에 따라 tmux세션을 생성한다.

homepage세션에서 2개 리포지터리니까 세로를 2분할해서 사용한다.
그리고 윗쪽을 좌우로 분할해서
왼쪽에는 homepage-backend 경로에서 claude를 실행 오른쪽에는 터미널 실행
왼쪽에는 homepage-frontend 경로에서 claude를 실행 오른쪽에는 터미널 실행
