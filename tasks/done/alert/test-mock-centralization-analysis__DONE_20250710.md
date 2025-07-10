# 🚨 테스트 Mock 중앙화 분석 및 실행 계획

**우선순위**: 중간  
**예상 작업시간**: 4-6시간  
**복잡도**: 중간  
**리스크**: 중간 (기존 테스트 깨질 가능성)

## 📋 현재 상황 분석

### 문제점
- 각 테스트 파일이 개별적으로 mock 객체 정의
- 동일한 mock 객체(tmux session, claude process)가 여러 파일에서 중복 정의
- `fixtures/mock_data.py`는 생성했으나 기존 테스트들이 미사용

### 영향 받는 파일 (약 15개)
- `tests/unit/core/cache/test_session_cache.py`
- `tests/unit/core/prompt/test_prompt_detector.py`
- `tests/unit/core/session/test_claude_restart.py`
- `tests/integration/test_full_automation.py`
- 기타 모든 Mock 사용 테스트 파일

## 🔧 실행 계획

### Phase 1: 현황 조사 (1시간)
1. **Mock 사용 현황 분석**
   ```bash
   grep -r "Mock\|MagicMock" tests/ --include="*.py" > mock_usage_report.txt
   grep -r "from unittest.mock import" tests/ --include="*.py" >> mock_usage_report.txt
   ```

2. **중복 Mock 패턴 식별**
   - TmuxSession mock 패턴
   - ClaudeProcess mock 패턴
   - Cache mock 패턴

### Phase 2: 중앙화 설계 (1시간)
1. **fixtures/mock_data.py 확장**
   - 현재 정의된 mock들 검토
   - 자주 사용되는 mock 패턴 추가
   - Factory 패턴으로 parameterized mock 생성

2. **Migration 전략 수립**
   - 파일별 우선순위 결정
   - Breaking change 최소화 방안

### Phase 3: 점진적 Migration (2-3시간)
1. **High-impact, Low-risk 파일부터 시작**
   - 단위 테스트 중 독립적인 파일들
   - 실패해도 전체에 영향이 적은 테스트들

2. **각 파일별 작업**
   - Mock import 변경
   - 기존 Mock 정의 제거
   - 테스트 실행 및 검증

### Phase 4: 검증 및 정리 (1시간)
1. **전체 테스트 실행**
2. **커버리지 변화 확인**
3. **성능 영향 측정**

## ⚠️ 주의사항

### 리스크 요소
- **Mock 동작 차이**: 기존 mock과 새 mock의 미묘한 동작 차이
- **테스트 의존성**: 일부 테스트가 특정 mock 동작에 의존할 수 있음
- **실행 순서**: Mock 초기화 순서가 테스트 결과에 영향

### 완화 방안
1. **백업 생성**: 모든 수정 전 git 브랜치 생성
2. **점진적 적용**: 한 번에 한 파일씩 수정
3. **회귀 테스트**: 각 수정 후 즉시 테스트 실행

## 🎯 성공 기준

### 정량적 목표
- Mock 중복 코드 50% 이상 감소
- 테스트 성공률 유지 (현재 47%)
- 테스트 실행 시간 10% 이내 증가

### 정성적 목표
- Mock 정의의 일관성 확보
- 테스트 코드 가독성 향상
- 유지보수성 개선

## 📅 실행 권장 타이밍

**즉시 실행 가능**: 아니오  
**선행 조건**: 현재 실패하는 테스트들의 기본적인 수정 완료 후  
**최적 타이밍**: 테스트 성공률이 70% 이상 달성된 후

**이유**: 현재 많은 테스트가 기본적인 문제로 실패하고 있어, mock 중앙화보다는 개별 테스트 수정이 우선

**처리 상태**: ✅ **converted**  
**새 파일**: `/tasks/todo/test-mock-centralization.md`  
**전환 일시**: 2025-07-10  
**우선순위 재평가**: 중간 → 낮음 (기본 테스트 수정 후 진행)