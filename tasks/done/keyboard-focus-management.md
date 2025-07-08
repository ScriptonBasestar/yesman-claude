# 키보드 포커스 관리 시스템 구현

## 작업 개요
**상태**: 📋 진행중  
**우선순위**: HIGH  
**예상 소요시간**: 1시간  
**관련 컴포넌트**: `tauri-dashboard/src/lib/utils/keyboard-navigation.ts`

## 목표
키보드 네비게이션의 기반이 되는 포커스 관리 시스템을 구현하여 접근성 향상

## 상세 요구사항

### 기능 요구사항
- ✅ **포커스 요소 등록**: 포커스 가능한 요소들 자동 감지 및 관리
- ✅ **포커스 이동**: 방향키를 통한 논리적 포커스 이동
- ✅ **포커스 상태 추적**: 현재 포커스된 요소 상태 관리
- ✅ **이벤트 핸들링**: 키보드 이벤트 통합 처리

### 기술 구현
```typescript
// tauri-dashboard/src/lib/utils/keyboard-navigation.ts
export class KeyboardNavigationManager {
    private focusableElements: HTMLElement[] = [];
    private currentIndex: number = 0;
    private container: HTMLElement | null = null;
    
    constructor(containerSelector?: string) {
        if (containerSelector) {
            this.container = document.querySelector(containerSelector);
        }
    }
    
    registerElements(container: HTMLElement): void {
        const focusableSelectors = [
            'button',
            'input',
            'select',
            'textarea',
            'a[href]',
            '[tabindex]:not([tabindex="-1"])'
        ].join(',');
        
        this.focusableElements = Array.from(
            container.querySelectorAll(focusableSelectors)
        ) as HTMLElement[];
        
        this.currentIndex = 0;
    }
    
    moveFocus(direction: 'up' | 'down' | 'left' | 'right'): void {
        if (this.focusableElements.length === 0) return;
        
        switch (direction) {
            case 'down':
            case 'right':
                this.currentIndex = (this.currentIndex + 1) % this.focusableElements.length;
                break;
            case 'up':
            case 'left':
                this.currentIndex = this.currentIndex === 0 
                    ? this.focusableElements.length - 1 
                    : this.currentIndex - 1;
                break;
        }
        
        this.focusableElements[this.currentIndex]?.focus();
    }
    
    handleKeyPress(event: KeyboardEvent): boolean {
        switch (event.key) {
            case 'ArrowUp':
                event.preventDefault();
                this.moveFocus('up');
                return true;
            case 'ArrowDown':
                event.preventDefault();
                this.moveFocus('down');
                return true;
            case 'ArrowLeft':
                event.preventDefault();
                this.moveFocus('left');
                return true;
            case 'ArrowRight':
                event.preventDefault();
                this.moveFocus('right');
                return true;
            default:
                return false;
        }
    }
    
    getCurrentElement(): HTMLElement | null {
        return this.focusableElements[this.currentIndex] || null;
    }
    
    setFocusIndex(index: number): void {
        if (index >= 0 && index < this.focusableElements.length) {
            this.currentIndex = index;
            this.focusableElements[index]?.focus();
        }
    }
}
```

## 구현 결과
- ✅ 기본 포커스 관리 클래스 완성
- ✅ 방향키 이동 로직 구현
- ✅ 키보드 이벤트 핸들링 완료
- ✅ 포커스 상태 추적 기능 완성

## 성공 기준
- [x] 모든 포커스 가능한 요소가 올바르게 등록됨
- [x] 방향키로 논리적 순서대로 포커스 이동
- [x] 현재 포커스 상태를 정확히 추적
- [x] 키보드 이벤트가 적절히 처리됨

## 다음 단계
이 기반 시스템을 활용하여 세션 브라우저에 키보드 네비게이션 적용

---
**상태**: ✅ **완료**  
**완료일**: 2025-01-08