---
source: alert
severity: medium
alert_id: test-mock-centralization-analysis
tags: [testing, mock, refactoring, code-quality, maintenance]
created: 2025-07-10
priority: low
---

# 테스트 Mock 중앙화 및 표준화

**예상 시간**: 4-6시간  
**우선순위**: 낮음 (P3)  
**복잡도**: 중간

## 목표
15개 테스트 파일에 분산된 중복 mock 객체를 중앙화하여 일관성 확보 및 유지보수성 향상

## 📋 현재 상황
- **문제점**: 각 테스트 파일이 개별적으로 mock 객체 정의
- **중복 대상**: TmuxSession, ClaudeProcess, Cache mock 등
- **영향 파일**: 약 15개 테스트 파일
- **현재 상태**: `fixtures/mock_data.py` 생성했으나 기존 테스트에서 미사용

## 작업 내용

### 1. 즉시 대응 (Immediate Mitigation)
- [ ] Mock 사용 현황 전체 분석 및 문서화
- [ ] 기존 `fixtures/mock_data.py` 검토 및 확장 계획 수립
- [ ] 가장 중복이 많은 mock 패턴 우선 식별

### 2. 근본 원인 해결 (Root Cause Fix)
- [ ] `fixtures/mock_data.py` 확장 및 표준 mock 팩토리 구현
- [ ] 점진적 마이그레이션으로 기존 테스트 파일 업데이트
- [ ] Mock 사용 가이드라인 및 컨벤션 수립
- [ ] 중복 mock 코드 제거 및 일관성 확보

### 3. 추가 모니터링 설정 (Monitoring)
- [ ] Mock 중복 감지를 위한 lint 규칙 추가
- [ ] 테스트 실행 시간 및 성능 변화 추적
- [ ] 향후 중복 mock 생성 방지 체크리스트 수립

## 상세 실행 계획

### Phase 1: 현황 조사 및 분석 (1시간)
**Mock 사용 현황 전체 분석**:
```bash
# Mock 사용 패턴 분석
grep -r "Mock\|MagicMock" tests/ --include="*.py" > mock_usage_report.txt
grep -r "from unittest.mock import" tests/ --include="*.py" >> mock_usage_report.txt
```

**중복 패턴 식별**:
- TmuxSession mock 패턴 (가장 빈번)
- ClaudeProcess mock 패턴
- Cache mock 패턴
- SessionManager mock 패턴

### Phase 2: 중앙화 설계 (1시간)
**fixtures/mock_data.py 확장**:
```python
# fixtures/mock_data.py 확장 예시
class MockFactory:
    @staticmethod
    def create_tmux_session(name="test-session", status="active"):
        """표준 TmuxSession mock 생성"""
        pass
    
    @staticmethod  
    def create_claude_process(pid=1234, status="running"):
        """표준 ClaudeProcess mock 생성"""
        pass
```

### Phase 3: 점진적 마이그레이션 (2-3시간)
**우선순위 기반 접근**:
1. **독립적 단위 테스트** 먼저 (위험도 낮음)
2. **통합 테스트**는 나중에 (위험도 높음)
3. **각 파일별 즉시 검증** 필수

**마이그레이션 단계**:
- Mock import 변경
- 기존 mock 정의 제거  
- 표준 mock 팩토리 사용
- 테스트 실행 및 검증

### Phase 4: 검증 및 표준화 (1시간)
- [ ] 전체 테스트 스위트 실행
- [ ] Mock 중복 제거 효과 측정
- [ ] 성능 영향 분석 및 문서 업데이트

## 대상 Mock 패턴

### 1. TmuxSession Mock (최우선)
**현재**: 8개 파일에서 개별 정의
**목표**: 표준 팩토리 메서드로 통합

### 2. ClaudeProcess Mock
**현재**: 5개 파일에서 개별 정의  
**목표**: 파라미터화된 mock 생성

### 3. Cache Mock
**현재**: 4개 파일에서 개별 정의
**목표**: 캐시 전략별 mock 제공

## 위험 요인 및 완화 방안

### 주요 리스크
1. **Mock 동작 차이**: 기존 mock과 새 mock의 미묘한 차이
2. **테스트 의존성**: 특정 mock 동작에 의존하는 테스트
3. **실행 순서**: Mock 초기화 순서로 인한 부작용

### 완화 방안
1. **점진적 적용**: 한 번에 한 파일씩 안전하게 수정
2. **회귀 테스트**: 각 수정 후 즉시 테스트 실행
3. **Git 브랜치**: 안전한 실험 환경 구성

## 선행 조건 ⚠️

**즉시 실행 권장하지 않음**:
- 현재 테스트 성공률 47%로 낮은 상태
- 기본적인 테스트 수정이 우선순위

**최적 실행 타이밍**:
- 테스트 성공률 70% 이상 달성 후
- 기본적인 테스트 오류 수정 완료 후
- 프로젝트 안정화 단계에서 진행

## 성공 기준
- [ ] Mock 중복 코드 50% 이상 감소
- [ ] 테스트 성공률 유지 또는 개선 
- [ ] 테스트 실행 시간 10% 이내 증가
- [ ] 표준 mock 팩토리 구현 완료
- [ ] Mock 사용 가이드라인 문서화

## 예상 효과

### 긍정적 효과
- **일관성 확보**: 모든 테스트에서 동일한 mock 사용
- **유지보수성**: 중앙화된 mock 정의로 관리 용이
- **가독성 향상**: 테스트 파일에서 mock 정의 부분 제거
- **표준화**: Mock 사용 패턴 통일

### 주의사항
- **초기 오버헤드**: 마이그레이션 과정에서 일시적 복잡성 증가
- **학습 곡선**: 새로운 mock 팩토리 사용법 숙지 필요

## 구현 예시

### 중앙화된 Mock 팩토리
```python
# fixtures/mock_data.py
class MockFactory:
    @staticmethod
    def tmux_session(name="test-session", windows=1, status="active"):
        """TmuxSession mock 생성"""
        mock = Mock()
        mock.name = name
        mock.windows = windows
        mock.status = status
        return mock
    
    @staticmethod
    def claude_process(pid=1234, status="running", memory_usage=100):
        """ClaudeProcess mock 생성"""
        mock = Mock()
        mock.pid = pid
        mock.status = status  
        mock.memory_usage = memory_usage
        return mock
```

### 사용 예시
```python
# Before (중복)
mock_session = Mock()
mock_session.name = "test-session"
mock_session.status = "active"

# After (중앙화)
from fixtures.mock_data import MockFactory
mock_session = MockFactory.tmux_session(name="test-session")
```

## 완료 기준
- [ ] 15개 테스트 파일의 중복 mock 제거
- [ ] 표준 mock 팩토리 구현 및 문서화
- [ ] 전체 테스트 성공률 유지
- [ ] Mock 사용 가이드라인 수립
- [ ] 향후 중복 방지 체크리스트 작성

## 주의사항
- 현재 시점에서는 기본 테스트 수정이 우선순위
- 테스트 안정화 후 진행 권장  
- 점진적 접근으로 위험 최소화
- 각 마이그레이션 단계별 즉시 검증 필수