#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""
Automated Quality Gates Checker for Yesman-Claude.

This script implements the comprehensive quality gate system designed in Phase 2,
providing automated checks for code quality, performance, security, and architecture
compliance. It supports both CI/CD integration and local development workflows.

Quality Gate Types:
- BLOCKING: Prevent deployment/merge (linting, security, breaking changes)
- WARNING: Require review (complexity, coverage, documentation)
- ADVISORY: Best practice guidance (async adoption, type annotations)
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class GateResult(Enum):
    """Quality gate check results."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


class GateLevel(Enum):
    """Quality gate severity levels."""

    BLOCKING = "blocking"
    WARNING = "warning"
    ADVISORY = "advisory"


@dataclass
class QualityCheck:
    """Individual quality check result."""

    name: str
    level: GateLevel
    result: GateResult
    score: float
    threshold: float
    message: str
    details: Dict[str, Any]
    execution_time: float


@dataclass
class QualityGateResults:
    """Complete quality gate execution results."""

    overall_result: GateResult
    blocking_failures: int
    warning_failures: int
    total_checks: int
    execution_time: float
    checks: List[QualityCheck]
    summary: Dict[str, Any]


class QualityGatesChecker:
    """
    Comprehensive quality gates checker implementing the Phase 2 quality framework.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize quality gates checker.

        Args:
            config_path: Optional path to quality gates configuration
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.results: List[QualityCheck] = []

        # Performance monitoring integration
        self.performance_monitor = None
        try:
            from scripts.performance_baseline import create_quality_gates_metrics, get_performance_monitor

            self.performance_monitor = get_performance_monitor()
            self._create_quality_gates_metrics = create_quality_gates_metrics
        except ImportError:
            self.logger.warning("Performance monitoring not available")

    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load quality gates configuration."""
        default_config = {
            "blocking_gates": {
                "linting_violations_max": 200,
                "security_critical_issues_max": 0,
                "test_coverage_min": 35,
                "performance_regression_threshold": 10,
            },
            "warning_gates": {
                "code_complexity_max": 15,
                "documentation_coverage_min": 60,
                "memory_usage_increase_max": 20,
                "new_violations_per_pr_max": 5,
            },
            "advisory_gates": {
                "async_adoption_target": 30,
                "type_annotation_coverage": 80,
                "performance_optimization_score": 70,
            },
            "enabled_checks": ["linting", "security", "test_coverage", "complexity", "documentation", "performance", "async_adoption", "type_annotations"],
        }

        if config_path and config_path.exists():
            try:
                with open(config_path) as f:
                    user_config = json.load(f)
                # Merge user config with defaults
                for section, values in user_config.items():
                    if section in default_config:
                        default_config[section].update(values)
                    else:
                        default_config[section] = values
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")

        return default_config

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for quality gates."""
        logger = logging.getLogger("quality_gates")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _record_performance_metrics(self, gate_name: str, execution_time: float, result: str, exit_code: int = 0) -> None:
        """Record performance metrics for a quality gate execution."""
        if self.performance_monitor and hasattr(self, "_create_quality_gates_metrics"):
            try:
                metrics = self._create_quality_gates_metrics(
                    gate_name=gate_name,
                    execution_time_ms=execution_time * 1000,  # Convert to milliseconds
                    result=result,
                    exit_code=exit_code,
                )
                self.performance_monitor.record_quality_gates_metrics(metrics)
            except Exception as e:
                self.logger.debug(f"Failed to record performance metrics for {gate_name}: {e}")

    async def run_all_gates(self) -> QualityGateResults:
        """
        Run all enabled quality gates.

        Returns:
            Complete quality gate results
        """
        self.logger.info("🛡️ Running Yesman-Claude Quality Gates...")
        start_time = time.perf_counter()

        self.results = []
        enabled_checks = self.config.get("enabled_checks", [])

        # Execute checks in parallel where possible
        check_tasks = []

        if "linting" in enabled_checks:
            check_tasks.append(self._check_linting())
        if "security" in enabled_checks:
            check_tasks.append(self._check_security())
        if "test_coverage" in enabled_checks:
            check_tasks.append(self._check_test_coverage())
        if "complexity" in enabled_checks:
            check_tasks.append(self._check_complexity())
        if "documentation" in enabled_checks:
            check_tasks.append(self._check_documentation())
        if "performance" in enabled_checks:
            check_tasks.append(self._check_performance())
        if "async_adoption" in enabled_checks:
            check_tasks.append(self._check_async_adoption())
        if "type_annotations" in enabled_checks:
            check_tasks.append(self._check_type_annotations())

        # Execute all checks
        for check_task in check_tasks:
            try:
                result = await check_task
                self.results.append(result)
            except Exception as e:
                self.logger.error(f"Error running quality check: {e}")
                # Add error result
                self.results.append(
                    QualityCheck(
                        name="check_error",
                        level=GateLevel.BLOCKING,
                        result=GateResult.FAIL,
                        score=0.0,
                        threshold=100.0,
                        message=f"Quality check failed: {e}",
                        details={"error": str(e)},
                        execution_time=0.0,
                    )
                )

        execution_time = time.perf_counter() - start_time
        return self._compile_results(execution_time)

    async def _check_linting(self) -> QualityCheck:
        """Check code linting violations (BLOCKING gate)."""
        start_time = time.perf_counter()

        try:
            # Run ruff linting check
            result = subprocess.run(["ruff", "check", ".", "--output-format=json"], capture_output=True, text=True)

            violations = 0
            details = {"violations": []}

            if result.stdout:
                try:
                    lint_results = json.loads(result.stdout)
                    violations = len(lint_results)

                    # Group violations by type for analysis
                    violation_types = {}
                    for violation in lint_results:
                        rule_code = violation.get("code", "unknown")
                        if rule_code not in violation_types:
                            violation_types[rule_code] = 0
                        violation_types[rule_code] += 1

                    details = {
                        "total_violations": violations,
                        "violation_types": violation_types,
                        "top_violations": list(lint_results[:10]),  # First 10 for details
                    }
                except json.JSONDecodeError:
                    # Fallback: count lines of output
                    violations = len([line for line in result.stdout.split("\n") if line.strip()])

            threshold = self.config["blocking_gates"]["linting_violations_max"]
            is_passing = violations <= threshold

            execution_time = time.perf_counter() - start_time
            result_status = GateResult.PASS if is_passing else GateResult.FAIL

            # Record performance metrics
            self._record_performance_metrics(gate_name="linting", execution_time=execution_time, result=result_status.value, exit_code=result.returncode)

            return QualityCheck(
                name="linting",
                level=GateLevel.BLOCKING,
                result=result_status,
                score=max(0, 100 - (violations / max(1, threshold) * 100)),
                threshold=threshold,
                message=f"Linting check: {violations} violations (threshold: {threshold})",
                details=details,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.perf_counter() - start_time

            # Record performance metrics for failed check
            self._record_performance_metrics(gate_name="linting", execution_time=execution_time, result="fail", exit_code=1)

            return QualityCheck(
                name="linting",
                level=GateLevel.BLOCKING,
                result=GateResult.FAIL,
                score=0.0,
                threshold=self.config["blocking_gates"]["linting_violations_max"],
                message=f"Linting check failed: {e}",
                details={"error": str(e)},
                execution_time=execution_time,
            )

    async def _check_security(self) -> QualityCheck:
        """Check security vulnerabilities (BLOCKING gate)."""
        start_time = time.perf_counter()

        try:
            # Run bandit security scan
            result = subprocess.run(["bandit", "-r", ".", "-f", "json"], capture_output=True, text=True)

            critical_issues = 0
            details = {"issues": []}

            if result.stdout:
                try:
                    security_results = json.loads(result.stdout)
                    results = security_results.get("results", [])

                    # Count critical/high severity issues
                    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

                    for issue in results:
                        severity = issue.get("issue_severity", "LOW")
                        if severity in severity_counts:
                            severity_counts[severity] += 1

                        if severity == "HIGH":
                            critical_issues += 1

                    details = {
                        "total_issues": len(results),
                        "critical_issues": critical_issues,
                        "severity_breakdown": severity_counts,
                        "sample_issues": results[:5],  # First 5 for details
                    }

                except json.JSONDecodeError as e:
                    self.logger.warning(f"Could not parse bandit output: {e}")

            threshold = self.config["blocking_gates"]["security_critical_issues_max"]
            is_passing = critical_issues <= threshold

            execution_time = time.perf_counter() - start_time

            return QualityCheck(
                name="security",
                level=GateLevel.BLOCKING,
                result=GateResult.PASS if is_passing else GateResult.FAIL,
                score=100 if is_passing else 0,
                threshold=threshold,
                message=f"Security check: {critical_issues} critical issues (threshold: {threshold})",
                details=details,
                execution_time=execution_time,
            )

        except FileNotFoundError:
            execution_time = time.perf_counter() - start_time
            self.logger.warning("Bandit not found, skipping security check")
            return QualityCheck(
                name="security",
                level=GateLevel.BLOCKING,
                result=GateResult.SKIP,
                score=0.0,
                threshold=0,
                message="Security check skipped: bandit not installed",
                details={"skipped": True, "reason": "bandit not found"},
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            return QualityCheck(
                name="security",
                level=GateLevel.BLOCKING,
                result=GateResult.FAIL,
                score=0.0,
                threshold=self.config["blocking_gates"]["security_critical_issues_max"],
                message=f"Security check failed: {e}",
                details={"error": str(e)},
                execution_time=execution_time,
            )

    async def _check_test_coverage(self) -> QualityCheck:
        """Check test coverage (BLOCKING gate)."""
        start_time = time.perf_counter()

        try:
            # Run pytest with coverage
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=libs", "--cov=commands", "--cov=api", "--cov-report=json", "--cov-report=term-missing", "--quiet"], capture_output=True, text=True, timeout=300
            )

            coverage_percent = 0.0
            details = {"coverage_data": {}}

            # Try to read coverage.json
            coverage_file = Path("coverage.json")
            if coverage_file.exists():
                try:
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)

                    coverage_percent = coverage_data["totals"]["percent_covered"]

                    # Analyze file-level coverage
                    file_coverage = {}
                    for file_path, file_data in coverage_data.get("files", {}).items():
                        file_coverage[file_path] = file_data["summary"]["percent_covered"]

                    # Find files with low coverage
                    low_coverage_files = {path: coverage for path, coverage in file_coverage.items() if coverage < 50}

                    details = {
                        "total_coverage": coverage_percent,
                        "files_analyzed": len(file_coverage),
                        "low_coverage_files": low_coverage_files,
                        "coverage_by_module": self._group_coverage_by_module(file_coverage),
                    }

                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.warning(f"Could not parse coverage data: {e}")

            threshold = self.config["blocking_gates"]["test_coverage_min"]
            is_passing = coverage_percent >= threshold

            execution_time = time.perf_counter() - start_time

            return QualityCheck(
                name="test_coverage",
                level=GateLevel.BLOCKING,
                result=GateResult.PASS if is_passing else GateResult.FAIL,
                score=coverage_percent,
                threshold=threshold,
                message=f"Test coverage: {coverage_percent:.1f}% (threshold: {threshold}%)",
                details=details,
                execution_time=execution_time,
            )

        except subprocess.TimeoutExpired:
            execution_time = time.perf_counter() - start_time
            return QualityCheck(
                name="test_coverage",
                level=GateLevel.BLOCKING,
                result=GateResult.FAIL,
                score=0.0,
                threshold=self.config["blocking_gates"]["test_coverage_min"],
                message="Test coverage check timed out (>5 minutes)",
                details={"timeout": True},
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            return QualityCheck(
                name="test_coverage",
                level=GateLevel.BLOCKING,
                result=GateResult.FAIL,
                score=0.0,
                threshold=self.config["blocking_gates"]["test_coverage_min"],
                message=f"Test coverage check failed: {e}",
                details={"error": str(e)},
                execution_time=execution_time,
            )

    def _group_coverage_by_module(self, file_coverage: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """Group coverage data by module for analysis."""
        modules = {}

        for file_path, coverage in file_coverage.items():
            # Extract module name (e.g., libs/core/file.py -> libs.core)
            parts = Path(file_path).parts
            if len(parts) >= 2:
                module = ".".join(parts[:-1])  # Exclude filename

                if module not in modules:
                    modules[module] = {"files": [], "total_coverage": 0.0, "file_count": 0}

                modules[module]["files"].append({"file": parts[-1], "coverage": coverage})
                modules[module]["total_coverage"] += coverage
                modules[module]["file_count"] += 1

        # Calculate average coverage per module
        for module_data in modules.values():
            if module_data["file_count"] > 0:
                module_data["average_coverage"] = module_data["total_coverage"] / module_data["file_count"]

        return modules

    async def _check_complexity(self) -> QualityCheck:
        """Check code complexity (WARNING gate)."""
        start_time = time.perf_counter()

        try:
            # Run radon complexity analysis
            result = subprocess.run(["radon", "cc", ".", "--json"], capture_output=True, text=True)

            avg_complexity = 0.0
            high_complexity_functions = []
            details = {"complexity_data": {}}

            if result.returncode == 0 and result.stdout:
                try:
                    complexity_data = json.loads(result.stdout)

                    complexities = []
                    for file_path, file_data in complexity_data.items():
                        for item in file_data:
                            if item.get("type") == "function":
                                complexity = item.get("complexity", 0)
                                complexities.append(complexity)

                                # Track high complexity functions
                                if complexity > self.config["warning_gates"]["code_complexity_max"]:
                                    high_complexity_functions.append({"file": file_path, "function": item.get("name", "unknown"), "complexity": complexity, "line": item.get("lineno", 0)})

                    if complexities:
                        avg_complexity = sum(complexities) / len(complexities)

                    details = {
                        "average_complexity": avg_complexity,
                        "total_functions": len(complexities),
                        "high_complexity_count": len(high_complexity_functions),
                        "high_complexity_functions": high_complexity_functions[:10],  # Top 10
                        "complexity_distribution": self._calculate_complexity_distribution(complexities),
                    }

                except json.JSONDecodeError as e:
                    self.logger.warning(f"Could not parse radon output: {e}")

            threshold = self.config["warning_gates"]["code_complexity_max"]
            is_passing = avg_complexity <= threshold

            execution_time = time.perf_counter() - start_time

            return QualityCheck(
                name="complexity",
                level=GateLevel.WARNING,
                result=GateResult.PASS if is_passing else GateResult.WARNING,
                score=max(0, 100 - (avg_complexity / threshold * 100)) if threshold > 0 else 100,
                threshold=threshold,
                message=f"Code complexity: {avg_complexity:.1f} average (threshold: {threshold})",
                details=details,
                execution_time=execution_time,
            )

        except FileNotFoundError:
            execution_time = time.perf_counter() - start_time
            self.logger.warning("Radon not found, skipping complexity check")
            return QualityCheck(
                name="complexity",
                level=GateLevel.WARNING,
                result=GateResult.SKIP,
                score=0.0,
                threshold=0,
                message="Complexity check skipped: radon not installed",
                details={"skipped": True, "reason": "radon not found"},
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            return QualityCheck(
                name="complexity",
                level=GateLevel.WARNING,
                result=GateResult.FAIL,
                score=0.0,
                threshold=self.config["warning_gates"]["code_complexity_max"],
                message=f"Complexity check failed: {e}",
                details={"error": str(e)},
                execution_time=execution_time,
            )

    def _calculate_complexity_distribution(self, complexities: List[float]) -> Dict[str, int]:
        """Calculate complexity score distribution."""
        distribution = {"1-5 (Simple)": 0, "6-10 (Moderate)": 0, "11-15 (Complex)": 0, "16+ (Very Complex)": 0}

        for complexity in complexities:
            if complexity <= 5:
                distribution["1-5 (Simple)"] += 1
            elif complexity <= 10:
                distribution["6-10 (Moderate)"] += 1
            elif complexity <= 15:
                distribution["11-15 (Complex)"] += 1
            else:
                distribution["16+ (Very Complex)"] += 1

        return distribution

    async def _check_documentation(self) -> QualityCheck:
        """Check documentation coverage (WARNING gate)."""
        start_time = time.perf_counter()

        try:
            documented_count = 0
            total_count = 0
            details = {"files_analyzed": 0, "modules": {}}

            # Analyze Python files for docstring coverage
            for py_file in Path(".").rglob("*.py"):
                if any(skip in str(py_file) for skip in ["venv", "__pycache__", ".git", "build"]):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    import ast

                    tree = ast.parse(content)

                    file_documented = 0
                    file_total = 0

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                            file_total += 1
                            total_count += 1

                            if ast.get_docstring(node):
                                file_documented += 1
                                documented_count += 1

                    if file_total > 0:
                        details["files_analyzed"] += 1
                        module_name = str(py_file.relative_to("."))
                        details["modules"][module_name] = {"documented": file_documented, "total": file_total, "coverage": (file_documented / file_total * 100) if file_total > 0 else 0}

                except Exception as e:
                    self.logger.debug(f"Error analyzing {py_file}: {e}")
                    continue

            coverage_percent = (documented_count / total_count * 100) if total_count > 0 else 0
            threshold = self.config["warning_gates"]["documentation_coverage_min"]
            is_passing = coverage_percent >= threshold

            # Find modules with low documentation
            low_doc_modules = {module: data for module, data in details["modules"].items() if data["coverage"] < 50 and data["total"] > 2}

            details.update({"total_items": total_count, "documented_items": documented_count, "coverage_percent": coverage_percent, "low_documentation_modules": low_doc_modules})

            execution_time = time.perf_counter() - start_time

            return QualityCheck(
                name="documentation",
                level=GateLevel.WARNING,
                result=GateResult.PASS if is_passing else GateResult.WARNING,
                score=coverage_percent,
                threshold=threshold,
                message=f"Documentation coverage: {coverage_percent:.1f}% (threshold: {threshold}%)",
                details=details,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.perf_counter() - start_time
            return QualityCheck(
                name="documentation",
                level=GateLevel.WARNING,
                result=GateResult.FAIL,
                score=0.0,
                threshold=self.config["warning_gates"]["documentation_coverage_min"],
                message=f"Documentation check failed: {e}",
                details={"error": str(e)},
                execution_time=execution_time,
            )

    async def _check_performance(self) -> QualityCheck:
        """Check performance benchmarks (WARNING gate)."""
        start_time = time.perf_counter()

        try:
            # Look for existing performance test results
            benchmark_files = list(Path(".").glob("**/benchmark*.json"))
            performance_score = 50.0  # Default neutral score
            details = {"benchmarks": []}

            if benchmark_files:
                try:
                    # Use the most recent benchmark file
                    latest_benchmark = max(benchmark_files, key=lambda p: p.stat().st_mtime)

                    with open(latest_benchmark) as f:
                        benchmark_data = json.load(f)

                    # Calculate performance score from benchmark data
                    if "benchmarks" in benchmark_data:
                        benchmarks = benchmark_data["benchmarks"]
                        avg_time = sum(b.get("stats", {}).get("mean", 1.0) for b in benchmarks) / len(benchmarks)

                        # Score based on execution time (lower is better)
                        if avg_time < 0.1:
                            performance_score = 100
                        elif avg_time < 0.5:
                            performance_score = 80
                        elif avg_time < 1.0:
                            performance_score = 60
                        elif avg_time < 2.0:
                            performance_score = 40
                        else:
                            performance_score = 20

                        details = {
                            "benchmark_file": str(latest_benchmark),
                            "benchmark_count": len(benchmarks),
                            "average_execution_time": avg_time,
                            "performance_score": performance_score,
                            "sample_benchmarks": benchmarks[:5],
                        }

                except Exception as e:
                    self.logger.warning(f"Could not parse benchmark data: {e}")
            else:
                # Run basic performance check if no benchmarks exist
                try:
                    # Simple startup time test
                    import_start = time.perf_counter()
                    subprocess.run([sys.executable, "-c", "import libs.core"], capture_output=True, timeout=10)
                    import_time = time.perf_counter() - import_start

                    performance_score = max(20, 100 - (import_time * 20))  # 5s = 0 score
                    details = {"test_type": "import_performance", "import_time": import_time, "performance_score": performance_score}

                except subprocess.TimeoutExpired:
                    performance_score = 10
                    details = {"test_type": "import_performance", "timeout": True}

            threshold = self.config.get("warning_gates", {}).get("performance_score_min", 50)
            is_passing = performance_score >= threshold

            execution_time = time.perf_counter() - start_time

            return QualityCheck(
                name="performance",
                level=GateLevel.WARNING,
                result=GateResult.PASS if is_passing else GateResult.WARNING,
                score=performance_score,
                threshold=threshold,
                message=f"Performance score: {performance_score:.1f}/100 (threshold: {threshold})",
                details=details,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.perf_counter() - start_time
            return QualityCheck(
                name="performance",
                level=GateLevel.WARNING,
                result=GateResult.FAIL,
                score=0.0,
                threshold=50,
                message=f"Performance check failed: {e}",
                details={"error": str(e)},
                execution_time=execution_time,
            )

    async def _check_async_adoption(self) -> QualityCheck:
        """Check async function adoption (ADVISORY gate)."""
        start_time = time.perf_counter()

        try:
            async_functions = 0
            total_functions = 0
            details = {"files_analyzed": 0, "modules": {}}

            # Analyze Python files for async function usage
            for py_file in Path(".").rglob("*.py"):
                if any(skip in str(py_file) for skip in ["venv", "__pycache__", ".git", "build"]):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    import ast

                    tree = ast.parse(content)

                    file_async = 0
                    file_total = 0

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            file_total += 1
                            total_functions += 1
                        elif isinstance(node, ast.AsyncFunctionDef):
                            file_async += 1
                            file_total += 1
                            async_functions += 1
                            total_functions += 1

                    if file_total > 0:
                        details["files_analyzed"] += 1
                        module_name = str(py_file.relative_to("."))
                        details["modules"][module_name] = {"async_functions": file_async, "total_functions": file_total, "async_percent": (file_async / file_total * 100) if file_total > 0 else 0}

                except Exception as e:
                    self.logger.debug(f"Error analyzing {py_file}: {e}")
                    continue

            async_percent = (async_functions / total_functions * 100) if total_functions > 0 else 0
            threshold = self.config["advisory_gates"]["async_adoption_target"]
            is_passing = async_percent >= threshold

            # Find modules with good async adoption
            high_async_modules = {module: data for module, data in details["modules"].items() if data["async_percent"] > 50 and data["total_functions"] > 2}

            details.update({"total_functions": total_functions, "async_functions": async_functions, "async_percent": async_percent, "high_async_modules": high_async_modules})

            execution_time = time.perf_counter() - start_time

            return QualityCheck(
                name="async_adoption",
                level=GateLevel.ADVISORY,
                result=GateResult.PASS if is_passing else GateResult.WARNING,
                score=async_percent,
                threshold=threshold,
                message=f"Async adoption: {async_percent:.1f}% (target: {threshold}%)",
                details=details,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.perf_counter() - start_time
            return QualityCheck(
                name="async_adoption",
                level=GateLevel.ADVISORY,
                result=GateResult.FAIL,
                score=0.0,
                threshold=self.config["advisory_gates"]["async_adoption_target"],
                message=f"Async adoption check failed: {e}",
                details={"error": str(e)},
                execution_time=execution_time,
            )

    async def _check_type_annotations(self) -> QualityCheck:
        """Check type annotation coverage (ADVISORY gate)."""
        start_time = time.perf_counter()

        try:
            # Run mypy for type checking analysis
            result = subprocess.run(["mypy", ".", "--show-error-codes", "--no-error-summary"], capture_output=True, text=True)

            # Analyze type annotation coverage manually
            annotated_functions = 0
            total_functions = 0
            details = {"files_analyzed": 0, "modules": {}}

            for py_file in Path(".").rglob("*.py"):
                if any(skip in str(py_file) for skip in ["venv", "__pycache__", ".git", "build"]):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    import ast

                    tree = ast.parse(content)

                    file_annotated = 0
                    file_total = 0

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            file_total += 1
                            total_functions += 1

                            # Check if function has type annotations
                            has_annotations = node.returns is not None or any(arg.annotation is not None for arg in node.args.args)

                            if has_annotations:
                                file_annotated += 1
                                annotated_functions += 1

                    if file_total > 0:
                        details["files_analyzed"] += 1
                        module_name = str(py_file.relative_to("."))
                        details["modules"][module_name] = {
                            "annotated_functions": file_annotated,
                            "total_functions": file_total,
                            "annotation_percent": (file_annotated / file_total * 100) if file_total > 0 else 0,
                        }

                except Exception as e:
                    self.logger.debug(f"Error analyzing {py_file}: {e}")
                    continue

            annotation_percent = (annotated_functions / total_functions * 100) if total_functions > 0 else 0
            threshold = self.config["advisory_gates"]["type_annotation_coverage"]
            is_passing = annotation_percent >= threshold

            # Count mypy errors for additional context
            mypy_errors = len([line for line in result.stdout.split("\n") if ":" in line and "error:" in line])

            details.update(
                {"total_functions": total_functions, "annotated_functions": annotated_functions, "annotation_percent": annotation_percent, "mypy_errors": mypy_errors, "mypy_available": True}
            )

            execution_time = time.perf_counter() - start_time

            return QualityCheck(
                name="type_annotations",
                level=GateLevel.ADVISORY,
                result=GateResult.PASS if is_passing else GateResult.WARNING,
                score=annotation_percent,
                threshold=threshold,
                message=f"Type annotations: {annotation_percent:.1f}% (target: {threshold}%)",
                details=details,
                execution_time=execution_time,
            )

        except FileNotFoundError:
            execution_time = time.perf_counter() - start_time
            self.logger.warning("MyPy not found, using basic type annotation check")

            # Basic fallback without mypy
            return QualityCheck(
                name="type_annotations",
                level=GateLevel.ADVISORY,
                result=GateResult.SKIP,
                score=0.0,
                threshold=0,
                message="Type annotation check skipped: mypy not installed",
                details={"skipped": True, "reason": "mypy not found"},
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            return QualityCheck(
                name="type_annotations",
                level=GateLevel.ADVISORY,
                result=GateResult.FAIL,
                score=0.0,
                threshold=self.config["advisory_gates"]["type_annotation_coverage"],
                message=f"Type annotation check failed: {e}",
                details={"error": str(e)},
                execution_time=execution_time,
            )

    def _compile_results(self, execution_time: float) -> QualityGateResults:
        """Compile individual check results into overall results."""
        blocking_failures = len([r for r in self.results if r.level == GateLevel.BLOCKING and r.result == GateResult.FAIL])
        warning_failures = len([r for r in self.results if r.level == GateLevel.WARNING and r.result == GateResult.WARNING])

        # Determine overall result
        if blocking_failures > 0:
            overall_result = GateResult.FAIL
        elif warning_failures > 0:
            overall_result = GateResult.WARNING
        else:
            overall_result = GateResult.PASS

        # Calculate summary statistics
        summary = {
            "overall_score": self._calculate_overall_score(),
            "blocking_gates": {
                "total": len([r for r in self.results if r.level == GateLevel.BLOCKING]),
                "passed": len([r for r in self.results if r.level == GateLevel.BLOCKING and r.result == GateResult.PASS]),
                "failed": blocking_failures,
            },
            "warning_gates": {
                "total": len([r for r in self.results if r.level == GateLevel.WARNING]),
                "passed": len([r for r in self.results if r.level == GateLevel.WARNING and r.result == GateResult.PASS]),
                "failed": warning_failures,
            },
            "advisory_gates": {
                "total": len([r for r in self.results if r.level == GateLevel.ADVISORY]),
                "passed": len([r for r in self.results if r.level == GateLevel.ADVISORY and r.result == GateResult.PASS]),
                "failed": len([r for r in self.results if r.level == GateLevel.ADVISORY and r.result == GateResult.WARNING]),
            },
        }

        return QualityGateResults(
            overall_result=overall_result,
            blocking_failures=blocking_failures,
            warning_failures=warning_failures,
            total_checks=len(self.results),
            execution_time=execution_time,
            checks=self.results,
            summary=summary,
        )

    def _calculate_overall_score(self) -> float:
        """Calculate weighted overall quality score."""
        if not self.results:
            return 0.0

        # Weighted scoring: blocking gates count more
        weights = {GateLevel.BLOCKING: 0.5, GateLevel.WARNING: 0.3, GateLevel.ADVISORY: 0.2}

        weighted_score = 0.0
        total_weight = 0.0

        for result in self.results:
            if result.result != GateResult.SKIP:
                weight = weights.get(result.level, 0.1)
                score = result.score if result.result != GateResult.FAIL else 0.0
                weighted_score += score * weight
                total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def generate_report(self, results: QualityGateResults, format: str = "markdown") -> str:
        """Generate quality gates report."""
        if format == "json":
            return json.dumps(asdict(results), indent=2, default=str)

        # Markdown report
        report = f"""# 🛡️ Quality Gates Report

**Overall Result**: {self._format_result_emoji(results.overall_result)} {results.overall_result.value.upper()}
**Overall Score**: {results.summary["overall_score"]:.1f}/100
**Execution Time**: {results.execution_time:.2f}s

## 📊 Summary

| Gate Level | Total | Passed | Failed |
|------------|-------|--------|--------|
| 🔴 **Blocking** | {results.summary["blocking_gates"]["total"]} | {results.summary["blocking_gates"]["passed"]} | {results.summary["blocking_gates"]["failed"]} |
| 🟡 **Warning** | {results.summary["warning_gates"]["total"]} | {results.summary["warning_gates"]["passed"]} | {results.summary["warning_gates"]["failed"]} |
| 🟢 **Advisory** | {results.summary["advisory_gates"]["total"]} | {results.summary["advisory_gates"]["passed"]} | {results.summary["advisory_gates"]["failed"]} |

## 🔍 Detailed Results

"""

        # Group results by level
        for level in [GateLevel.BLOCKING, GateLevel.WARNING, GateLevel.ADVISORY]:
            level_results = [r for r in results.checks if r.level == level]
            if not level_results:
                continue

            level_emoji = {"blocking": "🔴", "warning": "🟡", "advisory": "🟢"}[level.value]
            report += f"### {level_emoji} {level.value.title()} Gates\n\n"

            for result in level_results:
                result_emoji = self._format_result_emoji(result.result)
                report += f"#### {result_emoji} {result.name.replace('_', ' ').title()}\n"
                report += f"- **Result**: {result.result.value}\n"
                report += f"- **Score**: {result.score:.1f}/{result.threshold}\n"
                report += f"- **Message**: {result.message}\n"
                report += f"- **Execution Time**: {result.execution_time:.3f}s\n"

                if result.details and any(key not in ["error", "skipped"] for key in result.details.keys()):
                    report += f"- **Details**: {self._format_details_summary(result.details)}\n"

                report += "\n"

        report += """
## 🎯 Recommendations

"""

        if results.blocking_failures > 0:
            report += "### 🚨 Critical Actions Required\n"
            for result in results.checks:
                if result.level == GateLevel.BLOCKING and result.result == GateResult.FAIL:
                    report += f"- **{result.name}**: {result.message}\n"
            report += "\n"

        warning_issues = [r for r in results.checks if r.level == GateLevel.WARNING and r.result == GateResult.WARNING]
        if warning_issues:
            report += "### ⚠️ Improvements Recommended\n"
            for result in warning_issues:
                report += f"- **{result.name}**: {result.message}\n"
            report += "\n"

        advisory_issues = [r for r in results.checks if r.level == GateLevel.ADVISORY and r.result == GateResult.WARNING]
        if advisory_issues:
            report += "### 💡 Best Practice Suggestions\n"
            for result in advisory_issues:
                report += f"- **{result.name}**: {result.message}\n"
            report += "\n"

        report += """---
*Generated by Yesman-Claude Quality Gates System*
"""

        return report

    def _format_result_emoji(self, result: GateResult) -> str:
        """Format result with appropriate emoji."""
        emoji_map = {GateResult.PASS: "✅", GateResult.FAIL: "❌", GateResult.WARNING: "⚠️", GateResult.SKIP: "⏭️"}
        return emoji_map.get(result, "❓")

    def _format_details_summary(self, details: Dict[str, Any]) -> str:
        """Format details for summary display."""
        if not details:
            return "No additional details"

        summary_items = []
        for key, value in details.items():
            if key in ["error", "skipped"]:
                continue

            if isinstance(value, (int, float)):
                summary_items.append(f"{key}: {value}")
            elif isinstance(value, dict) and len(value) < 5:
                summary_items.append(f"{key}: {len(value)} items")
            elif isinstance(value, list) and len(value) < 10:
                summary_items.append(f"{key}: {len(value)} items")

        return ", ".join(summary_items) if summary_items else "See full report for details"

    async def run_essential_gates(self) -> QualityGateResults:
        """
        Run essential quality gates for fast pre-commit checks.

        Returns:
            Essential quality gate results (blocking gates only)
        """
        self.logger.info("🛡️ Running Essential Quality Gates (pre-commit)...")
        start_time = time.perf_counter()

        self.results = []

        # Run only essential blocking checks
        essential_checks = ["linting", "security"]
        check_tasks = []

        if "linting" in essential_checks:
            check_tasks.append(self._check_linting())
        if "security" in essential_checks:
            check_tasks.append(self._check_security())

        # Execute essential checks
        for check_task in check_tasks:
            try:
                result = await check_task
                self.results.append(result)
            except Exception as e:
                self.logger.error(f"Error running essential check: {e}")
                self.results.append(
                    QualityCheck(
                        name="essential_check_error",
                        level=GateLevel.BLOCKING,
                        result=GateResult.FAIL,
                        score=0.0,
                        threshold=100.0,
                        message=f"Essential check failed: {e}",
                        details={"error": str(e)},
                        execution_time=0.0,
                    )
                )

        execution_time = time.perf_counter() - start_time
        return self._compile_results(execution_time)

    async def run_comprehensive_gates(self) -> QualityGateResults:
        """
        Run comprehensive quality gates for pre-push validation.

        Returns:
            Complete quality gate results (all levels)
        """
        # This just delegates to run_all_gates for comprehensive checks
        return await self.run_all_gates()


async def main():
    """Main entry point for quality gates checker."""
    import argparse

    parser = argparse.ArgumentParser(description="Yesman-Claude Quality Gates Checker")
    parser.add_argument("--config", type=Path, help="Path to quality gates configuration file")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--output", type=Path, help="Output file path")
    parser.add_argument("--fail-on-warning", action="store_true", help="Fail on warning-level issues")

    args = parser.parse_args()

    # Initialize quality gates checker
    checker = QualityGatesChecker(config_path=args.config)

    # Run all quality gates
    results = await checker.run_all_gates()

    # Generate report
    report = checker.generate_report(results, format=args.format)

    # Output report
    if args.output:
        args.output.write_text(report)
        print(f"Quality gates report written to {args.output}")
    else:
        print(report)

    # Determine exit code
    exit_code = 0
    if results.overall_result == GateResult.FAIL:
        exit_code = 1
    elif results.overall_result == GateResult.WARNING and args.fail_on_warning:
        exit_code = 1

    if exit_code == 0:
        print(f"\n✅ Quality gates passed! Overall score: {results.summary['overall_score']:.1f}/100")
    else:
        print(f"\n❌ Quality gates failed! Overall score: {results.summary['overall_score']:.1f}/100")
        if results.blocking_failures > 0:
            print(f"   Blocking failures: {results.blocking_failures}")
        if results.warning_failures > 0:
            print(f"   Warning failures: {results.warning_failures}")

    sys.exit(exit_code)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
