# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Advanced conflict prediction system for multi-agent branch development."""

import ast
import difflib
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import NamedTuple

from .branch_manager import BranchManager
from .conflict_resolution import (
    ConflictInfo,
    ConflictResolutionEngine,
    ConflictSeverity,
    ConflictType,
)
from .semantic_analyzer import SemanticAnalyzer

logger = logging.getLogger(__name__)

# Constants for magic number replacements
SIMILARITY_THRESHOLD_HIGH = 0.8
SIMILARITY_THRESHOLD_MEDIUM = 0.8
CONFIDENCE_CRITICAL_THRESHOLD = 0.9
CONFIDENCE_HIGH_THRESHOLD = 0.7
CONFIDENCE_MEDIUM_THRESHOLD = 0.4
MIN_PARTS_FOR_PARSING = 2
HIGH_OVERLAP_THRESHOLD = 5
SIGNIFICANT_DIFFERENCES_THRESHOLD = 3
HIGH_SCORE_THRESHOLD = 5
MEDIUM_SCORE_THRESHOLD = 2


class PredictionConfidence(Enum):
    """Confidence levels for conflict predictions."""

    LOW = "low"  # 20-40% chance
    MEDIUM = "medium"  # 40-70% chance
    HIGH = "high"  # 70-90% chance
    CRITICAL = "critical"  # 90%+ chance


class ConflictPattern(Enum):
    """Types of conflict patterns that can be predicted."""

    OVERLAPPING_IMPORTS = "overlapping_imports"
    FUNCTION_SIGNATURE_DRIFT = "function_signature_drift"
    VARIABLE_NAMING_COLLISION = "variable_naming_collision"
    CLASS_HIERARCHY_CHANGE = "class_hierarchy_change"
    DEPENDENCY_VERSION_MISMATCH = "dependency_version_mismatch"
    API_BREAKING_CHANGE = "api_breaking_change"
    RESOURCE_CONTENTION = "resource_contention"
    MERGE_CONTEXT_LOSS = "merge_context_loss"


@dataclass
class PredictionResult:
    """Result of a conflict prediction analysis."""

    prediction_id: str
    confidence: PredictionConfidence
    pattern: ConflictPattern
    affected_branches: list[str]
    affected_files: list[str]
    predicted_conflict_type: ConflictType
    predicted_severity: ConflictSeverity
    likelihood_score: float  # 0.0-1.0
    description: str
    prevention_suggestions: list[str] = field(default_factory=list)
    timeline_prediction: datetime | None = None
    affected_agents: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)
    predicted_at: datetime = field(default_factory=datetime.now)


class ConflictVector(NamedTuple):
    """Vector representing potential conflict characteristics."""

    file_overlap_score: float
    change_frequency_score: float
    complexity_score: float
    dependency_coupling_score: float
    semantic_distance_score: float
    temporal_proximity_score: float


class ConflictPredictor:
    """Advanced system for predicting potential conflicts before they occur."""

    def __init__(
        self,
        conflict_engine: ConflictResolutionEngine,
        branch_manager: BranchManager,
        repo_path: str | None = None,
    ) -> None:
        """Initialize the conflict predictor.

        Args:
            conflict_engine: ConflictResolutionEngine for resolution context
            branch_manager: BranchManager for branch operations
            repo_path: Path to git repository

        Returns:
            Description of return value
        """
        self.conflict_engine = conflict_engine
        self.branch_manager = branch_manager
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

        # Initialize semantic analyzer for deep code analysis
        self.semantic_analyzer = SemanticAnalyzer(branch_manager, repo_path)

        # Prediction storage
        self.predictions: dict[str, PredictionResult] = {}
        self.prediction_history: list[PredictionResult] = []

        # Pattern recognition models
        self.pattern_detectors = {
            ConflictPattern.OVERLAPPING_IMPORTS: self._detect_import_conflicts,
            ConflictPattern.FUNCTION_SIGNATURE_DRIFT: self._detect_signature_drift,
            ConflictPattern.VARIABLE_NAMING_COLLISION: self._detect_naming_collisions,
            ConflictPattern.CLASS_HIERARCHY_CHANGE: self._detect_hierarchy_changes,
            ConflictPattern.DEPENDENCY_VERSION_MISMATCH: self._detect_version_conflicts,
            ConflictPattern.API_BREAKING_CHANGE: ConflictPredictor._detect_api_changes,
            ConflictPattern.RESOURCE_CONTENTION: (ConflictPredictor._detect_resource_conflicts),
            ConflictPattern.MERGE_CONTEXT_LOSS: ConflictPredictor._detect_context_loss,
        }

        # Machine learning components (simplified heuristics for now)
        self.historical_patterns: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
        self.conflict_vectors: dict[str, ConflictVector] = {}

        # Configuration
        self.prediction_window = timedelta(days=7)  # Look ahead window
        self.min_confidence_threshold = 0.3
        self.max_predictions_per_run = 50

        # Performance tracking
        self.prediction_stats = {
            "total_predictions": 0,
            "accurate_predictions": 0,
            "false_positives": 0,
            "prevented_conflicts": 0,
            "accuracy_rate": 0.0,
        }

    async def predict_conflicts(
        self,
        branches: list[str],
        time_horizon: timedelta | None = None,
    ) -> list[PredictionResult]:
        """Predict potential conflicts between branches.

        Args:
            branches: List of branch names to analyze
            time_horizon: How far ahead to predict (defaults to prediction_window)

        Returns:
            List of conflict predictions sorted by likelihood
        """
        logger.info("Predicting conflicts for branches: %s", branches)

        time_horizon = time_horizon or self.prediction_window
        predictions = []

        try:
            # Generate conflict vectors for all branch pairs
            for i, branch1 in enumerate(branches):
                for branch2 in branches[i + 1 :]:
                    vector = await self._calculate_conflict_vector(branch1, branch2)
                    self.conflict_vectors[f"{branch1}:{branch2}"] = vector

                    # Run pattern detection
                    for detector in self.pattern_detectors.values():
                        prediction = await detector(branch1, branch2, vector)
                        if prediction and prediction.likelihood_score >= self.min_confidence_threshold:
                            predictions.append(prediction)

            # Apply machine learning scoring
            predictions = await self._apply_ml_scoring(predictions)

            # Sort by likelihood and confidence
            predictions.sort(
                key=lambda p: (p.likelihood_score, p.confidence.value),
                reverse=True,
            )

            # Limit results
            predictions = predictions[: self.max_predictions_per_run]

            # Store predictions
            for prediction in predictions:
                self.predictions[prediction.prediction_id] = prediction
                self.prediction_history.append(prediction)

            self.prediction_stats["total_predictions"] += len(predictions)
            logger.info("Generated %d conflict predictions", len(predictions))

        except Exception:
            logger.exception("Error predicting conflicts:")

        return predictions

    async def _calculate_conflict_vector(
        self,
        branch1: str,
        branch2: str,
    ) -> ConflictVector:
        """Calculate multi-dimensional conflict probability vector."""
        try:
            # File overlap analysis
            files1 = await self.conflict_engine._get_changed_files(branch1)
            files2 = await self.conflict_engine._get_changed_files(branch2)

            common_files = set(files1.keys()) & set(files2.keys())
            file_overlap_score = len(common_files) / max(
                len(files1) + len(files2) - len(common_files),
                1,
            )

            # Change frequency analysis
            freq1 = await self._get_change_frequency(branch1)
            freq2 = await self._get_change_frequency(branch2)
            change_frequency_score = min(freq1 * freq2 / 100, 1.0)  # Normalize

            # Code complexity analysis
            complexity1 = await self._calculate_branch_complexity(branch1)
            complexity2 = await self._calculate_branch_complexity(branch2)
            complexity_score = (complexity1 + complexity2) / 200  # Normalize

            # Dependency coupling analysis
            coupling_score = await self._calculate_dependency_coupling(branch1, branch2)

            # Semantic distance analysis
            semantic_score = await self._calculate_semantic_distance(branch1, branch2)

            # Temporal proximity analysis
            temporal_score = await self._calculate_temporal_proximity(branch1, branch2)

            return ConflictVector(
                file_overlap_score=file_overlap_score,
                change_frequency_score=change_frequency_score,
                complexity_score=complexity_score,
                dependency_coupling_score=coupling_score,
                semantic_distance_score=semantic_score,
                temporal_proximity_score=temporal_score,
            )

        except Exception:
            logger.exception("Error calculating conflict vector:")
            return ConflictVector(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    async def _detect_import_conflicts(
        self,
        branch1: str,
        branch2: str,
        vector: ConflictVector,
    ) -> PredictionResult | None:
        """Detect potential import statement conflicts."""
        try:
            # Get Python files changed in both branches
            files1 = await self._get_python_files_with_imports(branch1)
            files2 = await self._get_python_files_with_imports(branch2)

            common_files = set(files1.keys()) & set(files2.keys())
            if not common_files:
                return None

            conflict_likelihood = 0.0
            affected_files = []

            for file_path in common_files:
                imports1 = files1[file_path]
                imports2 = files2[file_path]

                if self._imports_likely_to_conflict(imports1, imports2):
                    affected_files.append(file_path)
                    conflict_likelihood += 0.2

            if not affected_files:
                return None

            # Adjust likelihood based on vector components
            conflict_likelihood += vector.file_overlap_score * 0.3
            conflict_likelihood += vector.change_frequency_score * 0.2
            conflict_likelihood = min(conflict_likelihood, 1.0)

            confidence = self._likelihood_to_confidence(conflict_likelihood)

            return PredictionResult(
                prediction_id=f"import_conflict_{branch1}_{branch2}_{len(affected_files)}",
                confidence=confidence,
                pattern=ConflictPattern.OVERLAPPING_IMPORTS,
                affected_branches=[branch1, branch2],
                affected_files=affected_files,
                predicted_conflict_type=ConflictType.MERGE_CONFLICT,
                predicted_severity=ConflictSeverity.LOW,
                likelihood_score=conflict_likelihood,
                description=f"Import conflicts predicted in {len(affected_files)} files between {branch1} and {branch2}",
                prevention_suggestions=[
                    "Use consistent import ordering across branches",
                    "Coordinate import additions through team communication",
                    "Consider using automated import sorting tools",
                ],
                timeline_prediction=datetime.now(UTC) + timedelta(days=2),
                metadata={
                    "import_overlap_count": len(affected_files),
                    "vector_components": vector._asdict(),
                },
            )

        except Exception:
            logger.exception("Error detecting import conflicts:")
            return None

    async def _detect_signature_drift(
        self,
        branch1: str,
        branch2: str,
        vector: ConflictVector,
    ) -> PredictionResult | None:
        """Detect potential function signature conflicts."""
        try:
            # Get function signatures from both branches
            functions1 = await self._get_all_function_signatures(branch1)
            functions2 = await self._get_all_function_signatures(branch2)

            common_functions = set(functions1.keys()) & set(functions2.keys())
            if not common_functions:
                return None

            drift_score = 0.0
            affected_functions = []

            for func_name in common_functions:
                sig1 = functions1[func_name]
                sig2 = functions2[func_name]

                if sig1 != sig2:
                    # Calculate signature similarity
                    similarity = difflib.SequenceMatcher(None, sig1, sig2).ratio()
                    if similarity < SIMILARITY_THRESHOLD_HIGH:  # Significant difference
                        affected_functions.append(func_name)
                        drift_score += 1.0 - similarity

            if not affected_functions:
                return None

            drift_score /= len(common_functions)  # Normalize
            drift_score += vector.semantic_distance_score * 0.3
            drift_score = min(drift_score, 1.0)

            confidence = self._likelihood_to_confidence(drift_score)
            severity = ConflictSeverity.HIGH if len(affected_functions) > HIGH_OVERLAP_THRESHOLD else ConflictSeverity.MEDIUM

            return PredictionResult(
                prediction_id=f"signature_drift_{branch1}_{branch2}_{len(affected_functions)}",
                confidence=confidence,
                pattern=ConflictPattern.FUNCTION_SIGNATURE_DRIFT,
                affected_branches=[branch1, branch2],
                affected_files=list(
                    {f.split(":")[0] for f in affected_functions if ":" in f},
                ),
                predicted_conflict_type=ConflictType.SEMANTIC,
                predicted_severity=severity,
                likelihood_score=drift_score,
                description=f"Function signature drift detected in {len(affected_functions)} functions",
                prevention_suggestions=[
                    "Coordinate API changes through design reviews",
                    "Use versioned APIs during development",
                    "Implement automated signature compatibility checks",
                ],
                timeline_prediction=datetime.now(UTC) + timedelta(days=1),
                metadata={
                    "affected_functions": affected_functions[:10],  # Limit for storage
                    "drift_severity": severity.value,
                },
            )

        except Exception:
            logger.exception("Error detecting signature drift:")
            return None

    async def _detect_naming_collisions(
        self,
        branch1: str,
        branch2: str,
        vector: ConflictVector,
    ) -> PredictionResult | None:
        """Detect potential variable/class naming collisions."""
        try:
            # Get symbol definitions from both branches
            symbols1 = await self._extract_symbol_definitions(branch1)
            symbols2 = await self._extract_symbol_definitions(branch2)

            # Find potential naming collisions
            collision_likelihood = 0.0
            potential_collisions = []

            for symbol_name in symbols1:
                if symbol_name in symbols2:
                    # Check if definitions are different
                    if symbols1[symbol_name] != symbols2[symbol_name]:
                        potential_collisions.append(symbol_name)
                        collision_likelihood += 0.1

            if not potential_collisions:
                return None

            collision_likelihood += vector.complexity_score * 0.2
            collision_likelihood = min(collision_likelihood, 1.0)

            confidence = self._likelihood_to_confidence(collision_likelihood)

            return PredictionResult(
                prediction_id=f"naming_collision_{branch1}_{branch2}_{len(potential_collisions)}",
                confidence=confidence,
                pattern=ConflictPattern.VARIABLE_NAMING_COLLISION,
                affected_branches=[branch1, branch2],
                affected_files=[],  # Will be populated with actual file analysis
                predicted_conflict_type=ConflictType.SEMANTIC,
                predicted_severity=ConflictSeverity.MEDIUM,
                likelihood_score=collision_likelihood,
                description=f"Naming collisions predicted for {len(potential_collisions)} symbols",
                prevention_suggestions=[
                    "Use consistent naming conventions across teams",
                    "Implement namespace prefixing for new symbols",
                    "Review symbol visibility and scope design",
                ],
                timeline_prediction=datetime.now(UTC) + timedelta(days=3),
                metadata={"collision_symbols": potential_collisions[:20]},
            )

        except Exception:
            logger.exception("Error detecting naming collisions:")
            return None

    async def _detect_hierarchy_changes(
        self,
        branch1: str,
        branch2: str,
        vector: ConflictVector,
    ) -> PredictionResult | None:
        """Detect potential class hierarchy conflicts."""
        try:
            # Get class hierarchies from both branches
            hierarchies1 = await self._extract_class_hierarchies(branch1)
            hierarchies2 = await self._extract_class_hierarchies(branch2)

            common_classes = set(hierarchies1.keys()) & set(hierarchies2.keys())
            if not common_classes:
                return None

            hierarchy_conflicts = []
            conflict_score = 0.0

            for class_name in common_classes:
                hier1 = hierarchies1[class_name]
                hier2 = hierarchies2[class_name]

                if hier1 != hier2:
                    hierarchy_conflicts.append(class_name)
                    # Weight conflicts by hierarchy depth
                    depth_impact = max(len(hier1), len(hier2)) / 10
                    conflict_score += 0.2 + depth_impact

            if not hierarchy_conflicts:
                return None

            conflict_score = min(conflict_score, 1.0)
            confidence = self._likelihood_to_confidence(conflict_score)

            return PredictionResult(
                prediction_id=f"hierarchy_conflict_{branch1}_{branch2}_{len(hierarchy_conflicts)}",
                confidence=confidence,
                pattern=ConflictPattern.CLASS_HIERARCHY_CHANGE,
                affected_branches=[branch1, branch2],
                affected_files=[],
                predicted_conflict_type=ConflictType.SEMANTIC,
                predicted_severity=ConflictSeverity.HIGH,
                likelihood_score=conflict_score,
                description=f"Class hierarchy conflicts predicted for {len(hierarchy_conflicts)} classes",
                prevention_suggestions=[
                    "Coordinate inheritance changes through architecture reviews",
                    "Use composition over inheritance where possible",
                    "Implement automated hierarchy compatibility tests",
                ],
                timeline_prediction=datetime.now(UTC) + timedelta(days=1),
                metadata={"affected_classes": hierarchy_conflicts},
            )

        except Exception:
            logger.exception("Error detecting hierarchy changes:")
            return None

    async def _detect_version_conflicts(
        self,
        branch1: str,
        branch2: str,
        vector: ConflictVector,
    ) -> PredictionResult | None:
        """Detect potential dependency version conflicts."""
        try:
            # Get dependency versions from both branches
            deps1 = await self._get_dependency_versions(branch1)
            deps2 = await self._get_dependency_versions(branch2)

            common_deps = set(deps1.keys()) & set(deps2.keys())
            if not common_deps:
                return None

            version_conflicts = []
            conflict_score = 0.0

            for dep_name in common_deps:
                ver1 = deps1[dep_name]
                ver2 = deps2[dep_name]

                if ver1 != ver2:
                    version_conflicts.append((dep_name, ver1, ver2))
                    # Weight by version distance
                    version_distance = self._calculate_version_distance(ver1, ver2)
                    conflict_score += version_distance

            if not version_conflicts:
                return None

            conflict_score /= len(common_deps)  # Normalize
            confidence = self._likelihood_to_confidence(conflict_score)

            return PredictionResult(
                prediction_id=f"version_conflict_{branch1}_{branch2}_{len(version_conflicts)}",
                confidence=confidence,
                pattern=ConflictPattern.DEPENDENCY_VERSION_MISMATCH,
                affected_branches=[branch1, branch2],
                affected_files=["requirements.txt", "pyproject.toml", "setup.py"],
                predicted_conflict_type=ConflictType.DEPENDENCY,
                predicted_severity=ConflictSeverity.MEDIUM,
                likelihood_score=conflict_score,
                description=f"Dependency version conflicts predicted for {len(version_conflicts)} packages",
                prevention_suggestions=[
                    "Use dependency pinning strategies",
                    "Coordinate major version upgrades",
                    "Implement automated dependency compatibility testing",
                ],
                timeline_prediction=datetime.now(UTC) + timedelta(hours=12),
                metadata={"version_conflicts": version_conflicts},
            )

        except Exception:
            logger.exception("Error detecting version conflicts:")
            return None

    @staticmethod
    async def _detect_api_changes(
        branch1: str,
        branch2: str,
        vector: ConflictVector,
    ) -> PredictionResult | None:
        """Detect potential API breaking changes."""
        # Implementation would analyze public API changes
        # This is a simplified version
        return None

    @staticmethod
    async def _detect_resource_conflicts(
        branch1: str,
        branch2: str,
        vector: ConflictVector,
    ) -> PredictionResult | None:
        """Detect potential resource contention conflicts."""
        # Implementation would analyze file locks, database access, etc.
        return None

    @staticmethod
    async def _detect_context_loss(
        branch1: str,
        branch2: str,
        vector: ConflictVector,
    ) -> PredictionResult | None:
        """Detect potential merge context loss scenarios."""
        # Implementation would analyze merge complexity
        return None

    async def _apply_ml_scoring(
        self,
        predictions: list[PredictionResult],
    ) -> list[PredictionResult]:
        """Apply machine learning scoring to improve prediction accuracy."""
        # This would implement actual ML scoring
        # For now, apply simple heuristics

        for prediction in predictions:
            # Adjust confidence based on historical accuracy
            pattern_history = self.historical_patterns.get(prediction.pattern.value, [])
            if pattern_history:
                avg_accuracy = sum(bool(p.get("accurate", 0)) for p in pattern_history) / len(
                    pattern_history,
                )
                prediction.likelihood_score *= 0.5 + avg_accuracy * 0.5
                prediction.confidence = self._likelihood_to_confidence(
                    prediction.likelihood_score,
                )

        return predictions

    @staticmethod
    def _likelihood_to_confidence(likelihood: float) -> PredictionConfidence:
        """Convert likelihood score to confidence enum."""
        if likelihood >= CONFIDENCE_CRITICAL_THRESHOLD:
            return PredictionConfidence.CRITICAL
        if likelihood >= CONFIDENCE_HIGH_THRESHOLD:
            return PredictionConfidence.HIGH
        if likelihood >= CONFIDENCE_MEDIUM_THRESHOLD:
            return PredictionConfidence.MEDIUM
        return PredictionConfidence.LOW

    # Helper methods for analysis

    async def _get_change_frequency(self, branch: str) -> float:
        """Get change frequency for a branch (commits per day)."""
        try:
            result = await self.conflict_engine._run_git_command(
                ["rev-list", "--count", "--since=1 week ago", branch],
            )
            commit_count = int(result.stdout.strip())
            return commit_count / 7.0  # commits per day
        except Exception:
            return 0.0

    async def _calculate_branch_complexity(self, branch: str) -> float:
        """Calculate complexity score for a branch."""
        try:
            # Simple complexity metric based on lines changed
            result = await self.conflict_engine._run_git_command(
                ["diff", "--stat", f"HEAD..{branch}"],
            )

            lines_changed = 0
            for line in result.stdout.split("\n"):
                if "+" in line and "-" in line:
                    # Parse insertion/deletion counts
                    parts = line.strip().split()
                    if len(parts) >= MIN_PARTS_FOR_PARSING:
                        try:
                            additions = int(parts[-2])
                            deletions = int(parts[-1])
                            lines_changed += additions + deletions
                        except ValueError:
                            continue

            return min(lines_changed / 10, 100)  # Normalize to 0-100
        except Exception:
            return 0.0

    @staticmethod
    async def _calculate_dependency_coupling(branch1: str, branch2: str) -> float:
        """Calculate dependency coupling between branches."""
        # Simplified implementation
        return 0.5

    @staticmethod
    async def _calculate_semantic_distance(branch1: str, branch2: str) -> float:
        """Calculate semantic distance between branches."""
        # Simplified implementation
        return 0.5

    @staticmethod
    async def _calculate_temporal_proximity(branch1: str, branch2: str) -> float:
        """Calculate temporal proximity of changes."""
        # Simplified implementation
        return 0.5

    async def _get_python_files_with_imports(self, branch: str) -> dict[str, list[str]]:
        """Get Python files and their import statements."""
        files = {}
        try:
            python_files = await self.conflict_engine._get_python_files_changed(branch)
            for file_path in python_files:
                content = await self.conflict_engine._get_file_content(
                    file_path,
                    branch,
                )
                if content:
                    imports = self._extract_imports(content)
                    files[file_path] = imports
        except Exception:
            logger.exception("Error getting Python files with imports:")
        return files

    @staticmethod
    def _extract_imports(content: str) -> list[str]:
        """Extract import statements from Python code."""
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
        except SyntaxError:
            # Fallback to regex for invalid syntax
            import_patterns = [
                r"^import\s+[\w\.]+",
                r"^from\s+[\w\.]+\s+import\s+[\w\.,\s]+",
            ]
            for raw_line in content.split("\n"):
                line = raw_line.strip()
                for pattern in import_patterns:
                    if re.match(pattern, line):
                        imports.append(line)
                        break
        return imports

    @staticmethod
    def _imports_likely_to_conflict(
        imports1: list[str],
        imports2: list[str],
    ) -> bool:
        """Check if import lists are likely to conflict."""
        set1 = set(imports1)
        set2 = set(imports2)

        overlap = set1 & set2
        different = (set1 - set2) | (set2 - set1)

        # Heuristic: high overlap + significant differences = likely conflict
        if len(overlap) > HIGH_OVERLAP_THRESHOLD and len(different) > SIGNIFICANT_DIFFERENCES_THRESHOLD:
            return True

        for imp1 in imports1:
            for imp2 in imports2:
                if imp1 != imp2 and difflib.SequenceMatcher(None, imp1, imp2).ratio() > SIMILARITY_THRESHOLD_MEDIUM:
                    return True

        return False

    async def _get_all_function_signatures(self, branch: str) -> dict[str, str]:
        """Get all function signatures from a branch."""
        signatures = {}
        try:
            python_files = await self.conflict_engine._get_python_files_changed(branch)
            for file_path in python_files:
                content = await self.conflict_engine._get_file_content(
                    file_path,
                    branch,
                )
                if content:
                    file_sigs = self.conflict_engine._extract_function_signatures(
                        content,
                    )
                    for func_name, signature in file_sigs.items():
                        signatures[f"{file_path}:{func_name}"] = signature
        except Exception:
            logger.exception("Error getting function signatures:")
        return signatures

    async def _extract_symbol_definitions(self, branch: str) -> dict[str, str]:
        """Extract symbol definitions from a branch."""
        symbols = {}
        try:
            python_files = await self.conflict_engine._get_python_files_changed(branch)
            for file_path in python_files:
                content = await self.conflict_engine._get_file_content(
                    file_path,
                    branch,
                )
                if content:
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(
                                node,
                                ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
                            ):
                                symbols[node.name] = f"{file_path}:{node.lineno}"
                    except SyntaxError:
                        pass
        except Exception:
            logger.exception("Error extracting symbol definitions:")
        return symbols

    async def _extract_class_hierarchies(self, branch: str) -> dict[str, list[str]]:
        """Extract class inheritance hierarchies."""
        hierarchies = {}
        try:
            python_files = await self.conflict_engine._get_python_files_changed(branch)
            for file_path in python_files:
                content = await self.conflict_engine._get_file_content(
                    file_path,
                    branch,
                )
                if content:
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                bases = []
                                for base in node.bases:
                                    if isinstance(base, ast.Name):
                                        bases.append(base.id)
                                    elif isinstance(base, ast.Attribute):
                                        bases.append(ast.unparse(base))
                                hierarchies[node.name] = bases
                    except SyntaxError:
                        pass
        except Exception:
            logger.exception("Error extracting class hierarchies:")
        return hierarchies

    async def _get_dependency_versions(self, branch: str) -> dict[str, str]:
        """Get dependency versions from requirements files."""
        versions = {}
        try:
            # Check requirements.txt
            req_content = await self.conflict_engine._get_file_content(
                "requirements.txt",
                branch,
            )
            if req_content:
                for raw_line in req_content.split("\n"):
                    line = raw_line.strip()
                    if line and not line.startswith("#") and "==" in line:
                        pkg, ver = line.split("==", 1)
                        versions[pkg.strip()] = ver.strip()

            # Check pyproject.toml
            pyproject_content = await self.conflict_engine._get_file_content(
                "pyproject.toml",
                branch,
            )
            if pyproject_content:
                # Simple parsing for dependencies
                lines = pyproject_content.split("\n")
                in_dependencies = False
                for raw_line in lines:
                    line = raw_line.strip()
                    if line == "[dependencies]" or "dependencies = [" in line:
                        in_dependencies = True
                    elif line.startswith("[") and in_dependencies:
                        in_dependencies = False
                    elif in_dependencies and "=" in line and '"' in line:
                        # Parse "package>=version" format
                        parts = line.split("=", 1)
                        if len(parts) == MIN_PARTS_FOR_PARSING:
                            pkg = parts[0].strip().strip("\"'")
                            ver = parts[1].strip().strip("\"'")
                            versions[pkg] = ver

        except Exception:
            logger.exception("Error getting dependency versions:")
        return versions

    @staticmethod
    def _calculate_version_distance(ver1: str, ver2: str) -> float:
        """Calculate semantic distance between version strings."""
        try:
            # Simple version comparison
            def parse_version(v: str) -> list[int]:
                return [int(x) for x in v.split(".") if x.isdigit()]

            v1_parts = parse_version(ver1)
            v2_parts = parse_version(ver2)

            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            distance = 0.0
            weight = 1.0
            for a, b in zip(v1_parts, v2_parts, strict=False):
                distance += abs(a - b) * weight
                weight *= 0.1  # Major versions matter more

            return min(distance / 10, 1.0)  # Normalize
        except Exception:
            return 0.5  # Default moderate distance

    def get_prediction_summary(self) -> dict[str, object]:
        """Get summary of all predictions and statistics."""
        if not self.predictions:
            return {
                "total_predictions": 0,
                "by_confidence": {},
                "by_pattern": {},
                "accuracy_metrics": self.prediction_stats.copy(),
            }

        confidence_counts = Counter(p.confidence.value for p in self.predictions.values())
        pattern_counts = Counter(p.pattern.value for p in self.predictions.values())

        return {
            "total_predictions": len(self.predictions),
            "active_predictions": len(
                [p for p in self.predictions.values() if p.timeline_prediction and p.timeline_prediction > datetime.now(UTC)],
            ),
            "by_confidence": dict(confidence_counts),
            "by_pattern": dict(pattern_counts),
            "accuracy_metrics": self.prediction_stats.copy(),
            "most_likely_conflicts": [
                {
                    "prediction_id": p.prediction_id,
                    "likelihood": p.likelihood_score,
                    "pattern": p.pattern.value,
                    "description": p.description,
                }
                for p in sorted(
                    self.predictions.values(),
                    key=lambda x: x.likelihood_score,
                    reverse=True,
                )[:5]
            ],
        }

    @staticmethod
    def validate_prediction_accuracy(actual_conflicts: list[ConflictInfo]) -> None:
        """Validate prediction accuracy against actual conflicts."""
        # Implementation would compare predictions with actual conflicts
        # and update accuracy metrics

    def analyze_conflict_patterns(self) -> dict[str, object]:
        """Analyze detailed conflict patterns and trends."""
        if not self.predictions:
            return {
                "frequent_conflict_files": [],
                "conflict_hotspots": [],
                "pattern_distribution": {},
                "temporal_trends": {},
            }

        # Analyze frequent conflict files
        file_conflicts: Counter[str] = Counter()
        for prediction in self.predictions.values():
            for file_path in prediction.affected_files:
                file_conflicts[file_path] += 1

        frequent_files = [{"file": file_path, "conflict_count": count} for file_path, count in file_conflicts.most_common(10)]

        # Analyze conflict hotspots
        branch_conflicts: Counter[str] = Counter()
        for prediction in self.predictions.values():
            for branch in prediction.affected_branches:
                branch_conflicts[branch] += int(prediction.likelihood_score * 10)  # Scale to avoid losing precision

        hotspots = [
            {
                "location": branch,
                "severity": ("high" if score > HIGH_SCORE_THRESHOLD else "medium" if score > MEDIUM_SCORE_THRESHOLD else "low"),
                "score": score,
            }
            for branch, score in branch_conflicts.most_common(5)
        ]

        # Pattern distribution
        pattern_dist = Counter(p.pattern.value for p in self.predictions.values())

        # Temporal trends (predictions by day)
        temporal_trends: defaultdict[str, int] = defaultdict(int)
        for prediction in self.predictions.values():
            day_key = prediction.predicted_at.strftime("%Y-%m-%d")
            temporal_trends[day_key] += 1

        return {
            "frequent_conflict_files": frequent_files,
            "conflict_hotspots": hotspots,
            "pattern_distribution": dict(pattern_dist),
            "temporal_trends": dict(temporal_trends),
            "total_predictions": len(self.predictions),
            "average_confidence": (sum(p.likelihood_score for p in self.predictions.values()) / max(len(self.predictions), 1)),
        }
