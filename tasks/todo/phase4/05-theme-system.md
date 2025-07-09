# Task 4.5: 통합 테마 시스템

**예상 시간**: 2.5시간  
**선행 조건**: Task 4.1 시작  
**우선순위**: 중간

## 목표
모든 인터페이스에서 일관된 테마를 제공하는 시스템을 구현한다.

## 작업 내용

### 1. Theme 데이터 클래스
**파일**: `libs/dashboard/theme_system.py`

```python
@dataclass
class Theme:
    name: str
    mode: ThemeMode
    colors: ColorPalette
    typography: Typography
    spacing: Spacing
    custom_css: str = ""
```

### 2. ThemeManager 클래스
주요 기능:
- 테마 로드/저장
- 시스템 테마 감지
- 테마 전환
- CSS/Rich 내보내기

### 3. 기본 테마 정의
- Default Light
- Default Dark
- High Contrast
- 사용자 정의 테마

### 4. 테마 내보내기
```python
def export_css(self, theme: Theme) -> str:
    """CSS 변수로 내보내기"""

def export_rich_theme(self, theme: Theme) -> Dict:
    """Rich 스타일로 내보내기"""
```

### 5. 플랫폼별 다크모드 감지
- macOS: `defaults read`
- Windows: 레지스트리
- Linux: 환경 변수

## 완료 기준
- [ ] Theme 데이터 모델 구현
- [ ] ThemeManager 구현
- [ ] 3개 기본 테마 정의
- [ ] 테마 저장/로드 기능
- [ ] 플랫폼별 테마 감지

## 테스트
```python
manager = ThemeManager()

# 테마 전환
manager.set_mode(ThemeMode.DARK)
assert manager.current_theme.name == "Default Dark"

# CSS 내보내기
css = manager.export_css()
assert "--color-primary" in css

# 테마 저장
custom_theme = Theme(name="Custom", mode=ThemeMode.CUSTOM)
manager.save_theme("my-theme", custom_theme)
```

## 주의사항
- 색상 대비 접근성
- 테마 전환 시 깜빡임 방지
- 사용자 설정 우선