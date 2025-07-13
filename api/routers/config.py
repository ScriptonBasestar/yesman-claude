import os
import sys

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from libs.yesman_config import YesmanConfig


# API 응답을 위한 Pydantic 모델
class AppConfig(BaseModel):
    log_level: str
    log_path: str
    # 다른 설정들도 필요에 따라 추가
    # 예: confidence_threshold: float


router = APIRouter()
config_manager = YesmanConfig()


@router.get("/config", response_model=AppConfig)
def get_app_config():
    """애플리케이션의 현재 설정을 조회합니다."""
    try:
        # YesmanConfig에서 직접 전체 config 딕셔너리를 가져옵니다.
        # get() 메서드는 특정 키에 대한 값을 가져오므로, 내부 config 객체에 직접 접근합니다.
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
        config_data = config.dict(exclude_unset=True)
        config_manager.save(config_data)
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")
