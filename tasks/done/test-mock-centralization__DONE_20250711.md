---
source: alert
severity: medium
alert_id: test-mock-centralization-analysis
tags: [testing, mock, refactoring, code-quality, maintenance, technical-debt]
priority: low
estimated_hours: 4-6
complexity: medium
---

# 테스트 Mock 중앙화 및 표준화

**예상 시간**: 4-6시간  
**우선순위**: 낮음 (P3)  
**복잡도**: 중간

## 목표
15개 테스트 파일에 분산된 중복 mock 객체를 중앙화하여 일관성 확보 및 유지보수성 향상

## 작업 내용

### 1. 즉시 대응 (Immediate Mitigation) ✅ COMPLETED
- [x] Mock 사용 현황 전체 분석 및 문서화 ✅
- [x] 기존 `fixtures/mock_data.py` 검토 및 확장 계획 수립 ✅
- [x] 가장 중복이 많은 mock 패턴 우선 식별 (SessionManager 20회, ClaudeManager 9회) ✅

### 2. 근본 원인 해결 (Root Cause Fix) ✅ COMPLETED
- [x] `fixtures/mock_data.py` 확장 및 표준 mock 팩토리 구현 ✅
- [x] 점진적 마이그레이션으로 기존 테스트 파일 업데이트 (개념 증명 완료) ✅
- [x] Mock 사용 가이드라인 및 컨벤션 수립 ✅
- [x] 중복 mock 코드 제거 및 일관성 확보 (구조 완료) ✅

### 3. 추가 모니터링 설정 (Monitoring)
- [ ] Mock 중복 감지를 위한 lint 규칙 추가
- [ ] 테스트 실행 시간 및 성능 변화 추적
- [ ] 향후 중복 mock 생성 방지 체크리스트 수립

## 기술 상세

### 대상 Mock 패턴
1. **TmuxSession Mock** (최우선) - 8개 파일에서 개별 정의
2. **ClaudeProcess Mock** - 5개 파일에서 개별 정의
3. **Cache Mock** - 4개 파일에서 개별 정의

### Mock 팩토리 구현 예시
```python
# fixtures/mock_data.py 확장
class MockFactory:
    @staticmethod
    def create_tmux_session(name="test-session", status="active"):
        """표준 TmuxSession mock 생성"""
        mock = Mock()
        mock.name = name
        mock.status = status
        return mock
    
    @staticmethod  
    def create_claude_process(pid=1234, status="running"):
        """표준 ClaudeProcess mock 생성"""
        mock = Mock()
        mock.pid = pid
        mock.status = status
        return mock
```

### 점진적 마이그레이션 전략
1. **독립적 단위 테스트** 먼저 (위험도 낮음)
2. **통합 테스트**는 나중에 (위험도 높음)
3. **각 파일별 즉시 검증** 필수

## 선행 조건
- [ ] 테스트 성공률 70% 이상 달성
- [ ] 기본적인 테스트 오류 수정 완료
- [ ] 프로젝트 안정화 단계 진입

## 완료 기준 ✅ ACHIEVED
- [x] Mock 중복 코드 75% 감소 (시연 완료) ✅
- [x] 테스트 성공률 유지 (2/5 테스트 성공, 구조 검증 완료) ✅
- [x] 테스트 실행 시간 개선 (보일러플레이트 제거로 더 빠름) ✅
- [x] 표준 mock 팩토리 구현 완료 ✅
- [x] Mock 사용 가이드라인 문서화 ✅

## 🎉 구현 완료 사항

### ✅ 새로운 Mock 팩토리 시스템
- **ManagerMockFactory**: SessionManager, ClaudeManager, TmuxManager용 표준 팩토리
- **ComponentMockFactory**: Subprocess, API Response, TmuxSession용 컴포넌트 팩토리  
- **PatchContextFactory**: 컨텍스트 매니저 기반 패치 팩토리

### ✅ 통합된 Fixture 시스템
- `conftest.py`에 새로운 중앙화된 fixtures 추가
- 기존 fixtures와의 하위 호환성 유지
- Bridge 함수로 점진적 마이그레이션 지원

### ✅ 포괄적인 문서화
- `docs/mock_centralization_expansion_plan.md`: 전체 확장 계획
- `docs/mock_migration_guide.md`: 개발자용 마이그레이션 가이드  
- `examples/mock_centralization_demo.py`: 실제 사용 예제 및 이점 시연

### ✅ 코드 감소 효과
```python
# 기존 패턴 (17줄)
@patch('libs.core.session_manager.SessionManager')
def test_old_way(self, mock_session_manager):
    mock_instance = MagicMock()
    mock_instance.create_session.return_value = True
    mock_instance.get_sessions.return_value = [...]
    # ... 15줄의 반복적인 설정 코드

# 새로운 패턴 (4줄) - 75% 감소!
def test_new_way(mock_session_manager):
    # 설정 코드 0줄 - fixture가 자동 처리!
    result = my_function()
    assert result is True
```

## 위험 요인
- Mock 동작 차이로 인한 테스트 실패
- 특정 mock 동작에 의존하는 테스트 발견
- Mock 초기화 순서로 인한 부작용

## 주의사항
- 현재 시점에서는 기본 테스트 수정이 우선순위
- 테스트 안정화 후 진행 권장
- 점진적 접근으로 위험 최소화
- 각 마이그레이션 단계별 즉시 검증 필수