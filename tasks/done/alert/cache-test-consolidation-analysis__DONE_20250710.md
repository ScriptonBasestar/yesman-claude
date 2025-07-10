# 🚨 캐시 테스트 통합 복잡성 분석 및 실행 계획

**우선순위**: 높음  
**예상 작업시간**: 8-12시간  
**복잡도**: 높음  
**리스크**: 높음 (6개 파일 간 복잡한 의존성)

## 📋 현재 상황 분석

### 대상 파일 구조
```
캐시 관련 테스트 (6개 파일, 총 1,484줄)
├── test_session_cache.py (309줄) - 기본 캐시 기능
├── test_session_manager_cache.py (212줄) - 세션 매니저 통합  
├── test_session_cache_integration.py (170줄) - 캐시 통합 테스트
├── test_dashboard_cache_integration.py (229줄) - 대시보드 통합
├── test_advanced_cache_strategies.py (314줄) - 고급 전략
└── test_cache_visualization.py (250줄) - 시각화 기능
```

### 복잡성 요인
1. **각기 다른 테스트 범위**: 단위/통합/시각화 테스트 혼재
2. **의존성 체인**: session → cache → dashboard 의존성
3. **중복 기능**: 동일한 캐시 기능을 다른 관점에서 테스트
4. **통합 레벨 차이**: 모듈 수준부터 시스템 수준까지 다양

## 🔧 제안 통합 전략

### Option 1: 기능별 3개 파일 (권장 ❌)
```
├── test_cache_core.py - 기본 캐시 기능 (1,2번 통합)
├── test_cache_strategies.py - 캐시 전략 (5,6번 통합)  
└── test_cache_integration.py - 통합 테스트 (3,4번 통합)
```

**문제점**: 여전히 파일당 500줄 이상, 단일 책임 원칙 위배

### Option 2: 레이어별 분리 (권장 ✅)
```
tests/unit/core/cache/ (단위 테스트)
├── test_session_cache.py (300줄) - 핵심 캐시 로직
├── test_cache_strategies.py (314줄) - 전략 패턴 테스트
└── test_cache_basic.py (200줄) - 기본 CRUD 작업

tests/integration/cache/ (통합 테스트)  
├── test_session_manager_integration.py (250줄)
├── test_dashboard_integration.py (300줄)
└── test_cache_visualization.py (250줄)
```

### Option 3: 세분화된 분리 (최적 ⭐)
```
tests/unit/core/cache/
├── test_cache_basic.py (150줄) - CRUD, 기본 동작
├── test_cache_expiration.py (120줄) - TTL, 만료 로직  
├── test_cache_strategies.py (200줄) - LRU/LFU/TTL 전략
└── test_cache_concurrency.py (100줄) - 동시성, 스레드 안전성

tests/integration/cache/
├── test_session_cache_integration.py (170줄) - 기존 유지
├── test_dashboard_cache_integration.py (229줄) - 기존 유지  
├── test_session_manager_cache.py (212줄) - 기존 유지
└── test_cache_visualization.py (250줄) - 시각화는 별도 유지
```

## 🔍 상세 분석 필요 사항

### 1. 중복 테스트 케이스 식별
```bash
# 테스트 함수명 추출 및 중복 확인
for file in test_*cache*.py; do
  echo "=== $file ==="
  grep -n "def test_" "$file" | sed 's/.*def //' | sed 's/(.*://'
done | sort | uniq -c | sort -nr
```

### 2. 공통 Fixture 분석
```bash
# setUp, fixture, mock 패턴 확인
grep -n "setUp\|@pytest.fixture\|Mock" test_*cache*.py
```

### 3. 의존성 매트릭스 작성
- 각 테스트가 의존하는 외부 모듈
- 테스트 간 데이터 공유 여부
- Mock 객체 사용 패턴

## ⚠️ 높은 위험도 요인

### 1. 복잡한 의존성 체인
```python
SessionCache ← SessionManager ← Dashboard ← Visualization
```
각 레벨에서 캐시 동작이 다르게 테스트됨

### 2. 통합 테스트 특성
- 실제 캐시 인스턴스 공유
- 상태 의존성 있을 가능성
- Mock 레벨이 다름 (unit vs integration)

### 3. 현재 테스트 실패 상황
- 일부 캐시 테스트가 이미 실패 중
- 통합 과정에서 더 많은 실패 발생 가능

## 📅 단계별 실행 계획

### Phase 1: 현황 조사 및 매핑 (2-3시간)
1. **중복 테스트 함수 매핑**
2. **의존성 체인 분석**  
3. **Mock 사용 패턴 파악**
4. **공통 코드 식별**

### Phase 2: 설계 및 검증 (2시간)
1. **최종 파일 구조 결정**
2. **Migration 순서 계획**
3. **Risk 완화 방안 수립**

### Phase 3: 점진적 통합 (4-6시간)
1. **단위 테스트부터 시작** (위험도 낮음)
2. **통합 테스트는 마지막** (위험도 높음)
3. **각 단계별 검증**

### Phase 4: 검증 및 정리 (1-2시간)
1. **전체 테스트 실행**
2. **성능 영향 측정**
3. **문서 업데이트**

## 🚨 권장 사항

### ❌ 즉시 실행 권장하지 않음

**이유**:
1. **높은 복잡도**: 6개 파일 간 복잡한 관계
2. **현재 실패 상황**: 일부 캐시 테스트가 이미 실패
3. **높은 위험도**: 잘못 통합 시 더 많은 테스트 실패

### ✅ 대안 접근법

#### 선행 작업 (권장)
1. **개별 파일 안정화**
   - 현재 실패하는 캐시 테스트들 먼저 수정
   - 각 파일의 성공률을 80% 이상으로 향상

2. **대형 파일 분할 우선**
   - `test_cache_strategies.py` (314줄) 분할 먼저 진행
   - 성공률 100%인 파일이므로 안전

#### 조건부 실행
**선행 조건**:
- 캐시 관련 테스트 성공률 80% 이상
- 대형 파일 분할 완료
- Mock 중앙화 완료

**실행 순서**:
1. 단위 테스트 통합 (test_session_cache.py 위주)
2. 통합 테스트는 기존 구조 유지
3. 점진적 개선

## 🏷️ 태스크 재분류

**현재**: results/refactoring.tests/issues/  
**권장**: tasks/alert/ → tasks/todo/  
**우선순위**: P2 (중간) → P3 (낮음)

**처리 상태**: ✅ **converted**  
**새 파일**: `/tasks/todo/cache-test-consolidation.md`  
**전환 일시**: 2025-07-10

**재분류 이유**: 
- 현재 시점에서는 위험도가 높고 복잡함
- 다른 기본적인 테스트 수정이 우선
- 프로젝트 안정화 후 진행이 적절

## 📊 ROI 분석

**비용**: 8-12시간 + 높은 위험도  
**혜택**: 캐시 테스트 관리 개선, 중복 제거  

**결론**: 현재 ROI 부정적, 프로젝트 후반부에 진행 권장