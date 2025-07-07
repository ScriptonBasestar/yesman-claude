#!/usr/bin/env python3
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from .utils import ensure_log_directory

class YesmanConfig:
    def __init__(self):
        self.global_path = Path.home() / ".yesman" / "yesman.yaml"
        self.local_path = Path.cwd() / ".yesman" / "yesman.yaml"
        self.config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        global_cfg: Dict[str, Any] = {}
        local_cfg: Dict[str, Any] = {}
        
        if self.global_path.exists():
            with open(self.global_path, "r", encoding="utf-8") as f:
                global_cfg = yaml.safe_load(f) or {}
        
        if self.local_path.exists():
            with open(self.local_path, "r", encoding="utf-8") as f:
                local_cfg = yaml.safe_load(f) or {}
        
        mode = local_cfg.get("mode", "merge")
        
        if mode == "local":
            if not local_cfg:
                raise RuntimeError(f"mode: local but {self.local_path} doesn't exist or is empty")
            return local_cfg
        elif mode == "merge":
            merged = {**global_cfg, **local_cfg}
            return merged
        else:
            raise ValueError(f"Unsupported mode: {mode}")
    
    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO").upper()
        log_path_str = self.config.get("log_path", "~/tmp/logs/yesman/")
        log_path = ensure_log_directory(Path(log_path_str))
        
        log_file = log_path / "yesman.log"
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file)
            ]
        )
        self.logger = logging.getLogger("yesman")
        self.logger.info(f"Yesman started with log level: {log_level}")
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def save(self, new_config_data: Dict[str, Any]):
        """Saves the configuration updates to the local yesman.yaml file."""
        current_local_cfg: Dict[str, Any] = {}
        if self.local_path.exists():
            with open(self.local_path, "r", encoding="utf-8") as f:
                current_local_cfg = yaml.safe_load(f) or {}

        # Update the loaded local config with the new data
        updated_local_cfg = {**current_local_cfg, **new_config_data}

        # Ensure the directory exists
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.local_path, "w", encoding="utf-8") as f:
            yaml.dump(updated_local_cfg, f, default_flow_style=False)
        
        # Reload the in-memory config to reflect the changes
        self.config = self._load_config()