# Task 4.2: 대시보드 런처 구현

**예상 시간**: 2.5시간  
**선행 조건**: Task 4.1 시작  
**우선순위**: 높음

## 목표
최적의 대시보드 인터페이스를 감지하고 실행하는 런처를 구현한다.

## 작업 내용

### 1. DashboardLauncher 클래스
**파일**: `libs/dashboard/dashboard_launcher.py`

주요 메서드:
- `detect_best_interface()`: 최적 인터페이스 자동 감지
- `get_available_interfaces()`: 사용 가능한 인터페이스 목록
- `check_system_requirements()`: 시스템 요구사항 확인
- `install_dependencies()`: 의존성 설치

### 2. 환경 감지 로직
```python
def _is_gui_available(self) -> bool:
    # macOS, Windows, Linux GUI 확인

def _is_ssh_session(self) -> bool:
    # SSH 환경 확인

def _is_tauri_available(self) -> bool:
    # Tauri 앱 설치 여부
```

### 3. 인터페이스 정보 관리
```python
def get_interface_info(self, interface: str) -> Dict[str, Any]:
    return {
        "name": "Terminal UI",
        "description": "...",
        "requirements": [...],
        "available": True,
        "reason": None
    }
```

### 4. 의존성 확인
- Python 패키지 확인
- 시스템 명령어 확인
- 버전 호환성 체크

### 5. 의존성 자동 설치
```python
def install_dependencies(self, interface: str) -> bool:
    if interface == "web":
        subprocess.run([sys.executable, "-m", "pip", "install", ...])
```

## 완료 기준
- [ ] DashboardLauncher 클래스 구현
- [ ] 환경 감지 메서드 구현
- [ ] 인터페이스 정보 시스템
- [ ] 의존성 확인 및 설치
- [ ] 플랫폼별 테스트

## 테스트
```python
launcher = DashboardLauncher()

# 자동 감지 테스트
best = launcher.detect_best_interface()
print(f"Best interface: {best}")

# 시스템 요구사항
reqs = launcher.check_system_requirements()
for req, status in reqs.items():
    print(f"{req}: {'✓' if status else '✗'}")
```

## 주의사항
- 플랫폼별 차이 처리
- 권한 문제 고려
- 사용자 피드백 제공