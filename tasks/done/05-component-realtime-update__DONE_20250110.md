# Task 2.5: 컴포넌트 실시간 업데이트 구현

**예상 시간**: 3시간  
**선행 조건**: Task 2.4 완료  
**우선순위**: 높음

## 목표
각 컴포넌트가 WebSocket 업데이트를 받아 실시간으로 UI를 갱신하도록 구현한다.

## 작업 내용

### 1. SessionBrowser 실시간 업데이트
**파일**: `web-dashboard/static/js/components/session-browser.js` 수정

추가 기능:
- `updateSession()` 메서드
- 세션 추가/제거 애니메이션
- 상태 변경 하이라이트

### 2. 업데이트 애니메이션
- 새 세션: 슬라이드 인 + 녹색 하이라이트
- 업데이트: 노란색 펄스 효과
- 제거: 빨간색 페이드 아웃

### 3. 증분 업데이트
- 전체 재렌더링 대신 변경된 부분만 업데이트
- DOM diff 최소화
- 성능 최적화

### 4. 실시간 활동 표시
- Claude 활성 상태 실시간 표시
- 마지막 활동 시간 업데이트
- 활성 상태 아이콘 애니메이션

### 5. 컴포넌트 생명주기 관리
```javascript
connectedCallback() {
    this.setupRealtimeUpdates();
}

disconnectedCallback() {
    this.cleanup();
}
```

## 완료 기준
- [x] SessionBrowser 실시간 업데이트
- [x] HealthWidget 실시간 업데이트
- [x] ActivityHeatmap 실시간 업데이트
- [x] 애니메이션 효과 적용
- [x] 메모리 누수 없음

## 테스트
```javascript
// 세션 업데이트 시뮬레이션
window.wsManager.trigger('session_update', {
    session_name: "test-session",
    session: { status: "active", claude_active: true }
});

// 애니메이션 확인
// 개발자 도구 > Elements > 변경사항 관찰
```

## 주의사항
- 과도한 애니메이션 자제
- 사용자 선호에 따른 애니메이션 비활성화 옵션
- 접근성 고려 (prefers-reduced-motion)