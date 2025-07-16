#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Any

import yaml

from .utils import ensure_log_directory


class YesmanConfig:
    def __init__(self):
        self.root_dir = Path.home() / ".scripton" / "yesman"
        self.global_path = self.root_dir / "yesman.yaml"
        self.local_path = Path.cwd() / ".scripton" / "yesman" / "yesman.yaml"
        self.config = self._load_config()
        self._setup_logging()
        # 필요한 디렉토리 생성
        self._ensure_directories()

    def _load_config(self) -> dict[str, Any]:
        global_cfg: dict[str, Any] = {}
        local_cfg: dict[str, Any] = {}

        if self.global_path.exists():
            with open(self.global_path, encoding="utf-8") as f:
                global_cfg = yaml.safe_load(f) or {}

        if self.local_path.exists():
            with open(self.local_path, encoding="utf-8") as f:
                local_cfg = yaml.safe_load(f) or {}

        mode = local_cfg.get("mode", "merge")

        if mode in {"isolated", "local"}:  # Support both for backward compatibility
            if not local_cfg or (len(local_cfg) == 1 and "mode" in local_cfg):
                raise RuntimeError(f"mode: {mode} but {self.local_path} doesn't exist or is empty")
            return local_cfg
        elif mode == "merge":
            merged = {**global_cfg, **local_cfg}
            return merged
        else:
            raise ValueError(f"Unsupported mode: {mode}")

    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO").upper()
        log_path_str = self.config.get("log_path", "~/.scripton/yesman/logs/")
        log_path = ensure_log_directory(Path(log_path_str))

        log_file = log_path / "yesman.log"

        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
            ],
        )
        self.logger = logging.getLogger("yesman")
        self.logger.info(f"Yesman started with log level: {log_level}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def save(self, new_config_data: dict[str, Any]):
        """Saves the configuration updates to the local yesman.yaml file."""
        current_local_cfg: dict[str, Any] = {}
        if self.local_path.exists():
            with open(self.local_path, encoding="utf-8") as f:
                current_local_cfg = yaml.safe_load(f) or {}

        # Update the loaded local config with the new data
        updated_local_cfg = {**current_local_cfg, **new_config_data}

        # Ensure the directory exists
        self.local_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.local_path, "w", encoding="utf-8") as f:
            yaml.dump(updated_local_cfg, f, default_flow_style=False)

        # Reload the in-memory config to reflect the changes
        self.config = self._load_config()
    
    def _ensure_directories(self):
        """필요한 디렉토리들을 생성합니다."""
        directories = [
            self.root_dir,
            self.root_dir / "sessions",
            self.root_dir / "templates",
            self.root_dir / "logs",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_sessions_dir(self) -> Path:
        """세션 설정 파일들이 저장되는 디렉토리를 반환합니다."""
        return self.root_dir / "sessions"
    
    def get_templates_dir(self) -> Path:
        """템플릿 파일들이 저장되는 디렉토리를 반환합니다."""
        return self.root_dir / "templates"
