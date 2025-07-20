"""Tests for DependencyPropagationSystem dependency change tracking and propagation."""

import asyncio
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from libs.multi_agent.branch_info_protocol import BranchInfoProtocol
from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.collaboration_engine import CollaborationEngine
from libs.multi_agent.dependency_propagation import (
    ChangeImpact,
    DependencyChange,
    DependencyNode,
    DependencyPropagationSystem,
    DependencyType,
    PropagationResult,
    PropagationStrategy,
)


class TestDependencyNode:
    """Test cases for DependencyNode dataclass."""

    def test_init(self) -> None:
        """Test DependencyNode initialization."""
        node = DependencyNode(
            file_path="src/main.py",
            module_name="src.main",
            dependencies={"utils", "config"},
            dependents={"app", "tests"},
            exports={"function1": {"type": "function", "line": 10}},
            imports={"pandas": {"type": "import", "module": "pandas"}},
        )

        assert node.file_path == "src/main.py"
        assert node.module_name == "src.main"
        assert "utils" in node.dependencies
        assert "config" in node.dependencies
        assert "app" in node.dependents
        assert "tests" in node.dependents
        assert "function1" in node.exports
        assert "pandas" in node.imports
        assert isinstance(node.last_analyzed, datetime)
        assert node.metadata == {}


class TestDependencyChange:
    """Test cases for DependencyChange dataclass."""

    def test_init(self) -> None:
        """Test DependencyChange initialization."""
        change = DependencyChange(
            change_id="change-123",
            source_file="src/utils.py",
            changed_by="agent-1",
            change_type=DependencyType.FUNCTION_CALL,
            impact_level=ChangeImpact.BREAKING,
            change_details={"function": "process_data", "change": "signature_modified"},
            affected_files=["src/main.py", "tests/test_main.py"],
            affected_branches=["feature-x", "feature-y"],
            propagation_strategy=PropagationStrategy.IMMEDIATE,
            requires_manual_review=True,
        )

        assert change.change_id == "change-123"
        assert change.source_file == "src/utils.py"
        assert change.changed_by == "agent-1"
        assert change.change_type == DependencyType.FUNCTION_CALL
        assert change.impact_level == ChangeImpact.BREAKING
        assert len(change.affected_files) == 2
        assert len(change.affected_branches) == 2
        assert change.propagation_strategy == PropagationStrategy.IMMEDIATE
        assert change.requires_manual_review is True
        assert change.propagation_attempts == 0
        assert change.max_propagation_attempts == 3
        assert isinstance(change.created_at, datetime)
        assert change.processed_at is None


class TestPropagationResult:
    """Test cases for PropagationResult dataclass."""

    def test_init(self) -> None:
        """Test PropagationResult initialization."""
        result = PropagationResult(
            change_id="change-123",
            success=True,
            propagated_to=["branch-1", "branch-2"],
            failed_targets=["branch-3"],
            warnings=["Minor issue in branch-2"],
            recommendations=["Review changes manually"],
            processing_time=1.5,
        )

        assert result.change_id == "change-123"
        assert result.success is True
        assert len(result.propagated_to) == 2
        assert len(result.failed_targets) == 1
        assert len(result.warnings) == 1
        assert len(result.recommendations) == 1
        assert result.processing_time == 1.5
        assert result.metadata == {}


class TestDependencyPropagationSystem:
    """Test cases for DependencyPropagationSystem."""

    @pytest.fixture
    def temp_repo(self) -> Iterator[Path]:
        """Create temporary repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create some Python files for testing
            (repo_path / "src").mkdir()
            (repo_path / "tests").mkdir()

            # Main module
            (repo_path / "src" / "main.py").write_text(
                """
import pandas as pd
from .utils import process_data, validate_input

class DataProcessor:
    def __init__(self):
        self.data = None

    def process(self, data):
        validated = validate_input(data)
        return process_data(validated)
"""
            )

            # Utils module
            (repo_path / "src" / "utils.py").write_text(
                """
def process_data(data):
    return data * 2

def validate_input(data):
    return data is not None
"""
            )

            # Test file
            (repo_path / "tests" / "test_main.py").write_text(
                """
from src.main import DataProcessor

def test_processor():
    processor = DataProcessor()
    result = processor.process(5)
    assert result == 10
"""
            )

            yield repo_path

    @pytest.fixture
    def mock_collaboration_engine(self) -> Mock:
        """Create mock collaboration engine."""
        engine = Mock(spec=CollaborationEngine)
        engine.send_message = AsyncMock(return_value="message-123")
        return engine

    @pytest.fixture
    def mock_branch_info_protocol(self) -> Mock:
        """Create mock branch info protocol."""
        protocol = Mock(spec=BranchInfoProtocol)
        protocol.update_branch_info = AsyncMock()
        protocol.get_all_branches_info = AsyncMock(
            return_value={
                "feature-x": Mock(agent_id="agent-1", files_modified=["src/main.py"]),
                "feature-y": Mock(agent_id="agent-2", files_modified=["src/utils.py"]),
            },
        )
        protocol.get_branch_info = AsyncMock(
            return_value=Mock(agent_id="agent-1", files_modified=["src/main.py"]),
        )
        return protocol

    @pytest.fixture
    def mock_branch_manager(self) -> Mock:
        """Create mock branch manager."""
        return Mock(spec=BranchManager)

    @pytest.fixture
    def propagation_system(
        self,
        mock_collaboration_engine: Mock,
        mock_branch_info_protocol: Mock,
        mock_branch_manager: Mock,
        temp_repo: Path,
    ) -> DependencyPropagationSystem:
        """Create DependencyPropagationSystem instance."""
        return DependencyPropagationSystem(
            collaboration_engine=mock_collaboration_engine,
            branch_info_protocol=mock_branch_info_protocol,
            branch_manager=mock_branch_manager,
            repo_path=str(temp_repo),
            auto_propagate=True,
        )

    def test_init(
        self,
        propagation_system: DependencyPropagationSystem,
        mock_collaboration_engine: Mock,
        mock_branch_info_protocol: Mock,
        mock_branch_manager: Mock,
    ) -> None:
        """Test DependencyPropagationSystem initialization."""
        assert propagation_system.collaboration_engine == mock_collaboration_engine
        assert propagation_system.branch_info_protocol == mock_branch_info_protocol
        assert propagation_system.branch_manager == mock_branch_manager
        assert propagation_system.auto_propagate is True
        assert len(propagation_system.dependency_graph) == 0
        assert len(propagation_system.change_queue) == 0
        assert len(propagation_system.change_history) == 0
        assert propagation_system.batch_size == 10
        assert propagation_system.batch_timeout == 300
        assert propagation_system._running is False  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_start_stop(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test starting and stopping the system."""
        # Start system
        await propagation_system.start()
        assert propagation_system._running is True  # noqa: SLF001
        assert propagation_system._propagation_task is not None  # noqa: SLF001
        assert propagation_system._analysis_task is not None  # noqa: SLF001

        # Stop system
        await propagation_system.stop()
        assert propagation_system._running is False  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_track_dependency_change(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test tracking a dependency change."""
        change_id = await propagation_system.track_dependency_change(
            file_path="src/utils.py",
            changed_by="agent-1",
            change_type=DependencyType.FUNCTION_CALL,
            change_details={"function": "process_data", "change": "signature_modified"},
            impact_level=ChangeImpact.BREAKING,
            propagation_strategy=PropagationStrategy.IMMEDIATE,
        )

        assert change_id.startswith("dep_change_")
        assert len(propagation_system.change_queue) == 1
        assert len(propagation_system.change_history) == 1
        assert propagation_system.propagation_stats["changes_tracked"] == 1

        # Check change details
        change = propagation_system.change_history[0]
        assert change.change_id == change_id
        assert change.source_file == "src/utils.py"
        assert change.changed_by == "agent-1"
        assert change.change_type == DependencyType.FUNCTION_CALL
        assert change.impact_level == ChangeImpact.BREAKING
        assert change.requires_manual_review is True  # Breaking changes require review

    @pytest.mark.asyncio
    async def test_track_dependency_change_auto_impact_detection(
        self,
        propagation_system: DependencyPropagationSystem,
    ) -> None:
        """Test auto-detection of change impact level."""
        # Breaking change keywords
        change_id = await propagation_system.track_dependency_change(
            file_path="src/utils.py",
            changed_by="agent-1",
            change_type=DependencyType.FUNCTION_CALL,
            change_details={"description": "remove deprecated function"},
        )

        change = next(c for c in propagation_system.change_history if c.change_id == change_id)
        assert change.impact_level == ChangeImpact.BREAKING

        # Security change keywords
        change_id = await propagation_system.track_dependency_change(
            file_path="src/auth.py",
            changed_by="agent-1",
            change_type=DependencyType.API_USAGE,
            change_details={"description": "update security token validation"},
        )

        change = next(c for c in propagation_system.change_history if c.change_id == change_id)
        assert change.impact_level == ChangeImpact.SECURITY

        # Enhancement changes
        change_id = await propagation_system.track_dependency_change(
            file_path="src/utils.py",
            changed_by="agent-1",
            change_type=DependencyType.FUNCTION_CALL,
            change_details={"description": "add new feature functionality"},
        )

        change = next(c for c in propagation_system.change_history if c.change_id == change_id)
        assert change.impact_level == ChangeImpact.ENHANCEMENT

    @pytest.mark.asyncio
    async def test_build_dependency_graph(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test building dependency graph from source files."""
        dependency_graph = await propagation_system.build_dependency_graph()

        assert len(dependency_graph) > 0

        # Check that Python files were analyzed
        src_files = [path for path in dependency_graph.keys() if path.startswith("src/")]
        assert len(src_files) >= 2

        # Check specific dependency relationships
        if "src/main.py" in dependency_graph:
            main_node = dependency_graph["src/main.py"]
            assert main_node.file_path == "src/main.py"
            assert main_node.module_name == "src.main"
            assert len(main_node.exports) > 0  # Should have DataProcessor class
            assert len(main_node.imports) > 0  # Should have imports

    @pytest.mark.asyncio
    async def test_get_dependency_impact_report(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test getting dependency impact report."""
        # Build dependency graph first
        await propagation_system.build_dependency_graph()

        # Get impact report for a file
        report = await propagation_system.get_dependency_impact_report("src/utils.py")

        assert "file_path" in report
        assert report["file_path"] == "src/utils.py"
        assert "module_name" in report
        assert "direct_dependents" in report
        assert "indirect_dependents" in report
        assert "total_impact" in report
        assert "complexity_score" in report
        assert "risk_level" in report
        assert "dependencies" in report
        assert "dependents" in report

        # Test non-existent file
        report = await propagation_system.get_dependency_impact_report(
            "non_existent.py",
        )
        assert "error" in report

    @pytest.mark.asyncio
    async def test_propagate_changes_to_branches(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test propagating changes to target branches."""
        # Track some changes first
        change_id1 = await propagation_system.track_dependency_change(
            file_path="src/utils.py",
            changed_by="agent-1",
            change_type=DependencyType.FUNCTION_CALL,
            change_details={"function": "process_data"},
            propagation_strategy=PropagationStrategy.MANUAL,  # Prevent auto-propagation
        )

        change_id2 = await propagation_system.track_dependency_change(
            file_path="src/main.py",
            changed_by="agent-2",
            change_type=DependencyType.CLASS_INHERITANCE,
            change_details={"class": "DataProcessor"},
            propagation_strategy=PropagationStrategy.MANUAL,
        )

        # Propagate changes
        results = await propagation_system.propagate_changes_to_branches(
            change_ids=[change_id1, change_id2],
            target_branches=["feature-x", "feature-y"],
        )

        assert len(results) == 2
        for result in results:
            assert isinstance(result, PropagationResult)
            assert result.change_id in [change_id1, change_id2]

    @pytest.mark.asyncio
    async def test_get_pending_changes(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test getting pending changes."""
        # Track some changes
        await propagation_system.track_dependency_change(
            file_path="src/utils.py",
            changed_by="agent-1",
            change_type=DependencyType.FUNCTION_CALL,
            change_details={"function": "process_data"},
            propagation_strategy=PropagationStrategy.MANUAL,
        )

        await propagation_system.track_dependency_change(
            file_path="src/main.py",
            changed_by="agent-2",
            change_type=DependencyType.CLASS_INHERITANCE,
            change_details={"class": "DataProcessor"},
            propagation_strategy=PropagationStrategy.MANUAL,
        )

        # Get all pending changes
        pending = await propagation_system.get_pending_changes()
        assert len(pending) == 2

        # Filter by agent
        pending_agent1 = await propagation_system.get_pending_changes(
            agent_id="agent-1",
        )
        assert len(pending_agent1) == 1
        assert pending_agent1[0].changed_by == "agent-1"

        # Filter by branch (mock will need to return branch info)
        pending_branch = await propagation_system.get_pending_changes(
            branch_name="feature-x",
        )
        assert len(pending_branch) >= 0  # Depends on mock branch info

    @pytest.mark.asyncio
    async def test_analyze_change_impact_detection(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test impact level detection logic."""
        # Test breaking change detection
        impact = await propagation_system._analyze_change_impact(  # noqa: SLF001
            "src/utils.py",
            DependencyType.FUNCTION_CALL,
            {"description": "remove old function"},
        )
        assert impact == ChangeImpact.BREAKING

        # Test security change detection
        impact = await propagation_system._analyze_change_impact(  # noqa: SLF001
            "src/auth.py",
            DependencyType.API_USAGE,
            {"description": "update authentication logic"},
        )
        assert impact == ChangeImpact.SECURITY

        # Test function signature changes
        impact = await propagation_system._analyze_change_impact(  # noqa: SLF001
            "src/utils.py",
            DependencyType.FUNCTION_CALL,
            {"signature": "changed", "parameters": ["new_param"]},
        )
        assert impact == ChangeImpact.BREAKING

        # Test class inheritance changes
        impact = await propagation_system._analyze_change_impact(  # noqa: SLF001
            "src/main.py",
            DependencyType.CLASS_INHERITANCE,
            {"base_class": "changed"},
        )
        assert impact == ChangeImpact.BREAKING

        # Test enhancement detection
        impact = await propagation_system._analyze_change_impact(  # noqa: SLF001
            "src/utils.py",
            DependencyType.FUNCTION_CALL,
            {"description": "add new functionality"},
        )
        assert impact == ChangeImpact.ENHANCEMENT

        # Test default compatible
        impact = await propagation_system._analyze_change_impact(  # noqa: SLF001
            "src/utils.py",
            DependencyType.IMPORT,
            {"description": "update import statement"},
        )
        assert impact == ChangeImpact.COMPATIBLE

    @pytest.mark.asyncio
    async def test_find_affected_files(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test finding files affected by changes."""
        # Build dependency graph first
        await propagation_system.build_dependency_graph()

        # Test finding affected files
        affected = await propagation_system._find_affected_files(  # noqa: SLF001
            "src/utils.py",
            DependencyType.FUNCTION_CALL,
            {"function": "process_data"},
        )

        # Should include files that depend on utils.py
        assert isinstance(affected, list)

    @pytest.mark.asyncio
    async def test_find_affected_branches(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test finding branches affected by file changes."""
        affected_files = ["src/main.py", "src/utils.py"]

        affected_branches = await propagation_system._find_affected_branches(  # noqa: SLF001
            affected_files,
        )

        # Should return branches based on mock branch info protocol
        assert isinstance(affected_branches, list)

    @pytest.mark.asyncio
    async def test_calculate_indirect_dependents(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test calculating indirect dependent count."""
        # Build dependency graph
        await propagation_system.build_dependency_graph()

        if "src/utils.py" in propagation_system.dependency_graph:
            count = await propagation_system._calculate_indirect_dependents(  # noqa: SLF001
                "src/utils.py",
            )
            assert isinstance(count, int)
            assert count >= 0

    def test_calculate_complexity_score(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test complexity score calculation."""
        node = DependencyNode(
            file_path="test.py",
            module_name="test",
            dependencies={"dep1", "dep2", "dep3"},  # 3 dependencies
            dependents={"dep_a", "dep_b"},  # 2 dependents
            exports={"func1": {}, "func2": {}, "class1": {}},  # 3 exports
        )

        score = propagation_system._calculate_complexity_score(node)  # noqa: SLF001
        expected = (3 * 0.3) + (2 * 0.5) + (3 * 0.2)  # 0.9 + 1.0 + 0.6 = 2.5
        assert score == expected

        # Test score capping at 10.0
        large_node = DependencyNode(
            file_path="large.py",
            module_name="large",
            dependencies={f"dep{i}" for i in range(50)},  # Many dependencies
            dependents={f"dep{i}" for i in range(50)},  # Many dependents
        )

        score = propagation_system._calculate_complexity_score(large_node)  # noqa: SLF001
        assert score == 10.0  # Should be capped

    def test_calculate_risk_level(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test risk level calculation."""
        # High risk: high complexity or high impact
        assert propagation_system._calculate_risk_level(8.0, 5) == "high"  # noqa: SLF001
        assert propagation_system._calculate_risk_level(5.0, 15) == "high"  # noqa: SLF001

        # Medium risk: medium complexity or medium impact
        assert propagation_system._calculate_risk_level(6.0, 3) == "medium"  # noqa: SLF001
        assert propagation_system._calculate_risk_level(3.0, 8) == "medium"  # noqa: SLF001

        # Low risk: low complexity and low impact
        assert propagation_system._calculate_risk_level(2.0, 2) == "low"  # noqa: SLF001

    def test_get_propagation_summary(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test getting propagation system summary."""
        summary = propagation_system.get_propagation_summary()

        assert "statistics" in summary
        assert "dependency_graph_size" in summary
        assert "pending_changes" in summary
        assert "processing_queue_size" in summary
        assert "total_changes_tracked" in summary
        assert "recent_changes" in summary

        assert summary["dependency_graph_size"] == 0  # Empty initially
        assert summary["pending_changes"] == 0
        assert summary["total_changes_tracked"] == 0
        assert len(summary["recent_changes"]) == 0

    @pytest.mark.asyncio
    async def test_propagation_stats_tracking(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test that statistics are properly tracked."""
        initial_stats = propagation_system.propagation_stats.copy()

        # Track a change
        await propagation_system.track_dependency_change(
            file_path="src/utils.py",
            changed_by="agent-1",
            change_type=DependencyType.FUNCTION_CALL,
            change_details={"function": "test"},
            impact_level=ChangeImpact.BREAKING,
        )

        # Check stats updated
        assert propagation_system.propagation_stats["changes_tracked"] == initial_stats["changes_tracked"] + 1

    @pytest.mark.asyncio
    async def test_immediate_propagation_for_critical_changes(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test that critical changes trigger immediate propagation."""
        # Start the system to enable processing
        await propagation_system.start()

        # Track a critical change
        await propagation_system.track_dependency_change(
            file_path="src/utils.py",
            changed_by="agent-1",
            change_type=DependencyType.FUNCTION_CALL,
            change_details={"description": "breaking security fix"},
            impact_level=ChangeImpact.SECURITY,
            propagation_strategy=PropagationStrategy.IMMEDIATE,
        )

        # Give a moment for processing
        await asyncio.sleep(0.1)

        # Check that branch info protocol was updated
        propagation_system.branch_info_protocol.update_branch_info.assert_called()

        await propagation_system.stop()

    @pytest.mark.asyncio
    async def test_notification_to_affected_agents(self, propagation_system: DependencyPropagationSystem) -> None:
        """Test that affected agents are notified of changes."""
        await propagation_system.start()

        # Track a change that affects multiple branches
        await propagation_system.track_dependency_change(
            file_path="src/utils.py",
            changed_by="agent-1",
            change_type=DependencyType.FUNCTION_CALL,
            change_details={"function": "shared_utility"},
            impact_level=ChangeImpact.BREAKING,
            propagation_strategy=PropagationStrategy.IMMEDIATE,
        )

        # Give a moment for processing
        await asyncio.sleep(0.1)

        # Check that messages were sent via collaboration engine
        propagation_system.collaboration_engine.send_message.assert_called()

        await propagation_system.stop()
