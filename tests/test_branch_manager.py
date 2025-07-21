"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Tests for BranchManager class."""

import subprocess
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from libs.multi_agent.branch_manager import BranchInfo, BranchManager


class TestBranchManager:
    """Test cases for BranchManager."""

    @pytest.fixture
    @staticmethod
    def mock_git_repo( tmp_path: Path) -> Path:
        """Create a mock git repository."""
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

        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "."], check=False, cwd=repo_path)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=False, cwd=repo_path)

        # Create develop branch
        subprocess.run(["git", "checkout", "-b", "develop"], check=False, cwd=repo_path)

        return repo_path

    @pytest.fixture
    @staticmethod
    def branch_manager(mock_git_repo: Path) -> BranchManager:
        """Create BranchManager instance."""
        return BranchManager(repo_path=str(mock_git_repo))

    @staticmethod
    def test_init(branch_manager: BranchManager, mock_git_repo: Path) -> None:
        """Test BranchManager initialization."""
        assert branch_manager.repo_path == mock_git_repo
        assert branch_manager.branch_prefix == "feat/multi-agent"
        assert branch_manager.branches == {}

    @staticmethod
    def test_get_current_branch(branch_manager: BranchManager) -> None:
        """Test getting current branch."""
        current = branch_manager._get_current_branch()
        assert current == "develop"

    @staticmethod
    def test_branch_exists(branch_manager: BranchManager) -> None:
        """Test checking if branch exists."""
        assert branch_manager._branch_exists("develop") is True
        assert branch_manager._branch_exists("nonexistent") is False

    @staticmethod
    def test_create_feature_branch(branch_manager: BranchManager) -> None:
        """Test creating a feature branch."""
        with patch.object(branch_manager, "_run_git_command") as mock_run:
            # Mock responses
            mock_run.side_effect = [
                MagicMock(stdout="develop\n* main\n"),  # branch exists check
                MagicMock(),  # fetch
                MagicMock(),  # checkout -b
            ]

            branch_name = branch_manager.create_feature_branch(
                "test-issue-123",
                base_branch="develop",
            )

            assert branch_name.startswith("feat/multi-agent/test-issue-123-")
            assert branch_name in branch_manager.branches

            # Check branch info
            info = branch_manager.branches[branch_name]
            assert info.name == branch_name
            assert info.base_branch == "develop"
            assert info.status == "active"
            assert info.metadata["issue_name"] == "test-issue-123"

    @staticmethod
    def test_create_feature_branch_sanitization(branch_manager: BranchManager) -> None:
        """Test branch name sanitization."""
        with patch.object(branch_manager, "_run_git_command") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="develop\n"),
                MagicMock(),
                MagicMock(),
            ]

            branch_name = branch_manager.create_feature_branch(
                "Test Issue #123 (with special chars!)",
            )

            # Check sanitization
            assert "test-issue-123-with-special-chars" in branch_name
            assert "#" not in branch_name
            assert "(" not in branch_name
            assert "!" not in branch_name

    @staticmethod
    def test_list_active_branches(branch_manager: BranchManager) -> None:
        """Test listing active branches."""
        # Add some test branches to metadata
        branch1 = BranchInfo(
            name="feat/multi-agent/issue1",
            base_branch="develop",
            created_at=datetime.now(UTC),
            status="active",
        )
        branch2 = BranchInfo(
            name="feat/multi-agent/issue2",
            base_branch="develop",
            created_at=datetime.now(UTC),
            status="merged",
        )

        branch_manager.branches = {branch1.name: branch1, branch2.name: branch2}

        with patch.object(branch_manager, "_run_git_command") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="  develop\n  feat/multi-agent/issue1\n  feat/multi-agent/issue2\n",
            )

            active = branch_manager.list_active_branches()

            assert len(active) == 1
            assert active[0].name == "feat/multi-agent/issue1"

    @staticmethod
    def test_get_branch_status(branch_manager: BranchManager) -> None:
        """Test getting branch status."""
        branch_info = BranchInfo(
            name="feat/multi-agent/test",
            base_branch="develop",
            created_at=datetime.now(UTC),
        )
        branch_manager.branches["feat/multi-agent/test"] = branch_info

        with patch.object(branch_manager, "_run_git_command") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="feat/multi-agent/test\n"),  # branch exists
                MagicMock(stdout="2\t5"),  # ahead/behind
                MagicMock(
                    stdout="abc123|John Doe|2024-01-10|Test commit",
                ),  # last commit
            ]

            status = branch_manager.get_branch_status("feat/multi-agent/test")

            assert status["name"] == "feat/multi-agent/test"
            assert status["base_branch"] == "develop"
            assert status["ahead"] == 5
            assert status["behind"] == 2
            assert status["last_commit"]["hash"] == "abc123"
            assert status["last_commit"]["message"] == "Test commit"

    @staticmethod
    def test_switch_branch(branch_manager: BranchManager) -> None:
        """Test switching branches."""
        with patch.object(branch_manager, "_run_git_command") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="develop\n"),  # branch exists
                MagicMock(),  # checkout
            ]

            result = branch_manager.switch_branch("develop")
            assert result is True

            # Test non-existent branch
            mock_run.side_effect = [
                MagicMock(stdout=""),  # branch doesn't exist
            ]

            result = branch_manager.switch_branch("nonexistent")
            assert result is False

    @staticmethod
    def test_update_branch_metadata(branch_manager: BranchManager) -> None:
        """Test updating branch metadata."""
        branch_name = "feat/multi-agent/test"

        # Update non-existent branch
        branch_manager.update_branch_metadata(
            branch_name,
            {"agent_id": "agent-1", "task": "implement feature"},
        )

        assert branch_name in branch_manager.branches
        assert branch_manager.branches[branch_name].metadata["agent_id"] == "agent-1"
        assert branch_manager.branches[branch_name].metadata["task"] == "implement feature"

    @staticmethod
    def test_mark_branch_merged(branch_manager: BranchManager) -> None:
        """Test marking branch as merged."""
        branch_info = BranchInfo(
            name="feat/multi-agent/test",
            base_branch="develop",
            created_at=datetime.now(UTC),
            status="active",
        )
        branch_manager.branches[branch_info.name] = branch_info

        branch_manager.mark_branch_merged(branch_info.name)

        assert branch_manager.branches[branch_info.name].status == "merged"

    @staticmethod
    def test_cleanup_merged_branches(branch_manager: BranchManager) -> None:
        """Test cleaning up merged branches."""
        # Add test branches
        branch1 = BranchInfo(
            name="feat/multi-agent/merged1",
            base_branch="develop",
            created_at=datetime.now(UTC),
            status="merged",
        )
        branch2 = BranchInfo(
            name="feat/multi-agent/active1",
            base_branch="develop",
            created_at=datetime.now(UTC),
            status="active",
        )

        branch_manager.branches = {branch1.name: branch1, branch2.name: branch2}

        with patch.object(branch_manager, "_branch_exists", return_value=True):
            # Dry run
            cleaned = branch_manager.cleanup_merged_branches(dry_run=True)
            assert len(cleaned) == 1
            assert branch1.name in cleaned
            assert len(branch_manager.branches) == 2  # Not removed in dry run

            # Actual cleanup
            with patch.object(branch_manager, "_run_git_command"):
                cleaned = branch_manager.cleanup_merged_branches(dry_run=False)
                assert len(cleaned) == 1
                assert branch1.name not in branch_manager.branches
                assert branch2.name in branch_manager.branches

    @staticmethod
    def test_get_branch_conflicts(branch_manager: BranchManager) -> None:
        """Test checking branch conflicts."""
        with patch.object(branch_manager, "_run_git_command") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="feat/multi-agent/test\n"),  # branch exists
                MagicMock(
                    stdout="CONFLICT (content): Merge conflict in file.py\n",
                    returncode=1,
                ),
            ]

            conflicts = branch_manager.get_branch_conflicts(
                "feat/multi-agent/test",
                "develop",
            )

            assert conflicts["has_conflicts"] is True
            assert len(conflicts["conflicts"]) == 1
            assert "file.py" in conflicts["conflicts"][0]

    @staticmethod
    def test_metadata_persistence(branch_manager: BranchManager, tmp_path: Path) -> None:  # noqa: ARG002
        """Test saving and loading branch metadata."""
        # Create test branch info
        branch_info = BranchInfo(
            name="feat/multi-agent/test",
            base_branch="develop",
            created_at=datetime.now(UTC),
            metadata={"test": "value"},
        )

        branch_manager.branches[branch_info.name] = branch_info

        # Save metadata
        branch_manager._save_branch_metadata()

        # Create new manager instance to test loading
        new_manager = BranchManager(repo_path=str(branch_manager.repo_path))

        assert len(new_manager.branches) == 1
        assert "feat/multi-agent/test" in new_manager.branches
        loaded_info = new_manager.branches["feat/multi-agent/test"]
        assert loaded_info.base_branch == "develop"
        assert loaded_info.metadata["test"] == "value"
