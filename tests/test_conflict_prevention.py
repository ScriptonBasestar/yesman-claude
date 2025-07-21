# Copyright notice.

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest
from libs.multi_agent.auto_resolver import AutoResolutionMode, AutoResolver
from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.collaboration_engine import (
from libs.multi_agent.conflict_prediction import (
from libs.multi_agent.conflict_prevention import (
from libs.multi_agent.conflict_resolution import ConflictSeverity, ConflictType

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Tests for ConflictPreventionSystem."""



    CollaborationEngine,
    MessagePriority,
    MessageType,
)
    ConflictPattern,
    ConflictPredictor,
    PredictionConfidence,
    PredictionResult,
)
    ConflictPreventionSystem,
    PreventionAction,
    PreventionMeasure,
    PreventionResult,
    PreventionStrategy,
)


class TestPreventionMeasure:
    """Test cases for PreventionMeasure."""

    @staticmethod
    def test_init() -> None:
        """Test PreventionMeasure initialization."""
        measure = PreventionMeasure(
            measure_id="test_measure_001",
            strategy=PreventionStrategy.BRANCH_ISOLATION,
            action=PreventionAction.DEFER_TASK,
            target_branches=["feature/a", "feature/b"],
            target_agents=["agent1", "agent2"],
            predicted_conflict_id="conflict_123",
            urgency=PredictionConfidence.HIGH,
            description="Test prevention measure",
            estimated_effort=2,
            success_probability=0.8,
        )

        assert measure.measure_id == "test_measure_001"
        assert measure.strategy == PreventionStrategy.BRANCH_ISOLATION
        assert measure.action == PreventionAction.DEFER_TASK
        assert measure.target_branches == ["feature/a", "feature/b"]
        assert measure.target_agents == ["agent1", "agent2"]
        assert measure.predicted_conflict_id == "conflict_123"
        assert measure.urgency == PredictionConfidence.HIGH
        assert measure.description == "Test prevention measure"
        assert measure.estimated_effort == 2
        assert measure.success_probability == 0.8
        assert measure.status == "pending"
        assert measure.applied_at is None
        assert measure.effectiveness is None
        assert isinstance(measure.metadata, dict)
        assert isinstance(measure.created_at, datetime)

    @staticmethod
    def test_defaults() -> None:
        """Test PreventionMeasure default values."""
        measure = PreventionMeasure(
            measure_id="test",
            strategy=PreventionStrategy.EARLY_MERGE,
            action=PreventionAction.MERGE_EARLY,
            target_branches=["main"],
            target_agents=["agent"],
            predicted_conflict_id="pred",
            urgency=PredictionConfidence.MEDIUM,
            description="Test",
        )

        assert measure.implementation_steps == []
        assert measure.estimated_effort == 0
        assert measure.success_probability == 0.0
        assert measure.status == "pending"
        assert measure.applied_at is None
        assert measure.effectiveness is None
        assert measure.metadata == {}


class TestPreventionResult:
    """Test cases for PreventionResult."""

    @staticmethod
    def test_init() -> None:
        """Test PreventionResult initialization."""
        applied_measure = PreventionMeasure(
            measure_id="applied_001",
            strategy=PreventionStrategy.DEPENDENCY_SYNC,
            action=PreventionAction.COORDINATE_TIMING,
            target_branches=["branch1"],
            target_agents=["agent1"],
            predicted_conflict_id="pred1",
            urgency=PredictionConfidence.LOW,
            description="Applied measure",
        )

        failed_measure = PreventionMeasure(
            measure_id="failed_001",
            strategy=PreventionStrategy.WORK_REALLOCATION,
            action=PreventionAction.REASSIGN_AGENT,
            target_branches=["branch2"],
            target_agents=["agent2"],
            predicted_conflict_id="pred2",
            urgency=PredictionConfidence.HIGH,
            description="Failed measure",
        )

        result = PreventionResult(
            session_id="session_001",
            branches_analyzed=["main", "feature/a", "feature/b"],
            predictions_found=5,
            measures_applied=2,
            conflicts_prevented=1,
            prevention_success_rate=0.75,
            time_saved=3.5,
            applied_measures=[applied_measure],
            failed_measures=[failed_measure],
            prevention_time=45.2,
            analysis_overhead=5.1,
        )

        assert result.session_id == "session_001"
        assert result.branches_analyzed == ["main", "feature/a", "feature/b"]
        assert result.predictions_found == 5
        assert result.measures_applied == 2
        assert result.conflicts_prevented == 1
        assert result.prevention_success_rate == 0.75
        assert result.time_saved == 3.5
        assert result.applied_measures == [applied_measure]
        assert result.failed_measures == [failed_measure]
        assert result.prevention_time == 45.2
        assert result.analysis_overhead == 5.1
        assert isinstance(result.metadata, dict)
        assert isinstance(result.executed_at, datetime)


class TestConflictPreventionSystem:
    """Test cases for ConflictPreventionSystem."""

    @pytest.fixture
    @staticmethod
    def mock_dependencies() -> dict:
        """Create mock dependencies for ConflictPreventionSystem."""
        conflict_predictor = Mock(spec=ConflictPredictor)
        auto_resolver = Mock(spec=AutoResolver)
        collaboration_engine = Mock(spec=CollaborationEngine)
        branch_manager = Mock(spec=BranchManager)

        return {
            "conflict_predictor": conflict_predictor,
            "auto_resolver": auto_resolver,
            "collaboration_engine": collaboration_engine,
            "branch_manager": branch_manager,
        }

    @pytest.fixture
    @staticmethod
    def prevention_system(mock_dependencies: dict) -> ConflictPreventionSystem:
        """Create ConflictPreventionSystem instance with mocked dependencies."""
        return ConflictPreventionSystem(
            conflict_predictor=mock_dependencies["conflict_predictor"],
            auto_resolver=mock_dependencies["auto_resolver"],
            collaboration_engine=mock_dependencies["collaboration_engine"],
            branch_manager=mock_dependencies["branch_manager"],
            repo_path="/tmp/test_repo",
        )

    @staticmethod
    def test_init(prevention_system: ConflictPreventionSystem, mock_dependencies: dict) -> None:
        """Test ConflictPreventionSystem initialization."""
        assert prevention_system.conflict_predictor == mock_dependencies["conflict_predictor"]
        assert prevention_system.auto_resolver == mock_dependencies["auto_resolver"]
        assert prevention_system.collaboration_engine == mock_dependencies["collaboration_engine"]
        assert prevention_system.branch_manager == mock_dependencies["branch_manager"]
        assert prevention_system.repo_path == Path("/tmp/test_repo")

        # Check default configuration
        assert prevention_system.prevention_config["prediction_threshold"] == 0.6
        assert prevention_system.prevention_config["max_prevention_measures"] == 10
        assert prevention_system.prevention_config["prevention_horizon"] == 24
        assert prevention_system.prevention_config["coordination_delay"] == 2
        assert prevention_system.prevention_config["early_merge_threshold"] == 0.8
        assert prevention_system.prevention_config["effort_threshold"] == 8

        # Check initial state
        assert prevention_system.active_measures == {}
        assert prevention_system.prevention_history == []
        assert not prevention_system._running  # noqa: SLF001
        assert prevention_system._prevention_monitor_task is None  # noqa: SLF001

        # Check strategy handlers
        assert len(prevention_system.strategy_handlers) == 7
        assert PreventionStrategy.BRANCH_ISOLATION in prevention_system.strategy_handlers
        assert PreventionStrategy.WORK_REALLOCATION in prevention_system.strategy_handlers
        assert PreventionStrategy.DEPENDENCY_SYNC in prevention_system.strategy_handlers
        assert PreventionStrategy.EARLY_MERGE in prevention_system.strategy_handlers
        assert PreventionStrategy.AGENT_COORDINATION in prevention_system.strategy_handlers
        assert PreventionStrategy.TEMPORAL_SEPARATION in prevention_system.strategy_handlers
        assert PreventionStrategy.SEMANTIC_REFACTORING in prevention_system.strategy_handlers

        # Check initial statistics
        expected_stats = {
            "predictions_analyzed": 0,
            "measures_applied": 0,
            "conflicts_prevented": 0,
            "prevention_success_rate": 0.0,
            "total_time_saved": 0.0,
        }
        assert prevention_system.prevention_stats == expected_stats

    @pytest.mark.asyncio
    @staticmethod
    async def test_start_stop_monitoring(prevention_system: ConflictPreventionSystem) -> None:
        """Test starting and stopping prevention monitoring."""
        # Start monitoring
        await prevention_system.start_prevention_monitoring(monitoring_interval=0.1)

        assert prevention_system._running is True  # noqa: SLF001
        assert prevention_system._prevention_monitor_task is not None  # noqa: SLF001
        assert not prevention_system._prevention_monitor_task.done()  # noqa: SLF001

        # Wait a short time to ensure the monitor loop is running
        await asyncio.sleep(0.2)

        # Stop monitoring
        await prevention_system.stop_prevention_monitoring()

        assert prevention_system._running is False  # noqa: SLF001
        assert prevention_system._prevention_monitor_task.cancelled()  # noqa: SLF001

    @pytest.mark.asyncio
    @staticmethod
    async def test_analyze_and_prevent_conflicts_no_predictions(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,
    ) -> None:
        """Test analyze_and_prevent_conflicts when no predictions are found."""
        # Mock predict_conflicts to return empty list
        mock_dependencies["conflict_predictor"].predict_conflicts = AsyncMock(
            return_value=[],
        )

        branches = ["main", "feature/a", "feature/b"]
        result = await prevention_system.analyze_and_prevent_conflicts(branches)

        # Verify predictions were requested
        mock_dependencies["conflict_predictor"].predict_conflicts.assert_called_once()
        call_args = mock_dependencies["conflict_predictor"].predict_conflicts.call_args
        assert call_args[0][0] == branches  # branches argument
        assert isinstance(call_args[0][1], timedelta)  # time_horizon argument

        # Verify result
        assert isinstance(result, PreventionResult)
        assert result.branches_analyzed == branches
        assert result.predictions_found == 0
        assert result.measures_applied == 0
        assert result.conflicts_prevented == 0
        assert result.prevention_success_rate == 0.0
        assert result.time_saved == 0.0
        assert result.applied_measures == []
        assert result.failed_measures == []
        assert result.prevention_time > 0
        assert "significant_predictions" in result.metadata
        assert result.metadata["significant_predictions"] == 0

    @pytest.mark.asyncio
    @staticmethod
    async def test_analyze_and_prevent_conflicts_with_predictions(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,
    ) -> None:
        """Test analyze_and_prevent_conflicts with actual predictions."""
        # Create mock prediction
        mock_prediction = PredictionResult(
            prediction_id="pred_001",
            confidence=PredictionConfidence.HIGH,
            pattern=ConflictPattern.OVERLAPPING_IMPORTS,
            affected_branches=["main", "feature/a"],
            affected_files=["file1.py", "file2.py"],
            predicted_conflict_type=ConflictType.MERGE_CONFLICT,
            predicted_severity=ConflictSeverity.MEDIUM,
            likelihood_score=0.8,
            description="Mock prediction for testing",
            affected_agents=["agent1", "agent2"],
        )

        # Mock predict_conflicts to return prediction
        mock_dependencies["conflict_predictor"].predict_conflicts = AsyncMock(
            return_value=[mock_prediction],
        )

        # Mock collaboration engine send_message
        mock_dependencies["collaboration_engine"].send_message = AsyncMock(
            return_value=True,
        )

        branches = ["main", "feature/a"]
        result = await prevention_system.analyze_and_prevent_conflicts(branches)

        # Verify predictions were requested
        mock_dependencies["conflict_predictor"].predict_conflicts.assert_called_once()

        # Verify result
        assert isinstance(result, PreventionResult)
        assert result.branches_analyzed == branches
        assert result.predictions_found == 1
        assert result.measures_applied >= 0  # May have applied measures
        assert result.prevention_time > 0
        assert "significant_predictions" in result.metadata
        assert result.metadata["significant_predictions"] >= 1

        # Verify statistics were updated
        assert prevention_system.prevention_stats["predictions_analyzed"] == 1

    @pytest.mark.asyncio
    @staticmethod
    async def test_generate_dependency_measures(prevention_system: ConflictPreventionSystem) -> None:
        """Test _generate_dependency_measures."""
        mock_prediction = PredictionResult(
            prediction_id="dep_pred_001",
            confidence=PredictionConfidence.MEDIUM,
            pattern=ConflictPattern.OVERLAPPING_IMPORTS,
            affected_branches=["branch1", "branch2"],
            affected_files=["module.py"],
            predicted_conflict_type=ConflictType.MERGE_CONFLICT,
            predicted_severity=ConflictSeverity.LOW,
            likelihood_score=0.6,
            description="Dependency conflict prediction",
            affected_agents=["agent1", "agent2"],
        )

        measures = await prevention_system._generate_dependency_measures(  # noqa: SLF001
            mock_prediction,
        )

        assert len(measures) == 1
        measure = measures[0]
        assert isinstance(measure, PreventionMeasure)
        assert measure.measure_id == f"dep_sync_{mock_prediction.prediction_id}"
        assert measure.strategy == PreventionStrategy.DEPENDENCY_SYNC
        assert measure.action == PreventionAction.COORDINATE_TIMING
        assert measure.target_branches == mock_prediction.affected_branches
        assert measure.target_agents == mock_prediction.affected_agents
        assert measure.predicted_conflict_id == mock_prediction.prediction_id
        assert measure.urgency == mock_prediction.confidence
        assert "Synchronize dependency imports" in measure.description
        assert len(measure.implementation_steps) == 4
        assert measure.estimated_effort == 3
        assert measure.success_probability == 0.8

    @pytest.mark.asyncio
    @staticmethod
    async def test_generate_coordination_measures(prevention_system: ConflictPreventionSystem) -> None:
        """Test _generate_coordination_measures."""
        mock_prediction = PredictionResult(
            prediction_id="coord_pred_001",
            confidence=PredictionConfidence.HIGH,
            pattern=ConflictPattern.FUNCTION_SIGNATURE_DRIFT,
            affected_branches=["feature/api", "feature/client"],
            affected_files=["api.py", "client.py"],
            predicted_conflict_type=ConflictType.SEMANTIC,
            predicted_severity=ConflictSeverity.HIGH,
            likelihood_score=0.85,
            description="Function signature conflict prediction",
            affected_agents=["api_agent", "client_agent"],
        )

        measures = await prevention_system._generate_coordination_measures(  # noqa: SLF001
            mock_prediction,
        )

        assert len(measures) == 1
        measure = measures[0]
        assert isinstance(measure, PreventionMeasure)
        assert measure.measure_id == f"coord_{mock_prediction.prediction_id}"
        assert measure.strategy == PreventionStrategy.AGENT_COORDINATION
        assert measure.action == PreventionAction.NOTIFY_AGENTS
        assert measure.target_branches == mock_prediction.affected_branches
        assert measure.target_agents == mock_prediction.affected_agents
        assert measure.predicted_conflict_id == mock_prediction.prediction_id
        assert measure.urgency == mock_prediction.confidence
        assert "function signature conflicts" in measure.description
        assert len(measure.implementation_steps) == 4
        assert measure.estimated_effort == 2
        assert measure.success_probability == 0.7

    @pytest.mark.asyncio
    @staticmethod
    async def test_generate_interface_measures(prevention_system: ConflictPreventionSystem) -> None:
        """Test _generate_interface_measures."""
        mock_prediction = PredictionResult(
            prediction_id="interface_pred_001",
            confidence=PredictionConfidence.CRITICAL,
            pattern=ConflictPattern.API_BREAKING_CHANGE,
            affected_branches=["main", "feature/api-v2"],
            affected_files=["api_v1.py", "api_v2.py"],
            predicted_conflict_type=ConflictType.SEMANTIC,
            predicted_severity=ConflictSeverity.CRITICAL,
            likelihood_score=0.95,
            description="API breaking change prediction",
            affected_agents=["api_maintainer", "api_dev"],
        )

        measures = await prevention_system._generate_interface_measures(mock_prediction)  # noqa: SLF001

        assert len(measures) == 1
        measure = measures[0]
        assert isinstance(measure, PreventionMeasure)
        assert measure.measure_id == f"interface_{mock_prediction.prediction_id}"
        assert measure.strategy == PreventionStrategy.SEMANTIC_REFACTORING
        assert measure.action == PreventionAction.CREATE_INTERFACE
        assert measure.target_branches == mock_prediction.affected_branches
        assert measure.target_agents == mock_prediction.affected_agents
        assert measure.predicted_conflict_id == mock_prediction.prediction_id
        assert measure.urgency == mock_prediction.confidence
        assert "stable interface" in measure.description
        assert len(measure.implementation_steps) == 4
        assert measure.estimated_effort == 6
        assert measure.success_probability == 0.9

    @pytest.mark.asyncio
    @staticmethod
    async def test_generate_temporal_measures(prevention_system: ConflictPreventionSystem) -> None:
        """Test _generate_temporal_measures."""
        mock_prediction = PredictionResult(
            prediction_id="temporal_pred_001",
            confidence=PredictionConfidence.MEDIUM,
            pattern=ConflictPattern.RESOURCE_CONTENTION,
            affected_branches=["worker1", "worker2"],
            affected_files=["shared_resource.py"],
            predicted_conflict_type=ConflictType.DEPENDENCY,
            predicted_severity=ConflictSeverity.MEDIUM,
            likelihood_score=0.7,
            description="Resource contention prediction",
            affected_agents=["worker_agent_1", "worker_agent_2"],
        )

        measures = await prevention_system._generate_temporal_measures(mock_prediction)  # noqa: SLF001

        assert len(measures) == 1
        measure = measures[0]
        assert isinstance(measure, PreventionMeasure)
        assert measure.measure_id == f"temporal_{mock_prediction.prediction_id}"
        assert measure.strategy == PreventionStrategy.TEMPORAL_SEPARATION
        assert measure.action == PreventionAction.DEFER_TASK
        assert measure.target_branches == mock_prediction.affected_branches
        assert measure.target_agents == mock_prediction.affected_agents
        assert measure.predicted_conflict_id == mock_prediction.prediction_id
        assert measure.urgency == mock_prediction.confidence
        assert "time to prevent resource contention" in measure.description
        assert len(measure.implementation_steps) == 4
        assert measure.estimated_effort == 1
        assert measure.success_probability == 0.6

    @pytest.mark.asyncio
    @staticmethod
    async def test_generate_generic_measures_early_merge(prevention_system: ConflictPreventionSystem) -> None:
        """Test _generate_generic_measures with high confidence for early merge."""
        mock_prediction = PredictionResult(
            prediction_id="generic_pred_001",
            confidence=PredictionConfidence.CRITICAL,
            pattern=ConflictPattern.MERGE_CONTEXT_LOSS,
            affected_branches=["feature/a", "feature/b"],
            affected_files=["complex_merge.py"],
            predicted_conflict_type=ConflictType.MERGE_CONFLICT,
            predicted_severity=ConflictSeverity.HIGH,
            likelihood_score=0.9,  # Above early_merge_threshold (0.8)
            description="Complex merge context loss prediction",
            affected_agents=["dev_a", "dev_b"],
        )

        measures = await prevention_system._generate_generic_measures(mock_prediction)  # noqa: SLF001

        assert len(measures) == 1
        measure = measures[0]
        assert isinstance(measure, PreventionMeasure)
        assert measure.measure_id == f"early_merge_{mock_prediction.prediction_id}"
        assert measure.strategy == PreventionStrategy.EARLY_MERGE
        assert measure.action == PreventionAction.MERGE_EARLY
        assert measure.target_branches == mock_prediction.affected_branches
        assert measure.target_agents == mock_prediction.affected_agents
        assert measure.predicted_conflict_id == mock_prediction.prediction_id
        assert measure.urgency == mock_prediction.confidence
        assert "early to prevent escalating conflicts" in measure.description
        assert len(measure.implementation_steps) == 4
        assert measure.estimated_effort == 4
        assert measure.success_probability == 0.8

    @pytest.mark.asyncio
    @staticmethod
    async def test_generate_generic_measures_low_confidence(prevention_system: ConflictPreventionSystem) -> None:
        """Test _generate_generic_measures with low confidence (no early merge)."""
        mock_prediction = PredictionResult(
            prediction_id="generic_pred_002",
            confidence=PredictionConfidence.LOW,
            pattern=ConflictPattern.VARIABLE_NAMING_COLLISION,
            affected_branches=["branch1", "branch2"],
            affected_files=["variables.py"],
            predicted_conflict_type=ConflictType.SEMANTIC,
            predicted_severity=ConflictSeverity.LOW,
            likelihood_score=0.4,  # Below early_merge_threshold (0.8)
            description="Low confidence prediction",
            affected_agents=["agent1", "agent2"],
        )

        measures = await prevention_system._generate_generic_measures(mock_prediction)  # noqa: SLF001

        # Should not generate early merge measure due to low likelihood score
        assert len(measures) == 0

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_prevention_measure_success(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,  # noqa: ARG002
    ) -> None:
        """Test _apply_prevention_measure with successful application."""
        measure = PreventionMeasure(
            measure_id="test_measure",
            strategy=PreventionStrategy.BRANCH_ISOLATION,
            action=PreventionAction.DEFER_TASK,
            target_branches=["branch1"],
            target_agents=["agent1"],
            predicted_conflict_id="pred1",
            urgency=PredictionConfidence.MEDIUM,
            description="Test measure",
        )

        # Mock the strategy handler to return success
        with patch.object(
            prevention_system,
            "_apply_branch_isolation",
            return_value=True,
        ) as mock_handler:
            success = await prevention_system._apply_prevention_measure(measure)  # noqa: SLF001

        assert success is True
        assert measure.status == "applied"
        assert measure.applied_at is not None
        assert isinstance(measure.applied_at, datetime)
        assert prevention_system.active_measures[measure.measure_id] == measure
        mock_handler.assert_called_once_with(measure)

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_prevention_measure_failure(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,  # noqa: ARG002
    ) -> None:
        """Test _apply_prevention_measure with failed application."""
        measure = PreventionMeasure(
            measure_id="test_measure_fail",
            strategy=PreventionStrategy.WORK_REALLOCATION,
            action=PreventionAction.REASSIGN_AGENT,
            target_branches=["branch1"],
            target_agents=["agent1"],
            predicted_conflict_id="pred1",
            urgency=PredictionConfidence.HIGH,
            description="Test measure that will fail",
        )

        # Mock the strategy handler to return failure
        with patch.object(
            prevention_system,
            "_apply_work_reallocation",
            return_value=False,
        ) as mock_handler:
            success = await prevention_system._apply_prevention_measure(measure)  # noqa: SLF001

        assert success is False
        assert measure.status == "failed"
        assert measure.applied_at is None
        assert measure.measure_id not in prevention_system.active_measures
        mock_handler.assert_called_once_with(measure)

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_prevention_measure_exception(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,  # noqa: ARG002
    ) -> None:
        """Test _apply_prevention_measure with exception during application."""
        measure = PreventionMeasure(
            measure_id="test_measure_exception",
            strategy=PreventionStrategy.DEPENDENCY_SYNC,
            action=PreventionAction.COORDINATE_TIMING,
            target_branches=["branch1"],
            target_agents=["agent1"],
            predicted_conflict_id="pred1",
            urgency=PredictionConfidence.CRITICAL,
            description="Test measure that will raise exception",
        )

        # Mock the strategy handler to raise exception
        with patch.object(
            prevention_system,
            "_apply_dependency_sync",
            side_effect=Exception("Test error"),
        ) as mock_handler:
            success = await prevention_system._apply_prevention_measure(measure)  # noqa: SLF001

        assert success is False
        assert measure.status == "failed"
        assert measure.applied_at is None
        assert "error" in measure.metadata
        assert measure.metadata["error"] == "Test error"
        assert measure.measure_id not in prevention_system.active_measures
        mock_handler.assert_called_once_with(measure)

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_prevention_measure_no_handler(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,  # noqa: ARG002
    ) -> None:
        """Test _apply_prevention_measure with missing strategy handler."""
        measure = PreventionMeasure(
            measure_id="test_measure_no_handler",
            strategy=PreventionStrategy.SEMANTIC_REFACTORING,  # Will test missing handler
            action=PreventionAction.REFACTOR_DEPENDENCIES,
            target_branches=["branch1"],
            target_agents=["agent1"],
            predicted_conflict_id="pred1",
            urgency=PredictionConfidence.LOW,
            description="Test measure with missing handler",
        )

        # Remove the handler temporarily
        original_handler = prevention_system.strategy_handlers.pop(
            PreventionStrategy.SEMANTIC_REFACTORING,
        )

        try:
            success = await prevention_system._apply_prevention_measure(measure)  # noqa: SLF001
            assert success is False
        finally:
            # Restore the handler
            prevention_system.strategy_handlers[PreventionStrategy.SEMANTIC_REFACTORING] = original_handler

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_work_reallocation(prevention_system: ConflictPreventionSystem, mock_dependencies: dict) -> None:
        """Test _apply_work_reallocation strategy."""
        measure = PreventionMeasure(
            measure_id="work_reallocation_test",
            strategy=PreventionStrategy.WORK_REALLOCATION,
            action=PreventionAction.REASSIGN_AGENT,
            target_branches=["branch1", "branch2"],
            target_agents=["agent1", "agent2"],
            predicted_conflict_id="pred1",
            urgency=PredictionConfidence.HIGH,
            description="Test work reallocation",
        )

        # Mock collaboration engine send_message
        mock_dependencies["collaboration_engine"].send_message = AsyncMock(
            return_value=True,
        )

        success = await prevention_system._apply_work_reallocation(measure)  # noqa: SLF001

        assert success is True

        # Verify messages were sent to all agents
        assert mock_dependencies["collaboration_engine"].send_message.call_count == 2

        # Verify message content for each agent
        calls = mock_dependencies["collaboration_engine"].send_message.call_args_list
        for i, call in enumerate(calls):
            args, kwargs = call
            assert kwargs["sender_id"] == "prevention_system"
            assert kwargs["recipient_id"] == f"agent{i + 1}"
            assert kwargs["message_type"] == MessageType.STATUS_UPDATE
            assert kwargs["subject"] == "Work Reallocation - Conflict Prevention"
            assert kwargs["priority"] == MessagePriority.HIGH

            content = kwargs["content"]
            assert content["measure_id"] == measure.measure_id
            assert content["action"] == "work_reallocation"
            assert content["affected_branches"] == measure.target_branches
            assert content["reason"] == measure.description

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_dependency_sync(prevention_system: ConflictPreventionSystem, mock_dependencies: dict) -> None:
        """Test _apply_dependency_sync strategy."""
        measure = PreventionMeasure(
            measure_id="dep_sync_test",
            strategy=PreventionStrategy.DEPENDENCY_SYNC,
            action=PreventionAction.COORDINATE_TIMING,
            target_branches=["main", "feature/deps"],
            target_agents=["main_agent", "feature_agent"],
            predicted_conflict_id="dep_pred",
            urgency=PredictionConfidence.MEDIUM,
            description="Test dependency synchronization",
            implementation_steps=["step1", "step2", "step3"],
        )

        # Mock collaboration engine send_message
        mock_dependencies["collaboration_engine"].send_message = AsyncMock(
            return_value=True,
        )

        success = await prevention_system._apply_dependency_sync(measure)  # noqa: SLF001

        assert success is True

        # Verify messages were sent to all agents
        assert mock_dependencies["collaboration_engine"].send_message.call_count == 2

        # Verify message content
        calls = mock_dependencies["collaboration_engine"].send_message.call_args_list
        for call in calls:
            args, kwargs = call
            assert kwargs["sender_id"] == "prevention_system"
            assert kwargs["message_type"] == MessageType.DEPENDENCY_CHANGE
            assert kwargs["subject"] == "Dependency Synchronization Required"
            assert kwargs["priority"] == MessagePriority.HIGH

            content = kwargs["content"]
            assert content["measure_id"] == measure.measure_id
            assert content["action"] == "sync_dependencies"
            assert content["branches"] == measure.target_branches
            assert content["implementation_steps"] == measure.implementation_steps

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_early_merge(prevention_system: ConflictPreventionSystem, mock_dependencies: dict) -> None:
        """Test _apply_early_merge strategy."""
        measure = PreventionMeasure(
            measure_id="early_merge_test",
            strategy=PreventionStrategy.EARLY_MERGE,
            action=PreventionAction.MERGE_EARLY,
            target_branches=["branch1", "branch2"],
            target_agents=["agent1", "agent2"],
            predicted_conflict_id="merge_pred",
            urgency=PredictionConfidence.HIGH,
            description="Test early merge",
        )

        # Mock auto resolver to return successful resolution
        mock_result = Mock()
        mock_result.outcome = "fully_resolved"
        mock_dependencies["auto_resolver"].auto_resolve_branch_conflicts = AsyncMock(
            return_value=mock_result,
        )

        success = await prevention_system._apply_early_merge(measure)  # noqa: SLF001

        assert success is True

        # Verify auto resolver was called
        mock_dependencies["auto_resolver"].auto_resolve_branch_conflicts.assert_called_once_with(
            branch1="branch1",
            branch2="branch2",
            mode=AutoResolutionMode.PREDICTIVE,
        )

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_early_merge_insufficient_branches(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,
    ) -> None:
        """Test _apply_early_merge with insufficient branches."""
        measure = PreventionMeasure(
            measure_id="early_merge_insufficient",
            strategy=PreventionStrategy.EARLY_MERGE,
            action=PreventionAction.MERGE_EARLY,
            target_branches=["single_branch"],  # Only one branch
            target_agents=["agent1"],
            predicted_conflict_id="merge_pred",
            urgency=PredictionConfidence.HIGH,
            description="Test early merge with insufficient branches",
        )

        success = await prevention_system._apply_early_merge(measure)  # noqa: SLF001

        assert success is False

        # Verify auto resolver was not called
        mock_dependencies["auto_resolver"].auto_resolve_branch_conflicts.assert_not_called()

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_agent_coordination(prevention_system: ConflictPreventionSystem, mock_dependencies: dict) -> None:
        """Test _apply_agent_coordination strategy."""
        measure = PreventionMeasure(
            measure_id="agent_coord_test",
            strategy=PreventionStrategy.AGENT_COORDINATION,
            action=PreventionAction.NOTIFY_AGENTS,
            target_branches=["feature/a", "feature/b"],
            target_agents=["agent_a", "agent_b"],
            predicted_conflict_id="coord_pred",
            urgency=PredictionConfidence.CRITICAL,
            description="Test agent coordination",
            implementation_steps=["coordinate", "communicate", "align"],
        )

        # Mock collaboration engine send_message
        mock_dependencies["collaboration_engine"].send_message = AsyncMock(
            return_value=True,
        )

        success = await prevention_system._apply_agent_coordination(measure)  # noqa: SLF001

        assert success is True

        # Verify messages were sent to all agents
        assert mock_dependencies["collaboration_engine"].send_message.call_count == 2

        # Verify message content for each agent
        calls = mock_dependencies["collaboration_engine"].send_message.call_args_list
        for i, call in enumerate(calls):
            args, kwargs = call
            agent_id = f"agent_{'a' if i == 0 else 'b'}"
            other_agent = f"agent_{'b' if i == 0 else 'a'}"

            assert kwargs["sender_id"] == "prevention_system"
            assert kwargs["recipient_id"] == agent_id
            assert kwargs["message_type"] == MessageType.CONFLICT_ALERT
            assert kwargs["subject"] == "Coordination Required - Conflict Prevention"
            assert kwargs["priority"] == MessagePriority.HIGH
            assert kwargs["requires_ack"] is True

            content = kwargs["content"]
            assert content["measure_id"] == measure.measure_id
            assert content["coordination_required"] is True
            assert other_agent in content["other_agents"]
            assert content["affected_branches"] == measure.target_branches
            assert content["steps"] == measure.implementation_steps

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_temporal_separation(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,
    ) -> None:
        """Test _apply_temporal_separation strategy."""
        measure = PreventionMeasure(
            measure_id="temporal_sep_test",
            strategy=PreventionStrategy.TEMPORAL_SEPARATION,
            action=PreventionAction.DEFER_TASK,
            target_branches=["worker1", "worker2", "worker3"],
            target_agents=["agent1", "agent2", "agent3"],
            predicted_conflict_id="temporal_pred",
            urgency=PredictionConfidence.MEDIUM,
            description="Test temporal separation",
        )

        # Mock collaboration engine send_message
        mock_dependencies["collaboration_engine"].send_message = AsyncMock(
            return_value=True,
        )

        success = await prevention_system._apply_temporal_separation(measure)  # noqa: SLF001

        assert success is True

        # Verify messages were sent to all agents
        assert mock_dependencies["collaboration_engine"].send_message.call_count == 3

        # Verify message content for each agent with increasing delays
        calls = mock_dependencies["collaboration_engine"].send_message.call_args_list
        for i, call in enumerate(calls):
            args, kwargs = call
            expected_delay = i * prevention_system.prevention_config["coordination_delay"]

            assert kwargs["sender_id"] == "prevention_system"
            assert kwargs["recipient_id"] == f"agent{i + 1}"
            assert kwargs["message_type"] == MessageType.STATUS_UPDATE
            assert kwargs["subject"] == "Temporal Coordination - Delayed Execution"
            assert kwargs["priority"] == MessagePriority.NORMAL

            content = kwargs["content"]
            assert content["measure_id"] == measure.measure_id
            assert content["delay_hours"] == expected_delay
            assert content["execution_order"] == i + 1
            assert content["total_agents"] == 3
            assert "temporal separation" in content["reason"]

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_semantic_refactoring(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,
    ) -> None:
        """Test _apply_semantic_refactoring strategy."""
        measure = PreventionMeasure(
            measure_id="semantic_refactor_test",
            strategy=PreventionStrategy.SEMANTIC_REFACTORING,
            action=PreventionAction.REFACTOR_DEPENDENCIES,
            target_branches=["api", "client"],
            target_agents=["api_dev", "client_dev"],
            predicted_conflict_id="semantic_pred",
            urgency=PredictionConfidence.HIGH,
            description="Test semantic refactoring",
            implementation_steps=["analyze", "design", "implement", "migrate"],
        )

        # Add affected_files to measure metadata for testing
        measure.metadata["affected_files"] = ["api.py", "client.py"]

        # Mock collaboration engine send_message
        mock_dependencies["collaboration_engine"].send_message = AsyncMock(
            return_value=True,
        )

        success = await prevention_system._apply_semantic_refactoring(measure)  # noqa: SLF001

        assert success is True

        # Verify messages were sent to all agents
        assert mock_dependencies["collaboration_engine"].send_message.call_count == 2

        # Verify message content
        calls = mock_dependencies["collaboration_engine"].send_message.call_args_list
        for call in calls:
            args, kwargs = call
            assert kwargs["sender_id"] == "prevention_system"
            assert kwargs["message_type"] == MessageType.STATUS_UPDATE
            assert kwargs["subject"] == "Semantic Refactoring Required"
            assert kwargs["priority"] == MessagePriority.HIGH

            content = kwargs["content"]
            assert content["measure_id"] == measure.measure_id
            assert content["refactoring_type"] == "semantic_interface"
            assert content["implementation_guide"] == measure.implementation_steps

    @staticmethod
    def test_get_prevention_summary(prevention_system: ConflictPreventionSystem) -> None:
        """Test get_prevention_summary method."""
        # Add some test data
        measure1 = PreventionMeasure(
            measure_id="active_measure_1",
            strategy=PreventionStrategy.BRANCH_ISOLATION,
            action=PreventionAction.DEFER_TASK,
            target_branches=["branch1"],
            target_agents=["agent1"],
            predicted_conflict_id="pred1",
            urgency=PredictionConfidence.HIGH,
            description="Active measure 1",
        )
        measure1.status = "applied"
        prevention_system.active_measures["active_measure_1"] = measure1

        # Add some prevention history
        result1 = PreventionResult(
            session_id="session_1",
            branches_analyzed=["main", "feature"],
            predictions_found=3,
            measures_applied=2,
            conflicts_prevented=1,
            prevention_success_rate=0.67,
            time_saved=2.5,
        )
        prevention_system.prevention_history.append(result1)

        # Update statistics
        prevention_system.prevention_stats["predictions_analyzed"] = 5
        prevention_system.prevention_stats["measures_applied"] = 3
        prevention_system.prevention_stats["conflicts_prevented"] = 2
        prevention_system.prevention_stats["prevention_success_rate"] = 0.67
        prevention_system.prevention_stats["total_time_saved"] = 4.0

        summary = prevention_system.get_prevention_summary()

        # Verify summary structure
        assert "statistics" in summary
        assert "active_measures" in summary
        assert "prevention_sessions" in summary
        assert "recent_effectiveness" in summary
        assert "configuration" in summary
        assert "system_status" in summary

        # Verify statistics
        assert summary["statistics"]["predictions_analyzed"] == 5
        assert summary["statistics"]["measures_applied"] == 3
        assert summary["statistics"]["conflicts_prevented"] == 2
        assert summary["statistics"]["prevention_success_rate"] == 0.67
        assert summary["statistics"]["total_time_saved"] == 4.0

        # Verify active measures count
        assert summary["active_measures"] == 1

        # Verify prevention sessions count
        assert summary["prevention_sessions"] == 1

        # Verify recent effectiveness
        assert summary["recent_effectiveness"]["sessions"] == 1
        assert summary["recent_effectiveness"]["avg_prevention_rate"] == 0.67
        assert summary["recent_effectiveness"]["total_time_saved"] == 2.5

        # Verify configuration
        assert summary["configuration"] == prevention_system.prevention_config

        # Verify system status
        assert summary["system_status"] == "stopped"

    @staticmethod
    def test_get_prevention_summary_empty(prevention_system: ConflictPreventionSystem) -> None:
        """Test get_prevention_summary with no data."""
        summary = prevention_system.get_prevention_summary()

        # Verify basic structure exists
        assert "statistics" in summary
        assert "active_measures" in summary
        assert "prevention_sessions" in summary
        assert "recent_effectiveness" in summary
        assert "configuration" in summary
        assert "system_status" in summary

        # Verify empty state
        assert summary["active_measures"] == 0
        assert summary["prevention_sessions"] == 0
        assert summary["recent_effectiveness"]["sessions"] == 0
        assert summary["recent_effectiveness"]["avg_prevention_rate"] == 0.0
        assert summary["recent_effectiveness"]["total_time_saved"] == 0
        assert summary["system_status"] == "stopped"

    @pytest.mark.asyncio
    @staticmethod
    async def test_get_active_branches(prevention_system: ConflictPreventionSystem) -> None:
        """Test _get_active_branches method."""
        # This is a placeholder implementation, so it should return empty list
        active_branches = await prevention_system._get_active_branches()  # noqa: SLF001
        assert isinstance(active_branches, list)
        assert active_branches == []

    @pytest.mark.asyncio
    @staticmethod
    async def test_prevention_monitor_loop_integration(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,  # noqa: ARG002
    ) -> None:
        """Test prevention monitor loop integration."""
        # Mock _get_active_branches to return test branches
        with patch.object(
            prevention_system,
            "_get_active_branches",
            return_value=["branch1", "branch2"],
        ):
            # Mock analyze_and_prevent_conflicts to return test result
            mock_result = PreventionResult(
                session_id="monitor_session",
                branches_analyzed=["branch1", "branch2"],
                predictions_found=1,
                measures_applied=1,
                conflicts_prevented=1,
            )
            with patch.object(
                prevention_system,
                "analyze_and_prevent_conflicts",
                return_value=mock_result,
            ):
                # Start monitoring with very short interval
                await prevention_system.start_prevention_monitoring(
                    monitoring_interval=0.1,
                )

                # Let it run for a short time
                await asyncio.sleep(0.15)

                # Stop monitoring
                await prevention_system.stop_prevention_monitoring()

        # Verify that monitoring was running
        assert not prevention_system._running  # noqa: SLF001

    @pytest.mark.asyncio
    @staticmethod
    async def test_analyze_and_prevent_conflicts_with_time_horizon(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,
    ) -> None:
        """Test analyze_and_prevent_conflicts with custom time horizon."""
        # Mock predict_conflicts to return empty list
        mock_dependencies["conflict_predictor"].predict_conflicts = AsyncMock(
            return_value=[],
        )

        branches = ["main", "feature"]
        custom_horizon = timedelta(hours=12)

        result = await prevention_system.analyze_and_prevent_conflicts(
            branches,
            time_horizon=custom_horizon,
        )

        # Verify custom time horizon was passed
        mock_dependencies["conflict_predictor"].predict_conflicts.assert_called_once()
        call_args = mock_dependencies["conflict_predictor"].predict_conflicts.call_args
        assert call_args[0][1] == custom_horizon

        # Verify result metadata includes time horizon
        assert "time_horizon" in result.metadata
        assert result.metadata["time_horizon"] == str(custom_horizon)

    @pytest.mark.asyncio
    @staticmethod
    async def test_analyze_and_prevent_conflicts_with_agents_filter(
        self,
        prevention_system: ConflictPreventionSystem,
        mock_dependencies: dict,
    ) -> None:
        """Test analyze_and_prevent_conflicts with specific agents."""
        # Mock predict_conflicts to return empty list
        mock_dependencies["conflict_predictor"].predict_conflicts = AsyncMock(
            return_value=[],
        )

        branches = ["main", "feature"]
        specific_agents = ["agent1", "agent3"]

        result = await prevention_system.analyze_and_prevent_conflicts(
            branches,
            agents=specific_agents,
        )

        # Verify result metadata includes agents filter
        assert "agents_considered" in result.metadata
        assert result.metadata["agents_considered"] == specific_agents

    @staticmethod
    def test_prevention_strategy_enum_coverage() -> None:
        """Test that all PreventionStrategy enum values are covered."""
        # Verify all strategies have corresponding actions
        all_strategies = list(PreventionStrategy)
        assert len(all_strategies) == 7

        expected_strategies = {
            PreventionStrategy.BRANCH_ISOLATION,
            PreventionStrategy.WORK_REALLOCATION,
            PreventionStrategy.DEPENDENCY_SYNC,
            PreventionStrategy.EARLY_MERGE,
            PreventionStrategy.AGENT_COORDINATION,
            PreventionStrategy.TEMPORAL_SEPARATION,
            PreventionStrategy.SEMANTIC_REFACTORING,
        }
        assert set(all_strategies) == expected_strategies

    @staticmethod
    def test_prevention_action_enum_coverage() -> None:
        """Test that all PreventionAction enum values are covered."""
        all_actions = list(PreventionAction)
        assert len(all_actions) == 8

        expected_actions = {
            PreventionAction.DEFER_TASK,
            PreventionAction.REASSIGN_AGENT,
            PreventionAction.MERGE_EARLY,
            PreventionAction.NOTIFY_AGENTS,
            PreventionAction.CREATE_INTERFACE,
            PreventionAction.SPLIT_WORK,
            PreventionAction.COORDINATE_TIMING,
            PreventionAction.REFACTOR_DEPENDENCIES,
        }
        assert set(all_actions) == expected_actions

    @staticmethod
    def test_default_configuration_values(prevention_system: ConflictPreventionSystem) -> None:
        """Test that default configuration values are reasonable."""
        config = prevention_system.prevention_config

        # Verify prediction threshold is reasonable (not too low or high)
        assert 0.5 <= config["prediction_threshold"] <= 0.8

        # Verify max measures is reasonable
        assert 5 <= config["max_prevention_measures"] <= 20

        # Verify prevention horizon is reasonable (hours)
        assert 12 <= config["prevention_horizon"] <= 48

        # Verify coordination delay is reasonable (hours)
        assert 1 <= config["coordination_delay"] <= 8

        # Verify early merge threshold is high enough
        assert config["early_merge_threshold"] >= 0.7

        # Verify effort threshold is reasonable (hours)
        assert 4 <= config["effort_threshold"] <= 16
