# 키보드 네비게이션 지원 구현

## 작업 개요
**상태**: 📋 대기중  
**우선순위**: HIGH  
**예상 소요시간**: 2-3시간  
**관련 컴포넌트**: `libs/dashboard/widgets/session_browser.py`

## 목표
마우스 없이도 키보드만으로 세션 브라우저를 빠르고 효율적으로 탐색할 수 있는 기능 구현

## 상세 요구사항

### 키보드 단축키 정의
- **방향키 (↑↓←→)**: 세션/패널 간 이동
- **Enter**: 선택된 세션/패널 접속
- **ESC**: 상위 레벨로 돌아가기 또는 선택 취소
- **Tab/Shift+Tab**: 포커스 영역 간 이동
- **Space**: 세션 시작/정지 토글
- **Ctrl+R**: 세션 새로고침
- **Delete**: 세션 종료 확인

### 접근성 요구사항
- **포커스 하이라이트**: 현재 선택된 항목 명확한 시각적 표시
- **스크린 리더 지원**: ARIA 라벨 및 역할 정의
- **키보드 트랩**: 모달/드롭다운에서 포커스 격리
- **건너뛰기 링크**: 메인 콘텐츠로 바로 이동

## 구현 계획

### 1단계: 포커스 관리 시스템 (1시간)
```typescript
// tauri-dashboard/src/lib/utils/keyboard-navigation.ts
export class KeyboardNavigationManager {
    private focusableElements: HTMLElement[] = [];
    private currentIndex: number = 0;
    
    registerElements(container: HTMLElement): void {
        // 포커스 가능한 요소들 등록 및 관리
    }
    
    handleKeyPress(event: KeyboardEvent): void {
        // 키보드 이벤트 처리 및 라우팅
    }
    
    moveFocus(direction: 'up' | 'down' | 'left' | 'right'): void {
        // 방향키에 따른 포커스 이동
    }
}
```

### 2단계: 세션 브라우저 키보드 통합 (1시간)
```svelte
<!-- tauri-dashboard/src/lib/components/session/SessionBrowser.svelte -->
<script>
    import { KeyboardNavigationManager } from '$lib/utils/keyboard-navigation';
    
    let navigationManager: KeyboardNavigationManager;
    
    onMount(() => {
        navigationManager = new KeyboardNavigationManager();
        // 키보드 이벤트 리스너 등록
    });
    
    function handleKeydown(event: KeyboardEvent) {
        // 컴포넌트별 키보드 동작 처리
    }
</script>

<div class="session-browser" on:keydown={handleKeydown} tabindex="0">
    <!-- 키보드 접근 가능한 세션 목록 -->
</div>
```

### 3단계: 시각적 피드백 구현 (30분)
```css
/* 포커스 하이라이트 스타일 */
.session-item:focus {
    outline: 2px solid #007acc;
    outline-offset: 2px;
    background-color: var(--focus-bg-color);
}

.session-item.keyboard-focused {
    box-shadow: 0 0 0 3px rgba(0, 122, 204, 0.5);
}
```

### 4단계: 컨텍스트 메뉴 키보드 지원 (30분)
- 우클릭 메뉴를 키보드로 열기 (Shift+F10 또는 Menu 키)
- 메뉴 항목 간 방향키 이동
- Enter로 선택, ESC로 닫기

## 구현 상세

### 키보드 이벤트 매핑
```typescript
const keyboardActions = {
    'ArrowUp': () => moveFocus('up'),
    'ArrowDown': () => moveFocus('down'),
    'ArrowLeft': () => moveFocus('left'),
    'ArrowRight': () => moveFocus('right'),
    'Enter': () => executeAction('select'),
    'Escape': () => executeAction('cancel'),
    'Space': () => executeAction('toggle'),
    'Delete': () => executeAction('delete'),
    'F2': () => executeAction('rename'),
    'Ctrl+R': () => executeAction('refresh')
};
```

### ARIA 접근성 구현
```html
<div 
    role="grid" 
    aria-label="세션 브라우저"
    aria-rowcount={sessions.length}
>
    <div 
        role="gridcell" 
        aria-selected={isSelected}
        aria-label={`세션: ${session.name}, 상태: ${session.status}`}
        tabindex={isSelected ? 0 : -1}
    >
        {session.name}
    </div>
</div>
```

## 성공 기준
- [ ] 모든 세션 브라우저 기능이 키보드만으로 접근 가능
- [ ] 포커스 이동이 논리적 순서로 진행됨
- [ ] 시각적 포커스 인디케이터가 명확하게 표시됨
- [ ] 스크린 리더에서 모든 요소가 적절히 읽힘
- [ ] 키보드 트랩이 모달에서 올바르게 작동함

## 테스트 계획
1. **탭 순서 테스트**: Tab 키로 모든 요소 순차 접근 확인
2. **방향키 테스트**: 그리드 형태 네비게이션 정확성 검증
3. **스크린 리더 테스트**: NVDA/JAWS로 접근성 확인
4. **키보드 전용 사용성 테스트**: 마우스 없이 전체 워크플로우 완주

## 의존성
- **연관 작업**: 세션 히트맵과 UI 통합 필요
- **라이브러리**: 접근성 유틸리티 함수 개발

---
*이 기능은 접근성 및 파워 유저 경험 향상의 핵심 요소입니다.*