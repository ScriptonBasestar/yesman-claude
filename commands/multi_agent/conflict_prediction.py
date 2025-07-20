"""Conflict prediction and analysis commands."""

import asyncio
import logging
from datetime import timedelta

from libs.core.base_command import BaseCommand, CommandError
from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.conflict_prediction import ConflictPredictor
from libs.multi_agent.conflict_resolution import ConflictResolutionEngine

logger = logging.getLogger(__name__)


class PredictConflictsCommand(BaseCommand):
    """Predict potential conflicts between branches."""

    def execute(
        self,
        branches: list[str] | None = None,
        repo_path: str | None = None,
        time_horizon: int = 7,
        min_confidence: float = 0.3,
        limit: int = 10,
        **kwargs,
    ) -> dict:
        """Execute the predict conflicts command."""
        try:
            # Validate required parameters
            if not branches:
                msg = "Branches list is required for conflict prediction"
                raise CommandError(msg)

            self.print_info(f"🔮 Predicting conflicts for branches: {', '.join(branches)}")
            self.print_info(f"   Time horizon: {time_horizon} days")
            self.print_info(f"   Confidence threshold: {min_confidence}")

            # Create prediction system
            branch_manager = BranchManager(repo_path=repo_path)
            conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
            predictor = ConflictPredictor(conflict_engine, branch_manager, repo_path)

            # Set prediction parameters
            predictor.min_confidence_threshold = min_confidence
            predictor.max_predictions_per_run = limit * 2  # Get more, filter later

            async def run_prediction():
                horizon = timedelta(days=time_horizon)
                predictions = await predictor.predict_conflicts(branches, horizon)

                if not predictions:
                    self.print_success("✅ No potential conflicts predicted")
                    return {
                        "success": True,
                        "branches": branches,
                        "repo_path": repo_path,
                        "predictions": [],
                        "parameters": {
                            "time_horizon": time_horizon,
                            "min_confidence": min_confidence,
                            "limit": limit,
                        },
                    }

                # Filter and limit results
                filtered_predictions = [p for p in predictions if p.likelihood_score >= min_confidence]
                filtered_predictions = filtered_predictions[:limit]

                self.print_info(f"⚠️  Found {len(filtered_predictions)} potential conflicts:")
                self.print_info("=" * 80)

                for i, prediction in enumerate(filtered_predictions, 1):
                    confidence_icon = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🔴",
                        "critical": "💀",
                    }.get(prediction.confidence.value, "❓")

                    self.print_info(f"{i}. {confidence_icon} {prediction.prediction_id}")
                    self.print_info(f"   Confidence: {prediction.confidence.value} ({prediction.likelihood_score:.2f})")
                    self.print_info(f"   Branches: {', '.join(prediction.affected_branches)}")
                    self.print_info(f"   Predicted files: {', '.join(prediction.affected_files)}")
                    self.print_info(f"   Description: {prediction.description}")
                    if prediction.prevention_suggestions:
                        self.print_info("   Prevention strategies:")
                        for suggestion in prediction.prevention_suggestions[:2]:  # Show first 2 suggestions
                            self.print_info(f"      - {suggestion}")
                    self.print_info("")

                return {
                    "success": True,
                    "branches": branches,
                    "repo_path": repo_path,
                    "predictions": filtered_predictions,
                    "count": len(filtered_predictions),
                    "parameters": {
                        "time_horizon": time_horizon,
                        "min_confidence": min_confidence,
                        "limit": limit,
                    },
                }

            return asyncio.run(run_prediction())

        except Exception as e:
            msg = f"Error predicting conflicts: {e}"
            raise CommandError(msg) from e


class PredictionSummaryCommand(BaseCommand):
    """Show prediction summary and statistics."""

    def execute(self, repo_path: str | None = None, **kwargs) -> dict:
        """Execute the prediction summary command."""
        try:
            self.print_info("🔮 Conflict Prediction Summary")
            self.print_info("=" * 40)

            # Create prediction system
            branch_manager = BranchManager(repo_path=repo_path)
            conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
            predictor = ConflictPredictor(conflict_engine, branch_manager, repo_path)

            summary = predictor.get_prediction_summary()

            # Overall statistics
            self.print_info(f"Total Predictions: {summary['total_predictions']}")
            if "accuracy_metrics" in summary:
                metrics = summary["accuracy_metrics"]
                self.print_info(f"Accurate Predictions: {metrics.get('accurate_predictions', 0)}")
                self.print_info(f"False Positives: {metrics.get('false_positives', 0)}")
                self.print_info(f"Accuracy Rate: {metrics.get('accuracy_rate', 0):.1%}")

            # Confidence breakdown
            if summary.get("by_confidence"):
                self.print_info("\n📊 Confidence Breakdown:")
                for confidence, count in summary["by_confidence"].items():
                    if count > 0:
                        self.print_info(f"  {confidence.capitalize()}: {count}")

            return {"success": True, "repo_path": repo_path, "summary": summary}

        except Exception as e:
            msg = f"Error getting prediction summary: {e}"
            raise CommandError(msg) from e


class AnalyzeConflictPatternsCommand(BaseCommand):
    """Analyze detailed conflict patterns and trends."""

    def execute(self, repo_path: str | None = None, **kwargs) -> dict:
        """Execute the analyze conflict patterns command."""
        try:
            self.print_info("📈 Analyzing conflict patterns...")

            # Create prediction system
            branch_manager = BranchManager(repo_path=repo_path)
            conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
            predictor = ConflictPredictor(conflict_engine, branch_manager, repo_path)

            analysis = predictor.analyze_conflict_patterns()

            self.print_info("🔍 Conflict Pattern Analysis")
            self.print_info("=" * 50)

            # Display pattern insights
            if analysis.get("frequent_conflict_files"):
                self.print_info("\n🎯 Most Conflict-Prone Files:")
                for file_info in analysis["frequent_conflict_files"][:5]:
                    self.print_info(f"  📄 {file_info['file']}: {file_info['conflict_count']} conflicts")

            if analysis.get("conflict_hotspots"):
                self.print_info("\n🔥 Conflict Hotspots:")
                for hotspot in analysis["conflict_hotspots"][:3]:
                    self.print_info(f"  📍 {hotspot['location']}: {hotspot['severity']}")

            return {"success": True, "repo_path": repo_path, "analysis": analysis}

        except Exception as e:
            msg = f"Error analyzing conflict patterns: {e}"
            raise CommandError(msg) from e
