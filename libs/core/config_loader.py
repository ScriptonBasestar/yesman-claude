"""Centralized configuration loader with multiple source support"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .config_schema import YesmanConfigSchema


class ConfigSource(ABC):
    """Abstract base class for configuration sources"""

    @abstractmethod
    def load(self) -> dict[str, Any]:
        """Load configuration from this source"""
        pass

    @abstractmethod
    def exists(self) -> bool:
        """Check if this source exists/is available"""
        pass


class YamlFileSource(ConfigSource):
    """YAML file configuration source"""

    def __init__(self, path: Path | str):
        self.path = Path(path).expanduser()

    def load(self) -> dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.exists():
            return {}

        with open(self.path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def exists(self) -> bool:
        """Check if file exists"""
        return self.path.exists() and self.path.is_file()


class EnvironmentSource(ConfigSource):
    """Environment variable configuration source"""

    def __init__(self, prefix: str = "YESMAN_"):
        self.prefix = prefix

    def load(self) -> dict[str, Any]:
        """Load configuration from environment variables"""
        config: dict[str, Any] = {}

        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(self.prefix) :].lower()

                # Handle nested keys (e.g., YESMAN_TMUX_DEFAULT_SHELL -> tmux.default_shell)
                parts = config_key.split("_")
                current = config

                for i, part in enumerate(parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    elif not isinstance(current[part], dict):
                        # Skip if we hit a non-dict value
                        break
                    current = current[part]

                # Set the value, attempting type conversion
                if isinstance(current, dict):
                    current[parts[-1]] = self._convert_value(value)

        return config

    def exists(self) -> bool:
        """Environment source always exists"""
        return True

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        # Try boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value


class DictSource(ConfigSource):
    """Dictionary configuration source (for programmatic config)"""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def load(self) -> dict[str, Any]:
        """Return the dictionary"""
        return self.config.copy()

    def exists(self) -> bool:
        """Dict source always exists"""
        return True


class ConfigLoader:
    """Centralized configuration loader with validation"""

    def __init__(self):
        self._sources: list[ConfigSource] = []
        self._cached_config: YesmanConfigSchema | None = None

    def add_source(self, source: ConfigSource) -> None:
        """Add a configuration source"""
        self._sources.append(source)
        # Invalidate cache when source is added
        self._cached_config = None

    def load(self, validate: bool = True) -> YesmanConfigSchema:
        """Load and merge configurations from all sources"""
        if self._cached_config is not None:
            return self._cached_config

        merged_config: dict[str, Any] = {}

        # Load from each source in order (later sources override earlier ones)
        for source in self._sources:
            if source.exists():
                config = source.load()
                merged_config = self._deep_merge(merged_config, config)

        # Validate if requested
        if validate:
            self._cached_config = self.validate(merged_config)
            return self._cached_config

        # Return unvalidated config wrapped in schema
        self._cached_config = YesmanConfigSchema.model_validate(merged_config)
        return self._cached_config

    def validate(self, config: dict[str, Any]) -> YesmanConfigSchema:
        """Validate configuration against schema"""
        try:
            return YesmanConfigSchema.model_validate(config)
        except ValidationError as e:
            # Re-raise with more context
            errors = []
            for error in e.errors():
                loc = ".".join(str(x) for x in error["loc"])
                msg = error["msg"]
                errors.append(f"  - {loc}: {msg}")

            raise ValueError("Configuration validation failed:\n" + "\n".join(errors)) from e

    def reload(self) -> YesmanConfigSchema:
        """Force reload configuration from all sources"""
        self._cached_config = None
        return self.load()

    def _deep_merge(self, dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries"""
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get_config_sources_info(self) -> list[dict[str, Any]]:
        """Get information about configured sources"""
        info = []
        for i, source in enumerate(self._sources):
            source_info = {
                "index": i,
                "type": source.__class__.__name__,
                "exists": source.exists(),
            }

            if isinstance(source, YamlFileSource):
                source_info["path"] = str(source.path)
            elif isinstance(source, EnvironmentSource):
                source_info["prefix"] = source.prefix

            info.append(source_info)

        return info


def create_default_loader() -> ConfigLoader:
    """Create a ConfigLoader with default sources"""
    loader = ConfigLoader()

    # Add default configuration sources in priority order
    # 1. Default config
    default_config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
    if default_config_path.exists():
        loader.add_source(YamlFileSource(default_config_path))

    # 2. Global config
    global_config = Path.home() / ".scripton" / "yesman" / "yesman.yaml"
    loader.add_source(YamlFileSource(global_config))

    # 3. Local project config
    local_config = Path.cwd() / ".scripton" / "yesman" / "yesman.yaml"
    loader.add_source(YamlFileSource(local_config))

    # 4. Environment-specific config (if YESMAN_ENV is set)
    env = os.environ.get("YESMAN_ENV")
    if env:
        env_config_path = Path(__file__).parent.parent.parent / "config" / f"{env}.yaml"
        if env_config_path.exists():
            loader.add_source(YamlFileSource(env_config_path))

    # 5. Environment variables (highest priority)
    loader.add_source(EnvironmentSource())

    return loader
