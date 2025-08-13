#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Complete Deployment Pipeline Orchestration.

This module provides end-to-end deployment pipeline orchestration including
validation, canary deployment, monitoring, and automated rollback capabilities.
"""


class DeploymentPipelineError(Exception):
    """Base exception for deployment pipeline failures."""
    pass


class DeploymentTimeoutError(DeploymentPipelineError):
    """Exception raised when deployment operations timeout."""
    
    def __init__(self, phase: str = None) -> None:
        if phase:
            message = f"Deployment timeout during {phase} phase"
        else:
            message = "Deployment operation timed out"
        super().__init__(message)
        self.phase = phase


class DeploymentValidationError(DeploymentPipelineError):
    """Exception raised when deployment validation fails."""
    
    def __init__(self, reason: str = None) -> None:
        if reason:
            message = f"Deployment validation failed: {reason}"
        else:
            message = "Deployment validation failed"
        super().__init__(message)
        self.reason = reason


import asyncio
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from libs.dashboard.monitoring_integration import get_monitoring_dashboard
from libs.deployment.canary_manager import CanaryConfig, CanaryDeploymentManager
from libs.incident.incident_response import IncidentResponseSystem
from scripts.deployment_validator import DeploymentValidator


class DeploymentPhase(Enum):
    """Phases of the deployment pipeline."""

    INITIALIZING = "initializing"
    VALIDATION = "validation"
    CANARY = "canary"
    MONITORING = "monitoring"
    PROMOTION = "promotion"
    COMPLETION = "completion"
    ROLLBACK = "rollback"
    FAILED = "failed"


class DeploymentResult(Enum):
    """Final result of deployment pipeline."""

    SUCCESS = "success"
    FAILED_VALIDATION = "failed_validation"
    FAILED_CANARY = "failed_canary"
    ROLLED_BACK = "rolled_back"
    EMERGENCY_ROLLBACK = "emergency_rollback"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class DeploymentPhaseResult:
    """Result of a deployment phase."""

    phase: DeploymentPhase
    success: bool
    duration_ms: int
    details: dict[str, Any]
    error: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class DeploymentConfig:
    """Configuration for deployment pipeline."""

    # Deployment identification
    deployment_name: str
    version: str
    environment: str = "production"

    # Validation configuration
    skip_validation: bool = False
    validation_timeout_minutes: int = 10

    # Canary configuration
    canary_enabled: bool = True
    canary_config: CanaryConfig | None = None

    # Monitoring configuration
    monitoring_duration_minutes: int = 15
    health_check_interval_seconds: int = 30

    # Rollback configuration
    auto_rollback_enabled: bool = True
    rollback_timeout_minutes: int = 5
    emergency_rollback_threshold_minutes: int = 30

    # Notification configuration
    notification_channels: list[str] = field(default_factory=lambda: ["slack"])
    notify_on_phases: list[DeploymentPhase] = field(default_factory=lambda: [DeploymentPhase.VALIDATION, DeploymentPhase.CANARY, DeploymentPhase.COMPLETION, DeploymentPhase.ROLLBACK])

    # Advanced configuration
    parallel_validation: bool = True
    pre_deployment_hooks: list[str] = field(default_factory=list)
    post_deployment_hooks: list[str] = field(default_factory=list)
    deployment_timeout_minutes: int = 60
    require_manual_approval: bool = False


@dataclass
class DeploymentPipelineState:
    """State of the deployment pipeline."""

    deployment_id: str
    config: DeploymentConfig
    current_phase: DeploymentPhase
    start_time: float
    completion_time: float | None = None
    phase_results: list[DeploymentPhaseResult] = field(default_factory=list)
    final_result: DeploymentResult | None = None
    canary_deployment_id: str | None = None
    rollback_reason: str | None = None
    manual_approval_required: bool = False
    metrics_at_start: dict[str, Any] = field(default_factory=dict)
    metrics_at_completion: dict[str, Any] = field(default_factory=dict)


class DeploymentPipeline:
    """Complete deployment pipeline orchestration system."""

    def __init__(self) -> None:
        """Initialize the deployment pipeline."""
        self.validator = DeploymentValidator()
        self.canary_manager = CanaryDeploymentManager()
        self.monitoring = get_monitoring_dashboard()
        self.event_bus = get_event_bus()
        self.incident_response = IncidentResponseSystem()

        # Pipeline state
        self.active_deployments: dict[str, DeploymentPipelineState] = {}
        self.deployment_history: list[DeploymentPipelineState] = []

        # Configuration
        self.data_path = Path("data/deployments")
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Pipeline hooks
        self.pre_deployment_hooks: dict[str, callable] = {}
        self.post_deployment_hooks: dict[str, callable] = {}

        # Setup default hooks
        self._setup_default_hooks()

    def _setup_default_hooks(self) -> None:
        """Setup default deployment hooks."""
        self.pre_deployment_hooks = {
            "backup_database": self._backup_database_hook,
            "notify_team": self._notify_team_hook,
            "prepare_infrastructure": self._prepare_infrastructure_hook,
            "validate_dependencies": self._validate_dependencies_hook,
        }

        self.post_deployment_hooks = {
            "run_smoke_tests": self._run_smoke_tests_hook,
            "update_monitoring": self._update_monitoring_hook,
            "cleanup_resources": self._cleanup_resources_hook,
            "send_completion_notification": self._send_completion_notification_hook,
        }

    async def execute_deployment(self, config: DeploymentConfig) -> dict[str, Any]:
        """Execute complete deployment pipeline.

        Args:
            config: Deployment configuration

        Returns:
            Dictionary with deployment results
        """
        deployment_id = f"deploy_{config.deployment_name}_{int(time.time())}"

        # Create pipeline state
        pipeline_state = DeploymentPipelineState(deployment_id=deployment_id, config=config, current_phase=DeploymentPhase.INITIALIZING, start_time=time.time())

        self.active_deployments[deployment_id] = pipeline_state

        try:
            # Capture initial system metrics
            pipeline_state.metrics_at_start = await self._capture_system_metrics()

            # Publish deployment started event
            await self._publish_deployment_event(
                "deployment_started",
                {
                    "deployment_id": deployment_id,
                    "deployment_name": config.deployment_name,
                    "version": config.version,
                    "environment": config.environment,
                    "canary_enabled": config.canary_enabled,
                    "auto_rollback_enabled": config.auto_rollback_enabled,
                },
            )

            # Execute deployment phases
            success = await self._execute_deployment_phases(pipeline_state)

            if success:
                pipeline_state.final_result = DeploymentResult.SUCCESS

            pipeline_state.completion_time = time.time()

            # Capture final metrics
            pipeline_state.metrics_at_completion = await self._capture_system_metrics()

            # Move to history
            self.deployment_history.append(pipeline_state)
            if deployment_id in self.active_deployments:
                del self.active_deployments[deployment_id]

            # Save deployment data
            await self._save_deployment_data(pipeline_state)

            # Generate final result
            return self._generate_deployment_result(pipeline_state)

        except TimeoutError:
            pipeline_state.final_result = DeploymentResult.TIMEOUT
            pipeline_state.completion_time = time.time()

            await self._publish_deployment_event(
                "deployment_timeout", {"deployment_id": deployment_id, "timeout_minutes": config.deployment_timeout_minutes, "current_phase": pipeline_state.current_phase.value}
            )

            # Attempt emergency rollback
            await self._emergency_rollback(pipeline_state)

            return self._generate_deployment_result(pipeline_state)

        except Exception as e:
            pipeline_state.final_result = DeploymentResult.FAILED_VALIDATION
            pipeline_state.completion_time = time.time()

            await self._publish_deployment_event("deployment_error", {"deployment_id": deployment_id, "error": str(e), "current_phase": pipeline_state.current_phase.value})

            return self._generate_deployment_result(pipeline_state)

    async def _execute_deployment_phases(self, pipeline_state: DeploymentPipelineState) -> bool:
        """Execute all phases of the deployment pipeline.

        Args:
            pipeline_state: Current pipeline state

        Returns:
            True if all phases completed successfully
        """
        config = pipeline_state.config
        deployment_timeout = time.time() + (config.deployment_timeout_minutes * 60)

        # Phase 1: Pre-deployment hooks
        if not await self._execute_pre_deployment_hooks(pipeline_state):
            return False

        # Phase 2: Validation
        if not config.skip_validation:
            pipeline_state.current_phase = DeploymentPhase.VALIDATION

            if time.time() > deployment_timeout:
                raise DeploymentTimeoutError("validation")

            if not await self._execute_validation_phase(pipeline_state):
                pipeline_state.final_result = DeploymentResult.FAILED_VALIDATION
                return False

        # Phase 3: Canary Deployment
        if config.canary_enabled:
            pipeline_state.current_phase = DeploymentPhase.CANARY

            if time.time() > deployment_timeout:
                raise DeploymentTimeoutError("canary")

            if not await self._execute_canary_phase(pipeline_state):
                pipeline_state.final_result = DeploymentResult.FAILED_CANARY
                if config.auto_rollback_enabled:
                    await self._execute_rollback_phase(pipeline_state)
                return False

        # Phase 4: Monitoring and Health Checks
        pipeline_state.current_phase = DeploymentPhase.MONITORING

        if time.time() > deployment_timeout:
            raise DeploymentTimeoutError("monitoring")

        if not await self._execute_monitoring_phase(pipeline_state):
            if config.auto_rollback_enabled:
                await self._execute_rollback_phase(pipeline_state)
            return False

        # Phase 5: Manual Approval (if required)
        if config.require_manual_approval:
            pipeline_state.manual_approval_required = True

            await self._publish_deployment_event("manual_approval_required", {"deployment_id": pipeline_state.deployment_id, "deployment_name": config.deployment_name, "approval_timeout_minutes": 30})

            # Wait for manual approval (mock implementation)
            approval_timeout = time.time() + (30 * 60)  # 30 minutes
            while time.time() < approval_timeout and pipeline_state.manual_approval_required:
                await asyncio.sleep(10)
                if time.time() > deployment_timeout:
                    raise DeploymentTimeoutError("manual_approval")

            if pipeline_state.manual_approval_required:
                await self._publish_deployment_event("manual_approval_timeout", {"deployment_id": pipeline_state.deployment_id})
                return False

        # Phase 6: Promotion (if using canary)
        if config.canary_enabled:
            pipeline_state.current_phase = DeploymentPhase.PROMOTION

            if not await self._execute_promotion_phase(pipeline_state):
                if config.auto_rollback_enabled:
                    await self._execute_rollback_phase(pipeline_state)
                return False

        # Phase 7: Post-deployment hooks
        pipeline_state.current_phase = DeploymentPhase.COMPLETION

        await self._execute_post_deployment_hooks(pipeline_state)

        return True

    async def _execute_validation_phase(self, pipeline_state: DeploymentPipelineState) -> bool:
        """Execute deployment validation phase.

        Args:
            pipeline_state: Current pipeline state

        Returns:
            True if validation passes
        """
        phase_start = time.perf_counter()

        try:
            # Run deployment validation
            validation_results = await asyncio.wait_for(self.validator.validate_deployment(), timeout=pipeline_state.config.validation_timeout_minutes * 60)

            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            # Create phase result
            phase_result = DeploymentPhaseResult(
                phase=DeploymentPhase.VALIDATION,
                success=validation_results["can_deploy"],
                duration_ms=phase_duration,
                details={
                    "total_checks": validation_results["total_checks"],
                    "passed": len(validation_results["passed"]),
                    "failed": len(validation_results["failed"]),
                    "warnings": len(validation_results["warnings"]),
                    "critical_failures": validation_results["critical_failures"],
                    "execution_time_ms": validation_results["execution_time_ms"],
                },
                warnings=[check["name"] for check in validation_results.get("warnings", [])],
            )

            if not validation_results["can_deploy"]:
                phase_result.error = f"Validation failed with {validation_results['critical_failures']} critical failures"

            pipeline_state.phase_results.append(phase_result)

            # Publish validation result
            await self._publish_deployment_event(
                "validation_completed",
                {
                    "deployment_id": pipeline_state.deployment_id,
                    "validation_passed": validation_results["can_deploy"],
                    "total_checks": validation_results["total_checks"],
                    "failed_checks": len(validation_results["failed"]),
                    "critical_failures": validation_results["critical_failures"],
                    "validation_duration_ms": phase_duration,
                },
            )

            return validation_results["can_deploy"]

        except TimeoutError:
            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(phase=DeploymentPhase.VALIDATION, success=False, duration_ms=phase_duration, details={"timeout": True}, error="Validation timed out")
            pipeline_state.phase_results.append(phase_result)

            await self._publish_deployment_event("validation_timeout", {"deployment_id": pipeline_state.deployment_id, "timeout_minutes": pipeline_state.config.validation_timeout_minutes})

            return False

        except Exception as e:
            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(phase=DeploymentPhase.VALIDATION, success=False, duration_ms=phase_duration, details={"error": str(e)}, error=str(e))
            pipeline_state.phase_results.append(phase_result)

            return False

    async def _execute_canary_phase(self, pipeline_state: DeploymentPipelineState) -> bool:
        """Execute canary deployment phase.

        Args:
            pipeline_state: Current pipeline state

        Returns:
            True if canary deployment succeeds
        """
        phase_start = time.perf_counter()

        try:
            # Use provided canary config or create default
            canary_config = pipeline_state.config.canary_config or CanaryConfig()

            # Start canary deployment
            canary_result = await self.canary_manager.start_canary_deployment(deployment_id=pipeline_state.deployment_id, config=canary_config)

            pipeline_state.canary_deployment_id = pipeline_state.deployment_id

            # Wait for canary completion
            await self._wait_for_canary_completion(pipeline_state, canary_config)

            # Check final canary status
            canary_status = await self._get_canary_status(pipeline_state.deployment_id)

            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(
                phase=DeploymentPhase.CANARY,
                success=canary_status["success"],
                duration_ms=phase_duration,
                details={
                    "canary_percentage": canary_result.get("canary_percentage", 0),
                    "monitoring_started": canary_result.get("monitoring_started", False),
                    "baseline_captured": canary_result.get("baseline_captured", False),
                    "final_status": canary_status,
                },
            )

            if not canary_status["success"]:
                phase_result.error = canary_status.get("failure_reason", "Canary deployment failed")

            pipeline_state.phase_results.append(phase_result)

            # Publish canary result
            await self._publish_deployment_event(
                "canary_completed",
                {
                    "deployment_id": pipeline_state.deployment_id,
                    "canary_success": canary_status["success"],
                    "canary_duration_ms": phase_duration,
                    "failure_reason": canary_status.get("failure_reason"),
                },
            )

            return canary_status["success"]

        except Exception as e:
            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(phase=DeploymentPhase.CANARY, success=False, duration_ms=phase_duration, details={"error": str(e)}, error=str(e))
            pipeline_state.phase_results.append(phase_result)

            return False

    async def _execute_monitoring_phase(self, pipeline_state: DeploymentPipelineState) -> bool:
        """Execute deployment monitoring phase.

        Args:
            pipeline_state: Current pipeline state

        Returns:
            True if monitoring passes health checks
        """
        phase_start = time.perf_counter()
        config = pipeline_state.config

        try:
            # Monitor system health for specified duration
            monitoring_end_time = time.time() + (config.monitoring_duration_minutes * 60)
            health_check_failures = 0
            max_failures = 3  # Allow some transient failures

            while time.time() < monitoring_end_time:
                # Perform health check
                health_status = await self._perform_health_check()

                if not health_status["healthy"]:
                    health_check_failures += 1

                    if health_check_failures >= max_failures:
                        phase_duration = int((time.perf_counter() - phase_start) * 1000)

                        phase_result = DeploymentPhaseResult(
                            phase=DeploymentPhase.MONITORING,
                            success=False,
                            duration_ms=phase_duration,
                            details={"health_check_failures": health_check_failures, "max_failures": max_failures, "last_health_status": health_status},
                            error=f"Health checks failed {health_check_failures} times",
                        )
                        pipeline_state.phase_results.append(phase_result)

                        return False
                else:
                    # Reset failure counter on successful check
                    health_check_failures = 0

                # Wait before next health check
                await asyncio.sleep(config.health_check_interval_seconds)

            # Monitoring completed successfully
            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(
                phase=DeploymentPhase.MONITORING,
                success=True,
                duration_ms=phase_duration,
                details={
                    "monitoring_duration_minutes": config.monitoring_duration_minutes,
                    "health_check_interval_seconds": config.health_check_interval_seconds,
                    "total_health_check_failures": health_check_failures,
                    "final_health_status": await self._perform_health_check(),
                },
            )
            pipeline_state.phase_results.append(phase_result)

            # Publish monitoring result
            await self._publish_deployment_event(
                "monitoring_completed",
                {
                    "deployment_id": pipeline_state.deployment_id,
                    "monitoring_success": True,
                    "monitoring_duration_minutes": config.monitoring_duration_minutes,
                    "health_check_failures": health_check_failures,
                },
            )

            return True

        except Exception as e:
            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(phase=DeploymentPhase.MONITORING, success=False, duration_ms=phase_duration, details={"error": str(e)}, error=str(e))
            pipeline_state.phase_results.append(phase_result)

            return False

    async def _execute_promotion_phase(self, pipeline_state: DeploymentPipelineState) -> bool:
        """Execute deployment promotion phase.

        Args:
            pipeline_state: Current pipeline state

        Returns:
            True if promotion succeeds
        """
        phase_start = time.perf_counter()

        try:
            # Get canary deployment status
            deployment_status = await self.canary_manager.get_deployment_status()

            if not deployment_status.get("active_deployment"):
                raise DeploymentValidationError("no_active_canary")

            # In a real implementation, promotion would involve:
            # - Routing 100% traffic to the new version
            # - Updating load balancer configuration
            # - Updating service discovery
            # - Cleaning up old version resources

            # Mock promotion logic
            await asyncio.sleep(2)  # Simulate promotion time

            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(
                phase=DeploymentPhase.PROMOTION,
                success=True,
                duration_ms=phase_duration,
                details={"promoted_version": pipeline_state.config.version, "traffic_percentage": 100, "promotion_method": "load_balancer_update"},
            )
            pipeline_state.phase_results.append(phase_result)

            # Publish promotion result
            await self._publish_deployment_event(
                "promotion_completed", {"deployment_id": pipeline_state.deployment_id, "promoted_version": pipeline_state.config.version, "promotion_duration_ms": phase_duration}
            )

            return True

        except Exception as e:
            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(phase=DeploymentPhase.PROMOTION, success=False, duration_ms=phase_duration, details={"error": str(e)}, error=str(e))
            pipeline_state.phase_results.append(phase_result)

            return False

    async def _execute_rollback_phase(self, pipeline_state: DeploymentPipelineState) -> None:
        """Execute deployment rollback phase.

        Args:
            pipeline_state: Current pipeline state
        """
        pipeline_state.current_phase = DeploymentPhase.ROLLBACK
        phase_start = time.perf_counter()

        try:
            # Trigger canary rollback if active
            if pipeline_state.canary_deployment_id:
                rollback_result = await self.canary_manager.manual_rollback(reason="Deployment pipeline triggered rollback")

                if rollback_result["success"]:
                    pipeline_state.rollback_reason = "Automated rollback due to deployment failure"
                    pipeline_state.final_result = DeploymentResult.ROLLED_BACK
                else:
                    pipeline_state.rollback_reason = f"Rollback failed: {rollback_result.get('error', 'Unknown error')}"
                    pipeline_state.final_result = DeploymentResult.EMERGENCY_ROLLBACK

            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(
                phase=DeploymentPhase.ROLLBACK, success=True, duration_ms=phase_duration, details={"rollback_reason": pipeline_state.rollback_reason, "rollback_method": "canary_manager"}
            )
            pipeline_state.phase_results.append(phase_result)

            # Publish rollback result
            await self._publish_deployment_event(
                "rollback_completed", {"deployment_id": pipeline_state.deployment_id, "rollback_reason": pipeline_state.rollback_reason, "rollback_duration_ms": phase_duration}
            )

        except Exception as e:
            phase_duration = int((time.perf_counter() - phase_start) * 1000)

            phase_result = DeploymentPhaseResult(phase=DeploymentPhase.ROLLBACK, success=False, duration_ms=phase_duration, details={"error": str(e)}, error=str(e))
            pipeline_state.phase_results.append(phase_result)

    async def _emergency_rollback(self, pipeline_state: DeploymentPipelineState) -> None:
        """Perform emergency rollback.

        Args:
            pipeline_state: Current pipeline state
        """
        pipeline_state.final_result = DeploymentResult.EMERGENCY_ROLLBACK

        try:
            # Attempt rapid rollback
            if pipeline_state.canary_deployment_id:
                await self.canary_manager.manual_rollback(reason="Emergency rollback due to timeout")

            # Publish emergency rollback
            await self._publish_deployment_event("emergency_rollback", {"deployment_id": pipeline_state.deployment_id, "trigger": "deployment_timeout", "emergency_rollback_time": time.time()})

        except Exception as e:
            await self._publish_deployment_event("emergency_rollback_failed", {"deployment_id": pipeline_state.deployment_id, "error": str(e)})

    async def _wait_for_canary_completion(self, pipeline_state: DeploymentPipelineState, canary_config: CanaryConfig) -> None:
        """Wait for canary deployment to complete.

        Args:
            pipeline_state: Current pipeline state
            canary_config: Canary configuration
        """
        timeout = time.time() + (canary_config.duration_minutes * 60) + 60  # Extra minute for safety

        while time.time() < timeout:
            deployment_status = await self.canary_manager.get_deployment_status()

            if not deployment_status.get("active_deployment"):
                # Canary completed (either promoted or rolled back)
                break

            await asyncio.sleep(30)  # Check every 30 seconds

        if time.time() >= timeout:
            # Force rollback on timeout
            await self.canary_manager.manual_rollback(reason="Canary deployment timeout")

    async def _get_canary_status(self, deployment_id: str) -> dict[str, Any]:
        """Get the final status of a canary deployment.

        Args:
            deployment_id: Canary deployment ID

        Returns:
            Dictionary with canary status
        """
        # Mock implementation - in real system this would check actual deployment status
        deployment_status = await self.canary_manager.get_deployment_status()

        if deployment_status.get("active_deployment"):
            return {"success": False, "failure_reason": "Canary deployment still active (timeout)"}

        # Check deployment history for completion status
        # For now, assume success if no active deployment
        return {"success": True, "completion_time": time.time()}

    async def _perform_health_check(self) -> dict[str, Any]:
        """Perform system health check.

        Returns:
            Dictionary with health check results
        """
        try:
            # Get current health score from monitoring
            health_score = self.monitoring._calculate_health_score()
            active_alerts = len(self.monitoring.get_active_alerts())

            # Consider system healthy if health score > 70 and no critical alerts
            critical_alerts = len([alert for alert in self.monitoring.get_active_alerts() if alert.severity.value in {"critical", "error"}])

            healthy = health_score > 70 and critical_alerts == 0

            return {"healthy": healthy, "health_score": health_score, "active_alerts": active_alerts, "critical_alerts": critical_alerts, "timestamp": time.time()}
        except Exception as e:
            return {"healthy": False, "error": str(e), "timestamp": time.time()}

    async def _execute_pre_deployment_hooks(self, pipeline_state: DeploymentPipelineState) -> bool:
        """Execute pre-deployment hooks.

        Args:
            pipeline_state: Current pipeline state

        Returns:
            True if all hooks succeed
        """
        for hook_name in pipeline_state.config.pre_deployment_hooks:
            if hook_name in self.pre_deployment_hooks:
                try:
                    await self.pre_deployment_hooks[hook_name](pipeline_state)
                except Exception as e:
                    await self._publish_deployment_event("pre_deployment_hook_failed", {"deployment_id": pipeline_state.deployment_id, "hook_name": hook_name, "error": str(e)})
                    return False
        return True

    async def _execute_post_deployment_hooks(self, pipeline_state: DeploymentPipelineState) -> None:
        """Execute post-deployment hooks.

        Args:
            pipeline_state: Current pipeline state
        """
        for hook_name in pipeline_state.config.post_deployment_hooks:
            if hook_name in self.post_deployment_hooks:
                try:
                    await self.post_deployment_hooks[hook_name](pipeline_state)
                except Exception as e:
                    await self._publish_deployment_event("post_deployment_hook_failed", {"deployment_id": pipeline_state.deployment_id, "hook_name": hook_name, "error": str(e)})

    # Default Hook Implementations
    async def _backup_database_hook(self, pipeline_state: DeploymentPipelineState) -> None:
        """Backup database before deployment."""
        await asyncio.sleep(1)  # Mock backup time

    async def _notify_team_hook(self, pipeline_state: DeploymentPipelineState) -> None:
        """Notify team of deployment start."""
        await self._publish_deployment_event("team_notified", {"deployment_id": pipeline_state.deployment_id, "notification_channels": pipeline_state.config.notification_channels})

    async def _prepare_infrastructure_hook(self, pipeline_state: DeploymentPipelineState) -> None:
        """Prepare infrastructure for deployment."""
        await asyncio.sleep(0.5)  # Mock preparation time

    async def _validate_dependencies_hook(self, pipeline_state: DeploymentPipelineState) -> None:
        """Validate external dependencies."""
        await asyncio.sleep(0.5)  # Mock validation time

    async def _run_smoke_tests_hook(self, pipeline_state: DeploymentPipelineState) -> None:
        """Run smoke tests after deployment."""
        await asyncio.sleep(2)  # Mock test time

    async def _update_monitoring_hook(self, pipeline_state: DeploymentPipelineState) -> None:
        """Update monitoring configuration."""
        await asyncio.sleep(0.5)  # Mock update time

    async def _cleanup_resources_hook(self, pipeline_state: DeploymentPipelineState) -> None:
        """Cleanup old deployment resources."""
        await asyncio.sleep(1)  # Mock cleanup time

    async def _send_completion_notification_hook(self, pipeline_state: DeploymentPipelineState) -> None:
        """Send deployment completion notification."""
        await self._publish_deployment_event(
            "completion_notification_sent",
            {
                "deployment_id": pipeline_state.deployment_id,
                "final_result": pipeline_state.final_result.value if pipeline_state.final_result else "unknown",
                "notification_channels": pipeline_state.config.notification_channels,
            },
        )

    async def _capture_system_metrics(self) -> dict[str, Any]:
        """Capture current system metrics.

        Returns:
            Dictionary with system metrics
        """
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            return {
                "health_score": dashboard_data.get("health_score", 0),
                "active_alerts": dashboard_data.get("alerts", {}).get("active", 0),
                "metrics_summary": dashboard_data.get("metrics", {}),
                "timestamp": time.time(),
            }
        except Exception:
            return {"health_score": 0, "active_alerts": 0, "metrics_summary": {}, "timestamp": time.time()}

    async def _save_deployment_data(self, pipeline_state: DeploymentPipelineState) -> None:
        """Save deployment data to file.

        Args:
            pipeline_state: Pipeline state to save
        """
        try:
            deployment_file = self.data_path / f"{pipeline_state.deployment_id}.json"
            deployment_data = asdict(pipeline_state)

            # Convert enum values to strings
            def convert_enums(obj):
                if isinstance(obj, dict):
                    return {k: convert_enums(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_enums(item) for item in obj]
                elif hasattr(obj, "value"):
                    return obj.value
                else:
                    return obj

            deployment_data = convert_enums(deployment_data)

            with open(deployment_file, "w", encoding="utf-8") as f:
                json.dump(deployment_data, f, indent=2)
        except Exception:
            pass  # Don't let save failures affect deployments

    async def _publish_deployment_event(self, event_subtype: str, data: dict[str, Any]) -> None:
        """Publish a deployment pipeline event.

        Args:
            event_subtype: Type of deployment event
            data: Event data
        """
        await self.event_bus.publish(
            Event(type=EventType.CUSTOM, data={"event_subtype": f"deployment_{event_subtype}", **data}, timestamp=time.time(), source="deployment_pipeline", priority=EventPriority.HIGH)
        )

    def _generate_deployment_result(self, pipeline_state: DeploymentPipelineState) -> dict[str, Any]:
        """Generate final deployment result.

        Args:
            pipeline_state: Completed pipeline state

        Returns:
            Dictionary with deployment results
        """
        total_duration = (pipeline_state.completion_time or time.time()) - pipeline_state.start_time

        return {
            "deployment_id": pipeline_state.deployment_id,
            "deployment_name": pipeline_state.config.deployment_name,
            "version": pipeline_state.config.version,
            "environment": pipeline_state.config.environment,
            "success": pipeline_state.final_result == DeploymentResult.SUCCESS,
            "final_result": pipeline_state.final_result.value if pipeline_state.final_result else "unknown",
            "current_phase": pipeline_state.current_phase.value,
            "start_time": pipeline_state.start_time,
            "completion_time": pipeline_state.completion_time,
            "total_duration_minutes": total_duration / 60,
            "phase_results": [asdict(phase) for phase in pipeline_state.phase_results],
            "canary_deployment_id": pipeline_state.canary_deployment_id,
            "rollback_reason": pipeline_state.rollback_reason,
            "metrics": {"start": pipeline_state.metrics_at_start, "completion": pipeline_state.metrics_at_completion},
        }

    # Public API Methods
    async def cancel_deployment(self, deployment_id: str) -> dict[str, Any]:
        """Cancel an active deployment.

        Args:
            deployment_id: ID of deployment to cancel

        Returns:
            Cancellation result
        """
        if deployment_id not in self.active_deployments:
            return {"success": False, "error": "Deployment not found or not active"}

        pipeline_state = self.active_deployments[deployment_id]
        pipeline_state.final_result = DeploymentResult.CANCELLED

        # Attempt rollback if canary is active
        if pipeline_state.canary_deployment_id:
            await self.canary_manager.manual_rollback(reason="Deployment cancelled by user")

        # Publish cancellation event
        await self._publish_deployment_event("deployment_cancelled", {"deployment_id": deployment_id, "cancelled_phase": pipeline_state.current_phase.value, "cancellation_time": time.time()})

        return {"success": True, "deployment_id": deployment_id, "cancelled_phase": pipeline_state.current_phase.value}

    def get_deployment_status(self, deployment_id: str) -> dict[str, Any] | None:
        """Get status of a deployment.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment status or None if not found
        """
        if deployment_id in self.active_deployments:
            pipeline_state = self.active_deployments[deployment_id]
            return {
                "deployment_id": deployment_id,
                "status": "active",
                "current_phase": pipeline_state.current_phase.value,
                "start_time": pipeline_state.start_time,
                "elapsed_minutes": (time.time() - pipeline_state.start_time) / 60,
                "completed_phases": len(pipeline_state.phase_results),
                "canary_deployment_id": pipeline_state.canary_deployment_id,
            }

        # Check deployment history
        for deployment in reversed(self.deployment_history):
            if deployment.deployment_id == deployment_id:
                return {
                    "deployment_id": deployment_id,
                    "status": "completed",
                    "final_result": deployment.final_result.value if deployment.final_result else "unknown",
                    "start_time": deployment.start_time,
                    "completion_time": deployment.completion_time,
                    "total_duration_minutes": ((deployment.completion_time or time.time()) - deployment.start_time) / 60,
                    "completed_phases": len(deployment.phase_results),
                    "rollback_reason": deployment.rollback_reason,
                }

        return None

    def get_active_deployments(self) -> list[dict[str, Any]]:
        """Get list of active deployments.

        Returns:
            List of active deployment summaries
        """
        return [
            {
                "deployment_id": deployment_id,
                "deployment_name": pipeline.config.deployment_name,
                "version": pipeline.config.version,
                "current_phase": pipeline.current_phase.value,
                "start_time": pipeline.start_time,
                "elapsed_minutes": (time.time() - pipeline.start_time) / 60,
            }
            for deployment_id, pipeline in self.active_deployments.items()
        ]

    def get_deployment_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent deployment history.

        Args:
            limit: Maximum number of deployments to return

        Returns:
            List of recent deployment summaries
        """
        recent_deployments = list(self.deployment_history)[-limit:]

        return [
            {
                "deployment_id": deployment.deployment_id,
                "deployment_name": deployment.config.deployment_name,
                "version": deployment.config.version,
                "final_result": deployment.final_result.value if deployment.final_result else "unknown",
                "start_time": deployment.start_time,
                "completion_time": deployment.completion_time,
                "total_duration_minutes": ((deployment.completion_time or time.time()) - deployment.start_time) / 60,
                "rollback_reason": deployment.rollback_reason,
            }
            for deployment in reversed(recent_deployments)
        ]


# Main execution function
async def run_deployment_pipeline(config: DeploymentConfig) -> dict[str, Any]:
    """Run a deployment pipeline with the given configuration.

    Args:
        config: Deployment configuration

    Returns:
        Deployment results
    """
    pipeline = DeploymentPipeline()
    return await pipeline.execute_deployment(config)


if __name__ == "__main__":
    import sys

    # Simple CLI for testing
    if len(sys.argv) < 3:
        print("Usage: deployment_pipeline.py <deployment_name> <version>")
        sys.exit(1)

    deployment_name = sys.argv[1]
    version = sys.argv[2]

    # Create test configuration
    test_config = DeploymentConfig(deployment_name=deployment_name, version=version, environment="test", canary_enabled=True, auto_rollback_enabled=True, monitoring_duration_minutes=5)

    # Run deployment
    result = asyncio.run(run_deployment_pipeline(test_config))

    print(f"Deployment result: {result['final_result']}")
    print(f"Total duration: {result['total_duration_minutes']:.1f} minutes")

    if not result["success"]:
        print(f"Failure reason: {result.get('rollback_reason', 'Unknown')}")
        sys.exit(1)
