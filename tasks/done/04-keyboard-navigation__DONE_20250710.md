# Task 4.4: 키보드 네비게이션 시스템

**예상 시간**: 3시간  
**선행 조건**: Task 4.3 시작  
**우선순위**: 중간

## 목표
모든 인터페이스에서 일관된 키보드 네비게이션을 제공하는 시스템을 구현한다.

## 작업 내용

### 1. KeyboardNavigationManager 클래스
**파일**: `libs/dashboard/keyboard_navigation.py`

핵심 기능:
- 키 바인딩 관리
- 액션 핸들러 등록
- 컨텍스트 관리
- Vim 모드 지원

### 2. KeyBinding 데이터 클래스
```python
@dataclass
class KeyBinding:
    key: str
    modifiers: List[KeyModifier]
    action: str
    description: str
    context: Optional[str] = None
```

### 3. 기본 키 바인딩
- Tab/Shift+Tab: 포커스 이동
- 방향키: 네비게이션
- Enter: 활성화
- Ctrl+R: 새로고침
- Ctrl+F: 찾기

### 4. 포커스 관리
```python
def add_focusable_element(self, element_id):
def focus_next(self):
def focus_prev(self):
```

### 5. WebKeyboardHandler
JavaScript 키보드 처리:
```javascript
class KeyboardNavigationManager {
    registerBinding(key, modifiers, action)
    handleKeyDown(event)
    executeAction(action)
}
```

## 완료 기준
- [x] Python 키보드 매니저 구현
- [x] JavaScript 키보드 핸들러
- [x] 기본 바인딩 등록
- [x] 포커스 관리 시스템
- [x] Vim 모드 지원

## 테스트
```python
# 키 바인딩 테스트
manager = KeyboardNavigationManager()
manager.register_action("test", lambda: print("Test"))
manager.register_binding("t", [KeyModifier.CTRL], "test", "Test")

# 키 이벤트 처리
handled = manager.handle_key_event("t", [KeyModifier.CTRL])
assert handled == True
```

## 주의사항
- 플랫폼별 키 차이
- 키 충돌 방지
- 접근성 고려