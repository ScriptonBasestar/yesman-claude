# API Tech Stack

FastAPI 기반 웹 API 서버의 기술 스택을 설명합니다.

## 🌐 Core API Framework

### 언어 및 프레임워크

- **Python 3.12+**: 메인 개발 언어
- **FastAPI**: 현대적 웹 API 프레임워크
  - 자동 OpenAPI 문서 생성
  - 타입 힌트 기반 데이터 검증
  - 높은 성능 (Starlette + Pydantic 기반)

### 서버 및 배포

- **Uvicorn**: ASGI 서버
  - 비동기 요청 처리
  - 핫 리로드 지원 (개발 모드)

## 📊 API Architecture

### 라우터 구조

```
api/
├── main.py              # FastAPI 앱 진입점
├── models.py            # 데이터 모델 정의
├── requirements.txt     # API 전용 의존성
└── routers/
    ├── sessions.py      # 세션 관리 API
    └── controllers.py   # 컨트롤러 관리 API
```

### 주요 엔드포인트

#### Sessions Router (`/api/sessions`)

- `GET /sessions` - 모든 tmux 세션 조회
- `POST /sessions/{name}` - 특정 세션 생성
- `DELETE /sessions/{name}` - 특정 세션 삭제
- `GET /sessions/{name}/status` - 세션 상태 조회

#### Controllers Router (`/api/controllers`)

- `GET /controllers` - 모든 Claude 컨트롤러 상태 조회
- `POST /controllers/{name}/start` - 컨트롤러 시작
- `POST /controllers/{name}/stop` - 컨트롤러 중지
- `POST /controllers/{name}/restart` - 컨트롤러 재시작

## 🔗 Integration Points

### Python Core Libraries

- **libs.core.session_manager**: 세션 관리 로직
- **libs.core.claude_manager**: Claude 컨트롤러 관리
- **libs.tmux_manager**: Tmux 세션 조작

### 외부 시스템

- **tmux**: 세션 상태 및 조작
- **Claude Code**: 프로세스 모니터링 및 제어

## 🛠️ Development

### 실행 방법

```bash
# 개발 서버 실행
cd api
python -m uvicorn main:app --reload

# 또는 프로젝트 루트에서
uvicorn api.main:app --reload
```

### API 문서 접근

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 📦 Dependencies

### 핵심 의존성

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
```

### 프로젝트 의존성

- **yesman-claude core**: 세션 및 컨트롤러 관리 로직
- **tmux/tmuxp**: 세션 관리 백엔드

## 🔒 Security Considerations

### 현재 구현

- **로컬 접근만**: localhost 바인딩
- **인증 없음**: 로컬 개발용

### 향후 개선 사항

- **API 키 인증**: 외부 접근 시 필요
- **CORS 설정**: 웹 클라이언트 지원
- **Rate Limiting**: 과도한 요청 방지

## 🚀 Production Considerations

### 배포 옵션

- **개발**: `uvicorn --reload`
- **프로덕션**: `uvicorn --workers 4`
- **컨테이너**: Docker + Gunicorn

### 모니터링

- **헬스체크**: `/health` 엔드포인트
- **메트릭**: Prometheus 호환 가능
- **로깅**: 구조화된 JSON 로그

______________________________________________________________________

**마지막 업데이트**: 2025-07-07\
**API 버전**: v1.0\
**호환성**: yesman-claude core v2.0+
