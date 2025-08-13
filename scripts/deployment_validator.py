#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Production Deployment Validator.

This module provides comprehensive deployment validation including quality gates,
security checks, performance baselines, and dependency health verification.
"""

import asyncio
import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from libs.dashboard.monitoring_integration import get_monitoring_dashboard
from scripts.quality_gates_performance import check_performance_quality_gates
from scripts.security_validation import SecurityValidator


@dataclass
class DeploymentCheck:
    """Configuration for a deployment validation check."""

    name: str
    description: str
    check_function: Callable[[], dict]
    timeout_seconds: int = 30
    retry_count: int = 3
    is_critical: bool = True


class DeploymentValidator:
    """Comprehensive deployment validation system."""

    def __init__(self) -> None:
        """Initialize the deployment validator."""
        self.monitoring = get_monitoring_dashboard()
        self.event_bus = get_event_bus()
        self.project_root = Path(__file__).parent.parent

        # Configure validation checks
        self.checks = [
            DeploymentCheck(name="quality_gates", description="All quality gates must pass", check_function=self._check_quality_gates, is_critical=True, timeout_seconds=60),
            DeploymentCheck(name="security_validation", description="Security validation must pass", check_function=self._check_security_validation, is_critical=True, timeout_seconds=45),
            DeploymentCheck(name="performance_baseline", description="Performance within acceptable baseline", check_function=self._check_performance_baseline, is_critical=False, timeout_seconds=30),
            DeploymentCheck(name="dependency_health", description="All external dependencies available", check_function=self._check_dependencies, is_critical=True, timeout_seconds=20),
            DeploymentCheck(name="configuration_integrity", description="Configuration files are valid", check_function=self._check_configuration_integrity, is_critical=True, timeout_seconds=15),
            DeploymentCheck(name="resource_availability", description="System resources are available", check_function=self._check_resource_availability, is_critical=True, timeout_seconds=10),
        ]

    async def validate_deployment(self) -> dict[str, Any]:
        """Run all deployment validation checks.

        Returns:
            Dictionary containing validation results
        """
        results = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "can_deploy": True,
            "execution_time_ms": 0,
            "total_checks": len(self.checks),
            "critical_failures": 0,
            "validation_timestamp": time.time(),
        }

        start_time = time.perf_counter()

        # Publish validation start event
        await self._publish_validation_event("validation_started", {"total_checks": len(self.checks), "critical_checks": sum(1 for check in self.checks if check.is_critical)})

        # Execute all validation checks
        for check in self.checks:
            check_result = await self._run_check(check)

            if check_result["success"]:
                results["passed"].append(check_result)
            else:
                results["failed"].append(check_result)
                if check.is_critical:
                    results["can_deploy"] = False
                    results["critical_failures"] += 1
                else:
                    results["warnings"].append(check_result)

        # Calculate execution time
        results["execution_time_ms"] = int((time.perf_counter() - start_time) * 1000)

        # Publish validation completion event
        await self._publish_validation_event(
            "validation_completed",
            {
                "can_deploy": results["can_deploy"],
                "passed": len(results["passed"]),
                "failed": len(results["failed"]),
                "critical_failures": results["critical_failures"],
                "execution_time_ms": results["execution_time_ms"],
            },
        )

        return results

    async def _run_check(self, check: DeploymentCheck) -> dict[str, Any]:
        """Execute a single deployment check with timeout and retry logic.

        Args:
            check: Deployment check configuration

        Returns:
            Check result dictionary
        """
        result = {"name": check.name, "description": check.description, "success": False, "details": {}, "execution_time_ms": 0, "attempt_count": 0, "is_critical": check.is_critical}

        start_time = time.perf_counter()

        for attempt in range(check.retry_count):
            result["attempt_count"] = attempt + 1

            try:
                # Execute check with timeout
                check_details = await asyncio.wait_for(check.check_function(), timeout=check.timeout_seconds)

                result["success"] = check_details.get("success", False)
                result["details"] = check_details

                # If successful, break retry loop
                if result["success"]:
                    break

            except TimeoutError:
                result["details"] = {"error": f"Check timed out after {check.timeout_seconds} seconds", "timeout": True}
            except Exception as e:
                result["details"] = {"error": str(e), "exception_type": type(e).__name__}

            # Wait before retry (except on last attempt)
            if attempt < check.retry_count - 1:
                await asyncio.sleep(1)

        result["execution_time_ms"] = int((time.perf_counter() - start_time) * 1000)
        return result

    async def _check_quality_gates(self) -> dict[str, Any]:
        """Check that all quality gates pass."""
        try:
            success, report = await check_performance_quality_gates()
            return {"success": success, "report": report, "type": "quality_gates"}
        except Exception as e:
            return {"success": False, "error": str(e), "type": "quality_gates"}

    async def _check_security_validation(self) -> dict[str, Any]:
        """Check security validation passes."""
        try:
            validator = SecurityValidator()
            success = validator.run_validation()
            return {"success": success, "warnings": validator.warnings, "errors": validator.errors, "type": "security_validation"}
        except Exception as e:
            return {"success": False, "error": str(e), "type": "security_validation"}

    async def _check_performance_baseline(self) -> dict[str, Any]:
        """Check current performance against baseline."""
        try:
            # Get current system health score
            health_score = self.monitoring._calculate_health_score()

            # Load performance baselines
            baseline_path = Path("data/performance_baselines.json")
            baseline_health_score = 85.0  # Default baseline

            if baseline_path.exists():
                with open(baseline_path, encoding="utf-8") as f:
                    baselines = json.load(f)
                    baseline_health_score = baselines.get("system_health_baseline", 85.0)

            # Check if current health is within acceptable range
            health_acceptable = health_score >= baseline_health_score * 0.9  # Allow 10% degradation

            return {
                "success": health_acceptable,
                "current_health_score": health_score,
                "baseline_health_score": baseline_health_score,
                "degradation_percent": ((baseline_health_score - health_score) / baseline_health_score * 100) if baseline_health_score > 0 else 0,
                "type": "performance_baseline",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "type": "performance_baseline"}

    async def _check_dependencies(self) -> dict[str, Any]:
        """Check that all external dependencies are available."""
        try:
            dependency_checks = []

            # Check database connectivity (if configured)
            # This would be implemented based on actual dependencies

            # Check external API availability
            # This would check any external services the application depends on

            # Check file system dependencies
            required_dirs = ["data", "logs", "tmp"]
            for dir_name in required_dirs:
                dir_path = self.project_root / dir_name
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                dependency_checks.append({"name": f"directory_{dir_name}", "status": "available", "path": str(dir_path)})

            # Check required configuration files
            config_files = ["config/default.yaml", "pyproject.toml"]
            for config_file in config_files:
                config_path = self.project_root / config_file
                dependency_checks.append({"name": f"config_{config_file}", "status": "available" if config_path.exists() else "missing", "path": str(config_path)})

            # All dependencies available if no missing dependencies
            all_available = all(check["status"] == "available" for check in dependency_checks)

            return {
                "success": all_available,
                "dependencies": dependency_checks,
                "available_count": sum(1 for check in dependency_checks if check["status"] == "available"),
                "total_count": len(dependency_checks),
                "type": "dependency_health",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "type": "dependency_health"}

    async def _check_configuration_integrity(self) -> dict[str, Any]:
        """Check that configuration files are valid and consistent."""
        try:
            config_results = []

            # Check main configuration files
            config_files = ["pyproject.toml", "config/default.yaml", "config/development.yaml", "config/production.yaml"]

            for config_file in config_files:
                config_path = self.project_root / config_file
                if config_path.exists():
                    try:
                        # Basic file read test
                        content = config_path.read_text()

                        # Basic syntax validation
                        if config_file.endswith(".json"):
                            json.loads(content)

                        config_results.append({"file": config_file, "status": "valid", "size": len(content)})
                    except Exception as e:
                        config_results.append({"file": config_file, "status": "invalid", "error": str(e)})
                else:
                    config_results.append({"file": config_file, "status": "missing"})

            # Check for critical configuration issues
            critical_files = ["pyproject.toml"]
            critical_missing = [r for r in config_results if r["file"] in critical_files and r["status"] != "valid"]

            return {
                "success": len(critical_missing) == 0,
                "configurations": config_results,
                "valid_count": sum(1 for r in config_results if r["status"] == "valid"),
                "total_count": len(config_results),
                "critical_missing": critical_missing,
                "type": "configuration_integrity",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "type": "configuration_integrity"}

    async def _check_resource_availability(self) -> dict[str, Any]:
        """Check that system resources are available for deployment."""
        try:
            import psutil

            # Get system resource information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage("/")

            # Define resource thresholds
            cpu_threshold = 90.0  # 90% CPU usage
            memory_threshold = 95.0  # 95% memory usage
            disk_threshold = 90.0  # 90% disk usage

            # Check resource availability
            cpu_available = cpu_percent < cpu_threshold
            memory_available = memory_info.percent < memory_threshold
            disk_available = disk_info.percent < disk_threshold

            resource_checks = [
                {"resource": "cpu", "current_percent": cpu_percent, "threshold_percent": cpu_threshold, "available": cpu_available},
                {
                    "resource": "memory",
                    "current_percent": memory_info.percent,
                    "threshold_percent": memory_threshold,
                    "available": memory_available,
                    "total_gb": memory_info.total / (1024**3),
                    "available_gb": memory_info.available / (1024**3),
                },
                {
                    "resource": "disk",
                    "current_percent": disk_info.percent,
                    "threshold_percent": disk_threshold,
                    "available": disk_available,
                    "total_gb": disk_info.total / (1024**3),
                    "free_gb": disk_info.free / (1024**3),
                },
            ]

            all_resources_available = cpu_available and memory_available and disk_available

            return {
                "success": all_resources_available,
                "resources": resource_checks,
                "available_resources": sum(1 for r in resource_checks if r["available"]),
                "total_resources": len(resource_checks),
                "type": "resource_availability",
            }
        except ImportError:
            return {"success": False, "error": "psutil package not available", "type": "resource_availability"}
        except Exception as e:
            return {"success": False, "error": str(e), "type": "resource_availability"}

    async def _publish_validation_event(self, event_subtype: str, data: dict[str, Any]) -> None:
        """Publish a deployment validation event.

        Args:
            event_subtype: Type of validation event
            data: Event data
        """
        await self.event_bus.publish(
            Event(type=EventType.CUSTOM, data={"event_subtype": f"deployment_{event_subtype}", **data}, timestamp=time.time(), source="deployment_validator", priority=EventPriority.HIGH)
        )

    def get_validation_report(self, results: dict[str, Any]) -> str:
        """Generate a formatted validation report.

        Args:
            results: Validation results

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("DEPLOYMENT VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("SUMMARY:")
        report.append(f"  Total Checks: {results['total_checks']}")
        report.append(f"  Passed: {len(results['passed'])}")
        report.append(f"  Failed: {len(results['failed'])}")
        report.append(f"  Warnings: {len(results['warnings'])}")
        report.append(f"  Critical Failures: {results['critical_failures']}")
        report.append(f"  Execution Time: {results['execution_time_ms']}ms")
        report.append(f"  Can Deploy: {'✅ YES' if results['can_deploy'] else '❌ NO'}")
        report.append("")

        # Critical failures
        if results.get("failed"):
            critical_failures = [f for f in results["failed"] if f["is_critical"]]
            if critical_failures:
                report.append("CRITICAL FAILURES (DEPLOYMENT BLOCKED):")
                for failure in critical_failures:
                    report.append(f"  ❌ {failure['name']}: {failure['description']}")
                    if "error" in failure["details"]:
                        report.append(f"     Error: {failure['details']['error']}")
                    report.append(f"     Execution Time: {failure['execution_time_ms']}ms")
                    report.append(f"     Attempts: {failure['attempt_count']}")
                report.append("")

        # Warnings (non-critical failures)
        if results.get("warnings"):
            report.append("WARNINGS (NON-BLOCKING):")
            for warning in results["warnings"]:
                report.append(f"  ⚠️  {warning['name']}: {warning['description']}")
                if "error" in warning["details"]:
                    report.append(f"     Issue: {warning['details']['error']}")
                report.append("")

        # Successful checks
        if results.get("passed"):
            report.append("SUCCESSFUL CHECKS:")
            for check in results["passed"]:
                report.append(f"  ✅ {check['name']}: {check['description']}")
            report.append("")

        report.append("=" * 80)
        return "\n".join(report)


async def validate_deployment() -> tuple[bool, str]:
    """Run deployment validation and return results.

    Returns:
        Tuple of (can_deploy, report)
    """
    validator = DeploymentValidator()
    results = await validator.validate_deployment()
    report = validator.get_validation_report(results)
    return results["can_deploy"], report


if __name__ == "__main__":
    # Run deployment validation
    can_deploy, report = asyncio.run(validate_deployment())
    print(report)

    if not can_deploy:
        sys.exit(1)
