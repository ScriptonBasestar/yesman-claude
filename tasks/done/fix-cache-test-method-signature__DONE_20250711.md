---
source: alert
severity: medium
alert_id: cache-test-consolidation-analysis
tags: [testing, cache, method-signature, renderer, technical-debt]
priority: medium
estimated_hours: 2-3
complexity: low
---

# 캐시 테스트 메서드 시그니처 수정

**예상 시간**: 2-3시간  
**우선순위**: 중간 (P2)  
**복잡도**: 낮음

## 목표
TUIRenderer.render_widget 메서드 시그니처 불일치로 인한 캐시 성능 테스트 실패 해결

## 작업 내용

### 1. 즉시 대응 (Immediate Mitigation)
- [x] 테스트 실패 원인 분석 완료 (render_widget 메서드 시그니처 불일치)
- [x] test_optimizations.py의 test_cache_performance_improvement 메서드 수정
- [x] test_global_cache_utilities 메서드 수정

### 2. 근본 원인 해결 (Root Cause Fix)  
- [x] TUIRenderer.render_widget 호출 방식 표준화
- [x] cached_render 데코레이터와 render_widget 메서드 시그니처 호환성 확보
- [x] 모든 캐시 관련 테스트에서 올바른 메서드 호출 패턴 적용

### 3. 추가 모니터링 설정 (Monitoring)
- [x] 메서드 시그니처 불일치 탐지를 위한 테스트 추가
- [x] 향후 유사한 문제 방지를 위한 타입 힌트 강화

## 기술 상세

### 현재 문제
**TUIRenderer.render_widget 메서드 시그니처:**
```python
def render_widget(self, widget_type: WidgetType, data: Any, options: Optional[Dict[str, Any]] = None) -> str:
```

**테스트에서 잘못된 호출:**
```python
def slow_render(*args, **kwargs):
    time.sleep(0.05)  # 50ms delay
    return original_render(*args, **kwargs)  # 5개 인자 전달

# 오류: TUIRenderer.render_widget() takes from 3 to 4 positional arguments but 5 were given
```

### 해결 방안
**올바른 메서드 호출 패턴:**
```python
def slow_render(widget_type, data, options=None):
    time.sleep(0.05)  # 50ms delay
    return original_render(widget_type, data, options)
```

**cached_render 데코레이터 적용:**
```python
# 올바른 패턴
cached_method = cached_render()(self.renderer.render_widget)
self.renderer.render_widget = cached_method.__get__(self.renderer, TUIRenderer)

# 호출
result = self.renderer.render_widget(WidgetType.METRIC_CARD, metric)
```

## 선행 조건
- [x] TUIRenderer 클래스 및 render_widget 메서드 구현 완료
- [x] cached_render 데코레이터 구현 완료
- [x] 테스트 환경 구축 완료

## 완료 기준
- [x] test_cache_performance_improvement 테스트 통과
- [x] test_global_cache_utilities 테스트 통과
- [x] 모든 캐시 관련 테스트 성공률 100% 달성 (32/32 테스트 통과)
- [x] 메서드 시그니처 불일치 문제 해결

## 위험 요인
- 낮음: 단순한 메서드 호출 패턴 수정
- 기존 캐시 기능에 영향 없음
- 다른 테스트에 부작용 없음

## 구현 계획

### Step 1: 테스트 메서드 수정
```python
def test_cache_performance_improvement(self):
    """Test that caching improves performance"""
    metric = MetricCardData(title="Performance Test", value=75.5, suffix="%")
    
    # 올바른 메서드 래핑
    original_render = self.renderer.render_widget
    def slow_render(widget_type, data, options=None):
        time.sleep(0.05)  # 50ms delay
        return original_render(widget_type, data, options)
    
    self.renderer.render_widget = slow_render
    # ... 나머지 로직
```

### Step 2: 캐시 데코레이터 적용 방식 수정
```python
# 캐시 데코레이터 적용
cached_method = cached_render()(self.renderer.render_widget)
self.renderer.render_widget = cached_method.__get__(self.renderer, TUIRenderer)

# 올바른 호출
result1 = self.renderer.render_widget(WidgetType.METRIC_CARD, metric)
result2 = self.renderer.render_widget(WidgetType.METRIC_CARD, metric)
```

### Step 3: 검증 및 테스트
```python
# 결과 검증
assert result1 == result2
assert time2 < time1 * 0.5  # 캐시로 인한 성능 향상 검증
```