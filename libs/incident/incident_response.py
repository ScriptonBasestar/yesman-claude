#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Automated Incident Response System.

This module provides comprehensive incident detection, response automation,
escalation procedures, and integration with monitoring and alerting systems.
"""

import asyncio
import json
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from libs.dashboard.monitoring_integration import AlertSeverity, PerformanceAlert, get_monitoring_dashboard

logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    """Incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Incident status tracking."""

    DETECTED = "detected"
    RESPONDING = "responding"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ResponseActionStatus(Enum):
    """Status of automated response actions."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class IncidentDefinition:
    """Configuration for incident detection and response."""

    name: str
    severity: IncidentSeverity
    conditions: list[str]  # Alert conditions that trigger this incident
    auto_actions: list[str]  # Automated response actions
    notification_channels: list[str]
    escalation_time_minutes: int = 15
    description: str = ""
    runbook_url: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class ResponseAction:
    """Automated response action configuration."""

    action_id: str
    name: str
    description: str
    status: ResponseActionStatus
    start_time: float | None = None
    completion_time: float | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class Incident:
    """Active incident tracking."""

    incident_id: str
    definition: IncidentDefinition
    status: IncidentStatus
    severity: IncidentSeverity
    start_time: float
    triggering_alerts: list[PerformanceAlert]
    response_actions: list[ResponseAction] = field(default_factory=list)
    escalation_time: float | None = None
    resolution_time: float | None = None
    assigned_to: str | None = None
    notes: list[str] = field(default_factory=list)
    metrics_at_start: dict[str, Any] = field(default_factory=dict)
    metrics_at_resolution: dict[str, Any] = field(default_factory=dict)


class IncidentResponseSystem:
    """Automated incident response and management system."""

    def __init__(self) -> None:
        """Initialize the incident response system."""
        self.monitoring = get_monitoring_dashboard()
        self.event_bus = get_event_bus()

        # Incident tracking
        self.active_incidents: dict[str, Incident] = {}
        self.incident_history: deque[Incident] = deque(maxlen=1000)

        # Configuration
        self.incident_definitions = self._load_incident_definitions()
        self.response_handlers: dict[str, Callable] = self._setup_response_handlers()

        # System state
        self._is_running = False
        self._processing_task: asyncio.Task | None = None
        self._escalation_task: asyncio.Task | None = None

        # Notification callbacks
        self._notification_callbacks: list[Callable[[Incident], None]] = []

        # Data persistence
        self.incident_data_path = Path("data/incidents")
        self.incident_data_path.mkdir(parents=True, exist_ok=True)

        # Setup event subscriptions
        self._setup_event_subscriptions()

    def _load_incident_definitions(self) -> list[IncidentDefinition]:
        """Load incident response definitions.

        Returns:
            List of incident definitions
        """
        return [
            IncidentDefinition(
                name="high_error_rate",
                severity=IncidentSeverity.HIGH,
                conditions=["error_rate > 5%", "error_count > 50"],
                auto_actions=["scale_up", "circuit_breaker", "alert_team"],
                notification_channels=["slack", "email"],
                escalation_time_minutes=10,
                description="High error rate detected across the system",
                tags=["performance", "errors"],
            ),
            IncidentDefinition(
                name="system_overload",
                severity=IncidentSeverity.CRITICAL,
                conditions=["cpu_usage > 90%", "memory_usage > 95%", "response_time > 5000ms"],
                auto_actions=["emergency_scale_up", "shed_load", "alert_oncall", "enable_maintenance_mode"],
                notification_channels=["slack", "pagerduty", "phone"],
                escalation_time_minutes=5,
                description="System resources critically overloaded",
                tags=["performance", "resources", "critical"],
            ),
            IncidentDefinition(
                name="security_breach_detected",
                severity=IncidentSeverity.CRITICAL,
                conditions=["security_violations > 0", "failed_auth_attempts > 100", "suspicious_activity_detected"],
                auto_actions=["lock_down", "isolate_affected", "alert_security_team", "capture_forensics"],
                notification_channels=["security_team", "management", "pagerduty"],
                escalation_time_minutes=1,
                description="Potential security breach or attack detected",
                tags=["security", "breach", "critical"],
            ),
            IncidentDefinition(
                name="service_unavailable",
                severity=IncidentSeverity.HIGH,
                conditions=["health_score < 30", "service_down", "connectivity_lost"],
                auto_actions=["restart_services", "failover", "alert_team"],
                notification_channels=["slack", "email", "pagerduty"],
                escalation_time_minutes=5,
                description="Critical services are unavailable",
                tags=["availability", "outage"],
            ),
            IncidentDefinition(
                name="deployment_failure",
                severity=IncidentSeverity.MEDIUM,
                conditions=["deployment_failed", "canary_rollback", "health_check_failed"],
                auto_actions=["rollback_deployment", "alert_devops", "capture_logs"],
                notification_channels=["slack", "email"],
                escalation_time_minutes=15,
                description="Deployment or rollback failure detected",
                tags=["deployment", "devops"],
            ),
            IncidentDefinition(
                name="resource_exhaustion",
                severity=IncidentSeverity.HIGH,
                conditions=["disk_usage > 95%", "memory_leak_detected", "connection_pool_exhausted"],
                auto_actions=["cleanup_resources", "scale_up", "restart_affected_services"],
                notification_channels=["slack", "email"],
                escalation_time_minutes=10,
                description="System resources are being exhausted",
                tags=["resources", "capacity"],
            ),
            IncidentDefinition(
                name="performance_degradation",
                severity=IncidentSeverity.MEDIUM,
                conditions=["response_time > 2000ms", "throughput < baseline_50%", "queue_backup"],
                auto_actions=["scale_up", "optimize_queries", "clear_caches"],
                notification_channels=["slack"],
                escalation_time_minutes=20,
                description="System performance has degraded significantly",
                tags=["performance", "degradation"],
            ),
        ]

    def _setup_response_handlers(self) -> dict[str, Callable]:
        """Setup automated response action handlers.

        Returns:
            Dictionary mapping action names to handler functions
        """
        return {
            "scale_up": self._handle_scale_up,
            "scale_down": self._handle_scale_down,
            "emergency_scale_up": self._handle_emergency_scale_up,
            "circuit_breaker": self._handle_circuit_breaker,
            "shed_load": self._handle_shed_load,
            "restart_services": self._handle_restart_services,
            "failover": self._handle_failover,
            "rollback_deployment": self._handle_rollback_deployment,
            "enable_maintenance_mode": self._handle_enable_maintenance_mode,
            "lock_down": self._handle_lock_down,
            "isolate_affected": self._handle_isolate_affected,
            "cleanup_resources": self._handle_cleanup_resources,
            "optimize_queries": self._handle_optimize_queries,
            "clear_caches": self._handle_clear_caches,
            "capture_logs": self._handle_capture_logs,
            "capture_forensics": self._handle_capture_forensics,
            "alert_team": self._handle_alert_team,
            "alert_oncall": self._handle_alert_oncall,
            "alert_security_team": self._handle_alert_security_team,
            "alert_devops": self._handle_alert_devops,
        }

    def _setup_event_subscriptions(self) -> None:
        """Setup event bus subscriptions for incident detection."""
        self.event_bus.subscribe(EventType.CUSTOM, self._handle_custom_event)
        self.event_bus.subscribe(EventType.PERFORMANCE_ALERT, self._handle_performance_alert)
        self.event_bus.subscribe(EventType.SYSTEM_ERROR, self._handle_system_error)

    async def start(self) -> None:
        """Start the incident response system."""
        if self._is_running:
            return

        self._is_running = True

        # Start processing tasks
        self._processing_task = asyncio.create_task(self._incident_processing_loop())
        self._escalation_task = asyncio.create_task(self._escalation_loop())

        # Register with monitoring dashboard for alerts
        self.monitoring.register_alert_callback(self.handle_alert)

        await self._publish_incident_event("system_started", {"incident_definitions": len(self.incident_definitions), "response_handlers": len(self.response_handlers)})

    async def stop(self) -> None:
        """Stop the incident response system."""
        if not self._is_running:
            return

        self._is_running = False

        # Cancel processing tasks
        for task in [self._processing_task, self._escalation_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await self._publish_incident_event("system_stopped", {"active_incidents": len(self.active_incidents), "total_incidents_handled": len(self.incident_history)})

    async def handle_alert(self, alert: PerformanceAlert) -> None:
        """Handle incoming alert and determine if incident response is needed.

        Args:
            alert: Performance alert to evaluate
        """
        try:
            # Check if this alert matches any incident definitions
            for incident_def in self.incident_definitions:
                if self._matches_incident_conditions(alert, incident_def):
                    await self._trigger_incident_response(incident_def, [alert])
        except Exception as e:
            await self._publish_incident_event("alert_handling_error", {"alert_component": alert.component, "alert_severity": alert.severity.value, "error": str(e)})

    def _matches_incident_conditions(self, alert: PerformanceAlert, incident_def: IncidentDefinition) -> bool:
        """Check if an alert matches incident trigger conditions.

        Args:
            alert: Performance alert
            incident_def: Incident definition

        Returns:
            True if alert matches incident conditions
        """
        # Simple condition matching - in production this would be more sophisticated
        conditions_met = 0

        for condition in incident_def.conditions:
            if self._evaluate_condition(alert, condition):
                conditions_met += 1

        # Require at least one condition to match
        return conditions_met > 0

    def _evaluate_condition(self, alert: PerformanceAlert, condition: str) -> bool:
        """Evaluate a single incident condition against an alert.

        Args:
            alert: Performance alert
            condition: Condition string to evaluate

        Returns:
            True if condition is met
        """
        condition_lower = condition.lower()

        # Error rate conditions
        if "error_rate" in condition_lower and alert.metric_type.value == "error_rate":
            if ">" in condition:
                try:
                    threshold = float(condition.split(">")[1].strip().replace("%", ""))
                    return alert.current_value > threshold
                except (ValueError, IndexError):
                    pass

        # Response time conditions
        if "response_time" in condition_lower and alert.metric_type.value == "response_time":
            if ">" in condition:
                try:
                    threshold = float(condition.split(">")[1].strip().replace("ms", ""))
                    return alert.current_value > threshold
                except (ValueError, IndexError):
                    pass

        # CPU/Memory usage conditions
        if "cpu_usage" in condition_lower or "memory_usage" in condition_lower:
            if alert.metric_type.value in {"cpu_usage", "memory_usage"} and ">" in condition:
                try:
                    threshold = float(condition.split(">")[1].strip().replace("%", ""))
                    return alert.current_value > threshold
                except (ValueError, IndexError):
                    pass

        # Health score conditions
        if "health_score" in condition_lower:
            # Get current health score from monitoring
            health_score = self.monitoring._calculate_health_score()
            if "<" in condition:
                try:
                    threshold = float(condition.split("<")[1].strip())
                    return health_score < threshold
                except (ValueError, IndexError):
                    pass

        # Severity-based matching
        severity_mapping = {
            "critical": [AlertSeverity.CRITICAL],
            "high": [AlertSeverity.CRITICAL, AlertSeverity.ERROR],
            "medium": [AlertSeverity.ERROR, AlertSeverity.WARNING],
            "low": [AlertSeverity.WARNING, AlertSeverity.INFO],
        }

        return alert.severity in severity_mapping.get(condition_lower, [])

    async def _trigger_incident_response(self, incident_def: IncidentDefinition, triggering_alerts: list[PerformanceAlert]) -> None:
        """Trigger automated incident response.

        Args:
            incident_def: Incident definition
            triggering_alerts: Alerts that triggered the incident
        """
        # Check if similar incident is already active
        for incident in self.active_incidents.values():
            if incident.definition.name == incident_def.name and incident.status in {IncidentStatus.DETECTED, IncidentStatus.RESPONDING}:
                # Update existing incident with new alerts
                incident.triggering_alerts.extend(triggering_alerts)
                return

        # Create new incident
        incident_id = f"{incident_def.name}_{int(time.time())}"

        # Capture current system metrics
        current_metrics = {}
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            current_metrics = {
                "health_score": dashboard_data.get("health_score", 0),
                "active_alerts": dashboard_data.get("alerts", {}).get("active", 0),
                "metrics_summary": dashboard_data.get("metrics", {}),
            }
        except Exception as e:
            logger.debug("Failed to collect context data: %s", e)

        incident = Incident(
            incident_id=incident_id,
            definition=incident_def,
            status=IncidentStatus.DETECTED,
            severity=incident_def.severity,
            start_time=time.time(),
            triggering_alerts=triggering_alerts,
            metrics_at_start=current_metrics,
        )

        # Add to active incidents
        self.active_incidents[incident_id] = incident

        # Publish incident created event
        await self._publish_incident_event(
            "incident_created",
            {
                "incident_id": incident_id,
                "incident_name": incident_def.name,
                "severity": incident_def.severity.value,
                "triggering_alerts": len(triggering_alerts),
                "auto_actions": len(incident_def.auto_actions),
                "escalation_time_minutes": incident_def.escalation_time_minutes,
            },
        )

        # Execute automated response actions
        incident.status = IncidentStatus.RESPONDING

        for action_name in incident_def.auto_actions:
            response_action = ResponseAction(action_id=f"{incident_id}_{action_name}", name=action_name, description=f"Automated response: {action_name}", status=ResponseActionStatus.PENDING)
            incident.response_actions.append(response_action)

        # Start executing actions asynchronously
        asyncio.create_task(self._execute_response_actions(incident))

        # Send notifications
        await self._send_notifications(incident)

        # Save incident state
        await self._save_incident_data(incident)

    async def _execute_response_actions(self, incident: Incident) -> None:
        """Execute all automated response actions for an incident.

        Args:
            incident: Incident to execute actions for
        """
        for action in incident.response_actions:
            try:
                action.status = ResponseActionStatus.EXECUTING
                action.start_time = time.time()

                # Get handler for this action
                handler = self.response_handlers.get(action.name)
                if handler:
                    action.result = await handler(incident, action)
                    action.status = ResponseActionStatus.COMPLETED
                else:
                    action.error = f"No handler found for action: {action.name}"
                    action.status = ResponseActionStatus.SKIPPED

                action.completion_time = time.time()

                # Publish action completion event
                await self._publish_incident_event(
                    "action_completed",
                    {
                        "incident_id": incident.incident_id,
                        "action_name": action.name,
                        "status": action.status.value,
                        "execution_time_ms": ((action.completion_time or 0) - (action.start_time or 0)) * 1000,
                        "success": action.status == ResponseActionStatus.COMPLETED,
                    },
                )

            except Exception as e:
                action.error = str(e)
                action.status = ResponseActionStatus.FAILED
                action.completion_time = time.time()

                await self._publish_incident_event("action_failed", {"incident_id": incident.incident_id, "action_name": action.name, "error": str(e)})

        # Check if incident can be auto-resolved
        await self._check_auto_resolution(incident)

    async def _send_notifications(self, incident: Incident) -> None:
        """Send notifications for an incident.

        Args:
            incident: Incident to send notifications for
        """
        notification_data = {
            "incident_id": incident.incident_id,
            "incident_name": incident.definition.name,
            "severity": incident.severity.value,
            "description": incident.definition.description,
            "start_time": incident.start_time,
            "triggering_alerts": len(incident.triggering_alerts),
            "auto_actions": [action.name for action in incident.response_actions],
            "escalation_time_minutes": incident.definition.escalation_time_minutes,
        }

        # Call notification callbacks
        for callback in self._notification_callbacks:
            try:
                callback(incident)
            except Exception as e:
                logger.debug("Notification callback failed: %s", e)

        # Publish notification event
        await self._publish_incident_event("notifications_sent", {"incident_id": incident.incident_id, "channels": incident.definition.notification_channels, "notification_data": notification_data})

    async def _incident_processing_loop(self) -> None:
        """Main incident processing loop."""
        while self._is_running:
            try:
                # Process active incidents
                for incident_id, incident in list(self.active_incidents.items()):
                    await self._process_incident(incident)

                await asyncio.sleep(30)  # Process every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._publish_incident_event("processing_error", {"error": str(e)})
                await asyncio.sleep(30)

    async def _escalation_loop(self) -> None:
        """Loop to handle incident escalation."""
        while self._is_running:
            try:
                current_time = time.time()

                for incident in self.active_incidents.values():
                    # Check if incident needs escalation
                    if (
                        incident.status in {IncidentStatus.DETECTED, IncidentStatus.RESPONDING}
                        and not incident.escalation_time
                        and current_time - incident.start_time > incident.definition.escalation_time_minutes * 60
                    ):
                        await self._escalate_incident(incident)

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._publish_incident_event("escalation_error", {"error": str(e)})
                await asyncio.sleep(60)

    async def _process_incident(self, incident: Incident) -> None:
        """Process a single incident for updates and status changes.

        Args:
            incident: Incident to process
        """
        # Check if incident conditions still exist
        if incident.status == IncidentStatus.RESPONDING:
            # Get current system health
            try:
                health_score = self.monitoring._calculate_health_score()
                active_alerts = len(self.monitoring.get_active_alerts())

                # Simple auto-resolution logic
                if health_score > 80 and active_alerts == 0:
                    await self._resolve_incident(incident, "System health restored")

            except Exception as e:
                logger.debug("Auto resolution check failed: %s", e)

    async def _escalate_incident(self, incident: Incident) -> None:
        """Escalate an incident to higher priority.

        Args:
            incident: Incident to escalate
        """
        incident.status = IncidentStatus.ESCALATED
        incident.escalation_time = time.time()

        await self._publish_incident_event(
            "incident_escalated",
            {
                "incident_id": incident.incident_id,
                "incident_name": incident.definition.name,
                "severity": incident.severity.value,
                "escalation_time": incident.escalation_time,
                "time_to_escalation_minutes": (incident.escalation_time - incident.start_time) / 60,
            },
        )

        # Send escalation notifications
        await self._send_notifications(incident)

        # Save updated state
        await self._save_incident_data(incident)

    async def _resolve_incident(self, incident: Incident, resolution_note: str) -> None:
        """Resolve an incident.

        Args:
            incident: Incident to resolve
            resolution_note: Note describing the resolution
        """
        incident.status = IncidentStatus.RESOLVED
        incident.resolution_time = time.time()
        incident.notes.append(f"Auto-resolved: {resolution_note}")

        # Capture metrics at resolution
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            incident.metrics_at_resolution = {
                "health_score": dashboard_data.get("health_score", 0),
                "active_alerts": dashboard_data.get("alerts", {}).get("active", 0),
                "metrics_summary": dashboard_data.get("metrics", {}),
            }
        except Exception as e:
            logger.debug("Context collection failed: %s", e)

        await self._publish_incident_event(
            "incident_resolved",
            {
                "incident_id": incident.incident_id,
                "incident_name": incident.definition.name,
                "resolution_time": incident.resolution_time,
                "total_duration_minutes": (incident.resolution_time - incident.start_time) / 60,
                "resolution_note": resolution_note,
                "actions_executed": len([a for a in incident.response_actions if a.status == ResponseActionStatus.COMPLETED]),
                "actions_failed": len([a for a in incident.response_actions if a.status == ResponseActionStatus.FAILED]),
            },
        )

        # Move to history and remove from active
        self.incident_history.append(incident)
        if incident.incident_id in self.active_incidents:
            del self.active_incidents[incident.incident_id]

        # Save final state
        await self._save_incident_data(incident)

    async def _check_auto_resolution(self, incident: Incident) -> None:
        """Check if incident can be automatically resolved.

        Args:
            incident: Incident to check
        """
        # Count successful actions
        successful_actions = len([a for a in incident.response_actions if a.status == ResponseActionStatus.COMPLETED])
        total_actions = len(incident.response_actions)

        if total_actions > 0 and successful_actions == total_actions:
            # All actions completed successfully
            await asyncio.sleep(30)  # Wait a bit before checking resolution

            try:
                health_score = self.monitoring._calculate_health_score()
                active_alerts = len(self.monitoring.get_active_alerts())

                if health_score > 70:  # Improved health
                    await self._resolve_incident(incident, "All automated actions completed successfully and system health improved")
            except Exception:
                pass

    # Response Action Handlers
    async def _handle_scale_up(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle scale up action."""
        # Mock implementation - would integrate with actual scaling systems
        await asyncio.sleep(1)  # Simulate scaling time
        return {"action": "scale_up", "instances_added": 1, "new_instance_count": 3, "scaling_provider": "mock"}

    async def _handle_emergency_scale_up(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle emergency scale up action."""
        await asyncio.sleep(0.5)  # Faster emergency scaling
        return {"action": "emergency_scale_up", "instances_added": 2, "new_instance_count": 4, "scaling_provider": "mock"}

    async def _handle_scale_down(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle scale down action."""
        await asyncio.sleep(1)
        return {"action": "scale_down", "instances_removed": 1, "new_instance_count": 2, "scaling_provider": "mock"}

    async def _handle_circuit_breaker(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle circuit breaker activation."""
        return {"action": "circuit_breaker", "circuit_state": "open", "affected_services": ["api", "database"]}

    async def _handle_shed_load(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle load shedding action."""
        return {"action": "shed_load", "load_shed_percentage": 20, "affected_endpoints": ["non-critical-api"]}

    async def _handle_restart_services(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle service restart action."""
        await asyncio.sleep(2)  # Simulate restart time
        return {"action": "restart_services", "services_restarted": ["app-server", "background-worker"], "restart_duration_seconds": 2}

    async def _handle_failover(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle failover action."""
        return {"action": "failover", "primary_region": "us-east-1", "failover_region": "us-west-2", "services_failed_over": ["api", "database"]}

    async def _handle_rollback_deployment(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle deployment rollback action."""
        return {"action": "rollback_deployment", "previous_version": "v1.2.3", "rollback_version": "v1.2.2", "rollback_completed": True}

    async def _handle_enable_maintenance_mode(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle maintenance mode activation."""
        return {"action": "enable_maintenance_mode", "maintenance_mode": True, "maintenance_message": "System temporarily under maintenance"}

    async def _handle_lock_down(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle security lockdown action."""
        return {"action": "lock_down", "security_level": "high", "access_restricted": True, "lockdown_scope": ["external_access", "admin_functions"]}

    async def _handle_isolate_affected(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle isolation of affected systems."""
        return {"action": "isolate_affected", "isolated_components": ["suspicious-node-1", "compromised-service"], "isolation_method": "network_quarantine"}

    async def _handle_cleanup_resources(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle resource cleanup action."""
        return {"action": "cleanup_resources", "cleaned_items": ["temp_files", "old_logs", "unused_connections"], "space_freed_mb": 1024}

    async def _handle_optimize_queries(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle query optimization action."""
        return {"action": "optimize_queries", "optimizations_applied": ["query_cache", "index_hints"], "performance_improvement_percent": 15}

    async def _handle_clear_caches(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle cache clearing action."""
        return {"action": "clear_caches", "caches_cleared": ["redis", "memcached", "application_cache"], "cache_hit_rate_reset": True}

    async def _handle_capture_logs(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle log capture action."""
        return {"action": "capture_logs", "log_files_captured": ["app.log", "error.log", "access.log"], "log_archive_location": "/var/log/incident_logs/incident_" + incident.incident_id}

    async def _handle_capture_forensics(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle forensic data capture action."""
        return {"action": "capture_forensics", "forensic_data": ["memory_dump", "network_capture", "system_state"], "forensic_archive_location": "/var/forensics/incident_" + incident.incident_id}

    async def _handle_alert_team(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle team alerting action."""
        return {"action": "alert_team", "teams_alerted": ["dev_team", "ops_team"], "notification_channels": ["slack", "email"]}

    async def _handle_alert_oncall(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle on-call alerting action."""
        return {"action": "alert_oncall", "oncall_person": "ops_engineer_primary", "notification_methods": ["pagerduty", "phone", "sms"]}

    async def _handle_alert_security_team(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle security team alerting action."""
        return {"action": "alert_security_team", "security_contacts": ["security_lead", "ciso"], "notification_priority": "urgent"}

    async def _handle_alert_devops(self, incident: Incident, action: ResponseAction) -> dict[str, Any]:
        """Handle DevOps team alerting action."""
        return {"action": "alert_devops", "devops_contacts": ["devops_lead", "platform_team"], "context": "deployment_related_incident"}

    async def _handle_custom_event(self, event: Event) -> None:
        """Handle custom events that might trigger incidents."""
        # Check for specific event subtypes that should trigger incidents
        event_subtype = event.data.get("event_subtype", "")

        if event_subtype in {"canary_rollback", "deployment_failed", "security_violation"}:
            # Create a synthetic alert to trigger incident processing
            alert = PerformanceAlert(
                timestamp=event.timestamp,
                severity=AlertSeverity.ERROR,
                metric_type="custom",
                component=event.source,
                current_value=1,
                threshold=0,
                message=f"Event-triggered alert: {event_subtype}",
                context=event.data,
            )
            await self.handle_alert(alert)

    async def _handle_performance_alert(self, event: Event) -> None:
        """Handle performance alert events."""
        # Convert event to PerformanceAlert if needed
        pass  # Already handled by direct alert callback

    async def _handle_system_error(self, event: Event) -> None:
        """Handle system error events."""
        # Create alert from system error
        alert = PerformanceAlert(
            timestamp=event.timestamp,
            severity=AlertSeverity.ERROR,
            metric_type="system_error",
            component=event.source,
            current_value=1,
            threshold=0,
            message="System error detected",
            context=event.data,
        )
        await self.handle_alert(alert)

    async def _save_incident_data(self, incident: Incident) -> None:
        """Save incident data to file.

        Args:
            incident: Incident to save
        """
        try:
            incident_file = self.incident_data_path / f"{incident.incident_id}.json"
            incident_data = asdict(incident)

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

            incident_data = convert_enums(incident_data)

            with open(incident_file, "w", encoding="utf-8") as f:
                json.dump(incident_data, f, indent=2)
        except Exception as e:
            logger.debug("Context collection failed: %s", e)  # Don't let save failures affect incident handling

    async def _publish_incident_event(self, event_subtype: str, data: dict[str, Any]) -> None:
        """Publish an incident response event.

        Args:
            event_subtype: Type of incident event
            data: Event data
        """
        await self.event_bus.publish(
            Event(type=EventType.CUSTOM, data={"event_subtype": f"incident_{event_subtype}", **data}, timestamp=time.time(), source="incident_response", priority=EventPriority.HIGH)
        )

    def register_notification_callback(self, callback: Callable[[Incident], None]) -> None:
        """Register a callback for incident notifications.

        Args:
            callback: Function to call when incident notifications are sent
        """
        self._notification_callbacks.append(callback)

    def get_active_incidents(self) -> list[Incident]:
        """Get list of active incidents.

        Returns:
            List of active incidents
        """
        return list(self.active_incidents.values())

    def get_incident_history(self, limit: int = 10) -> list[Incident]:
        """Get recent incident history.

        Args:
            limit: Maximum number of incidents to return

        Returns:
            List of recent incidents
        """
        return list(self.incident_history)[-limit:]

    def get_incident_statistics(self) -> dict[str, Any]:
        """Get incident response statistics.

        Returns:
            Dictionary with incident statistics
        """
        total_incidents = len(self.incident_history) + len(self.active_incidents)
        resolved_incidents = len([i for i in self.incident_history if i.status == IncidentStatus.RESOLVED])

        if self.incident_history:
            avg_resolution_time = sum((i.resolution_time - i.start_time) for i in self.incident_history if i.resolution_time) / len([i for i in self.incident_history if i.resolution_time])
        else:
            avg_resolution_time = 0

        return {
            "total_incidents": total_incidents,
            "active_incidents": len(self.active_incidents),
            "resolved_incidents": resolved_incidents,
            "resolution_rate": resolved_incidents / total_incidents if total_incidents > 0 else 0,
            "avg_resolution_time_minutes": avg_resolution_time / 60 if avg_resolution_time > 0 else 0,
            "incident_definitions": len(self.incident_definitions),
            "response_handlers": len(self.response_handlers),
            "system_running": self._is_running,
        }
