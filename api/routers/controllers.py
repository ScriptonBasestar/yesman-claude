from fastapi import APIRouter, HTTPException
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from libs.core.claude_manager import ClaudeManager

router = APIRouter()
# ClaudeManager는 싱글턴처럼 동작하며 여러 컨트롤러 인스턴스를 관리합니다.
# 애플리케이션 전체에서 하나의 인스턴스를 공유해야 합니다.
# (여기서는 간단하게 전역 변수로 생성했지만, 실제 프로덕션에서는 Depends 등으로 관리하는 것이 더 좋습니다.)
cm = ClaudeManager()

@router.get("/sessions/{session_name}/controller/status", response_model=str)
def get_controller_status(session_name: str):
    """지정된 세션의 컨트롤러 상태를 조회합니다 ('running' 또는 'stopped')."""
    try:
        controller = cm.get_controller(session_name)
        return "running" if controller.is_running else "stopped"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get controller status: {str(e)}")

@router.post("/sessions/{session_name}/controller/start", status_code=204)
def start_controller(session_name: str):
    """지정된 세션의 컨트롤러를 시작합니다."""
    try:
        controller = cm.get_controller(session_name)
        success = controller.start()
        if not success:
            raise HTTPException(status_code=500, detail="Controller failed to start. The session or pane may not be ready.")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start controller: {str(e)}")

@router.post("/sessions/{session_name}/controller/stop", status_code=204)
def stop_controller(session_name: str):
    """지정된 세션의 컨트롤러를 중지합니다."""
    try:
        controller = cm.get_controller(session_name)
        success = controller.stop()
        if not success:
            raise HTTPException(status_code=500, detail="Controller failed to stop gracefully.")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop controller: {str(e)}")

@router.post("/sessions/{session_name}/controller/restart", status_code=204)
def restart_claude_pane(session_name: str):
    """Claude가 실행 중인 pane을 재시작합니다."""
    try:
        controller = cm.get_controller(session_name)
        success = controller.restart_claude_pane()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to restart Claude pane.")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart Claude pane: {str(e)}") 