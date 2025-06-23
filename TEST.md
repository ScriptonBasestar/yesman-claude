# TEST.md

## 1. 리포지토리 클론 및 이동
```bash
git clone https://github.com/yourusername/yesman-claude.git
cd yesman-claude
```

## 2. 가상환경 생성 및 활성화
- Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
- Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. 의존성 설치
```bash
pip install --upgrade pip setuptools wheel
pip install -e .
```

## 4. 설정 파일 준비
- 글로벌 설정: `~/.yesman/yesman.yaml`
- 프로젝트별 설정: `<프로젝트 경로>/.yesman/yesman.yaml`

### 예시 글로벌 설정 (`~/.yesman/yesman.yaml`)
```yaml
mode: merge
auto_select:
  123: 1
  12: 1
  yn: yes
log_level: debug
log_path: ~/tmp/logs/yesman/
```

### 예시 프로젝트 설정 (`./.yesman/yesman.yaml`)
```yaml
mode: local
auto_select_on_pattern: false  # 로컬 설정이 글로벌을 덮음
```

## 5. 프로젝트 세션 정의
- `~/.yesman/projects.yaml` 생성
```yaml
sessions:
  homepage:
    - path: ~/workspace/homepage-backend
      name: homepage-backend
    - path: ~/workspace/homepage-frontend
      name: homepage-frontend
```

## 6. tmux 세션 확인
```bash
yesman show
```

## 7. tmux 세션 생성 및 접속
```bash
yesman session homepage
tmux ls
```

## 8. auto_claude 테스트
1) 패턴 파일 준비: `~/.yesman/pattern/{yn,12,123}/*.txt`
2) 매칭될 텍스트를 출력하는 스크립트 실행 후, 1초 대기 시 자동 입력 동작 확인
```bash
python auto_claude.py
```

---
*위 단계를 따라 로컬에서 Yesman Claude의 주요 기능을 테스트할 수 있습니다.* 