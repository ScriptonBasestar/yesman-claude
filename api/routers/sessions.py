"""Session management API router."""

import os
import sys

import libtmux
from fastapi import APIRouter, HTTPException

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from api import models
from libs.core.session_manager import SessionManager
from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig

router = APIRouter()
sm = SessionManager()
# TmuxManager는 YesmanConfig 객체를 인자로 받으므로, 먼저 생성해줍니다.
config = YesmanConfig()
tm = TmuxManager(config)


def convert_session_to_pydantic(session_data) -> models.SessionInfo:
    """내부 SessionInfo 데이터 클래스를 Pydantic SessionInfo 모델로 변환."""
    # libs.core.models.WindowInfo의 index가 str 타입이므로 int로 변환 필요
    windows = [
        models.WindowInfo(
            index=int(w.index),
            name=w.name,
            panes=[
                models.PaneInfo(
                    command=p.command,
                    is_claude=p.is_claude,
                    is_controller=p.is_controller,
                )
                for p in w.panes
            ],
        )
        for w in session_data.windows
    ]

    return models.SessionInfo(
        session_name=session_data.session_name,
        project_name=session_data.project_name,
        status=session_data.status,
        template=session_data.template,
        windows=windows,
    )


@router.get("/sessions", response_model=list[models.SessionInfo])
def get_all_sessions():
    """모든 tmux 세션의 상세 정보를 조회합니다. (캐시 적용)."""
    try:
        sessions_data = sm.get_all_sessions()
        return [convert_session_to_pydantic(s) for s in sessions_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_name}/info")
def get_session_info(session_name: str):
    """세션의 상세 정보를 조회합니다. (캐시 적용)."""
    try:
        return tm.get_session_info(session_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{project_name}/setup", status_code=204)
def setup_tmux_session(project_name: str):
    """지정된 이름의 프로젝트에 대한 tmux 세션을 설정(생성)합니다."""
    try:
        projects = tm.load_projects().get("sessions", {})
        project_config = projects.get(project_name)

        if not project_config:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{project_name}' not found in projects.yaml",
            )

        # create_session에 실제 세션 이름을 전달
        session_name_for_creation = project_config.get("override", {}).get(
            "session_name",
            project_name,
        )
        tm.create_session(session_name_for_creation, project_config)
        return
    except Exception as e:
        # libtmux가 세션을 생성할 때 발생하는 예외를 그대로 전달
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}",
        )


@router.post("/sessions/{session_name}/start", status_code=204)
def start_session(session_name: str):
    """지정된 세션을 시작합니다."""
    try:
        # 먼저 세션이 이미 실행 중인지 확인
        server = libtmux.Server()
        existing_session = server.sessions.filter(session_name=session_name)

        if existing_session:
            # 이미 존재하는 세션이면 에러 반환
            raise HTTPException(
                status_code=400,
                detail=f"Session '{session_name}' is already running",
            )

        # projects.yaml에서 해당 세션의 설정을 찾기
        projects = tm.load_projects().get("sessions", {})
        project_config = None
        project_name = None

        # 세션명으로 프로젝트 찾기
        for name, config in projects.items():
            session_name_from_config = config.get("override", {}).get(
                "session_name",
                name,
            )
            if session_name_from_config == session_name:
                project_config = config
                project_name = name
                break

        if not project_config:
            raise HTTPException(
                status_code=404,
                detail=f"No project configuration found for session '{session_name}'",
            )

        # 세션 생성 - 실제 세션 이름을 사용
        session_name_for_creation = project_config.get("override", {}).get(
            "session_name",
            project_name,
        )
        tm.create_session(session_name_for_creation, project_config)
        return

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start session: {str(e)}",
        )


@router.post("/sessions/teardown-all", status_code=204)
def teardown_all_sessions():
    """모든 tmux 세션을 종료합니다."""
    try:
        server = libtmux.Server()
        # yesman이 관리하는 세션만 종료하기 위해, projects.yaml 기반으로 필터링
        projects = tm.load_projects().get("sessions", {})
        managed_session_names = [p.get("override", {}).get("session_name", name) for name, p in projects.items()]

        for session in server.sessions:
            if session.name in managed_session_names:
                session.kill_session()

        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
