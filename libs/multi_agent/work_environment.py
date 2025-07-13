"""Isolated work environment management for multi-agent development"""

import json
import logging
import os
import shutil
import subprocess
import venv
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class WorkEnvironment:
    """Represents an isolated work environment for a branch"""

    branch_name: str
    worktree_path: Path
    venv_path: Path
    config: Dict[str, Any]
    agent_id: Optional[str] = None
    status: str = "initialized"  # initialized, active, suspended, terminated

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["worktree_path"] = str(self.worktree_path)
        data["venv_path"] = str(self.venv_path)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkEnvironment":
        """Create from dictionary"""
        data["worktree_path"] = Path(data["worktree_path"])
        data["venv_path"] = Path(data["venv_path"])
        return cls(**data)


class WorkEnvironmentManager:
    """Manages isolated work environments for branches"""

    def __init__(self, repo_path: str = ".", work_dir: Optional[str] = None):
        """
        Initialize work environment manager

        Args:
            repo_path: Path to main repository
            work_dir: Directory for worktrees and environments
        """
        self.repo_path = Path(repo_path).resolve()
        self.work_dir = Path(work_dir) if work_dir else self.repo_path.parent / ".yesman-work"
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.environments: Dict[str, WorkEnvironment] = {}
        self._load_environments()

    def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> subprocess.CompletedProcess:
        """Run a command with optional working directory and environment"""
        logger.debug(f"Running command: {' '.join(cmd)} in {cwd or 'current dir'}")

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
                logger.error(f"Command failed: {result.stderr}")

            return result

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            raise

    def _get_environments_file(self) -> Path:
        """Get path to environments metadata file"""
        return self.work_dir / "environments.json"

    def _load_environments(self) -> None:
        """Load environments metadata"""
        metadata_file = self._get_environments_file()

        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    data = json.load(f)
                    self.environments = {name: WorkEnvironment.from_dict(info) for name, info in data.items()}
                logger.info(f"Loaded {len(self.environments)} work environments")
            except Exception as e:
                logger.error(f"Failed to load environments: {e}")
                self.environments = {}

    def _save_environments(self) -> None:
        """Save environments metadata"""
        metadata_file = self._get_environments_file()

        try:
            data = {name: env.to_dict() for name, env in self.environments.items()}

            with open(metadata_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.environments)} work environments")
        except Exception as e:
            logger.error(f"Failed to save environments: {e}")

    def create_work_environment(
        self,
        branch_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> WorkEnvironment:
        """
        Create an isolated work environment for a branch

        Args:
            branch_name: Name of the branch
            config: Configuration for the environment

        Returns:
            WorkEnvironment object
        """
        if branch_name in self.environments:
            logger.warning(f"Environment for branch {branch_name} already exists")
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

        logger.info(f"Created work environment for branch: {branch_name}")
        return env

    def _create_worktree(self, branch_name: str) -> Path:
        """Create a git worktree for the branch"""
        # Sanitize branch name for directory
        safe_name = branch_name.replace("/", "_")
        worktree_path = self.work_dir / "worktrees" / safe_name

        if worktree_path.exists():
            logger.warning(f"Worktree already exists at {worktree_path}")
            return worktree_path

        # Create worktree
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        result = self._run_command(
            ["git", "worktree", "add", str(worktree_path), branch_name],
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {result.stderr}")

        logger.info(f"Created worktree at {worktree_path}")
        return worktree_path

    def _create_venv(
        self,
        branch_name: str,
        worktree_path: Path,
        config: Dict[str, Any],
    ) -> Path:
        """Create a virtual environment for the branch"""
        safe_name = branch_name.replace("/", "_")
        venv_path = self.work_dir / "venvs" / safe_name

        if venv_path.exists():
            logger.warning(f"Virtual environment already exists at {venv_path}")
            return venv_path

        # Create virtual environment
        venv_path.parent.mkdir(parents=True, exist_ok=True)
        venv.create(venv_path, with_pip=True)

        logger.info(f"Created virtual environment at {venv_path}")

        # Install dependencies if requested
        if config.get("install_deps", True):
            self._install_dependencies(venv_path, worktree_path)

        return venv_path

    def _install_dependencies(self, venv_path: Path, worktree_path: Path) -> None:
        """Install dependencies in the virtual environment"""
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
                logger.info(f"Installing dependencies from {req_file}")
                result = self._run_command(
                    [str(pip_path), "install", "-r", str(req_path)],
                )

                if result.returncode != 0:
                    logger.error(f"Failed to install dependencies: {result.stderr}")

        # Check for pyproject.toml
        pyproject_path = worktree_path / "pyproject.toml"
        if pyproject_path.exists():
            logger.info("Installing from pyproject.toml")
            self._run_command([str(pip_path), "install", "-e", str(worktree_path)])

    def _setup_environment(self, env: WorkEnvironment) -> None:
        """Set up the work environment"""
        # Copy configuration files if requested
        if env.config.get("copy_config", True):
            self._copy_config_files(env)

        # Create activation script with custom env vars
        self._create_activation_script(env)

        # Initialize any project-specific setup
        self._run_project_setup(env)

    def _copy_config_files(self, env: WorkEnvironment) -> None:
        """Copy configuration files to the work environment"""
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
                    logger.debug(f"Copied {config_file} to work environment")

    def _create_activation_script(self, env: WorkEnvironment) -> None:
        """Create custom activation script with environment variables"""
        activate_dir = env.venv_path / "bin"
        if not activate_dir.exists():
            activate_dir = env.venv_path / "Scripts"  # Windows

        custom_activate = activate_dir / "activate_custom"

        with open(custom_activate, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"# Custom activation script for {env.branch_name}\n\n")

            # Source original activate
            f.write(f"source {activate_dir}/activate\n\n")

            # Set custom environment variables
            f.write("# Custom environment variables\n")
            f.write(f"export YESMAN_BRANCH={env.branch_name}\n")
            f.write(f"export YESMAN_WORKTREE={env.worktree_path}\n")

            for key, value in env.config.get("env_vars", {}).items():
                f.write(f"export {key}={value}\n")

            f.write("\n# Change to worktree directory\n")
            f.write(f"cd {env.worktree_path}\n")

        # Make executable with restricted permissions
        os.chmod(custom_activate, 0o700)

    def _run_project_setup(self, env: WorkEnvironment) -> None:
        """Run any project-specific setup commands"""
        setup_commands = env.config.get("setup_commands", [])

        for cmd in setup_commands:
            logger.info(f"Running setup command: {cmd}")
            result = self._run_command(cmd.split(), cwd=env.worktree_path)

            if result.returncode != 0:
                logger.error(f"Setup command failed: {cmd}")

    def get_environment(self, branch_name: str) -> Optional[WorkEnvironment]:
        """Get work environment for a branch"""
        return self.environments.get(branch_name)

    def activate_environment(self, branch_name: str) -> Tuple[Path, Dict[str, str]]:
        """
        Get activation details for an environment

        Returns:
            Tuple of (worktree_path, environment_variables)
        """
        env = self.get_environment(branch_name)
        if not env:
            raise ValueError(f"No environment found for branch {branch_name}")

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
        env_vars.update(env.config.get("env_vars", {}))

        # Update status
        env.status = "active"
        self._save_environments()

        return env.worktree_path, env_vars

    @contextmanager
    def work_in_environment(self, branch_name: str):
        """Context manager to work in an environment"""
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
        """Suspend a work environment"""
        env = self.get_environment(branch_name)
        if env:
            env.status = "suspended"
            self._save_environments()
            logger.info(f"Suspended environment for branch: {branch_name}")

    def terminate_environment(
        self,
        branch_name: str,
        remove_files: bool = False,
    ) -> None:
        """Terminate a work environment"""
        env = self.get_environment(branch_name)
        if not env:
            logger.warning(f"No environment found for branch {branch_name}")
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

                logger.info(f"Removed worktree: {env.worktree_path}")

            # Remove virtual environment
            if env.venv_path.exists():
                shutil.rmtree(env.venv_path)
                logger.info(f"Removed virtual environment: {env.venv_path}")

            # Remove from environments
            del self.environments[branch_name]

        self._save_environments()
        logger.info(f"Terminated environment for branch: {branch_name}")

    def cleanup_terminated(self) -> List[str]:
        """Clean up all terminated environments"""
        cleaned = []

        for branch_name, env in list(self.environments.items()):
            if env.status == "terminated":
                self.terminate_environment(branch_name, remove_files=True)
                cleaned.append(branch_name)

        return cleaned

    def list_environments(self) -> List[WorkEnvironment]:
        """List all work environments"""
        return list(self.environments.values())
