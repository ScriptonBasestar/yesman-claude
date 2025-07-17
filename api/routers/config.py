from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from libs.core.services import get_config, get_tmux_manager


# API 응답을 위한 Pydantic 모델
class AppConfig(BaseModel):
    log_level: str
    log_path: str
    # 다른 설정들도 필요에 따라 추가
    # 예: confidence_threshold: float


router = APIRouter()


@router.get("/config", response_model=AppConfig)
def get_app_config():
    """애플리케이션의 현재 설정을 조회합니다."""
    try:
        # DI 컨테이너에서 YesmanConfig 인스턴스를 가져옵니다.
        config_manager = get_config()
        current_config = config_manager.config
        return AppConfig(**current_config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


# TODO: POST 엔드포인트를 만들어 YesmanConfig에 저장하는 로직이 필요합니다.
#       YesmanConfig에 save 메서드를 추가해야 합니다.
@router.post("/config", status_code=204)
def save_app_config(config: AppConfig):
    """애플리케이션 설정을 저장합니다."""
    try:
        config_manager = get_config()
        config_data = config.dict(exclude_unset=True)
        config_manager.save(config_data)
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")


@router.get("/config/projects", response_model=list[str])
def get_available_projects():
    """세션 설정에 정의된 모든 프로젝트 목록을 반환합니다."""
    try:
        tm = get_tmux_manager()
        projects = tm.load_projects().get("sessions", {})
        return list(projects.keys())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")


@router.get("/config/session-files", response_model=list[str])
def list_session_files():
    """사용 가능한 세션 설정 파일 목록을 반환합니다."""
    try:
        tm = get_tmux_manager()
        return tm.list_session_configs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list session files: {str(e)}")


@router.get("/config/paths", response_model=dict[str, str])
def get_config_paths():
    """설정 파일 경로 정보를 반환합니다."""
    try:
        config_manager = get_config()
        tm = get_tmux_manager()
        return {
            "root_dir": str(config_manager.root_dir),
            "sessions_dir": str(tm.sessions_path),
            "templates_dir": str(tm.templates_path),
            "global_config": str(config_manager.global_path),
            "local_config": str(config_manager.local_path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config paths: {str(e)}")
