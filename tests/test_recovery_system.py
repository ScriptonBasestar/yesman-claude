"""Test rollback mechanism and error recovery system."""

import asyncio
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.recovery_engine import (
    OperationSnapshot,
    OperationType,
    RecoveryAction,
    RecoveryEngine,
)
from libs.multi_agent.types import AgentState, Task, TaskStatus


class TestRecoveryEngine:
    """Test recovery engine functionality."""

    @pytest.fixture
    def temp_work_dir(self) -> Iterator[str]:
        """Create temporary work directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def recovery_engine(self, temp_work_dir: str) -> RecoveryEngine:
        """Create recovery engine for testing."""
        return RecoveryEngine(work_dir=temp_work_dir, max_snapshots=10)

    def test_recovery_engine_initialization(self, recovery_engine: RecoveryEngine) -> None:
        """Test recovery engine initialization."""
        assert recovery_engine.work_dir.exists()
        assert recovery_engine.snapshots_dir.exists()
        assert recovery_engine.backups_dir.exists()
        assert len(recovery_engine.recovery_strategies) > 0
        assert "task_timeout" in recovery_engine.recovery_strategies
        assert "agent_error" in recovery_engine.recovery_strategies

    def test_operation_snapshot_serialization(self) -> None:
        """Test snapshot serialization/deserialization."""
        snapshot = OperationSnapshot(
            snapshot_id="test-snapshot",
            operation_type=OperationType.TASK_EXECUTION,
            timestamp=datetime.now(),
            description="Test snapshot",
            agent_states={"agent-1": {"state": "idle"}},
            task_states={"task-1": {"status": "pending"}},
            operation_context={"test": True},
        )

        # Test serialization
        data = snapshot.to_dict()
        assert data["snapshot_id"] == "test-snapshot"
        assert data["operation_type"] == "task_execution"

        # Test deserialization
        restored = OperationSnapshot.from_dict(data)
        assert restored.snapshot_id == snapshot.snapshot_id
        assert restored.operation_type == snapshot.operation_type
        assert restored.agent_states == snapshot.agent_states

    def test_recovery_strategy_registration(self, recovery_engine: RecoveryEngine) -> None:
        """Test registering custom recovery strategies."""
        recovery_engine.register_recovery_strategy(
            name="custom_test",
            error_pattern=r"test.*error",
            max_retries=5,
            retry_delay=2.0,
            recovery_actions=[RecoveryAction.RETRY, RecoveryAction.ROLLBACK],
        )

        assert "custom_test" in recovery_engine.recovery_strategies
        strategy = recovery_engine.recovery_strategies["custom_test"]
        assert strategy.max_retries == 5
        assert strategy.retry_delay == 2.0
        assert RecoveryAction.RETRY in strategy.recovery_actions

    @pytest.mark.asyncio
    async def test_snapshot_creation(self, recovery_engine: RecoveryEngine) -> None:
        """Test creating operation snapshots."""
        # Create mock agent pool
        agent_pool = Mock()
        agent_pool.agents = {
            "agent-1": Mock(to_dict=Mock(return_value={"agent_id": "agent-1", "state": "idle"})),
        }
        agent_pool.tasks = {
            "task-1": Mock(to_dict=Mock(return_value={"task_id": "task-1", "status": "pending"})),
        }

        snapshot_id = await recovery_engine.create_snapshot(
            operation_type=OperationType.TASK_EXECUTION,
            description="Test snapshot",
            agent_pool=agent_pool,
            operation_context={"test": True},
        )

        assert snapshot_id is not None
        assert snapshot_id in recovery_engine.snapshots

        snapshot = recovery_engine.snapshots[snapshot_id]
        assert snapshot.description == "Test snapshot"
        assert snapshot.operation_type == OperationType.TASK_EXECUTION
        assert len(snapshot.agent_states) == 1
        assert len(snapshot.task_states) == 1

    @pytest.mark.asyncio
    async def test_file_backup_and_restore(self, recovery_engine: RecoveryEngine, temp_work_dir: str) -> None:
        """Test file backup and restore functionality."""
        # Create test file
        test_file = Path(temp_work_dir) / "test.txt"
        test_file.write_text("original content")

        # Create snapshot with file backup
        snapshot_id = await recovery_engine.create_snapshot(
            operation_type=OperationType.FILE_MODIFICATION,
            description="File modification test",
            files_to_backup=[str(test_file)],
        )

        # Modify the file
        test_file.write_text("modified content")
        assert test_file.read_text() == "modified content"

        # Rollback
        success = await recovery_engine.rollback_operation(snapshot_id)
        assert success

        # Verify file was restored
        assert test_file.read_text() == "original content"

    @pytest.mark.asyncio
    async def test_agent_state_rollback(self, recovery_engine: RecoveryEngine) -> None:
        """Test rolling back agent states."""
        # Create mock agent pool
        agent_pool = Mock()

        # Create agent with initial state
        agent = Mock()
        agent.agent_id = "agent-1"
        agent.state = AgentState.IDLE
        agent.current_task = None
        agent.process = None
        agent.to_dict.return_value = {
            "agent_id": "agent-1",
            "state": "idle",
            "current_task": None,
        }

        agent_pool.agents = {"agent-1": agent}
        agent_pool.tasks = {}

        # Create snapshot
        snapshot_id = await recovery_engine.create_snapshot(
            operation_type=OperationType.AGENT_ASSIGNMENT,
            description="Agent assignment test",
            agent_pool=agent_pool,
        )

        # Modify agent state
        agent.state = AgentState.WORKING
        agent.current_task = "task-1"

        # Rollback
        success = await recovery_engine.rollback_operation(
            snapshot_id,
            agent_pool=agent_pool,
        )
        assert success

        # Verify agent state was restored
        assert agent.state == AgentState.IDLE
        assert agent.current_task is None

    @pytest.mark.asyncio
    async def test_error_strategy_matching(self, recovery_engine: RecoveryEngine) -> None:
        """Test finding appropriate recovery strategies for different errors."""
        # Test timeout error
        strategy = recovery_engine._find_recovery_strategy("Task timed out after 300 seconds")  # noqa: SLF001
        assert strategy is not None
        assert strategy.error_pattern == r"timed? ?out|timeout"

        # Test agent error
        strategy = recovery_engine._find_recovery_strategy("Agent execution error occurred")  # noqa: SLF001
        assert strategy is not None
        assert "agent" in strategy.error_pattern.lower()

        # Test git error
        strategy = recovery_engine._find_recovery_strategy("fatal: git repository not found")  # noqa: SLF001
        assert strategy is not None
        assert "git" in strategy.error_pattern.lower()

        # Test generic error (fallback)
        strategy = recovery_engine._find_recovery_strategy("Some unknown error")  # noqa: SLF001
        assert strategy is not None

    @pytest.mark.asyncio
    async def test_operation_failure_handling(self, recovery_engine: RecoveryEngine) -> None:
        """Test handling operation failures with recovery."""
        # Mock agent pool
        agent_pool = Mock()
        agent_pool.agents = {"agent-1": Mock(to_dict=Mock(return_value={"agent_id": "agent-1"}))}
        agent_pool.tasks = {"task-1": Mock(to_dict=Mock(return_value={"task_id": "task-1"}))}

        # Create snapshot first
        snapshot_id = await recovery_engine.create_snapshot(
            operation_type=OperationType.TASK_EXECUTION,
            description="Test operation",
            agent_pool=agent_pool,
        )

        # Register operation
        operation_id = "test-operation"
        recovery_engine.start_operation(operation_id, snapshot_id)

        # Test failure handling
        exception = Exception("Task timeout error")
        context = {
            "operation_type": "task_execution",
            "agent_id": "agent-1",
        }

        # Mock recovery action to succeed
        with patch.object(recovery_engine, "_execute_recovery_action", return_value=True):
            success = await recovery_engine.handle_operation_failure(
                operation_id=operation_id,
                exception=exception,
                context=context,
                agent_pool=agent_pool,
            )

        assert success
        assert recovery_engine.recovery_metrics["failed_operations"] > 0
        assert recovery_engine.recovery_metrics["successful_recoveries"] > 0

    @pytest.mark.asyncio
    async def test_recovery_action_execution(self, recovery_engine: RecoveryEngine) -> None:
        """Test execution of different recovery actions."""
        # Test SKIP action
        success = await recovery_engine._execute_recovery_action(  # noqa: SLF001
            action=RecoveryAction.SKIP,
            snapshot_id=None,
            exception=Exception("test"),
            context={},
        )
        assert success

        # Test RESET_AGENT action
        agent_pool = Mock()
        agent = Mock()
        agent.process = None
        agent.state = AgentState.ERROR
        agent.current_task = "task-1"
        agent_pool.agents = {"agent-1": agent}

        success = await recovery_engine._execute_recovery_action(  # noqa: SLF001
            action=RecoveryAction.RESET_AGENT,
            snapshot_id=None,
            exception=Exception("test"),
            context={"agent_id": "agent-1"},
            agent_pool=agent_pool,
        )
        assert success
        assert agent.state == AgentState.IDLE
        assert agent.current_task is None

    def test_snapshot_cleanup(self, recovery_engine: RecoveryEngine) -> None:
        """Test automatic cleanup of old snapshots."""
        # Create multiple snapshots
        for i in range(15):  # More than max_snapshots (10)
            snapshot = OperationSnapshot(
                snapshot_id=f"snapshot-{i}",
                operation_type=OperationType.TASK_EXECUTION,
                timestamp=datetime.now(),
                description=f"Test snapshot {i}",
            )
            recovery_engine.snapshots[snapshot.snapshot_id] = snapshot

        # Initial count should be 15
        assert len(recovery_engine.snapshots) == 15

        # Cleanup should reduce to max_snapshots
        asyncio.run(recovery_engine._cleanup_old_snapshots())  # noqa: SLF001
        assert len(recovery_engine.snapshots) <= recovery_engine.max_snapshots

    def test_metrics_tracking(self, recovery_engine: RecoveryEngine) -> None:
        """Test recovery metrics tracking."""
        initial_metrics = recovery_engine.get_recovery_metrics()

        # Simulate some operations
        recovery_engine.recovery_metrics["total_operations"] += 5
        recovery_engine.recovery_metrics["failed_operations"] += 2
        recovery_engine.recovery_metrics["successful_recoveries"] += 1
        recovery_engine.recovery_metrics["rollbacks_performed"] += 1

        updated_metrics = recovery_engine.get_recovery_metrics()

        assert updated_metrics["total_operations"] == initial_metrics["total_operations"] + 5
        assert updated_metrics["failed_operations"] == initial_metrics["failed_operations"] + 2
        assert updated_metrics["successful_recoveries"] == initial_metrics["successful_recoveries"] + 1
        assert updated_metrics["rollbacks_performed"] == initial_metrics["rollbacks_performed"] + 1

    def test_state_persistence(self, recovery_engine: RecoveryEngine) -> None:
        """Test persistence of recovery state."""
        # Add some data
        recovery_engine.failure_counts["test_operation"] = 3

        # Save state
        recovery_engine._save_state()  # noqa: SLF001

        # Clear current data
        recovery_engine.failure_counts.clear()

        # Load state back
        recovery_engine._load_state()  # noqa: SLF001

        # Verify data was persisted
        assert recovery_engine.failure_counts.get("test_operation") == 3

        # Test that state file exists
        state_file = recovery_engine._get_state_file()  # noqa: SLF001
        assert state_file.exists()


class TestAgentPoolRecoveryIntegration:
    """Test integration of recovery system with AgentPool."""

    @pytest.fixture
    def agent_pool(self) -> Iterator[AgentPool]:
        """Create agent pool for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pool = AgentPool(max_agents=2, work_dir=tmpdir)
            yield pool

    def test_recovery_system_enablement(self, agent_pool: AgentPool) -> None:
        """Test enabling recovery system in agent pool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_recovery_system(work_dir=tmpdir)

            assert agent_pool._recovery_enabled  # noqa: SLF001
            assert agent_pool.recovery_engine is not None

    @pytest.mark.asyncio
    async def test_snapshot_creation_via_agent_pool(self, agent_pool: AgentPool) -> None:
        """Test creating snapshots through agent pool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_recovery_system(work_dir=tmpdir)

            snapshot_id = await agent_pool.create_operation_snapshot(
                operation_type="task_execution",
                description="Test operation",
                context={"test": True},
            )

            assert snapshot_id is not None
            assert snapshot_id in agent_pool.recovery_engine.snapshots

    @pytest.mark.asyncio
    async def test_manual_rollback_via_agent_pool(self, agent_pool: AgentPool) -> None:
        """Test manual rollback through agent pool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_recovery_system(work_dir=tmpdir)

            # Create snapshot
            snapshot_id = await agent_pool.create_operation_snapshot(
                operation_type="task_execution",
                description="Test operation",
            )

            # Attempt rollback
            success = await agent_pool.rollback_to_snapshot(snapshot_id)
            assert success

    def test_recovery_status_retrieval(self, agent_pool: AgentPool) -> None:
        """Test retrieving recovery status."""
        # Without recovery enabled
        status = agent_pool.get_recovery_status()
        assert status["recovery_enabled"] is False

        # With recovery enabled
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_recovery_system(work_dir=tmpdir)
            status = agent_pool.get_recovery_status()

            assert status["recovery_enabled"] is True
            assert "metrics" in status
            assert "recent_operations" in status

    def test_snapshot_listing(self, agent_pool: AgentPool) -> None:
        """Test listing recovery snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_recovery_system(work_dir=tmpdir)

            # Initially no snapshots
            snapshots = agent_pool.list_recovery_snapshots()
            assert len(snapshots) == 0

            # Create a snapshot manually
            snapshot = OperationSnapshot(
                snapshot_id="test-snapshot",
                operation_type=OperationType.TASK_EXECUTION,
                timestamp=datetime.now(),
                description="Test snapshot",
            )
            agent_pool.recovery_engine.snapshots["test-snapshot"] = snapshot

            # Should now appear in list
            snapshots = agent_pool.list_recovery_snapshots()
            assert len(snapshots) == 1
            assert snapshots[0]["snapshot_id"] == "test-snapshot"

    @pytest.mark.asyncio
    async def test_execute_with_recovery(self, agent_pool: AgentPool) -> None:
        """Test executing operations with automatic recovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_recovery_system(work_dir=tmpdir)

            # Test successful operation
            async def successful_operation() -> str:
                return "success"

            success, result = await agent_pool.execute_with_recovery(
                operation_func=successful_operation,
                operation_type="task_execution",
                description="Test successful operation",
            )

            assert success is True
            assert result == "success"

            # Test failing operation with retries
            call_count = 0

            async def failing_operation() -> str:
                nonlocal call_count
                call_count += 1
                if call_count < 3:  # Fail first 2 times
                    msg = "Test failure"
                    raise Exception(msg)
                return "success after retries"

            success, result = await agent_pool.execute_with_recovery(
                operation_func=failing_operation,
                operation_type="task_execution",
                description="Test failing operation",
                max_retries=3,
            )

            assert success is True
            assert result == "success after retries"
            assert call_count == 3

    def test_error_handling_when_recovery_disabled(self, agent_pool: AgentPool) -> None:
        """Test error handling when recovery system is not enabled."""
        # Don't enable recovery system

        status = agent_pool.get_recovery_status()
        assert status["recovery_enabled"] is False

        snapshots = agent_pool.list_recovery_snapshots()
        assert len(snapshots) == 0

    @pytest.mark.asyncio
    async def test_task_failure_callback_integration(self, agent_pool: AgentPool) -> None:
        """Test that task failures trigger recovery callbacks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_recovery_system(work_dir=tmpdir)

            # Create a task
            task = Task(
                task_id="test-task",
                title="Test Task",
                description="Test task for recovery",
                command=["echo", "test"],
                working_directory=".",
                status=TaskStatus.FAILED,
                error="Test error for recovery",
            )

            # Mock the recovery engine's handle_operation_failure
            with patch.object(
                agent_pool.recovery_engine,
                "handle_operation_failure",
                new_callable=AsyncMock,
            ) as mock_handle:
                # Trigger task failed callbacks
                for callback in agent_pool.task_failed_callbacks:
                    await callback(task)

                # Verify that recovery was attempted
                mock_handle.assert_called_once()
                call_args = mock_handle.call_args
                assert call_args[1]["context"]["task_id"] == "test-task"


if __name__ == "__main__":
    pytest.main([__file__])
