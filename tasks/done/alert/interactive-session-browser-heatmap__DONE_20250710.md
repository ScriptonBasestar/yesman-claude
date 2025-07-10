# 인터랙티브 세션 브라우저 - 히트맵 구현

## 작업 개요
**상태**: 📋 대기중  
**우선순위**: HIGH  
**예상 소요시간**: 3-4시간  
**관련 컴포넌트**: `libs/dashboard/widgets/activity_heatmap.py`

## 목표
세션별 활성도를 시각적 히트맵으로 표시하여 프로젝트별 활동 패턴을 한눈에 파악 가능하게 구현

## 상세 요구사항

### 기능 요구사항
- ✅ **시간대별 활성도 표시**: 24시간 × 7일 그리드 형태의 히트맵
- ✅ **세션별 필터링**: 특정 세션만 선택하여 활성도 확인
- ✅ **색상 코딩**: 활성도 강도에 따른 그라데이션 색상 (초록 → 노랑 → 빨강)
- ✅ **툴팁 정보**: 마우스 오버 시 구체적인 활동 시간 및 명령어 수 표시

### 기술 요구사항
- **프론트엔드**: SvelteKit 컴포넌트 (`SessionHeatmap.svelte`)
- **백엔드**: Python 데이터 처리 (`libs/dashboard/widgets/activity_heatmap.py`)
- **데이터 수집**: tmux 세션 활동 로그 분석
- **실시간 업데이트**: 5초 간격으로 히트맵 데이터 갱신

## 구현 계획

### 1단계: 데이터 수집 엔진 (1시간)
```python
# libs/dashboard/widgets/activity_heatmap.py
class ActivityHeatmapGenerator:
    def collect_session_activity(self, session_name: str, time_range: str) -> Dict:
        # tmux 세션의 활동 로그 수집
        # 시간대별 명령어 실행 횟수 및 활성 시간 계산
        pass
    
    def generate_heatmap_data(self, sessions: List[str]) -> Dict:
        # 히트맵 렌더링용 데이터 생성
        # 24x7 그리드 형태로 정규화
        pass
```

### 2단계: API 엔드포인트 구현 (30분)
```python
# api/routers/dashboard.py
@router.get("/heatmap/{session_name}")
async def get_session_heatmap(session_name: str, days: int = 7):
    # 세션별 히트맵 데이터 반환
    pass
```

### 3단계: 프론트엔드 컴포넌트 (2시간)
```svelte
<!-- tauri-dashboard/src/lib/components/dashboard/SessionHeatmap.svelte -->
<script>
  // D3.js 또는 Chart.js를 사용한 히트맵 시각화
  // 실시간 데이터 업데이트 로직
</script>
```

### 4단계: 대시보드 통합 (30분)
- 메인 대시보드에 히트맵 위젯 추가
- 세션 선택 필터와 연동
- 반응형 레이아웃 적용

## 성공 기준
- [ ] 최근 7일간 세션 활동이 히트맵으로 정확히 표시됨
- [ ] 사용자가 특정 시간대 클릭 시 상세 활동 정보 표시
- [ ] 5초 이내에 히트맵 데이터 로딩 완료
- [ ] 다중 세션 선택 시 통합 히트맵 표시 가능

## 의존성
- **선행 작업**: 세션 모니터링 시스템 구축 완료
- **연관 작업**: 키보드 네비게이션 구현과 UI 통합 필요

## 참고사항
- GitHub 스타일 기여도 그래프를 참고하여 직관적인 UI 설계
- 모바일 환경에서도 터치 인터랙션 지원
- 다크모드/라이트모드 테마 대응

**처리 상태**: ✅ **converted**  
**새 파일**: `/tasks/todo/interactive-session-heatmap.md`  
**전환 일시**: 2025-07-10  
**우선순위 재평가**: HIGH → MEDIUM (기본 기능 완성 후 진행)

---
*이 작업은 사용자 경험 개선의 핵심 기능으로 높은 우선순위를 가집니다.*