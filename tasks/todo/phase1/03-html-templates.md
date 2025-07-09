# Task 1.3: HTML 템플릿 구조 구현

**예상 시간**: 2시간  
**선행 조건**: Task 1.1 완료  
**우선순위**: 높음

## 목표
대시보드의 기본 HTML 템플릿 구조를 생성하고 레이아웃을 구현한다.

## 작업 내용

### 1. 기본 레이아웃 템플릿
**파일**: `web-dashboard/static/templates/layout.html`

구현 요소:
- HTML5 기본 구조
- 메타 태그 (viewport, charset)
- CSS/JS 링크
- 네비게이션 바
- 메인 컨텐츠 영역
- 푸터
- 다크모드 토글 버튼

### 2. 대시보드 메인 페이지
**파일**: `web-dashboard/static/templates/dashboard.html`

구현 요소:
- layout.html 상속
- 상태 요약 카드 (4개)
- 위젯 컨테이너 구조
- Alpine.js x-data 속성

### 3. 컴포넌트 플레이스홀더
각 위젯이 들어갈 자리 표시:
- `<session-browser></session-browser>`
- `<health-widget></health-widget>`
- `<activity-heatmap></activity-heatmap>`

### 4. 반응형 그리드 레이아웃
- Tailwind CSS 그리드 시스템 활용
- 모바일/태블릿/데스크톱 대응
- 위젯 크기 조정 가능

### 5. 테마 지원
- CSS 변수 활용
- 라이트/다크 테마 클래스
- 테마 전환 스크립트

## 완료 기준
- [x] layout.html 템플릿 완성
- [x] dashboard.html 템플릿 완성
- [x] 반응형 디자인 확인
- [x] 다크모드 토글 작동
- [x] FastAPI에서 템플릿 렌더링 확인

## 테스트
```bash
# 브라우저에서 확인
http://localhost:8000/web/

# 반응형 테스트 (Chrome DevTools)
- Mobile: 375px
- Tablet: 768px
- Desktop: 1024px+
```

## 주의사항
- SEO 고려 (시맨틱 HTML)
- 접근성 고려 (ARIA 속성)
- 로딩 성능 최적화