#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Contextual Error Handler.

This module provides intelligent error handling with context-aware user-friendly
messages, automated resolution suggestions, and integration with the monitoring
system for enhanced error analysis.
"""

import inspect
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from libs.dashboard.monitoring_integration import get_monitoring_dashboard


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    SYSTEM = "system"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    DATABASE = "database"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class UserFriendlyError:
    """User-friendly error representation with context and resolution guidance."""
    
    error_code: str
    category: ErrorCategory
    severity: ErrorSeverity
    user_message: str
    technical_details: str
    suggested_actions: List[str]
    documentation_links: List[str]
    context: Dict[str, Any] = field(default_factory=dict)
    auto_fix_available: bool = False
    troubleshooting_guide_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    component: Optional[str] = None
    request_id: Optional[str] = None


class ContextualErrorHandler:
    """Intelligent error handler with context-aware processing."""
    
    def __init__(self):
        """Initialize the contextual error handler."""
        self.monitoring = get_monitoring_dashboard()
        self.error_templates = self._load_error_templates()
        self.error_patterns = self._load_error_patterns()
        self.context_enhancers = self._setup_context_enhancers()
    
    def _load_error_templates(self) -> Dict[str, UserFriendlyError]:
        """Load comprehensive error templates for common issues."""
        return {
            "SYS-001": UserFriendlyError(
                error_code="SYS-001",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                user_message="System performance is slower than usual. We're working to optimize response times.",
                technical_details="Performance metrics indicate response times above normal thresholds",
                suggested_actions=[
                    "Wait a few moments and try your request again",
                    "Close unnecessary browser tabs to free up system resources", 
                    "Check your internet connection stability",
                    "If the issue persists, the system will automatically attempt to optimize performance"
                ],
                documentation_links=[
                    "/docs/generated/performance_guide.md",
                    "/docs/generated/troubleshooting_guide.md#performance-issues"
                ],
                auto_fix_available=True,
                troubleshooting_guide_id="high_response_time"
            ),
            
            "SYS-002": UserFriendlyError(
                error_code="SYS-002",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                user_message="System memory usage is high. Some operations may be slower temporarily.",
                technical_details="Memory usage has exceeded safe operational thresholds",
                suggested_actions=[
                    "Close unused applications to free up memory",
                    "Save your current work as a precaution",
                    "Restart your browser if it becomes unresponsive", 
                    "The system will automatically clear caches and optimize memory usage"
                ],
                documentation_links=[
                    "/docs/generated/troubleshooting_guide.md#memory-issues",
                    "/docs/generated/performance_guide.md#memory-optimization"
                ],
                auto_fix_available=True
            ),
            
            "NET-001": UserFriendlyError(
                error_code="NET-001",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                user_message="Unable to connect to Claude. This might be a temporary network issue.",
                technical_details="Connection timeout or network error when attempting to reach Claude API",
                suggested_actions=[
                    "Check your internet connection",
                    "Wait 30 seconds and try again",
                    "Try refreshing the page",
                    "If the problem continues, Claude's services might be experiencing issues"
                ],
                documentation_links=[
                    "/docs/generated/troubleshooting_guide.md#network-issues",
                    "/docs/generated/api_reference.md#error-codes"
                ],
                auto_fix_available=True,
                troubleshooting_guide_id="connection_issues"
            ),
            
            "NET-002": UserFriendlyError(
                error_code="NET-002", 
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                user_message="Request timed out. The server took longer than expected to respond.",
                technical_details="Request exceeded configured timeout threshold",
                suggested_actions=[
                    "Try your request again - it might work on the second attempt",
                    "If processing a large request, consider breaking it into smaller parts",
                    "Check your internet connection stability"
                ],
                documentation_links=[
                    "/docs/generated/troubleshooting_guide.md#network-issues"
                ],
                auto_fix_available=False
            ),
            
            "AUTH-001": UserFriendlyError(
                error_code="AUTH-001",
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                user_message="Authentication failed. Please verify your credentials and try again.",
                technical_details="Invalid authentication credentials or expired session",
                suggested_actions=[
                    "Double-check your API key if using API access",
                    "Try logging out and logging back in",
                    "Clear your browser cache and cookies",
                    "Contact support if you continue to have authentication issues"
                ],
                documentation_links=[
                    "/docs/generated/api_reference.md#authentication",
                    "/docs/generated/troubleshooting_guide.md#authentication-failures"
                ],
                auto_fix_available=False
            ),
            
            "AUTH-002": UserFriendlyError(
                error_code="AUTH-002",
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.MEDIUM,
                user_message="Your session has expired. Please log in again to continue.",
                technical_details="Authentication token has expired and needs to be refreshed",
                suggested_actions=[
                    "Click 'Log In' to authenticate again",
                    "Your work will be saved automatically",
                    "Consider enabling 'Remember Me' for longer sessions"
                ],
                documentation_links=[
                    "/docs/generated/api_reference.md#authentication"
                ],
                auto_fix_available=False
            ),
            
            "CFG-001": UserFriendlyError(
                error_code="CFG-001",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.MEDIUM,
                user_message="There's an issue with the current configuration. Using default settings instead.",
                technical_details="Configuration validation failed, falling back to safe defaults",
                suggested_actions=[
                    "Your session will continue with default settings",
                    "Check your configuration file for syntax errors",
                    "Review the configuration documentation for proper format",
                    "Contact support if you need help with configuration"
                ],
                documentation_links=[
                    "/docs/configuration.md",
                    "/docs/generated/troubleshooting_guide.md#configuration-issues"
                ],
                auto_fix_available=True
            ),
            
            "DB-001": UserFriendlyError(
                error_code="DB-001",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                user_message="Unable to save your data right now. Your changes are temporarily stored in memory.",
                technical_details="Database connection failed or query timeout exceeded",
                suggested_actions=[
                    "Don't close your browser - your changes are temporarily saved",
                    "Try saving again in a few moments",
                    "If the problem continues, export your work as a backup",
                    "The system will automatically attempt to reconnect to the database"
                ],
                documentation_links=[
                    "/docs/generated/troubleshooting_guide.md#database-problems"
                ],
                auto_fix_available=True
            ),
            
            "VAL-001": UserFriendlyError(
                error_code="VAL-001",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                user_message="The information you entered doesn't match the expected format.",
                technical_details="Input validation failed for one or more fields",
                suggested_actions=[
                    "Check the highlighted fields for errors",
                    "Make sure required fields are filled in",
                    "Verify that dates, emails, and numbers are in the correct format",
                    "Refer to the help text for format examples"
                ],
                documentation_links=[
                    "/docs/user-guide.md#data-formats"
                ],
                auto_fix_available=False
            ),
            
            "PERF-001": UserFriendlyError(
                error_code="PERF-001",
                category=ErrorCategory.PERFORMANCE,
                severity=ErrorSeverity.MEDIUM,
                user_message="The system is experiencing high load. Your request may take longer than usual.",
                technical_details="Performance metrics indicate system resource constraints",
                suggested_actions=[
                    "Please wait while your request is processed",
                    "Avoid submitting multiple requests at the same time",
                    "Consider simplifying complex requests",
                    "The system will automatically optimize performance"
                ],
                documentation_links=[
                    "/docs/generated/performance_guide.md",
                    "/docs/generated/troubleshooting_guide.md#performance-issues"
                ],
                auto_fix_available=True,
                troubleshooting_guide_id="high_response_time"
            )
        }
    
    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load error patterns for automatic classification."""
        return {
            # Connection and network patterns
            "connection": {
                "keywords": ["connection", "timeout", "network", "unreachable", "refused"],
                "exception_types": ["ConnectionError", "TimeoutError", "ConnectTimeout"],
                "error_code": "NET-001"
            },
            "timeout": {
                "keywords": ["timeout", "timed out", "deadline exceeded"],
                "exception_types": ["TimeoutError", "asyncio.TimeoutError"],
                "error_code": "NET-002"
            },
            
            # Authentication patterns
            "authentication": {
                "keywords": ["unauthorized", "authentication", "invalid credentials", "access denied"],
                "exception_types": ["AuthenticationError", "PermissionError"],
                "error_code": "AUTH-001"
            },
            "session_expired": {
                "keywords": ["session expired", "token expired", "login required"],
                "exception_types": ["SessionExpiredError"],
                "error_code": "AUTH-002"
            },
            
            # System resource patterns
            "memory": {
                "keywords": ["memory", "out of memory", "allocation failed"],
                "exception_types": ["MemoryError", "OutOfMemoryError"],
                "error_code": "SYS-002"
            },
            "performance": {
                "keywords": ["slow", "performance", "high load", "resource"],
                "exception_types": ["PerformanceError"],
                "error_code": "PERF-001"
            },
            
            # Database patterns
            "database": {
                "keywords": ["database", "sql", "query", "connection pool", "transaction"],
                "exception_types": ["DatabaseError", "OperationalError", "IntegrityError"],
                "error_code": "DB-001"
            },
            
            # Configuration patterns
            "configuration": {
                "keywords": ["configuration", "config", "settings", "invalid format"],
                "exception_types": ["ConfigurationError", "ValueError"],
                "error_code": "CFG-001"
            },
            
            # Validation patterns
            "validation": {
                "keywords": ["validation", "invalid", "format", "required field"],
                "exception_types": ["ValidationError", "ValueError"],
                "error_code": "VAL-001"
            }
        }
    
    def _setup_context_enhancers(self) -> Dict[str, callable]:
        """Setup context enhancement functions."""
        return {
            "system_health": self._enhance_with_system_health,
            "performance_metrics": self._enhance_with_performance_metrics,
            "recent_errors": self._enhance_with_error_history,
            "component_status": self._enhance_with_component_status
        }
    
    async def handle_error(self, 
                          exception: Exception, 
                          context: Dict[str, Any] = None,
                          request_id: str = None) -> UserFriendlyError:
        """Convert technical exception into user-friendly error with context.
        
        Args:
            exception: The exception that occurred
            context: Optional context information
            request_id: Optional request identifier
            
        Returns:
            UserFriendlyError with enhanced context and suggestions
        """
        try:
            # Classify the error
            error_code = await self._classify_error(exception)
            
            # Get base error template
            base_error = self.error_templates.get(error_code, self._create_generic_error(exception))
            
            # Enhance with current system context
            enhanced_error = await self._enhance_error_with_context(base_error, context, exception)
            
            # Add request tracking
            if request_id:
                enhanced_error.request_id = request_id
            
            # Determine component from stack trace
            enhanced_error.component = self._extract_component_from_exception(exception)
            
            # Add auto-fix suggestions if available
            if enhanced_error.auto_fix_available:
                enhanced_error = await self._add_auto_fix_suggestions(enhanced_error, exception, context)
            
            # Log the error for monitoring
            await self._log_error_for_monitoring(enhanced_error, exception)
            
            return enhanced_error
            
        except Exception as handler_error:
            # Fallback error if handler itself fails
            return UserFriendlyError(
                error_code="ERR-HANDLER",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                user_message="An unexpected error occurred. Please try again or contact support.",
                technical_details=f"Error handler failed: {str(handler_error)}",
                suggested_actions=[
                    "Try refreshing the page",
                    "Contact support with the error details",
                    "Include the time when this error occurred"
                ],
                documentation_links=[],
                timestamp=time.time()
            )
    
    async def _classify_error(self, exception: Exception) -> str:
        """Classify error based on exception type and message.
        
        Args:
            exception: The exception to classify
            
        Returns:
            Error code string
        """
        exception_name = exception.__class__.__name__
        exception_message = str(exception).lower()
        
        # Check patterns for automatic classification
        for pattern_name, pattern_info in self.error_patterns.items():
            # Check exception type match
            if exception_name in pattern_info["exception_types"]:
                return pattern_info["error_code"]
            
            # Check keyword match in message
            if any(keyword in exception_message for keyword in pattern_info["keywords"]):
                return pattern_info["error_code"]
        
        # Check for specific known error types
        if isinstance(exception, (ConnectionError, TimeoutError)):
            return "NET-001"
        elif isinstance(exception, PermissionError):
            return "AUTH-001"
        elif isinstance(exception, MemoryError):
            return "SYS-002"
        elif isinstance(exception, ValueError):
            if "validation" in exception_message or "invalid" in exception_message:
                return "VAL-001"
            else:
                return "CFG-001"
        
        # Default to generic system error
        return "SYS-001"
    
    def _create_generic_error(self, exception: Exception) -> UserFriendlyError:
        """Create a generic error template for unknown exceptions.
        
        Args:
            exception: The exception to create a template for
            
        Returns:
            Generic UserFriendlyError
        """
        return UserFriendlyError(
            error_code="GEN-001",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            user_message="Something unexpected happened. We're working to resolve this issue.",
            technical_details=f"{exception.__class__.__name__}: {str(exception)}",
            suggested_actions=[
                "Try your request again",
                "If the problem persists, please contact support",
                "Include the error details and time when reporting"
            ],
            documentation_links=[
                "/docs/generated/troubleshooting_guide.md",
                "/docs/generated/error_reference.md"
            ],
            auto_fix_available=False
        )
    
    async def _enhance_error_with_context(self, 
                                        error: UserFriendlyError, 
                                        context: Dict[str, Any] = None,
                                        exception: Exception = None) -> UserFriendlyError:
        """Enhance error with current system context.
        
        Args:
            error: Base error to enhance
            context: Optional additional context
            exception: Original exception for analysis
            
        Returns:
            Enhanced UserFriendlyError
        """
        enhanced_context = error.context.copy()
        enhanced_actions = error.suggested_actions.copy()
        
        # Get system context
        system_context = await self._get_system_context()
        enhanced_context.update(system_context)
        
        # Add provided context
        if context:
            enhanced_context.update(context)
        
        # Enhance based on system health
        if system_context.get('health_score', 100) < 70:
            enhanced_actions.insert(0, "⚠️ System health is degraded - this may be affecting performance")
        
        # Enhance based on active alerts
        active_alerts = system_context.get('active_alerts', 0)
        if active_alerts > 0:
            enhanced_actions.insert(0, f"ℹ️ System has {active_alerts} active alerts that may be related")
        
        # Add memory-specific guidance
        if system_context.get('high_memory_usage', False):
            enhanced_actions.insert(0, "💾 System memory usage is high - consider closing unused applications")
        
        # Add recent errors context
        if system_context.get('recent_errors', False):
            enhanced_actions.append("📊 Multiple recent errors detected - system may need attention")
        
        # Enhance technical details with context
        enhanced_technical_details = error.technical_details
        if exception:
            # Add stack trace summary (last few calls)
            tb_lines = traceback.format_tb(exception.__traceback__)
            if tb_lines:
                last_calls = tb_lines[-2:] if len(tb_lines) > 2 else tb_lines
                enhanced_technical_details += f" | Stack: {''.join(last_calls).strip()}"
        
        # Add system context summary
        context_summary = f"Health: {system_context.get('health_score', 100)}%, " \
                         f"Alerts: {active_alerts}, " \
                         f"Time: {time.strftime('%H:%M:%S')}"
        enhanced_technical_details += f" | Context: {context_summary}"
        
        # Create enhanced error
        return UserFriendlyError(
            error_code=error.error_code,
            category=error.category,
            severity=error.severity,
            user_message=error.user_message,
            technical_details=enhanced_technical_details,
            suggested_actions=enhanced_actions,
            documentation_links=error.documentation_links,
            context=enhanced_context,
            auto_fix_available=error.auto_fix_available,
            troubleshooting_guide_id=error.troubleshooting_guide_id,
            timestamp=error.timestamp,
            component=error.component,
            request_id=error.request_id
        )
    
    async def _get_system_context(self) -> Dict[str, Any]:
        """Get comprehensive system context for error enhancement.
        
        Returns:
            Dictionary with current system context
        """
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            
            context = {
                'timestamp': time.time(),
                'health_score': dashboard_data.get('health_score', 100),
                'active_alerts': len(dashboard_data.get('alerts', {}).get('recent', [])),
                'metrics_available': bool(dashboard_data.get('metrics')),
            }
            
            # Add specific context flags
            health_score = context['health_score']
            if health_score < 70:
                context['system_degraded'] = True
            
            if context['active_alerts'] > 3:
                context['recent_errors'] = True
            
            # Add memory context from metrics
            metrics = dashboard_data.get('metrics', {})
            if metrics:
                total_memory = sum(
                    comp.get('memory_usage', {}).get('current', 0) 
                    for comp in metrics.values()
                )
                
                if total_memory > 50:  # > 50MB total
                    context['high_memory_usage'] = True
                
                # Add response time context
                avg_response_time = sum(
                    comp.get('response_time', {}).get('average', 0)
                    for comp in metrics.values()
                ) / len(metrics) if metrics else 0
                
                context['avg_response_time'] = avg_response_time
                if avg_response_time > 100:
                    context['high_response_time'] = True
            
            return context
            
        except Exception:
            # Fallback context if monitoring is unavailable
            return {
                'timestamp': time.time(),
                'health_score': 100,
                'active_alerts': 0,
                'monitoring_unavailable': True
            }
    
    def _extract_component_from_exception(self, exception: Exception) -> Optional[str]:
        """Extract component name from exception stack trace.
        
        Args:
            exception: Exception to analyze
            
        Returns:
            Component name if identifiable, None otherwise
        """
        try:
            # Get the stack trace
            tb = exception.__traceback__
            if not tb:
                return None
            
            # Look through stack frames for component indicators
            while tb:
                frame = tb.tb_frame
                filename = frame.f_code.co_filename
                
                # Extract component from file path patterns
                if '/libs/' in filename:
                    # Extract from libs/<component>/<file>.py
                    parts = filename.split('/libs/')[-1].split('/')
                    if len(parts) > 1 and parts[0]:
                        return parts[0]
                elif '/api/' in filename:
                    return 'api'
                elif '/tauri-dashboard/' in filename:
                    return 'dashboard'
                elif '/scripts/' in filename:
                    return 'scripts'
                
                tb = tb.tb_next
            
            return None
            
        except Exception:
            return None
    
    async def _add_auto_fix_suggestions(self, 
                                      error: UserFriendlyError, 
                                      exception: Exception,
                                      context: Dict[str, Any] = None) -> UserFriendlyError:
        """Add automated fix suggestions to the error.
        
        Args:
            error: Error to enhance with auto-fix suggestions
            exception: Original exception
            context: Additional context
            
        Returns:
            Enhanced error with auto-fix suggestions
        """
        enhanced_actions = error.suggested_actions.copy()
        
        # Add auto-fix suggestions based on error type
        if error.error_code in ["SYS-001", "PERF-001"]:
            enhanced_actions.extend([
                "🔧 Automated performance optimization is available",
                "System can automatically clear caches and optimize resource usage",
                "Click 'Auto-Fix' in the troubleshooting panel to apply optimizations"
            ])
        elif error.error_code == "SYS-002":
            enhanced_actions.extend([
                "🔧 Automated memory cleanup is available", 
                "System can clear caches and free up memory automatically",
                "Restart of memory-intensive components can be automated"
            ])
        elif error.error_code == "NET-001":
            enhanced_actions.extend([
                "🔧 Network connectivity tests can be run automatically",
                "System can check firewall rules and restart network services",
                "Automated retry with exponential backoff is available"
            ])
        elif error.error_code == "DB-001":
            enhanced_actions.extend([
                "🔧 Database connection recovery is automated",
                "System will automatically retry failed operations", 
                "Connection pool optimization can be applied automatically"
            ])
        elif error.error_code == "CFG-001":
            enhanced_actions.extend([
                "🔧 Configuration validation and repair is available",
                "System can automatically restore valid configuration",
                "Backup configurations can be applied automatically"
            ])
        
        # Create enhanced error
        return UserFriendlyError(
            error_code=error.error_code,
            category=error.category,
            severity=error.severity,
            user_message=error.user_message,
            technical_details=error.technical_details,
            suggested_actions=enhanced_actions,
            documentation_links=error.documentation_links,
            context=error.context,
            auto_fix_available=error.auto_fix_available,
            troubleshooting_guide_id=error.troubleshooting_guide_id,
            timestamp=error.timestamp,
            component=error.component,
            request_id=error.request_id
        )
    
    async def _log_error_for_monitoring(self, 
                                      error: UserFriendlyError, 
                                      exception: Exception) -> None:
        """Log error information for monitoring and analysis.
        
        Args:
            error: User-friendly error to log
            exception: Original exception
        """
        try:
            from libs.core.async_event_bus import Event, EventType, EventPriority
            
            # Create monitoring event
            event = Event(
                type=EventType.CUSTOM,
                data={
                    'event_subtype': 'user_friendly_error',
                    'error_code': error.error_code,
                    'category': error.category.value,
                    'severity': error.severity.value,
                    'component': error.component,
                    'user_message': error.user_message,
                    'technical_details': error.technical_details,
                    'auto_fix_available': error.auto_fix_available,
                    'troubleshooting_guide_id': error.troubleshooting_guide_id,
                    'exception_type': exception.__class__.__name__,
                    'exception_message': str(exception),
                    'context': error.context
                },
                timestamp=error.timestamp,
                source='contextual_error_handler',
                priority=EventPriority.HIGH if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else EventPriority.NORMAL
            )
            
            # Publish to event bus
            await self.monitoring.event_bus.publish(event)
            
        except Exception:
            # Don't let logging failures break error handling
            pass
    
    # Context enhancer methods
    async def _enhance_with_system_health(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance context with system health information."""
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            context['system_health'] = {
                'score': dashboard_data.get('health_score', 100),
                'status': 'healthy' if dashboard_data.get('health_score', 100) > 80 else 'degraded'
            }
        except Exception:
            context['system_health'] = {'score': 100, 'status': 'unknown'}
        return context
    
    async def _enhance_with_performance_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance context with performance metrics."""
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            metrics = dashboard_data.get('metrics', {})
            
            if metrics:
                # Calculate aggregate performance metrics
                total_components = len(metrics)
                avg_response_time = sum(
                    comp.get('response_time', {}).get('average', 0)
                    for comp in metrics.values()
                ) / total_components if total_components > 0 else 0
                
                total_memory = sum(
                    comp.get('memory_usage', {}).get('current', 0)
                    for comp in metrics.values()
                )
                
                context['performance'] = {
                    'avg_response_time': avg_response_time,
                    'total_memory_mb': total_memory,
                    'components_monitored': total_components
                }
        except Exception:
            context['performance'] = {'status': 'unavailable'}
        return context
    
    async def _enhance_with_error_history(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance context with recent error history."""
        try:
            active_alerts = self.monitoring.get_active_alerts()
            recent_alerts = [alert for alert in active_alerts if time.time() - alert.timestamp < 3600]
            
            context['error_history'] = {
                'recent_errors_count': len(recent_alerts),
                'error_types': list(set(alert.metric_type.value for alert in recent_alerts)),
                'most_recent': recent_alerts[0].timestamp if recent_alerts else None
            }
        except Exception:
            context['error_history'] = {'status': 'unavailable'}
        return context
    
    async def _enhance_with_component_status(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance context with component status information."""
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            metrics = dashboard_data.get('metrics', {})
            
            component_status = {}
            for component, comp_metrics in metrics.items():
                # Determine component health
                rt = comp_metrics.get('response_time', {}).get('average', 0)
                mem = comp_metrics.get('memory_usage', {}).get('current', 0)
                
                status = 'healthy'
                if rt > 200 or mem > 15:
                    status = 'unhealthy'
                elif rt > 100 or mem > 10:
                    status = 'degraded'
                
                component_status[component] = {
                    'status': status,
                    'response_time': rt,
                    'memory_usage': mem
                }
            
            context['component_status'] = component_status
        except Exception:
            context['component_status'] = {'status': 'unavailable'}
        return context
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics.
        
        Returns:
            Dictionary with error statistics
        """
        try:
            active_alerts = self.monitoring.get_active_alerts()
            
            # Categorize alerts by severity
            severity_counts = {}
            for alert in active_alerts:
                severity = alert.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            return {
                'total_active_alerts': len(active_alerts),
                'severity_breakdown': severity_counts,
                'error_templates_loaded': len(self.error_templates),
                'error_patterns_loaded': len(self.error_patterns),
                'last_updated': time.time()
            }
        except Exception:
            return {
                'error': 'Statistics unavailable',
                'last_updated': time.time()
            }
    
    async def test_error_handling(self, error_type: str = "generic") -> UserFriendlyError:
        """Test error handling with a sample error.
        
        Args:
            error_type: Type of error to simulate
            
        Returns:
            UserFriendlyError result
        """
        test_exceptions = {
            "network": ConnectionError("Failed to connect to test service"),
            "memory": MemoryError("Unable to allocate memory"),
            "auth": PermissionError("Access denied"),
            "validation": ValueError("Invalid input format"),
            "generic": Exception("Test exception")
        }
        
        exception = test_exceptions.get(error_type, Exception("Test exception"))
        
        return await self.handle_error(
            exception,
            context={'test': True, 'error_type': error_type},
            request_id=f"test-{int(time.time())}"
        )