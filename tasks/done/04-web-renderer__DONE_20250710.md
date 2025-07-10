# Task 3.4: Web 렌더러 구현

**예상 시간**: 3시간  
**선행 조건**: Task 3.1, 3.2 완료  
**우선순위**: 높음

## 목표
HTML/JavaScript 코드를 생성하는 Web 렌더러를 구현한다.

## 작업 내용

### 1. WebRenderer 클래스
**파일**: `libs/dashboard/renderers/web_renderer.py`

```python
class WebRenderer(BaseRenderer):
    def __init__(self):
        super().__init__(RenderFormat.WEB)
        self.component_id_counter = 0
```

### 2. HTML 생성 메서드
각 위젯별 HTML 생성:
- Tailwind CSS 클래스 사용
- 데이터 속성 추가
- JavaScript 훅 포인트

### 3. 컴포넌트 ID 관리
- 고유 ID 생성
- DOM 선택자 제공
- 이벤트 바인딩 지원

### 4. 레이아웃 렌더링
```python
def render_layout(self, layout, widgets):
    if layout["type"] == "grid":
        return self._render_grid_layout(layout, widgets)
    elif layout["type"] == "flex":
        return self._render_flex_layout(layout, widgets)
```

### 5. JavaScript 데이터 임베딩
```python
html += f"""
<script>
window.widgetData['{component_id}'] = {json.dumps(data)};
</script>
"""
```

## 완료 기준
- [ ] WebRenderer 클래스 구현
- [ ] 모든 위젯 HTML 생성
- [ ] 레이아웃 시스템 구현
- [ ] CSS 클래스 적용
- [ ] JavaScript 통합 지원

## 테스트
```python
renderer = WebRenderer()

# HTML 생성 테스트
html = renderer.render_widget(
    WidgetType.SESSION_BROWSER,
    {"sessions": [...]},
    {"view_mode": "list"}
)

# HTML 검증
assert '<div' in html
assert 'session-browser' in html
```

## 주의사항
- XSS 방지 (HTML 이스케이프)
- 유효한 HTML5 생성
- 접근성 속성 포함