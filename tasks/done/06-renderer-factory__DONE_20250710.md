# Task 3.6: 렌더러 팩토리 및 통합

**예상 시간**: 2시간  
**선행 조건**: Task 3.3-3.5 완료  
**우선순위**: 높음

## 목표
렌더러 생성과 관리를 위한 팩토리 패턴을 구현한다.

## 작업 내용

### 1. RendererFactory 클래스
**파일**: `libs/dashboard/renderers/renderer_factory.py`

```python
class RendererFactory:
    _renderer_classes = {
        RenderFormat.TUI: TUIRenderer,
        RenderFormat.WEB: WebRenderer,
        RenderFormat.TAURI: TauriRenderer
    }
    
    @classmethod
    def create(cls, format: RenderFormat, **kwargs):
        pass
```

### 2. 렌더러 등록 시스템
- `register_all()`: 모든 렌더러 등록
- 전역 레지스트리에 등록
- 초기화 시 자동 등록

### 3. 범용 렌더링 메서드
```python
@classmethod
def render_universal(cls, widget_type, data, format=None, options=None):
    if format:
        # 특정 포맷으로 렌더링
    else:
        # 모든 포맷으로 렌더링
```

### 4. 간편 함수
```python
def render_widget(widget_type, data, format, options=None):
    return RendererFactory.render_universal(...)

def render_all_formats(widget_type, data, options=None):
    return RendererFactory.render_universal(...)
```

### 5. 에러 처리
- 알 수 없는 포맷
- 렌더링 실패
- 적절한 예외 발생

## 완료 기준
- [ ] RendererFactory 클래스 구현
- [ ] 렌더러 자동 등록
- [ ] 범용 렌더링 메서드
- [ ] 간편 함수 구현
- [ ] 에러 처리 구현

## 테스트
```python
from libs.dashboard.renderers.renderer_factory import (
    RendererFactory, render_widget, render_all_formats
)

# 단일 포맷 렌더링
result = render_widget(
    "session_browser",
    {"sessions": []},
    RenderFormat.WEB
)

# 모든 포맷 렌더링
results = render_all_formats(
    "health_meter",
    {"overall_score": 85}
)
assert len(results) == 3  # TUI, WEB, TAURI
```

## 주의사항
- 싱글톤 패턴 고려
- 스레드 안전성
- 확장성 고려