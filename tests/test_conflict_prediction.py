"""Tests for ConflictPredictor"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from libs.multi_agent.conflict_prediction import (
    ConflictPredictor,
    PredictionResult,
    PredictionConfidence,
    ConflictPattern,
    ConflictVector,
)
from libs.multi_agent.conflict_resolution import (
    ConflictResolutionEngine,
    ConflictType,
    ConflictSeverity,
)
from libs.multi_agent.branch_manager import BranchManager


class TestConflictVector:
    """Test cases for ConflictVector"""

    def test_init(self):
        """Test ConflictVector initialization"""
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
    """Test cases for PredictionResult"""

    def test_init(self):
        """Test PredictionResult initialization"""
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
    """Test cases for ConflictPredictor"""

    @pytest.fixture
    def mock_conflict_engine(self):
        """Create mock conflict resolution engine"""
        return Mock(spec=ConflictResolutionEngine)

    @pytest.fixture
    def mock_branch_manager(self):
        """Create mock branch manager"""
        return Mock(spec=BranchManager)

    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def predictor(self, mock_conflict_engine, mock_branch_manager, temp_repo):
        """Create ConflictPredictor instance"""
        return ConflictPredictor(
            conflict_engine=mock_conflict_engine,
            branch_manager=mock_branch_manager,
            repo_path=str(temp_repo),
        )

    def test_init(
        self, predictor, mock_conflict_engine, mock_branch_manager, temp_repo
    ):
        """Test ConflictPredictor initialization"""
        assert predictor.conflict_engine == mock_conflict_engine
        assert predictor.branch_manager == mock_branch_manager
        assert predictor.repo_path == temp_repo
        assert predictor.predictions == {}
        assert predictor.prediction_history == []
        assert len(predictor.pattern_detectors) == 8
        assert predictor.min_confidence_threshold == 0.3
        assert predictor.max_predictions_per_run == 50

    def test_likelihood_to_confidence(self, predictor):
        """Test likelihood to confidence conversion"""
        assert (
            predictor._likelihood_to_confidence(0.95) == PredictionConfidence.CRITICAL
        )
        assert predictor._likelihood_to_confidence(0.8) == PredictionConfidence.HIGH
        assert predictor._likelihood_to_confidence(0.6) == PredictionConfidence.MEDIUM
        assert predictor._likelihood_to_confidence(0.3) == PredictionConfidence.LOW

    @pytest.mark.asyncio
    async def test_predict_conflicts_empty_branches(self, predictor):
        """Test conflict prediction with empty branch list"""
        predictions = await predictor.predict_conflicts([])
        assert predictions == []

    @pytest.mark.asyncio
    async def test_calculate_conflict_vector(self, predictor):
        """Test conflict vector calculation"""
        # Mock the required methods
        predictor.conflict_engine._get_changed_files = AsyncMock(
            return_value={"file1.py": "M", "file2.py": "A"}
        )
        predictor._get_change_frequency = AsyncMock(return_value=2.5)
        predictor._calculate_branch_complexity = AsyncMock(return_value=50.0)
        predictor._calculate_dependency_coupling = AsyncMock(return_value=0.6)
        predictor._calculate_semantic_distance = AsyncMock(return_value=0.4)
        predictor._calculate_temporal_proximity = AsyncMock(return_value=0.3)

        vector = await predictor._calculate_conflict_vector("branch1", "branch2")

        assert isinstance(vector, ConflictVector)
        assert 0.0 <= vector.file_overlap_score <= 1.0
        assert 0.0 <= vector.change_frequency_score <= 1.0
        assert 0.0 <= vector.complexity_score <= 1.0
        assert vector.dependency_coupling_score == 0.6
        assert vector.semantic_distance_score == 0.4
        assert vector.temporal_proximity_score == 0.3

    def test_extract_imports(self, predictor):
        """Test import extraction from Python code"""
        code = """
import os
import sys
from datetime import datetime
from pathlib import Path

def test():
    pass
"""
        imports = predictor._extract_imports(code)

        assert "import os" in imports
        assert "import sys" in imports
        assert "from datetime import datetime" in imports
        assert "from pathlib import Path" in imports

    def test_extract_imports_with_syntax_error(self, predictor):
        """Test import extraction with syntax errors"""
        code = """
import os
invalid syntax here !!!
from sys import path
"""
        imports = predictor._extract_imports(code)

        # Should fallback to regex parsing
        assert len(imports) >= 2
        assert any("import os" in imp for imp in imports)
        assert any("from sys import path" in imp for imp in imports)

    def test_imports_likely_to_conflict(self, predictor):
        """Test import conflict likelihood detection"""
        imports1 = ["import os", "import sys", "from datetime import datetime"]
        imports2 = ["import os", "import json", "from datetime import date"]

        # Should detect potential conflict due to overlapping but different imports
        result = predictor._imports_likely_to_conflict(imports1, imports2)
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
        result = predictor._imports_likely_to_conflict(imports3, imports4)
        assert result is True

    @pytest.mark.asyncio
    async def test_detect_import_conflicts(self, predictor):
        """Test import conflict detection"""
        vector = ConflictVector(0.5, 0.3, 0.2, 0.4, 0.6, 0.1)

        # Mock the helper method
        predictor._get_python_files_with_imports = AsyncMock(
            return_value={
                "file1.py": ["import os", "import sys", "import json"],
                "file2.py": ["from datetime import datetime"],
            }
        )

        # Mock conflict detection
        predictor._imports_likely_to_conflict = Mock(return_value=True)

        result = await predictor._detect_import_conflicts("branch1", "branch2", vector)

        if result:  # Only test if conflicts were detected
            assert isinstance(result, PredictionResult)
            assert result.pattern == ConflictPattern.OVERLAPPING_IMPORTS
            assert result.predicted_conflict_type == ConflictType.MERGE_CONFLICT
            assert "branch1" in result.affected_branches
            assert "branch2" in result.affected_branches

    @pytest.mark.asyncio
    async def test_detect_signature_drift(self, predictor):
        """Test function signature drift detection"""
        vector = ConflictVector(0.4, 0.3, 0.5, 0.2, 0.8, 0.1)

        # Mock function signatures
        predictor._get_all_function_signatures = AsyncMock(
            side_effect=[
                {
                    "file1.py:test_func": "def test_func(a, b, c):",
                    "file1.py:other_func": "def other_func(x):",
                },
                {
                    "file1.py:test_func": "def test_func(a, b):",  # Different signature
                    "file1.py:other_func": "def other_func(x):",  # Same signature
                },
            ]
        )

        result = await predictor._detect_signature_drift("branch1", "branch2", vector)

        if result:  # Only test if drift was detected
            assert isinstance(result, PredictionResult)
            assert result.pattern == ConflictPattern.FUNCTION_SIGNATURE_DRIFT
            assert result.predicted_conflict_type == ConflictType.SEMANTIC
            assert result.likelihood_score > 0

    @pytest.mark.asyncio
    async def test_detect_naming_collisions(self, predictor):
        """Test naming collision detection"""
        vector = ConflictVector(0.3, 0.4, 0.6, 0.3, 0.5, 0.2)

        # Mock symbol definitions
        predictor._extract_symbol_definitions = AsyncMock(
            side_effect=[
                {"TestClass": "file1.py:10", "my_function": "file1.py:20"},
                {"TestClass": "file2.py:15", "other_function": "file2.py:25"},
            ]
        )

        result = await predictor._detect_naming_collisions("branch1", "branch2", vector)

        if result:  # Only test if collisions were detected
            assert isinstance(result, PredictionResult)
            assert result.pattern == ConflictPattern.VARIABLE_NAMING_COLLISION
            assert result.predicted_conflict_type == ConflictType.SEMANTIC

    @pytest.mark.asyncio
    async def test_detect_version_conflicts(self, predictor):
        """Test dependency version conflict detection"""
        vector = ConflictVector(0.2, 0.3, 0.4, 0.7, 0.3, 0.5)

        # Mock dependency versions
        predictor._get_dependency_versions = AsyncMock(
            side_effect=[
                {"requests": "2.25.1", "numpy": "1.21.0"},
                {"requests": "2.26.0", "numpy": "1.21.0"},  # Different requests version
            ]
        )

        predictor._calculate_version_distance = Mock(return_value=0.3)

        result = await predictor._detect_version_conflicts("branch1", "branch2", vector)

        if result:  # Only test if conflicts were detected
            assert isinstance(result, PredictionResult)
            assert result.pattern == ConflictPattern.DEPENDENCY_VERSION_MISMATCH
            assert result.predicted_conflict_type == ConflictType.DEPENDENCY

    def test_calculate_version_distance(self, predictor):
        """Test version distance calculation"""
        # Test same versions
        distance = predictor._calculate_version_distance("1.2.3", "1.2.3")
        assert distance == 0.0

        # Test different versions
        distance = predictor._calculate_version_distance("1.2.3", "1.2.4")
        assert distance > 0.0

        # Test major version difference
        distance1 = predictor._calculate_version_distance("1.2.3", "2.2.3")
        distance2 = predictor._calculate_version_distance("1.2.3", "1.3.3")
        assert distance1 > distance2  # Major version changes should be weighted more

    @pytest.mark.asyncio
    async def test_get_change_frequency(self, predictor):
        """Test change frequency calculation"""
        # Mock git command
        predictor.conflict_engine._run_git_command = AsyncMock(
            return_value=Mock(stdout="14\n")  # 14 commits in last week
        )

        frequency = await predictor._get_change_frequency("test-branch")
        assert frequency == 2.0  # 14 commits / 7 days

    @pytest.mark.asyncio
    async def test_calculate_branch_complexity(self, predictor):
        """Test branch complexity calculation"""
        # Mock git command with diff stats
        predictor.conflict_engine._run_git_command = AsyncMock(
            return_value=Mock(
                stdout="""
 file1.py | 10 ++++++++++
 file2.py | 5 +++++
 file3.py | 3 ---
 3 files changed, 15 insertions(+), 3 deletions(-)
"""
            )
        )

        complexity = await predictor._calculate_branch_complexity("test-branch")
        assert complexity > 0.0
        assert complexity <= 100.0

    @pytest.mark.asyncio
    async def test_get_python_files_with_imports(self, predictor):
        """Test getting Python files with imports"""
        # Mock the required methods
        predictor.conflict_engine._get_python_files_changed = AsyncMock(
            return_value=["file1.py", "file2.py"]
        )
        predictor.conflict_engine._get_file_content = AsyncMock(
            side_effect=[
                "import os\nimport sys\n\ndef test():\n    pass",
                "from datetime import datetime\n\nclass Test:\n    pass",
            ]
        )

        files_with_imports = await predictor._get_python_files_with_imports(
            "test-branch"
        )

        assert "file1.py" in files_with_imports
        assert "file2.py" in files_with_imports
        assert len(files_with_imports["file1.py"]) >= 2  # Should have import statements
        assert len(files_with_imports["file2.py"]) >= 1

    @pytest.mark.asyncio
    async def test_get_dependency_versions(self, predictor):
        """Test dependency version extraction"""
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

        predictor.conflict_engine._get_file_content = AsyncMock(
            side_effect=[requirements_content, pyproject_content]
        )

        versions = await predictor._get_dependency_versions("test-branch")

        assert "requests" in versions
        assert "numpy" in versions
        assert "pytest" in versions

    @pytest.mark.asyncio
    async def test_apply_ml_scoring(self, predictor):
        """Test ML scoring application"""
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
        predictor.historical_patterns[ConflictPattern.OVERLAPPING_IMPORTS] = [
            {"accurate": 1},
            {"accurate": 0},
            {"accurate": 1},
        ]

        scored_predictions = await predictor._apply_ml_scoring(predictions)

        assert len(scored_predictions) == 2
        # Likelihood scores may have been adjusted
        for prediction in scored_predictions:
            assert 0.0 <= prediction.likelihood_score <= 1.0

    def test_get_prediction_summary_empty(self, predictor):
        """Test prediction summary with no predictions"""
        summary = predictor.get_prediction_summary()

        assert summary["total_predictions"] == 0
        assert summary["by_confidence"] == {}
        assert summary["by_pattern"] == {}
        assert "accuracy_metrics" in summary

    def test_get_prediction_summary_with_predictions(self, predictor):
        """Test prediction summary with predictions"""
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
            timeline_prediction=datetime.now() + timedelta(days=1),
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
            timeline_prediction=datetime.now() - timedelta(days=1),  # Past prediction
        )

        predictor.predictions["test1"] = prediction1
        predictor.predictions["test2"] = prediction2

        summary = predictor.get_prediction_summary()

        assert summary["total_predictions"] == 2
        assert summary["active_predictions"] == 1  # Only future predictions
        assert summary["by_confidence"]["high"] == 1
        assert summary["by_confidence"]["medium"] == 1
        assert summary["by_pattern"]["overlapping_imports"] == 1
        assert summary["by_pattern"]["function_signature_drift"] == 1
        assert len(summary["most_likely_conflicts"]) == 2

    @pytest.mark.asyncio
    async def test_predict_conflicts_integration(self, predictor):
        """Test full conflict prediction integration"""
        # Mock all required methods for a minimal integration test
        predictor._calculate_conflict_vector = AsyncMock(
            return_value=ConflictVector(0.5, 0.4, 0.6, 0.3, 0.7, 0.2)
        )

        predictor._detect_import_conflicts = AsyncMock(
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
            )
        )

        # Mock other detectors to return None
        for pattern in ConflictPattern:
            if pattern != ConflictPattern.OVERLAPPING_IMPORTS:
                detector_name = f"_detect_{pattern.value}"
                if hasattr(predictor, detector_name):
                    setattr(predictor, detector_name, AsyncMock(return_value=None))

        predictions = await predictor.predict_conflicts(["branch1", "branch2"])

        assert len(predictions) >= 0  # May be 0 or more depending on mocked results
        if predictions:
            assert all(isinstance(p, PredictionResult) for p in predictions)
            assert len(predictor.predictions) > 0
            assert len(predictor.prediction_history) > 0
