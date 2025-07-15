# 3단계: 컨트롤러 관리 로직 이전

## 목표

Claude 컨트롤러의 상태를 조회하고 제어(시작, 중지, 재시작)하는 기능들을 FastAPI 서버의 API 엔드포인트로 이전합니다.

## 상세 실행 계획

### 1. 컨트롤러 라우터 파일 생성

`api/routers/` 디렉터리에 `controllers.py` 파일을 생성하여 컨트롤러 관련 엔드포인트를 분리합니다.

### 2. 컨트롤러 관리 엔드포인트 구현

`api/routers/controllers.py` 파일에 컨트롤러 제어 관련 엔드포인트를 구현합니다. 핵심 로직은 `libs.core.claude_manager` 모듈을 재사용합니다.

```python
# api/routers/controllers.py
from fastapi import APIRouter, HTTPException
from libs.core.claude_manager import ClaudeManager

router = APIRouter()
cm = ClaudeManager()

@router.get("/sessions/{session_name}/controller/status", response_model=str)
def get_controller_status(session_name: str):
    """지정된 세션의 컨트롤러 상태를 조회합니다."""
    # 이 부분은 claude_manager의 실제 구현에 따라 달라질 수 있습니다.
    # get_controller가 None을 반환할 수 있으므로 예외 처리가 필요합니다.
    controller = cm.get_controller(session_name)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")
    
    if controller.is_running:
        return "running"
    return "stopped"

@router.post("/sessions/{session_name}/controller/start", status_code=204)
def start_controller(session_name: str):
    """컨트롤러를 시작합니다."""
    controller = cm.get_controller(session_name)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")
    
    success = controller.start()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start controller")
    return

@router.post("/sessions/{session_name}/controller/stop", status_code=204)
def stop_controller(session_name: str):
    """컨트롤러를 중지합니다."""
    controller = cm.get_controller(session_name)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")
        
    success = controller.stop()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop controller")
    return

@router.post("/sessions/{session_name}/controller/restart", status_code=204)
def restart_claude_pane(session_name: str):
    """Claude가 실행 중인 pane을 재시작합니다."""
    controller = cm.get_controller(session_name)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")

    success = controller.restart_claude_pane()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to restart Claude pane")
    return
```

### 3. 메인 앱에 라우터 등록

`api/main.py` 파일에 컨트롤러 라우터를 추가합니다.

```python
# api/main.py
from fastapi import FastAPI
from .routers import sessions, controllers # controllers 추가

app = FastAPI()

app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(controllers.router, prefix="/api", tags=["controllers"]) # 추가

@app.get("/")
def read_root():
    return {"message": "Yesman Claude API Server is running!"}

```

### 4. 실행 및 API 문서 확인

서버를 재시작(`pnpm run dev:api`)하고, `http://localhost:8000/docs`에서 새로 추가된 컨트롤러 관련 엔드포인트들을 확인하고 테스트합니다.

## 예상 결과

- 컨트롤러 제어 로직이 `api/routers/controllers.py`로 분리됨.
- `GET /api/sessions/{name}/controller/status`, `POST /api/sessions/{name}/controller/start` 등 컨트롤러 관리를 위한 RESTful API가
  구현됨.
- API 문서를 통해 컨트롤러 관련 엔드포인트를 테스트할 수 있음.
