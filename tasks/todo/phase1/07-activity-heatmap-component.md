# Task 1.7: 활동 히트맵 컴포넌트 구현

**예상 시간**: 3시간  
**선행 조건**: Task 1.4 완료  
**우선순위**: 중간

## 목표
GitHub 스타일의 활동 히트맵 컴포넌트를 구현한다.

## 작업 내용

### 1. ActivityHeatmap 클래스 구현
**파일**: `web-dashboard/static/js/components/activity-heatmap.js`

기본 구조:
```javascript
class ActivityHeatmap extends HTMLElement {
    constructor() {
        super();
        this.activityData = null;
    }
    
    connectedCallback() {}
    async loadActivityData() {}
    render() {}
}

customElements.define('activity-heatmap', ActivityHeatmap);
```

### 2. 히트맵 그리드 생성
- 52주 × 7일 그리드
- 각 셀은 하루를 표현
- 최근 365일 데이터 표시

### 3. 색상 단계 구현
활동량에 따른 5단계 색상:
- 0: 회색 (활동 없음)
- 1-2: 연한 녹색
- 3-5: 녹색
- 6-10: 진한 녹색
- 11+: 매우 진한 녹색

### 4. 요일/월 라벨
- 왼쪽: 요일 라벨 (Sun-Sat)
- 상단: 월 라벨 (매월 첫 주에만)

### 5. 툴팁 기능
각 셀 호버 시:
- 날짜 표시
- 활동 수 표시
- 작은 팝업으로 표시

### 6. 범례 및 통계
- 하단에 색상 범례
- 전체 활동 일수
- 활동률 퍼센트

## 완료 기준
- [ ] ActivityHeatmap 클래스 구현
- [ ] 52×7 그리드 렌더링
- [ ] 색상 단계 적용
- [ ] 요일/월 라벨 표시
- [ ] 툴팁 기능 작동

## 테스트
```javascript
// 샘플 데이터로 테스트
const heatmap = document.querySelector('activity-heatmap');
heatmap.updateActivity({
    activities: [
        { date: "2024-01-01", activity_count: 5 },
        { date: "2024-01-02", activity_count: 3 }
    ]
});
```

## 주의사항
- 날짜 계산 정확성
- 시간대 고려
- 모바일에서도 사용 가능한 크기