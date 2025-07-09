# Task 3.8: 렌더러 시스템 테스트

**예상 시간**: 2시간  
**선행 조건**: Task 3.1-3.7 완료  
**우선순위**: 높음

## 목표
전체 렌더러 시스템에 대한 종합적인 테스트를 작성한다.

## 작업 내용

### 1. 단위 테스트
**파일**: `tests/test_renderers.py`

테스트 항목:
- 각 렌더러 개별 테스트
- 데이터 모델 테스트
- 팩토리 테스트

### 2. 통합 테스트
- 여러 포맷 동시 렌더링
- 데이터 변환 파이프라인
- 에러 처리 시나리오

### 3. 성능 테스트
```python
@pytest.mark.benchmark
def test_render_performance(benchmark):
    result = benchmark(render_widget, ...)
    assert benchmark.stats["mean"] < 0.05  # 50ms
```

### 4. 호환성 테스트
- 다양한 데이터 형식
- 엣지 케이스
- 빈 데이터 처리

### 5. 메모리 테스트
- 메모리 누수 검사
- 대용량 데이터 처리
- 캐시 크기 제한

## 완료 기준
- [ ] 단위 테스트 90% 커버리지
- [ ] 통합 테스트 작성
- [ ] 성능 벤치마크 통과
- [ ] 메모리 안정성 확인
- [ ] CI 통합

## 테스트 실행
```bash
# 전체 테스트
pytest tests/test_renderers.py -v

# 커버리지 확인
pytest tests/test_renderers.py --cov=libs.dashboard.renderers

# 성능 테스트만
pytest tests/test_renderers.py -v --benchmark-only
```

## 주의사항
- 테스트 독립성 유지
- 모킹 적절히 활용
- 실패 시 명확한 메시지