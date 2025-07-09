# Task 3.1: 기본 렌더러 인터페이스 구현

**예상 시간**: 2시간  
**선행 조건**: Phase 2 완료  
**우선순위**: 높음

## 목표
모든 렌더러가 상속받을 기본 렌더러 인터페이스를 구현한다.

## 작업 내용

### 1. BaseRenderer 추상 클래스
**파일**: `libs/dashboard/renderers/base_renderer.py`

구현 내용:
- 추상 메서드 정의
- 공통 유틸리티 메서드
- 테마/설정 관리

### 2. Enum 정의
```python
class RenderFormat(Enum):
    TUI = "tui"
    WEB = "web"
    TAURI = "tauri"
    JSON = "json"
    MARKDOWN = "markdown"

class WidgetType(Enum):
    SESSION_BROWSER = "session_browser"
    HEALTH_METER = "health_meter"
    # ...
```

### 3. 추상 메서드
- `render_widget()`: 위젯 렌더링
- `render_layout()`: 레이아웃 렌더링
- `render_container()`: 컨테이너 렌더링

### 4. 공통 유틸리티
- `format_number()`: 숫자 포맷팅
- `format_date()`: 날짜 포맷팅
- `format_percentage()`: 퍼센트 포맷팅
- `get_color()`: 테마 색상 조회

### 5. RendererRegistry 구현
- 렌더러 등록/조회
- 전역 레지스트리 인스턴스

## 완료 기준
- [ ] BaseRenderer 클래스 구현
- [ ] Enum 타입 정의
- [ ] 추상 메서드 정의
- [ ] 유틸리티 메서드 구현
- [ ] RendererRegistry 구현

## 테스트
```python
from libs.dashboard.renderers.base_renderer import BaseRenderer, RenderFormat

# 추상 클래스이므로 직접 인스턴스화 불가
# 상속 테스트
class TestRenderer(BaseRenderer):
    def render_widget(self, widget_type, data, options=None):
        return "test"
```

## 주의사항
- Python 3.8+ 타입 힌트 사용
- 확장성 고려한 설계
- 문서화 철저히