# Task 1.2: FastAPI 라우터 구현

**예상 시간**: 2.5시간  
**선행 조건**: Task 1.1 완료  
**우선순위**: 높음

## 목표
웹 대시보드를 위한 FastAPI 라우터를 구현하고 기본 엔드포인트를 생성한다.

## 작업 내용

### 1. 기본 라우터 파일 생성
**파일**: `api/routers/dashboard.py`

구현 내용:
- `/web/` - 메인 대시보드 페이지
- `/web/api/sessions` - 세션 목록 API
- `/web/api/health` - 프로젝트 건강도 API
- `/web/api/activity` - 활동 데이터 API
- `/web/api/stats` - 통계 요약 API

### 2. Jinja2 템플릿 설정
```python
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="web-dashboard/static/templates")
```

### 3. 정적 파일 서빙 설정
```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="web-dashboard/static"), name="static")
```

### 4. 세션 매니저 통합
- SessionManager 인스턴스 생성
- 세션 데이터를 웹 형식으로 변환
- 캐시된 세션 정보 활용

### 5. API 응답 형식 정의
- 일관된 JSON 응답 구조
- 에러 핸들링
- CORS 설정 (필요시)

## 완료 기준
- [ ] FastAPI 라우터 파일 생성
- [ ] 5개 엔드포인트 모두 구현
- [ ] 템플릿 렌더링 테스트
- [ ] API 응답 테스트
- [ ] 에러 핸들링 구현

## 테스트
```bash
# FastAPI 서버 실행
cd api
uvicorn main:app --reload

# API 테스트
curl http://localhost:8000/web/api/sessions
curl http://localhost:8000/web/api/health
```

## 주의사항
- 기존 SessionManager와 호환성 유지
- API 응답 시간 100ms 이내 목표
- 에러 상황에 대한 적절한 HTTP 상태 코드 반환