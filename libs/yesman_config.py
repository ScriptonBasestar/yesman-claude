#!/usr/bin/env python3

# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Yesman configuration management using centralized config loader."""

import logging
from pathlib import Path
from typing import Any, cast

import yaml

from .core.config_loader import (
    ConfigLoader,
    DictSource,
    create_cached_config_loader,
    create_default_loader,
)
from .core.config_schema import YesmanConfigSchema
from .utils import ensure_log_directory


class YesmanConfig:
    """Main configuration class for Yesman.

    This class provides backward compatibility while using the new
    centralized configuration management system.
    """

    def __init__(self, config_loader: ConfigLoader | None = None) -> None:
        """Initialize YesmanConfig.

        Args:
            config_loader: Optional custom config loader. If not provided,
                         uses the default loader with standard sources.
        """
        # Use provided loader or create default
        self._loader = config_loader or create_default_loader()

        # Load configuration
        self._config_schema = self._loader.load()

        # Setup paths for backward compatibility
        self.root_dir = Path(self._config_schema.root_dir).expanduser()
        self.global_path = self.root_dir / "yesman.yaml"
        self.local_path = Path.cwd() / ".scripton" / "yesman" / "yesman.yaml"

        # Convert schema to dict for backward compatibility
        self.config = self._config_schema.model_dump()

        # Setup logging
        self._setup_logging()

        # Ensure necessary directories exist
        self._ensure_directories()

        # Store logger
        self.logger = logging.getLogger("yesman")
        self.logger.info("Yesman configuration loaded successfully")

    def _setup_logging(self) -> None:
        """Setup logging based on configuration."""
        log_config = self._config_schema.logging
        log_path = ensure_log_directory(Path(log_config.log_path))
        log_file = log_path / "yesman.log"

        # Configure logging
        handlers: list[logging.Handler] = [logging.FileHandler(log_file)]

        # Add console handler in development mode
        if self._config_schema.logging.level == "DEBUG":
            handlers.append(logging.StreamHandler())

        logging.basicConfig(
            level=getattr(logging, log_config.level),
            format=log_config.format,
            handlers=handlers,
        )

    def _ensure_directories(self) -> None:
        """Create necessary directories."""
        directories = [
            self.root_dir,
            self.root_dir / self._config_schema.session.sessions_dir,
            self.root_dir / self._config_schema.session.templates_dir,
            Path(self._config_schema.logging.log_path).expanduser(),
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: object = None) -> object:
        """Get configuration value by key (backward compatibility).

        Supports dot notation for nested values (e.g., 'tmux.default_shell')

        Returns:
            Description of return value
        """
        # Handle dot notation
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def save(self, new_config_data: dict[str, Any]) -> None:
        """Save configuration updates to local file."""
        # Load current local config
        current_local_cfg: dict[str, Any] = {}
        if self.local_path.exists():
            with open(self.local_path, encoding="utf-8") as f:
                current_local_cfg = yaml.safe_load(f) or {}

        # Merge with new data
        updated_local_cfg = {**current_local_cfg, **new_config_data}

        # Ensure directory exists
        self.local_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to file
        with open(self.local_path, "w", encoding="utf-8") as f:
            yaml.dump(updated_local_cfg, f, default_flow_style=False)

        # Reload configuration
        # Add the new local config as a source and reload
        self._loader.add_source(DictSource(new_config_data))
        self._config_schema = self._loader.reload()
        self.config = self._config_schema.model_dump()

    def get_sessions_dir(self) -> Path:
        """Get sessions directory path."""
        return self.root_dir / self._config_schema.session.sessions_dir

    def get_templates_dir(self) -> Path:
        """Get templates directory path."""
        return self.root_dir / self._config_schema.session.templates_dir

    def get_projects_file(self) -> Path:
        """Get projects file path."""
        return self.get_sessions_dir() / self._config_schema.session.projects_file

    def reload(self) -> None:
        """Reload configuration from all sources."""
        self._config_schema = self._loader.reload()
        self.config = self._config_schema.model_dump()
        self.logger.info("Configuration reloaded")

    def validate(self) -> bool:
        """Validate current configuration."""
        try:
            self._loader.validate(self.config)
            return True
        except ValueError:
            self.logger.exception("Configuration validation failed")  # noqa: G004
            return False

    @property
    def schema(self) -> YesmanConfigSchema:
        """Get typed configuration schema."""
        return self._config_schema

    def get_cache_stats(self) -> dict[str, Any] | None:
        """Get cache statistics if using cached loader."""
        if hasattr(self._loader, "get_cache_stats"):
            return self._loader.get_cache_stats()  # type: ignore[no-any-return]
        return None

    def invalidate_cache(self) -> None:
        """Invalidate configuration cache if using cached loader."""
        if hasattr(self._loader, "invalidate_cache"):
            self._loader.invalidate_cache()

    def __repr__(self) -> str:
        """String representation."""
        sources = self._loader.get_config_sources_info()
        cache_info = " (cached)" if hasattr(self._loader, "get_cache_stats") else ""
        return f"YesmanConfig(sources={len(sources)}, mode={self._config_schema.mode}){cache_info}"


def create_cached_yesman_config(cache_ttl: float = 300.0) -> YesmanConfig:
    """Create a YesmanConfig instance with caching enabled.

    Args:
        cache_ttl: Cache time-to-live in seconds (default: 5 minutes)

    Returns:
        YesmanConfig instance with caching enabled
    """
    cached_loader = create_cached_config_loader(cache_ttl=cache_ttl)
    return YesmanConfig(config_loader=cast(ConfigLoader, cached_loader))
