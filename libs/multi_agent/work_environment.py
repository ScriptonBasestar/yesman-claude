# Copyright notice.

import json
import logging
import os
import shutil
import subprocess
import venv
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Isolated work environment management for multi-agent development."""


logger = logging.getLogger(__name__)


@dataclass
class WorkEnvironment:
    """Represents an isolated work environment for a branch."""

    branch_name: str
    worktree_path: Path
    venv_path: Path
    config: dict[str, object]
    agent_id: str | None = None
    status: str = "initialized"  # initialized, active, suspended, terminated

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary.

        Returns:
        object: Description of return value.
        """
        data = asdict(self)
        data["worktree_path"] = str(self.worktree_path)
        data["venv_path"] = str(self.venv_path)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "WorkEnvironment":
        """Create from dictionary.

        Returns:
        WorkEnvironment: Description of return value.
        """
        data["worktree_path"] = Path(cast(str, data["worktree_path"]))
        data["venv_path"] = Path(cast(str, data["venv_path"]))
        return cls(**cast(dict[str, Any], data))


class WorkEnvironmentManager:
    """Manages isolated work environments for branches."""

    def __init__(self, repo_path: str = ".", work_dir: str | None = None) -> None:
        """Initialize work environment manager.

        Args:
            repo_path: Path to main repository
            work_dir: Directory for worktrees and environments

        """
        self.repo_path = Path(repo_path).resolve()
        self.work_dir = (
            Path(work_dir) if work_dir else self.repo_path.parent / ".yesman-work"
        )
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.environments: dict[str, WorkEnvironment] = {}
        self._load_environments()

    def _run_command(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """Run a command with optional working directory and environment.

        Returns:
            Subprocess.Completedprocess object.


        """
        logger.debug("Running command: {' '.join(cmd)} in {cwd or 'current dir'}")

        try:
            result = subprocess.run(
                cmd,
                check=False,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                env=env or os.environ.copy(),
                timeout=300,  # 5 minutes timeout
            )

            if result.returncode != 0:
                logger.error("Command failed: {result.stderr}")

            return result

        except subprocess.TimeoutExpired:
            logger.exception("Command timed out")
            raise

    def _get_environments_file(self) -> Path:
        """Get path to environments metadata file.

        Returns:
        Path: Description of return value.
        """
        return self.work_dir / "environments.json"

    def _load_environments(self) -> None:
        """Load environments metadata."""
        metadata_file = self._get_environments_file()

        if metadata_file.exists():
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self.environments = {
                        name: WorkEnvironment.from_dict(info)
                        for name, info in data.items()
                    }
                logger.info("Loaded {len(self.environments)} work environments")
            except Exception:
                logger.exception("Failed to load environments")
                self.environments = {}

    def _save_environments(self) -> None:
        """Save environments metadata."""
        metadata_file = self._get_environments_file()

        try:
            data = {name: env.to_dict() for name, env in self.environments.items()}

            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug("Saved {len(self.environments)} work environments")
        except Exception:
            logger.exception("Failed to save environments")

    def create_work_environment(
        self,
        branch_name: str,
        config: dict[str, object] | None = None,
    ) -> WorkEnvironment:
        """Create an isolated work environment for a branch.

        Args:
            branch_name: Name of the branch
            config: Configuration for the environment

        Returns:
                Workenvironment object the created item.
        """
        if branch_name in self.environments:
            logger.warning("Environment for branch {branch_name} already exists")
            return self.environments[branch_name]

        # Default configuration
        default_config = {
            "python_version": "3.9",
            "install_deps": True,
            "copy_config": True,
            "env_vars": {},
        }

        if config:
            default_config.update(config)

        # Create worktree
        worktree_path = self._create_worktree(branch_name)

        # Create virtual environment
        venv_path = self._create_venv(branch_name, worktree_path, default_config)

        # Create environment object
        env = WorkEnvironment(
            branch_name=branch_name,
            worktree_path=worktree_path,
            venv_path=venv_path,
            config=default_config,
        )

        # Set up environment
        self._setup_environment(env)

        # Save metadata
        self.environments[branch_name] = env
        self._save_environments()

        logger.info("Created work environment for branch: {branch_name}")
        return env

    def _create_worktree(self, branch_name: str) -> Path:
        """Create a git worktree for the branch.

        Returns:
        Path: Description of return value.
        """
        # Sanitize branch name for directory
        safe_name = branch_name.replace("/", "_")
        worktree_path = self.work_dir / "worktrees" / safe_name

        if worktree_path.exists():
            logger.warning("Worktree already exists at {worktree_path}")
            return worktree_path

        # Create worktree
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        result = self._run_command(
            ["git", "worktree", "add", str(worktree_path), branch_name],
        )

        if result.returncode != 0:
            msg = f"Failed to create worktree: {result.stderr}"
            raise RuntimeError(msg)

        logger.info("Created worktree at {worktree_path}")
        return worktree_path

    def _create_venv(
        self,
        branch_name: str,
        worktree_path: Path,
        config: dict[str, object],
    ) -> Path:
        """Create a virtual environment for the branch.

        Returns:
        Path: Description of return value.
        """
        safe_name = branch_name.replace("/", "_")
        venv_path = self.work_dir / "venvs" / safe_name

        if venv_path.exists():
            logger.warning("Virtual environment already exists at {venv_path}")
            return venv_path

        # Create virtual environment
        venv_path.parent.mkdir(parents=True, exist_ok=True)
        venv.create(venv_path, with_pip=True)

        logger.info("Created virtual environment at {venv_path}")

        # Install dependencies if requested
        if config.get("install_deps", True):
            self._install_dependencies(venv_path, worktree_path)

        return venv_path

    def _install_dependencies(self, venv_path: Path, worktree_path: Path) -> None:
        """Install dependencies in the virtual environment."""
        pip_path = venv_path / "bin" / "pip"
        if not pip_path.exists():
            pip_path = venv_path / "Scripts" / "pip.exe"  # Windows

        # Upgrade pip first
        self._run_command([str(pip_path), "install", "--upgrade", "pip"])

        # Look for requirements files
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements/dev.txt",
            "requirements/development.txt",
        ]

        for req_file in requirements_files:
            req_path = worktree_path / req_file
            if req_path.exists():
                logger.info("Installing dependencies from {req_file}")
                result = self._run_command(
                    [str(pip_path), "install", "-r", str(req_path)],
                )

                if result.returncode != 0:
                    logger.error("Failed to install dependencies: {result.stderr}")

        # Check for pyproject.toml
        pyproject_path = worktree_path / "pyproject.toml"
        if pyproject_path.exists():
            logger.info("Installing from pyproject.toml")
            self._run_command([str(pip_path), "install", "-e", str(worktree_path)])

    def _setup_environment(self, env: WorkEnvironment) -> None:
        """Set up the work environment."""
        # Copy configuration files if requested
        if env.config.get("copy_config", True):
            self._copy_config_files(env)

        # Create activation script with custom env vars
        self._create_activation_script(env)

        # Initialize any project-specific setup
        self._run_project_setup(env)

    def _copy_config_files(self, env: WorkEnvironment) -> None:
        """Copy configuration files to the work environment."""
        config_files = [
            ".env",
            ".env.local",
            ".env.development",
            "config.yaml",
            "config.json",
            "settings.json",
        ]

        for config_file in config_files:
            src = self.repo_path / config_file
            if src.exists():
                dst = env.worktree_path / config_file
                if not dst.exists():
                    shutil.copy2(src, dst)
                    logger.debug("Copied {config_file} to work environment")

    @staticmethod
    def _create_activation_script(env: WorkEnvironment) -> None:
        """Create custom activation script with environment variables."""
        activate_dir = env.venv_path / "bin"
        if not activate_dir.exists():
            activate_dir = env.venv_path / "Scripts"  # Windows

        custom_activate = activate_dir / "activate_custom"

        with open(custom_activate, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\n")
            f.write(f"# Custom activation script for {env.branch_name}\n\n")

            # Source original activate
            f.write(f"source {activate_dir}/activate\n\n")

            # Set custom environment variables
            f.write("# Custom environment variables\n")
            f.write(f"export YESMAN_BRANCH={env.branch_name}\n")
            f.write(f"export YESMAN_WORKTREE={env.worktree_path}\n")

            env_vars = cast(dict[str, str], env.config.get("env_vars", {}))
            f.writelines(f"export {key}={value}\n" for key, value in env_vars.items())

            f.write("\n# Change to worktree directory\n")
            f.write(f"cd {env.worktree_path}\n")

        # Make executable with restricted permissions
        os.chmod(custom_activate, 0o700)

    def _run_project_setup(self, env: WorkEnvironment) -> None:
        """Run any project-specific setup commands."""
        setup_commands = cast(list[str], env.config.get("setup_commands", []))

        for cmd in setup_commands:
            logger.info("Running setup command: {cmd}")
            result = self._run_command(cmd.split(), cwd=env.worktree_path)

            if result.returncode != 0:
                logger.error("Setup command failed: {cmd}")

    def get_environment(self, branch_name: str) -> WorkEnvironment | None:
        """Get work environment for a branch.

        Returns:
        object: Description of return value.
        """
        return self.environments.get(branch_name)

    def activate_environment(self, branch_name: str) -> tuple[Path, dict[str, str]]:
        """Get activation details for an environment.

        Returns:
            Tuple of (worktree_path, environment_variables)
        """
        env = self.get_environment(branch_name)
        if not env:
            msg = f"No environment found for branch {branch_name}"
            raise ValueError(msg)

        # Build environment variables
        env_vars = os.environ.copy()
        env_vars.update(
            {
                "VIRTUAL_ENV": str(env.venv_path),
                "PATH": f"{env.venv_path}/bin:{env_vars['PATH']}",
                "YESMAN_BRANCH": branch_name,
                "YESMAN_WORKTREE": str(env.worktree_path),
            },
        )

        # Add custom env vars
        custom_env_vars = cast(dict[str, str], env.config.get("env_vars", {}))
        env_vars.update(custom_env_vars)

        # Update status
        env.status = "active"
        self._save_environments()

        return env.worktree_path, env_vars

    @contextmanager
    def work_in_environment(self, branch_name: str) -> Generator[Path, None, None]:
        """Context manager to work in an environment."""
        original_cwd = os.getcwd()
        original_env = os.environ.copy()

        try:
            worktree_path, env_vars = self.activate_environment(branch_name)

            # Change directory
            os.chdir(worktree_path)

            # Update environment
            os.environ.clear()
            os.environ.update(env_vars)

            yield worktree_path

        finally:
            # Restore original state
            os.chdir(original_cwd)
            os.environ.clear()
            os.environ.update(original_env)

    def suspend_environment(self, branch_name: str) -> None:
        """Suspend a work environment."""
        env = self.get_environment(branch_name)
        if env:
            env.status = "suspended"
            self._save_environments()
            logger.info("Suspended environment for branch: {branch_name}")

    def terminate_environment(
        self,
        branch_name: str,
        remove_files: bool = False,  # noqa: FBT001
    ) -> None:
        """Terminate a work environment."""
        env = self.get_environment(branch_name)
        if not env:
            logger.warning("No environment found for branch {branch_name}")
            return

        # Update status
        env.status = "terminated"

        if remove_files:
            # Remove worktree
            if env.worktree_path.exists():
                # First, remove from git worktree list
                self._run_command(["git", "worktree", "remove", str(env.worktree_path)])

                # Ensure directory is removed
                if env.worktree_path.exists():
                    shutil.rmtree(env.worktree_path)

                logger.info("Removed worktree: {env.worktree_path}")

            # Remove virtual environment
            if env.venv_path.exists():
                shutil.rmtree(env.venv_path)
                logger.info("Removed virtual environment: {env.venv_path}")

            # Remove from environments
            del self.environments[branch_name]

        self._save_environments()
        logger.info("Terminated environment for branch: {branch_name}")

    def cleanup_terminated(self) -> list[str]:
        """Clean up all terminated environments.

        Returns:
        object: Description of return value.
        """
        cleaned = []

        for branch_name, env in list(self.environments.items()):
            if env.status == "terminated":
                self.terminate_environment(branch_name, remove_files=True)
                cleaned.append(branch_name)

        return cleaned

    def list_environments(self) -> list[WorkEnvironment]:
        """List all work environments.

        Returns:
        object: Description of return value.
        """
        return list(self.environments.values())
