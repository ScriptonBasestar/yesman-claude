"""Branch management system for multi-agent parallel development."""

import json
import logging
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BranchInfo:
    """Information about a git branch."""

    name: str
    base_branch: str
    created_at: datetime
    last_commit: str | None = None
    status: str = "active"  # active, merged, abandoned
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BranchInfo":
        """Create from dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class BranchManager:
    """Manages git branches for multi-agent parallel development."""

    def __init__(self, repo_path: str = ".", branch_prefix: str = "feat/multi-agent") -> None:
        """Initialize branch manager.

        Args:
            repo_path: Path to git repository
            branch_prefix: Prefix for multi-agent branches
        """
        self.repo_path = Path(repo_path).resolve()
        self.branch_prefix = branch_prefix
        self.branches: dict[str, BranchInfo] = {}
        self._load_branch_metadata()

    def _run_git_command(
        self,
        args: list[str],
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a git command and return result."""
        cmd = ["git", *args]
        logger.debug(f"Running git command: {' '.join(cmd)}")

        try:
            return subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check,
                timeout=30,
            )
        except subprocess.CalledProcessError as e:
            logger.exception("Git command failed: %s", e.stderr)
            raise
        except subprocess.TimeoutExpired:
            logger.exception("Git command timed out: %s", " ".join(cmd))
            raise

    def _get_current_branch(self) -> str:
        """Get current branch name."""
        result = self._run_git_command(["branch", "--show-current"])
        return result.stdout.strip() if result.stdout else ""

    def _branch_exists(self, branch_name: str) -> bool:
        """Check if branch exists."""
        result = self._run_git_command(["branch", "--list", branch_name], check=False)
        return bool(result.stdout.strip())

    def _get_branch_metadata_file(self) -> Path:
        """Get path to branch metadata file."""
        return self.repo_path / ".scripton" / "yesman" / "multi_agent_branches.json"

    def _load_branch_metadata(self) -> None:
        """Load branch metadata from file."""
        metadata_file = self._get_branch_metadata_file()

        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    data = json.load(f)
                    self.branches = {name: BranchInfo.from_dict(info) for name, info in data.items()}
                logger.info(f"Loaded {len(self.branches)} branch metadata entries")
            except Exception as e:
                logger.exception("Failed to load branch metadata: %s", e)
                self.branches = {}
        else:
            self.branches = {}

    def _save_branch_metadata(self) -> None:
        """Save branch metadata to file."""
        metadata_file = self._get_branch_metadata_file()
        metadata_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = {name: info.to_dict() for name, info in self.branches.items()}

            with open(metadata_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved branch metadata for {len(self.branches)} branches")
        except Exception as e:
            logger.exception("Failed to save branch metadata: %s", e)

    def create_feature_branch(
        self,
        issue_name: str,
        base_branch: str = "develop",
    ) -> str:
        """Create a feature branch for an issue.

        Args:
            issue_name: Name/ID of the issue
            base_branch: Base branch to create from

        Returns:
            Name of created branch
        """
        # Sanitize issue name for branch naming
        safe_issue_name = re.sub(r"[^a-zA-Z0-9-]", "-", issue_name.lower())
        safe_issue_name = re.sub(r"-+", "-", safe_issue_name).strip("-")

        # Generate branch name
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        branch_name = f"{self.branch_prefix}/{safe_issue_name}-{timestamp}"

        # Ensure base branch exists
        if not self._branch_exists(base_branch):
            msg = f"Base branch '{base_branch}' does not exist"
            raise ValueError(msg)

        # Fetch latest changes
        logger.info(f"Fetching latest changes for {base_branch}")
        self._run_git_command(["fetch", "origin", base_branch])

        # Create and checkout new branch
        logger.info(f"Creating branch: {branch_name} from {base_branch}")
        self._run_git_command(["checkout", "-b", branch_name, f"origin/{base_branch}"])

        # Record branch metadata
        branch_info = BranchInfo(
            name=branch_name,
            base_branch=base_branch,
            created_at=datetime.now(UTC),
            metadata={
                "issue_name": issue_name,
                "agent_id": None,  # Will be set when agent claims the branch
            },
        )

        self.branches[branch_name] = branch_info
        self._save_branch_metadata()

        logger.info(f"Successfully created branch: {branch_name}")
        return branch_name

    def list_active_branches(self) -> list[BranchInfo]:
        """List all active multi-agent branches."""
        active_branches = []

        # Get all branches
        result = self._run_git_command(["branch", "-a"])
        all_branches = [line.strip().replace("* ", "") for line in result.stdout.strip().split("\n") if line.strip()]

        # Filter for our multi-agent branches
        for branch in all_branches:
            if self.branch_prefix in branch:
                branch_name = branch.replace("remotes/origin/", "")

                # Get or create branch info
                if branch_name in self.branches:
                    info = self.branches[branch_name]
                else:
                    # Create minimal info for unknown branches
                    info = BranchInfo(
                        name=branch_name,
                        base_branch="unknown",
                        created_at=datetime.now(UTC),
                    )
                    self.branches[branch_name] = info

                if info.status == "active":
                    active_branches.append(info)

        return active_branches

    def get_branch_status(self, branch_name: str) -> dict[str, Any]:
        """Get detailed status of a branch."""
        if not self._branch_exists(branch_name):
            msg = f"Branch '{branch_name}' does not exist"
            raise ValueError(msg)

        # Get branch info
        info = self.branches.get(branch_name)
        if not info:
            info = BranchInfo(
                name=branch_name,
                base_branch="unknown",
                created_at=datetime.now(UTC),
            )

        # Get commits ahead/behind base
        base = info.base_branch
        if base != "unknown":
            # Check ahead/behind
            result = self._run_git_command(
                [
                    "rev-list",
                    "--left-right",
                    "--count",
                    f"origin/{base}...{branch_name}",
                ],
            )

            if result.stdout.strip():
                behind, ahead = map(int, result.stdout.strip().split())
            else:
                behind, ahead = 0, 0
        else:
            behind, ahead = 0, 0

        # Get last commit
        result = self._run_git_command(
            ["log", "-1", "--pretty=format:%H|%an|%ad|%s", branch_name],
        )

        last_commit = None
        if result.stdout.strip():
            parts = result.stdout.strip().split("|", 3)
            if len(parts) == 4:
                last_commit = {
                    "hash": parts[0][:8],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3],
                }

        return {
            "name": branch_name,
            "base_branch": info.base_branch,
            "created_at": info.created_at.isoformat(),
            "status": info.status,
            "ahead": ahead,
            "behind": behind,
            "last_commit": last_commit,
            "metadata": info.metadata,
        }

    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a specific branch."""
        if not self._branch_exists(branch_name):
            logger.error(f"Branch '{branch_name}' does not exist")
            return False

        try:
            self._run_git_command(["checkout", branch_name])
            logger.info(f"Switched to branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.exception("Failed to switch branch: %s", e)
            return False

    def update_branch_metadata(
        self,
        branch_name: str,
        metadata: dict[str, Any],
    ) -> None:
        """Update metadata for a branch."""
        if branch_name not in self.branches:
            logger.warning(f"Branch '{branch_name}' not in metadata, creating entry")
            self.branches[branch_name] = BranchInfo(
                name=branch_name,
                base_branch="unknown",
                created_at=datetime.now(UTC),
            )

        self.branches[branch_name].metadata.update(metadata)
        self._save_branch_metadata()

    def mark_branch_merged(self, branch_name: str) -> None:
        """Mark a branch as merged."""
        if branch_name in self.branches:
            self.branches[branch_name].status = "merged"
            self._save_branch_metadata()
            logger.info(f"Marked branch '{branch_name}' as merged")

    def cleanup_merged_branches(self, dry_run: bool = True) -> list[str]:
        """Clean up merged branches."""
        cleaned = []

        for branch_name, info in self.branches.items():
            if info.status == "merged" and self._branch_exists(branch_name):
                if not dry_run:
                    try:
                        # Delete local branch
                        self._run_git_command(["branch", "-d", branch_name])
                        logger.info(f"Deleted local branch: {branch_name}")

                        # Try to delete remote branch
                        self._run_git_command(
                            ["push", "origin", "--delete", branch_name],
                            check=False,
                        )

                    except subprocess.CalledProcessError as e:
                        logger.exception("Failed to delete branch %s: %s", branch_name, e)
                        continue

                cleaned.append(branch_name)

        if not dry_run:
            # Remove from metadata
            for branch in cleaned:
                del self.branches[branch]
            self._save_branch_metadata()

        return cleaned

    def get_branch_conflicts(
        self,
        branch_name: str,
        target_branch: str | None = None,
    ) -> dict[str, Any]:
        """Check for potential conflicts with target branch."""
        if not self._branch_exists(branch_name):
            msg = f"Branch '{branch_name}' does not exist"
            raise ValueError(msg)

        if target_branch is None:
            # Use base branch as target
            info = self.branches.get(branch_name)
            target_branch = info.base_branch if info else "develop"

        # Try merge in memory (dry run)
        result = self._run_git_command(
            ["merge-tree", f"origin/{target_branch}", branch_name],
            check=False,
        )

        conflicts = []
        if result.returncode != 0 or result.stdout.strip():
            # Parse conflict information
            for line in result.stdout.strip().split("\n"):
                if line.startswith("CONFLICT"):
                    conflicts.append(line)

        return {
            "branch": branch_name,
            "target": target_branch,
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
        }
