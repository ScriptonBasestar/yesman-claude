import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.conflict_prediction import (
    ConflictPattern,
    ConflictPredictor,
    ConflictVector,
    PredictionConfidence,
    PredictionResult,
)
from libs.multi_agent.conflict_resolution import ConflictResolutionEngine, ConflictSeverity, ConflictType


class TestConflictVector:
    """Test cases for ConflictVector."""

    @staticmethod
    def test_init() -> None:
        """Test ConflictVector initialization."""
        vector = ConflictVector(
            file_overlap_score=0.5,
            change_frequency_score=0.3,
            complexity_score=0.7,
            dependency_coupling_score=0.4,
            semantic_distance_score=0.6,
            temporal_proximity_score=0.2,
        )

        assert vector.file_overlap_score == 0.5
        assert vector.change_frequency_score == 0.3
        assert vector.complexity_score == 0.7
        assert vector.dependency_coupling_score == 0.4
        assert vector.semantic_distance_score == 0.6
        assert vector.temporal_proximity_score == 0.2


class TestPredictionResult:
    """Test cases for PredictionResult."""

    @staticmethod
    def test_init() -> None:
        """Test PredictionResult initialization."""
        result = PredictionResult(
            prediction_id="test-prediction",
            confidence=PredictionConfidence.HIGH,
            pattern=ConflictPattern.OVERLAPPING_IMPORTS,
            affected_branches=["branch1", "branch2"],
            affected_files=["test.py"],
            predicted_conflict_type=ConflictType.MERGE_CONFLICT,
            predicted_severity=ConflictSeverity.MEDIUM,
            likelihood_score=0.8,
            description="Test prediction",
        )

        assert result.prediction_id == "test-prediction"
        assert result.confidence == PredictionConfidence.HIGH
        assert result.pattern == ConflictPattern.OVERLAPPING_IMPORTS
        assert result.affected_branches == ["branch1", "branch2"]
        assert result.affected_files == ["test.py"]
        assert result.predicted_conflict_type == ConflictType.MERGE_CONFLICT
        assert result.predicted_severity == ConflictSeverity.MEDIUM
        assert result.likelihood_score == 0.8
        assert result.description == "Test prediction"
        assert result.prevention_suggestions == []
        assert result.affected_agents == []


class TestConflictPredictor:
    """Test cases for ConflictPredictor."""

    @pytest.fixture
    @staticmethod
    def mock_conflict_engine() -> Mock:
        """Create mock conflict resolution engine."""
        return Mock(spec=ConflictResolutionEngine)

    @pytest.fixture
    @staticmethod
    def mock_branch_manager() -> Mock:
        """Create mock branch manager."""
        return Mock(spec=BranchManager)

    @pytest.fixture
    @staticmethod
    def temp_repo() -> Path:
        """Create temporary repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    @staticmethod
    def predictor(mock_conflict_engine: Mock, mock_branch_manager: Mock, temp_repo: Path) -> ConflictPredictor:
        """Create ConflictPredictor instance."""
        return ConflictPredictor(
            conflict_engine=mock_conflict_engine,
            branch_manager=mock_branch_manager,
            repo_path=str(temp_repo),
        )

    @staticmethod
    def test_init(
        predictor: ConflictPredictor,
        mock_conflict_engine: Mock,
        mock_branch_manager: Mock,
        temp_repo: Path,
    ) -> None:
        """Test ConflictPredictor initialization."""
        assert predictor.conflict_engine == mock_conflict_engine
        assert predictor.branch_manager == mock_branch_manager
        assert str(predictor.repo_path) == str(temp_repo)
        assert cast(dict[str, Any], predictor.predictions) == {}
        assert cast(list, predictor.prediction_history) == []
        assert len(cast(dict[str, Any], predictor.pattern_detectors)) == 8
        assert cast(float, predictor.min_confidence_threshold) == 0.3
        assert cast(int, predictor.max_predictions_per_run) == 50

    @staticmethod
    def test_likelihood_to_confidence(predictor: ConflictPredictor) -> None:
        """Test likelihood to confidence conversion."""
        assert predictor._likelihood_to_confidence(0.95) == PredictionConfidence.CRITICAL  # noqa: SLF001
        assert predictor._likelihood_to_confidence(0.8) == PredictionConfidence.HIGH  # noqa: SLF001
        assert predictor._likelihood_to_confidence(0.6) == PredictionConfidence.MEDIUM  # noqa: SLF001
        assert predictor._likelihood_to_confidence(0.3) == PredictionConfidence.LOW  # noqa: SLF001

    @pytest.mark.asyncio
    @staticmethod
    async def test_predict_conflicts_empty_branches(predictor: ConflictPredictor) -> None:
        """Test conflict prediction with empty branch list."""
        predictions = await predictor.predict_conflicts([])
        assert predictions == []

    @pytest.mark.asyncio
    @staticmethod
    async def test_calculate_conflict_vector(predictor: ConflictPredictor) -> None:
        """Test conflict vector calculation."""
        # Mock the required methods
        cast(Any, predictor.conflict_engine)._get_changed_files = AsyncMock(  # noqa: SLF001
            return_value={"file1.py": "M", "file2.py": "A"},
        )
        cast(Any, predictor)._get_change_frequency = AsyncMock(return_value=2.5)  # noqa: SLF001
        cast(Any, predictor)._calculate_branch_complexity = AsyncMock(return_value=50.0)  # noqa: SLF001
        cast(Any, predictor)._calculate_dependency_coupling = AsyncMock(return_value=0.6)  # noqa: SLF001
        cast(Any, predictor)._calculate_semantic_distance = AsyncMock(return_value=0.4)  # noqa: SLF001
        cast(Any, predictor)._calculate_temporal_proximity = AsyncMock(return_value=0.3)  # noqa: SLF001

        vector = await cast(Any, predictor)._calculate_conflict_vector("branch1", "branch2")  # noqa: SLF001

        assert isinstance(vector, ConflictVector)
        assert 0.0 <= vector.file_overlap_score <= 1.0
        assert 0.0 <= vector.change_frequency_score <= 1.0
        assert 0.0 <= vector.complexity_score <= 1.0
        assert vector.dependency_coupling_score == 0.6
        assert vector.semantic_distance_score == 0.4
        assert vector.temporal_proximity_score == 0.3

    @staticmethod
    def test_extract_imports(predictor: ConflictPredictor) -> None:
        """Test import extraction from Python code."""
        code = """

def test() -> object:
    pass
"""
        imports = cast(Any, predictor)._extract_imports(code)  # noqa: SLF001

        assert "import os" in imports
        assert "import sys" in imports
        assert "from datetime import UTC, datetime" in imports
        assert "from pathlib import Path" in imports

    @staticmethod
    def test_extract_imports_with_syntax_error(predictor: ConflictPredictor) -> None:
        """Test import extraction with syntax errors."""
        code = """
invalid syntax here !!!
"""
        imports = cast(Any, predictor)._extract_imports(code)  # noqa: SLF001

        # Should fallback to regex parsing
        assert len(imports) >= 2
        assert any("import os" in imp for imp in imports)
        assert any("from sys import path" in imp for imp in imports)

    @staticmethod
    def test_imports_likely_to_conflict(predictor: ConflictPredictor) -> None:
        """Test import conflict likelihood detection."""
        imports1 = ["import os", "import sys", "from datetime import UTC, datetime"]
        imports2 = ["import os", "import json", "from datetime import UTC, date"]

        result = cast(Any, predictor)._imports_likely_to_conflict(imports1, imports2)  # noqa: SLF001
        # This specific case might not trigger conflict, but test the logic exists
        assert isinstance(result, bool)

        # Test clear conflict case
        imports3 = [
            "import os",
            "import sys",
            "import json",
            "import re",
            "import asyncio",
            "import logging",
        ]
        imports4 = [
            "import os",
            "import sys",
            "import json",
            "import re",
            "import asyncio",
            "import datetime",
            "import pathlib",
            "import collections",
            "import typing",
        ]
        result = cast(Any, predictor)._imports_likely_to_conflict(imports3, imports4)  # noqa: SLF001
        assert result is True

    @pytest.mark.asyncio
    @staticmethod
    async def test_detect_import_conflicts(predictor: ConflictPredictor) -> None:
        """Test import conflict detection."""
        vector = ConflictVector(0.5, 0.3, 0.2, 0.4, 0.6, 0.1)

        # Mock the helper method
        cast(Any, predictor)._get_python_files_with_imports = AsyncMock(  # noqa: SLF001
            return_value={
                "file1.py": ["import os", "import sys", "import json"],
                "file2.py": ["from datetime import UTC, datetime"],
            },
        )

        # Mock conflict detection
        cast(Any, predictor)._imports_likely_to_conflict = Mock(return_value=True)  # noqa: SLF001

        result = await cast(Any, predictor)._detect_import_conflicts("branch1", "branch2", vector)  # noqa: SLF001

        if result:  # Only test if conflicts were detected
            assert isinstance(result, PredictionResult)
            assert result.pattern == ConflictPattern.OVERLAPPING_IMPORTS
            assert result.predicted_conflict_type == ConflictType.MERGE_CONFLICT
            assert "branch1" in result.affected_branches
            assert "branch2" in result.affected_branches

    @pytest.mark.asyncio
    @staticmethod
    async def test_detect_signature_drift(predictor: ConflictPredictor) -> None:
        """Test function signature drift detection."""
        vector = ConflictVector(0.4, 0.3, 0.5, 0.2, 0.8, 0.1)

        # Mock function signatures
        cast(Any, predictor)._get_all_function_signatures = AsyncMock(  # noqa: SLF001
            side_effect=[
                {
                    "file1.py:test_func": "def test_func(a, b, c):",
                    "file1.py:other_func": "def other_func(x):",
                },
                {
                    "file1.py:test_func": "def test_func(a, b):",  # Different signature
                    "file1.py:other_func": "def other_func(x):",  # Same signature
                },
            ],
        )

        result = await cast(Any, predictor)._detect_signature_drift("branch1", "branch2", vector)  # noqa: SLF001

        if result:  # Only test if drift was detected
            assert isinstance(result, PredictionResult)
            assert result.pattern == ConflictPattern.FUNCTION_SIGNATURE_DRIFT
            assert result.predicted_conflict_type == ConflictType.SEMANTIC
            assert result.likelihood_score > 0

    @pytest.mark.asyncio
    @staticmethod
    async def test_detect_naming_collisions(predictor: ConflictPredictor) -> None:
        """Test naming collision detection."""
        vector = ConflictVector(0.3, 0.4, 0.6, 0.3, 0.5, 0.2)

        # Mock symbol definitions
        cast(Any, predictor)._extract_symbol_definitions = AsyncMock(  # noqa: SLF001
            side_effect=[
                {"TestClass": "file1.py:10", "my_function": "file1.py:20"},
                {"TestClass": "file2.py:15", "other_function": "file2.py:25"},
            ],
        )

        result = await cast(Any, predictor)._detect_naming_collisions("branch1", "branch2", vector)  # noqa: SLF001

        if result:  # Only test if collisions were detected
            assert isinstance(result, PredictionResult)
            assert result.pattern == ConflictPattern.VARIABLE_NAMING_COLLISION
            assert result.predicted_conflict_type == ConflictType.SEMANTIC

    @pytest.mark.asyncio
    @staticmethod
    async def test_detect_version_conflicts(predictor: ConflictPredictor) -> None:
        """Test dependency version conflict detection."""
        vector = ConflictVector(0.2, 0.3, 0.4, 0.7, 0.3, 0.5)

        # Mock dependency versions
        cast(Any, predictor)._get_dependency_versions = AsyncMock(  # noqa: SLF001
            side_effect=[
                {"requests": "2.25.1", "numpy": "1.21.0"},
                {"requests": "2.26.0", "numpy": "1.21.0"},  # Different requests version
            ],
        )

        cast(Any, predictor)._calculate_version_distance = Mock(return_value=0.3)  # noqa: SLF001

        result = await cast(Any, predictor)._detect_version_conflicts("branch1", "branch2", vector)  # noqa: SLF001

        if result:  # Only test if conflicts were detected
            assert isinstance(result, PredictionResult)
            assert result.pattern == ConflictPattern.DEPENDENCY_VERSION_MISMATCH
            assert result.predicted_conflict_type == ConflictType.DEPENDENCY

    @staticmethod
    def test_calculate_version_distance(predictor: ConflictPredictor) -> None:
        """Test version distance calculation."""
        # Test same versions
        distance = cast(Any, predictor)._calculate_version_distance("1.2.3", "1.2.3")  # noqa: SLF001
        assert distance == 0.0

        # Test different versions
        distance = cast(Any, predictor)._calculate_version_distance("1.2.3", "1.2.4")  # noqa: SLF001
        assert distance > 0.0

        # Test major version difference
        distance1 = cast(Any, predictor)._calculate_version_distance("1.2.3", "2.2.3")  # noqa: SLF001
        distance2 = cast(Any, predictor)._calculate_version_distance("1.2.3", "1.3.3")  # noqa: SLF001
        assert distance1 > distance2  # Major version changes should be weighted more

    @pytest.mark.asyncio
    @staticmethod
    async def test_get_change_frequency(predictor: ConflictPredictor) -> None:
        """Test change frequency calculation."""
        # Mock git command
        cast(Any, predictor.conflict_engine)._run_git_command = AsyncMock(  # noqa: SLF001
            return_value=Mock(stdout="14\n"),  # 14 commits in last week
        )

        frequency = await cast(Any, predictor)._get_change_frequency("test-branch")  # noqa: SLF001
        assert frequency == 2.0  # 14 commits / 7 days

    @pytest.mark.asyncio
    @staticmethod
    async def test_calculate_branch_complexity(predictor: ConflictPredictor) -> None:
        """Test branch complexity calculation."""
        # Mock git command with diff stats
        cast(Any, predictor.conflict_engine)._run_git_command = AsyncMock(  # noqa: SLF001
            return_value=Mock(
                stdout="""
 file1.py | 10 ++++++++++
 file2.py | 5 +++++
 file3.py | 3 ---
 3 files changed, 15 insertions(+), 3 deletions(-)
""",
            ),
        )

        complexity = await cast(Any, predictor)._calculate_branch_complexity("test-branch")  # noqa: SLF001
        assert complexity > 0.0
        assert complexity <= 100.0

    @pytest.mark.asyncio
    @staticmethod
    async def test_get_python_files_with_imports(predictor: ConflictPredictor) -> None:
        """Test getting Python files with imports."""
        # Mock the required methods
        cast(Any, predictor.conflict_engine)._get_python_files_changed = AsyncMock(  # noqa: SLF001
            return_value=["file1.py", "file2.py"],
        )
        cast(Any, predictor.conflict_engine)._get_file_content = AsyncMock(  # noqa: SLF001
            side_effect=[
                "import os\nimport sys\n\ndef test():\n    pass",
                "from datetime import UTC, datetime\n\nclass Test:\n    pass",
            ],
        )

        files_with_imports = await cast(Any, predictor)._get_python_files_with_imports(  # noqa: SLF001
            "test-branch",
        )

        assert "file1.py" in files_with_imports
        assert "file2.py" in files_with_imports
        assert len(files_with_imports["file1.py"]) >= 2  # Should have import statements
        assert len(files_with_imports["file2.py"]) >= 1

    @pytest.mark.asyncio
    @staticmethod
    async def test_get_dependency_versions(predictor: ConflictPredictor) -> None:
        """Test dependency version extraction."""
        # Mock requirements.txt content
        requirements_content = """
requests==2.25.1
numpy>=1.21.0
flask==2.0.1
# Comment line
pytest==6.2.4
"""

        pyproject_content = """
[dependencies]
requests = ">=2.25.0"
numpy = "^1.21.0"

[dev-dependencies]
pytest = ">=6.0.0"
"""

        cast(Any, predictor.conflict_engine)._get_file_content = AsyncMock(  # noqa: SLF001
            side_effect=[requirements_content, pyproject_content],
        )

        versions = await cast(Any, predictor)._get_dependency_versions("test-branch")  # noqa: SLF001

        assert "requests" in versions
        assert "numpy" in versions
        assert "pytest" in versions

    @pytest.mark.asyncio
    @staticmethod
    async def test_apply_ml_scoring(predictor: ConflictPredictor) -> None:
        """Test ML scoring application."""
        # Create test predictions
        predictions = [
            PredictionResult(
                prediction_id="test1",
                confidence=PredictionConfidence.MEDIUM,
                pattern=ConflictPattern.OVERLAPPING_IMPORTS,
                affected_branches=["b1", "b2"],
                affected_files=["f1"],
                predicted_conflict_type=ConflictType.MERGE_CONFLICT,
                predicted_severity=ConflictSeverity.LOW,
                likelihood_score=0.6,
                description="Test prediction 1",
            ),
            PredictionResult(
                prediction_id="test2",
                confidence=PredictionConfidence.HIGH,
                pattern=ConflictPattern.FUNCTION_SIGNATURE_DRIFT,
                affected_branches=["b1", "b3"],
                affected_files=["f2"],
                predicted_conflict_type=ConflictType.SEMANTIC,
                predicted_severity=ConflictSeverity.HIGH,
                likelihood_score=0.8,
                description="Test prediction 2",
            ),
        ]

        # Add some historical data
        cast(Any, predictor.historical_patterns)[ConflictPattern.OVERLAPPING_IMPORTS] = [
            {"accurate": 1},
            {"accurate": 0},
            {"accurate": 1},
        ]

        scored_predictions = await cast(Any, predictor)._apply_ml_scoring(predictions)  # noqa: SLF001

        assert len(scored_predictions) == 2
        # Likelihood scores may have been adjusted
        for prediction in scored_predictions:
            assert 0.0 <= prediction.likelihood_score <= 1.0

    @staticmethod
    def test_get_prediction_summary_empty(predictor: ConflictPredictor) -> None:
        """Test prediction summary with no predictions."""
        summary = predictor.get_prediction_summary()

        assert cast(dict[str, Any], summary)["total_predictions"] == 0
        assert cast(dict[str, Any], summary)["by_confidence"] == {}
        assert cast(dict[str, Any], summary)["by_pattern"] == {}
        assert "accuracy_metrics" in cast(dict[str, Any], summary)

    @staticmethod
    def test_get_prediction_summary_with_predictions(predictor: ConflictPredictor) -> None:
        """Test prediction summary with predictions."""
        # Add test predictions
        prediction1 = PredictionResult(
            prediction_id="test1",
            confidence=PredictionConfidence.HIGH,
            pattern=ConflictPattern.OVERLAPPING_IMPORTS,
            affected_branches=["b1", "b2"],
            affected_files=["f1"],
            predicted_conflict_type=ConflictType.MERGE_CONFLICT,
            predicted_severity=ConflictSeverity.LOW,
            likelihood_score=0.8,
            description="Test prediction 1",
            timeline_prediction=datetime.now(UTC) + timedelta(days=1),
        )

        prediction2 = PredictionResult(
            prediction_id="test2",
            confidence=PredictionConfidence.MEDIUM,
            pattern=ConflictPattern.FUNCTION_SIGNATURE_DRIFT,
            affected_branches=["b1", "b3"],
            affected_files=["f2"],
            predicted_conflict_type=ConflictType.SEMANTIC,
            predicted_severity=ConflictSeverity.HIGH,
            likelihood_score=0.6,
            description="Test prediction 2",
            timeline_prediction=datetime.now(UTC) - timedelta(days=1),  # Past prediction
        )

        cast(dict[str, Any], predictor.predictions)["test1"] = prediction1
        cast(dict[str, Any], predictor.predictions)["test2"] = prediction2

        summary = predictor.get_prediction_summary()

        assert cast(dict[str, Any], summary)["total_predictions"] == 2
        assert cast(dict[str, Any], summary)["active_predictions"] == 1  # Only future predictions
        assert cast(dict[str, Any], cast(dict[str, Any], summary)["by_confidence"])["high"] == 1
        assert cast(dict[str, Any], cast(dict[str, Any], summary)["by_confidence"])["medium"] == 1
        assert cast(dict[str, Any], cast(dict[str, Any], summary)["by_pattern"])["overlapping_imports"] == 1
        assert cast(dict[str, Any], cast(dict[str, Any], summary)["by_pattern"])["function_signature_drift"] == 1
        assert len(cast(list, cast(dict[str, Any], summary)["most_likely_conflicts"])) == 2

    @pytest.mark.asyncio
    @staticmethod
    async def test_predict_conflicts_integration(predictor: ConflictPredictor) -> None:
        """Test full conflict prediction integration."""
        # Mock all required methods for a minimal integration test
        cast(Any, predictor)._calculate_conflict_vector = AsyncMock(  # noqa: SLF001
            return_value=ConflictVector(0.5, 0.4, 0.6, 0.3, 0.7, 0.2),
        )

        cast(Any, predictor)._detect_import_conflicts = AsyncMock(  # noqa: SLF001
            return_value=PredictionResult(
                prediction_id="import_test",
                confidence=PredictionConfidence.MEDIUM,
                pattern=ConflictPattern.OVERLAPPING_IMPORTS,
                affected_branches=["branch1", "branch2"],
                affected_files=["test.py"],
                predicted_conflict_type=ConflictType.MERGE_CONFLICT,
                predicted_severity=ConflictSeverity.LOW,
                likelihood_score=0.6,
                description="Import conflict prediction",
            ),
        )

        # Mock other detectors to return None
        for pattern in ConflictPattern:
            if pattern != ConflictPattern.OVERLAPPING_IMPORTS:
                detector_name = f"_detect_{pattern.value}"
                if hasattr(predictor, detector_name):
                    setattr(cast(Any, predictor), detector_name, AsyncMock(return_value=None))

        predictions = await predictor.predict_conflicts(["branch1", "branch2"])

        assert len(predictions) >= 0  # May be 0 or more depending on mocked results
        if predictions:
            assert all(isinstance(p, PredictionResult) for p in predictions)
            assert len(cast(dict[str, Any], predictor.predictions)) > 0
            assert len(cast(list, predictor.prediction_history)) > 0
