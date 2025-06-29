"""Dashboard runner module"""

import logging
from pathlib import Path

from libs.yesman_config import YesmanConfig
from .app import DashboardApp
from ..utils import ensure_log_directory


class Dashboard:
    """Dashboard runner class for backward compatibility"""
    
    def __init__(self):
        self.config = YesmanConfig()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file-only output"""
        logger = logging.getLogger("yesman.dashboard")
        logger.propagate = False
        
        log_path_str = self.config.get("log_path", "~/tmp/logs/yesman/")
        log_path = ensure_log_directory(Path(log_path_str))
        
        log_file = log_path / "dashboard.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logger.level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def run_dashboard(self, refresh_interval: float = 2.0):
        """Run the dashboard with periodic updates using textual"""
        self.logger.info("Starting yesman dashboard")
        app = DashboardApp()
        app.run()


def run_dashboard(refresh_interval: float = 2.0):
    """Run the dashboard"""
    dashboard = Dashboard()
    dashboard.run_dashboard(refresh_interval)