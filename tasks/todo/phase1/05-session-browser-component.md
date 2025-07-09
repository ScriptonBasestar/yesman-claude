# Task 1.5: 세션 브라우저 컴포넌트 구현

**예상 시간**: 3시간  
**선행 조건**: Task 1.4 완료  
**우선순위**: 높음

## 목표
웹 컴포넌트 기반의 세션 브라우저를 구현한다.

## 작업 내용

### 1. SessionBrowser 클래스 구현
**파일**: `web-dashboard/static/js/components/session-browser.js`

기본 구조:
```javascript
class SessionBrowser extends HTMLElement {
    constructor() {
        super();
        this.sessions = [];
        this.viewMode = 'list'; // list, grid, tree
    }
    
    connectedCallback() {}
    async loadSessions() {}
    render() {}
}

customElements.define('session-browser', SessionBrowser);
```

### 2. 뷰 모드 구현
- 리스트 뷰: 세션 정보를 목록으로 표시
- 그리드 뷰: 카드 형태로 배치
- 트리 뷰: 세션-윈도우-페인 계층 구조

### 3. 세션 액션 버튼
각 세션에 대한 액션:
- Enter: 세션 진입
- Stop: 세션 중지
- Refresh: 세션 새로고침

### 4. 뷰 모드 전환 UI
- 버튼 그룹으로 뷰 모드 선택
- 현재 선택된 모드 하이라이트
- 로컬 스토리지에 선호 설정 저장

### 5. 렌더링 메서드
- `renderListView()`
- `renderGridView()`
- `renderTreeView()`

## 완료 기준
- [ ] SessionBrowser 클래스 구현
- [ ] 3가지 뷰 모드 모두 작동
- [ ] 세션 데이터 표시 확인
- [ ] 뷰 모드 전환 작동
- [ ] 액션 버튼 이벤트 바인딩

## 테스트
```javascript
// 컴포넌트 등록 확인
customElements.get('session-browser')

// 뷰 모드 전환 테스트
document.querySelector('session-browser').changeViewMode('grid')

// 세션 데이터 로드 테스트
document.querySelector('session-browser').loadSessions()
```

## 주의사항
- Web Components 표준 준수
- Shadow DOM은 사용하지 않음 (스타일링 편의)
- 메모리 효율적인 렌더링