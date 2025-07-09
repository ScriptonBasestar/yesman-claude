# Task 2.4: 실시간 업데이트 통합

**예상 시간**: 2시간  
**선행 조건**: Task 2.3 완료  
**우선순위**: 높음

## 목표
WebSocket을 통한 실시간 업데이트를 프론트엔드에 통합한다.

## 작업 내용

### 1. main.js WebSocket 통합
**파일**: `web-dashboard/static/js/main.js` 수정

추가 내용:
- WebSocket 매니저 초기화
- 이벤트 리스너 등록
- 채널 구독

### 2. 업데이트 핸들러 구현
```javascript
function updateSessionDisplay(data) {}
function updateHealthDisplay(data) {}
function updateActivityDisplay(data) {}
```

### 3. 알림 시스템
- 연결 상태 알림
- 업데이트 알림
- 에러 알림
- Toast 스타일 UI

### 4. Alpine.js 데이터 동기화
- WebSocket 데이터를 Alpine 컴포넌트에 반영
- 반응형 업데이트
- 상태 관리 통합

### 5. 연결 상태 표시
- 헤더에 연결 상태 아이콘
- 연결 끊김 시 재연결 중 표시
- 오프라인 모드 안내

## 완료 기준
- [ ] WebSocket 초기화 코드 추가
- [ ] 실시간 업데이트 작동
- [ ] 알림 시스템 구현
- [ ] 연결 상태 표시
- [ ] 오프라인 처리

## 테스트
```javascript
// 실시간 업데이트 테스트
1. 대시보드 열기
2. 다른 터미널에서 세션 생성/삭제
3. 대시보드에 즉시 반영 확인

// 재연결 테스트
1. 서버 중지
2. 재연결 시도 확인
3. 서버 재시작
4. 자동 재연결 확인
```

## 주의사항
- UI 깜빡임 최소화
- 부드러운 전환 효과
- 중복 업데이트 방지