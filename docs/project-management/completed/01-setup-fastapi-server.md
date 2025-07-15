# 1단계: FastAPI 서버 기본 구조 설정

## 목표

프로젝트의 새로운 백엔드 코어를 담당할 FastAPI 애플리케이션의 기본 골격을 생성합니다. 이 서버는 향후 모든 비즈니스 로직과 상태 관리를 책임지게 됩니다.

## 상세 실행 계획

### 1. API 서버 디렉터리 생성

프로젝트 루트에 API 서버 코드를 담을 `api` 디렉터리를 생성합니다.

```bash
mkdir api
cd api
```

### 2. FastAPI 기본 파일 생성

`api` 디렉터리 내에 다음 파일들을 생성합니다.

- `main.py`: FastAPI 앱의 주 진입점(entrypoint) 파일.
- `requirements.txt`: Python 의존성을 관리할 파일.

### 3. 의존성 정의

`api/requirements.txt` 파일에 다음의 필수 의존성을 추가합니다.

```
fastapi
uvicorn[standard]
pydantic
```

- `fastapi`: 핵심 웹 프레임워크.
- `uvicorn`: 고성능 ASGI 서버.
- `pydantic`: 데이터 유효성 검사 및 모델 정의.

### 4. "Hello World" 엔드포인트 작성

`api/main.py` 파일에 서버가 정상적으로 동작하는지 확인할 수 있는 가장 간단한 API 엔드포인트를 작성합니다.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Yesman Claude API Server is running!"}
```

### 5. 가상 환경 설정 및 의존성 설치

터미널에서 `api` 디렉터리로 이동하여 Python 가상 환경을 설정하고 `requirements.txt`에 명시된 패키지들을 설치합니다.

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6. 개발 서버 실행 스크립트 추가

프로젝트 루트의 `package.json` 파일의 `scripts` 섹션에 FastAPI 개발 서버를 쉽게 실행할 수 있는 명령어를 추가합니다.

```json
// package.json
"scripts": {
  // ... 기존 스크립트들
  "dev:api": "uvicorn api.main:app --reload --port 8000"
},
```

- `--reload`: 코드가 변경될 때마다 서버가 자동으로 재시작됩니다.
- `--port 8000`: API 서버가 8000번 포트에서 실행됩니다.

### 7. 실행 확인

프로젝트 루트에서 다음 명령어를 실행하여 API 서버가 정상적으로 구동되는지 확인합니다.

```bash
pnpm run dev:api
```

터미널에 uvicorn 서버가 실행 중이라는 로그가 나타나고, 웹 브라우저에서 `http://localhost:8000`에 접속했을 때
`{"message": "Yesman Claude API Server is running!"}` 메시지가 보이면 성공입니다.

## 예상 결과

- `api` 디렉터리와 그 안에 `main.py`, `requirements.txt`, `.venv`가 생성됨.
- `pnpm run dev:api` 명령으로 FastAPI 개발 서버를 실행할 수 있음.
- API 서버가 `http://localhost:8000`에서 정상적으로 응답함.
