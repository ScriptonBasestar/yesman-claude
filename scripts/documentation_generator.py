#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Live Documentation Generator.

This script provides automated documentation generation with live system metrics
integration. It generates comprehensive documentation that stays current with
system changes and includes real-time performance data.
"""

import ast
import asyncio
import inspect
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from libs.dashboard.monitoring_integration import get_monitoring_dashboard


class LiveDocumentationGenerator:
    """Live documentation generator with system metrics integration."""
    
    def __init__(self):
        """Initialize the documentation generator."""
        self.monitoring = get_monitoring_dashboard()
        self.project_root = Path(__file__).parent.parent
        self.docs_dir = self.project_root / "docs" / "generated"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Component mapping for enhanced documentation
        self.component_map = self._build_component_map()
        
    def _build_component_map(self) -> Dict[str, Dict[str, str]]:
        """Build a map of components to their documentation details."""
        return {
            'content_capture': {
                'description': 'Captures and processes content from Claude sessions with context awareness',
                'purpose': 'Content extraction and preprocessing for automation workflows',
                'dependencies': ['claude_manager', 'session_manager'],
                'key_metrics': ['response_time', 'memory_usage', 'cpu_usage'],
                'common_issues': [
                    'High memory usage during large content processing',
                    'Slow response times with complex content structures',
                    'Session timeout during long capture operations'
                ]
            },
            'claude_status_check': {
                'description': 'Monitors Claude session status and health with real-time validation',
                'purpose': 'Ensures Claude sessions remain active and responsive',
                'dependencies': ['claude_manager', 'monitoring_integration'],
                'key_metrics': ['response_time', 'error_rate', 'availability'],
                'common_issues': [
                    'Connection timeouts to Claude API',
                    'Authentication failures',
                    'Rate limiting errors'
                ]
            },
            'prompt_detection': {
                'description': 'Intelligent detection and classification of user prompts and system interactions',
                'purpose': 'Automated prompt analysis for workflow triggers and response optimization',
                'dependencies': ['ai_adaptive_response', 'context_detector'],
                'key_metrics': ['response_time', 'accuracy_rate', 'cpu_usage'],
                'common_issues': [
                    'False positive prompt detections',
                    'High CPU usage during complex pattern matching',
                    'Accuracy degradation with unusual prompt formats'
                ]
            },
            'content_processing': {
                'description': 'Advanced content processing with AI-enhanced analysis and transformation',
                'purpose': 'Content transformation, analysis, and optimization for downstream workflows',
                'dependencies': ['content_capture', 'ai_adaptive_response'],
                'key_metrics': ['response_time', 'memory_usage', 'throughput'],
                'common_issues': [
                    'Memory leaks during large document processing',
                    'Performance degradation with complex content',
                    'Error handling for malformed content structures'
                ]
            },
            'response_sending': {
                'description': 'Handles automated response delivery with context-aware messaging',
                'purpose': 'Efficient and reliable response delivery to users and systems',
                'dependencies': ['content_processing', 'session_manager'],
                'key_metrics': ['response_time', 'success_rate', 'network_io'],
                'common_issues': [
                    'Network connectivity issues',
                    'Message delivery failures',
                    'Response formatting errors'
                ]
            },
            'automation_analysis': {
                'description': 'Comprehensive automation workflow analysis with performance insights',
                'purpose': 'Analysis and optimization of automation processes and decision workflows',
                'dependencies': ['workflow_engine', 'monitoring_integration'],
                'key_metrics': ['response_time', 'accuracy_rate', 'cpu_usage'],
                'common_issues': [
                    'Complex workflow analysis timeouts',
                    'Resource intensive analysis operations',
                    'Accuracy issues with edge case scenarios'
                ]
            },
            'test_performance': {
                'description': 'Test execution monitoring and performance analysis',
                'purpose': 'Comprehensive test suite performance tracking and optimization',
                'dependencies': ['monitoring_integration'],
                'key_metrics': ['test_success_rate', 'execution_time', 'memory_usage'],
                'common_issues': [
                    'Test timeout issues',
                    'Memory usage spikes during test execution',
                    'Flaky test results affecting reliability'
                ]
            }
        }
    
    async def generate_comprehensive_documentation(self) -> Dict[str, str]:
        """Generate all documentation with live system data.
        
        Returns:
            Dictionary mapping document names to their content
        """
        print("🚀 Starting comprehensive documentation generation...")
        docs = {}
        
        try:
            # Generate core documentation sections
            print("📊 Generating API reference with live metrics...")
            docs['api_reference'] = await self._generate_api_documentation()
            
            print("🔧 Generating component guide with performance data...")
            docs['component_guide'] = await self._generate_component_documentation()
            
            print("🔍 Generating troubleshooting guide with system context...")
            docs['troubleshooting_guide'] = await self._generate_troubleshooting_documentation()
            
            print("⚡ Generating performance optimization guide...")
            docs['performance_guide'] = await self._generate_performance_documentation()
            
            print("🚀 Generating deployment guide with current config...")
            docs['deployment_guide'] = await self._generate_deployment_documentation()
            
            print("❌ Generating error documentation with context...")
            docs['error_reference'] = await self._generate_error_documentation()
            
            print("🧪 Generating testing guide with metrics...")
            docs['testing_guide'] = await self._generate_testing_documentation()
            
            # Write all documentation files
            for doc_name, content in docs.items():
                doc_path = self.docs_dir / f"{doc_name}.md"
                with open(doc_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Generated: {doc_path}")
            
            # Generate master index
            await self._generate_documentation_index(docs)
            
            print(f"🎉 Documentation generation completed! Generated {len(docs)} documents.")
            return docs
            
        except Exception as e:
            print(f"❌ Documentation generation failed: {e}")
            return {'error': f'Generation failed: {str(e)}'}
    
    async def _generate_api_documentation(self) -> str:
        """Generate comprehensive API documentation with live examples."""
        current_time = time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Get live API health data
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            health_score = dashboard_data.get('health_score', 100)
            api_metrics = dashboard_data.get('metrics', {})
        except Exception:
            health_score = 100
            api_metrics = {}
        
        doc_content = [
            "# API Reference Documentation",
            "",
            f"*Generated on: {current_time}*",
            f"*System Health: {health_score}%*",
            "",
            "## Overview",
            "",
            "This document provides comprehensive API reference for the Yesman Claude Agent system.",
            "All examples include live system data and current performance metrics.",
            "",
            "## API Health Status",
            "",
        ]
        
        # Add API health information
        if api_metrics:
            doc_content.extend([
                "### Current API Performance",
                "",
                "| Endpoint | Response Time (ms) | Status |",
                "|----------|-------------------|--------|"
            ])
            
            for component, metrics in api_metrics.items():
                rt_data = metrics.get('response_time', {})
                avg_rt = rt_data.get('average', 0)
                status = '🟢 Healthy' if avg_rt < 100 else '🟡 Slow' if avg_rt < 200 else '🔴 Critical'
                
                doc_content.append(f"| {component} | {avg_rt:.1f} | {status} |")
            
            doc_content.extend(["", ""])
        
        # Core API Endpoints
        doc_content.extend([
            "## Core API Endpoints",
            "",
            "### Session Management",
            "",
            "#### GET /api/sessions",
            "Retrieve all active sessions with their current status.",
            "",
            "**Response Example:**",
            "```json",
            "{",
            '  "sessions": [',
            '    {',
            '      "id": "session_123",',
            '      "name": "development-session",',
            '      "status": "active",',
            f'      "health_score": {health_score},',
            '      "last_activity": "2024-01-15T10:30:00Z"',
            '    }',
            '  ],',
            f'  "total": 1,',
            f'  "system_health": {health_score}',
            "}",
            "```",
            "",
            "#### POST /api/sessions",
            "Create a new session with specified configuration.",
            "",
            "**Request Body:**",
            "```json",
            "{",
            '  "name": "new-session",',
            '  "config": {',
            '    "auto_response": true,',
            '    "monitoring_enabled": true',
            '  }',
            "}",
            "```",
            "",
            "### Dashboard API",
            "",
            "#### GET /api/dashboard/metrics",
            "Retrieve current system metrics and performance data.",
            "",
            "**Response includes:**",
            "- Real-time performance metrics",
            "- Component health status",
            "- Active alerts and warnings",
            "- Resource usage statistics",
            "",
            "#### GET /api/dashboard/health",
            f"Current system health score: **{health_score}%**",
            "",
            "### Configuration API",
            "",
            "#### GET /api/config",
            "Retrieve current system configuration.",
            "",
            "#### POST /api/config",
            "Update system configuration (requires admin privileges).",
            "",
            "### WebSocket API",
            "",
            "#### /ws/dashboard",
            "Real-time dashboard updates including:",
            "- Performance metrics",
            "- System alerts",
            "- Session status changes",
            "- Health score updates",
            "",
            "**Connection Example:**",
            "```javascript",
            "const ws = new WebSocket('ws://localhost:8000/ws/dashboard');",
            "ws.onmessage = (event) => {",
            "  const data = JSON.parse(event.data);",
            "  console.log('Dashboard update:', data);",
            "};",
            "```",
            "",
            "## Error Codes",
            "",
            "| Code | Description | Common Causes |",
            "|------|-------------|---------------|",
            "| 400 | Bad Request | Invalid JSON, missing parameters |",
            "| 401 | Unauthorized | Invalid API key or expired token |",
            "| 404 | Not Found | Session or resource doesn't exist |",
            "| 429 | Rate Limited | Too many requests, wait and retry |",
            "| 500 | Server Error | System issue, check logs |",
            "| 503 | Service Unavailable | System maintenance or overload |",
            "",
            "## Rate Limiting",
            "",
            "- API requests: 100 requests per minute per IP",
            "- WebSocket connections: 10 concurrent connections per IP",
            "- Heavy operations (session creation): 5 per minute per user",
            "",
            "## Authentication",
            "",
            "All API endpoints require authentication via:",
            "1. API Key in header: `X-API-Key: your-api-key`",
            "2. Bearer token: `Authorization: Bearer your-token`",
            "",
            "## Best Practices",
            "",
            "1. **Error Handling**: Always check response status codes",
            "2. **Rate Limiting**: Implement exponential backoff",
            "3. **Monitoring**: Use WebSocket for real-time updates",
            "4. **Caching**: Cache configuration data when possible",
            "5. **Timeouts**: Set appropriate request timeouts",
            "",
            "## SDK Examples",
            "",
            "### Python SDK",
            "```python",
            "from yesman_client import YesmanClient",
            "",
            "client = YesmanClient(api_key='your-api-key')",
            "sessions = client.sessions.list()",
            "health = client.dashboard.get_health()",
            f"print(f'System health: {health_score}%')",
            "```",
            "",
            "### JavaScript SDK",
            "```javascript",
            "import { YesmanClient } from '@yesman/client';",
            "",
            "const client = new YesmanClient({",
            "  apiKey: 'your-api-key',",
            "  baseUrl: 'http://localhost:8000'",
            "});",
            "",
            "const sessions = await client.sessions.list();",
            f"const health = await client.dashboard.getHealth(); // Current: {health_score}%",
            "```",
            "",
            "---",
            "",
            f"*Last updated: {current_time}*  ",
            f"*System Status: {health_score}% healthy*"
        ])
        
        return "\n".join(doc_content)
    
    async def _generate_component_documentation(self) -> str:
        """Generate component documentation with live performance data."""
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            components_data = dashboard_data.get('metrics', {})
        except Exception:
            dashboard_data = {'health_score': 100}
            components_data = {}
        
        current_time = time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        doc_content = [
            "# Component Performance Guide",
            "",
            "This document provides a comprehensive overview of system components with live performance data",
            "and detailed troubleshooting information.",
            "",
            f"*Generated on: {current_time}*",
            f"*System Health: {dashboard_data.get('health_score', 100)}%*",
            "",
            "## Component Overview",
            "",
            "### System Architecture",
            "",
            "The Yesman Claude Agent consists of several interconnected components that work together",
            "to provide intelligent automation and monitoring capabilities:",
            "",
        ]
        
        # Generate documentation for each component
        for component_name, component_info in self.component_map.items():
            metrics = components_data.get(component_name, {})
            
            doc_content.extend([
                f"### {component_name.replace('_', ' ').title()}",
                "",
                f"**Description:** {component_info['description']}",
                "",
                f"**Purpose:** {component_info['purpose']}",
                "",
                f"**Dependencies:** {', '.join(component_info['dependencies'])}",
                ""
            ])
            
            # Health status
            is_healthy = self._is_component_healthy(metrics)
            status_icon = '🟢' if is_healthy else '🔴'
            status_text = 'Healthy' if is_healthy else 'Issues Detected'
            
            doc_content.extend([
                f"**Current Status:** {status_icon} {status_text}",
                ""
            ])
            
            # Performance metrics
            if metrics:
                doc_content.extend([
                    "#### Live Performance Metrics",
                    "",
                    "| Metric | Current | Average | Peak | Status |",
                    "|--------|---------|---------|------|--------|"
                ])
                
                for metric_name in component_info['key_metrics']:
                    if metric_name in metrics:
                        metric_data = metrics[metric_name]
                        current_val = metric_data.get('current', 0)
                        avg_val = metric_data.get('average', 0)
                        max_val = metric_data.get('max', 0)
                        
                        # Determine status
                        status = self._get_metric_status(metric_name, current_val)
                        
                        doc_content.append(
                            f"| {metric_name.replace('_', ' ').title()} | "
                            f"{current_val:.1f} | {avg_val:.1f} | {max_val:.1f} | {status} |"
                        )
                
                doc_content.extend(["", ""])
            else:
                doc_content.extend([
                    "#### Performance Metrics",
                    "",
                    "⚠️ No current metrics available. Component may not be active or monitored.",
                    "",
                ])
            
            # Common issues and solutions
            doc_content.extend([
                "#### Common Issues & Solutions",
                "",
            ])
            
            for i, issue in enumerate(component_info['common_issues'], 1):
                doc_content.extend([
                    f"{i}. **{issue}**",
                    f"   - *Check:* Monitor {', '.join(component_info['key_metrics'])} metrics",
                    f"   - *Solution:* Refer to troubleshooting guide for automated fixes",
                    ""
                ])
            
            # Configuration and optimization
            doc_content.extend([
                "#### Configuration & Optimization",
                "",
                "**Key Configuration Parameters:**",
                "- Response time targets: < 100ms average",
                "- Memory usage limits: < 10MB per operation",
                "- Error rate threshold: < 1%",
                "",
                "**Optimization Tips:**",
                "- Enable caching for frequently accessed data",
                "- Monitor resource usage patterns",
                "- Use connection pooling where applicable",
                "- Implement circuit breakers for external dependencies",
                "",
                "**Monitoring Commands:**",
                f"```bash",
                f"# Check {component_name} status",
                f"make component-status COMPONENT={component_name}",
                f"",
                f"# View detailed metrics",
                f"make performance-report COMPONENT={component_name}",
                f"",
                f"# Restart component if needed",
                f"make restart-component COMPONENT={component_name}",
                f"```",
                "",
                "---",
                ""
            ])
        
        # Add system-wide information
        doc_content.extend([
            "## System-Wide Metrics",
            "",
            "### Overall Health Assessment",
            "",
        ])
        
        if components_data:
            healthy_components = sum(1 for comp_metrics in components_data.values() 
                                   if self._is_component_healthy(comp_metrics))
            total_components = len(components_data)
            health_percentage = (healthy_components / total_components * 100) if total_components > 0 else 100
            
            doc_content.extend([
                f"- **Healthy Components:** {healthy_components}/{total_components} ({health_percentage:.1f}%)",
                f"- **System Health Score:** {dashboard_data.get('health_score', 100):.1f}%",
                "",
                "### Resource Usage Summary",
                "",
            ])
            
            # Calculate average metrics across all components
            avg_metrics = self._calculate_average_metrics(components_data)
            
            doc_content.extend([
                "| Resource | Average Usage | Status | Recommendation |",
                "|----------|---------------|--------|----------------|"
            ])
            
            for metric_name, avg_value in avg_metrics.items():
                status = self._get_metric_status(metric_name, avg_value)
                recommendation = self._get_optimization_recommendation(metric_name, avg_value)
                
                doc_content.append(
                    f"| {metric_name.replace('_', ' ').title()} | "
                    f"{avg_value:.1f} | {status} | {recommendation} |"
                )
        
        doc_content.extend([
            "",
            "## Troubleshooting Quick Reference",
            "",
            "### Performance Issues",
            "1. **High Response Time**: Check system load, review database queries",
            "2. **Memory Leaks**: Monitor memory usage patterns, restart affected components",
            "3. **CPU Spikes**: Identify resource-intensive operations, optimize algorithms",
            "",
            "### Common Commands",
            "```bash",
            "# System health check",
            "make system-status",
            "",
            "# Component-specific diagnostics",
            "make component-diagnostics COMPONENT=<component_name>",
            "",
            "# Performance monitoring",
            "make performance-monitor",
            "",
            "# Emergency component restart",
            "make emergency-restart COMPONENT=<component_name>",
            "```",
            "",
            "---",
            "",
            f"*Documentation generated: {current_time}*  ",
            f"*Next update: Automated refresh every 30 minutes*  ",
            f"*For real-time metrics, visit the dashboard at http://localhost:1420*"
        ])
        
        return "\n".join(doc_content)
    
    def _is_component_healthy(self, metrics: Dict) -> bool:
        """Determine if a component is healthy based on its metrics."""
        if not metrics:
            return False
        
        # Check response time
        rt_data = metrics.get('response_time', {})
        if rt_data.get('average', 0) > 100:  # > 100ms average
            return False
        
        # Check memory usage
        mem_data = metrics.get('memory_usage', {})
        if mem_data.get('current', 0) > 20:  # > 20MB current usage
            return False
        
        # Check error rate
        error_data = metrics.get('error_rate', {})
        if error_data.get('current', 0) > 0.01:  # > 1% error rate
            return False
        
        return True
    
    def _get_metric_status(self, metric_name: str, value: float) -> str:
        """Get status icon for a metric value."""
        thresholds = {
            'response_time': {'good': 50, 'warning': 100, 'critical': 200},
            'memory_usage': {'good': 5, 'warning': 10, 'critical': 20},
            'cpu_usage': {'good': 30, 'warning': 60, 'critical': 90},
            'error_rate': {'good': 0.001, 'warning': 0.01, 'critical': 0.05}
        }
        
        if metric_name not in thresholds:
            return '➖'
        
        threshold = thresholds[metric_name]
        
        if value <= threshold['good']:
            return '🟢 Good'
        elif value <= threshold['warning']:
            return '🟡 Warning'
        elif value <= threshold['critical']:
            return '🟠 Critical'
        else:
            return '🔴 Severe'
    
    def _get_optimization_recommendation(self, metric_name: str, value: float) -> str:
        """Get optimization recommendation for a metric."""
        recommendations = {
            'response_time': {
                50: 'Optimal',
                100: 'Consider caching',
                200: 'Optimize queries',
                float('inf'): 'Critical - immediate attention needed'
            },
            'memory_usage': {
                5: 'Efficient',
                10: 'Monitor growth',
                20: 'Investigate leaks',
                float('inf'): 'Critical - restart recommended'
            },
            'cpu_usage': {
                30: 'Efficient',
                60: 'Monitor load',
                90: 'Scale resources',
                float('inf'): 'Critical - investigate bottlenecks'
            },
            'error_rate': {
                0.001: 'Excellent',
                0.01: 'Investigate patterns',
                0.05: 'Fix critical issues',
                float('inf'): 'Critical - system unstable'
            }
        }
        
        if metric_name not in recommendations:
            return 'Monitor'
        
        rec_map = recommendations[metric_name]
        for threshold, recommendation in rec_map.items():
            if value <= threshold:
                return recommendation
        
        return 'Critical action needed'
    
    def _calculate_average_metrics(self, components_data: Dict) -> Dict[str, float]:
        """Calculate average metrics across all components."""
        metric_totals = defaultdict(list)
        
        for component, metrics in components_data.items():
            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict) and 'average' in metric_data:
                    metric_totals[metric_name].append(metric_data['average'])
        
        return {
            metric_name: sum(values) / len(values) if values else 0
            for metric_name, values in metric_totals.items()
        }
    
    async def _generate_troubleshooting_documentation(self) -> str:
        """Generate troubleshooting guide with current system context."""
        current_time = time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            active_alerts = self.monitoring.get_active_alerts()
        except Exception:
            dashboard_data = {'health_score': 100}
            active_alerts = []
        
        doc_content = [
            "# Comprehensive Troubleshooting Guide",
            "",
            "This guide provides step-by-step troubleshooting procedures with live system context",
            "and automated resolution capabilities.",
            "",
            f"*Generated on: {current_time}*",
            f"*System Health: {dashboard_data.get('health_score', 100)}%*",
            f"*Active Alerts: {len(active_alerts)}*",
            "",
        ]
        
        # Current system status
        if active_alerts:
            doc_content.extend([
                "## 🚨 Current System Alerts",
                "",
                "| Severity | Component | Message | Time |",
                "|----------|-----------|---------|------|"
            ])
            
            for alert in active_alerts[:10]:  # Show top 10 alerts
                time_str = time.strftime('%H:%M:%S', time.localtime(alert.timestamp))
                doc_content.append(
                    f"| {alert.severity.value.upper()} | {alert.component} | "
                    f"{alert.message[:50]}... | {time_str} |"
                )
            
            doc_content.extend(["", ""])
        else:
            doc_content.extend([
                "## ✅ System Status: All Clear",
                "",
                "No active alerts detected. System is operating normally.",
                "",
            ])
        
        # Troubleshooting categories
        doc_content.extend([
            "## Troubleshooting Categories",
            "",
            "### 🚀 Performance Issues",
            "",
            "#### High Response Time",
            "",
            "**Symptoms:**",
            "- API responses > 100ms",
            "- User interface feels sluggish",
            "- Dashboard updates are delayed",
            "",
            "**Automated Diagnosis:**",
            "```bash",
            "# Check current response times",
            "make performance-report",
            "",
            "# Run automated troubleshooting",
            "python -m libs.troubleshooting.troubleshooting_engine",
            "```",
            "",
            "**Manual Steps:**",
            "1. Check system resource usage: `make system-status`",
            "2. Identify bottleneck components",
            "3. Review recent changes or deployments",
            "4. Scale resources if needed",
            "",
            "#### Memory Issues",
            "",
            "**Symptoms:**",
            "- Memory usage > 1GB",
            "- Frequent garbage collection",
            "- System becomes unresponsive",
            "",
            "**Resolution Steps:**",
            "1. **Immediate:** `make clean-cache && make restart-components`",
            "2. **Investigation:** Check memory usage patterns",
            "3. **Prevention:** Implement memory monitoring alerts",
            "",
            "### 🔒 Security Issues",
            "",
            "#### Authentication Failures",
            "",
            "**Symptoms:**",
            "- Failed login attempts",
            "- API key validation errors",
            "- Token expiration issues",
            "",
            "**Automated Resolution:**",
            "```bash",
            "# Run security validation",
            "make security-check",
            "",
            "# Reset authentication if needed",
            "make auth-reset",
            "```",
            "",
            "### 🌐 Network Issues",
            "",
            "#### Connection Problems",
            "",
            "**Symptoms:**",
            "- API timeouts",
            "- Claude connection failures",
            "- Dashboard not loading",
            "",
            "**Quick Fixes:**",
            "1. **Network Test:** `ping -c 4 anthropic.com`",
            "2. **Service Restart:** `make restart-network-services`",
            "3. **Port Check:** `netstat -tlnp | grep :8000`",
            "",
            "### 💾 Data Issues",
            "",
            "#### Database Problems",
            "",
            "**Symptoms:**",
            "- Session data not persisting",
            "- Configuration changes lost",
            "- Query performance degradation",
            "",
            "**Resolution:**",
            "```bash",
            "# Database health check",
            "make db-check",
            "",
            "# Repair if needed",
            "make db-repair",
            "",
            "# Backup before major changes",
            "make db-backup",
            "```",
            "",
            "## 🔧 Automated Troubleshooting",
            "",
            "The system includes an intelligent troubleshooting engine that can automatically",
            "diagnose and fix common issues.",
            "",
            "### Using the Troubleshooting Engine",
            "",
            "```python",
            "from libs.troubleshooting import IntelligentTroubleshootingEngine",
            "",
            "# Initialize the engine",
            "engine = IntelligentTroubleshootingEngine()",
            "",
            "# Diagnose current issues",
            "issues = await engine.diagnose_current_issues()",
            "",
            "# Execute automated fixes",
            "for issue in issues:",
            "    if issue['automated_steps_available'] > 0:",
            "        results = await engine.execute_automated_troubleshooting(issue['guide'])",
            "        print(f'Resolution status: {results[\"resolution_status\"]}'))",
            "```",
            "",
            "### Available Automated Fixes",
            "",
            "| Issue Type | Automation Level | Safety Level |",
            "|------------|-----------------|--------------|",
            "| High Response Time | Partial | Safe |",
            "| Memory Issues | Full | Safe |",
            "| Cache Problems | Full | Safe |",
            "| Network Connectivity | Partial | Moderate |",
            "| Security Violations | Partial | High Risk |",
            "",
            "## 📊 Diagnostic Commands",
            "",
            "### System Health",
            "```bash",
            "# Overall system status",
            "make system-status",
            "",
            "# Component health check",
            "make health-check",
            "",
            "# Performance metrics",
            "make performance-report",
            "",
            "# Security validation",
            "make security-check",
            "```",
            "",
            "### Logging and Monitoring",
            "```bash",
            "# View recent logs",
            "make logs-recent",
            "",
            "# Monitor real-time activity",
            "make monitor-realtime",
            "",
            "# Export diagnostic data",
            "make diagnostic-export",
            "```",
            "",
            "### Recovery Operations",
            "```bash",
            "# Emergency restart",
            "make emergency-restart",
            "",
            "# Safe component restart",
            "make restart-component COMPONENT=<name>",
            "",
            "# Full system reset (use with caution)",
            "make system-reset",
            "```",
            "",
            "## 🚨 Emergency Procedures",
            "",
            "### System Unresponsive",
            "1. **Check Process Status:** `ps aux | grep yesman`",
            "2. **Force Restart:** `make force-restart`",
            "3. **Check Logs:** `tail -100 logs/emergency.log`",
            "4. **Contact Support:** Include diagnostic data",
            "",
            "### Data Corruption",
            "1. **Stop System:** `make stop-all`",
            "2. **Restore Backup:** `make restore-backup BACKUP=latest`",
            "3. **Validate Integrity:** `make data-integrity-check`",
            "4. **Resume Operations:** `make start-all`",
            "",
            "### Security Incident",
            "1. **Isolate System:** `make security-isolate`",
            "2. **Collect Evidence:** `make security-audit-full`",
            "3. **Reset Credentials:** `make security-reset-all`",
            "4. **Review Access Logs:** `make security-logs-review`",
            "",
            "## 📞 Support Escalation",
            "",
            "### When to Escalate",
            "- System health < 50% for > 10 minutes",
            "- Critical security alerts",
            "- Data integrity issues",
            "- Multiple component failures",
            "",
            "### Information to Provide",
            "1. **System Status:** `make diagnostic-full-report`",
            "2. **Error Logs:** Recent error messages and stack traces",
            "3. **Reproduction Steps:** How to reproduce the issue",
            "4. **Impact Assessment:** What functionality is affected",
            "",
            "### Contact Information",
            "- **Emergency:** Create GitHub issue with 'emergency' label",
            "- **General Support:** Use GitHub issues with appropriate labels",
            "- **Documentation Issues:** Contribute via pull request",
            "",
            "---",
            "",
            f"*Last Updated: {current_time}*  ",
            f"*Auto-refresh: Every 15 minutes or when alerts change*  ",
            f"*For real-time troubleshooting, use the dashboard at http://localhost:1420*"
        ])
        
        return "\n".join(doc_content)
    
    async def _generate_performance_documentation(self) -> str:
        """Generate performance optimization guide with current metrics."""
        current_time = time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            metrics = dashboard_data.get('metrics', {})
        except Exception:
            dashboard_data = {'health_score': 100}
            metrics = {}
        
        doc_content = [
            "# Performance Optimization Guide",
            "",
            "Comprehensive guide for optimizing Yesman Claude Agent performance with",
            "live system analysis and actionable recommendations.",
            "",
            f"*Generated on: {current_time}*",
            f"*System Health: {dashboard_data.get('health_score', 100)}%*",
            "",
            "## Current Performance Overview",
            "",
        ]
        
        if metrics:
            # Calculate performance summary
            total_components = len(metrics)
            avg_response_time = sum(
                comp.get('response_time', {}).get('average', 0)
                for comp in metrics.values()
            ) / total_components if total_components > 0 else 0
            
            doc_content.extend([
                f"- **Components Monitored:** {total_components}",
                f"- **Average Response Time:** {avg_response_time:.1f}ms",
                f"- **Performance Target:** < 100ms",
                f"- **Status:** {'✅ Meeting targets' if avg_response_time < 100 else '⚠️ Above targets'}",
                "",
                "### Component Performance Analysis",
                "",
                "| Component | Response Time | Memory Usage | CPU Usage | Optimization Priority |",
                "|-----------|---------------|--------------|-----------|---------------------|"
            ])
            
            for component, comp_metrics in metrics.items():
                rt = comp_metrics.get('response_time', {}).get('average', 0)
                mem = comp_metrics.get('memory_usage', {}).get('current', 0)
                cpu = comp_metrics.get('cpu_usage', {}).get('average', 0)
                
                priority = 'High' if rt > 200 or mem > 15 or cpu > 80 else \
                          'Medium' if rt > 100 or mem > 10 or cpu > 50 else 'Low'
                
                doc_content.append(
                    f"| {component} | {rt:.1f}ms | {mem:.1f}MB | {cpu:.1f}% | {priority} |"
                )
        
        doc_content.extend([
            "",
            "## Optimization Strategies",
            "",
            "### Response Time Optimization",
            "",
            "#### 1. Caching Implementation",
            "```python",
            "# Enable component-level caching",
            "from libs.core.config_cache import enable_caching",
            "",
            "# Cache frequently accessed data",
            "enable_caching()",
            "```",
            "",
            "**Benefits:**",
            "- Reduces database queries by 60-80%",
            "- Improves response time by 40-60%",
            "- Lower CPU usage during peak loads",
            "",
            "#### 2. Connection Pooling",
            "```yaml",
            "# config/production.yaml",
            "database:",
            "  pool_size: 20",
            "  max_overflow: 30",
            "  pool_timeout: 30",
            "```",
            "",
            "#### 3. Asynchronous Processing",
            "```python",
            "# Use async operations for I/O bound tasks",
            "import asyncio",
            "",
            "async def optimized_processing():",
            "    tasks = [",
            "        process_component_async(comp)",
            "        for comp in components",
            "    ]",
            "    results = await asyncio.gather(*tasks)",
            "    return results",
            "```",
            "",
            "### Memory Optimization",
            "",
            "#### 1. Memory Profiling",
            "```bash",
            "# Monitor memory usage",
            "make memory-profile",
            "",
            "# Identify memory leaks",
            "make memory-leak-check",
            "```",
            "",
            "#### 2. Garbage Collection Tuning",
            "```python",
            "import gc",
            "",
            "# Optimize garbage collection",
            "gc.set_threshold(700, 10, 10)",
            "gc.collect()  # Force collection when needed",
            "```",
            "",
            "#### 3. Data Structure Optimization",
            "- Use generators for large datasets",
            "- Implement lazy loading for heavy objects",
            "- Clear references when objects are no longer needed",
            "",
            "### CPU Optimization",
            "",
            "#### 1. Process Pool for CPU-Intensive Tasks",
            "```python",
            "from concurrent.futures import ProcessPoolExecutor",
            "",
            "with ProcessPoolExecutor(max_workers=4) as executor:",
            "    futures = [",
            "        executor.submit(cpu_intensive_task, data)",
            "        for data in dataset",
            "    ]",
            "    results = [future.result() for future in futures]",
            "```",
            "",
            "#### 2. Algorithm Optimization",
            "- Replace O(n²) algorithms with O(n log n) where possible",
            "- Use binary search for sorted data",
            "- Implement memoization for recursive functions",
            "",
            "### Database Performance",
            "",
            "#### 1. Query Optimization",
            "```sql",
            "-- Add appropriate indexes",
            "CREATE INDEX idx_session_timestamp ON sessions(last_activity);",
            "CREATE INDEX idx_metrics_component ON metrics(component_name, timestamp);",
            "```",
            "",
            "#### 2. Connection Management",
            "```python",
            "# Use connection pooling",
            "from sqlalchemy import create_engine",
            "",
            "engine = create_engine(",
            "    'sqlite:///yesman.db',",
            "    pool_size=20,",
            "    max_overflow=0,",
            "    pool_pre_ping=True",
            ")",
            "```",
            "",
            "## Performance Monitoring",
            "",
            "### Real-time Monitoring Setup",
            "```bash",
            "# Start performance monitoring",
            "make performance-monitor-start",
            "",
            "# View real-time metrics",
            "make performance-dashboard",
            "",
            "# Set up alerts",
            "make performance-alerts-configure",
            "```",
            "",
            "### Key Performance Indicators (KPIs)",
            "",
            "| Metric | Target | Warning | Critical | Current Status |",
            "|--------|--------|---------|----------|----------------|"
        ])
        
        # Add current KPI status if metrics available
        if metrics:
            kpi_metrics = [
                ('Response Time', 'ms', 100, 200, avg_response_time),
                ('Memory Usage', 'MB', 50, 100, sum(comp.get('memory_usage', {}).get('current', 0) for comp in metrics.values())),
                ('CPU Usage', '%', 70, 90, sum(comp.get('cpu_usage', {}).get('average', 0) for comp in metrics.values()) / len(metrics)),
                ('Error Rate', '%', 1, 5, sum(comp.get('error_rate', {}).get('current', 0) for comp in metrics.values()) * 100 / len(metrics))
            ]
            
            for name, unit, target, critical, current in kpi_metrics:
                status = '🟢 Good' if current <= target else '🟡 Warning' if current <= critical else '🔴 Critical'
                doc_content.append(f"| {name} | < {target}{unit} | < {critical}{unit} | > {critical}{unit} | {current:.1f}{unit} {status} |")
        
        doc_content.extend([
            "",
            "## Performance Testing",
            "",
            "### Load Testing",
            "```bash",
            "# Run load tests",
            "make load-test",
            "",
            "# Stress test specific components",
            "make stress-test COMPONENT=content_processing",
            "",
            "# Benchmark against baseline",
            "make performance-benchmark",
            "```",
            "",
            "### Performance Regression Testing",
            "```bash",
            "# Establish performance baseline",
            "make performance-baseline-create",
            "",
            "# Run regression tests",
            "make performance-regression-test",
            "",
            "# Compare with previous versions",
            "make performance-compare VERSION=v1.0.0",
            "```",
            "",
            "## Optimization Checklist",
            "",
            "### Daily Tasks",
            "- [ ] Check system health score (target: > 95%)",
            "- [ ] Review response time metrics",
            "- [ ] Monitor memory usage trends",
            "- [ ] Check for performance alerts",
            "",
            "### Weekly Tasks",
            "- [ ] Run full performance analysis",
            "- [ ] Review and optimize slow queries",
            "- [ ] Clean up temporary files and caches",
            "- [ ] Update performance baselines",
            "",
            "### Monthly Tasks",
            "- [ ] Comprehensive performance audit",
            "- [ ] Capacity planning review",
            "- [ ] Performance testing full suite",
            "- [ ] Documentation updates",
            "",
            "## Scaling Recommendations",
            "",
            "### Horizontal Scaling",
            "- Deploy multiple instances behind load balancer",
            "- Implement session affinity for stateful components",
            "- Use distributed caching (Redis)",
            "",
            "### Vertical Scaling",
            "- Increase CPU cores for compute-intensive tasks",
            "- Add memory for large dataset processing",
            "- Upgrade storage for I/O intensive operations",
            "",
            "### Auto-scaling Configuration",
            "```yaml",
            "# Auto-scaling rules",
            "scaling:",
            "  cpu_threshold: 70",
            "  memory_threshold: 80",
            "  response_time_threshold: 150",
            "  min_instances: 2",
            "  max_instances: 10",
            "```",
            "",
            "---",
            "",
            f"*Performance guide updated: {current_time}*  ",
            f"*Next analysis: Scheduled every hour*  ",
            f"*For real-time metrics: http://localhost:1420/performance*"
        ])
        
        return "\n".join(doc_content)
    
    async def _generate_deployment_documentation(self) -> str:
        """Generate deployment guide with current configuration."""
        current_time = time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        doc_content = [
            "# Deployment Guide",
            "",
            "Comprehensive deployment guide for the Yesman Claude Agent with current",
            "configuration examples and best practices.",
            "",
            f"*Generated on: {current_time}*",
            "",
            "## Deployment Overview",
            "",
            "The Yesman Claude Agent supports multiple deployment strategies:",
            "",
            "- **Local Development**: Single-machine setup for development",
            "- **Production Single-Node**: Optimized single-server deployment", 
            "- **Multi-Node Cluster**: High-availability distributed deployment",
            "- **Container Deployment**: Docker-based deployment",
            "",
            "## Quick Start Deployment",
            "",
            "### Prerequisites",
            "```bash",
            "# System requirements check",
            "make deployment-requirements-check",
            "",
            "# Install system dependencies",
            "sudo apt update && sudo apt install -y python3.9 python3-pip git",
            "",
            "# Install uv (Python package manager)",
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "```",
            "",
            "### Local Development Setup",
            "```bash",
            "# Clone repository",
            "git clone https://github.com/your-org/yesman-agent.git",
            "cd yesman-agent",
            "",
            "# Install dependencies",
            "uv sync",
            "",
            "# Initialize configuration",
            "make setup",
            "",
            "# Start development server",
            "make dev",
            "```",
            "",
            "### Production Deployment",
            "",
            "#### 1. Environment Preparation",
            "```bash",
            "# Create deployment directory",
            "sudo mkdir -p /opt/yesman-agent",
            "sudo chown $USER:$USER /opt/yesman-agent",
            "cd /opt/yesman-agent",
            "",
            "# Clone and configure",
            "git clone https://github.com/your-org/yesman-agent.git .",
            "uv sync --frozen",
            "```",
            "",
            "#### 2. Configuration",
            "```yaml",
            "# config/production.yaml",
            "server:",
            "  host: 0.0.0.0",
            "  port: 8000",
            "  workers: 4",
            "",
            "database:",
            "  url: postgresql://user:pass@localhost:5432/yesman",
            "  pool_size: 20",
            "",
            "monitoring:",
            "  enabled: true",
            "  metrics_interval: 60",
            "  health_check_interval: 30",
            "",
            "security:",
            "  api_key_required: true",
            "  rate_limiting: true",
            "  max_requests_per_minute: 100",
            "```",
            "",
            "#### 3. Service Configuration",
            "```ini",
            "# /etc/systemd/system/yesman-agent.service",
            "[Unit]",
            "Description=Yesman Claude Agent",
            "After=network.target",
            "",
            "[Service]",
            "Type=exec",
            "User=yesman",
            "Group=yesman",
            "WorkingDirectory=/opt/yesman-agent",
            "Environment=YESMAN_CONFIG=production",
            "ExecStart=/opt/yesman-agent/.venv/bin/python -m api.main",
            "Restart=always",
            "RestartSec=10",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "```",
            "",
            "```bash",
            "# Enable and start service",
            "sudo systemctl enable yesman-agent",
            "sudo systemctl start yesman-agent",
            "sudo systemctl status yesman-agent",
            "```",
            "",
            "## Docker Deployment",
            "",
            "### Dockerfile",
            "```dockerfile",
            "FROM python:3.9-slim",
            "",
            "# Install system dependencies",
            "RUN apt-get update && apt-get install -y \\",
            "    git curl build-essential \\",
            "    && rm -rf /var/lib/apt/lists/*",
            "",
            "# Install uv",
            "RUN curl -LsSf https://astral.sh/uv/install.sh | sh",
            "ENV PATH=\"/root/.cargo/bin:$PATH\"",
            "",
            "# Set working directory",
            "WORKDIR /app",
            "",
            "# Copy project files",
            "COPY . .",
            "",
            "# Install dependencies",
            "RUN uv sync --frozen",
            "",
            "# Expose port",
            "EXPOSE 8000",
            "",
            "# Start application",
            "CMD [\"uv\", \"run\", \"python\", \"-m\", \"api.main\"]",
            "```",
            "",
            "### Docker Compose",
            "```yaml",
            "version: '3.8'",
            "",
            "services:",
            "  yesman-agent:",
            "    build: .",
            "    ports:",
            "      - \"8000:8000\"",
            "    environment:",
            "      - YESMAN_CONFIG=production",
            "    volumes:",
            "      - ./data:/app/data",
            "      - ./logs:/app/logs",
            "    depends_on:",
            "      - postgres",
            "      - redis",
            "",
            "  postgres:",
            "    image: postgres:13",
            "    environment:",
            "      POSTGRES_DB: yesman",
            "      POSTGRES_USER: yesman",
            "      POSTGRES_PASSWORD: secure_password",
            "    volumes:",
            "      - postgres_data:/var/lib/postgresql/data",
            "",
            "  redis:",
            "    image: redis:6-alpine",
            "    command: redis-server --appendonly yes",
            "    volumes:",
            "      - redis_data:/data",
            "",
            "volumes:",
            "  postgres_data:",
            "  redis_data:",
            "```",
            "",
            "### Deployment Commands",
            "```bash",
            "# Build and start",
            "docker-compose up -d --build",
            "",
            "# View logs",
            "docker-compose logs -f yesman-agent",
            "",
            "# Scale services",
            "docker-compose up -d --scale yesman-agent=3",
            "",
            "# Health check",
            "docker-compose exec yesman-agent make health-check",
            "```",
            "",
            "## Kubernetes Deployment",
            "",
            "### Deployment Manifest",
            "```yaml",
            "apiVersion: apps/v1",
            "kind: Deployment",
            "metadata:",
            "  name: yesman-agent",
            "  labels:",
            "    app: yesman-agent",
            "spec:",
            "  replicas: 3",
            "  selector:",
            "    matchLabels:",
            "      app: yesman-agent",
            "  template:",
            "    metadata:",
            "      labels:",
            "        app: yesman-agent",
            "    spec:",
            "      containers:",
            "      - name: yesman-agent",
            "        image: yesman-agent:latest",
            "        ports:",
            "        - containerPort: 8000",
            "        env:",
            "        - name: YESMAN_CONFIG",
            "          value: \"production\"",
            "        resources:",
            "          requests:",
            "            memory: \"512Mi\"",
            "            cpu: \"500m\"",
            "          limits:",
            "            memory: \"1Gi\"",
            "            cpu: \"1000m\"",
            "        livenessProbe:",
            "          httpGet:",
            "            path: /health",
            "            port: 8000",
            "          initialDelaySeconds: 30",
            "          periodSeconds: 10",
            "        readinessProbe:",
            "          httpGet:",
            "            path: /ready",
            "            port: 8000",
            "          initialDelaySeconds: 5",
            "          periodSeconds: 5",
            "```",
            "",
            "## Monitoring and Observability",
            "",
            "### Prometheus Configuration",
            "```yaml",
            "# prometheus.yml",
            "scrape_configs:",
            "  - job_name: 'yesman-agent'",
            "    static_configs:",
            "      - targets: ['localhost:8000']",
            "    metrics_path: '/metrics'",
            "    scrape_interval: 30s",
            "```",
            "",
            "### Grafana Dashboard",
            "```json",
            "{",
            '  "dashboard": {',
            '    "title": "Yesman Agent Metrics",',
            '    "panels": [',
            '      {',
            '        "title": "Response Time",',
            '        "type": "graph",',
            '        "targets": [',
            '          {',
            '            "expr": "yesman_response_time_average"',
            '          }',
            '        ]',
            '      }',
            '    ]',
            '  }',
            "}",
            "```",
            "",
            "## Security Considerations",
            "",
            "### SSL/TLS Configuration",
            "```nginx",
            "# /etc/nginx/sites-available/yesman-agent",
            "server {",
            "    listen 443 ssl http2;",
            "    server_name your-domain.com;",
            "",
            "    ssl_certificate /etc/ssl/certs/your-domain.crt;",
            "    ssl_certificate_key /etc/ssl/private/your-domain.key;",
            "",
            "    location / {",
            "        proxy_pass http://127.0.0.1:8000;",
            "        proxy_set_header Host $host;",
            "        proxy_set_header X-Real-IP $remote_addr;",
            "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
            "        proxy_set_header X-Forwarded-Proto $scheme;",
            "    }",
            "}",
            "```",
            "",
            "### Firewall Rules",
            "```bash",
            "# UFW configuration",
            "sudo ufw default deny incoming",
            "sudo ufw default allow outgoing",
            "sudo ufw allow ssh",
            "sudo ufw allow 443/tcp",
            "sudo ufw allow 80/tcp",
            "sudo ufw --force enable",
            "```",
            "",
            "## Backup and Recovery",
            "",
            "### Automated Backups",
            "```bash",
            "#!/bin/bash",
            "# backup.sh",
            "BACKUP_DIR=\"/opt/backups/yesman-$(date +%Y%m%d_%H%M%S)\"",
            "mkdir -p $BACKUP_DIR",
            "",
            "# Backup database",
            "pg_dump yesman > $BACKUP_DIR/database.sql",
            "",
            "# Backup configuration",
            "cp -r /opt/yesman-agent/config $BACKUP_DIR/",
            "",
            "# Backup data directory",
            "cp -r /opt/yesman-agent/data $BACKUP_DIR/",
            "",
            "# Compress backup",
            "tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR",
            "rm -rf $BACKUP_DIR",
            "```",
            "",
            "### Recovery Procedures",
            "```bash",
            "# Stop services",
            "sudo systemctl stop yesman-agent",
            "",
            "# Restore database",
            "psql yesman < backup/database.sql",
            "",
            "# Restore configuration",
            "cp -r backup/config/* /opt/yesman-agent/config/",
            "",
            "# Restore data",
            "cp -r backup/data/* /opt/yesman-agent/data/",
            "",
            "# Restart services",
            "sudo systemctl start yesman-agent",
            "```",
            "",
            "## Troubleshooting Deployment Issues",
            "",
            "### Common Issues",
            "",
            "#### Permission Denied",
            "```bash",
            "# Fix ownership",
            "sudo chown -R yesman:yesman /opt/yesman-agent",
            "",
            "# Fix permissions",
            "chmod +x /opt/yesman-agent/scripts/*.py",
            "```",
            "",
            "#### Port Already in Use",
            "```bash",
            "# Find process using port",
            "sudo netstat -tlnp | grep :8000",
            "",
            "# Kill process",
            "sudo kill -9 <PID>",
            "```",
            "",
            "#### Database Connection Failed",
            "```bash",
            "# Test database connection",
            "psql -h localhost -U yesman -d yesman",
            "",
            "# Check database service",
            "sudo systemctl status postgresql",
            "```",
            "",
            "## Performance Tuning",
            "",
            "### Production Optimizations",
            "```yaml",
            "# config/production.yaml",
            "server:",
            "  workers: 4  # Number of CPU cores",
            "  worker_connections: 1000",
            "  keepalive_timeout: 65",
            "",
            "database:",
            "  pool_size: 20",
            "  max_overflow: 30",
            "  pool_timeout: 30",
            "",
            "caching:",
            "  enabled: true",
            "  backend: redis",
            "  ttl: 3600",
            "```",
            "",
            "### Resource Limits",
            "```bash",
            "# Set system limits",
            "echo 'yesman soft nofile 65536' >> /etc/security/limits.conf",
            "echo 'yesman hard nofile 65536' >> /etc/security/limits.conf",
            "```",
            "",
            "---",
            "",
            f"*Deployment guide updated: {current_time}*  ",
            f"*For deployment support: Create GitHub issue with 'deployment' label*"
        ])
        
        return "\n".join(doc_content)
    
    async def _generate_error_documentation(self) -> str:
        """Generate error documentation with contextual examples."""
        current_time = time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        doc_content = [
            "# Error Reference Documentation",
            "",
            "Comprehensive error reference with contextual examples, resolution steps,",
            "and automated troubleshooting capabilities.",
            "",
            f"*Generated on: {current_time}*",
            "",
            "## Error Categories",
            "",
            "### System Errors (SYS-xxx)",
            "",
            "#### SYS-001: High Response Time",
            "**Description:** System response time exceeds acceptable thresholds",
            "",
            "**Symptoms:**",
            "- API requests taking > 100ms",
            "- Dashboard loading slowly",
            "- User interface lag",
            "",
            "**Common Causes:**",
            "- High system load",
            "- Database query bottlenecks",
            "- Network latency",
            "- Memory pressure",
            "",
            "**Automated Resolution:**",
            "```python",
            "from libs.troubleshooting import IntelligentTroubleshootingEngine",
            "",
            "engine = IntelligentTroubleshootingEngine()",
            "issues = await engine.diagnose_current_issues()",
            "results = await engine.execute_automated_troubleshooting(issues[0]['guide'])",
            "```",
            "",
            "**Manual Steps:**",
            "1. Check system resources: `make system-status`",
            "2. Identify slow components: `make performance-report`",
            "3. Optimize or restart affected components",
            "",
            "---",
            "",
            "#### SYS-002: Memory Usage Critical",
            "**Description:** System memory usage exceeds safe thresholds",
            "",
            "**Error Example:**",
            "```",
            "MemoryError: Unable to allocate memory for operation",
            "Component: content_processing",
            "Current Usage: 15.2MB (threshold: 10MB)",
            "```",
            "",
            "**Resolution Steps:**",
            "1. **Immediate:** `make clean-cache`",
            "2. **Analysis:** `make memory-profile`",
            "3. **Fix:** `make restart-component COMPONENT=content_processing`",
            "",
            "---",
            "",
            "### Security Errors (SEC-xxx)",
            "",
            "#### SEC-001: Authentication Failed",
            "**Description:** API authentication or authorization failure",
            "",
            "**Error Example:**",
            "```json",
            "{",
            '  "error": "SEC-001",',
            '  "message": "Invalid API key",',
            '  "timestamp": "2024-01-15T10:30:00Z",',
            '  "request_id": "req_12345"',
            "}",
            "```",
            "",
            "**Resolution:**",
            "- Verify API key validity",
            "- Check token expiration",
            "- Review authentication configuration",
            "",
            "#### SEC-002: Security Violation Detected",
            "**Description:** Security validation failure or suspicious activity",
            "",
            "**Automated Response:**",
            "- Component isolation",
            "- Access logging",
            "- Alert notifications",
            "",
            "---",
            "",
            "### Network Errors (NET-xxx)",
            "",
            "#### NET-001: Connection Timeout",
            "**Description:** Network connection timeout to external services",
            "",
            "**Error Example:**",
            "```",
            "ConnectionTimeout: Failed to connect to anthropic.com",
            "Timeout: 30 seconds",
            "Component: claude_status_check",
            "```",
            "",
            "**Troubleshooting:**",
            "1. **Network Test:** `ping anthropic.com`",
            "2. **Firewall Check:** `sudo ufw status`",
            "3. **Service Restart:** `make restart-network-services`",
            "",
            "#### NET-002: API Rate Limited",
            "**Description:** External API rate limiting encountered",
            "",
            "**Resolution:**",
            "- Implement exponential backoff",
            "- Check rate limit headers",
            "- Consider request queuing",
            "",
            "---",
            "",
            "### Database Errors (DB-xxx)",
            "",
            "#### DB-001: Connection Pool Exhausted",
            "**Description:** Database connection pool has reached maximum capacity",
            "",
            "**Error Example:**",
            "```",
            "PoolTimeoutError: Timeout waiting for connection from pool",
            "Pool size: 20",
            "Overflow: 30",
            "Wait time: 30s",
            "```",
            "",
            "**Resolution:**",
            "1. **Immediate:** Increase pool size temporarily",
            "2. **Analysis:** Identify long-running queries",
            "3. **Fix:** Optimize queries or increase pool permanently",
            "",
            "#### DB-002: Query Timeout",
            "**Description:** Database query execution timeout",
            "",
            "**Optimization:**",
            "```sql",
            "-- Add missing indexes",
            "CREATE INDEX CONCURRENTLY idx_sessions_activity ON sessions(last_activity);",
            "",
            "-- Analyze query performance",
            "EXPLAIN ANALYZE SELECT * FROM sessions WHERE last_activity > NOW() - INTERVAL '1 hour';",
            "```",
            "",
            "---",
            "",
            "### Application Errors (APP-xxx)",
            "",
            "#### APP-001: Configuration Invalid",
            "**Description:** Application configuration validation failure",
            "",
            "**Error Example:**",
            "```yaml",
            "# Invalid configuration",
            "server:",
            "  port: \"invalid_port\"  # Should be integer",
            "  workers: -1           # Should be positive",
            "```",
            "",
            "**Resolution:**",
            "1. **Validate:** `make config-validate`",
            "2. **Fix:** Correct configuration values",
            "3. **Test:** `make config-test`",
            "",
            "#### APP-002: Session Creation Failed",
            "**Description:** Unable to create new session",
            "",
            "**Common Causes:**",
            "- Resource constraints",
            "- Invalid session configuration",
            "- File system permissions",
            "",
            "**Automated Fix Available:** Yes",
            "",
            "---",
            "",
            "### Testing Errors (TEST-xxx)",
            "",
            "#### TEST-001: Test Suite Timeout",
            "**Description:** Test execution exceeded timeout limits",
            "",
            "**Resolution:**",
            "```bash",
            "# Increase test timeout",
            "export TEST_TIMEOUT=300  # 5 minutes",
            "",
            "# Run with verbose output",
            "make test-verbose",
            "",
            "# Run specific failing test",
            "make test-single TEST=test_slow_operation",
            "```",
            "",
            "#### TEST-002: Mock Service Unavailable",
            "**Description:** Test mock service connection failed",
            "",
            "**Resolution:**",
            "1. **Restart mocks:** `make test-mocks-restart`",
            "2. **Check ports:** `netstat -tlnp | grep :9999`",
            "3. **Reset test environment:** `make test-env-reset`",
            "",
            "---",
            "",
            "## Error Response Format",
            "",
            "### Standard Error Response",
            "```json",
            "{",
            '  "error": {',
            '    "code": "SYS-001",',
            '    "message": "High response time detected",',
            '    "details": "Average response time: 250ms (threshold: 100ms)",',
            '    "component": "content_processing",',
            '    "timestamp": "2024-01-15T10:30:00Z",',
            '    "request_id": "req_12345",',
            '    "suggestions": [',
            '      "Check system resources",',
            '      "Run automated troubleshooting",',
            '      "Contact support if issue persists"',
            '    ],',
            '    "documentation": "/docs/troubleshooting#sys-001",',
            '    "auto_fix_available": true',
            '  }',
            "}",
            "```",
            "",
            "### Error Context Enhancement",
            "```json",
            "{",
            '  "error": {',
            '    "code": "DB-001",',
            '    "context": {',
            '      "system_health": 75,',
            '      "active_connections": 18,',
            '      "pool_utilization": 90,',
            '      "recent_similar_errors": 3',
            '    },',
            '    "related_alerts": [',
            '      "High database load detected",',
            '      "Connection pool near capacity"',
            '    ]',
            '  }',
            "}",
            "```",
            "",
            "## Error Handling Best Practices",
            "",
            "### Client-Side Error Handling",
            "```javascript",
            "// JavaScript example",
            "async function handleApiCall() {",
            "  try {",
            "    const response = await fetch('/api/sessions');",
            "    if (!response.ok) {",
            "      const error = await response.json();",
            "      handleError(error);",
            "      return;",
            "    }",
            "    const data = await response.json();",
            "    return data;",
            "  } catch (error) {",
            "    handleNetworkError(error);",
            "  }",
            "}",
            "",
            "function handleError(error) {",
            "  switch(error.error.code) {",
            "    case 'SYS-001':",
            "      showPerformanceWarning();",
            "      break;",
            "    case 'SEC-001':",
            "      redirectToLogin();",
            "      break;",
            "    default:",
            "      showGenericError(error);",
            "  }",
            "}",
            "```",
            "",
            "### Python Error Handling",
            "```python",
            "from libs.errors import ContextualErrorHandler",
            "",
            "async def handle_request():",
            "    error_handler = ContextualErrorHandler()",
            "    ",
            "    try:",
            "        # Process request",
            "        result = await process_request()",
            "        return result",
            "    except Exception as e:",
            "        # Convert to user-friendly error",
            "        friendly_error = await error_handler.handle_error(e)",
            "        ",
            "        # Log for monitoring",
            "        logger.error(f'Request failed: {friendly_error.error_code}', extra={",
            "            'user_message': friendly_error.user_message,",
            "            'technical_details': friendly_error.technical_details",
            "        })",
            "        ",
            "        # Return structured error response",
            "        return create_error_response(friendly_error)",
            "```",
            "",
            "## Monitoring and Alerting",
            "",
            "### Error Rate Monitoring",
            "```bash",
            "# Set up error rate alerts",
            "make alerts-configure ERROR_RATE_THRESHOLD=0.01",
            "",
            "# Monitor error patterns",
            "make error-analysis",
            "",
            "# Generate error report",
            "make error-report PERIOD=24h",
            "```",
            "",
            "### Error Dashboards",
            "- **Real-time Error Feed**: Latest errors and their status",
            "- **Error Rate Trends**: Historical error rate analysis",
            "- **Component Error Breakdown**: Errors by component",
            "- **Resolution Time Tracking**: Time to resolve different error types",
            "",
            "## Emergency Response Procedures",
            "",
            "### Critical Error Response",
            "1. **Immediate Assessment**: `make system-health-check`",
            "2. **Error Isolation**: Identify affected components",
            "3. **Service Degradation**: Implement graceful degradation",
            "4. **Communication**: Update status page and notifications",
            "5. **Resolution**: Apply fixes and monitor recovery",
            "6. **Post-mortem**: Document and improve processes",
            "",
            "### Error Recovery Automation",
            "```python",
            "# Automated error recovery",
            "from libs.troubleshooting import IntelligentTroubleshootingEngine",
            "",
            "async def automated_error_recovery():",
            "    engine = IntelligentTroubleshootingEngine()",
            "    ",
            "    # Diagnose all current issues",
            "    issues = await engine.diagnose_current_issues()",
            "    ",
            "    # Execute automated fixes for safe operations",
            "    for issue in issues:",
            "        if issue['safety_assessment']['overall_safety'] == 'safe':",
            "            await engine.execute_automated_troubleshooting(issue['guide'])",
            "```",
            "",
            "---",
            "",
            f"*Error documentation updated: {current_time}*  ",
            f"*For error-specific support: Include error code in GitHub issue title*"
        ])
        
        return "\n".join(doc_content)
    
    async def _generate_testing_documentation(self) -> str:
        """Generate testing guide with current metrics."""
        current_time = time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        try:
            test_summary = self.monitoring.get_test_performance_summary()
        except Exception:
            test_summary = {}
        
        doc_content = [
            "# Testing Guide & Metrics",
            "",
            "Comprehensive testing guide with live test performance metrics and",
            "quality assurance procedures.",
            "",
            f"*Generated on: {current_time}*",
            "",
            "## Test Performance Overview",
            "",
        ]
        
        if test_summary:
            doc_content.extend([
                "### Current Test Suite Performance",
                "",
                "| Test Suite | Runs | Success Rate | Avg Duration | Status |",
                "|------------|------|--------------|--------------|--------|"
            ])
            
            for test_name, metrics in test_summary.items():
                success_rate = metrics['success_rate'] * 100
                avg_duration = metrics['avg_duration_ms']
                status = '🟢 Good' if success_rate > 95 and avg_duration < 5000 else \
                        '🟡 Warning' if success_rate > 90 and avg_duration < 10000 else '🔴 Issues'
                
                doc_content.append(
                    f"| {test_name} | {metrics['total_runs']} | "
                    f"{success_rate:.1f}% | {avg_duration:.0f}ms | {status} |"
                )
            
            doc_content.extend(["", ""])
        else:
            doc_content.extend([
                "⚠️ No test performance data available. Run tests to generate metrics.",
                "",
            ])
        
        doc_content.extend([
            "## Testing Strategy",
            "",
            "### Test Pyramid Structure",
            "",
            "```",
            "    /\\",
            "   /  \\     E2E Tests (10%)",
            "  /____\\    - Full system integration",
            " /      \\   - User journey validation",
            "/________\\  ",
            "\\        /  Integration Tests (30%)",
            " \\______/   - Component interactions",
            "  \\    /    - API endpoint testing",
            "   \\__/     ",
            "   ____     Unit Tests (60%)",
            "  |____|    - Individual function testing",
            "            - Fast feedback loops",
            "```",
            "",
            "### Test Categories",
            "",
            "#### 1. Unit Tests",
            "**Purpose:** Test individual functions and methods in isolation",
            "",
            "**Location:** `tests/unit/`",
            "",
            "**Examples:**",
            "```python",
            "# tests/unit/core/test_session_manager.py",
            "def test_session_creation():",
            "    manager = SessionManager()",
            "    session = manager.create_session('test-session')",
            "    assert session.name == 'test-session'",
            "    assert session.status == 'active'",
            "```",
            "",
            "**Running:**",
            "```bash",
            "# Run all unit tests",
            "make test-unit",
            "",
            "# Run specific test file",
            "make test-unit FILE=tests/unit/core/test_session_manager.py",
            "",
            "# Run with coverage",
            "make test-unit-coverage",
            "```",
            "",
            "#### 2. Integration Tests",
            "**Purpose:** Test component interactions and API endpoints",
            "",
            "**Location:** `tests/integration/`",
            "",
            "**Examples:**",
            "```python",
            "# tests/integration/test_api_integration.py",
            "@pytest.mark.asyncio",
            "async def test_session_api_workflow():",
            "    async with AsyncClient(app=app, base_url='http://test') as client:",
            "        # Create session",
            "        response = await client.post('/api/sessions', json={",
            "            'name': 'integration-test'",
            "        })",
            "        assert response.status_code == 201",
            "        ",
            "        # Verify session exists",
            "        session_id = response.json()['id']",
            "        response = await client.get(f'/api/sessions/{session_id}')",
            "        assert response.status_code == 200",
            "```",
            "",
            "#### 3. End-to-End (E2E) Tests",
            "**Purpose:** Test complete user workflows",
            "",
            "**Location:** `tests/e2e/`",
            "",
            "**Examples:**",
            "```python",
            "# tests/e2e/test_dashboard_workflow.py",
            "def test_complete_dashboard_workflow(page):",
            "    # Navigate to dashboard",
            "    page.goto('http://localhost:1420')",
            "    ",
            "    # Create new session",
            "    page.click('[data-testid=\"create-session-button\"]')",
            "    page.fill('[data-testid=\"session-name\"]', 'e2e-test')",
            "    page.click('[data-testid=\"confirm-create\"]')",
            "    ",
            "    # Verify session appears in list",
            "    expect(page.locator('[data-testid=\"session-e2e-test\"]')).to_be_visible()",
            "```",
            "",
            "## Test Execution",
            "",
            "### Local Testing",
            "```bash",
            "# Run all tests",
            "make test",
            "",
            "# Run tests with coverage report",
            "make test-coverage",
            "",
            "# Run tests in watch mode (during development)",
            "make test-watch",
            "",
            "# Run performance tests",
            "make test-performance",
            "",
            "# Run security tests",
            "make test-security",
            "```",
            "",
            "### Continuous Integration",
            "```yaml",
            "# .github/workflows/test.yml",
            "name: Test Suite",
            "",
            "on: [push, pull_request]",
            "",
            "jobs:",
            "  test:",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - uses: actions/checkout@v3",
            "      - uses: actions/setup-python@v4",
            "        with:",
            "          python-version: '3.9'",
            "      - name: Install dependencies",
            "        run: |",
            "          curl -LsSf https://astral.sh/uv/install.sh | sh",
            "          uv sync",
            "      - name: Run tests",
            "        run: make test-ci",
            "      - name: Upload coverage",
            "        uses: codecov/codecov-action@v3",
            "```",
            "",
            "## Test Data Management",
            "",
            "### Fixtures and Factories",
            "```python",
            "# tests/fixtures/test_helpers.py",
            "from dataclasses import dataclass",
            "import pytest",
            "",
            "@dataclass",
            "class TestSession:",
            "    name: str",
            "    config: dict",
            "    status: str = 'active'",
            "",
            "@pytest.fixture",
            "def sample_session():",
            "    return TestSession(",
            "        name='test-session',",
            "        config={'auto_response': True}",
            "    )",
            "",
            "@pytest.fixture",
            "async def test_database():",
            "    # Setup test database",
            "    db = await create_test_database()",
            "    yield db",
            "    # Cleanup",
            "    await db.cleanup()",
            "```",
            "",
            "### Mock Services",
            "```python",
            "# tests/fixtures/mock_factories.py",
            "class MockClaudeAPI:",
            "    def __init__(self):",
            "        self.responses = {}",
            "        self.call_count = 0",
            "    ",
            "    def mock_response(self, endpoint: str, response: dict):",
            "        self.responses[endpoint] = response",
            "    ",
            "    async def request(self, endpoint: str, data: dict):",
            "        self.call_count += 1",
            "        return self.responses.get(endpoint, {'error': 'Not mocked'})",
            "",
            "@pytest.fixture",
            "def mock_claude_api():",
            "    api = MockClaudeAPI()",
            "    api.mock_response('/chat', {",
            "        'message': 'Mocked Claude response',",
            "        'status': 'success'",
            "    })",
            "    return api",
            "```",
            "",
            "## Quality Gates",
            "",
            "### Code Coverage Requirements",
            "```bash",
            "# Minimum coverage thresholds",
            "COVERAGE_UNIT_MIN=90%",
            "COVERAGE_INTEGRATION_MIN=80%",
            "COVERAGE_OVERALL_MIN=85%",
            "",
            "# Check coverage",
            "make coverage-report",
            "make coverage-check",
            "```",
            "",
            "### Performance Benchmarks",
            "```python",
            "# tests/performance/test_benchmarks.py",
            "@pytest.mark.benchmark",
            "def test_session_creation_performance(benchmark):",
            "    def create_session():",
            "        manager = SessionManager()",
            "        return manager.create_session('perf-test')",
            "    ",
            "    result = benchmark(create_session)",
            "    ",
            "    # Performance assertions",
            "    assert benchmark.stats.mean < 0.1  # < 100ms average",
            "    assert benchmark.stats.max < 0.2   # < 200ms maximum",
            "```",
            "",
            "### Security Testing",
            "```python",
            "# tests/security/test_security_validation.py",
            "@pytest.mark.security",
            "async def test_api_authentication():",
            "    async with AsyncClient(app=app) as client:",
            "        # Test without API key",
            "        response = await client.get('/api/sessions')",
            "        assert response.status_code == 401",
            "        ",
            "        # Test with invalid API key",
            "        headers = {'X-API-Key': 'invalid-key'}",
            "        response = await client.get('/api/sessions', headers=headers)",
            "        assert response.status_code == 401",
            "        ",
            "        # Test with valid API key",
            "        headers = {'X-API-Key': 'valid-test-key'}",
            "        response = await client.get('/api/sessions', headers=headers)",
            "        assert response.status_code == 200",
            "```",
            "",
            "## Test Environment Setup",
            "",
            "### Development Environment",
            "```bash",
            "# Setup test environment",
            "make test-env-setup",
            "",
            "# Start test services (database, redis, etc.)",
            "make test-services-start",
            "",
            "# Reset test data",
            "make test-data-reset",
            "",
            "# Cleanup test environment",
            "make test-env-cleanup",
            "```",
            "",
            "### Docker Test Environment",
            "```yaml",
            "# docker-compose.test.yml",
            "version: '3.8'",
            "",
            "services:",
            "  test-app:",
            "    build: .",
            "    environment:",
            "      - YESMAN_CONFIG=test",
            "    depends_on:",
            "      - test-db",
            "      - test-redis",
            "    volumes:",
            "      - ./tests:/app/tests",
            "",
            "  test-db:",
            "    image: postgres:13",
            "    environment:",
            "      POSTGRES_DB: yesman_test",
            "      POSTGRES_USER: test",
            "      POSTGRES_PASSWORD: test",
            "",
            "  test-redis:",
            "    image: redis:6-alpine",
            "```",
            "",
            "## Debugging Tests",
            "",
            "### Debug Mode",
            "```bash",
            "# Run tests with debug output",
            "make test-debug",
            "",
            "# Run specific test with pdb",
            "python -m pytest tests/unit/test_specific.py::test_function -s --pdb",
            "",
            "# Run tests with verbose logging",
            "PYTEST_LOG_LEVEL=DEBUG make test",
            "```",
            "",
            "### Test Isolation",
            "```python",
            "# Ensure test isolation",
            "@pytest.fixture(autouse=True)",
            "async def isolate_test():",
            "    # Setup",
            "    await reset_global_state()",
            "    yield",
            "    # Teardown",
            "    await cleanup_global_state()",
            "```",
            "",
            "## Test Reporting",
            "",
            "### JUnit XML Reports",
            "```bash",
            "# Generate JUnit XML reports",
            "make test-junit",
            "",
            "# View reports",
            "open test-reports/junit.xml",
            "```",
            "",
            "### HTML Coverage Reports",
            "```bash",
            "# Generate HTML coverage report",
            "make coverage-html",
            "",
            "# Open in browser",
            "open htmlcov/index.html",
            "```",
            "",
            "### Performance Reports",
            "```bash",
            "# Generate performance benchmark report",
            "make benchmark-report",
            "",
            "# Compare with baseline",
            "make benchmark-compare BASELINE=v1.0.0",
            "```",
            "",
            "## Best Practices",
            "",
            "### Test Organization",
            "1. **Follow AAA Pattern**: Arrange, Act, Assert",
            "2. **One Assertion Per Test**: Focus on single behavior",
            "3. **Descriptive Names**: Test names should explain what is being tested",
            "4. **Test Independence**: Tests should not depend on each other",
            "",
            "### Test Data",
            "1. **Use Factories**: Generate test data programmatically",
            "2. **Avoid Hard-Coded Values**: Use variables and constants",
            "3. **Clean Up**: Always clean up test data after tests",
            "",
            "### Performance Considerations",
            "1. **Parallel Execution**: Run independent tests in parallel",
            "2. **Mock External Services**: Don't rely on external APIs",
            "3. **Database Transactions**: Use database rollbacks for cleanup",
            "",
            "### Security Testing",
            "1. **Test All Auth Paths**: Valid and invalid authentication",
            "2. **Input Validation**: Test with malicious input",
            "3. **Permission Checks**: Verify authorization controls",
            "",
            "---",
            "",
            f"*Testing guide updated: {current_time}*  ",
            f"*Test metrics refresh: Every test run*  ",
            f"*For testing issues: Create GitHub issue with 'testing' label*"
        ])
        
        return "\n".join(doc_content)
    
    async def _generate_documentation_index(self, docs: Dict[str, str]) -> None:
        """Generate master documentation index."""
        current_time = time.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        index_content = [
            "# Generated Documentation Index",
            "",
            f"*Auto-generated on: {current_time}*",
            "",
            "This directory contains automatically generated documentation with live system data.",
            "Documentation is refreshed automatically to stay current with system changes.",
            "",
            "## Available Documentation",
            "",
        ]
        
        # Add links to all generated documents
        for doc_name in sorted(docs.keys()):
            if doc_name == 'error':
                continue
                
            title = doc_name.replace('_', ' ').title()
            index_content.extend([
                f"### [{title}]({doc_name}.md)",
                f"- **File:** `{doc_name}.md`",
                f"- **Purpose:** {self._get_doc_purpose(doc_name)}",
                f"- **Update Frequency:** {self._get_update_frequency(doc_name)}",
                ""
            ])
        
        index_content.extend([
            "## Documentation Features",
            "",
            "- **📊 Live Metrics**: Real-time system performance data",
            "- **🎯 Context-Aware**: Current system state and health information",
            "- **🔧 Actionable**: Direct links to troubleshooting tools",
            "- **📈 Performance Data**: Historical trends and optimization recommendations",
            "- **🚨 Alert Integration**: Current alerts and system issues",
            "",
            "## How to Use",
            "",
            "1. **Start with Component Guide**: Understand system architecture and performance",
            "2. **Check Troubleshooting Guide**: For current issues and automated fixes",
            "3. **Reference API Documentation**: For integration and development",
            "4. **Follow Performance Guide**: For optimization recommendations",
            "5. **Use Error Reference**: For specific error resolution",
            "",
            "## Automatic Updates",
            "",
            "This documentation is automatically updated when:",
            "- System metrics change significantly",
            "- New alerts are triggered",
            "- Performance thresholds are exceeded",
            "- Manual refresh is requested",
            "",
            "## Manual Refresh",
            "",
            "```bash",
            "# Regenerate all documentation",
            "python scripts/documentation_generator.py",
            "",
            "# Generate specific document",
            "python scripts/documentation_generator.py --doc=component_guide",
            "",
            "# Schedule automatic updates",
            "make docs-schedule-updates",
            "```",
            "",
            "---",
            "",
            f"*Index generated: {current_time}*  ",
            "*Next update: Automated based on system changes*"
        ])
        
        index_path = self.docs_dir / "README.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(index_content))
    
    def _get_doc_purpose(self, doc_name: str) -> str:
        """Get the purpose description for a document."""
        purposes = {
            'api_reference': 'Comprehensive API documentation with live examples',
            'component_guide': 'Component performance analysis and optimization',
            'troubleshooting_guide': 'Step-by-step issue resolution with automation',
            'performance_guide': 'Performance optimization recommendations and metrics',
            'deployment_guide': 'Deployment procedures and configuration examples',
            'error_reference': 'Error codes, causes, and resolution steps',
            'testing_guide': 'Testing procedures and quality metrics'
        }
        return purposes.get(doc_name, 'System documentation and guidance')
    
    def _get_update_frequency(self, doc_name: str) -> str:
        """Get the update frequency for a document."""
        frequencies = {
            'api_reference': 'Every 30 minutes',
            'component_guide': 'Every 15 minutes',
            'troubleshooting_guide': 'When alerts change',
            'performance_guide': 'Every hour',
            'deployment_guide': 'On configuration changes',
            'error_reference': 'Daily or when new errors detected',
            'testing_guide': 'After test runs'
        }
        return frequencies.get(doc_name, 'Daily')


async def main():
    """Main function to generate documentation."""
    generator = LiveDocumentationGenerator()
    
    print("🚀 Starting Live Documentation Generation...")
    print("=" * 60)
    
    try:
        docs = await generator.generate_comprehensive_documentation()
        
        if 'error' in docs:
            print(f"❌ Error: {docs['error']}")
            return 1
        
        print("=" * 60)
        print(f"✅ Successfully generated {len(docs)} documentation files!")
        print(f"📁 Location: {generator.docs_dir}")
        print("🌐 View generated docs in your browser or editor")
        
        return 0
        
    except Exception as e:
        print(f"💥 Fatal error during documentation generation: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))