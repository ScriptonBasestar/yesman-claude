# Task 3.3: TUI 렌더러 구현

**예상 시간**: 3시간  
**선행 조건**: Task 3.1, 3.2 완료  
**우선순위**: 높음

## 목표
Rich 라이브러리를 사용하는 TUI 렌더러를 구현한다.

## 작업 내용

### 1. TUIRenderer 클래스
**파일**: `libs/dashboard/renderers/tui_renderer.py`

```python
class TUIRenderer(BaseRenderer):
    def __init__(self, console: Optional[Console] = None):
        super().__init__(RenderFormat.TUI)
        self.console = console or Console()
```

### 2. 위젯 렌더링 메서드
구현할 메서드:
- `_render_session_browser()`: 테이블/트리/카드 뷰
- `_render_health_meter()`: 프로그레스 바와 패널
- `_render_activity_heatmap()`: ASCII 히트맵
- `_render_progress_tracker()`: 프로그레스 바
- `_render_log_viewer()`: 로그 패널

### 3. Rich 컴포넌트 활용
- `Table`: 세션 목록
- `Tree`: 계층 구조
- `Panel`: 컨테이너
- `Progress`: 진행률
- `Columns`: 그리드 레이아웃

### 4. 뷰 모드별 렌더링
SessionBrowser의 경우:
- `_render_session_table()`: 테이블 뷰
- `_render_session_tree()`: 트리 뷰
- `_render_session_cards()`: 카드 뷰

### 5. 스타일링 및 색상
- 점수별 색상 적용
- 테마 색상 사용
- 아이콘 추가 (이모지)

## 완료 기준
- [ ] TUIRenderer 클래스 구현
- [ ] 모든 위젯 타입 렌더링
- [ ] Rich 컴포넌트 적절히 활용
- [ ] 색상 및 스타일 적용
- [ ] 테스트 코드 작성

## 테스트
```python
from rich.console import Console
from libs.dashboard.renderers.tui_renderer import TUIRenderer

console = Console()
renderer = TUIRenderer(console)

# 세션 렌더링 테스트
result = renderer.render_widget(
    WidgetType.SESSION_BROWSER,
    {"sessions": [...]},
    {"view_mode": "table"}
)
console.print(result)
```

## 주의사항
- Rich 버전 호환성
- 터미널 크기 고려
- 색상 깨짐 방지