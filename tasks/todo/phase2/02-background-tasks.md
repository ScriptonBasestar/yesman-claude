# Task 2.2: 백그라운드 태스크 시스템 구현

**예상 시간**: 2.5시간  
**선행 조건**: Task 2.1 완료  
**우선순위**: 높음

## 목표
실시간 데이터 업데이트를 위한 백그라운드 태스크 시스템을 구현한다.

## 작업 내용

### 1. BackgroundTaskRunner 클래스
**파일**: `api/background_tasks.py`

구현 내용:
- 태스크 라이프사이클 관리
- 비동기 태스크 실행
- 에러 처리 및 재시도

### 2. 모니터링 태스크 구현

#### 세션 모니터링 태스크
- 1초 간격으로 세션 상태 확인
- 변경사항 감지
- WebSocket으로 브로드캐스트

#### 건강도 모니터링 태스크
- 30초 간격으로 건강도 계산
- 변경사항만 전송
- 계산 결과 캐싱

#### 활동 모니터링 태스크
- 60초 간격으로 활동 데이터 수집
- Git 활동, 세션 활동 집계

### 3. 태스크 스케줄링
```python
async def start():
    self.tasks = [
        asyncio.create_task(self.monitor_sessions()),
        asyncio.create_task(self.monitor_health()),
        asyncio.create_task(self.monitor_activity())
    ]
```

### 4. 정리 태스크
- 오래된 연결 정리
- 메모리 정리
- 로그 정리

### 5. FastAPI 통합
- 앱 시작 시 태스크 시작
- 앱 종료 시 태스크 정리

## 완료 기준
- [ ] BackgroundTaskRunner 클래스 구현
- [ ] 3개 모니터링 태스크 구현
- [ ] 태스크 시작/중지 메커니즘
- [ ] WebSocket 브로드캐스트 연동
- [ ] 에러 처리 및 로깅

## 테스트
```python
# 태스크 실행 확인
task_runner = BackgroundTaskRunner()
await task_runner.start()

# WebSocket으로 업데이트 수신 확인
# 세션 상태 변경 시 메시지 수신
# 건강도 변경 시 메시지 수신
```

## 주의사항
- CPU 사용률 최소화
- 메모리 효율적 구현
- 태스크 간 동기화 고려