#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Unified Quality Gates with Security-Performance Integration.

This module combines performance and security quality gates,
enabling comprehensive quality checks with correlation analysis.
"""

import asyncio
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from libs.core.async_event_bus import get_event_bus
from libs.dashboard.monitoring_integration import (
    get_monitoring_dashboard,
)
from libs.dashboard.security_metrics_integration import (
    SecurityMetrics,
    get_security_metrics_integration,
)
from scripts.quality_gates_performance import (
    QualityGatesPerformanceChecker,
)
from scripts.security_validation_enhanced import EnhancedSecurityValidator


@dataclass
class SecurityQualityGate:
    """Security-related quality gate configuration."""

    name: str
    description: str
    metric: str  # 'violations', 'scan_time', 'false_positives', 'coverage'
    threshold: float
    level: str  # 'blocking', 'warning', 'advisory'
    severity_filter: str | None = None  # Filter by severity level


@dataclass
class UnifiedQualityGateResult:
    """Unified quality gate check result."""

    passed: bool
    performance_passed: bool
    security_passed: bool
    blocking_failures: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    correlations: list[dict[str, Any]]
    metrics: dict[str, Any]
    recommendations: list[str]


class UnifiedQualityGatesChecker:
    """Unified quality gates checker for security and performance."""

    def __init__(self, baseline_path: Path | None = None) -> None:
        """Initialize unified quality gates checker.

        Args:
            baseline_path: Path to baseline files
        """
        self.baseline_path = baseline_path or Path("data")
        self.monitoring_dashboard = get_monitoring_dashboard()
        self.security_metrics = get_security_metrics_integration(self.monitoring_dashboard)
        self.performance_checker = QualityGatesPerformanceChecker(self.baseline_path / "performance_baselines.json")
        self.event_bus = get_event_bus()

        # Security gates configuration
        self.security_gates = self._load_security_gates()

        # Correlation thresholds
        self.correlation_thresholds = {
            "security_scan_performance_impact": 20.0,  # % performance degradation
            "violation_error_correlation": 0.7,  # Correlation coefficient
            "security_regression_threshold": 50.0,  # % increase in violations
        }

    def _load_security_gates(self) -> list[SecurityQualityGate]:
        """Load security quality gates configuration.

        Returns:
            List of security quality gates
        """
        gates = []

        # Critical security violations gate
        gates.append(
            SecurityQualityGate(
                name="critical_violations",
                description="No critical security violations allowed",
                metric="violations",
                threshold=0,
                level="blocking",
                severity_filter="critical",
            )
        )

        # High severity violations gate
        gates.append(
            SecurityQualityGate(
                name="high_violations",
                description="Maximum 5 high severity violations",
                metric="violations",
                threshold=5,
                level="blocking",
                severity_filter="high",
            )
        )

        # Total violations gate
        gates.append(
            SecurityQualityGate(
                name="total_violations",
                description="Maximum 20 total security violations",
                metric="violations",
                threshold=20,
                level="warning",
            )
        )

        # Security scan time gate
        gates.append(
            SecurityQualityGate(
                name="security_scan_time",
                description="Security scan should complete within 5 seconds",
                metric="scan_time",
                threshold=5000,  # 5 seconds in ms
                level="warning",
            )
        )

        # False positive rate gate
        gates.append(
            SecurityQualityGate(
                name="false_positive_rate",
                description="False positive rate should be under 15%",
                metric="false_positives",
                threshold=15.0,
                level="advisory",
            )
        )

        # Scan coverage gate
        gates.append(
            SecurityQualityGate(
                name="scan_coverage",
                description="Security scan coverage should be at least 90%",
                metric="coverage",
                threshold=90.0,
                level="warning",
            )
        )

        return gates

    async def run_security_scan(self) -> SecurityMetrics:
        """Run security validation and collect metrics.

        Returns:
            Security scan metrics
        """
        print("🔍 Running security validation...")

        # Run enhanced security validator
        validator = EnhancedSecurityValidator()
        success = await validator.run_validation_async()

        # Create metrics from validator results
        total_violations = sum(validator.violation_counts.values())
        false_positive_rate = (validator.false_positives / max(total_violations, 1)) * 100 if total_violations > 0 else 0

        metrics = SecurityMetrics(
            scan_duration_ms=(validator.scan_end_time - validator.scan_start_time) * 1000,
            violations_found=total_violations,
            false_positive_rate=false_positive_rate,
            vulnerability_severity_counts=validator.violation_counts,
            scan_coverage_percent=(validator.files_scanned / max(validator.total_files, 1)) * 100,
        )

        return metrics

    async def check_security_gates(self, metrics: SecurityMetrics) -> dict[str, Any]:
        """Check security quality gates.

        Args:
            metrics: Security scan metrics

        Returns:
            Security gate check results
        """
        results = {
            "passed": [],
            "warnings": [],
            "failures": [],
            "blocking_failures": [],
        }

        for gate in self.security_gates:
            gate_result = self._check_single_security_gate(gate, metrics)

            if gate_result["passed"]:
                results["passed"].append(gate_result)
            elif gate.level == "blocking" and not gate_result["passed"]:
                results["blocking_failures"].append(gate_result)
                results["failures"].append(gate_result)
            elif gate.level == "warning" and not gate_result["passed"]:
                results["warnings"].append(gate_result)
            else:
                results["failures"].append(gate_result)

        return results

    def _check_single_security_gate(
        self,
        gate: SecurityQualityGate,
        metrics: SecurityMetrics,
    ) -> dict[str, Any]:
        """Check a single security gate.

        Args:
            gate: Security gate to check
            metrics: Security scan metrics

        Returns:
            Gate check result
        """
        result = {
            "name": gate.name,
            "description": gate.description,
            "level": gate.level,
            "passed": True,
            "value": 0.0,
            "threshold": gate.threshold,
        }

        # Get metric value based on gate configuration
        if gate.metric == "violations":
            if gate.severity_filter:
                value = metrics.vulnerability_severity_counts.get(gate.severity_filter, 0)
            else:
                value = metrics.violations_found
        elif gate.metric == "scan_time":
            value = metrics.scan_duration_ms
        elif gate.metric == "false_positives":
            value = metrics.false_positive_rate
        elif gate.metric == "coverage":
            value = metrics.scan_coverage_percent
        else:
            value = 0

        result["value"] = value

        # Check against threshold
        if gate.metric == "coverage":
            # For coverage, we want value >= threshold
            result["passed"] = value >= gate.threshold
        else:
            # For other metrics, we want value <= threshold
            result["passed"] = value <= gate.threshold

        return result

    async def check_security_performance_correlation(
        self,
        security_metrics: SecurityMetrics,
        performance_results: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Check for security-performance correlations.

        Args:
            security_metrics: Security scan metrics
            performance_results: Performance quality gate results

        Returns:
            List of correlation findings
        """
        correlations = []

        # Check if security scan impacted performance
        if self.security_metrics._performance_impact_cache:
            for component, impact in self.security_metrics._performance_impact_cache.items():
                if abs(impact) > self.correlation_thresholds["security_scan_performance_impact"]:
                    correlations.append(
                        {
                            "type": "security_scan_impact",
                            "component": component,
                            "impact_percent": impact,
                            "severity": "high" if abs(impact) > 50 else "medium",
                            "recommendation": self._get_correlation_recommendation("security_scan_impact", impact),
                        }
                    )

        # Check if high violation count correlates with errors
        if security_metrics.violations_found > 10:
            error_rates = self._get_error_rates_from_performance(performance_results)
            for component, error_rate in error_rates.items():
                if error_rate > 5:  # 5% error rate
                    correlations.append(
                        {
                            "type": "violation_error_correlation",
                            "component": component,
                            "violations": security_metrics.violations_found,
                            "error_rate": error_rate,
                            "severity": "medium",
                            "recommendation": self._get_correlation_recommendation("violation_error_correlation", error_rate),
                        }
                    )

        # Check for security regression
        security_baseline = self._load_security_baseline()
        if security_baseline:
            baseline_violations = security_baseline.get("total_violations", 0)
            if baseline_violations > 0:
                regression_percent = ((security_metrics.violations_found - baseline_violations) / baseline_violations) * 100

                if regression_percent > self.correlation_thresholds["security_regression_threshold"]:
                    correlations.append(
                        {
                            "type": "security_regression",
                            "baseline_violations": baseline_violations,
                            "current_violations": security_metrics.violations_found,
                            "regression_percent": regression_percent,
                            "severity": "high",
                            "recommendation": self._get_correlation_recommendation("security_regression", regression_percent),
                        }
                    )

        return correlations

    def _get_error_rates_from_performance(
        self,
        performance_results: dict[str, Any],
    ) -> dict[str, float]:
        """Extract error rates from performance results.

        Args:
            performance_results: Performance quality gate results

        Returns:
            Component error rates
        """
        error_rates = {}

        if "metrics" in performance_results:
            for component, metrics in performance_results["metrics"].items():
                if "error_rate" in metrics:
                    error_rates[component] = metrics["error_rate"].get("average", 0)

        return error_rates

    def _get_correlation_recommendation(
        self,
        correlation_type: str,
        value: float,
    ) -> str:
        """Get recommendation for correlation finding.

        Args:
            correlation_type: Type of correlation
            value: Correlation value

        Returns:
            Recommendation string
        """
        recommendations = {
            "security_scan_impact": {
                "high": "Security scans significantly impact performance. Schedule during maintenance windows.",
                "medium": "Security scans moderately impact performance. Consider optimizing scan patterns.",
                "low": "Security scans have acceptable performance impact.",
            },
            "violation_error_correlation": {
                "high": "High correlation between security violations and errors. Prioritize security fixes.",
                "medium": "Moderate correlation between violations and errors. Review security issues.",
                "low": "Low correlation between violations and errors.",
            },
            "security_regression": {
                "high": "Significant security regression detected. Immediate review required.",
                "medium": "Moderate security regression. Review recent changes.",
                "low": "Minor security regression. Monitor trend.",
            },
        }

        severity = "high" if abs(value) > 50 else "medium" if abs(value) > 20 else "low"

        return recommendations.get(correlation_type, {}).get(severity, "Review correlation findings and take appropriate action.")

    def _load_security_baseline(self) -> dict[str, Any] | None:
        """Load security baseline data.

        Returns:
            Security baseline dictionary or None
        """
        baseline_path = self.baseline_path / "security_baselines.json"
        if baseline_path.exists():
            try:
                with open(baseline_path, encoding="utf-8") as f:
                    baselines = json.load(f)
                    return baselines.get("security_validation", {})
            except Exception:
                pass
        return None

    def _update_security_baseline(self, metrics: SecurityMetrics) -> None:
        """Update security baseline with current metrics.

        Args:
            metrics: Current security metrics
        """
        baseline_path = self.baseline_path / "security_baselines.json"

        try:
            if baseline_path.exists():
                with open(baseline_path, encoding="utf-8") as f:
                    baselines = json.load(f)
            else:
                baselines = {}

            baselines["security_validation"] = {
                "total_violations": metrics.violations_found,
                "critical_violations": metrics.vulnerability_severity_counts.get("critical", 0),
                "high_violations": metrics.vulnerability_severity_counts.get("high", 0),
                "scan_time_ms": metrics.scan_duration_ms,
                "false_positive_rate": metrics.false_positive_rate,
                "scan_coverage": metrics.scan_coverage_percent,
                "timestamp": time.time(),
            }

            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            with open(baseline_path, "w", encoding="utf-8") as f:
                json.dump(baselines, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update security baseline: {e}")

    async def check_unified_quality_gates(
        self,
        run_security_scan: bool = True,
    ) -> UnifiedQualityGateResult:
        """Check all unified quality gates.

        Args:
            run_security_scan: Whether to run security scan

        Returns:
            Unified quality gate results
        """
        print("=" * 60)
        print("UNIFIED QUALITY GATES CHECK")
        print("=" * 60)

        # Initialize result
        result = UnifiedQualityGateResult(
            passed=True,
            performance_passed=True,
            security_passed=True,
            blocking_failures=[],
            warnings=[],
            correlations=[],
            metrics={},
            recommendations=[],
        )

        # Run security scan if requested
        security_metrics = None
        security_results = None
        if run_security_scan:
            try:
                security_metrics = await self.run_security_scan()
                security_results = await self.check_security_gates(security_metrics)

                # Update security baseline if all gates passed
                if not security_results.get("blocking_failures"):
                    self._update_security_baseline(security_metrics)

                result.metrics["security"] = {
                    "scan_time_ms": security_metrics.scan_duration_ms,
                    "violations": security_metrics.violations_found,
                    "severity_breakdown": security_metrics.vulnerability_severity_counts,
                    "false_positive_rate": security_metrics.false_positive_rate,
                    "coverage": security_metrics.scan_coverage_percent,
                }
            except Exception as e:
                print(f"⚠️  Security scan failed: {e}")
                result.security_passed = False
                result.warnings.append(
                    {
                        "name": "security_scan_failed",
                        "description": f"Security scan failed: {e}",
                    }
                )

        # Check performance quality gates
        try:
            performance_results = await self.performance_checker.check_performance_gates()

            result.metrics["performance"] = performance_results.get("metrics", {})

            # Process performance results
            if performance_results.get("blocking_failures"):
                result.performance_passed = False
                result.blocking_failures.extend(performance_results["blocking_failures"])

            result.warnings.extend(performance_results.get("warnings", []))

        except Exception as e:
            print(f"⚠️  Performance check failed: {e}")
            result.performance_passed = False
            result.warnings.append(
                {
                    "name": "performance_check_failed",
                    "description": f"Performance check failed: {e}",
                }
            )
            performance_results = {}

        # Process security results
        if security_results:
            if security_results.get("blocking_failures"):
                result.security_passed = False
                result.blocking_failures.extend(security_results["blocking_failures"])

            result.warnings.extend(security_results.get("warnings", []))

        # Check correlations if both checks succeeded
        if security_metrics and performance_results:
            correlations = await self.check_security_performance_correlation(
                security_metrics,
                performance_results,
            )
            result.correlations = correlations

            # Add correlation warnings
            for correlation in correlations:
                if correlation.get("severity") in {"high", "critical"}:
                    result.warnings.append(
                        {
                            "name": f"correlation_{correlation['type']}",
                            "description": correlation.get("recommendation", ""),
                            "details": correlation,
                        }
                    )

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        # Determine overall pass/fail
        result.passed = result.performance_passed and result.security_passed and len(result.blocking_failures) == 0

        return result

    def _generate_recommendations(
        self,
        result: UnifiedQualityGateResult,
    ) -> list[str]:
        """Generate recommendations based on results.

        Args:
            result: Unified quality gate results

        Returns:
            List of recommendations
        """
        recommendations = []

        # Security recommendations
        if not result.security_passed:
            recommendations.append("🔒 Security: Address critical security violations before deployment")

        security_metrics = result.metrics.get("security", {})
        if security_metrics.get("false_positive_rate", 0) > 20:
            recommendations.append("🎯 Security: High false positive rate detected. Review security rules.")

        # Performance recommendations
        if not result.performance_passed:
            recommendations.append("⚡ Performance: Optimize components exceeding performance thresholds")

        # Correlation recommendations
        high_impact_correlations = [c for c in result.correlations if c.get("severity") in {"high", "critical"}]
        if high_impact_correlations:
            recommendations.append("🔗 Correlation: Security operations significantly impact performance. Consider optimization or scheduling adjustments.")

        # General recommendations
        if result.passed:
            recommendations.append("✅ All quality gates passed. System ready for deployment.")
        else:
            recommendations.append("❌ Quality gates failed. Address blocking issues before proceeding.")

        return recommendations

    def generate_unified_report(self, result: UnifiedQualityGateResult) -> str:
        """Generate unified quality gates report.

        Args:
            result: Unified quality gate results

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("UNIFIED QUALITY GATES REPORT")
        report.append("=" * 60)
        report.append("")

        # Overall status
        status_icon = "✅" if result.passed else "❌"
        report.append(f"{status_icon} Overall Status: {'PASSED' if result.passed else 'FAILED'}")
        report.append(f"  Performance: {'✅ Passed' if result.performance_passed else '❌ Failed'}")
        report.append(f"  Security: {'✅ Passed' if result.security_passed else '❌ Failed'}")
        report.append("")

        # Blocking failures
        if result.blocking_failures:
            report.append("🚫 BLOCKING FAILURES:")
            for failure in result.blocking_failures:
                report.append(f"  ❌ {failure.get('name', 'unknown')}: {failure.get('description', '')}")
                if "value" in failure and "threshold" in failure:
                    report.append(f"     Value: {failure['value']:.2f}, Threshold: {failure['threshold']:.2f}")
            report.append("")

        # Warnings
        if result.warnings:
            report.append("⚠️  WARNINGS:")
            for warning in result.warnings[:10]:  # Limit to 10 warnings
                report.append(f"  ⚠️  {warning.get('name', 'unknown')}: {warning.get('description', '')}")
            if len(result.warnings) > 10:
                report.append(f"  ... and {len(result.warnings) - 10} more warnings")
            report.append("")

        # Correlations
        if result.correlations:
            report.append("🔗 SECURITY-PERFORMANCE CORRELATIONS:")
            for correlation in result.correlations:
                report.append(f"  • {correlation.get('type', 'unknown')}:")
                report.append(f"    Component: {correlation.get('component', 'N/A')}")
                report.append(f"    Severity: {correlation.get('severity', 'N/A')}")
                report.append(f"    Recommendation: {correlation.get('recommendation', 'N/A')}")
            report.append("")

        # Metrics summary
        if result.metrics:
            report.append("📊 METRICS SUMMARY:")

            # Security metrics
            if "security" in result.metrics:
                sec = result.metrics["security"]
                report.append("  Security:")
                report.append(f"    Scan time: {sec.get('scan_time_ms', 0):.0f}ms")
                report.append(f"    Total violations: {sec.get('violations', 0)}")
                report.append(f"    Coverage: {sec.get('coverage', 0):.1f}%")
                report.append(f"    False positive rate: {sec.get('false_positive_rate', 0):.1f}%")

            # Performance metrics (summary only)
            if "performance" in result.metrics:
                perf = result.metrics["performance"]
                if perf:
                    report.append("  Performance:")
                    # Count components
                    component_count = len(perf)
                    report.append(f"    Components monitored: {component_count}")
            report.append("")

        # Recommendations
        if result.recommendations:
            report.append("💡 RECOMMENDATIONS:")
            for rec in result.recommendations:
                report.append(f"  {rec}")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)


async def run_unified_quality_gates() -> tuple[bool, str]:
    """Run unified quality gates check.

    Returns:
        Tuple of (success, report)
    """
    checker = UnifiedQualityGatesChecker()

    # Start monitoring components
    await checker.monitoring_dashboard.start()
    await checker.security_metrics.start()

    try:
        # Run unified checks
        result = await checker.check_unified_quality_gates(run_security_scan=True)

        # Generate report
        report = checker.generate_unified_report(result)

        return result.passed, report

    finally:
        # Stop monitoring components
        await checker.monitoring_dashboard.stop()
        await checker.security_metrics.stop()


def main() -> None:
    """Main entry point for unified quality gates."""
    try:
        success, report = asyncio.run(run_unified_quality_gates())
        print(report)

        if not success:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"💥 Unified quality gates check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
