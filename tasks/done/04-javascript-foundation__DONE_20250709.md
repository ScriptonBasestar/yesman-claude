# Task 1.4: JavaScript 기반 구조 구현

**예상 시간**: 3시간  
**선행 조건**: Task 1.3 완료  
**우선순위**: 높음

## 목표
웹 대시보드의 JavaScript 기반 구조를 구현하고 전역 상태 관리를 설정한다.

## 작업 내용

### 1. 메인 JavaScript 파일
**파일**: `web-dashboard/static/js/main.js`

구현 내용:
- 전역 dashboard 객체 생성
- API 클라이언트 메서드
- 유틸리티 함수
- Alpine.js 컴포넌트 초기화

### 2. 전역 상태 관리
```javascript
window.dashboard = {
    state: {
        sessions: [],
        health: {},
        theme: 'light'
    },
    api: {
        getSessions() {},
        getHealth() {},
        getActivity() {}
    },
    utils: {
        formatDate() {},
        toggleTheme() {}
    }
};
```

### 3. Alpine.js 통합
- 대시보드 컴포넌트 함수
- 데이터 바인딩 설정
- 이벤트 핸들러 구현

### 4. API 통신 구현
- Fetch API 사용
- 에러 핸들링
- 로딩 상태 관리
- 자동 재시도 로직

### 5. 테마 시스템
- localStorage 활용
- 시스템 테마 감지
- CSS 클래스 토글

## 완료 기준
- [x] main.js 파일 생성 및 구조 구현
- [x] API 통신 메서드 구현
- [x] Alpine.js 컴포넌트 작동
- [x] 테마 전환 기능 작동
- [x] 에러 핸들링 구현

## 테스트
```javascript
// 브라우저 콘솔에서 테스트
window.dashboard.api.getSessions()
window.dashboard.utils.toggleTheme()

// Alpine.js 컴포넌트 확인
document.querySelector('[x-data]').__x
```

## 주의사항
- ES6+ 문법 사용
- 비동기 처리 적절히 구현
- 메모리 누수 방지