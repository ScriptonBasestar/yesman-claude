"""Performance metrics verification for multi-agent systems."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""

    single_agent_time: float = 0.0
    multi_agent_time: float = 0.0
    speed_improvement_ratio: float = 0.0
    total_conflicts: int = 0
    auto_resolved_conflicts: int = 0
    conflict_resolution_rate: float = 0.0
    total_merge_attempts: int = 0
    successful_merges: int = 0
    merge_success_rate: float = 0.0
    initial_quality_score: float = 0.0
    final_quality_score: float = 0.0
    quality_improvement: float = 0.0
    task_completion_times: list[float] = field(default_factory=list)
    agent_utilization_rates: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "single_agent_time": self.single_agent_time,
            "multi_agent_time": self.multi_agent_time,
            "speed_improvement_ratio": self.speed_improvement_ratio,
            "total_conflicts": self.total_conflicts,
            "auto_resolved_conflicts": self.auto_resolved_conflicts,
            "conflict_resolution_rate": self.conflict_resolution_rate,
            "total_merge_attempts": self.total_merge_attempts,
            "successful_merges": self.successful_merges,
            "merge_success_rate": self.merge_success_rate,
            "initial_quality_score": self.initial_quality_score,
            "final_quality_score": self.final_quality_score,
            "quality_improvement": self.quality_improvement,
            "task_completion_times": self.task_completion_times,
            "agent_utilization_rates": self.agent_utilization_rates,
        }


@dataclass
class SuccessCriteria:
    """Success criteria for performance validation."""

    min_speed_improvement: float = 1.2
    min_conflict_resolution_rate: float = 0.8
    min_merge_success_rate: float = 0.9
    min_quality_improvement: float = 0.1
    max_single_agent_time: float = 300.0
    max_multi_agent_time: float = 180.0

    def to_dict(self) -> dict[str, Any]:
        """Convert criteria to dictionary."""
        return {
            "min_speed_improvement": self.min_speed_improvement,
            "min_conflict_resolution_rate": self.min_conflict_resolution_rate,
            "min_merge_success_rate": self.min_merge_success_rate,
            "min_quality_improvement": self.min_quality_improvement,
            "max_single_agent_time": self.max_single_agent_time,
            "max_multi_agent_time": self.max_multi_agent_time,
        }


class MetricsVerifier:
    """Verifies performance metrics against success criteria."""

    def __init__(self, criteria: SuccessCriteria | None = None) -> None:
        self.criteria = criteria or SuccessCriteria()
        self.metrics_history: list[PerformanceMetrics] = []

    def verify_metrics(self, metrics: PerformanceMetrics) -> dict[str, bool]:
        """Verify metrics against success criteria."""
        results = {
            "speed_improvement": metrics.speed_improvement_ratio >= self.criteria.min_speed_improvement,
            "conflict_resolution": metrics.conflict_resolution_rate >= self.criteria.min_conflict_resolution_rate,
            "merge_success": metrics.merge_success_rate >= self.criteria.min_merge_success_rate,
            "quality_improvement": metrics.quality_improvement >= self.criteria.min_quality_improvement,
            "single_agent_time": metrics.single_agent_time <= self.criteria.max_single_agent_time,
            "multi_agent_time": metrics.multi_agent_time <= self.criteria.max_multi_agent_time,
        }
        return results

    def validate_performance(self, metrics: PerformanceMetrics) -> bool:
        """Validate overall performance against criteria."""
        verification_results = self.verify_metrics(metrics)
        return all(verification_results.values())

    def record_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record metrics in history."""
        self.metrics_history.append(metrics)

    def save_metrics(self, filepath: Path, metrics: PerformanceMetrics) -> None:
        """Save metrics to file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metrics.to_dict(), f, indent=2)

    def load_metrics(self, filepath: Path) -> PerformanceMetrics:
        """Load metrics from file."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        return PerformanceMetrics(
            single_agent_time=data.get("single_agent_time", 0.0),
            multi_agent_time=data.get("multi_agent_time", 0.0),
            speed_improvement_ratio=data.get("speed_improvement_ratio", 0.0),
            total_conflicts=data.get("total_conflicts", 0),
            auto_resolved_conflicts=data.get("auto_resolved_conflicts", 0),
            conflict_resolution_rate=data.get("conflict_resolution_rate", 0.0),
            total_merge_attempts=data.get("total_merge_attempts", 0),
            successful_merges=data.get("successful_merges", 0),
            merge_success_rate=data.get("merge_success_rate", 0.0),
            initial_quality_score=data.get("initial_quality_score", 0.0),
            final_quality_score=data.get("final_quality_score", 0.0),
            quality_improvement=data.get("quality_improvement", 0.0),
            task_completion_times=data.get("task_completion_times", []),
            agent_utilization_rates=data.get("agent_utilization_rates", []),
        )

    def generate_report(self, metrics: PerformanceMetrics) -> str:
        """Generate a performance report."""
        verification_results = self.verify_metrics(metrics)
        overall_success = self.validate_performance(metrics)

        report = "Performance Metrics Report\n"
        report += "=" * 30 + "\n\n"
        report += f"Overall Success: {'PASS' if overall_success else 'FAIL'}\n\n"

        report += "Detailed Results:\n"
        for criterion, result in verification_results.items():
            status = "PASS" if result else "FAIL"
            report += f"  {criterion}: {status}\n"

        report += "\nMetrics Summary:\n"
        report += f"  Speed Improvement: {metrics.speed_improvement_ratio:.2f}x\n"
        report += f"  Conflict Resolution Rate: {metrics.conflict_resolution_rate:.2%}\n"
        report += f"  Merge Success Rate: {metrics.merge_success_rate:.2%}\n"
        report += f"  Quality Improvement: {metrics.quality_improvement:.2%}\n"

        return report
