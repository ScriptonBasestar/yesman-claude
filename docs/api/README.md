# API 문서

## FastAPI 서버 API

Yesman-Claude의 REST API 엔드포인트에 대한 문서입니다.

### 주요 엔드포인트

API 서버는 `api/` 디렉토리에 위치하며, 다음과 같은 라우터들을 제공합니다:

- **Sessions**: 세션 관리 및 상태 조회
- **Controllers**: Claude 매니저 제어
- **Logs**: 로그 조회 및 관리
- **Config**: 설정 관리

### 실행 방법

```bash
cd api
python -m uvicorn main:app --reload
```

### API 문서 접속

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
