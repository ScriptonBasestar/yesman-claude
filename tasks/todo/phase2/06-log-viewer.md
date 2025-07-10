# Task 2.6: 실시간 로그 뷰어 구현

**예상 시간**: 2.5시간  
**선행 조건**: Task 2.3 완료  
**우선순위**: 중간

## 목표
실시간으로 로그를 스트리밍하고 표시하는 로그 뷰어 컴포넌트를 구현한다.

## 작업 내용

### 1. LogViewer 컴포넌트
**파일**: `web-dashboard/static/js/components/log-viewer.js`

기본 구조:
```javascript
class LogViewer extends HTMLElement {
    constructor() {
        super();
        this.logs = [];
        this.maxLogs = 1000;
        this.filters = {};
        this.isPaused = false;
    }
}
```

### 2. 로그 필터링
필터 옵션:
- 로그 레벨 (debug, info, warning, error)
- 소스별 필터
- 텍스트 검색
- 시간 범위

### 3. 컨트롤 바
- 일시정지/재개 버튼
- 로그 지우기 버튼
- 필터 드롭다운
- 자동 스크롤 토글

### 4. 로그 표시
- 로그 레벨별 색상 코딩
- 타임스탬프 표시
- 소스 표시
- 메시지 하이라이팅

### 5. 성능 최적화
- 가상 스크롤링 (많은 로그)
- 최대 로그 수 제한
- 오래된 로그 자동 제거

## 완료 기준
- [x] LogViewer 컴포넌트 구현
- [x] 실시간 로그 수신 및 표시
- [x] 필터링 기능 작동
- [x] 컨트롤 기능 구현
- [x] 성능 최적화 적용

## 테스트
```javascript
// 로그 추가 테스트
const viewer = document.querySelector('log-viewer');
viewer.addLog({
    level: 'info',
    timestamp: new Date().toISOString(),
    source: 'test',
    message: 'Test log message'
});

// 필터 테스트
viewer.setFilter('level', 'error');
```

## 주의사항
- 대량 로그 처리 시 성능
- 메모리 사용량 관리
- 로그 포맷 일관성