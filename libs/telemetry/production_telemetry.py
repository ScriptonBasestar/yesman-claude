#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Production Telemetry and Auto-scaling System.

This module provides comprehensive production telemetry collection,
real-time analysis, and automated scaling decisions based on system metrics.
"""

import asyncio
import json
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from libs.dashboard.monitoring_integration import get_monitoring_dashboard


class ScalingAction(Enum):
    """Types of scaling actions."""

    NONE = "none"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    EMERGENCY_SCALE_UP = "emergency_scale_up"


class ScalingUrgency(Enum):
    """Urgency levels for scaling actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """System metrics data structure."""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_total_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_total_gb: float
    disk_free_gb: float
    network_io: dict[str, int]
    active_connections: int
    process_count: int
    load_average: list[float]
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    throughput_rps: float = 0.0


@dataclass
class ScalingDecision:
    """Auto-scaling decision data structure."""

    action: ScalingAction
    urgency: ScalingUrgency
    reason: str
    confidence: float
    recommended_instances: int
    metrics: SystemMetrics
    timestamp: float
    trigger_thresholds: dict[str, float] = field(default_factory=dict)


@dataclass
class OptimizationRecommendation:
    """System optimization recommendation."""

    category: str  # 'performance', 'cost', 'reliability'
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    impact: str
    implementation_effort: str
    estimated_savings: dict[str, Any] | None = None
    technical_details: dict[str, Any] = field(default_factory=dict)


class ProductionTelemetryCollector:
    """Comprehensive production telemetry collection and analysis system."""

    def __init__(self, collection_interval: float = 5.0) -> None:
        """Initialize the production telemetry collector.

        Args:
            collection_interval: Interval between metric collections in seconds
        """
        self.collection_interval = collection_interval
        self.monitoring = get_monitoring_dashboard()
        self.event_bus = get_event_bus()

        # Metrics storage
        self.metrics_buffer: deque[SystemMetrics] = deque(maxlen=1000)
        self.scaling_decisions: deque[ScalingDecision] = deque(maxlen=100)
        self.optimization_recommendations: list[OptimizationRecommendation] = []

        # Configuration
        self.scaling_config = {
            # CPU thresholds
            "cpu_scale_up_threshold": 80.0,
            "cpu_scale_down_threshold": 20.0,
            "cpu_emergency_threshold": 95.0,
            # Memory thresholds
            "memory_scale_up_threshold": 80.0,
            "memory_scale_down_threshold": 30.0,
            "memory_emergency_threshold": 95.0,
            # Combined thresholds
            "combined_scale_up_threshold": 70.0,
            "combined_scale_down_threshold": 25.0,
            # Response time thresholds
            "response_time_scale_up_ms": 1000.0,
            "response_time_emergency_ms": 5000.0,
            # Error rate thresholds
            "error_rate_scale_up_percent": 5.0,
            "error_rate_emergency_percent": 10.0,
            # Scaling constraints
            "min_instances": 1,
            "max_instances": 10,
            "scale_up_step": 1,
            "scale_down_step": 1,
            "cooldown_minutes": 5,
            "emergency_cooldown_minutes": 1,
            # Analysis windows
            "decision_window_minutes": 10,
            "trend_analysis_minutes": 30,
        }

        # State tracking
        self._is_running = False
        self._collection_task: asyncio.Task | None = None
        self._analysis_task: asyncio.Task | None = None
        self._optimization_task: asyncio.Task | None = None
        self._last_scaling_action: float | None = None
        self._current_instances = 1  # Mock current instance count

        # Callbacks for scaling actions
        self._scaling_callbacks: list[Callable[[ScalingDecision], None]] = []

        # Data persistence
        self.data_path = Path("data/production_telemetry")
        self.data_path.mkdir(parents=True, exist_ok=True)

    async def start_collection(self) -> None:
        """Start production telemetry collection and analysis."""
        if self._is_running:
            return

        self._is_running = True

        # Start collection tasks
        self._collection_task = asyncio.create_task(self._collection_loop())
        self._analysis_task = asyncio.create_task(self._analysis_loop())
        self._optimization_task = asyncio.create_task(self._optimization_loop())

        # Publish telemetry start event
        await self._publish_telemetry_event("telemetry_started", {"collection_interval": self.collection_interval, "buffer_size": self.metrics_buffer.maxlen, "scaling_enabled": True})

    async def stop_collection(self) -> None:
        """Stop production telemetry collection and analysis."""
        if not self._is_running:
            return

        self._is_running = False

        # Cancel tasks
        for task in [self._collection_task, self._analysis_task, self._optimization_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Publish telemetry stop event
        await self._publish_telemetry_event("telemetry_stopped", {"collected_samples": len(self.metrics_buffer), "scaling_decisions": len(self.scaling_decisions)})

    async def _collection_loop(self) -> None:
        """Main telemetry collection loop."""
        while self._is_running:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                self.metrics_buffer.append(metrics)

                # Publish metrics collected event
                await self._publish_telemetry_event(
                    "metrics_collected",
                    {
                        "timestamp": metrics.timestamp,
                        "cpu_percent": metrics.cpu_percent,
                        "memory_percent": metrics.memory_percent,
                        "response_time_ms": metrics.response_time_ms,
                        "active_connections": metrics.active_connections,
                        "buffer_size": len(self.metrics_buffer),
                    },
                )

                # Save metrics to file periodically
                if len(self.metrics_buffer) % 100 == 0:
                    await self._save_metrics_snapshot()

                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._publish_telemetry_event("collection_error", {"error": str(e), "error_type": type(e).__name__})
                await asyncio.sleep(self.collection_interval)

    async def _analysis_loop(self) -> None:
        """Analysis loop for scaling decisions and trend detection."""
        while self._is_running:
            try:
                if len(self.metrics_buffer) >= 10:
                    # Analyze scaling needs
                    scaling_decision = await self._analyze_scaling_needs()

                    if scaling_decision.action != ScalingAction.NONE:
                        # Store scaling decision
                        self.scaling_decisions.append(scaling_decision)

                        # Execute scaling action
                        await self._trigger_scaling_action(scaling_decision)

                    # Analyze trends for optimization recommendations
                    if len(self.metrics_buffer) >= 100:
                        await self._analyze_optimization_opportunities()

                await asyncio.sleep(60)  # Analyze every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._publish_telemetry_event("analysis_error", {"error": str(e), "error_type": type(e).__name__})
                await asyncio.sleep(60)

    async def _optimization_loop(self) -> None:
        """Loop for generating optimization recommendations."""
        while self._is_running:
            try:
                # Generate optimization recommendations every 30 minutes
                if len(self.metrics_buffer) >= 360:  # 30 minutes of data
                    recommendations = await self._generate_optimization_recommendations()
                    self.optimization_recommendations.extend(recommendations)

                    if recommendations:
                        await self._publish_telemetry_event(
                            "optimization_recommendations",
                            {
                                "new_recommendations": len(recommendations),
                                "total_recommendations": len(self.optimization_recommendations),
                                "categories": list(set(r.category for r in recommendations)),
                            },
                        )

                await asyncio.sleep(1800)  # Every 30 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._publish_telemetry_event("optimization_error", {"error": str(e), "error_type": type(e).__name__})
                await asyncio.sleep(1800)

    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics.

        Returns:
            SystemMetrics object with current system state
        """
        try:
            import psutil

            # Basic system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage("/")
            network_info = psutil.net_io_counters()
            load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0, 0, 0]

            # Application-specific metrics from monitoring
            app_metrics = await self._get_application_metrics()

            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_info.percent,
                memory_total_gb=memory_info.total / (1024**3),
                memory_available_gb=memory_info.available / (1024**3),
                disk_usage_percent=disk_info.percent,
                disk_total_gb=disk_info.total / (1024**3),
                disk_free_gb=disk_info.free / (1024**3),
                network_io={"bytes_sent": network_info.bytes_sent, "bytes_recv": network_info.bytes_recv, "packets_sent": network_info.packets_sent, "packets_recv": network_info.packets_recv},
                active_connections=len(psutil.net_connections()),
                process_count=len(psutil.pids()),
                load_average=list(load_avg),
                response_time_ms=app_metrics.get("response_time_ms", 0.0),
                error_rate=app_metrics.get("error_rate", 0.0),
                throughput_rps=app_metrics.get("throughput_rps", 0.0),
            )

        except ImportError:
            # Return mock metrics if psutil is not available
            app_metrics = await self._get_application_metrics()
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=20.0,
                memory_percent=30.0,
                memory_total_gb=8.0,
                memory_available_gb=5.6,
                disk_usage_percent=45.0,
                disk_total_gb=100.0,
                disk_free_gb=55.0,
                network_io={"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0},
                active_connections=10,
                process_count=50,
                load_average=[0.5, 0.6, 0.7],
                response_time_ms=app_metrics.get("response_time_ms", 50.0),
                error_rate=app_metrics.get("error_rate", 0.1),
                throughput_rps=app_metrics.get("throughput_rps", 100.0),
            )
        except Exception as e:
            # Return error metrics
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_total_gb=0.0,
                memory_available_gb=0.0,
                disk_usage_percent=0.0,
                disk_total_gb=0.0,
                disk_free_gb=0.0,
                network_io={"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0},
                active_connections=0,
                process_count=0,
                load_average=[0, 0, 0],
                response_time_ms=0.0,
                error_rate=0.0,
                throughput_rps=0.0,
            )

    async def _get_application_metrics(self) -> dict[str, float]:
        """Get application-specific performance metrics.

        Returns:
            Dictionary with application metrics
        """
        try:
            # Get metrics from monitoring dashboard
            dashboard_data = await self.monitoring._prepare_dashboard_data()

            # Extract aggregated metrics
            total_response_time = 0.0
            total_samples = 0
            max_error_rate = 0.0

            if dashboard_data.get("metrics"):
                for component, metrics in dashboard_data["metrics"].items():
                    if "response_time" in metrics:
                        rt_data = metrics["response_time"]
                        total_response_time += rt_data.get("average", 0) * rt_data.get("samples", 1)
                        total_samples += rt_data.get("samples", 1)

                    if "error_rate" in metrics:
                        max_error_rate = max(max_error_rate, metrics["error_rate"].get("average", 0))

            avg_response_time = total_response_time / total_samples if total_samples > 0 else 0.0
            throughput = total_samples / 60.0 if total_samples > 0 else 0.0  # Rough RPS estimate

            return {"response_time_ms": avg_response_time, "error_rate": max_error_rate, "throughput_rps": throughput}
        except Exception:
            return {"response_time_ms": 50.0, "error_rate": 0.1, "throughput_rps": 10.0}

    async def _analyze_scaling_needs(self) -> ScalingDecision:
        """Analyze if scaling actions are needed based on current metrics.

        Returns:
            ScalingDecision with recommended action
        """
        if not self.metrics_buffer:
            return ScalingDecision(
                action=ScalingAction.NONE,
                urgency=ScalingUrgency.LOW,
                reason="No metrics available",
                confidence=0.0,
                recommended_instances=self._current_instances,
                metrics=SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=0,
                    memory_percent=0,
                    memory_total_gb=0,
                    memory_available_gb=0,
                    disk_usage_percent=0,
                    disk_total_gb=0,
                    disk_free_gb=0,
                    network_io={},
                    active_connections=0,
                    process_count=0,
                    load_average=[],
                ),
                timestamp=time.time(),
            )

        # Check cooldown period
        if self._last_scaling_action:
            minutes_since_last = (time.time() - self._last_scaling_action) / 60
            required_cooldown = self.scaling_config["cooldown_minutes"]

            if minutes_since_last < required_cooldown:
                return ScalingDecision(
                    action=ScalingAction.NONE,
                    urgency=ScalingUrgency.LOW,
                    reason=f"Cooldown period active ({required_cooldown - minutes_since_last:.1f} minutes remaining)",
                    confidence=0.0,
                    recommended_instances=self._current_instances,
                    metrics=self.metrics_buffer[-1],
                    timestamp=time.time(),
                )

        # Analyze recent metrics (last 10 samples)
        recent_metrics = list(self.metrics_buffer)[-10:]
        current_metrics = recent_metrics[-1]

        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
        max_error_rate = max(m.error_rate for m in recent_metrics)

        # Decision variables
        scale_up_reasons = []
        scale_down_reasons = []
        emergency_reasons = []
        confidence = 0.0

        # CPU analysis
        if avg_cpu > self.scaling_config["cpu_emergency_threshold"]:
            emergency_reasons.append(f"CPU usage critical ({avg_cpu:.1f}%)")
            confidence += 0.4
        elif avg_cpu > self.scaling_config["cpu_scale_up_threshold"]:
            scale_up_reasons.append(f"High CPU usage ({avg_cpu:.1f}%)")
            confidence += 0.3
        elif avg_cpu < self.scaling_config["cpu_scale_down_threshold"]:
            scale_down_reasons.append(f"Low CPU usage ({avg_cpu:.1f}%)")
            confidence += 0.2

        # Memory analysis
        if avg_memory > self.scaling_config["memory_emergency_threshold"]:
            emergency_reasons.append(f"Memory usage critical ({avg_memory:.1f}%)")
            confidence += 0.4
        elif avg_memory > self.scaling_config["memory_scale_up_threshold"]:
            scale_up_reasons.append(f"High memory usage ({avg_memory:.1f}%)")
            confidence += 0.3
        elif avg_memory < self.scaling_config["memory_scale_down_threshold"]:
            scale_down_reasons.append(f"Low memory usage ({avg_memory:.1f}%)")
            confidence += 0.2

        # Response time analysis
        if avg_response_time > self.scaling_config["response_time_emergency_ms"]:
            emergency_reasons.append(f"Response time critical ({avg_response_time:.0f}ms)")
            confidence += 0.3
        elif avg_response_time > self.scaling_config["response_time_scale_up_ms"]:
            scale_up_reasons.append(f"High response time ({avg_response_time:.0f}ms)")
            confidence += 0.2

        # Error rate analysis
        if max_error_rate > self.scaling_config["error_rate_emergency_percent"]:
            emergency_reasons.append(f"Error rate critical ({max_error_rate:.1f}%)")
            confidence += 0.3
        elif max_error_rate > self.scaling_config["error_rate_scale_up_percent"]:
            scale_up_reasons.append(f"High error rate ({max_error_rate:.1f}%)")
            confidence += 0.2

        # Combined analysis
        combined_load = (avg_cpu + avg_memory) / 2
        if combined_load > self.scaling_config["combined_scale_up_threshold"]:
            scale_up_reasons.append(f"High combined load ({combined_load:.1f}%)")
            confidence += 0.2
        elif combined_load < self.scaling_config["combined_scale_down_threshold"]:
            scale_down_reasons.append(f"Low combined load ({combined_load:.1f}%)")
            confidence += 0.1

        # Make scaling decision
        if emergency_reasons:
            action = ScalingAction.EMERGENCY_SCALE_UP
            urgency = ScalingUrgency.CRITICAL
            reason = "; ".join(emergency_reasons)
            recommended_instances = min(self._current_instances + 2, self.scaling_config["max_instances"])
        elif scale_up_reasons and len(scale_up_reasons) >= 2:
            action = ScalingAction.SCALE_UP
            urgency = ScalingUrgency.HIGH if confidence > 0.7 else ScalingUrgency.MEDIUM
            reason = "; ".join(scale_up_reasons)
            recommended_instances = min(self._current_instances + self.scaling_config["scale_up_step"], self.scaling_config["max_instances"])
        elif scale_down_reasons and len(scale_down_reasons) >= 2:
            action = ScalingAction.SCALE_DOWN
            urgency = ScalingUrgency.LOW
            reason = "; ".join(scale_down_reasons)
            recommended_instances = max(self._current_instances - self.scaling_config["scale_down_step"], self.scaling_config["min_instances"])
        else:
            action = ScalingAction.NONE
            urgency = ScalingUrgency.LOW
            reason = "System within normal parameters"
            recommended_instances = self._current_instances

        return ScalingDecision(
            action=action,
            urgency=urgency,
            reason=reason,
            confidence=min(confidence, 1.0),
            recommended_instances=recommended_instances,
            metrics=current_metrics,
            timestamp=time.time(),
            trigger_thresholds={
                "cpu_scale_up": self.scaling_config["cpu_scale_up_threshold"],
                "memory_scale_up": self.scaling_config["memory_scale_up_threshold"],
                "response_time_scale_up": self.scaling_config["response_time_scale_up_ms"],
                "error_rate_scale_up": self.scaling_config["error_rate_scale_up_percent"],
            },
        )

    async def _trigger_scaling_action(self, decision: ScalingDecision) -> None:
        """Trigger the scaling action based on decision.

        Args:
            decision: The scaling decision to execute
        """
        try:
            # Mock scaling implementation - in production this would:
            # - Call cloud provider APIs (AWS Auto Scaling, GCP MIG, Azure VMSS)
            # - Update Kubernetes HPA/VPA
            # - Adjust container orchestration
            # - Update load balancer configuration

            old_instances = self._current_instances
            self._current_instances = decision.recommended_instances
            self._last_scaling_action = decision.timestamp

            # Execute scaling callbacks
            for callback in self._scaling_callbacks:
                try:
                    callback(decision)
                except Exception:
                    pass

            # Publish scaling action event
            await self._publish_telemetry_event(
                "scaling_action_triggered",
                {
                    "action": decision.action.value,
                    "urgency": decision.urgency.value,
                    "reason": decision.reason,
                    "confidence": decision.confidence,
                    "old_instances": old_instances,
                    "new_instances": self._current_instances,
                    "instance_change": self._current_instances - old_instances,
                    "trigger_metrics": {
                        "cpu_percent": decision.metrics.cpu_percent,
                        "memory_percent": decision.metrics.memory_percent,
                        "response_time_ms": decision.metrics.response_time_ms,
                        "error_rate": decision.metrics.error_rate,
                    },
                    "trigger_thresholds": decision.trigger_thresholds,
                },
            )

        except Exception as e:
            await self._publish_telemetry_event("scaling_action_error", {"action": decision.action.value, "error": str(e), "error_type": type(e).__name__})

    async def _analyze_optimization_opportunities(self) -> None:
        """Analyze system metrics to identify optimization opportunities."""
        if len(self.metrics_buffer) < 100:
            return

        # Clear old recommendations
        self.optimization_recommendations.clear()

        # Analyze trends over different time windows
        recent_metrics = list(self.metrics_buffer)

        # CPU optimization analysis
        cpu_values = [m.cpu_percent for m in recent_metrics[-60:]]  # Last 5 minutes
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)

        if avg_cpu < 20 and max_cpu < 50:
            self.optimization_recommendations.append(
                OptimizationRecommendation(
                    category="cost",
                    priority="medium",
                    title="Consider downsizing instances",
                    description=f"Average CPU utilization is low ({avg_cpu:.1f}%), indicating over-provisioning",
                    impact="20-40% cost reduction",
                    implementation_effort="medium",
                    estimated_savings={"monthly_cost_reduction_percent": 30},
                    technical_details={"avg_cpu_percent": avg_cpu, "max_cpu_percent": max_cpu, "recommendation": "Consider smaller instance types or reduced instance count"},
                )
            )
        elif avg_cpu > 80:
            self.optimization_recommendations.append(
                OptimizationRecommendation(
                    category="performance",
                    priority="high",
                    title="CPU optimization needed",
                    description=f"High CPU utilization ({avg_cpu:.1f}%) may impact performance",
                    impact="Improved response times and system stability",
                    implementation_effort="medium",
                    technical_details={"avg_cpu_percent": avg_cpu, "max_cpu_percent": max_cpu, "recommendation": "Scale up instances or optimize CPU-intensive operations"},
                )
            )

        # Memory optimization analysis
        memory_values = [m.memory_percent for m in recent_metrics[-60:]]
        avg_memory = sum(memory_values) / len(memory_values)

        if avg_memory > 85:
            self.optimization_recommendations.append(
                OptimizationRecommendation(
                    category="reliability",
                    priority="high",
                    title="Memory optimization required",
                    description=f"High memory utilization ({avg_memory:.1f}%) poses stability risk",
                    impact="Reduced risk of out-of-memory errors",
                    implementation_effort="high",
                    technical_details={"avg_memory_percent": avg_memory, "recommendation": "Investigate memory leaks, optimize caching, or scale up"},
                )
            )

        # Response time analysis
        response_times = [m.response_time_ms for m in recent_metrics[-60:] if m.response_time_ms > 0]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)

            if avg_response_time > 500:
                self.optimization_recommendations.append(
                    OptimizationRecommendation(
                        category="performance",
                        priority="high",
                        title="Response time optimization needed",
                        description=f"Average response time ({avg_response_time:.0f}ms) exceeds target",
                        impact="Improved user experience and system throughput",
                        implementation_effort="high",
                        technical_details={"avg_response_time_ms": avg_response_time, "recommendation": "Optimize database queries, add caching, or scale horizontally"},
                    )
                )

        # Resource utilization patterns
        await self._analyze_utilization_patterns(recent_metrics)

    async def _analyze_utilization_patterns(self, metrics: list[SystemMetrics]) -> None:
        """Analyze resource utilization patterns for optimization opportunities.

        Args:
            metrics: List of system metrics to analyze
        """
        if len(metrics) < 100:
            return

        # Analyze daily patterns (if we have enough data)
        hours_of_data = (metrics[-1].timestamp - metrics[0].timestamp) / 3600

        if hours_of_data > 2:  # At least 2 hours of data
            # Find low and high utilization periods
            cpu_by_hour = {}
            for metric in metrics:
                hour = time.strftime("%H", time.localtime(metric.timestamp))
                if hour not in cpu_by_hour:
                    cpu_by_hour[hour] = []
                cpu_by_hour[hour].append(metric.cpu_percent)

            # Calculate hourly averages
            hourly_avg_cpu = {hour: sum(values) / len(values) for hour, values in cpu_by_hour.items() if values}

            if hourly_avg_cpu:
                min_hour = min(hourly_avg_cpu, key=hourly_avg_cpu.get)
                max_hour = max(hourly_avg_cpu, key=hourly_avg_cpu.get)
                min_cpu = hourly_avg_cpu[min_hour]
                max_cpu = hourly_avg_cpu[max_hour]

                if max_cpu - min_cpu > 40:  # Significant variation
                    self.optimization_recommendations.append(
                        OptimizationRecommendation(
                            category="cost",
                            priority="medium",
                            title="Implement time-based auto-scaling",
                            description=f"CPU usage varies significantly: {min_cpu:.1f}% at {min_hour}:00, {max_cpu:.1f}% at {max_hour}:00",
                            impact="15-25% cost reduction through better resource utilization",
                            implementation_effort="medium",
                            estimated_savings={"monthly_cost_reduction_percent": 20},
                            technical_details={
                                "low_usage_hour": min_hour,
                                "low_usage_cpu": min_cpu,
                                "high_usage_hour": max_hour,
                                "high_usage_cpu": max_cpu,
                                "recommendation": "Configure scheduled scaling policies",
                            },
                        )
                    )

    async def _generate_optimization_recommendations(self) -> list[OptimizationRecommendation]:
        """Generate optimization recommendations based on collected data.

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        if len(self.metrics_buffer) < 100:
            return recommendations

        recent_metrics = list(self.metrics_buffer)[-100:]  # Last ~8 minutes

        # Network I/O analysis
        if recent_metrics[0].network_io and recent_metrics[-1].network_io:
            bytes_sent_diff = recent_metrics[-1].network_io["bytes_sent"] - recent_metrics[0].network_io["bytes_sent"]
            bytes_recv_diff = recent_metrics[-1].network_io["bytes_recv"] - recent_metrics[0].network_io["bytes_recv"]

            # Convert to MB/s
            time_diff = recent_metrics[-1].timestamp - recent_metrics[0].timestamp
            if time_diff > 0:
                send_mbps = (bytes_sent_diff / (1024**2)) / time_diff
                recv_mbps = (bytes_recv_diff / (1024**2)) / time_diff

                if send_mbps > 100 or recv_mbps > 100:  # High network usage
                    recommendations.append(
                        OptimizationRecommendation(
                            category="performance",
                            priority="medium",
                            title="High network I/O detected",
                            description=f"Network usage: {send_mbps:.1f} MB/s out, {recv_mbps:.1f} MB/s in",
                            impact="Reduced latency and bandwidth costs",
                            implementation_effort="medium",
                            technical_details={"send_mbps": send_mbps, "recv_mbps": recv_mbps, "recommendation": "Consider data compression, CDN, or local caching"},
                        )
                    )

        # Disk usage analysis
        disk_metrics = [m for m in recent_metrics if m.disk_usage_percent > 0]
        if disk_metrics:
            avg_disk_usage = sum(m.disk_usage_percent for m in disk_metrics) / len(disk_metrics)

            if avg_disk_usage > 80:
                recommendations.append(
                    OptimizationRecommendation(
                        category="reliability",
                        priority="high",
                        title="Disk space optimization needed",
                        description=f"Disk usage is high ({avg_disk_usage:.1f}%)",
                        impact="Prevented service disruption from disk full conditions",
                        implementation_effort="medium",
                        technical_details={"avg_disk_usage_percent": avg_disk_usage, "recommendation": "Clean up logs, implement log rotation, or expand storage"},
                    )
                )

        return recommendations

    async def _save_metrics_snapshot(self) -> None:
        """Save current metrics snapshot to file."""
        try:
            snapshot_data = {
                "timestamp": time.time(),
                "metrics_count": len(self.metrics_buffer),
                "scaling_decisions_count": len(self.scaling_decisions),
                "current_instances": self._current_instances,
                "recent_metrics": [asdict(m) for m in list(self.metrics_buffer)[-10:]],  # Last 10 metrics
                "recent_decisions": [asdict(d) for d in list(self.scaling_decisions)[-5:]],  # Last 5 decisions
                "optimization_recommendations": [asdict(r) for r in self.optimization_recommendations],
            }

            snapshot_file = self.data_path / f"snapshot_{int(time.time())}.json"
            with open(snapshot_file, "w", encoding="utf-8") as f:
                json.dump(snapshot_data, f, indent=2)

            # Keep only the last 24 snapshots
            snapshot_files = sorted(self.data_path.glob("snapshot_*.json"))
            while len(snapshot_files) > 24:
                oldest_file = snapshot_files.pop(0)
                oldest_file.unlink()

        except Exception:
            pass  # Don't let save failures affect the main operation

    async def _publish_telemetry_event(self, event_subtype: str, data: dict[str, Any]) -> None:
        """Publish a telemetry event.

        Args:
            event_subtype: Type of telemetry event
            data: Event data
        """
        await self.event_bus.publish(
            Event(
                type=EventType.CUSTOM,
                data={"event_subtype": f"telemetry_{event_subtype}", **data},
                timestamp=time.time(),
                source="production_telemetry",
                priority=EventPriority.LOW if "error" not in event_subtype else EventPriority.NORMAL,
            )
        )

    def register_scaling_callback(self, callback: Callable[[ScalingDecision], None]) -> None:
        """Register a callback for scaling decisions.

        Args:
            callback: Function to call when scaling decision is made
        """
        self._scaling_callbacks.append(callback)

    def get_current_metrics(self) -> SystemMetrics | None:
        """Get the most recent system metrics.

        Returns:
            Latest SystemMetrics object or None if no metrics available
        """
        return self.metrics_buffer[-1] if self.metrics_buffer else None

    def get_scaling_history(self, limit: int = 10) -> list[ScalingDecision]:
        """Get recent scaling decisions.

        Args:
            limit: Maximum number of decisions to return

        Returns:
            List of recent scaling decisions
        """
        return list(self.scaling_decisions)[-limit:]

    def get_optimization_recommendations(self) -> list[OptimizationRecommendation]:
        """Get current optimization recommendations.

        Returns:
            List of current optimization recommendations
        """
        return self.optimization_recommendations.copy()

    def get_system_summary(self) -> dict[str, Any]:
        """Get comprehensive system summary.

        Returns:
            Dictionary with system status summary
        """
        current_metrics = self.get_current_metrics()
        recent_decisions = self.get_scaling_history(5)

        return {
            "collection_status": "running" if self._is_running else "stopped",
            "metrics_collected": len(self.metrics_buffer),
            "current_instances": self._current_instances,
            "last_scaling_action": self._last_scaling_action,
            "current_metrics": asdict(current_metrics) if current_metrics else None,
            "recent_scaling_decisions": [asdict(d) for d in recent_decisions],
            "optimization_recommendations": len(self.optimization_recommendations),
            "system_health": {
                "cpu_status": "normal" if current_metrics and current_metrics.cpu_percent < 80 else "high",
                "memory_status": "normal" if current_metrics and current_metrics.memory_percent < 80 else "high",
                "response_time_status": "normal" if current_metrics and current_metrics.response_time_ms < 500 else "high",
                "error_rate_status": "normal" if current_metrics and current_metrics.error_rate < 5 else "high",
            }
            if current_metrics
            else None,
        }
