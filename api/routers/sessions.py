from fastapi import APIRouter, HTTPException
from typing import List
import sys
import os
import libtmux

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from libs.core.session_manager import SessionManager
from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig
from api import models

router = APIRouter()
sm = SessionManager()
# TmuxManager는 YesmanConfig 객체를 인자로 받으므로, 먼저 생성해줍니다.
config = YesmanConfig()
tm = TmuxManager(config)

def convert_session_to_pydantic(session_data) -> models.SessionInfo:
    """내부 SessionInfo 데이터 클래스를 Pydantic SessionInfo 모델로 변환"""
    # libs.core.models.WindowInfo의 index가 str 타입이므로 int로 변환 필요
    windows = [
        models.WindowInfo(
            index=int(w.index),
            name=w.name,
            panes=[
                models.PaneInfo(
                    command=p.command,
                    is_claude=p.is_claude,
                    is_controller=p.is_controller
                ) for p in w.panes
            ]
        ) for w in session_data.windows
    ]

    return models.SessionInfo(
        session_name=session_data.session_name,
        project_name=session_data.project_name,
        status=session_data.status,
        template=session_data.template,
        windows=windows
    )

@router.get("/sessions", response_model=List[models.SessionInfo])
def get_all_sessions():
    """모든 tmux 세션의 상세 정보를 조회합니다."""
    try:
        sessions_data = sm.get_all_sessions()
        return [convert_session_to_pydantic(s) for s in sessions_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{project_name}/setup", status_code=204)
def setup_tmux_session(project_name: str):
    """지정된 이름의 프로젝트에 대한 tmux 세션을 설정(생성)합니다."""
    try:
        projects = tm.load_projects().get("sessions", {})
        project_config = projects.get(project_name)
        
        if not project_config:
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found in projects.yaml")
        
        # create_session의 두 번째 인자는 config 딕셔너리입니다.
        tm.create_session(project_name, project_config)
        return
    except Exception as e:
        # libtmux가 세션을 생성할 때 발생하는 예외를 그대로 전달
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.post("/sessions/teardown-all", status_code=204)
def teardown_all_sessions():
    """모든 tmux 세션을 종료합니다."""
    try:
        server = libtmux.Server()
        # yesman이 관리하는 세션만 종료하기 위해, projects.yaml 기반으로 필터링
        projects = tm.load_projects().get("sessions", {})
        managed_session_names = [
            p.get("override", {}).get("session_name", name) for name, p in projects.items()
        ]

        for session in server.sessions:
            if session.name in managed_session_names:
                session.kill_session()
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 