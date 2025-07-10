# Task 4.7: 통합 테스트 작성

**예상 시간**: 3시간  
**선행 조건**: Task 4.1-4.6 완료  
**우선순위**: 높음

## 목표
전체 시스템에 대한 종합적인 통합 테스트를 작성한다.

## 작업 내용

### 1. 통합 테스트 스위트
**파일**: `tests/test_integration.py`

테스트 클래스:
```python
class TestDashboardIntegration:
    def test_interface_detection(self)
    def test_multi_format_rendering(self)
    def test_theme_switching(self)
    def test_keyboard_navigation(self)
    def test_performance_monitoring(self)
```

### 2. 인터페이스 테스트
- 자동 감지 테스트
- 각 인터페이스 실행
- 전환 테스트

### 3. 종단간 테스트
```python
def test_end_to_end_dashboard_launch(self):
    # 1. 인터페이스 감지
    # 2. 대시보드 실행
    # 3. 데이터 로드
    # 4. 사용자 상호작용
    # 5. 종료
```

### 4. 동시성 테스트
```python
@pytest.mark.asyncio
async def test_concurrent_rendering(self):
    # 동시 렌더링
    # WebSocket 동시 연결
    # 메모리 안정성
```

### 5. 성능 벤치마크
```python
@pytest.mark.benchmark
def test_rendering_performance(self, benchmark):
    # 100개 세션 렌더링
    # 50ms 이내 목표
```

## 완료 기준
- [x] 통합 테스트 파일 생성
- [x] 15개 이상 테스트 케이스
- [x] 모든 테스트 통과
- [>] CI 파이프라인 통합
- [x] 성능 기준 충족

## 테스트 실행
```bash
# 전체 통합 테스트
pytest tests/test_integration.py -v

# 특정 테스트만
pytest tests/test_integration.py::TestDashboardIntegration::test_interface_detection

# 성능 테스트
pytest tests/test_integration.py --benchmark-only

# 커버리지 확인
pytest tests/test_integration.py --cov=libs.dashboard
```

## 주의사항
- 테스트 격리
- 실제 환경 시뮬레이션
- 명확한 실패 메시지

## 미완료 항목 
- **CI 파이프라인 통합**: GitHub Actions나 별도 CI/CD 시스템 설정이 필요한 작업으로, 현재 프로젝트 범위를 벗어남. 테스트 코드는 준비되어 있어 향후 CI 설정 시 즉시 사용 가능.