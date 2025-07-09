# Task 4.6: 성능 최적화 시스템

**예상 시간**: 2.5시간  
**선행 조건**: Phase 1-3 완료  
**우선순위**: 중간

## 목표
대시보드의 전반적인 성능을 모니터링하고 최적화하는 시스템을 구현한다.

## 작업 내용

### 1. PerformanceOptimizer 클래스
**파일**: `libs/dashboard/performance_optimizer.py`

주요 기능:
- CPU/메모리 모니터링
- 렌더링 시간 측정
- 자동 최적화 적용
- 성능 리포트 생성

### 2. PerformanceMetrics 데이터 클래스
```python
@dataclass
class PerformanceMetrics:
    cpu_usage: float
    memory_usage: float
    render_time: float
    widget_count: int
    active_connections: int
    cache_hit_rate: float
```

### 3. 모니터링 스레드
```python
def _monitor_loop(self):
    while self.monitoring:
        # CPU/메모리 측정
        # 최적화 필요 여부 체크
        # 자동 최적화 적용
```

### 4. 최적화 전략
- 업데이트 빈도 조절
- 캐시 정리
- 위젯 수 제한
- 애니메이션 비활성화

### 5. AsyncPerformanceOptimizer
비동기 최적화:
- 세마포어로 동시성 제한
- Rate limiting
- 배치 처리

## 완료 기준
- [ ] PerformanceOptimizer 구현
- [ ] 모니터링 시스템 구현
- [ ] 자동 최적화 로직
- [ ] 성능 리포트 생성
- [ ] 비동기 최적화 구현

## 테스트
```python
optimizer = PerformanceOptimizer()
optimizer.start_monitoring()

# 성능 리포트
report = optimizer.get_performance_report()
print(report["current"])
print(report["recommendations"])

# 렌더링 시간 측정
@optimizer.measure_render_time
def render_something():
    time.sleep(0.1)
```

## 주의사항
- 모니터링 오버헤드 최소화
- 정확한 측정
- 스레드 안전성