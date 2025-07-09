# Task 4.3: 통합 TUI 대시보드 구현

**예상 시간**: 3시간  
**선행 조건**: Phase 3 완료  
**우선순위**: 높음

## 목표
Textual 프레임워크를 사용하여 통합 TUI 대시보드를 구현한다.

## 작업 내용

### 1. TUIDashboard 클래스
**파일**: `libs/dashboard/tui_dashboard.py`

Textual 앱 구조:
```python
class TUIDashboard(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Dark Mode"),
        ("r", "refresh", "Refresh"),
        ("1-4", "view_*", "Switch View")
    ]
```

### 2. UI 컴포넌트 구성
- Header: 시계, 타이틀
- Sidebar: 네비게이션 버튼
- Main Content: 위젯 영역
- Footer: 단축키 안내

### 3. DashboardWidget 클래스
```python
class DashboardWidget(Static):
    def __init__(self, widget_type: WidgetType):
        self.widget_type = widget_type
        self.renderer = TUIRenderer()
    
    async def update_data(self, data):
        pass
```

### 4. 뷰 전환 시스템
- Sessions 뷰
- Health 뷰
- Activity 뷰
- Logs 뷰

### 5. 자동 새로고침
- 설정 가능한 간격
- 백그라운드 태스크
- 선택적 새로고침

## 완료 기준
- [ ] TUIDashboard 클래스 구현
- [ ] 4개 뷰 모두 작동
- [ ] 키보드 단축키 구현
- [ ] 자동 새로고침 기능
- [ ] 설정 화면 구현

## 테스트
```python
# TUI 대시보드 실행
from libs.dashboard.tui_dashboard import TUIDashboard

app = TUIDashboard()
app.run()

# 키보드 단축키 테스트
# q: 종료
# 1-4: 뷰 전환
# r: 새로고침
```

## 주의사항
- Textual 버전 호환성
- 터미널 크기 대응
- 비동기 처리 주의