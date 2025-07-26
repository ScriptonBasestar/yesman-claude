# Copyright notice.

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from libs.multi_agent.branch_info_protocol import (
    BranchInfo,
    BranchInfoProtocol,
    BranchInfoType,
    BranchSyncEvent,
    SyncStrategy,
)


class TestBranchInfo:
    """Test cases for BranchInfo dataclass."""

    @staticmethod
    def test_init() -> None:
        """Test BranchInfo initialization."""
        now = datetime.now(UTC)
        branch_info = BranchInfo(
            branch_name="feature-x",
            agent_id="agent-1",
            base_branch="main",
            created_at=now,
            last_updated=now,
            commit_count=5,
            files_modified=["file1.py", "file2.py"],
            tests_passed=True,
            build_status="success",
            merge_ready=True,
            work_items=["Task 1", "Task 2"],
        )

        assert branch_info.branch_name == "feature-x"
        assert branch_info.agent_id == "agent-1"
        assert branch_info.base_branch == "main"
        assert branch_info.commit_count == 5
        assert len(branch_info.files_modified) == 2
        assert branch_info.tests_passed is True
        assert branch_info.build_status == "success"
        assert branch_info.merge_ready is True
        assert len(branch_info.work_items) == 2
        assert branch_info.conflicts_detected == []
        assert branch_info.dependencies == {}
        assert branch_info.api_signatures == {}


class TestBranchSyncEvent:
    """Test cases for BranchSyncEvent dataclass."""

    @staticmethod
    def test_init() -> None:
        """Test BranchSyncEvent initialization."""
        event = BranchSyncEvent(
            event_id="sync-1",
            branch_name="feature-x",
            agent_id="agent-1",
            event_type=BranchInfoType.FILE_CHANGES,
            event_data={"files": ["file1.py", "file2.py"]},
            priority=MessagePriority.HIGH,
            requires_action=True,
            action_items=["Review changes", "Update tests"],
        )

        assert event.event_id == "sync-1"
        assert event.branch_name == "feature-x"
        assert event.agent_id == "agent-1"
        assert event.event_type == BranchInfoType.FILE_CHANGES
        assert event.event_data == {"files": ["file1.py", "file2.py"]}
        assert event.priority == MessagePriority.HIGH
        assert event.requires_action is True
        assert len(event.action_items) == 2
        assert isinstance(event.timestamp, datetime)


class TestBranchInfoProtocol:
    """Test cases for BranchInfoProtocol."""

    @pytest.fixture
    @staticmethod
    def mock_branch_manager() -> Mock:
        """Create mock branch manager."""
        return Mock(spec=BranchManager)

    @pytest.fixture
    @staticmethod
    def mock_collaboration_engine() -> Mock:
        """Create mock collaboration engine."""
        engine = Mock(spec=CollaborationEngine)
        engine.share_knowledge = AsyncMock(return_value="knowledge-123")
        engine.send_message = AsyncMock(return_value="message-123")
        return engine

    @pytest.fixture
    @staticmethod
    def protocol(
        mock_branch_manager: Mock, mock_collaboration_engine: Mock
    ) -> BranchInfoProtocol:
        """Create BranchInfoProtocol instance."""
        return BranchInfoProtocol(
            branch_manager=mock_branch_manager,
            collaboration_engine=mock_collaboration_engine,
            sync_strategy=SyncStrategy.SMART,
        )

    @staticmethod
    def test_init(
        protocol: BranchInfoProtocol,
        mock_branch_manager: Mock,
        mock_collaboration_engine: Mock,
    ) -> None:
        """Test BranchInfoProtocol initialization."""
        assert protocol.branch_manager == mock_branch_manager
        assert protocol.collaboration_engine == mock_collaboration_engine
        assert protocol.sync_strategy == SyncStrategy.SMART
        assert protocol.branch_info == {}
        assert protocol.sync_history == []
        assert len(protocol.branch_subscriptions) == 0
        assert protocol.sync_interval == 300
        assert protocol._running is False
        assert protocol._sync_task is None

    @pytest.mark.asyncio
    @staticmethod
    async def test_start_stop(protocol: BranchInfoProtocol) -> None:
        """Test starting and stopping the protocol."""
        # Start protocol
        await protocol.start()
        assert protocol._running is True
        assert protocol._sync_task is not None

        # Stop protocol
        await protocol.stop()
        assert protocol._running is False

    @pytest.mark.asyncio
    @staticmethod
    async def test_register_branch(protocol: BranchInfoProtocol) -> None:
        """Test registering a new branch."""
        branch_info = await protocol.register_branch(
            branch_name="feature-xyz",
            agent_id="agent-1",
            base_branch="develop",
            work_items=["Implement feature", "Write tests"],
        )

        assert branch_info.branch_name == "feature-xyz"
        assert branch_info.agent_id == "agent-1"
        assert branch_info.base_branch == "develop"
        assert len(branch_info.work_items) == 2
        assert "feature-xyz" in protocol.branch_info
        assert "agent-1" in protocol.branch_subscriptions["feature-xyz"]
        assert protocol.protocol_stats["subscriptions_active"] == 1

        # Check that knowledge was shared
        protocol.collaboration_engine.share_knowledge.assert_called_once()
        call_args = protocol.collaboration_engine.share_knowledge.call_args[1]
        assert call_args["contributor_id"] == "agent-1"
        assert "branch_info" in call_args["tags"]

    @pytest.mark.asyncio
    @staticmethod
    async def test_update_branch_info_file_changes(
        protocol: BranchInfoProtocol,
    ) -> None:
        """Test updating branch info with file changes."""
        # Register branch first
        await protocol.register_branch("feature-x", "agent-1")

        # Update with file changes
        await protocol.update_branch_info(
            branch_name="feature-x",
            info_type=BranchInfoType.FILE_CHANGES,
            update_data={"files": ["src/main.py", "src/utils.py"]},
        )

        branch_info = protocol.branch_info["feature-x"]
        assert branch_info.files_modified == ["src/main.py", "src/utils.py"]
        assert branch_info.last_updated > branch_info.created_at

    @pytest.mark.asyncio
    @staticmethod
    async def test_update_branch_info_test_status(protocol: BranchInfoProtocol) -> None:
        """Test updating branch info with test status."""
        await protocol.register_branch("feature-x", "agent-1")

        await protocol.update_branch_info(
            branch_name="feature-x",
            info_type=BranchInfoType.TEST_STATUS,
            update_data={"passed": True},
        )

        branch_info = protocol.branch_info["feature-x"]
        assert branch_info.tests_passed is True

    @pytest.mark.asyncio
    @staticmethod
    async def test_update_branch_info_build_status(
        protocol: BranchInfoProtocol,
    ) -> None:
        """Test updating branch info with build status."""
        await protocol.register_branch("feature-x", "agent-1")

        await protocol.update_branch_info(
            branch_name="feature-x",
            info_type=BranchInfoType.BUILD_STATUS,
            update_data={"status": "success"},
            requires_immediate_sync=True,  # Force sync
        )

        branch_info = protocol.branch_info["feature-x"]
        assert branch_info.build_status == "success"

        # Check that immediate sync was triggered
        assert (
            protocol.collaboration_engine.share_knowledge.call_count >= 2
        )  # Initial + update

    @pytest.mark.asyncio
    @staticmethod
    async def test_update_branch_info_conflicts(protocol: BranchInfoProtocol) -> None:
        """Test updating branch info with conflict information."""
        await protocol.register_branch("feature-x", "agent-1")

        conflicts = ["Merge conflict in main.py", "API signature mismatch"]
        await protocol.update_branch_info(
            branch_name="feature-x",
            info_type=BranchInfoType.CONFLICT_INFO,
            update_data={"conflicts": conflicts},
        )

        branch_info = protocol.branch_info["feature-x"]
        assert branch_info.conflicts_detected == conflicts
        assert protocol.protocol_stats["conflicts_detected"] == 2

    @pytest.mark.asyncio
    @staticmethod
    async def test_update_branch_info_api_changes(protocol: BranchInfoProtocol) -> None:
        """Test updating branch info with API changes."""
        await protocol.register_branch("feature-x", "agent-1")

        api_changes = {
            "process_data": {"args": ["data", "options"], "return": "DataFrame"},
            "validate_input": {"args": ["input"], "return": "bool"},
        }

        await protocol.update_branch_info(
            branch_name="feature-x",
            info_type=BranchInfoType.API_CHANGES,
            update_data={"signatures": api_changes},
        )

        branch_info = protocol.branch_info["feature-x"]
        assert branch_info.api_signatures == api_changes
        assert protocol.protocol_stats["api_changes_tracked"] == 1

    @pytest.mark.asyncio
    @staticmethod
    async def test_update_branch_info_dependencies(
        protocol: BranchInfoProtocol,
    ) -> None:
        """Test updating branch info with dependency map."""
        await protocol.register_branch("feature-x", "agent-1")

        dependencies = {
            "main.py": ["utils.py", "config.py"],
            "utils.py": ["constants.py"],
        }

        await protocol.update_branch_info(
            branch_name="feature-x",
            info_type=BranchInfoType.DEPENDENCY_MAP,
            update_data={"dependencies": dependencies},
        )

        branch_info = protocol.branch_info["feature-x"]
        assert branch_info.dependencies == dependencies

    @pytest.mark.asyncio
    @staticmethod
    async def test_update_branch_info_merge_readiness(
        protocol: BranchInfoProtocol,
    ) -> None:
        """Test updating branch info with merge readiness."""
        await protocol.register_branch("feature-x", "agent-1")

        await protocol.update_branch_info(
            branch_name="feature-x",
            info_type=BranchInfoType.MERGE_READINESS,
            update_data={"ready": True},
        )

        branch_info = protocol.branch_info["feature-x"]
        assert branch_info.merge_ready is True
        assert protocol.protocol_stats["merge_ready_branches"] == 1

    @pytest.mark.asyncio
    @staticmethod
    async def test_update_branch_info_work_progress(
        protocol: BranchInfoProtocol,
    ) -> None:
        """Test updating branch info with work progress."""
        await protocol.register_branch(
            "feature-x",
            "agent-1",
            work_items=["Task 1", "Task 2", "Task 3"],
        )

        await protocol.update_branch_info(
            branch_name="feature-x",
            info_type=BranchInfoType.WORK_PROGRESS,
            update_data={
                "completed": ["Task 1"],
                "remaining": ["Task 2", "Task 3"],
            },
        )

        branch_info = protocol.branch_info["feature-x"]
        assert branch_info.work_items == ["Task 2", "Task 3"]
        assert branch_info.metadata["completed_items"] == ["Task 1"]

    @pytest.mark.asyncio
    @staticmethod
    async def test_get_branch_info(protocol: BranchInfoProtocol) -> None:
        """Test getting branch information."""
        await protocol.register_branch("feature-x", "agent-1")

        # Get existing branch
        info = await protocol.get_branch_info("feature-x")
        assert info is not None
        assert info.branch_name == "feature-x"

        # Get non-existent branch
        info = await protocol.get_branch_info("non-existent")
        assert info is None

    @pytest.mark.asyncio
    @staticmethod
    async def test_get_all_branches_info(protocol: BranchInfoProtocol) -> None:
        """Test getting all branches information."""
        await protocol.register_branch("feature-x", "agent-1")
        await protocol.register_branch("feature-y", "agent-2")

        all_info = await protocol.get_all_branches_info()
        assert len(all_info) == 2
        assert "feature-x" in all_info
        assert "feature-y" in all_info

    @pytest.mark.asyncio
    @staticmethod
    async def test_subscribe_to_branch(protocol: BranchInfoProtocol) -> None:
        """Test subscribing to branch updates."""
        await protocol.register_branch("feature-x", "agent-1")

        # Subscribe another agent
        await protocol.subscribe_to_branch("agent-2", "feature-x")

        assert "agent-2" in protocol.branch_subscriptions["feature-x"]
        assert protocol.protocol_stats["subscriptions_active"] == 2  # agent-1 + agent-2

        # Check that initial info was sent
        protocol.collaboration_engine.send_message.assert_called()
        call_args = protocol.collaboration_engine.send_message.call_args[1]
        assert call_args["recipient_id"] == "agent-2"

    @pytest.mark.asyncio
    @staticmethod
    async def test_unsubscribe_from_branch(protocol: BranchInfoProtocol) -> None:
        """Test unsubscribing from branch updates."""
        await protocol.register_branch("feature-x", "agent-1")
        await protocol.subscribe_to_branch("agent-2", "feature-x")

        # Unsubscribe
        await protocol.unsubscribe_from_branch("agent-2", "feature-x")

        assert "agent-2" not in protocol.branch_subscriptions["feature-x"]
        assert protocol.protocol_stats["subscriptions_active"] == 1  # Only agent-1

    @pytest.mark.asyncio
    @staticmethod
    async def test_request_branch_sync(protocol: BranchInfoProtocol) -> None:
        """Test requesting branch synchronization."""
        await protocol.register_branch("feature-x", "agent-1")
        await protocol.register_branch("feature-y", "agent-2")

        # Reset mock to clear previous calls
        protocol.collaboration_engine.send_message.reset_mock()

        # Request sync for specific branches
        await protocol.request_branch_sync("agent-3", ["feature-x"])

        # Should send update to requester
        assert protocol.collaboration_engine.send_message.call_count == 1
        call_args = protocol.collaboration_engine.send_message.call_args[1]
        assert call_args["recipient_id"] == "agent-3"
        assert "sync_requested" in call_args["content"]["event_data"]

    @pytest.mark.asyncio
    @staticmethod
    async def test_detect_branch_conflicts(protocol: BranchInfoProtocol) -> None:
        """Test detecting conflicts between branches."""
        # Register two branches with overlapping changes
        await protocol.register_branch("feature-x", "agent-1")
        await protocol.register_branch("feature-y", "agent-2")

        # Update branch info with conflicting changes
        await protocol.update_branch_info(
            "feature-x",
            BranchInfoType.FILE_CHANGES,
            {"files": ["main.py", "utils.py"]},
        )
        await protocol.update_branch_info(
            "feature-y",
            BranchInfoType.FILE_CHANGES,
            {"files": ["main.py", "config.py"]},
        )

        # Update API signatures
        await protocol.update_branch_info(
            "feature-x",
            BranchInfoType.API_CHANGES,
            {"signatures": {"process": {"args": ["data"], "return": "Result"}}},
        )
        await protocol.update_branch_info(
            "feature-y",
            BranchInfoType.API_CHANGES,
            {
                "signatures": {
                    "process": {"args": ["data", "options"], "return": "Result"},
                },
            },
        )

        # Detect conflicts
        conflicts = await protocol.detect_branch_conflicts("feature-x", "feature-y")
        assert len(conflicts) >= 2
        assert any("main.py" in c for c in conflicts)
        assert any("process" in c for c in conflicts)

    @pytest.mark.asyncio
    @staticmethod
    async def test_prepare_merge_report(protocol: BranchInfoProtocol) -> None:
        """Test preparing merge readiness report."""
        await protocol.register_branch("feature-x", "agent-1")

        # Update branch to be merge-ready
        await protocol.update_branch_info(
            "feature-x",
            BranchInfoType.TEST_STATUS,
            {"passed": True},
        )
        await protocol.update_branch_info(
            "feature-x",
            BranchInfoType.BUILD_STATUS,
            {"status": "success"},
        )
        await protocol.update_branch_info(
            "feature-x",
            BranchInfoType.WORK_PROGRESS,
            {"completed": ["Task 1", "Task 2"], "remaining": []},
        )

        # Get merge report
        report = await protocol.prepare_merge_report("feature-x")

        assert report["branch_name"] == "feature-x"
        assert report["agent_id"] == "agent-1"
        assert report["merge_ready"] is True
        assert report["merge_score"] == 1.0
        assert report["criteria"]["tests_passed"] is True
        assert report["criteria"]["build_successful"] is True
        assert report["criteria"]["no_conflicts"] is True
        assert report["criteria"]["work_completed"] is True
        assert len(report["recommendations"]) == 0

    @pytest.mark.asyncio
    @staticmethod
    async def test_prepare_merge_report_not_ready(protocol: BranchInfoProtocol) -> None:
        """Test merge report for branch not ready to merge."""
        await protocol.register_branch(
            "feature-x",
            "agent-1",
            work_items=["Task 1", "Task 2"],
        )

        # Update with failures
        await protocol.update_branch_info(
            "feature-x",
            BranchInfoType.TEST_STATUS,
            {"passed": False},
        )
        await protocol.update_branch_info(
            "feature-x",
            BranchInfoType.CONFLICT_INFO,
            {"conflicts": ["Merge conflict in main.py"]},
        )

        report = await protocol.prepare_merge_report("feature-x")

        assert report["merge_ready"] is False
        assert report["merge_score"] < 1.0
        assert report["criteria"]["tests_passed"] is False
        assert report["criteria"]["no_conflicts"] is False
        assert report["criteria"]["work_completed"] is False
        assert len(report["recommendations"]) > 0
        assert any("Fix failing tests" in r for r in report["recommendations"])
        assert any("Resolve 1 conflicts" in r for r in report["recommendations"])

    @staticmethod
    def test_determine_priority(protocol: BranchInfoProtocol) -> None:
        """Test priority determination for different info types."""
        assert (
            protocol._determine_priority(BranchInfoType.CONFLICT_INFO)
            == MessagePriority.HIGH
        )
        assert (
            protocol._determine_priority(BranchInfoType.API_CHANGES)
            == MessagePriority.HIGH
        )
        assert (
            protocol._determine_priority(BranchInfoType.BUILD_STATUS)
            == MessagePriority.NORMAL
        )
        assert (
            protocol._determine_priority(BranchInfoType.FILE_CHANGES)
            == MessagePriority.LOW
        )

    @staticmethod
    def test_calculate_relevance(protocol: BranchInfoProtocol) -> None:
        """Test relevance score calculation."""
        assert protocol._calculate_relevance(BranchInfoType.CONFLICT_INFO) == 1.0
        assert protocol._calculate_relevance(BranchInfoType.API_CHANGES) == 0.9
        assert protocol._calculate_relevance(BranchInfoType.BRANCH_STATE) == 0.3

    @staticmethod
    def test_get_protocol_summary(protocol: BranchInfoProtocol) -> None:
        """Test getting protocol summary."""
        summary = protocol.get_protocol_summary()

        assert "statistics" in summary
        assert "active_branches" in summary
        assert "total_subscriptions" in summary
        assert "sync_strategy" in summary
        assert summary["sync_strategy"] == "smart"
        assert summary["active_branches"] == 0
        assert summary["total_subscriptions"] == 0

    @pytest.mark.asyncio
    @staticmethod
    async def test_immediate_sync_types(protocol: BranchInfoProtocol) -> None:
        """Test that certain info types trigger immediate sync."""
        await protocol.register_branch("feature-x", "agent-1")

        # Reset to count only update-triggered shares
        protocol.collaboration_engine.share_knowledge.reset_mock()

        # These should trigger immediate sync
        immediate_types = [
            BranchInfoType.CONFLICT_INFO,
            BranchInfoType.API_CHANGES,
            BranchInfoType.BUILD_STATUS,
        ]

        for info_type in immediate_types:
            await protocol.update_branch_info(
                "feature-x",
                info_type,
                {"test": "data"},
            )

        # Should have triggered sync for each immediate type
        assert protocol.collaboration_engine.share_knowledge.call_count == len(
            immediate_types,
        )

    @pytest.mark.asyncio
    @staticmethod
    async def test_sync_history_tracking(protocol: BranchInfoProtocol) -> None:
        """Test that sync events are properly tracked."""
        await protocol.register_branch("feature-x", "agent-1")

        # Trigger some syncs
        await protocol.update_branch_info(
            "feature-x",
            BranchInfoType.FILE_CHANGES,
            {"files": ["test.py"]},
            requires_immediate_sync=True,
        )

        assert len(protocol.sync_history) >= 2  # Registration + update
        assert protocol.protocol_stats["syncs_performed"] >= 2

        # Check sync event structure
        sync_event = protocol.sync_history[-1]
        assert sync_event.branch_name == "feature-x"
        assert sync_event.agent_id == "agent-1"
        assert sync_event.event_type == BranchInfoType.FILE_CHANGES
        assert isinstance(sync_event.timestamp, datetime)

    @pytest.mark.asyncio
    @staticmethod
    async def test_protocol_with_multiple_subscribers(
        protocol: BranchInfoProtocol,
    ) -> None:
        """Test protocol behavior with multiple subscribers."""
        await protocol.register_branch("feature-x", "agent-1")
        await protocol.subscribe_to_branch("agent-2", "feature-x")
        await protocol.subscribe_to_branch("agent-3", "feature-x")

        # Reset to count only update messages
        protocol.collaboration_engine.send_message.reset_mock()

        # Update branch info
        await protocol.update_branch_info(
            "feature-x",
            BranchInfoType.API_CHANGES,
            {"signatures": {"new_func": {"args": ["x"], "return": "int"}}},
        )

        # Should send to all subscribers except the branch owner
        # agent-2 and agent-3 should receive updates
        assert protocol.collaboration_engine.send_message.call_count == 2
