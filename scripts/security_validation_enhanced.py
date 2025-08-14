#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Enhanced Security validation script with performance metrics integration.

This script extends the security validation with timing instrumentation
and event bus integration for real-time monitoring.
"""

import ast
import asyncio
import re
import sys
import time
from pathlib import Path

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from libs.dashboard.security_metrics_integration import (
    SecurityMetrics,
)


class EnhancedSecurityValidator:
    """Enhanced security validation with metrics collection."""

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.event_bus = get_event_bus()

        # Metrics tracking
        self.scan_start_time = 0
        self.scan_end_time = 0
        self.files_scanned = 0
        self.total_files = 0
        self.violation_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        self.false_positives = 0

        # Security patterns to detect (inherited from original)
        self.dangerous_patterns = {
            "hardcoded_secrets": [
                r'(?i)(password|secret|key|token)\s*=\s*["\'][^"\']{8,}["\']',
                r'(?i)api[_-]?key\s*=\s*["\'][^"\']+["\']',
                r'(?i)secret[_-]?key\s*=\s*["\'][^"\']+["\']',
            ],
            "sql_injection_risk": [
                r'\.execute\s*\(\s*["\'].*%.*["\']',
                r'\.execute\s*\(\s*f["\'].*\{.*\}.*["\']',
                r"cursor\.execute.*%",
            ],
            "path_traversal_risk": [
                r"open\s*\(\s*.*\+.*\)",
                r"os\.path\.join\s*\(.*\+",
                r'["\']\.\.\/["\']',
                r'["\']\.\.\\\\["\']',
            ],
            "command_injection_risk": [
                r"subprocess\.(run|call|check_output).*shell\s*=\s*True",
                r"os\.system\s*\(",
                r"os\.popen\s*\(",
            ],
            "eval_usage": [
                r"\beval\s*\(",
                r"\bexec\s*\(",
            ],
            "weak_crypto": [
                r"hashlib\.md5\(",
                r"hashlib\.sha1\(",
                r"random\.random\(\)",
                r"random\.randint\(",
            ],
            "authentication_issues": [
                r"verify\s*=\s*False",
                r"SSL_VERIFY\s*=\s*False",
                r"check_hostname\s*=\s*False",
            ],
            "authorization_issues": [
                r"@app\.route.*methods\s*=\s*\[.*\].*\)",  # Missing auth decorators
                r"def\s+admin_.*\(.*\):",  # Admin functions without auth check
            ],
            "encryption_weaknesses": [
                r"AES\.MODE_ECB",
                r"DES\.",
                r"RC4\.",
            ],
        }

        # Pattern severity mapping
        self.pattern_severity = {
            "hardcoded_secrets": "critical",
            "sql_injection_risk": "high",
            "path_traversal_risk": "high",
            "command_injection_risk": "critical",
            "eval_usage": "high",
            "weak_crypto": "medium",
            "authentication_issues": "high",
            "authorization_issues": "high",
            "encryption_weaknesses": "medium",
        }

        # False positive detection patterns
        self.false_positive_patterns = [
            r"test_",
            r"_test\.py$",
            r"example",
            r"sample",
            r"demo",
            r"mock",
        ]

    async def validate_file_with_timing(self, file_path: Path) -> tuple[bool, float]:
        """Validate a single Python file with timing instrumentation.

        Args:
            file_path: Path to the file to validate

        Returns:
            Tuple of (success, scan_time_ms)
        """
        if not file_path.suffix == ".py":
            return True, 0

        start_time = time.time()

        try:
            content = file_path.read_text(encoding="utf-8")

            # Pattern-based checks
            await self._check_security_patterns_async(file_path, content)

            # AST-based checks for more complex patterns
            try:
                tree = ast.parse(content)
                await self._check_ast_security_async(file_path, tree)
            except SyntaxError:
                # Skip files with syntax errors (will be caught by other tools)
                pass

            scan_time_ms = (time.time() - start_time) * 1000
            self.files_scanned += 1

            return len(self.errors) == 0, scan_time_ms

        except Exception as e:
            self.warnings.append(f"Could not analyze {file_path}: {e}")
            scan_time_ms = (time.time() - start_time) * 1000
            return True, scan_time_ms

    async def _check_security_patterns_async(self, file_path: Path, content: str) -> None:
        """Check for dangerous security patterns using regex (async version).

        Args:
            file_path: Path to the file being checked
            content: File content
        """
        lines = content.split("\n")

        for category, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith("#"):
                        continue

                    if re.search(pattern, line):
                        # Check for false positives
                        is_false_positive = self._is_false_positive(file_path, line)

                        if is_false_positive:
                            self.false_positives += 1
                        else:
                            severity = self.pattern_severity.get(category, "low")
                            await self._add_security_issue_async(file_path, line_num, category, severity, f"Potential security issue: {pattern}")

    async def _check_ast_security_async(self, file_path: Path, tree: ast.AST) -> None:
        """Check for security issues using AST analysis (async version).

        Args:
            file_path: Path to the file being checked
            tree: AST tree
        """
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                await self._check_dangerous_calls_async(file_path, node)

            # Check for dangerous imports
            elif isinstance(node, ast.Import):
                await self._check_dangerous_imports_async(file_path, node)

            # Check for dangerous string operations
            elif isinstance(node, ast.BinOp):
                await self._check_string_operations_async(file_path, node)

    async def _check_dangerous_calls_async(self, file_path: Path, node: ast.Call) -> None:
        """Check for dangerous function calls (async version).

        Args:
            file_path: Path to the file being checked
            node: AST Call node
        """
        func_name = self._get_function_name(node.func)

        dangerous_calls = {
            "eval": "critical",
            "exec": "critical",
            "compile": "high",
            "__import__": "high",
            "os.system": "critical",
            "os.popen": "critical",
            "subprocess.call": "high",
        }

        if func_name in dangerous_calls:
            severity = dangerous_calls[func_name]
            await self._add_security_issue_async(file_path, node.lineno, "dangerous_function", severity, f"Dangerous function call: {func_name}")

    async def _check_dangerous_imports_async(self, file_path: Path, node: ast.Import) -> None:
        """Check for potentially dangerous imports (async version).

        Args:
            file_path: Path to the file being checked
            node: AST Import node
        """
        dangerous_imports = {
            "pickle": "medium",
            "dill": "medium",
            "marshal": "medium",
            "telnetlib": "high",
            "ftplib": "medium",
        }

        for alias in node.names:
            if alias.name in dangerous_imports:
                severity = dangerous_imports[alias.name]
                self.warnings.append(f"{file_path}:{node.lineno}: Warning ({severity}): Potentially unsafe import: {alias.name}")
                self.violation_counts[severity] += 1

    async def _check_string_operations_async(self, file_path: Path, node: ast.BinOp) -> None:
        """Check for dangerous string operations (async version).

        Args:
            file_path: Path to the file being checked
            node: AST BinOp node
        """
        if isinstance(node.op, ast.Mod) and hasattr(node.left, "s"):
            # Check for SQL-like string formatting
            if any(keyword in node.left.s.lower() for keyword in ["select", "insert", "update", "delete"]):
                self.warnings.append(f"{file_path}:{node.lineno}: Warning (high): Potential SQL injection risk in string formatting")
                self.violation_counts["high"] += 1

    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from AST node.

        Args:
            node: AST node

        Returns:
            Function name as string
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_function_name(node.value)}.{node.attr}"
        return ""

    def _is_false_positive(self, file_path: Path, line: str) -> bool:
        """Check if a detected issue is likely a false positive.

        Args:
            file_path: Path to the file
            line: Line content

        Returns:
            True if likely false positive
        """
        file_str = str(file_path)

        for pattern in self.false_positive_patterns:
            if re.search(pattern, file_str, re.IGNORECASE):
                return True
            if re.search(pattern, line, re.IGNORECASE):
                return True

        return False

    async def _add_security_issue_async(
        self,
        file_path: Path,
        line_num: int,
        category: str,
        severity: str,
        message: str,
    ) -> None:
        """Add a security issue to the error list (async version).

        Args:
            file_path: Path to the file
            line_num: Line number
            category: Issue category
            severity: Issue severity
            message: Issue message
        """
        issue = f"{file_path}:{line_num}: {severity.upper()}: {category} - {message}"

        if severity in {"critical", "high"}:
            self.errors.append(issue)
        else:
            self.warnings.append(issue)

        self.violation_counts[severity] += 1

        # Publish violation event
        await self._publish_violation_event(file_path, line_num, category, severity, message)

    async def _publish_violation_event(
        self,
        file_path: Path,
        line_num: int,
        category: str,
        severity: str,
        message: str,
    ) -> None:
        """Publish security violation event to event bus.

        Args:
            file_path: Path to the file
            line_num: Line number
            category: Issue category
            severity: Issue severity
            message: Issue message
        """

        event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "security",
                "security_event_type": "violation_detected",
                "component": str(file_path.relative_to(self.project_root)),
                "severity": severity,
                "violation_type": category,
                "description": message,
                "line_number": line_num,
                "remediation": self._get_remediation_advice(category),
            },
            timestamp=time.time(),
            source="security_validation",
            priority=EventPriority.HIGH if severity in {"critical", "high"} else EventPriority.NORMAL,
        )

        await self.event_bus.publish(event)

    def _get_remediation_advice(self, category: str) -> str:
        """Get remediation advice for a security issue category.

        Args:
            category: Issue category

        Returns:
            Remediation advice
        """
        remediation_map = {
            "hardcoded_secrets": "Use environment variables or secure key management systems",
            "sql_injection_risk": "Use parameterized queries or ORM with proper escaping",
            "path_traversal_risk": "Validate and sanitize file paths, use safe path operations",
            "command_injection_risk": "Avoid shell=True, use subprocess with list arguments",
            "eval_usage": "Replace eval/exec with safe alternatives like ast.literal_eval",
            "weak_crypto": "Use strong cryptographic algorithms (SHA256+, AES-256)",
            "authentication_issues": "Enable SSL/TLS verification and proper authentication",
            "authorization_issues": "Implement proper authorization checks and access controls",
            "encryption_weaknesses": "Use secure encryption modes (AES-GCM, AES-CBC with HMAC)",
        }

        return remediation_map.get(category, "Review security best practices for this issue")

    async def validate_configuration_async(self) -> bool:
        """Validate security-related configuration files (async version).

        Returns:
            True if validation passed
        """
        config_checks = await asyncio.gather(
            self._check_env_files_async(),
            self._check_requirements_security_async(),
            self._check_config_security_async(),
        )

        return all(config_checks)

    async def _check_env_files_async(self) -> bool:
        """Check for exposed secrets in environment files (async version).

        Returns:
            True if check passed
        """
        env_files = list(self.project_root.glob("**/.env*"))

        for env_file in env_files:
            if env_file.name == ".env.example":
                continue

            try:
                content = env_file.read_text()
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    if "=" in line and not line.strip().startswith("#"):
                        key, value = line.split("=", 1)
                        if len(value) > 20 and not value.startswith("$"):
                            self.warnings.append(f"{env_file}:{line_num}: Warning (medium): Potentially exposed secret: {key}")
                            self.violation_counts["medium"] += 1
            except Exception:
                continue

        return True

    async def _check_requirements_security_async(self) -> bool:
        """Check for known vulnerable packages in requirements (async version).

        Returns:
            True if check passed
        """
        req_files = list(self.project_root.glob("**/requirements*.txt"))
        req_files.extend(list(self.project_root.glob("**/pyproject.toml")))

        # Known vulnerable package patterns
        vulnerable_patterns = [
            (r"django\s*==?\s*[12]\.", "Django < 3.0"),
            (r"flask\s*==?\s*0\.", "Flask < 1.0"),
            (r"requests\s*==?\s*2\.[0-9]\.", "Requests < 2.20"),
            (r"pyyaml\s*==?\s*[34]\.", "PyYAML < 5.0"),
            (r"jinja2\s*==?\s*2\.[0-9]\.", "Jinja2 < 2.10"),
        ]

        for req_file in req_files:
            try:
                content = req_file.read_text()

                for pattern, package_desc in vulnerable_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.warnings.append(f"{req_file}: Warning (high): Vulnerable dependency: {package_desc}")
                        self.violation_counts["high"] += 1
            except Exception:
                continue

        return True

    async def _check_config_security_async(self) -> bool:
        """Check security configuration in config files (async version).

        Returns:
            True if check passed
        """
        config_files = list(self.project_root.glob("**/config/**/*.yaml"))
        config_files.extend(list(self.project_root.glob("**/config/**/*.yml")))
        config_files.extend(list(self.project_root.glob("**/config/**/*.json")))

        for config_file in config_files:
            try:
                content = config_file.read_text()

                # Check for debug mode in production configs
                if "production" in str(config_file).lower():
                    if re.search(r'debug["\s:=]+true', content.lower()):
                        self.errors.append(f"{config_file}: CRITICAL: Debug mode enabled in production config")
                        self.violation_counts["critical"] += 1

                # Check for insecure protocols
                if re.search(r"http://[^localhost]", content):
                    self.warnings.append(f"{config_file}: Warning (medium): Insecure HTTP protocol in config")
                    self.violation_counts["medium"] += 1

                # Check for weak authentication settings
                if re.search(r'(password|secret)["\s:=]+["\']?(admin|password|123)', content.lower()):
                    self.errors.append(f"{config_file}: HIGH: Weak or default credentials in config")
                    self.violation_counts["high"] += 1
            except Exception:
                continue

        return True

    async def run_validation_async(self) -> bool:
        """Run all security validations with metrics collection (async version).

        Returns:
            True if validation passed
        """
        print("🔒 Running enhanced security validation with metrics...")

        self.scan_start_time = time.time()

        # Collect Python files
        python_files = []
        for pattern in ["libs/**/*.py", "commands/**/*.py", "api/**/*.py", "scripts/**/*.py"]:
            python_files.extend(self.project_root.glob(pattern))

        self.total_files = len(python_files)

        # Validate Python files with timing
        file_scan_times = []
        for py_file in python_files:
            success, scan_time = await self.validate_file_with_timing(py_file)
            file_scan_times.append(scan_time)

        # Validate configuration
        await self.validate_configuration_async()

        self.scan_end_time = time.time()
        total_scan_time_ms = (self.scan_end_time - self.scan_start_time) * 1000

        # Calculate metrics
        total_violations = sum(self.violation_counts.values())
        false_positive_rate = (self.false_positives / max(total_violations, 1)) * 100 if total_violations > 0 else 0
        scan_coverage = (self.files_scanned / max(self.total_files, 1)) * 100

        # Create security metrics
        security_metrics = SecurityMetrics(
            scan_duration_ms=total_scan_time_ms,
            violations_found=total_violations,
            false_positive_rate=false_positive_rate,
            vulnerability_severity_counts=self.violation_counts,
            scan_coverage_percent=scan_coverage,
        )

        # Publish scan completion event
        await self._publish_scan_completed_event(security_metrics)

        # Report results
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} security warnings:")
            for warning in self.warnings[:10]:  # Limit output
                print(f"  {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")

        if self.errors:
            print(f"\n❌ {len(self.errors)} security errors:")
            for error in self.errors:
                print(f"  {error}")

        # Print metrics summary
        print("\n📊 Security Scan Metrics:")
        print(f"  Total scan time: {total_scan_time_ms:.2f}ms")
        print(f"  Files scanned: {self.files_scanned}/{self.total_files}")
        print(f"  Scan coverage: {scan_coverage:.1f}%")
        print(f"  Total violations: {total_violations}")
        print(f"  False positive rate: {false_positive_rate:.1f}%")
        print("  Severity breakdown:")
        for severity, count in self.violation_counts.items():
            if count > 0:
                print(f"    - {severity}: {count}")

        if len(self.errors) == 0:
            print(f"\n✅ Security validation passed ({self.files_scanned} files checked in {total_scan_time_ms:.0f}ms)")
            return True
        else:
            print("\n❌ Security validation failed")
            return False

    async def _publish_scan_completed_event(self, metrics: SecurityMetrics) -> None:
        """Publish scan completion event with metrics.

        Args:
            metrics: Security scan metrics
        """
        event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "security",
                "security_event_type": "scan_completed",
                "component": "security_validation",
                "scan_duration_ms": metrics.scan_duration_ms,
                "violations_found": metrics.violations_found,
                "false_positive_rate": metrics.false_positive_rate,
                "vulnerability_counts": metrics.vulnerability_severity_counts,
                "scan_coverage": metrics.scan_coverage_percent,
            },
            timestamp=time.time(),
            source="security_validation",
            priority=EventPriority.NORMAL,
        )

        await self.event_bus.publish(event)


async def main() -> None:
    """Main entry point for enhanced security validation."""
    validator = EnhancedSecurityValidator()

    try:
        success = await validator.run_validation_async()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Security validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
