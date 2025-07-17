"""Simple test for branch testing integration without git dependency."""

import tempfile
from unittest.mock import Mock

import pytest

from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.branch_test_manager import BranchTestManager, TestSuite, TestType


def test_agent_pool_test_integration():
    """Test AgentPool test integration without git dependency."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create agent pool
        agent_pool = AgentPool(max_agents=2, work_dir=tmpdir)

        # Mock the branch test manager to avoid git operations
        mock_btm = Mock(spec=BranchTestManager)
        mock_btm.test_suites = {
            "unit_tests": TestSuite(
                name="unit_tests",
                test_type=TestType.UNIT,
                command=["python", "-m", "pytest"],
                critical=True,
            ),
            "lint_check": TestSuite(
                name="lint_check",
                test_type=TestType.LINT,
                command=["ruff", "check"],
                critical=False,
            ),
        }

        # Enable testing with mocked manager
        agent_pool.branch_test_manager = mock_btm
        agent_pool._test_integration_enabled = True

        # Test task creation
        task = agent_pool.create_test_task(
            branch_name="test-branch",
            test_suite_name="unit_tests",
            priority=8,
        )

        assert task.title == "Test unit_tests on test-branch"
        assert task.priority == 8
        assert task.metadata["type"] == "test"
        assert task.metadata["branch"] == "test-branch"
        assert task.metadata["test_suite"] == "unit_tests"
        assert "python" in task.command[0]


@pytest.mark.asyncio
async def test_auto_test_branch_creation():
    """Test automatic test task creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create agent pool
        agent_pool = AgentPool(max_agents=2, work_dir=tmpdir)

        # Mock the branch test manager
        mock_btm = Mock(spec=BranchTestManager)
        mock_btm.test_suites = {
            "critical_test": TestSuite(
                name="critical_test",
                test_type=TestType.UNIT,
                command=["pytest"],
                critical=True,
            ),
            "normal_test": TestSuite(
                name="normal_test",
                test_type=TestType.LINT,
                command=["ruff"],
                critical=False,
            ),
        }

        agent_pool.branch_test_manager = mock_btm
        agent_pool._test_integration_enabled = True

        # Create auto test tasks
        task_ids = await agent_pool.auto_test_branch("test-branch")

        # Should create 2 tasks: 1 critical + 1 combined non-critical
        assert len(task_ids) == 2
        assert len(agent_pool.tasks) == 2

        # Verify task types
        tasks = list(agent_pool.tasks.values())
        critical_task = next((t for t in tasks if t.metadata.get("test_suite") == "critical_test"), None)
        combined_task = next((t for t in tasks if t.metadata.get("test_suite") is None), None)

        assert critical_task is not None
        assert combined_task is not None
        assert critical_task.priority == 8  # High priority for critical
        assert combined_task.priority == 6  # Medium priority for combined


def test_branch_test_status_retrieval():
    """Test retrieving branch test status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent_pool = AgentPool(max_agents=2, work_dir=tmpdir)

        # Mock the branch test manager with test summary
        mock_btm = Mock(spec=BranchTestManager)
        mock_btm.get_branch_test_summary.return_value = {
            "branch": "test-branch",
            "total_tests": 3,
            "passed": 2,
            "failed": 1,
            "status": "failed",
        }

        agent_pool.branch_test_manager = mock_btm
        agent_pool._test_integration_enabled = True

        status = agent_pool.get_branch_test_status("test-branch")

        assert status["branch"] == "test-branch"
        assert status["total_tests"] == 3
        assert status["passed"] == 2
        assert status["failed"] == 1
        assert status["status"] == "failed"


def test_error_handling_when_testing_disabled():
    """Test error handling when branch testing is not enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent_pool = AgentPool(max_agents=2, work_dir=tmpdir)
        # Don't enable branch testing

        with pytest.raises(RuntimeError, match="Branch testing is not enabled"):
            agent_pool.create_test_task("test-branch", "unit_tests")

        status = agent_pool.get_branch_test_status("test-branch")
        assert "error" in status


if __name__ == "__main__":
    pytest.main([__file__])
