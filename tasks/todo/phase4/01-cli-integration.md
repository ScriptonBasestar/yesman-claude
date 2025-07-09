# Task 4.1: 통합 CLI 명령어 구현

**예상 시간**: 3시간  
**선행 조건**: Phase 3 완료  
**우선순위**: 높음

## 목표
3가지 대시보드 인터페이스를 통합 관리하는 CLI 명령어를 구현한다.

## 작업 내용

### 1. dashboard 명령어 업데이트
**파일**: `commands/dashboard.py` 수정

새로운 옵션:
- `--interface, -i`: 인터페이스 선택 (tui/web/tauri/auto)
- `--port, -p`: 웹 대시보드 포트
- `--theme, -t`: 테마 선택
- `--detach, -d`: 백그라운드 실행

### 2. 인터페이스별 실행 함수
```python
def launch_tui_dashboard(theme, dev):
    pass

def launch_web_dashboard(host, port, theme, dev, detach):
    pass

def launch_tauri_dashboard(theme, dev, detach):
    pass
```

### 3. 서브커맨드 추가
```python
@dashboard_group.command()
def list_interfaces():
    """사용 가능한 인터페이스 목록"""

@dashboard_group.command()
def build(interface):
    """프로덕션 빌드"""
```

### 4. 자동 인터페이스 감지
- GUI 환경 확인
- SSH 세션 확인
- 최적 인터페이스 선택

### 5. 에러 처리
- 의존성 누락
- 포트 충돌
- 권한 문제

## 완료 기준
- [ ] dashboard 명령어 수정
- [ ] 3가지 인터페이스 실행
- [ ] 자동 감지 기능
- [ ] 서브커맨드 구현
- [ ] 에러 처리 완료

## 테스트
```bash
# 자동 선택
yesman dashboard

# 특정 인터페이스
yesman dashboard -i web
yesman dashboard -i tui
yesman dashboard -i tauri

# 옵션 테스트
yesman dashboard -i web -p 8080 -d
```

## 주의사항
- 기존 명령어 호환성 유지
- 명확한 도움말 제공
- 플랫폼별 차이 고려