# Task 1.6: 프로젝트 건강도 위젯 구현

**예상 시간**: 2.5시간  
**선행 조건**: Task 1.4 완료  
**우선순위**: 중간

## 목표
프로젝트 건강도를 시각적으로 표시하는 위젯 컴포넌트를 구현한다.

## 작업 내용

### 1. HealthWidget 클래스 구현
**파일**: `web-dashboard/static/js/components/health-widget.js`

기본 구조:
```javascript
class HealthWidget extends HTMLElement {
    constructor() {
        super();
        this.health = null;
    }
    
    connectedCallback() {}
    async loadHealth() {}
    render() {}
}

customElements.define('health-widget', HealthWidget);
```

### 2. 전체 점수 표시
- 큰 숫자로 점수 표시 (0-100)
- 점수에 따른 색상 변경
  - 80+: 녹색
  - 60-79: 노란색
  - 0-59: 빨간색

### 3. 카테고리별 점수
8개 카테고리 각각:
- 카테고리 이름
- 프로그레스 바
- 점수 숫자
- 색상 코딩

### 4. 개선 제안사항
- 최대 3개까지 표시
- 노란색 배경의 알림 박스
- 리스트 형태로 표시

### 5. 애니메이션
- 프로그레스 바 채우기 애니메이션
- 숫자 카운트업 효과 (선택사항)

## 완료 기준
- [x] HealthWidget 클래스 구현
- [x] 전체 점수 표시
- [x] 카테고리별 점수 표시
- [x] 제안사항 표시
- [x] 색상 코딩 적용

## 테스트
```javascript
// 컴포넌트 테스트
const widget = document.querySelector('health-widget');
widget.updateHealth({
    overall_score: 85,
    categories: {
        build: 90,
        tests: 80
    },
    suggestions: ["Increase test coverage"]
});
```

## 주의사항
- 반응형 디자인 고려
- 접근성 (ARIA) 속성 추가
- 성능 점수 변화 시 부드러운 전환