#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Canary Deployment Management System.

This module provides comprehensive canary deployment capabilities including
traffic management, automated monitoring, performance comparison, and
automatic rollback on failure detection.
"""


class CanaryDeploymentError(Exception):
    """Base exception for canary deployment failures."""

    def __init__(self, message: str = "Canary deployment failed", cause: Exception = None) -> None:
        if cause:
            full_message = f"{message}: {cause}"
        else:
            full_message = message
        super().__init__(full_message)
        self.__cause__ = cause


class DeploymentAlreadyActiveError(CanaryDeploymentError):
    """Exception raised when attempting to start a deployment while another is active."""

    def __init__(self, deployment_id: str = None) -> None:
        if deployment_id:
            super().__init__(f"Canary deployment {deployment_id} is already active")
        else:
            super().__init__("A canary deployment is already active")


class DeploymentValidationError(CanaryDeploymentError):
    """Exception raised when deployment validation fails."""
    pass


import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from libs.dashboard.monitoring_integration import get_monitoring_dashboard

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Status of a canary deployment."""

    PREPARING = "preparing"
    ACTIVE = "active"
    MONITORING = "monitoring"
    PROMOTING = "promoting"
    ROLLING_BACK = "rolling_back"
    COMPLETED = "completed"
    FAILED = "failed"


class RollbackReason(Enum):
    """Reasons for automatic rollback."""

    HIGH_ERROR_RATE = "high_error_rate"
    RESPONSE_TIME_REGRESSION = "response_time_regression"
    HEALTH_SCORE_DEGRADATION = "health_score_degradation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MANUAL_TRIGGER = "manual_trigger"
    TIMEOUT = "timeout"


@dataclass
class CanaryConfig:
    """Configuration for canary deployment."""

    traffic_percentage: int = 10
    duration_minutes: int = 10
    success_threshold: float = 99.0  # 99% success rate required
    max_error_rate: float = 1.0  # 1% error rate max
    max_response_time_regression: float = 20.0  # 20% max regression
    rollback_on_failure: bool = True
    metrics_check_interval: int = 30  # seconds
    health_score_threshold: float = 70.0
    auto_promote: bool = True

    # Advanced configuration
    ramp_up_steps: list[int] = field(default_factory=lambda: [5, 10, 25, 50])
    ramp_up_interval_minutes: int = 5
    baseline_collection_minutes: int = 5


@dataclass
class CanaryMetrics:
    """Metrics collected during canary deployment."""

    timestamp: float
    success_rate: float
    error_rate: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    health_score: float
    active_connections: int
    resource_utilization: dict[str, float]
    custom_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanaryDeployment:
    """Active canary deployment information."""

    deployment_id: str
    config: CanaryConfig
    status: DeploymentStatus
    start_time: float
    baseline_metrics: CanaryMetrics | None = None
    current_metrics: CanaryMetrics | None = None
    traffic_percentage: int = 0
    rollback_reason: RollbackReason | None = None
    completion_time: float | None = None
    promotion_time: float | None = None
    metrics_history: list[CanaryMetrics] = field(default_factory=list)


class CanaryDeploymentManager:
    """Manages canary deployments with automated monitoring and rollback."""

    def __init__(self, config: CanaryConfig | None = None) -> None:
        """Initialize the canary deployment manager.

        Args:
            config: Canary deployment configuration
        """
        self.config = config or CanaryConfig()
        self.monitoring = get_monitoring_dashboard()
        self.event_bus = get_event_bus()

        # Active deployment tracking
        self.active_deployment: CanaryDeployment | None = None
        self.deployment_history: list[CanaryDeployment] = []

        # Background tasks
        self._monitoring_task: asyncio.Task | None = None
        self._ramp_up_task: asyncio.Task | None = None

        # Traffic management (mock implementation - would integrate with actual load balancer)
        self._current_traffic_percentage = 0

        # Data persistence
        self.deployment_data_path = Path("data/canary_deployments.json")
        self._load_deployment_history()

    async def start_canary_deployment(self, deployment_id: str, config: CanaryConfig | None = None) -> dict[str, Any]:
        """Start a new canary deployment with monitoring.

        Args:
            deployment_id: Unique identifier for the deployment
            config: Optional deployment-specific configuration

        Returns:
            Dictionary with deployment start results
        """
        if self.active_deployment:
            raise DeploymentAlreadyActiveError(self.active_deployment.deployment_id)

        deployment_config = config or self.config

        # Create new deployment
        deployment = CanaryDeployment(deployment_id=deployment_id, config=deployment_config, status=DeploymentStatus.PREPARING, start_time=time.time())

        self.active_deployment = deployment

        try:
            # Capture baseline metrics
            await self._publish_deployment_event(
                "deployment_started",
                {
                    "deployment_id": deployment_id,
                    "config": {
                        "traffic_percentage": deployment_config.traffic_percentage,
                        "duration_minutes": deployment_config.duration_minutes,
                        "success_threshold": deployment_config.success_threshold,
                        "max_error_rate": deployment_config.max_error_rate,
                    },
                },
            )

            # Collect baseline metrics
            deployment.baseline_metrics = await self._capture_baseline_metrics()

            # Start with initial traffic percentage
            deployment.status = DeploymentStatus.ACTIVE
            deployment.traffic_percentage = deployment_config.traffic_percentage
            await self._configure_canary_traffic(deployment_config.traffic_percentage)

            # Start monitoring task
            self._monitoring_task = asyncio.create_task(self._monitor_canary_deployment(deployment))

            # Start ramp-up task if configured
            if deployment_config.ramp_up_steps:
                self._ramp_up_task = asyncio.create_task(self._ramp_up_traffic(deployment))

            result = {
                "deployment_id": deployment_id,
                "status": deployment.status.value,
                "canary_percentage": deployment.traffic_percentage,
                "monitoring_started": True,
                "baseline_captured": deployment.baseline_metrics is not None,
                "expected_completion_time": time.time() + (deployment_config.duration_minutes * 60),
                "config": {
                    "success_threshold": deployment_config.success_threshold,
                    "max_error_rate": deployment_config.max_error_rate,
                    "check_interval": deployment_config.metrics_check_interval,
                    "auto_promote": deployment_config.auto_promote,
                },
            }

            # Save deployment state
            await self._save_deployment_state()

            return result

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.completion_time = time.time()
            self.active_deployment = None

            await self._publish_deployment_event("deployment_failed", {"deployment_id": deployment_id, "error": str(e), "duration_seconds": deployment.completion_time - deployment.start_time})

            raise CanaryDeploymentError(cause=e) from e

    async def _capture_baseline_metrics(self) -> CanaryMetrics:
        """Capture baseline metrics before canary deployment.

        Returns:
            Baseline metrics
        """
        # Wait briefly for stable baseline
        await asyncio.sleep(2)

        try:
            # Get current system metrics
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            system_metrics = await self._get_system_resource_metrics()

            # Calculate aggregated metrics
            avg_response_time = 0.0
            success_rate = 100.0
            error_rate = 0.0

            # Extract metrics from monitoring dashboard
            if dashboard_data.get("metrics"):
                total_samples = 0

                for component, metrics in dashboard_data["metrics"].items():
                    if "response_time" in metrics:
                        rt_data = metrics["response_time"]
                        avg_response_time += rt_data.get("average", 0) * rt_data.get("samples", 1)
                        total_samples += rt_data.get("samples", 1)

                    if "error_rate" in metrics:
                        error_rate = max(error_rate, metrics["error_rate"].get("average", 0))

                if total_samples > 0:
                    avg_response_time /= total_samples

                success_rate = max(0, 100.0 - error_rate)

            return CanaryMetrics(
                timestamp=time.time(),
                success_rate=success_rate,
                error_rate=error_rate,
                avg_response_time_ms=avg_response_time,
                p95_response_time_ms=avg_response_time * 1.2,  # Estimated
                p99_response_time_ms=avg_response_time * 1.5,  # Estimated
                health_score=dashboard_data.get("health_score", 100.0),
                active_connections=system_metrics.get("connections", 0),
                resource_utilization={
                    "cpu_percent": system_metrics.get("cpu_percent", 0),
                    "memory_percent": system_metrics.get("memory_percent", 0),
                    "disk_percent": system_metrics.get("disk_percent", 0),
                },
            )
        except Exception:
            # Return default baseline if metrics collection fails
            return CanaryMetrics(
                timestamp=time.time(),
                success_rate=100.0,
                error_rate=0.0,
                avg_response_time_ms=50.0,
                p95_response_time_ms=75.0,
                p99_response_time_ms=100.0,
                health_score=100.0,
                active_connections=0,
                resource_utilization={"cpu_percent": 10, "memory_percent": 20, "disk_percent": 30},
            )

    async def _configure_canary_traffic(self, percentage: int) -> None:
        """Configure traffic routing for canary deployment.

        Args:
            percentage: Percentage of traffic to route to canary
        """
        # Mock implementation - in real deployment this would integrate with:
        # - Load balancers (HAProxy, NGINX, ALB, etc.)
        # - Service mesh (Istio, Linkerd, Consul Connect)
        # - Ingress controllers (NGINX Ingress, Traefik, etc.)

        self._current_traffic_percentage = percentage

        await self._publish_deployment_event(
            "traffic_configured", {"traffic_percentage": percentage, "previous_percentage": getattr(self, "_previous_traffic_percentage", 0), "configuration_time": time.time()}
        )

        self._previous_traffic_percentage = percentage

        # Simulate configuration delay
        await asyncio.sleep(0.5)

    async def _monitor_canary_deployment(self, deployment: CanaryDeployment) -> None:
        """Monitor canary deployment and handle automatic rollback.

        Args:
            deployment: The deployment to monitor
        """
        deployment.status = DeploymentStatus.MONITORING
        end_time = time.time() + (deployment.config.duration_minutes * 60)

        try:
            while time.time() < end_time and deployment.status == DeploymentStatus.MONITORING:
                # Collect current metrics
                current_metrics = await self._collect_current_metrics()
                deployment.current_metrics = current_metrics
                deployment.metrics_history.append(current_metrics)

                # Evaluate canary health
                health_evaluation = await self._evaluate_canary_health(deployment, current_metrics)

                # Publish monitoring update
                await self._publish_deployment_event(
                    "monitoring_update",
                    {
                        "deployment_id": deployment.deployment_id,
                        "metrics": {
                            "success_rate": current_metrics.success_rate,
                            "error_rate": current_metrics.error_rate,
                            "avg_response_time_ms": current_metrics.avg_response_time_ms,
                            "health_score": current_metrics.health_score,
                        },
                        "health_evaluation": health_evaluation,
                        "traffic_percentage": deployment.traffic_percentage,
                        "time_remaining_minutes": (end_time - time.time()) / 60,
                    },
                )

                # Check for rollback conditions
                if not health_evaluation["healthy"]:
                    await self._rollback_deployment(deployment, health_evaluation["reason"])
                    return

                # Save current state
                await self._save_deployment_state()

                # Wait before next check
                await asyncio.sleep(deployment.config.metrics_check_interval)

            # If we reach here, canary monitoring completed successfully
            if deployment.config.auto_promote and deployment.status == DeploymentStatus.MONITORING:
                await self._promote_canary_deployment(deployment)
            else:
                deployment.status = DeploymentStatus.COMPLETED
                deployment.completion_time = time.time()
                await self._publish_deployment_event(
                    "monitoring_completed",
                    {
                        "deployment_id": deployment.deployment_id,
                        "requires_manual_promotion": not deployment.config.auto_promote,
                        "duration_minutes": (deployment.completion_time - deployment.start_time) / 60,
                    },
                )

        except asyncio.CancelledError:
            deployment.status = DeploymentStatus.FAILED
            deployment.completion_time = time.time()
            await self._publish_deployment_event("monitoring_cancelled", {"deployment_id": deployment.deployment_id})
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.completion_time = time.time()
            await self._publish_deployment_event("monitoring_error", {"deployment_id": deployment.deployment_id, "error": str(e)})

    async def _collect_current_metrics(self) -> CanaryMetrics:
        """Collect current system metrics during canary deployment.

        Returns:
            Current metrics
        """
        try:
            # Get monitoring dashboard data
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            system_metrics = await self._get_system_resource_metrics()

            # Calculate current performance metrics
            avg_response_time = 0.0
            success_rate = 100.0
            error_rate = 0.0

            if dashboard_data.get("metrics"):
                total_samples = 0

                for component, metrics in dashboard_data["metrics"].items():
                    if "response_time" in metrics:
                        rt_data = metrics["response_time"]
                        avg_response_time += rt_data.get("average", 0) * rt_data.get("samples", 1)
                        total_samples += rt_data.get("samples", 1)

                    if "error_rate" in metrics:
                        error_rate = max(error_rate, metrics["error_rate"].get("average", 0))

                if total_samples > 0:
                    avg_response_time /= total_samples

                success_rate = max(0, 100.0 - error_rate)

            return CanaryMetrics(
                timestamp=time.time(),
                success_rate=success_rate,
                error_rate=error_rate,
                avg_response_time_ms=avg_response_time,
                p95_response_time_ms=avg_response_time * 1.2,
                p99_response_time_ms=avg_response_time * 1.5,
                health_score=dashboard_data.get("health_score", 100.0),
                active_connections=system_metrics.get("connections", 0),
                resource_utilization={
                    "cpu_percent": system_metrics.get("cpu_percent", 0),
                    "memory_percent": system_metrics.get("memory_percent", 0),
                    "disk_percent": system_metrics.get("disk_percent", 0),
                },
            )
        except Exception:
            # Return degraded metrics if collection fails
            return CanaryMetrics(
                timestamp=time.time(),
                success_rate=0.0,
                error_rate=100.0,
                avg_response_time_ms=5000.0,
                p95_response_time_ms=10000.0,
                p99_response_time_ms=15000.0,
                health_score=0.0,
                active_connections=0,
                resource_utilization={"cpu_percent": 100, "memory_percent": 100, "disk_percent": 100},
            )

    async def _evaluate_canary_health(self, deployment: CanaryDeployment, current_metrics: CanaryMetrics) -> dict[str, Any]:
        """Evaluate the health of a canary deployment.

        Args:
            deployment: The deployment to evaluate
            current_metrics: Current performance metrics

        Returns:
            Health evaluation results
        """
        evaluation = {"healthy": True, "reason": None, "details": {}, "checks": []}

        baseline = deployment.baseline_metrics
        config = deployment.config

        # Check error rate
        if current_metrics.error_rate > config.max_error_rate:
            evaluation["healthy"] = False
            evaluation["reason"] = RollbackReason.HIGH_ERROR_RATE
            evaluation["details"]["error_rate_check"] = {"current": current_metrics.error_rate, "threshold": config.max_error_rate, "exceeded_by": current_metrics.error_rate - config.max_error_rate}

        evaluation["checks"].append({"name": "error_rate", "passed": current_metrics.error_rate <= config.max_error_rate, "current": current_metrics.error_rate, "threshold": config.max_error_rate})

        # Check success rate
        if current_metrics.success_rate < config.success_threshold:
            evaluation["healthy"] = False
            if not evaluation["reason"]:
                evaluation["reason"] = RollbackReason.HIGH_ERROR_RATE
            evaluation["details"]["success_rate_check"] = {
                "current": current_metrics.success_rate,
                "threshold": config.success_threshold,
                "shortfall": config.success_threshold - current_metrics.success_rate,
            }

        evaluation["checks"].append(
            {"name": "success_rate", "passed": current_metrics.success_rate >= config.success_threshold, "current": current_metrics.success_rate, "threshold": config.success_threshold}
        )

        # Check response time regression (if baseline available)
        if baseline and baseline.avg_response_time_ms > 0:
            regression_percent = ((current_metrics.avg_response_time_ms - baseline.avg_response_time_ms) / baseline.avg_response_time_ms) * 100

            if regression_percent > config.max_response_time_regression:
                evaluation["healthy"] = False
                if not evaluation["reason"]:
                    evaluation["reason"] = RollbackReason.RESPONSE_TIME_REGRESSION
                evaluation["details"]["response_time_regression_check"] = {
                    "current_ms": current_metrics.avg_response_time_ms,
                    "baseline_ms": baseline.avg_response_time_ms,
                    "regression_percent": regression_percent,
                    "threshold_percent": config.max_response_time_regression,
                }

            evaluation["checks"].append(
                {
                    "name": "response_time_regression",
                    "passed": regression_percent <= config.max_response_time_regression,
                    "regression_percent": regression_percent,
                    "threshold_percent": config.max_response_time_regression,
                }
            )

        # Check health score
        if current_metrics.health_score < config.health_score_threshold:
            evaluation["healthy"] = False
            if not evaluation["reason"]:
                evaluation["reason"] = RollbackReason.HEALTH_SCORE_DEGRADATION
            evaluation["details"]["health_score_check"] = {
                "current": current_metrics.health_score,
                "threshold": config.health_score_threshold,
                "deficit": config.health_score_threshold - current_metrics.health_score,
            }

        evaluation["checks"].append(
            {"name": "health_score", "passed": current_metrics.health_score >= config.health_score_threshold, "current": current_metrics.health_score, "threshold": config.health_score_threshold}
        )

        # Check resource utilization
        cpu_threshold = 95.0
        memory_threshold = 90.0

        if current_metrics.resource_utilization.get("cpu_percent", 0) > cpu_threshold or current_metrics.resource_utilization.get("memory_percent", 0) > memory_threshold:
            evaluation["healthy"] = False
            if not evaluation["reason"]:
                evaluation["reason"] = RollbackReason.RESOURCE_EXHAUSTION
            evaluation["details"]["resource_check"] = {
                "cpu_percent": current_metrics.resource_utilization.get("cpu_percent", 0),
                "memory_percent": current_metrics.resource_utilization.get("memory_percent", 0),
                "cpu_threshold": cpu_threshold,
                "memory_threshold": memory_threshold,
            }

        evaluation["checks"].append(
            {
                "name": "resource_utilization",
                "passed": (current_metrics.resource_utilization.get("cpu_percent", 0) <= cpu_threshold and current_metrics.resource_utilization.get("memory_percent", 0) <= memory_threshold),
                "cpu_percent": current_metrics.resource_utilization.get("cpu_percent", 0),
                "memory_percent": current_metrics.resource_utilization.get("memory_percent", 0),
            }
        )

        return evaluation

    async def _rollback_deployment(self, deployment: CanaryDeployment, reason: RollbackReason) -> None:
        """Automatically rollback a failed canary deployment.

        Args:
            deployment: The deployment to rollback
            reason: Reason for the rollback
        """
        deployment.status = DeploymentStatus.ROLLING_BACK
        deployment.rollback_reason = reason

        try:
            # Route all traffic back to stable version
            await self._configure_canary_traffic(0)

            deployment.status = DeploymentStatus.FAILED
            deployment.completion_time = time.time()

            # Cancel monitoring tasks
            if self._monitoring_task and not self._monitoring_task.done():
                self._monitoring_task.cancel()
            if self._ramp_up_task and not self._ramp_up_task.done():
                self._ramp_up_task.cancel()

            # Publish rollback event
            await self._publish_deployment_event(
                "deployment_rolled_back",
                {
                    "deployment_id": deployment.deployment_id,
                    "rollback_reason": reason.value,
                    "rollback_time": deployment.completion_time,
                    "deployment_duration_minutes": (deployment.completion_time - deployment.start_time) / 60,
                    "traffic_percentage_at_rollback": deployment.traffic_percentage,
                    "metrics_at_rollback": {
                        "success_rate": deployment.current_metrics.success_rate if deployment.current_metrics else 0,
                        "error_rate": deployment.current_metrics.error_rate if deployment.current_metrics else 100,
                        "health_score": deployment.current_metrics.health_score if deployment.current_metrics else 0,
                    },
                },
            )

            # Add to history and clear active deployment
            self.deployment_history.append(deployment)
            self.active_deployment = None

            # Save state
            await self._save_deployment_state()

        except Exception as e:
            await self._publish_deployment_event("rollback_error", {"deployment_id": deployment.deployment_id, "rollback_reason": reason.value, "error": str(e)})

    async def _promote_canary_deployment(self, deployment: CanaryDeployment) -> None:
        """Promote a successful canary deployment to full deployment.

        Args:
            deployment: The deployment to promote
        """
        deployment.status = DeploymentStatus.PROMOTING

        try:
            # Route 100% traffic to canary (now becomes the stable version)
            await self._configure_canary_traffic(100)

            deployment.status = DeploymentStatus.COMPLETED
            deployment.completion_time = time.time()
            deployment.promotion_time = deployment.completion_time

            # Cancel monitoring tasks
            if self._monitoring_task and not self._monitoring_task.done():
                self._monitoring_task.cancel()
            if self._ramp_up_task and not self._ramp_up_task.done():
                self._ramp_up_task.cancel()

            # Publish promotion event
            await self._publish_deployment_event(
                "deployment_promoted",
                {
                    "deployment_id": deployment.deployment_id,
                    "promotion_time": deployment.promotion_time,
                    "total_deployment_duration_minutes": (deployment.completion_time - deployment.start_time) / 60,
                    "final_metrics": {
                        "success_rate": deployment.current_metrics.success_rate if deployment.current_metrics else 100,
                        "error_rate": deployment.current_metrics.error_rate if deployment.current_metrics else 0,
                        "avg_response_time_ms": deployment.current_metrics.avg_response_time_ms if deployment.current_metrics else 0,
                        "health_score": deployment.current_metrics.health_score if deployment.current_metrics else 100,
                    },
                },
            )

            # Add to history and clear active deployment
            self.deployment_history.append(deployment)
            self.active_deployment = None

            # Save state
            await self._save_deployment_state()

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.completion_time = time.time()

            await self._publish_deployment_event("promotion_error", {"deployment_id": deployment.deployment_id, "error": str(e)})

    async def _ramp_up_traffic(self, deployment: CanaryDeployment) -> None:
        """Gradually ramp up traffic to canary deployment.

        Args:
            deployment: The deployment to ramp up
        """
        if not deployment.config.ramp_up_steps:
            return

        try:
            for step_percentage in deployment.config.ramp_up_steps:
                if deployment.status != DeploymentStatus.MONITORING:
                    break

                # Wait for ramp-up interval
                await asyncio.sleep(deployment.config.ramp_up_interval_minutes * 60)

                if deployment.status != DeploymentStatus.MONITORING:
                    break

                # Increase traffic
                deployment.traffic_percentage = step_percentage
                await self._configure_canary_traffic(step_percentage)

                await self._publish_deployment_event("traffic_ramped_up", {"deployment_id": deployment.deployment_id, "new_traffic_percentage": step_percentage, "ramp_up_time": time.time()})

        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self._publish_deployment_event("ramp_up_error", {"deployment_id": deployment.deployment_id, "error": str(e)})

    async def _get_system_resource_metrics(self) -> dict[str, Any]:
        """Get current system resource metrics.

        Returns:
            Dictionary with system resource information
        """
        try:
            import psutil

            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "connections": len(psutil.net_connections()),
                "load_average": psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0, 0, 0],
            }
        except ImportError:
            return {"cpu_percent": 10, "memory_percent": 30, "disk_percent": 50, "connections": 10}
        except Exception:
            return {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0, "connections": 0}

    def _load_deployment_history(self) -> None:
        """Load deployment history from file."""
        if self.deployment_data_path.exists():
            try:
                with open(self.deployment_data_path, encoding="utf-8") as f:
                    json.load(f)
                    # Note: In a real implementation, you'd deserialize the deployment objects
                    # For now, we'll start with empty history
                    self.deployment_history = []
            except Exception:
                self.deployment_history = []

    async def _save_deployment_state(self) -> None:
        """Save current deployment state to file."""
        try:
            self.deployment_data_path.parent.mkdir(parents=True, exist_ok=True)

            state_data = {
                "active_deployment": {
                    "deployment_id": self.active_deployment.deployment_id,
                    "status": self.active_deployment.status.value,
                    "start_time": self.active_deployment.start_time,
                    "traffic_percentage": self.active_deployment.traffic_percentage,
                    "completion_time": self.active_deployment.completion_time,
                    "rollback_reason": self.active_deployment.rollback_reason.value if self.active_deployment.rollback_reason else None,
                }
                if self.active_deployment
                else None,
                "deployment_history_count": len(self.deployment_history),
                "last_updated": time.time(),
            }

            with open(self.deployment_data_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            # Don't let state saving failures affect deployments
            logger.debug("Failed to save deployment state: %s", e)

    async def _publish_deployment_event(self, event_subtype: str, data: dict[str, Any]) -> None:
        """Publish a canary deployment event.

        Args:
            event_subtype: Type of deployment event
            data: Event data
        """
        await self.event_bus.publish(
            Event(type=EventType.CUSTOM, data={"event_subtype": f"canary_{event_subtype}", **data}, timestamp=time.time(), source="canary_manager", priority=EventPriority.HIGH)
        )

    async def manual_rollback(self, reason: str = "Manual intervention") -> dict[str, Any]:
        """Manually trigger a rollback of the active canary deployment.

        Args:
            reason: Reason for manual rollback

        Returns:
            Rollback result
        """
        if not self.active_deployment:
            return {"success": False, "error": "No active deployment to rollback"}

        await self._rollback_deployment(self.active_deployment, RollbackReason.MANUAL_TRIGGER)

        return {"success": True, "deployment_id": self.active_deployment.deployment_id, "rollback_reason": reason, "rollback_time": time.time()}

    async def get_deployment_status(self) -> dict[str, Any]:
        """Get current deployment status.

        Returns:
            Current deployment status information
        """
        if not self.active_deployment:
            return {
                "active_deployment": None,
                "deployment_history_count": len(self.deployment_history),
                "last_deployment": self.deployment_history[-1].deployment_id if self.deployment_history else None,
            }

        deployment = self.active_deployment

        return {
            "active_deployment": {
                "deployment_id": deployment.deployment_id,
                "status": deployment.status.value,
                "start_time": deployment.start_time,
                "elapsed_minutes": (time.time() - deployment.start_time) / 60,
                "traffic_percentage": deployment.traffic_percentage,
                "current_metrics": {
                    "success_rate": deployment.current_metrics.success_rate if deployment.current_metrics else None,
                    "error_rate": deployment.current_metrics.error_rate if deployment.current_metrics else None,
                    "avg_response_time_ms": deployment.current_metrics.avg_response_time_ms if deployment.current_metrics else None,
                    "health_score": deployment.current_metrics.health_score if deployment.current_metrics else None,
                }
                if deployment.current_metrics
                else None,
                "baseline_metrics": {
                    "success_rate": deployment.baseline_metrics.success_rate if deployment.baseline_metrics else None,
                    "avg_response_time_ms": deployment.baseline_metrics.avg_response_time_ms if deployment.baseline_metrics else None,
                    "health_score": deployment.baseline_metrics.health_score if deployment.baseline_metrics else None,
                }
                if deployment.baseline_metrics
                else None,
                "rollback_reason": deployment.rollback_reason.value if deployment.rollback_reason else None,
            },
            "deployment_history_count": len(self.deployment_history),
        }
