# Task 3.5: Tauri 렌더러 구현

**예상 시간**: 2.5시간  
**선행 조건**: Task 3.1, 3.2 완료  
**우선순위**: 중간

## 목표
Tauri 앱에서 사용할 JSON 기반 렌더러를 구현한다.

## 작업 내용

### 1. TauriRenderer 클래스
**파일**: `libs/dashboard/renderers/tauri_renderer.py`

```python
class TauriRenderer(BaseRenderer):
    def __init__(self):
        super().__init__(RenderFormat.TAURI)
```

### 2. JSON 구조 생성
Tauri가 이해할 수 있는 구조:
```python
{
    "type": "widget",
    "widget_type": "session_browser",
    "id": "unique-id",
    "data": {...},
    "metadata": {...}
}
```

### 3. 데이터 처리 메서드
각 위젯별 특수 처리:
- `_process_session_browser()`: 액션 버튼 추가
- `_process_health_meter()`: 차트 데이터 생성
- `_process_activity_heatmap()`: 매트릭스 변환

### 4. 차트 데이터 변환
건강도, 메트릭 등을 차트 라이브러리용 데이터로:
```python
"chart_data": {
    "type": "radar",
    "labels": ["Build", "Tests", ...],
    "values": [90, 80, ...]
}
```

### 5. 색상 및 스타일 정보
```python
"style": {
    "background": "surface",
    "border": True,
    "shadow": True,
    "rounded": True
}
```

## 완료 기준
- [ ] TauriRenderer 클래스 구현
- [ ] JSON 구조 생성
- [ ] 데이터 처리 메서드 구현
- [ ] 차트 데이터 변환
- [ ] 메타데이터 포함

## 테스트
```python
renderer = TauriRenderer()

# JSON 생성 테스트
result = renderer.render_widget(
    WidgetType.SESSION_BROWSER,
    {"sessions": [...]}
)

# JSON 검증
assert isinstance(result, dict)
assert result["type"] == "session_browser"
assert "data" in result
```

## 주의사항
- JSON 직렬화 가능한 데이터만 사용
- 날짜는 ISO 형식으로
- 중첩 구조 깊이 제한