#!/usr/bin/env python3
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

class YesmanConfig:
    def __init__(self):
        self.config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        global_path = Path.home() / ".yesman" / "yesman.yaml"
        local_path = Path.cwd() / ".yesman" / "yesman.yaml"
        
        global_cfg: Dict[str, Any] = {}
        local_cfg: Dict[str, Any] = {}
        
        if global_path.exists():
            with open(global_path, "r", encoding="utf-8") as f:
                global_cfg = yaml.safe_load(f) or {}
        
        if local_path.exists():
            with open(local_path, "r", encoding="utf-8") as f:
                local_cfg = yaml.safe_load(f) or {}
        
        mode = local_cfg.get("mode", "merge")
        
        if mode == "local":
            if not local_cfg:
                raise RuntimeError(f"mode: local but {local_path} doesn't exist or is empty")
            return local_cfg
        elif mode == "merge":
            merged = {**global_cfg, **local_cfg}
            return merged
        else:
            raise ValueError(f"Unsupported mode: {mode}")
    
    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO").upper()
        log_path = self.config.get("log_path", "~/tmp/logs/yesman/")
        log_path = Path(os.path.expanduser(log_path))
        log_path.mkdir(parents=True, exist_ok=True)
        
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