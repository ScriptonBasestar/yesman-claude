# Task 1.8: CSS 스타일링 완성

**예상 시간**: 2시간  
**선행 조건**: Task 1.3-1.7 완료  
**우선순위**: 중간

## 목표
Tailwind CSS를 활용하여 대시보드의 전체적인 스타일링을 완성한다.

## 작업 내용

### 1. 메인 CSS 파일 구성
**파일**: `web-dashboard/static/css/main.css`

구조:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
    /* 커스텀 컴포넌트 스타일 */
}
```

### 2. 커스텀 컴포넌트 클래스
- `.session-card`: 세션 카드 스타일
- `.health-progress`: 건강도 프로그레스 바
- `.activity-cell`: 히트맵 셀
- `.heatmap-grid`: 히트맵 그리드 레이아웃

### 3. 다크 모드 스타일
- 배경색 전환
- 텍스트 색상 전환
- 보더 색상 조정
- 그림자 조정

### 4. 애니메이션 정의
- 페이드 인/아웃
- 슬라이드 인/아웃
- 프로그레스 바 채우기
- 호버 효과

### 5. 반응형 조정
- 모바일 (< 768px)
- 태블릿 (768px - 1024px)
- 데스크톱 (> 1024px)

## 완료 기준
- [x] main.css 파일 완성
- [x] 모든 컴포넌트 스타일 적용
- [x] 다크 모드 정상 작동
- [x] 애니메이션 부드럽게 작동
- [x] 반응형 디자인 확인

## 테스트
```bash
# Tailwind 빌드
cd web-dashboard
npx tailwindcss -i ./static/css/main.css -o ./static/css/output.css --watch

# 브라우저에서 확인
- 라이트/다크 모드 전환
- 다양한 화면 크기에서 테스트
- 애니메이션 성능 확인
```

## 주의사항
- Tailwind 클래스 우선 사용
- 커스텀 CSS는 최소화
- 성능을 위한 CSS 최적화