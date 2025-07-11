---
source: alert
severity: medium
alert_id: cache-test-consolidation-analysis
tags: [testing, refactoring, cache, maintenance, technical-debt]
priority: low
estimated_hours: 8-12
complexity: high
---

# 캐시 테스트 통합 및 최적화

**예상 시간**: 8-12시간  
**우선순위**: 낮음 (P3)  
**복잡도**: 높음

## 목표
6개 캐시 관련 테스트 파일(총 1,484줄)의 중복 제거 및 체계적 재구성을 통한 유지보수성 향상

## 작업 내용

### 1. 즉시 대응 (Immediate Mitigation)
- [x] 캐시 테스트 현황 조사 및 의존성 매핑
- [x] 실패하는 테스트 케이스 파악 및 우선순위 설정
- [x] 위험도 평가 및 안전한 통합 전략 수립

### 2. 근본 원인 해결 (Root Cause Fix)
- [ ] 단위/통합 테스트 분리를 위한 최적 파일 구조 설계
- [ ] 점진적 마이그레이션으로 안전한 통합 실행
- [ ] 중복 테스트 케이스 제거 및 공통 fixture 통합
- [ ] 복잡한 의존성 체인 단순화 (SessionCache → SessionManager → Dashboard)

### 3. 추가 모니터링 설정 (Monitoring)
- [ ] 테스트 성공률 및 실행 시간 모니터링
- [ ] 중복 제거 효과 측정 시스템 구축
- [ ] 향후 테스트 코드 품질 유지를 위한 가이드라인 수립

## 현황 분석

### 실패 테스트 케이스 우선순위 (2025-07-11)

**HIGH PRIORITY - 즉시 수정 필요:**
- `test_cache_integration.py` - ✅ **수정완료** (CacheStats 구조 문제)
- `test_error_handling.py` - ✅ **수정완료** (deprecated CacheManager 임포트)

**MEDIUM PRIORITY - 메서드 시그니처 문제:**
- `test_optimizations.py` - `TestOptimizationIntegration::test_cache_performance_improvement`
  - 원인: `render_widget` 메서드 시그니처 불일치
  - 영향: 캐시 성능 측정 불가능
- `test_optimizations.py` - `TestOptimizationIntegration::test_global_cache_utilities`
  - 원인: 동일한 메서드 시그니처 문제

**LOW PRIORITY - 아키텍처 변경 관련:**
- 3개 추가 테스트 파일의 `render_widget` 호출 방식 문제
- `RenderFormat.TUI` vs `WidgetType` enum 혼동

### 캐시 시스템 현황

**현재 작동 중인 캐시:**
- `RenderCache` (libs/dashboard/renderers/optimizations.py) - 정상 작동
- Tauri 백엔드 캐시 (Rust) - 정상 작동
- JavaScript 메모리 최적화 - 정상 작동

**제거된 캐시 시스템:**
- `SessionCache` - 완전 제거됨
- `CacheManager` - 완전 제거됨
- 핵심 캐시 인프라 - 재설계 필요

**위험도 평가:**
- 현재 시점에서 대규모 캐시 통합은 고위험 ⚠️
- 기존 RenderCache 시스템은 안정적 ✅
- 테스트 수정은 저위험 작업 ✅

### 안전한 통합 전략 (3단계 접근법)

**Phase 1: 테스트 안정화 (저위험) - 추천**
- ✅ 깨진 테스트 임포트 수정 (완료)
- ✅ CacheStats 구조 문제 수정 (완료)
- 🔄 메서드 시그니처 문제 수정 (진행중)
- 기존 RenderCache 테스트 커버리지 확대

**Phase 2: 점진적 확장 (중위험) - 조건부 권장**
- 전제조건: Phase 1 완료 + 전체 테스트 성공률 90% 이상
- RenderCache 기반 추가 캐시 유형 구현
- 단위 테스트와 통합 테스트 분리
- 성능 벤치마크 기준선 설정

**Phase 3: 대규모 재구성 (고위험) - 현재 비권장**
- 전제조건: Phase 2 완료 + 3개월 안정 운영
- 새로운 캐시 아키텍처 설계
- SessionCache 재구현 (필요시)
- 6개 파일 통합 작업

**긴급 권장사항:**
1. **현재 Phase 1만 진행** - 안정성 우선
2. **Phase 2/3는 연기** - 다른 우선순위 작업 완료 후
3. **현재 RenderCache 유지** - 성능 문제 없음
4. **문서화 우선** - 현재 아키텍처 기록

## 기술 상세

### 제안 파일 구조
```
tests/unit/core/cache/
├── test_cache_basic.py (150줄) - CRUD, 기본 동작
├── test_cache_expiration.py (120줄) - TTL, 만료 로직  
├── test_cache_strategies.py (200줄) - LRU/LFU/TTL 전략
└── test_cache_concurrency.py (100줄) - 동시성, 스레드 안전성

tests/integration/cache/
├── test_session_cache_integration.py (170줄)
├── test_dashboard_cache_integration.py (229줄)  
├── test_session_manager_cache.py (212줄)
└── test_cache_visualization.py (250줄)
```

### 선행 조건
- [ ] 현재 캐시 관련 테스트 성공률 80% 이상 달성
- [ ] 대형 파일 분할 작업 완료
- [ ] Mock 중앙화 시스템 구축 완료

## 완료 기준
- [ ] 6개 캐시 테스트 파일이 체계적으로 재구성됨
- [ ] 중복 테스트 케이스가 제거되고 공통 fixture 통합됨
- [ ] 전체 테스트 성공률이 기존 대비 유지되거나 향상됨
- [ ] 코드 라인 수가 20% 이상 감소함
- [ ] 유지보수 가이드 및 문서가 업데이트됨

## 위험 요인
- 복잡한 의존성 체인으로 인한 높은 실패 위험
- 상태 의존성이 있는 통합 테스트의 불안정성
- Mock 레벨 차이 (unit vs integration) 처리

## 주의사항
- 현재 시점에서는 위험도가 높아 즉시 실행 비권장
- 다른 기본적인 테스트 수정이 우선순위
- 프로젝트 전반적 안정화 후 진행 권장