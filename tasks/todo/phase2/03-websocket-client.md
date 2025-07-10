# Task 2.3: WebSocket 클라이언트 구현

**예상 시간**: 3시간  
**선행 조건**: Task 2.1 완료  
**우선순위**: 높음

## 목표
브라우저에서 사용할 WebSocket 클라이언트 매니저를 구현한다.

## 작업 내용

### 1. WebSocketManager 클래스
**파일**: `web-dashboard/static/js/utils/websocket.js`

주요 기능:
- 연결 관리
- 자동 재연결
- 메시지 핸들링
- 이벤트 시스템

### 2. 연결 관리 기능
```javascript
class WebSocketManager {
    connect(channel) {}
    disconnect(channel) {}
    send(channel, data) {}
    subscribe(channels) {}
}
```

### 3. 자동 재연결 로직
- 연결 끊김 감지
- 지수 백오프 재연결
- 최대 재연결 시도 횟수
- 재연결 시 상태 복구

### 4. 이벤트 시스템
```javascript
wsManager.on('connected', callback)
wsManager.on('disconnected', callback)
wsManager.on('session_update', callback)
wsManager.on('health_update', callback)
```

### 5. 하트비트 구현
- 30초마다 ping 전송
- pong 응답 확인
- 응답 없으면 재연결

## 완료 기준
- [x] WebSocketManager 클래스 구현
- [x] 연결/해제 기능 작동
- [x] 자동 재연결 테스트
- [x] 이벤트 시스템 작동
- [x] 메시지 송수신 확인

## 테스트
```javascript
// 브라우저 콘솔에서 테스트
const ws = new WebSocketManager();
ws.connect('dashboard');

ws.on('connected', (data) => {
    console.log('Connected:', data);
});

ws.on('session_update', (data) => {
    console.log('Session update:', data);
});
```

## 주의사항
- 브라우저 호환성 확인
- 메모리 누수 방지
- 에러 상황 우아한 처리