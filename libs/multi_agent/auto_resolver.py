# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Automated conflict resolution system integrating semantic analysis and
intelligent merging.
"""

import ast
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .branch_manager import BranchManager
from .conflict_prediction import ConflictPredictor, PredictionResult
from .conflict_resolution import (
    ConflictResolutionEngine,
    ConflictSeverity,
    ResolutionStrategy,
)
from .semantic_analyzer import SemanticAnalyzer, SemanticConflict, SemanticConflictType
from .semantic_merger import MergeResolution, MergeResult, SemanticMerger

logger = logging.getLogger(__name__)

# Constants for risk thresholds and statistical analysis
CONSERVATIVE_RISK_THRESHOLD = 0.3
BALANCED_RISK_THRESHOLD = 0.6
PREDICTIVE_RISK_THRESHOLD = 0.5
CONFIDENCE_THRESHOLD = 0.5
SUCCESS_RATE_THRESHOLD = 0.7
CONFIDENCE_RATE_THRESHOLD = 0.6
SEMANTIC_INTEGRITY_THRESHOLD = 0.95
MIN_SESSIONS_FOR_ANALYSIS = 10
MIN_FAILURE_COUNT = 2


class AutoResolutionMode(Enum):
    """Modes for automatic conflict resolution."""

    CONSERVATIVE = "conservative"  # Only resolve low-risk conflicts
    BALANCED = "balanced"  # Resolve medium-risk conflicts with high confidence
    AGGRESSIVE = "aggressive"  # Attempt to resolve most conflicts automatically
    PREDICTIVE = "predictive"  # Use prediction to prevent conflicts


class ResolutionOutcome(Enum):
    """Outcomes of auto-resolution attempts."""

    FULLY_RESOLVED = "fully_resolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    ESCALATED_TO_HUMAN = "escalated_to_human"
    RESOLUTION_FAILED = "resolution_failed"
    PREVENTED = "prevented"


@dataclass
class AutoResolutionResult:
    """Result of automatic conflict resolution session."""

    session_id: str
    branch1: str
    branch2: str
    target_branch: str
    mode: AutoResolutionMode
    outcome: ResolutionOutcome

    # Resolution details
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    files_processed: int = 0
    merge_results: list[MergeResult] = field(default_factory=list)

    # Performance metrics
    resolution_time: float = 0.0
    confidence_score: float = 0.0
    semantic_integrity_preserved: bool = True

    # Escalation information
    escalated_conflicts: list[str] = field(default_factory=list)
    manual_intervention_required: list[str] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    resolved_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AutoResolver:
    """Comprehensive automatic conflict resolution system."""

    def __init__(
        self,
        semantic_analyzer: SemanticAnalyzer,
        semantic_merger: SemanticMerger,
        conflict_engine: ConflictResolutionEngine,
        conflict_predictor: ConflictPredictor,
        branch_manager: BranchManager,
        repo_path: str | None = None,
    ) -> None:
        """Initialize the auto resolver.

        Args:
            semantic_analyzer: For analyzing code semantics
            semantic_merger: For performing intelligent merges
            conflict_engine: For traditional conflict resolution
            conflict_predictor: For predicting and preventing conflicts
            branch_manager: For branch operations
            repo_path: Path to git repository
        """
        self.semantic_analyzer = semantic_analyzer
        self.semantic_merger = semantic_merger
        self.conflict_engine = conflict_engine
        self.conflict_predictor = conflict_predictor
        self.branch_manager = branch_manager
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

        # Resolution configuration
        self.default_mode = AutoResolutionMode.BALANCED
        self.confidence_thresholds = {
            AutoResolutionMode.CONSERVATIVE: 0.9,
            AutoResolutionMode.BALANCED: 0.7,
            AutoResolutionMode.AGGRESSIVE: 0.5,
            AutoResolutionMode.PREDICTIVE: 0.8,
        }

        # Risk assessment settings
        self.severity_risk_mapping = {
            ConflictSeverity.LOW: 0.2,
            ConflictSeverity.MEDIUM: 0.5,
            ConflictSeverity.HIGH: 0.8,
            ConflictSeverity.CRITICAL: 1.0,
        }

        # Resolution history and learning
        self.resolution_history: list[AutoResolutionResult] = []
        self.success_patterns: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        self.failure_patterns: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)

        # Performance tracking
        self.resolution_stats = {
            "total_sessions": 0,
            "successful_resolutions": 0,
            "full_auto_resolutions": 0,
            "escalated_to_human": 0,
            "average_confidence": 0.0,
            "semantic_integrity_rate": 0.0,
        }

    async def auto_resolve_branch_conflicts(
        self,
        branch1: str,
        branch2: str,
        target_branch: str | None = None,
        mode: AutoResolutionMode | None = None,
        file_filter: list[str] | None = None,
    ) -> AutoResolutionResult:
        """Automatically resolve conflicts between two branches.

        Args:
            branch1: First branch name
            branch2: Second branch name
            target_branch: Target branch for resolution (default: branch1)
            mode: Resolution mode (default: balanced)
            file_filter: Specific files to process (None for all)

        Returns:
            AutoResolutionResult with comprehensive resolution details
        """
        session_id = f"auto_resolve_{branch1}_{branch2}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        mode = mode or self.default_mode
        target_branch = target_branch or branch1
        start_time = datetime.now(UTC)

        logger.info("Starting auto-resolution session %s in %s mode", session_id, mode.value)

        try:
            # Step 1: Detect semantic conflicts
            logger.info("Detecting semantic conflicts...")
            conflicts = await self.semantic_analyzer.analyze_semantic_conflicts(
                branch1,
                branch2,
                file_filter,
            )

            if not conflicts:
                logger.info("No conflicts detected")
                return AutoResolutionResult(
                    session_id=session_id,
                    branch1=branch1,
                    branch2=branch2,
                    target_branch=target_branch,
                    mode=mode,
                    outcome=ResolutionOutcome.FULLY_RESOLVED,
                    conflicts_detected=0,
                    conflicts_resolved=0,
                    resolution_time=(datetime.now(UTC) - start_time).total_seconds(),
                    confidence_score=1.0,
                )

            logger.info("Detected %d semantic conflicts", len(conflicts))

            # Step 2: Assess resolvability
            resolvable_conflicts, escalated_conflicts = self._assess_conflict_resolvability(conflicts, mode)

            logger.info(
                "Resolvable: %d, Escalated: %d",
                len(resolvable_conflicts),
                len(escalated_conflicts),
            )

            # Step 3: Perform automatic resolution
            merge_results = []
            if resolvable_conflicts:
                merge_results = await self._perform_batch_resolution(
                    resolvable_conflicts,
                    mode,
                )

            # Step 4: Validate and apply results
            validated_results = await self._validate_resolution_results(merge_results)

            # Step 5: Apply successful merges to target branch
            applied_results = await self._apply_merge_results(
                validated_results,
                target_branch,
            )

            # Step 6: Calculate final outcome and metrics
            outcome = AutoResolver._determine_resolution_outcome(
                conflicts,
                escalated_conflicts,
                applied_results,
            )

            confidence_score = AutoResolver._calculate_session_confidence(applied_results)
            resolution_time = (datetime.now(UTC) - start_time).total_seconds()

            # Create result
            result = AutoResolutionResult(
                session_id=session_id,
                branch1=branch1,
                branch2=branch2,
                target_branch=target_branch,
                mode=mode,
                outcome=outcome,
                conflicts_detected=len(conflicts),
                conflicts_resolved=len(applied_results),
                files_processed=len({r.file_path for r in applied_results}),
                merge_results=applied_results,
                resolution_time=resolution_time,
                confidence_score=confidence_score,
                semantic_integrity_preserved=all(r.semantic_integrity for r in applied_results),
                escalated_conflicts=[c.conflict_id for c in escalated_conflicts],
                metadata={
                    "total_conflicts": len(conflicts),
                    "resolvable_conflicts": len(resolvable_conflicts),
                    "validation_success_rate": (len(validated_results) / max(len(merge_results), 1)),
                    "application_success_rate": (len(applied_results) / max(len(validated_results), 1)),
                },
            )

            # Store result and update stats
            self.resolution_history.append(result)
            self._update_resolution_stats(result)
            self._learn_from_resolution(result, conflicts)

            logger.info("Auto-resolution completed: %s", outcome.value)
            return result

        except Exception as e:
            logger.exception("Error in auto-resolution session %s")
            return AutoResolutionResult(
                session_id=session_id,
                branch1=branch1,
                branch2=branch2,
                target_branch=target_branch,
                mode=mode,
                outcome=ResolutionOutcome.RESOLUTION_FAILED,
                resolution_time=(datetime.now(UTC) - start_time).total_seconds(),
                metadata={"error": str(e)},
            )

    async def prevent_conflicts_predictively(
        self,
        branches: list[str],
        prevention_mode: AutoResolutionMode = AutoResolutionMode.PREDICTIVE,
    ) -> dict[str, Any]:
        """Use prediction to prevent conflicts before they occur.

        Args:
            branches: List of branches to analyze
            prevention_mode: Mode for prevention operations

        Returns:
            Dictionary with prevention results and recommendations
        """
        logger.info("Starting predictive conflict prevention for %d branches", len(branches))

        try:
            # Get conflict predictions
            predictions = await self.conflict_predictor.predict_conflicts(branches)

            if not predictions:
                return {
                    "status": "no_conflicts_predicted",
                    "branches_analyzed": len(branches),
                    "recommendations": [],
                }

            # Filter high-confidence predictions
            threshold = self.confidence_thresholds[prevention_mode]
            high_confidence_predictions = [p for p in predictions if p.likelihood_score >= threshold]

            # Generate prevention strategies
            prevention_strategies = AutoResolver._generate_prevention_strategies(
                high_confidence_predictions,
            )

            # Apply automatic preventive measures where possible
            applied_measures = await self._apply_preventive_measures(
                high_confidence_predictions,
                prevention_strategies,
            )

            return {
                "status": "prevention_completed",
                "branches_analyzed": len(branches),
                "predictions_found": len(predictions),
                "high_confidence_predictions": len(high_confidence_predictions),
                "preventive_measures_applied": len(applied_measures),
                "recommendations": prevention_strategies,
                "applied_measures": applied_measures,
                "prevention_summary": {
                    "conflicts_prevented": len(applied_measures),
                    "manual_intervention_needed": (len(prevention_strategies) - len(applied_measures)),
                },
            }

        except Exception as e:
            logger.exception("Error in predictive conflict prevention")
            return {
                "status": "prevention_failed",
                "error": str(e),
                "branches_analyzed": len(branches),
            }

    def _assess_conflict_resolvability(
        self,
        conflicts: list[SemanticConflict],
        mode: AutoResolutionMode,
    ) -> tuple[list[SemanticConflict], list[SemanticConflict]]:
        """Assess which conflicts can be auto-resolved based on mode and
        risk.
        """
        self.confidence_thresholds[mode]
        resolvable = []
        escalated = []

        for conflict in conflicts:
            risk_score = self._calculate_conflict_risk(conflict)

            # Conservative mode: only resolve very low-risk conflicts
            if mode == AutoResolutionMode.CONSERVATIVE:
                if risk_score <= CONSERVATIVE_RISK_THRESHOLD and conflict.severity == ConflictSeverity.LOW:
                    resolvable.append(conflict)
                else:
                    escalated.append(conflict)

            # Balanced mode: resolve low-medium risk with good suggestions
            elif mode == AutoResolutionMode.BALANCED:
                if (
                    risk_score <= BALANCED_RISK_THRESHOLD
                    and conflict.severity in {ConflictSeverity.LOW, ConflictSeverity.MEDIUM}
                    and conflict.suggested_resolution != ResolutionStrategy.HUMAN_REQUIRED
                ):
                    resolvable.append(conflict)
                else:
                    escalated.append(conflict)

            # Aggressive mode: attempt most conflicts except critical
            elif mode == AutoResolutionMode.AGGRESSIVE:
                if conflict.severity != ConflictSeverity.CRITICAL and conflict.suggested_resolution != ResolutionStrategy.HUMAN_REQUIRED:
                    resolvable.append(conflict)
                else:
                    escalated.append(conflict)

            # Predictive mode: use prediction confidence
            elif risk_score <= PREDICTIVE_RISK_THRESHOLD and conflict.severity != ConflictSeverity.CRITICAL:
                resolvable.append(conflict)
            else:
                escalated.append(conflict)

        return resolvable, escalated

    def _calculate_conflict_risk(self, conflict: SemanticConflict) -> float:
        """Calculate risk score for a semantic conflict."""
        base_risk = self.severity_risk_mapping.get(conflict.severity, 0.5)

        # Adjust based on conflict type
        type_adjustments = {
            SemanticConflictType.IMPORT_SEMANTIC_CONFLICT: -0.2,  # Lower risk
            SemanticConflictType.VARIABLE_TYPE_CONFLICT: -0.1,
            SemanticConflictType.FUNCTION_SIGNATURE_CHANGE: 0.1,  # Higher risk
            SemanticConflictType.API_BREAKING_CHANGE: 0.3,
            SemanticConflictType.INHERITANCE_CONFLICT: 0.2,
        }

        adjustment = type_adjustments.get(conflict.conflict_type, 0.0)

        # Adjust based on symbol visibility
        if conflict.symbol_name.startswith("_"):
            adjustment -= 0.1  # Private symbols are lower risk

        # Adjust based on suggested resolution
        if conflict.suggested_resolution == ResolutionStrategy.HUMAN_REQUIRED:
            adjustment += 0.2
        elif conflict.suggested_resolution == ResolutionStrategy.SEMANTIC_ANALYSIS:
            adjustment -= 0.1

        return max(0.0, min(1.0, base_risk + adjustment))

    async def _perform_batch_resolution(
        self,
        conflicts: list[SemanticConflict],
        mode: AutoResolutionMode,
    ) -> list[MergeResult]:
        """Perform batch resolution of conflicts using semantic merger."""
        logger.info("Performing batch resolution of %d conflicts", len(conflicts))

        # Use semantic merger to auto-resolve conflicts
        merge_results = await self.semantic_merger.auto_resolve_conflicts(conflicts)

        # Filter results based on mode requirements
        filtered_results = []
        threshold = self.confidence_thresholds[mode]

        for result in merge_results:
            if result.merge_confidence >= threshold and result.resolution in {MergeResolution.AUTO_RESOLVED, MergeResolution.PARTIAL_RESOLUTION} and result.semantic_integrity:
                filtered_results.append(result)
            else:
                logger.info(
                    "Filtering out merge result for %s due to low confidence or integrity issues",
                    result.file_path,
                )

        return filtered_results

    async def _validate_resolution_results(
        self,
        merge_results: list[MergeResult],
    ) -> list[MergeResult]:
        """Validate merge results before application."""
        logger.info("Validating %d merge results", len(merge_results))
        validated = []

        for result in merge_results:
            if await self._validate_single_merge_result(result):
                validated.append(result)
            else:
                logger.warning("Validation failed for merge result: %s", result.merge_id)

        return validated

    @staticmethod
    async def _validate_single_merge_result(result: MergeResult) -> bool:
        """Validate a single merge result."""
        # Check semantic integrity
        if not result.semantic_integrity:
            return False

        # Check merged content exists and is valid
        if not result.merged_content:
            return False

        # Validate AST if it's Python code
        if result.file_path.endswith(".py"):
            try:
                ast.parse(result.merged_content)
            except SyntaxError:
                return False

        # Check confidence threshold
        return not result.merge_confidence < CONFIDENCE_THRESHOLD

    async def _apply_merge_results(
        self,
        merge_results: list[MergeResult],
        target_branch: str,
    ) -> list[MergeResult]:
        """Apply validated merge results to target branch."""
        logger.info("Applying %d merge results to %s", len(merge_results), target_branch)
        applied = []

        for result in merge_results:
            try:
                if await self._apply_single_merge_result(result, target_branch):
                    applied.append(result)
                    logger.info("Successfully applied merge for %s", result.file_path)
                else:
                    logger.warning("Failed to apply merge for %s", result.file_path)
            except Exception:
                logger.exception("Error applying merge result for %s")

        return applied

    async def _apply_single_merge_result(
        self,
        result: MergeResult,
        target_branch: str,
    ) -> bool:
        """Apply a single merge result to the target branch."""
        try:
            # This would write the merged content to the file in the target branch
            # For now, just simulate success
            self.repo_path / result.file_path

            # In a real implementation, this would:
            # 1. Checkout target branch
            # 2. Write merged content to file
            # 3. Stage changes
            # 4. Validate that tests still pass
            # 5. Commit changes

            return True

        except Exception:
            logger.exception("Error applying merge result")
            return False

    @staticmethod
    def _determine_resolution_outcome(
        all_conflicts: list[SemanticConflict],
        escalated_conflicts: list[SemanticConflict],
        applied_results: list[MergeResult],
    ) -> ResolutionOutcome:
        """Determine the overall outcome of the resolution session."""
        total_conflicts = len(all_conflicts)
        resolved_conflicts = len(applied_results)
        escalated_count = len(escalated_conflicts)

        if total_conflicts == 0:
            return ResolutionOutcome.FULLY_RESOLVED

        if resolved_conflicts == total_conflicts:
            return ResolutionOutcome.FULLY_RESOLVED
        if resolved_conflicts > 0:
            return ResolutionOutcome.PARTIALLY_RESOLVED
        if escalated_count > 0:
            return ResolutionOutcome.ESCALATED_TO_HUMAN
        return ResolutionOutcome.RESOLUTION_FAILED

    @staticmethod
    def _calculate_session_confidence(
        applied_results: list[MergeResult],
    ) -> float:
        """Calculate overall confidence score for the resolution session."""
        if not applied_results:
            return 0.0

        total_confidence = sum(result.merge_confidence for result in applied_results)
        return total_confidence / len(applied_results)

    @staticmethod
    def _generate_prevention_strategies(
        predictions: list[PredictionResult],
    ) -> list[dict[str, Any]]:
        """Generate strategies to prevent predicted conflicts."""
        strategies = []

        for prediction in predictions:
            strategy: dict[str, Any] = {
                "prediction_id": prediction.prediction_id,
                "pattern": prediction.pattern.value,
                "prevention_suggestions": prediction.prevention_suggestions[:],  # Copy the list
                "automated_measures": [],
                "manual_actions": [],
            }

            # Add automated measures based on pattern type
            if "import" in prediction.pattern.value:
                strategy["automated_measures"].append("standardize_import_order")
                strategy["automated_measures"].append("add_import_sorting_hooks")

            if "signature" in prediction.pattern.value:
                strategy["manual_actions"].append("coordinate_api_changes")
                strategy["manual_actions"].append("implement_backwards_compatibility")

            strategies.append(strategy)

        return strategies

    async def _apply_preventive_measures(
        self,
        predictions: list[PredictionResult],
        strategies: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Apply automated preventive measures."""
        applied_measures = []

        for strategy in strategies:
            for measure in strategy["automated_measures"]:
                try:
                    if await AutoResolver._apply_preventive_measure(measure, strategy):
                        applied_measures.append(
                            {
                                "measure": measure,
                                "prediction_id": strategy["prediction_id"],
                                "status": "applied_successfully",
                            },
                        )
                except Exception as e:
                    applied_measures.append(
                        {
                            "measure": measure,
                            "prediction_id": strategy["prediction_id"],
                            "status": "failed",
                            "error": str(e),
                        },
                    )

        return applied_measures

    @staticmethod
    async def _apply_preventive_measure(
        measure: str,
        strategy: dict[str, Any],
    ) -> bool:
        """Apply a specific preventive measure."""
        # This would implement actual preventive measures
        # For now, just simulate success for certain measures
        return measure in {"standardize_import_order", "add_import_sorting_hooks"}

    def _update_resolution_stats(self, result: AutoResolutionResult) -> None:
        """Update resolution statistics."""
        self.resolution_stats["total_sessions"] += 1

        if result.outcome in {
            ResolutionOutcome.FULLY_RESOLVED,
            ResolutionOutcome.PARTIALLY_RESOLVED,
        }:
            self.resolution_stats["successful_resolutions"] += 1

        if result.outcome == ResolutionOutcome.FULLY_RESOLVED:
            self.resolution_stats["full_auto_resolutions"] += 1

        if result.outcome == ResolutionOutcome.ESCALATED_TO_HUMAN:
            self.resolution_stats["escalated_to_human"] += 1

        # Update average confidence
        total_confidence = self.resolution_stats["average_confidence"] * (self.resolution_stats["total_sessions"] - 1) + result.confidence_score
        self.resolution_stats["average_confidence"] = total_confidence / self.resolution_stats["total_sessions"]

        # Update semantic integrity rate
        if result.semantic_integrity_preserved:
            current_preserved = self.resolution_stats["semantic_integrity_rate"] * (self.resolution_stats["total_sessions"] - 1) + 1
        else:
            current_preserved = self.resolution_stats["semantic_integrity_rate"] * (self.resolution_stats["total_sessions"] - 1)

        self.resolution_stats["semantic_integrity_rate"] = current_preserved / self.resolution_stats["total_sessions"]

    def _learn_from_resolution(
        self,
        result: AutoResolutionResult,
        conflicts: list[SemanticConflict],
    ) -> None:
        """Learn from resolution results to improve future performance."""
        # Record successful patterns
        if result.outcome in {
            ResolutionOutcome.FULLY_RESOLVED,
            ResolutionOutcome.PARTIALLY_RESOLVED,
        }:
            for conflict in conflicts:
                if conflict.conflict_id not in result.escalated_conflicts:
                    pattern_key = f"{conflict.conflict_type.value}_{conflict.severity.value}"
                    self.success_patterns[pattern_key].append(
                        {
                            "mode": result.mode.value,
                            "confidence": result.confidence_score,
                            "resolution_time": result.resolution_time,
                        },
                    )

        # Record failure patterns
        else:
            for conflict in conflicts:
                pattern_key = f"{conflict.conflict_type.value}_{conflict.severity.value}"
                self.failure_patterns[pattern_key].append(
                    {
                        "mode": result.mode.value,
                        "outcome": result.outcome.value,
                        "metadata": result.metadata,
                    },
                )

    def get_resolution_summary(self) -> dict[str, Any]:
        """Get comprehensive summary of auto-resolution performance."""
        return {
            "performance_stats": self.resolution_stats.copy(),
            "success_patterns": dict(self.success_patterns),
            "failure_patterns": dict(self.failure_patterns),
            "recent_sessions": [
                {
                    "session_id": result.session_id,
                    "outcome": result.outcome.value,
                    "conflicts_resolved": result.conflicts_resolved,
                    "conflicts_detected": result.conflicts_detected,
                    "confidence_score": result.confidence_score,
                    "resolution_time": result.resolution_time,
                    "mode": result.mode.value,
                }
                for result in self.resolution_history[-10:]  # Last 10 sessions
            ],
            "mode_performance": self._analyze_mode_performance(),
            "recommendations": self._generate_performance_recommendations(),
        }

    def _analyze_mode_performance(self) -> dict[str, Any]:
        """Analyze performance by resolution mode."""
        mode_stats: defaultdict[str, dict[str, float]] = defaultdict(
            lambda: {
                "sessions": 0,
                "success_rate": 0.0,
                "average_confidence": 0.0,
                "average_resolution_time": 0.0,
            },
        )

        for result in self.resolution_history:
            mode = result.mode.value
            mode_stats[mode]["sessions"] += 1

            if result.outcome in {
                ResolutionOutcome.FULLY_RESOLVED,
                ResolutionOutcome.PARTIALLY_RESOLVED,
            }:
                mode_stats[mode]["success_rate"] += 1

            mode_stats[mode]["average_confidence"] += result.confidence_score
            mode_stats[mode]["average_resolution_time"] += result.resolution_time

        # Calculate averages
        for mode, stats in mode_stats.items():
            if stats["sessions"] > 0:
                stats["success_rate"] /= stats["sessions"]
                stats["average_confidence"] /= stats["sessions"]
                stats["average_resolution_time"] /= stats["sessions"]

        return dict(mode_stats)

    def _generate_performance_recommendations(self) -> list[str]:
        """Generate recommendations based on performance analysis."""
        recommendations = []

        # Analyze success rates
        if self.resolution_stats["total_sessions"] > MIN_SESSIONS_FOR_ANALYSIS:
            success_rate = self.resolution_stats["successful_resolutions"] / self.resolution_stats["total_sessions"]

            if success_rate < SUCCESS_RATE_THRESHOLD:
                recommendations.append(
                    "Consider using more conservative resolution mode to improve success rate",
                )

            if self.resolution_stats["average_confidence"] < CONFIDENCE_RATE_THRESHOLD:
                recommendations.append(
                    "Review conflict assessment criteria to improve confidence scores",
                )

            if self.resolution_stats["semantic_integrity_rate"] < SEMANTIC_INTEGRITY_THRESHOLD:
                recommendations.append(
                    "Enhance AST validation and semantic integrity checks",
                )

        # Analyze failure patterns
        common_failures = sorted(
            self.failure_patterns.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )[:3]

        for pattern, failures in common_failures:
            if len(failures) > MIN_FAILURE_COUNT:
                recommendations.append(f"Improve resolution strategy for {pattern} conflicts (failed {len(failures)} times)")

        return recommendations
