from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from pathlib import Path
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from libs.yesman_config import YesmanConfig

router = APIRouter()
config = YesmanConfig()

@router.get("/sessions/{session_name}/logs", response_model=List[str])
def get_session_logs(session_name: str, limit: int = 100):
    """특정 세션의 최근 로그를 조회합니다."""
    try:
        log_path_str = config.get("log_path", "~/tmp/logs/yesman/")
        # 세션 이름에 유효하지 않은 문자가 있을 수 있으므로 정제합니다.
        safe_session_name = "".join(c for c in session_name if c.isalnum() or c in ('-', '_')).rstrip()
        log_file = Path(log_path_str).expanduser() / f"{safe_session_name}.log"

        if not log_file.exists():
            # 컨트롤러 로그가 없을 경우, 메인 로그를 대신 반환해볼 수 있습니다.
            log_file = Path(log_path_str).expanduser() / "yesman.log"
            if not log_file.exists():
                 raise HTTPException(status_code=404, detail=f"Log file for session '{session_name}' not found.")

        with open(log_file, "r", encoding="utf-8") as f:
            # 큰 로그 파일을 효율적으로 읽기 위해 마지막 N줄만 읽는 것이 좋지만,
            # 여기서는 간단하게 모든 줄을 읽고 마지막 부분만 반환합니다.
            lines = f.readlines()
            return lines[-limit:]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {str(e)}") 