"""Utility functions for yesman"""

import logging
import os
from pathlib import Path


def ensure_log_directory(log_path: Path) -> Path:
    """
    Ensure log directory exists with proper permissions.

    Args:
        log_path: Path to the log directory

    Returns:
        Path object for the log directory
    """
    # Expand user path and create directory
    log_path = log_path.expanduser()
    log_path.mkdir(parents=True, exist_ok=True)

    # Set permissions to 750 (rwxr-x---) - more restrictive
    try:
        os.chmod(log_path, 0o700)
    except OSError as e:
        logging.warning(f"Could not set permissions on {log_path}: {e}")

    return log_path


def get_default_log_path() -> Path:
    """Get the default log path for yesman."""
    return Path("~/tmp/logs/yesman/")
