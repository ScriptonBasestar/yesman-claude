"""Test configuration modes including backward compatibility."""

from pathlib import Path
from unittest.mock import patch
from typing import Any

import pytest
import yaml

from libs.yesman_config import YesmanConfig


class TestConfigModes:
    """Test configuration modes and backward compatibility."""

    def test_merge_mode_default(self, tmp_path: Any) -> None:
        """Test default merge mode behavior."""
        # Create global config
        global_dir = tmp_path / ".scripton" / "yesman"
        global_dir.mkdir()
        global_config = {
            "log_level": "INFO",
            "global_setting": "global_value",
        }
        with (global_dir / "yesman.yaml").open("w") as f:
            yaml.dump(global_config, f)

        # Create local config
        local_dir = tmp_path / "project" / ".scripton" / "yesman"
        local_dir.mkdir(parents=True)
        local_config = {
            "log_level": "DEBUG",
            "local_setting": "local_value",
        }
        with (local_dir / "yesman.yaml").open("w") as f:
            yaml.dump(local_config, f)

        # Test merge behavior
        with patch.object(Path, "home", return_value=tmp_path):
            with patch.object(Path, "cwd", return_value=tmp_path / "project"):
                config = YesmanConfig()

                # Local overrides global
                assert config.get("log_level") == "DEBUG"
                # Global setting is preserved
                assert config.get("global_setting") == "global_value"
                # Local setting is added
                assert config.get("local_setting") == "local_value"

    def test_isolated_mode(self, tmp_path: Any) -> None:
        """Test isolated mode (new name)."""
        # Create global config
        global_dir = tmp_path / ".scripton" / "yesman"
        global_dir.mkdir()
        global_config = {
            "log_level": "INFO",
            "global_setting": "global_value",
        }
        with (global_dir / "yesman.yaml").open("w") as f:
            yaml.dump(global_config, f)

        # Create local config with isolated mode
        local_dir = tmp_path / "project" / ".scripton" / "yesman"
        local_dir.mkdir(parents=True)
        local_config = {
            "mode": "isolated",
            "log_level": "DEBUG",
            "local_setting": "local_value",
        }
        with (local_dir / "yesman.yaml").open("w") as f:
            yaml.dump(local_config, f)

        # Test isolated behavior
        with patch.object(Path, "home", return_value=tmp_path):
            with patch.object(Path, "cwd", return_value=tmp_path / "project"):
                config = YesmanConfig()

                # Only local settings are used
                assert config.get("log_level") == "DEBUG"
                assert config.get("local_setting") == "local_value"
                # Global setting is NOT included
                assert config.get("global_setting") is None

    def test_local_mode_backward_compatibility(self, tmp_path: Any) -> None:
        """Test that 'local' mode still works for backward compatibility."""
        # Create global config
        global_dir = tmp_path / ".scripton" / "yesman"
        global_dir.mkdir()
        global_config = {
            "log_level": "INFO",
            "global_setting": "global_value",
        }
        with (global_dir / "yesman.yaml").open("w") as f:
            yaml.dump(global_config, f)

        # Create local config with old 'local' mode
        local_dir = tmp_path / "project" / ".scripton" / "yesman"
        local_dir.mkdir(parents=True)
        local_config = {
            "mode": "local",  # Old name
            "log_level": "DEBUG",
            "local_setting": "local_value",
        }
        with (local_dir / "yesman.yaml").open("w") as f:
            yaml.dump(local_config, f)

        # Test that it still works
        with patch.object(Path, "home", return_value=tmp_path):
            with patch.object(Path, "cwd", return_value=tmp_path / "project"):
                config = YesmanConfig()

                # Only local settings are used
                assert config.get("log_level") == "DEBUG"
                assert config.get("local_setting") == "local_value"
                # Global setting is NOT included
                assert config.get("global_setting") is None

    def test_isolated_mode_empty_error(self, tmp_path: Any) -> None:
        """Test error when isolated mode is set but local config is empty."""
        # Create empty local config with isolated mode
        local_dir = tmp_path / "project" / ".scripton" / "yesman"
        local_dir.mkdir(parents=True)
        local_config = {"mode": "isolated"}
        with (local_dir / "yesman.yaml").open("w") as f:
            yaml.dump(local_config, f)

        # Should raise RuntimeError
        with patch.object(Path, "home", return_value=tmp_path):
            with patch.object(Path, "cwd", return_value=tmp_path / "project"):
                with pytest.raises(RuntimeError, match="mode: isolated but.*doesn't exist or is empty"):
                    YesmanConfig()

    def test_unsupported_mode_error(self, tmp_path: Any) -> None:
        """Test error for unsupported mode."""
        # Create local config with invalid mode
        local_dir = tmp_path / "project" / ".scripton" / "yesman"
        local_dir.mkdir(parents=True)
        local_config = {"mode": "invalid_mode"}
        with (local_dir / "yesman.yaml").open("w") as f:
            yaml.dump(local_config, f)

        # Should raise ValueError
        with patch.object(Path, "home", return_value=tmp_path):
            with patch.object(Path, "cwd", return_value=tmp_path / "project"):
                with pytest.raises(ValueError, match="Unsupported mode: invalid_mode"):
                    YesmanConfig()
