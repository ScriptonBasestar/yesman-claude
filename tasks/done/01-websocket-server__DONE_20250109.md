# Task 2.1: WebSocket 서버 구현

**예상 시간**: 3시간  
**선행 조건**: Phase 1 완료  
**우선순위**: 높음

## 목표
FastAPI WebSocket 서버를 구현하고 연결 관리 시스템을 구축한다.

## 작업 내용

### 1. WebSocket 라우터 생성
**파일**: `api/routers/websocket.py`

구현할 클래스:
- `ConnectionManager`: WebSocket 연결 관리
- 채널별 연결 그룹 관리
- 연결/해제 처리

### 2. WebSocket 엔드포인트
구현할 엔드포인트:
- `/ws/dashboard` - 메인 대시보드 연결
- `/ws/sessions` - 세션 전용 채널
- `/ws/health` - 건강도 전용 채널
- `/ws/activity` - 활동 데이터 전용 채널

### 3. 메시지 프로토콜 정의
```python
{
    "type": "session_update",
    "timestamp": "2024-01-01T10:00:00",
    "data": {...}
}
```

### 4. 연결 관리 기능
- 연결 시 초기 데이터 전송
- 핑-퐁 메커니즘
- 연결 끊김 감지 및 정리
- 채널 구독/구독 해제

### 5. 브로드캐스트 메서드
- `broadcast_session_update()`
- `broadcast_health_update()`
- `broadcast_activity_update()`
- `broadcast_to_channel()`

## 완료 기준
- [x] WebSocket 라우터 파일 생성
- [x] ConnectionManager 클래스 구현
- [x] 4개 WebSocket 엔드포인트 구현
- [x] 메시지 송수신 테스트
- [x] 다중 클라이언트 연결 테스트

## 테스트
```bash
# WebSocket 테스트 도구
pip install websockets
python -m websockets ws://localhost:8000/ws/dashboard

# 또는 wscat 사용
npm install -g wscat
wscat -c ws://localhost:8000/ws/dashboard
```

## 주의사항
- 메모리 누수 방지 (연결 정리)
- 동시 연결 수 제한 고려
- 에러 발생 시 graceful 처리