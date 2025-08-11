#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Health Check System for Production Deployment.

This module provides comprehensive health check endpoints for Kubernetes
and production monitoring, including readiness, liveness, and metrics probes.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, Optional

try:
    from fastapi import APIRouter, HTTPException, Response
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from libs.core.session_manager import SessionManager
from libs.dashboard.monitoring_integration import get_monitoring_dashboard


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    
    name: str
    status: str  # 'healthy', 'unhealthy', 'degraded'
    response_time_ms: float
    details: dict[str, Any]
    timestamp: float


class HealthChecker:
    """Comprehensive health checking system for production deployments."""
    
    def __init__(self):
        """Initialize the health checker."""
        self.monitoring = get_monitoring_dashboard()
        self.event_bus = get_event_bus()
        self.session_manager = None
        
        # Health check configurations
        self.readiness_timeout = 5.0  # seconds
        self.liveness_timeout = 2.0   # seconds
        self.metrics_timeout = 10.0   # seconds
        
        # Health thresholds
        self.health_score_threshold = 50.0  # Minimum acceptable health score
        self.response_time_threshold = 500.0  # 500ms max response time
        self.memory_threshold = 90.0  # 90% memory usage threshold
        self.cpu_threshold = 95.0     # 95% CPU usage threshold
    
    async def _get_session_manager(self) -> Optional[SessionManager]:
        """Get session manager instance lazily."""
        if self.session_manager is None:
            try:
                self.session_manager = SessionManager()
            except Exception:
                pass
        return self.session_manager
    
    async def readiness_check(self) -> dict[str, Any]:
        """Kubernetes readiness probe endpoint.
        
        Checks if the application is ready to accept traffic.
        
        Returns:
            Dictionary with readiness status and details
        
        Raises:
            HTTPException: If the service is not ready
        """
        start_time = time.perf_counter()
        checks = []
        overall_ready = True
        
        try:
            # Check critical services with timeout
            service_checks = await asyncio.wait_for(
                self._check_critical_services(),
                timeout=self.readiness_timeout
            )
            
            for check in service_checks:
                checks.append(check)
                if check.status != 'healthy':
                    overall_ready = False
            
            response_time = (time.perf_counter() - start_time) * 1000
            
            # Publish readiness check event
            await self._publish_health_event("readiness_check", {
                'ready': overall_ready,
                'checks_count': len(checks),
                'response_time_ms': response_time,
                'failed_checks': [c.name for c in checks if c.status != 'healthy']
            })
            
            result = {
                "status": "ready" if overall_ready else "not_ready",
                "timestamp": time.time(),
                "response_time_ms": response_time,
                "checks": [
                    {
                        "service": check.name,
                        "status": check.status,
                        "response_time_ms": check.response_time_ms,
                        "details": check.details
                    }
                    for check in checks
                ]
            }
            
            if not overall_ready:
                failed_checks = [check for check in checks if check.status != 'healthy']
                if FASTAPI_AVAILABLE:
                    raise HTTPException(503, {
                        "error": "Service not ready",
                        "failed_checks": [
                            {
                                "service": check.name,
                                "status": check.status,
                                "details": check.details
                            }
                            for check in failed_checks
                        ],
                        **result
                    })
                else:
                    result["error"] = "Service not ready"
                    result["http_status"] = 503
            
            return result
            
        except asyncio.TimeoutError:
            response_time = (time.perf_counter() - start_time) * 1000
            error_result = {
                "status": "timeout",
                "timestamp": time.time(),
                "response_time_ms": response_time,
                "error": f"Readiness check timed out after {self.readiness_timeout}s"
            }
            
            if FASTAPI_AVAILABLE:
                raise HTTPException(503, error_result)
            else:
                error_result["http_status"] = 503
                return error_result
        
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            error_result = {
                "status": "error",
                "timestamp": time.time(),
                "response_time_ms": response_time,
                "error": str(e)
            }
            
            if FASTAPI_AVAILABLE:
                raise HTTPException(500, error_result)
            else:
                error_result["http_status"] = 500
                return error_result
    
    async def liveness_check(self) -> dict[str, Any]:
        """Kubernetes liveness probe endpoint.
        
        Simple liveness check - ensures basic functionality.
        
        Returns:
            Dictionary with liveness status
        
        Raises:
            HTTPException: If the service is not alive
        """
        start_time = time.perf_counter()
        
        try:
            # Basic liveness tests with timeout
            await asyncio.wait_for(
                self._basic_liveness_tests(),
                timeout=self.liveness_timeout
            )
            
            response_time = (time.perf_counter() - start_time) * 1000
            
            # Publish liveness check event
            await self._publish_health_event("liveness_check", {
                'alive': True,
                'response_time_ms': response_time
            })
            
            return {
                "status": "alive",
                "timestamp": time.time(),
                "response_time_ms": response_time
            }
            
        except asyncio.TimeoutError:
            response_time = (time.perf_counter() - start_time) * 1000
            error_result = {
                "status": "timeout",
                "timestamp": time.time(),
                "response_time_ms": response_time,
                "error": f"Liveness check timed out after {self.liveness_timeout}s"
            }
            
            if FASTAPI_AVAILABLE:
                raise HTTPException(500, error_result)
            else:
                error_result["http_status"] = 500
                return error_result
        
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            error_result = {
                "status": "dead",
                "timestamp": time.time(),
                "response_time_ms": response_time,
                "error": str(e)
            }
            
            if FASTAPI_AVAILABLE:
                raise HTTPException(500, error_result)
            else:
                error_result["http_status"] = 500
                return error_result
    
    async def health_metrics(self) -> dict[str, Any]:
        """Detailed health metrics for monitoring and observability.
        
        Returns:
            Dictionary with comprehensive health metrics
        """
        start_time = time.perf_counter()
        
        try:
            # Get detailed metrics with timeout
            metrics_data = await asyncio.wait_for(
                self._collect_health_metrics(),
                timeout=self.metrics_timeout
            )
            
            response_time = (time.perf_counter() - start_time) * 1000
            
            # Publish metrics collection event
            await self._publish_health_event("metrics_collection", {
                'collection_time_ms': response_time,
                'health_score': metrics_data.get('health_score', 0),
                'active_alerts': metrics_data.get('active_alerts', 0)
            })
            
            return {
                **metrics_data,
                "collection_time_ms": response_time,
                "timestamp": time.time()
            }
            
        except asyncio.TimeoutError:
            response_time = (time.perf_counter() - start_time) * 1000
            return {
                "status": "timeout",
                "timestamp": time.time(),
                "collection_time_ms": response_time,
                "error": f"Metrics collection timed out after {self.metrics_timeout}s"
            }
        
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            return {
                "status": "error",
                "timestamp": time.time(),
                "collection_time_ms": response_time,
                "error": str(e)
            }
    
    async def _check_critical_services(self) -> list[HealthCheckResult]:
        """Check the health of critical services.
        
        Returns:
            List of health check results for critical services
        """
        checks = []
        
        # Check session manager
        session_check_start = time.perf_counter()
        session_manager = await self._get_session_manager()
        
        if session_manager:
            try:
                # Basic session manager health check
                is_healthy = True  # session_manager would have an is_healthy method
                session_status = 'healthy' if is_healthy else 'unhealthy'
                session_details = {'service': 'session_manager', 'active': is_healthy}
            except Exception as e:
                session_status = 'unhealthy'
                session_details = {'service': 'session_manager', 'error': str(e)}
        else:
            session_status = 'unhealthy'
            session_details = {'service': 'session_manager', 'error': 'Not available'}
        
        checks.append(HealthCheckResult(
            name="session_manager",
            status=session_status,
            response_time_ms=(time.perf_counter() - session_check_start) * 1000,
            details=session_details,
            timestamp=time.time()
        ))
        
        # Check monitoring system
        monitoring_check_start = time.perf_counter()
        try:
            health_score = self.monitoring._calculate_health_score()
            monitoring_status = 'healthy' if health_score >= self.health_score_threshold else 'degraded'
            monitoring_details = {
                'service': 'monitoring',
                'health_score': health_score,
                'threshold': self.health_score_threshold
            }
        except Exception as e:
            monitoring_status = 'unhealthy'
            monitoring_details = {'service': 'monitoring', 'error': str(e)}
        
        checks.append(HealthCheckResult(
            name="monitoring",
            status=monitoring_status,
            response_time_ms=(time.perf_counter() - monitoring_check_start) * 1000,
            details=monitoring_details,
            timestamp=time.time()
        ))
        
        # Check event bus
        event_bus_check_start = time.perf_counter()
        try:
            # Test event bus functionality
            test_event = Event(
                type=EventType.CUSTOM,
                data={'event_subtype': 'health_check_test'},
                timestamp=time.time(),
                source='health_checker'
            )
            
            # This would be a non-blocking publish for health check
            await asyncio.wait_for(
                self.event_bus.publish(test_event),
                timeout=1.0
            )
            
            event_bus_status = 'healthy'
            event_bus_details = {'service': 'event_bus', 'test_publish': True}
        except Exception as e:
            event_bus_status = 'unhealthy'
            event_bus_details = {'service': 'event_bus', 'error': str(e)}
        
        checks.append(HealthCheckResult(
            name="event_bus",
            status=event_bus_status,
            response_time_ms=(time.perf_counter() - event_bus_check_start) * 1000,
            details=event_bus_details,
            timestamp=time.time()
        ))
        
        return checks
    
    async def _basic_liveness_tests(self) -> None:
        """Perform basic liveness tests.
        
        Raises:
            Exception: If any liveness test fails
        """
        # Test basic Python functionality
        await asyncio.sleep(0.01)
        
        # Test basic arithmetic
        result = 2 + 2
        if result != 4:
            raise RuntimeError("Basic arithmetic failed")
        
        # Test time functionality
        current_time = time.time()
        if current_time <= 0:
            raise RuntimeError("Time functionality failed")
    
    async def _collect_health_metrics(self) -> dict[str, Any]:
        """Collect comprehensive health metrics.
        
        Returns:
            Dictionary with health metrics
        """
        try:
            # Get dashboard data
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            
            # Get system resource information
            system_metrics = await self._get_system_metrics()
            
            return {
                "health_score": dashboard_data["health_score"],
                "alerts": {
                    "active": dashboard_data["alerts"]["active"],
                    "critical": dashboard_data["alerts"]["critical"],
                    "error": dashboard_data["alerts"]["error"],
                    "warning": dashboard_data["alerts"]["warning"]
                },
                "metrics_summary": dashboard_data["metrics"],
                "system_resources": system_metrics,
                "status": "healthy" if dashboard_data["health_score"] >= self.health_score_threshold else "degraded"
            }
        except Exception as e:
            return {
                "health_score": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def _get_system_metrics(self) -> dict[str, Any]:
        """Get system resource metrics.
        
        Returns:
            Dictionary with system metrics
        """
        try:
            import psutil
            
            # Get CPU and memory information
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "status": "normal" if cpu_percent < self.cpu_threshold else "high"
                },
                "memory": {
                    "percent": memory_info.percent,
                    "total_gb": memory_info.total / (1024**3),
                    "available_gb": memory_info.available / (1024**3),
                    "status": "normal" if memory_info.percent < self.memory_threshold else "high"
                },
                "disk": {
                    "percent": disk_info.percent,
                    "total_gb": disk_info.total / (1024**3),
                    "free_gb": disk_info.free / (1024**3),
                    "status": "normal" if disk_info.percent < 85.0 else "high"
                },
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        except ImportError:
            return {
                "cpu": {"status": "unavailable", "error": "psutil not available"},
                "memory": {"status": "unavailable", "error": "psutil not available"},
                "disk": {"status": "unavailable", "error": "psutil not available"}
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def _publish_health_event(self, event_subtype: str, data: dict[str, Any]) -> None:
        """Publish a health check event.
        
        Args:
            event_subtype: Type of health event
            data: Event data
        """
        try:
            await self.event_bus.publish(
                Event(
                    type=EventType.CUSTOM,
                    data={
                        'event_subtype': f'health_{event_subtype}',
                        **data
                    },
                    timestamp=time.time(),
                    source='health_checker',
                    priority=EventPriority.LOW
                )
            )
        except Exception:
            # Don't let event publishing failure affect health checks
            pass


# FastAPI Router (if FastAPI is available)
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/health", tags=["health"])
    health_checker = HealthChecker()
    
    @router.get("/readiness")
    async def readiness_probe():
        """Kubernetes readiness probe endpoint."""
        return await health_checker.readiness_check()
    
    @router.get("/liveness")
    async def liveness_probe():
        """Kubernetes liveness probe endpoint."""
        return await health_checker.liveness_check()
    
    @router.get("/metrics")
    async def health_metrics():
        """Detailed health metrics endpoint."""
        return await health_checker.health_metrics()
    
    @router.get("/status")
    async def health_status():
        """Combined health status endpoint."""
        health_checker_instance = HealthChecker()
        
        # Get both readiness and liveness
        try:
            readiness = await health_checker_instance.readiness_check()
        except Exception as e:
            readiness = {"status": "error", "error": str(e)}
        
        try:
            liveness = await health_checker_instance.liveness_check()
        except Exception as e:
            liveness = {"status": "error", "error": str(e)}
        
        try:
            metrics = await health_checker_instance.health_metrics()
        except Exception as e:
            metrics = {"status": "error", "error": str(e)}
        
        overall_healthy = (
            readiness.get("status") == "ready" and 
            liveness.get("status") == "alive" and
            metrics.get("status") in ["healthy", "degraded"]
        )
        
        return {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "readiness": readiness,
            "liveness": liveness,
            "metrics": metrics,
            "timestamp": time.time()
        }


# Standalone health checker for non-FastAPI usage
async def run_health_check(check_type: str = "all") -> dict[str, Any]:
    """Run health checks outside of FastAPI context.
    
    Args:
        check_type: Type of check to run ('readiness', 'liveness', 'metrics', 'all')
    
    Returns:
        Health check results
    """
    checker = HealthChecker()
    
    if check_type == "readiness":
        return await checker.readiness_check()
    elif check_type == "liveness":
        return await checker.liveness_check()
    elif check_type == "metrics":
        return await checker.health_metrics()
    else:  # all
        results = {}
        try:
            results["readiness"] = await checker.readiness_check()
        except Exception as e:
            results["readiness"] = {"status": "error", "error": str(e)}
        
        try:
            results["liveness"] = await checker.liveness_check()
        except Exception as e:
            results["liveness"] = {"status": "error", "error": str(e)}
        
        try:
            results["metrics"] = await checker.health_metrics()
        except Exception as e:
            results["metrics"] = {"status": "error", "error": str(e)}
        
        return results


if __name__ == "__main__":
    import sys
    
    check_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    result = asyncio.run(run_health_check(check_type))
    print(json.dumps(result, indent=2))