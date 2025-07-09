# Task 1.9: API 통합 및 테스트

**예상 시간**: 2시간  
**선행 조건**: Task 1.2, 1.4-1.7 완료  
**우선순위**: 높음

## 목표
프론트엔드 컴포넌트와 백엔드 API를 통합하고 전체적인 데이터 플로우를 테스트한다.

## 작업 내용

### 1. API 라우터 메인 앱 통합
**파일**: `api/main.py` 수정

```python
from api.routers import dashboard

# 라우터 추가
app.include_router(dashboard.router)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="web-dashboard/static"), name="static")
```

### 2. 실제 데이터 연결
- SessionManager와 연결
- HealthCalculator와 연결
- 실제 git 활동 데이터 수집

### 3. 에러 시나리오 테스트
- 네트워크 오류
- 빈 데이터 응답
- 잘못된 데이터 형식
- 타임아웃

### 4. 로딩 상태 구현
- 각 컴포넌트에 로딩 인디케이터
- 스켈레톤 UI
- 에러 메시지 표시

### 5. 통합 테스트 스크립트
**파일**: `web-dashboard/tests/integration.test.js`

테스트 항목:
- API 엔드포인트 응답
- 컴포넌트 데이터 로딩
- 사용자 인터랙션
- 에러 처리

## 완료 기준
- [ ] API 라우터 메인 앱에 통합
- [ ] 모든 컴포넌트 실제 데이터 표시
- [ ] 로딩 상태 표시
- [ ] 에러 처리 작동
- [ ] 통합 테스트 통과

## 테스트
```bash
# 전체 시스템 실행
uvicorn api.main:app --reload

# 브라우저에서 확인
http://localhost:8000/web/

# 개발자 도구 네트워크 탭에서 API 호출 확인
- /web/api/sessions
- /web/api/health
- /web/api/activity
```

## 주의사항
- CORS 설정 확인
- API 응답 캐싱 고려
- 에러 로깅 구현