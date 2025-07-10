# Task 3.7: 렌더링 최적화 및 캐싱

**예상 시간**: 2.5시간  
**선행 조건**: Task 3.6 완료  
**우선순위**: 중간

## 목표
렌더링 성능을 최적화하고 캐싱 시스템을 구현한다.

## 작업 내용

### 1. RenderCache 클래스
**파일**: `libs/dashboard/renderers/optimizations.py`

```python
class RenderCache:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
```

### 2. 캐시 키 생성
- 위젯 타입 + 데이터 해시
- 옵션 포함
- 일관된 키 생성

### 3. 캐시 데코레이터
```python
def cached_render(func):
    def wrapper(self, widget_type, data, options=None):
        cache_key = render_cache.get_key(...)
        cached = render_cache.get(cache_key)
        if cached:
            return cached
        result = func(...)
        render_cache.set(cache_key, result)
        return result
    return wrapper
```

### 4. LazyRenderer 구현
- 지연 렌더링
- 필요할 때만 실제 렌더링
- 메모리 효율성

### 5. BatchRenderer 구현
- 여러 위젯 한번에 렌더링
- 공통 작업 최적화
- 병렬 처리 가능

## 완료 기준
- [ ] RenderCache 클래스 구현
- [ ] 캐시 데코레이터 구현
- [ ] LazyRenderer 구현
- [ ] BatchRenderer 구현
- [ ] 성능 테스트 작성

## 테스트
```python
# 캐시 효과 측정
import time

# 첫 번째 렌더링 (캐시 미스)
start = time.time()
result1 = render_widget(...)
time1 = time.time() - start

# 두 번째 렌더링 (캐시 히트)
start = time.time()
result2 = render_widget(...)
time2 = time.time() - start

assert time2 < time1 * 0.1  # 90% 이상 빠름
```

## 주의사항
- 캐시 무효화 전략
- 메모리 사용량 관리
- 스레드 안전성