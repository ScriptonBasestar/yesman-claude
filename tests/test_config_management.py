"""Tests for centralized configuration management"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from libs.core.config_loader import (
    ConfigLoader,
    DictSource,
    EnvironmentSource,
    YamlFileSource,
    create_default_loader,
)
from libs.core.config_schema import YesmanConfigSchema
from libs.yesman_config import YesmanConfig


class TestConfigSchema:
    """Test configuration schema validation"""

    def test_default_config_valid(self):
        """Test that default configuration is valid"""
        config = YesmanConfigSchema()
        assert config.mode == "merge"
        assert config.tmux.default_shell == "/bin/bash"
        assert config.logging.level == "INFO"

    def test_validation_errors(self):
        """Test validation errors for invalid config"""
        with pytest.raises(ValueError):
            YesmanConfigSchema(mode="invalid_mode")

        with pytest.raises(ValueError):
            YesmanConfigSchema(logging={"level": "INVALID"})

        with pytest.raises(ValueError):
            YesmanConfigSchema(tmux={"status_position": "middle"})

    def test_path_expansion(self):
        """Test that paths are expanded correctly"""
        config = YesmanConfigSchema(root_dir="~/test")
        assert str(config.root_dir).startswith("/")
        assert "~" not in config.root_dir


class TestConfigSources:
    """Test configuration sources"""

    def test_yaml_file_source(self, tmp_path):
        """Test YAML file source"""
        # Create test config file
        config_file = tmp_path / "test.yaml"
        config_data = {"mode": "isolated", "logging": {"level": "DEBUG"}}
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Test loading
        source = YamlFileSource(config_file)
        assert source.exists()
        loaded = source.load()
        assert loaded == config_data

        # Test non-existent file
        source = YamlFileSource(tmp_path / "missing.yaml")
        assert not source.exists()
        assert source.load() == {}

    def test_environment_source(self):
        """Test environment variable source"""
        with patch.dict(
            os.environ,
            {
                "YESMAN_MODE": "local",
                "YESMAN_LOGGING_LEVEL": "WARNING",
                "YESMAN_TMUX_MOUSE": "false",
                "YESMAN_CONFIDENCE_THRESHOLD": "0.95",
                "OTHER_VAR": "ignored",
            },
        ):
            source = EnvironmentSource()
            assert source.exists()
            config = source.load()

            assert config["mode"] == "local"
            assert config["logging"]["level"] == "WARNING"
            assert config["tmux"]["mouse"] is False
            assert config["confidence_threshold"] == 0.95
            assert "other_var" not in config

    def test_dict_source(self):
        """Test dictionary source"""
        config_data = {"mode": "merge", "custom": {"key": "value"}}
        source = DictSource(config_data)
        assert source.exists()
        assert source.load() == config_data


class TestConfigLoader:
    """Test configuration loader"""

    def test_single_source(self):
        """Test loading from single source"""
        loader = ConfigLoader()
        loader.add_source(DictSource({"mode": "isolated"}))

        config = loader.load()
        assert config.mode == "isolated"

    def test_multiple_sources_merge(self):
        """Test merging multiple sources"""
        loader = ConfigLoader()

        # Base config
        loader.add_source(DictSource({"mode": "merge", "logging": {"level": "INFO"}}))

        # Override config
        loader.add_source(DictSource({"logging": {"level": "DEBUG"}, "confidence_threshold": 0.9}))

        config = loader.load()
        assert config.mode == "merge"  # From first source
        assert config.logging.level == "DEBUG"  # Overridden
        assert config.confidence_threshold == 0.9  # From second source

    def test_deep_merge(self):
        """Test deep merging of nested configs"""
        loader = ConfigLoader()

        loader.add_source(DictSource({"tmux": {"default_shell": "/bin/bash", "mouse": True}}))

        loader.add_source(DictSource({"tmux": {"mouse": False, "base_index": 1}}))

        config = loader.load()
        assert config.tmux.default_shell == "/bin/bash"  # Preserved
        assert config.tmux.mouse is False  # Overridden
        assert config.tmux.base_index == 1  # Added

    def test_validation_errors(self):
        """Test validation error handling"""
        loader = ConfigLoader()
        loader.add_source(DictSource({"mode": "invalid", "logging": {"level": "INVALID"}}))

        with pytest.raises(ValueError) as exc_info:
            loader.load()

        error_msg = str(exc_info.value)
        assert "Configuration validation failed" in error_msg
        assert "mode" in error_msg
        assert "logging.level" in error_msg

    def test_cache_invalidation(self):
        """Test that cache is invalidated when sources change"""
        loader = ConfigLoader()
        loader.add_source(DictSource({"mode": "merge"}))

        # First load
        config1 = loader.load()
        assert config1.mode == "merge"

        # Add another source
        loader.add_source(DictSource({"mode": "isolated"}))

        # Should get new config
        config2 = loader.load()
        assert config2.mode == "isolated"


class TestYesmanConfig:
    """Test YesmanConfig with new configuration system"""

    def test_backward_compatibility(self):
        """Test backward compatibility methods"""
        loader = ConfigLoader()
        loader.add_source(
            DictSource(
                {
                    "logging": {"level": "DEBUG"},
                    "tmux": {"default_shell": "/bin/zsh"},
                    "custom": {"nested": {"value": 42}},
                }
            )
        )

        config = YesmanConfig(config_loader=loader)

        # Test get method with dot notation
        assert config.get("logging.level") == "DEBUG"
        assert config.get("tmux.default_shell") == "/bin/zsh"
        assert config.get("custom.nested.value") == 42
        assert config.get("missing.key", "default") == "default"

    def test_save_and_reload(self, tmp_path):
        """Test saving and reloading configuration"""
        # Change working directory for test
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            config = YesmanConfig()

            # Save new config
            config.save({"custom_key": "custom_value", "logging": {"level": "WARNING"}})

            # Check file was created
            assert config.local_path.exists()

            # Reload and check
            config.reload()
            assert config.get("custom_key") == "custom_value"
            assert config.get("logging.level") == "WARNING"

        finally:
            os.chdir(original_cwd)

    def test_schema_access(self):
        """Test accessing typed schema"""
        config = YesmanConfig()
        schema = config.schema

        assert isinstance(schema, YesmanConfigSchema)
        assert hasattr(schema, "tmux")
        assert hasattr(schema, "logging")

    def test_directory_creation(self, tmp_path):
        """Test that required directories are created"""
        with patch("libs.yesman_config.Path.home", return_value=tmp_path):
            config = YesmanConfig()

            # Check directories were created
            assert (tmp_path / ".scripton" / "yesman").exists()
            assert (tmp_path / ".scripton" / "yesman" / "sessions").exists()
            assert (tmp_path / ".scripton" / "yesman" / "templates").exists()
            assert (tmp_path / ".scripton" / "yesman" / "logs").exists()


class TestEnvironmentSpecificConfig:
    """Test environment-specific configuration loading"""

    def test_development_environment(self):
        """Test loading development config"""
        with patch.dict(os.environ, {"YESMAN_ENV": "development"}):
            # Would load config/development.yaml if it exists
            loader = create_default_loader()
            sources = loader.get_config_sources_info()

            # Check that environment-specific source would be added
            source_types = [s["type"] for s in sources]
            assert "YamlFileSource" in source_types
            assert "EnvironmentSource" in source_types


class TestConfigPriority:
    """Test configuration priority order"""

    def test_priority_order(self, tmp_path):
        """Test that sources override in correct order"""
        # Create test files
        default_config = {"mode": "merge", "confidence_threshold": 0.5}
        global_config = {"mode": "isolated", "confidence_threshold": 0.7}
        local_config = {"confidence_threshold": 0.9}

        # Setup mock paths
        with patch("libs.core.config_loader.Path.home", return_value=tmp_path):
            with patch("libs.core.config_loader.Path.cwd", return_value=tmp_path):
                # Create config directories and files
                (tmp_path / ".scripton" / "yesman").mkdir(parents=True)
                (tmp_path / ".scripton" / "yesman" / "yesman.yaml").write_text(yaml.dump(global_config))

                (tmp_path / ".scripton" / "yesman" / "yesman.yaml").write_text(yaml.dump(local_config))

                # Test with environment variable override
                with patch.dict(os.environ, {"YESMAN_CONFIDENCE_THRESHOLD": "0.95"}):
                    loader = create_default_loader()
                    config = loader.load()

                    # Environment variable should win
                    assert config.confidence_threshold == 0.95
