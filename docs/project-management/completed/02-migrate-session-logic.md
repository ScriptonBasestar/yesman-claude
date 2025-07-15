# 2단계: 세션 관리 로직 이전

## 목표

기존 `python_bridge.rs`에 파편화되어 있던 세션 관련 기능들(세션 목록 조회, 생성, 삭제 등)을 FastAPI 서버의 API 엔드포인트로 구현합니다. 이를 통해 모든 클라이언트(Tauri, 웹)가
일관된 방식으로 세션 정보를 관리할 수 있게 합니다.

## 상세 실행 계획

### 1. API 라우터 구조화

로직이 복잡해지는 것을 방지하기 위해 기능별로 라우터 파일을 분리합니다.

- `api/routers/` 디렉터리를 생성합니다.
- `api/routers/sessions.py` 파일을 생성하여 세션 관련 엔드포인트를 모아둡니다.

### 2. Pydantic 모델 정의

API의 요청 및 응답 데이터 형식을 정의하기 위해 `api/models.py` 파일을 생성하고, 기존 `python_bridge.rs`의 Rust 구조체에 대응하는 Pydantic 모델을 작성합니다.

```python
# api/models.py
from pydantic import BaseModel
from typing import List, Optional

class PaneInfo(BaseModel):
    command: str
    is_claude: bool
    is_controller: bool

class WindowInfo(BaseModel):
    index: int
    name: str
    panes: List[PaneInfo]

class SessionInfo(BaseModel):
    session_name: str
    project_name: Optional[str] = None
    status: str
    template: str
    windows: List[WindowInfo]
```

### 3. 세션 관리 엔드포인트 구현

`api/routers/sessions.py` 파일에 기존 `python_bridge.rs`의 함수들에 해당하는 엔드포인트를 구현합니다. 핵심 로직은 기존 `libs.core.session_manager`를 그대로
재사용합니다.

```python
# api/routers/sessions.py
from fastapi import APIRouter
from typing import List
from libs.core.session_manager import SessionManager
from .. import models # api/models.py import

router = APIRouter()
sm = SessionManager()

@router.get("/sessions", response_model=List[models.SessionInfo])
def get_all_sessions():
    """모든 tmux 세션의 상세 정보를 조회합니다."""
    sessions_data = sm.get_all_sessions()
    # 기존 Session 객체를 Pydantic 모델로 변환하는 로직 필요
    # ...
    return sessions_data_as_pydantic_models

@router.post("/sessions/{session_name}/setup", status_code=204)
def setup_tmux_session(session_name: str):
    """지정된 이름의 tmux 세션을 설정합니다."""
    sm.setup_sessions(names=[session_name])
    return

@router.post("/sessions/teardown-all", status_code=204)
def teardown_all_sessions():
    """모든 tmux 세션을 종료합니다."""
    sm.teardown_all_sessions()
    return

# ... 기타 필요한 세션 관련 엔드포인트 추가 ...
```

**주의:** `sm.get_all_sessions()`가 반환하는 객체 타입과 Pydantic `response_model`이 일치해야 합니다. 필요시, 데이터를 Pydantic 모델로 변환하는 단계를 추가해야
합니다.

### 4. 메인 앱에 라우터 등록

`api/main.py` 파일에서 생성한 세션 라우터를 포함시키도록 수정합니다.

```python
# api/main.py
from fastapi import FastAPI
from .routers import sessions # 추가

app = FastAPI()

app.include_router(sessions.router, prefix="/api", tags=["sessions"]) # 추가

@app.get("/")
def read_root():
    return {"message": "Yesman Claude API Server is running!"}
```

- `prefix="/api"`: 모든 세션 관련 엔드포인트는 `/api` 접두사를 갖게 됩니다 (예: `/api/sessions`).
- `tags=["sessions"]`: 자동 생성되는 API 문서에서 엔드포인트를 그룹화합니다.

### 5. 실행 및 API 문서 확인

`pnpm run dev:api`로 서버를 실행하고, 웹 브라우저에서 `http://localhost:8000/docs`에 접속합니다. FastAPI가 자동으로 생성해주는 Swagger UI 화면에서
`/api/sessions` 엔드포인트가 정상적으로 보이는지, "Try it out" 버튼으로 실행했을 때 데이터가 잘 오는지 확인합니다.

## 예상 결과

- 세션 관리 로직이 `api/routers/sessions.py`로 분리됨.
- `GET /api/sessions`, `POST /api/sessions/{name}/setup` 등 RESTful API가 구현됨.
- 자동 생성된 API 문서(`/docs`)를 통해 새로운 엔드포인트를 테스트할 수 있음.
