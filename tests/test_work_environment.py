# Copyright notice.

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from libs.multi_agent.work_environment import WorkEnvironment, WorkEnvironmentManager

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Tests for WorkEnvironmentManager."""


class TestWorkEnvironmentManager:
    """Test cases for WorkEnvironmentManager."""

    @pytest.fixture
    @staticmethod
    def temp_repo(tmp_path: Path) -> Path:
        """Create a temporary git repository."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Initialize git repo

        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            check=False,
            cwd=repo_path,
        )
        subprocess.run(["git", "config", "user.name", "Test User"], check=False, cwd=repo_path)

        # Create initial files
        (repo_path / "README.md").write_text("# Test Repo")
        (repo_path / "requirements.txt").write_text("pytest>=6.0\nclick>=8.0")

        # Initial commit
        subprocess.run(["git", "add", "."], check=False, cwd=repo_path)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=False, cwd=repo_path)

        # Create test branch
        subprocess.run(["git", "checkout", "-b", "test-branch"], check=False, cwd=repo_path)

        return repo_path

    @pytest.fixture
    @staticmethod
    def work_dir(tmp_path: Path) -> Path:
        """Create a temporary work directory."""
        work_path = tmp_path / "work"
        work_path.mkdir()
        return work_path

    @pytest.fixture
    @staticmethod
    def manager(temp_repo: Path, work_dir: Path) -> WorkEnvironmentManager:
        """Create WorkEnvironmentManager instance."""
        return WorkEnvironmentManager(repo_path=str(temp_repo), work_dir=str(work_dir))

    @staticmethod
    def test_init(manager: WorkEnvironmentManager, temp_repo: Path, work_dir: Path) -> None:
        """Test WorkEnvironmentManager initialization."""
        assert manager.repo_path == temp_repo
        assert manager.work_dir == work_dir
        assert manager.environments == {}
        assert manager.work_dir.exists()

    @staticmethod
    def test_create_work_environment(manager: WorkEnvironmentManager) -> None:
        """Test creating a work environment."""
        with patch.object(manager, "_create_worktree") as mock_worktree:
            with patch.object(manager, "_create_venv") as mock_venv:
                with patch.object(manager, "_setup_environment") as mock_setup:
                    # Mock return values
                    mock_worktree.return_value = manager.work_dir / "worktrees" / "test-branch"
                    mock_venv.return_value = manager.work_dir / "venvs" / "test-branch"

                    # Create environment
                    env = manager.create_work_environment("test-branch")

                    # Verify environment
                    assert env.branch_name == "test-branch"
                    assert env.worktree_path == mock_worktree.return_value
                    assert env.venv_path == mock_venv.return_value
                    assert env.status == "initialized"

                    # Verify methods called
                    mock_worktree.assert_called_once_with("test-branch")
                    mock_venv.assert_called_once()
                    mock_setup.assert_called_once_with(env)

                    # Verify saved
                    assert "test-branch" in manager.environments

    @staticmethod
    def test_create_work_environment_custom_config(
        manager: WorkEnvironmentManager,
    ) -> None:
        """Test creating environment with custom configuration."""
        config = {
            "python_version": "3.12",
            "install_deps": False,
            "env_vars": {"FOO": "bar"},
        }

        with patch.object(manager, "_create_worktree") as mock_worktree:
            with patch.object(manager, "_create_venv") as mock_venv:
                with patch.object(manager, "_setup_environment"):
                    mock_worktree.return_value = Path(tempfile.mkdtemp())
                    mock_venv.return_value = Path(tempfile.mkdtemp())

                    env = manager.create_work_environment("test-branch", config)

                    # Verify config merged
                    assert env.config["python_version"] == "3.12"
                    assert env.config["install_deps"] is False
                    assert env.config["env_vars"]["FOO"] == "bar"

    @staticmethod
    def test_create_worktree(manager: WorkEnvironmentManager) -> None:
        """Test creating a git worktree."""
        with patch.object(manager, "_run_command") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            worktree_path = manager._create_worktree("feature/test")

            # Verify path
            expected_path = manager.work_dir / "worktrees" / "feature_test"
            assert worktree_path == expected_path

            # Verify git command
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert cmd[:3] == ["git", "worktree", "add"]
            assert str(expected_path) in cmd
            assert "feature/test" in cmd

    @staticmethod
    def test_create_venv(manager: WorkEnvironmentManager) -> None:
        """Test creating a virtual environment."""
        worktree_path = manager.work_dir / "worktrees" / "test"
        worktree_path.mkdir(parents=True)

        # Create dummy requirements
        (worktree_path / "requirements.txt").write_text("pytest")

        with patch("venv.create") as mock_venv_create:
            with patch.object(manager, "_install_dependencies") as mock_install:
                config = {"install_deps": True}

                venv_path = manager._create_venv("test-branch", worktree_path, config)

                # Verify venv creation
                expected_path = manager.work_dir / "venvs" / "test-branch"
                assert venv_path == expected_path
                mock_venv_create.assert_called_once_with(expected_path, with_pip=True)

                # Verify dependencies installation
                mock_install.assert_called_once_with(expected_path, worktree_path)

    @staticmethod
    def test_install_dependencies(manager: WorkEnvironmentManager) -> None:
        """Test installing dependencies."""
        venv_path = manager.work_dir / "venvs" / "test"
        venv_path.mkdir(parents=True)

        # Create mock pip
        pip_path = venv_path / "bin"
        pip_path.mkdir()
        (pip_path / "pip").touch()

        worktree_path = manager.work_dir / "worktrees" / "test"
        worktree_path.mkdir(parents=True)

        # Create requirements file
        (worktree_path / "requirements.txt").write_text("pytest>=6.0")

        with patch.object(manager, "_run_command") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            manager._install_dependencies(venv_path, worktree_path)

            # Should upgrade pip and install requirements
            assert mock_run.call_count >= 2

            # Check pip upgrade call
            pip_upgrade_call = mock_run.call_args_list[0][0][0]
            assert "pip" in pip_upgrade_call
            assert "install" in pip_upgrade_call
            assert "--upgrade" in pip_upgrade_call

    @staticmethod
    def test_setup_environment(manager: WorkEnvironmentManager) -> None:
        """Test setting up environment."""
        env = WorkEnvironment(
            branch_name="test",
            worktree_path=manager.work_dir / "worktrees" / "test",
            venv_path=manager.work_dir / "venvs" / "test",
            config={"copy_config": True},
        )

        with patch.object(manager, "_copy_config_files") as mock_copy:
            with patch.object(manager, "_create_activation_script") as mock_script:
                with patch.object(manager, "_run_project_setup") as mock_setup:
                    manager._setup_environment(env)

                    mock_copy.assert_called_once_with(env)
                    mock_script.assert_called_once_with(env)
                    mock_setup.assert_called_once_with(env)

    @staticmethod
    def test_activate_environment(manager: WorkEnvironmentManager) -> None:
        """Test activating an environment."""
        env = WorkEnvironment(
            branch_name="test",
            worktree_path=Path(tempfile.mkdtemp()),
            venv_path=Path(tempfile.mkdtemp()),
            config={"env_vars": {"CUSTOM_VAR": "value"}},
        )

        manager.environments["test"] = env

        worktree_path, env_vars = manager.activate_environment("test")

        assert worktree_path == env.worktree_path
        assert "VIRTUAL_ENV" in env_vars
        assert env_vars["VIRTUAL_ENV"] == str(env.venv_path)
        assert "YESMAN_BRANCH" in env_vars
        assert env_vars["YESMAN_BRANCH"] == "test"
        assert "CUSTOM_VAR" in env_vars
        assert env_vars["CUSTOM_VAR"] == "value"
        assert env.status == "active"

    @staticmethod
    def test_work_in_environment_context(manager: WorkEnvironmentManager) -> None:
        """Test work_in_environment context manager."""
        env = WorkEnvironment(
            branch_name="test",
            worktree_path=manager.work_dir / "worktree",
            venv_path=manager.work_dir / "venv",
            config={},
        )
        env.worktree_path.mkdir(parents=True)

        manager.environments["test"] = env

        original_cwd = os.getcwd()
        os.environ.copy()

        with manager.work_in_environment("test") as work_path:
            # Check we're in the worktree
            assert os.getcwd() == str(env.worktree_path)
            assert work_path == env.worktree_path

            # Check environment variables
            assert os.environ.get("YESMAN_BRANCH") == "test"

        # Check restoration
        assert os.getcwd() == original_cwd
        assert os.environ.get("YESMAN_BRANCH") != "test"

    @staticmethod
    def test_terminate_environment(manager: WorkEnvironmentManager) -> None:
        """Test terminating an environment."""
        env = WorkEnvironment(
            branch_name="test",
            worktree_path=manager.work_dir / "worktrees" / "test",
            venv_path=manager.work_dir / "venvs" / "test",
            config={},
        )

        # Create dummy directories
        env.worktree_path.mkdir(parents=True)
        env.venv_path.mkdir(parents=True)

        manager.environments["test"] = env

        with patch.object(manager, "_run_command") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Terminate without removing files
            manager.terminate_environment("test", remove_files=False)
            assert env.status == "terminated"
            assert "test" in manager.environments

            # Terminate with file removal
            manager.terminate_environment("test", remove_files=True)

            # Verify git worktree removal
            mock_run.assert_called_with(
                ["git", "worktree", "remove", str(env.worktree_path)],
            )

            # Verify removed from environments
            assert "test" not in manager.environments

    @staticmethod
    def test_list_environments(manager: WorkEnvironmentManager) -> None:
        """Test listing environments."""
        env1 = WorkEnvironment(
            branch_name="branch1",
            worktree_path=Path(tempfile.mkdtemp()),
            venv_path=Path(tempfile.mkdtemp()),
            config={},
        )
        env2 = WorkEnvironment(
            branch_name="branch2",
            worktree_path=Path(tempfile.mkdtemp()),
            venv_path=Path(tempfile.mkdtemp()),
            config={},
        )

        manager.environments = {"branch1": env1, "branch2": env2}

        envs = manager.list_environments()
        assert len(envs) == 2
        assert env1 in envs
        assert env2 in envs

    @staticmethod
    def test_environment_persistence(manager: WorkEnvironmentManager) -> None:
        """Test saving and loading environments."""
        env = WorkEnvironment(
            branch_name="test",
            worktree_path=manager.work_dir / "worktrees" / "test",
            venv_path=manager.work_dir / "venvs" / "test",
            config={"custom": "config"},
            agent_id="agent-1",
            status="active",
        )

        manager.environments["test"] = env
        manager._save_environments()

        # Create new manager to test loading
        new_manager = WorkEnvironmentManager(
            repo_path=str(manager.repo_path),
            work_dir=str(manager.work_dir),
        )

        assert len(new_manager.environments) == 1
        loaded_env = new_manager.environments["test"]
        assert loaded_env.branch_name == "test"
        assert loaded_env.config["custom"] == "config"
        assert loaded_env.agent_id == "agent-1"
        assert loaded_env.status == "active"
