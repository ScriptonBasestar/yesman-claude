#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Intelligent Troubleshooting Engine.

This module provides context-aware troubleshooting capabilities with automated fixes
for common system issues. It integrates with the monitoring dashboard to provide
intelligent issue diagnosis and resolution guidance.
"""

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from libs.dashboard.monitoring_integration import get_monitoring_dashboard


@dataclass
class TroubleshootingStep:
    """Individual troubleshooting step with execution details."""
    
    title: str
    description: str
    action_type: str  # 'check', 'fix', 'restart', 'configure'
    command: Optional[str] = None
    expected_output: Optional[str] = None
    success_criteria: Optional[str] = None
    automated: bool = False
    safety_level: str = 'safe'  # 'safe', 'moderate', 'high_risk'


@dataclass
class TroubleshootingGuide:
    """Complete troubleshooting guide for a specific issue."""
    
    problem_id: str
    title: str
    description: str
    symptoms: List[str]
    severity: str  # 'low', 'medium', 'high', 'critical'
    steps: List[TroubleshootingStep]
    related_metrics: List[str]
    documentation_links: List[str]
    tags: List[str] = None


class IntelligentTroubleshootingEngine:
    """Intelligent troubleshooting engine with context-aware diagnosis."""
    
    def __init__(self):
        """Initialize the troubleshooting engine."""
        self.monitoring = get_monitoring_dashboard()
        self.troubleshooting_guides = self._load_troubleshooting_database()
        self.user_session_context = {}
        self.execution_history = []
        self.project_root = Path(__file__).parent.parent.parent
    
    def _load_troubleshooting_database(self) -> List[TroubleshootingGuide]:
        """Load comprehensive troubleshooting guides with dynamic content."""
        return [
            TroubleshootingGuide(
                problem_id="high_response_time",
                title="High Response Time Detected",
                description="System response times are above normal thresholds, affecting user experience",
                symptoms=[
                    "Average response time > 100ms",
                    "User reports of slow performance",
                    "Dashboard shows performance alerts",
                    "High CPU or memory usage detected"
                ],
                severity="medium",
                steps=[
                    TroubleshootingStep(
                        title="Check Current System Load",
                        description="Verify CPU and memory usage to identify resource bottlenecks",
                        action_type="check",
                        command="make system-status",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Review Performance Metrics",
                        description="Analyze component-specific metrics for detailed performance insights",
                        action_type="check",
                        command="make performance-report",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Check for Resource Bottlenecks",
                        description="Identify components with high resource usage patterns",
                        action_type="check",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Clear System Caches",
                        description="Clear system caches to free up memory and improve performance",
                        action_type="fix",
                        command="make clean-cache",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Restart Performance-Heavy Components",
                        description="Restart components showing degraded performance (requires manual approval)",
                        action_type="restart",
                        command="make restart-component COMPONENT={component}",
                        automated=False,
                        safety_level="moderate"
                    )
                ],
                related_metrics=["response_time", "cpu_usage", "memory_usage"],
                documentation_links=[
                    "/docs/developer-guide/performance-monitoring.md",
                    "/docs/developer-guide/troubleshooting/troubleshooting-guide.md"
                ],
                tags=["performance", "response_time", "system_load"]
            ),
            TroubleshootingGuide(
                problem_id="security_violations",
                title="Security Violations Detected",
                description="Security validation has detected potential issues that require immediate attention",
                symptoms=[
                    "Security scan failures",
                    "Unusual authentication patterns",
                    "Suspicious file access attempts",
                    "Failed security validation checks"
                ],
                severity="high",
                steps=[
                    TroubleshootingStep(
                        title="Run Security Validation",
                        description="Execute comprehensive security scan to identify all issues",
                        action_type="check",
                        command="make security-check",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Review Security Logs",
                        description="Check authentication and access logs for suspicious activity",
                        action_type="check",
                        command="make security-logs",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Check File Permissions",
                        description="Verify file permissions and access controls are correctly configured",
                        action_type="check",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Update Security Baselines",
                        description="Update security baselines after resolving identified issues",
                        action_type="configure",
                        command="make security-baseline-update",
                        automated=False,
                        safety_level="moderate"
                    ),
                    TroubleshootingStep(
                        title="Isolate Affected Components",
                        description="Temporarily isolate components with security issues (requires approval)",
                        action_type="fix",
                        automated=False,
                        safety_level="high_risk"
                    )
                ],
                related_metrics=["security_violations", "failed_auth_attempts"],
                documentation_links=[
                    "/docs/development/security-coding-standards.md",
                    "/docs/development/security-audit-schedule.md"
                ],
                tags=["security", "authentication", "access_control"]
            ),
            TroubleshootingGuide(
                problem_id="connection_issues",
                title="Connection and Network Issues",
                description="Network connectivity problems affecting system communication",
                symptoms=[
                    "Connection timeouts",
                    "Network errors in logs",
                    "API calls failing",
                    "Dashboard not loading properly"
                ],
                severity="medium",
                steps=[
                    TroubleshootingStep(
                        title="Check Network Connectivity",
                        description="Verify basic network connectivity and DNS resolution",
                        action_type="check",
                        command="ping -c 4 8.8.8.8 && nslookup anthropic.com",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Test API Endpoints",
                        description="Test connectivity to critical API endpoints",
                        action_type="check",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Check Firewall Rules",
                        description="Verify firewall rules are not blocking necessary connections",
                        action_type="check",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Restart Network Services",
                        description="Restart network-related services if connectivity issues persist",
                        action_type="restart",
                        command="make restart-network-services",
                        automated=False,
                        safety_level="moderate"
                    )
                ],
                related_metrics=["network_io", "error_rate"],
                documentation_links=[
                    "/docs/developer-guide/troubleshooting/troubleshooting-guide.md"
                ],
                tags=["network", "connectivity", "api"]
            ),
            TroubleshootingGuide(
                problem_id="disk_space_low",
                title="Low Disk Space Warning",
                description="Available disk space is running low, which may affect system operation",
                symptoms=[
                    "Disk space warnings in logs",
                    "Failed file write operations",
                    "Temporary files not being created",
                    "System becoming unresponsive"
                ],
                severity="high",
                steps=[
                    TroubleshootingStep(
                        title="Check Disk Usage",
                        description="Analyze current disk usage and identify large files/directories",
                        action_type="check",
                        command="df -h && du -sh /* 2>/dev/null | sort -hr | head -10",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Clean Temporary Files",
                        description="Remove temporary files and clear system caches",
                        action_type="fix",
                        command="make clean-temp",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Clear Log Files",
                        description="Archive and compress old log files to free space",
                        action_type="fix",
                        command="make clean-logs",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Remove Old Build Artifacts",
                        description="Clean up old build artifacts and dependencies",
                        action_type="fix",
                        command="make clean-build",
                        automated=True,
                        safety_level="safe"
                    )
                ],
                related_metrics=["disk_usage"],
                documentation_links=[
                    "/docs/developer-guide/troubleshooting/troubleshooting-guide.md"
                ],
                tags=["disk_space", "cleanup", "storage"]
            ),
            TroubleshootingGuide(
                problem_id="test_failures",
                title="Test Suite Failures",
                description="Automated tests are failing, indicating potential code issues",
                symptoms=[
                    "Multiple test failures",
                    "CI/CD pipeline failures",
                    "Quality gate failures",
                    "Integration test errors"
                ],
                severity="medium",
                steps=[
                    TroubleshootingStep(
                        title="Run Specific Test Suite",
                        description="Run the failing test suite to get detailed error information",
                        action_type="check",
                        command="make test-verbose",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Check Test Dependencies",
                        description="Verify all test dependencies are properly installed",
                        action_type="check",
                        command="uv sync --dev",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Reset Test Environment",
                        description="Clean and reset test environment to known state",
                        action_type="fix",
                        command="make test-reset",
                        automated=True,
                        safety_level="safe"
                    ),
                    TroubleshootingStep(
                        title="Run Quality Gates",
                        description="Execute quality gates to identify specific issues",
                        action_type="check",
                        command="make quality-check",
                        automated=True,
                        safety_level="safe"
                    )
                ],
                related_metrics=["test_success_rate", "error_rate"],
                documentation_links=[
                    "/docs/developer-guide/testing/test-suite-guide.md",
                    "/docs/developer-guide/testing/integration-test-guide.md"
                ],
                tags=["testing", "ci_cd", "quality_gates"]
            )
        ]
    
    async def diagnose_current_issues(self, user_context: Dict = None) -> List[Dict[str, Any]]:
        """Diagnose current system issues and provide troubleshooting guidance.
        
        Args:
            user_context: Optional user context for enhanced diagnosis
            
        Returns:
            List of identified problems with troubleshooting guidance
        """
        try:
            # Get current system metrics
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            active_alerts = self.monitoring.get_active_alerts()
            
            # Analyze issues
            identified_problems = []
            
            # Check active alerts for matching guides
            for alert in active_alerts:
                matching_guides = self._find_matching_guides(alert)
                for guide in matching_guides:
                    problem_context = await self._analyze_problem_context(guide, dashboard_data, alert)
                    identified_problems.append({
                        'guide': guide,
                        'context': problem_context,
                        'alert': {
                            'severity': alert.severity.value,
                            'message': alert.message,
                            'timestamp': alert.timestamp,
                            'component': alert.component
                        },
                        'automated_steps_available': sum(1 for step in guide.steps if step.automated),
                        'estimated_resolution_time': self._estimate_resolution_time(guide),
                        'priority_score': self._calculate_priority_score(guide, alert),
                        'safety_assessment': self._assess_safety_level(guide)
                    })
            
            # Check for issues without alerts but visible in metrics
            await self._check_metric_based_issues(dashboard_data, identified_problems)
            
            # Sort by priority score (highest first)
            identified_problems.sort(key=lambda x: x['priority_score'], reverse=True)
            
            return identified_problems
            
        except Exception as e:
            return [{
                'error': f"Failed to diagnose issues: {str(e)}",
                'guide': None,
                'context': {},
                'automated_steps_available': 0,
                'estimated_resolution_time': 0,
                'priority_score': 0
            }]
    
    async def _check_metric_based_issues(self, dashboard_data: Dict, existing_problems: List) -> None:
        """Check for issues based on metrics that may not have triggered alerts yet."""
        metrics = dashboard_data.get('metrics', {})
        
        # Check for high response times
        if not any(p['guide'] and p['guide'].problem_id == 'high_response_time' for p in existing_problems):
            high_rt_components = []
            for component, comp_metrics in metrics.items():
                rt_data = comp_metrics.get('response_time', {})
                if rt_data.get('average', 0) > 80:  # Pre-alert threshold
                    high_rt_components.append(component)
            
            if high_rt_components:
                guide = next((g for g in self.troubleshooting_guides if g.problem_id == 'high_response_time'), None)
                if guide:
                    existing_problems.append({
                        'guide': guide,
                        'context': {'affected_components': high_rt_components, 'severity_assessment': 'preventive'},
                        'automated_steps_available': sum(1 for step in guide.steps if step.automated),
                        'estimated_resolution_time': self._estimate_resolution_time(guide),
                        'priority_score': 60,  # Medium priority for preventive
                        'alert': None
                    })
    
    def _find_matching_guides(self, alert) -> List[TroubleshootingGuide]:
        """Find troubleshooting guides that match the given alert."""
        matching_guides = []
        
        for guide in self.troubleshooting_guides:
            # Check if alert metric type is in guide's related metrics
            if alert.metric_type.value in guide.related_metrics:
                matching_guides.append(guide)
                continue
            
            # Check for component-specific matches
            if alert.component in guide.title.lower() or any(alert.component in metric for metric in guide.related_metrics):
                matching_guides.append(guide)
                continue
            
            # Check for keyword matches in alert message
            alert_keywords = alert.message.lower().split()
            guide_keywords = [tag.lower() for tag in (guide.tags or [])]
            if any(keyword in guide_keywords for keyword in alert_keywords):
                matching_guides.append(guide)
        
        return matching_guides
    
    async def _analyze_problem_context(self, guide: TroubleshootingGuide, dashboard_data: Dict, alert=None) -> Dict[str, Any]:
        """Analyze specific context for a troubleshooting guide."""
        context = {
            'current_metrics': {},
            'affected_components': [],
            'severity_assessment': guide.severity,
            'trend_analysis': {},
            'system_health': dashboard_data.get('health_score', 100)
        }
        
        # Extract relevant metrics
        metrics = dashboard_data.get('metrics', {})
        for metric_name in guide.related_metrics:
            if metric_name in ['response_time', 'memory_usage', 'cpu_usage', 'error_rate']:
                for component, comp_metrics in metrics.items():
                    if metric_name in comp_metrics:
                        if metric_name not in context['current_metrics']:
                            context['current_metrics'][metric_name] = {}
                        context['current_metrics'][metric_name][component] = comp_metrics[metric_name]
        
        # Identify affected components
        for component, comp_metrics in metrics.items():
            for related_metric in guide.related_metrics:
                if related_metric in comp_metrics:
                    metric_data = comp_metrics[related_metric]
                    if self._is_metric_concerning(related_metric, metric_data):
                        context['affected_components'].append({
                            'component': component,
                            'metric': related_metric,
                            'current_value': metric_data.get('current', 0),
                            'average_value': metric_data.get('average', 0),
                            'max_value': metric_data.get('max', 0)
                        })
        
        # Add alert-specific context
        if alert:
            context['alert_details'] = {
                'current_value': alert.current_value,
                'threshold': alert.threshold,
                'severity': alert.severity.value,
                'context': alert.context
            }
        
        return context
    
    def _is_metric_concerning(self, metric_name: str, metric_data: Dict) -> bool:
        """Determine if a metric value is concerning."""
        thresholds = {
            'response_time': {'current': 100, 'average': 80},
            'memory_usage': {'current': 10, 'average': 8},
            'cpu_usage': {'current': 80, 'average': 60},
            'error_rate': {'current': 0.05, 'average': 0.03}
        }
        
        if metric_name not in thresholds:
            return False
        
        metric_threshold = thresholds[metric_name]
        current_value = metric_data.get('current', 0)
        average_value = metric_data.get('average', 0)
        
        return (current_value > metric_threshold['current'] or 
                average_value > metric_threshold['average'])
    
    def _estimate_resolution_time(self, guide: TroubleshootingGuide) -> int:
        """Estimate resolution time in minutes."""
        base_time = {
            'low': 5,
            'medium': 15,
            'high': 30,
            'critical': 60
        }.get(guide.severity, 15)
        
        # Add time for manual steps
        manual_steps = sum(1 for step in guide.steps if not step.automated)
        automated_steps = sum(1 for step in guide.steps if step.automated)
        
        return base_time + (manual_steps * 5) + (automated_steps * 1)
    
    def _calculate_priority_score(self, guide: TroubleshootingGuide, alert=None) -> int:
        """Calculate priority score for the issue (0-100)."""
        # Base score from severity
        severity_scores = {
            'low': 20,
            'medium': 50,
            'high': 80,
            'critical': 100
        }
        
        score = severity_scores.get(guide.severity, 50)
        
        # Adjust based on alert severity if present
        if alert:
            alert_scores = {
                'info': 0,
                'warning': 10,
                'error': 20,
                'critical': 30
            }
            score += alert_scores.get(alert.severity.value, 0)
        
        # Boost score if many automated steps are available
        automated_steps = sum(1 for step in guide.steps if step.automated)
        if automated_steps >= 3:
            score += 10
        
        return min(100, score)
    
    def _assess_safety_level(self, guide: TroubleshootingGuide) -> Dict[str, Any]:
        """Assess the overall safety level of the troubleshooting guide."""
        safety_levels = [step.safety_level for step in guide.steps]
        
        high_risk_count = safety_levels.count('high_risk')
        moderate_risk_count = safety_levels.count('moderate')
        safe_count = safety_levels.count('safe')
        
        overall_safety = 'safe'
        if high_risk_count > 0:
            overall_safety = 'high_risk'
        elif moderate_risk_count > 0:
            overall_safety = 'moderate'
        
        return {
            'overall_safety': overall_safety,
            'safe_steps': safe_count,
            'moderate_steps': moderate_risk_count,
            'high_risk_steps': high_risk_count,
            'requires_approval': high_risk_count > 0 or moderate_risk_count > 0
        }
    
    async def execute_automated_troubleshooting(self, guide: TroubleshootingGuide, user_approved_steps: List[str] = None) -> Dict[str, Any]:
        """Execute automated troubleshooting steps.
        
        Args:
            guide: Troubleshooting guide to execute
            user_approved_steps: List of step titles that user has approved for execution
            
        Returns:
            Dictionary with execution results
        """
        results = {
            'guide_id': guide.problem_id,
            'steps_executed': [],
            'steps_failed': [],
            'steps_skipped': [],
            'manual_steps_required': [],
            'resolution_status': 'in_progress',
            'execution_time': time.time()
        }
        
        user_approved_steps = user_approved_steps or []
        
        for step in guide.steps:
            try:
                # Skip high-risk or moderate steps without approval
                if step.safety_level in ['moderate', 'high_risk'] and step.title not in user_approved_steps:
                    results['manual_steps_required'].append({
                        'title': step.title,
                        'description': step.description,
                        'command': step.command,
                        'safety_level': step.safety_level,
                        'requires_approval': True
                    })
                    continue
                
                if step.automated and step.command:
                    # Execute automated step
                    step_result = await self._execute_troubleshooting_step(step)
                    results['steps_executed'].append({
                        'step': step.title,
                        'action_type': step.action_type,
                        'command': step.command,
                        'result': step_result,
                        'success': step_result.get('success', False),
                        'output': step_result.get('output', ''),
                        'duration': step_result.get('duration', 0)
                    })
                    
                    if not step_result.get('success', False):
                        results['steps_failed'].append({
                            'step': step.title,
                            'error': step_result.get('error', 'Unknown error'),
                            'command': step.command
                        })
                elif step.automated and not step.command:
                    # Execute internal logic step
                    step_result = await self._execute_internal_step(step, guide)
                    results['steps_executed'].append({
                        'step': step.title,
                        'result': step_result,
                        'success': step_result.get('success', False)
                    })
                else:
                    # Manual step required
                    results['manual_steps_required'].append({
                        'title': step.title,
                        'description': step.description,
                        'command': step.command,
                        'safety_level': step.safety_level
                    })
                    
            except Exception as e:
                results['steps_failed'].append({
                    'step': step.title,
                    'error': f"Execution error: {str(e)}",
                    'command': step.command
                })
        
        # Determine resolution status
        if not results['steps_failed'] and not results['manual_steps_required']:
            results['resolution_status'] = 'resolved'
        elif results['manual_steps_required'] and not results['steps_failed']:
            results['resolution_status'] = 'manual_intervention_required'
        elif results['steps_failed']:
            results['resolution_status'] = 'failed'
        
        # Log execution history
        self.execution_history.append({
            'guide_id': guide.problem_id,
            'timestamp': time.time(),
            'results': results
        })
        
        return results
    
    async def _execute_troubleshooting_step(self, step: TroubleshootingStep) -> Dict[str, Any]:
        """Execute a single troubleshooting step.
        
        Args:
            step: The troubleshooting step to execute
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        
        try:
            # Handle different command types
            if step.command.startswith('make '):
                # Execute make command in project root
                result = await self._execute_make_command(step.command)
            else:
                # Execute shell command
                result = await self._execute_shell_command(step.command)
            
            duration = time.time() - start_time
            
            return {
                'success': result['returncode'] == 0,
                'output': result['stdout'],
                'error': result['stderr'] if result['returncode'] != 0 else None,
                'duration': duration,
                'command': step.command
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'duration': duration,
                'command': step.command
            }
    
    async def _execute_make_command(self, command: str) -> Dict[str, Any]:
        """Execute a make command in the project root."""
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=self.project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            'returncode': process.returncode,
            'stdout': stdout.decode('utf-8'),
            'stderr': stderr.decode('utf-8')
        }
    
    async def _execute_shell_command(self, command: str) -> Dict[str, Any]:
        """Execute a shell command safely."""
        # Security: Only allow specific safe commands
        safe_commands = [
            'ping', 'nslookup', 'df', 'du', 'ps', 'top', 'free',
            'netstat', 'ss', 'curl', 'wget'
        ]
        
        command_parts = command.split()
        if command_parts and command_parts[0] not in safe_commands:
            return {
                'returncode': 1,
                'stdout': '',
                'stderr': f'Command not allowed: {command_parts[0]}'
            }
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            'returncode': process.returncode,
            'stdout': stdout.decode('utf-8'),
            'stderr': stderr.decode('utf-8')
        }
    
    async def _execute_internal_step(self, step: TroubleshootingStep, guide: TroubleshootingGuide) -> Dict[str, Any]:
        """Execute internal logic steps without shell commands."""
        try:
            if "Check for Resource Bottlenecks" in step.title:
                return await self._check_resource_bottlenecks()
            elif "Test API Endpoints" in step.title:
                return await self._test_api_endpoints()
            elif "Check File Permissions" in step.title:
                return await self._check_file_permissions()
            else:
                return {'success': True, 'message': 'Internal step completed'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _check_resource_bottlenecks(self) -> Dict[str, Any]:
        """Internal method to check for resource bottlenecks."""
        try:
            # Get current dashboard data
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            metrics = dashboard_data.get('metrics', {})
            
            bottlenecks = []
            for component, comp_metrics in metrics.items():
                for metric_name, metric_data in comp_metrics.items():
                    if metric_name in ['cpu_usage', 'memory_usage']:
                        current_value = metric_data.get('current', 0)
                        if current_value > 80:  # High usage threshold
                            bottlenecks.append({
                                'component': component,
                                'metric': metric_name,
                                'value': current_value
                            })
            
            return {
                'success': True,
                'bottlenecks_found': len(bottlenecks),
                'bottlenecks': bottlenecks,
                'message': f'Found {len(bottlenecks)} resource bottlenecks'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_api_endpoints(self) -> Dict[str, Any]:
        """Test critical API endpoints."""
        endpoints = [
            'http://localhost:8000/health',
            'http://localhost:8000/api/sessions',
            'http://localhost:8000/api/config'
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                process = await asyncio.create_subprocess_shell(
                    f'curl -s -o /dev/null -w "%{{http_code}}" {endpoint}',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                status_code = stdout.decode('utf-8').strip()
                
                results.append({
                    'endpoint': endpoint,
                    'status_code': status_code,
                    'success': status_code.startswith('2')
                })
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'error': str(e),
                    'success': False
                })
        
        successful_tests = sum(1 for r in results if r.get('success', False))
        
        return {
            'success': successful_tests > 0,
            'endpoints_tested': len(endpoints),
            'successful_tests': successful_tests,
            'results': results,
            'message': f'Successfully tested {successful_tests}/{len(endpoints)} endpoints'
        }
    
    async def _check_file_permissions(self) -> Dict[str, Any]:
        """Check critical file permissions."""
        critical_files = [
            'config/',
            'logs/',
            'data/',
            'scripts/',
            '.env'
        ]
        
        permission_issues = []
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    # Check if path is readable
                    if full_path.is_file():
                        with open(full_path, 'r') as f:
                            f.read(1)  # Try to read first byte
                    elif full_path.is_dir():
                        list(full_path.iterdir())  # Try to list directory
                        
                except PermissionError:
                    permission_issues.append({
                        'path': str(full_path),
                        'issue': 'Permission denied'
                    })
                except Exception as e:
                    permission_issues.append({
                        'path': str(full_path),
                        'issue': str(e)
                    })
        
        return {
            'success': len(permission_issues) == 0,
            'files_checked': len(critical_files),
            'permission_issues': permission_issues,
            'message': f'Found {len(permission_issues)} permission issues'
        }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the history of troubleshooting executions."""
        return self.execution_history
    
    def get_available_guides(self, tags: List[str] = None) -> List[TroubleshootingGuide]:
        """Get available troubleshooting guides, optionally filtered by tags."""
        if not tags:
            return self.troubleshooting_guides
        
        filtered_guides = []
        for guide in self.troubleshooting_guides:
            if guide.tags and any(tag in guide.tags for tag in tags):
                filtered_guides.append(guide)
        
        return filtered_guides
    
    async def get_system_health_summary(self) -> Dict[str, Any]:
        """Get a comprehensive system health summary."""
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            active_alerts = self.monitoring.get_active_alerts()
            
            return {
                'health_score': dashboard_data.get('health_score', 100),
                'active_alerts_count': len(active_alerts),
                'alerts_by_severity': {
                    'critical': sum(1 for a in active_alerts if a.severity.value == 'critical'),
                    'error': sum(1 for a in active_alerts if a.severity.value == 'error'),
                    'warning': sum(1 for a in active_alerts if a.severity.value == 'warning'),
                    'info': sum(1 for a in active_alerts if a.severity.value == 'info'),
                },
                'available_guides': len(self.troubleshooting_guides),
                'recent_executions': len([e for e in self.execution_history if time.time() - e['timestamp'] < 3600]),
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'error': f'Failed to get health summary: {str(e)}',
                'health_score': 0,
                'timestamp': time.time()
            }