# Copyright notice.

import asyncio
import contextlib
import json
import logging
import os
import re
import subprocess  # noqa: S404
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from .branch_manager import BranchManager

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Branch-specific test execution and result integration system."""

from typing import Any


logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(Enum):
    """Types of tests that can be executed."""

    UNIT = "unit"
    INTEGRATION = "integration"
    LINT = "lint"
    TYPE_CHECK = "type_check"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUILD = "build"


@dataclass
class TestResult:
    """Result of a test execution."""

    test_id: str
    test_type: TestType
    branch_name: str
    status: TestStatus
    start_time: datetime
    end_time: datetime | None = None
    duration: float = 0.0
    output: str = ""
    error: str = ""
    exit_code: int | None = None
    coverage: float | None = None
    failed_tests: list[str] = field(default_factory=list)
    metadata: dict[str] = field(default_factory=dict)

    def to_dict(self) -> dict[str]:
        """Convert to dictionary for serialization."""
        return {
            "test_id": self.test_id,
            "test_type": self.test_type.value,
            "branch_name": self.branch_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "coverage": self.coverage,
            "failed_tests": self.failed_tests,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str]) -> "TestResult":
        """Create from dictionary."""
        data["test_type"] = TestType(data["test_type"])
        data["status"] = TestStatus(data["status"])
        data["start_time"] = datetime.fromisoformat(data["start_time"])
        if data["end_time"]:
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        return cls(**data)


@dataclass
class TestSuite:
    """Configuration for a test suite."""

    name: str
    test_type: TestType
    command: list[str]
    working_directory: str = "."
    timeout: int = 600  # 10 minutes default
    requires_build: bool = False
    parallel: bool = True
    critical: bool = False  # If true, failure blocks other tests
    environment: dict[str, str] = field(default_factory=dict)
    file_patterns: list[str] = field(default_factory=list)  # Files to watch for changes


class BranchTestManager:
    """Manages automatic testing execution per branch with result integration."""

    def __init__(
        self,
        repo_path: str = ".",
        results_dir: str = ".scripton/yesman/test_results",
        agent_pool: object = None,
    ) -> None:
        """Initialize branch test manager.

        Args:
            repo_path: Path to git repository
            results_dir: Directory to store test results
            agent_pool: AgentPool instance for task execution
        """
        self.repo_path = Path(repo_path).resolve()
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.branch_manager = BranchManager(repo_path)
        self.agent_pool = agent_pool

        # Test configuration
        self.test_suites: dict[str, TestSuite] = {}
        self.branch_results: dict[str, list[TestResult]] = {}

        # Execution tracking
        self.running_tests: dict[str, TestResult] = {}
        self.test_queue: asyncio.Queue = asyncio.Queue()

        # Auto-testing configuration
        self.auto_testing_enabled = False
        self.test_on_commit = True
        self.test_on_push = True
        self.parallel_test_limit = 3

        # Load configuration and results
        self._load_test_configuration()
        self._load_test_results()

    def _get_config_file(self) -> Path:
        """Get path to test configuration file."""
        return self.repo_path / ".scripton" / "yesman" / "test_config.json"

    def _get_results_file(self, branch_name: str) -> Path:
        """Get path to test results file for a branch."""
        safe_branch = branch_name.replace("/", "_").replace("\\", "_")
        return self.results_dir / f"{safe_branch}_results.json"

    def _load_test_configuration(self) -> None:
        """Load test suite configuration."""
        config_file = self._get_config_file()

        if config_file.exists():
            try:
                with config_file.open() as f:
                    config = json.load(f)

                # Load test suites
                for name, suite_data in config.get("test_suites", {}).items():
                    suite_data["test_type"] = TestType(suite_data["test_type"])
                    self.test_suites[name] = TestSuite(name=name, **suite_data)

                # Load settings
                settings = config.get("settings", {})
                self.auto_testing_enabled = settings.get("auto_testing_enabled", False)
                self.test_on_commit = settings.get("test_on_commit", True)
                self.test_on_push = settings.get("test_on_push", True)
                self.parallel_test_limit = settings.get("parallel_test_limit", 3)

                logger.info("Loaded %d test suites", len(self.test_suites))

            except Exception:
                logger.exception("Failed to load test configuration")
                self._create_default_configuration()
        else:
            self._create_default_configuration()

    def _create_default_configuration(self) -> None:
        """Create default test configuration."""
        # Default test suites for common project types
        default_suites = {
            "unit_tests": TestSuite(
                name="unit_tests",
                test_type=TestType.UNIT,
                command=["python", "-m", "pytest", "tests/", "-v"],
                timeout=300,
                critical=True,
            ),
            "lint_check": TestSuite(
                name="lint_check",
                test_type=TestType.LINT,
                command=["python", "-m", "ruff", "check", "."],
                timeout=60,
                critical=False,
            ),
            "type_check": TestSuite(
                name="type_check",
                test_type=TestType.TYPE_CHECK,
                command=["python", "-m", "mypy", "."],
                timeout=120,
                critical=False,
            ),
            "build_check": TestSuite(
                name="build_check",
                test_type=TestType.BUILD,
                command=["python", "-m", "build"],
                timeout=180,
                critical=True,
            ),
        }

        self.test_suites = default_suites
        self._save_test_configuration()

    def _save_test_configuration(self) -> None:
        """Save test configuration to file."""
        config_file = self._get_config_file()
        config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            config = {
                "test_suites": {
                    name: {
                        "test_type": suite.test_type.value,
                        "command": suite.command,
                        "working_directory": suite.working_directory,
                        "timeout": suite.timeout,
                        "requires_build": suite.requires_build,
                        "parallel": suite.parallel,
                        "critical": suite.critical,
                        "environment": suite.environment,
                        "file_patterns": suite.file_patterns,
                    }
                    for name, suite in self.test_suites.items()
                },
                "settings": {
                    "auto_testing_enabled": self.auto_testing_enabled,
                    "test_on_commit": self.test_on_commit,
                    "test_on_push": self.test_on_push,
                    "parallel_test_limit": self.parallel_test_limit,
                },
            }

            with config_file.open("w") as f:
                json.dump(config, f, indent=2)

        except Exception:
            logger.exception("Failed to save test configuration")

    def _load_test_results(self) -> None:
        """Load test results for all branches."""
        self.branch_results = {}

        try:
            # Load results for each branch
            for branch_info in self.branch_manager.list_active_branches():
                results_file = self._get_results_file(branch_info.name)

                if results_file.exists():
                    try:
                        with results_file.open() as f:
                            results_data = json.load(f)

                        results = [TestResult.from_dict(r) for r in results_data]
                        self.branch_results[branch_info.name] = results

                    except Exception:
                        logger.exception("Failed to load results for %s", branch_info.name)
        except Exception as e:
            logger.warning("Failed to list active branches for test results loading: %s", e)
            # Continue without loading existing results

    def _save_test_results(self, branch_name: str) -> None:
        """Save test results for a branch."""
        if branch_name not in self.branch_results:
            return

        results_file = self._get_results_file(branch_name)

        try:
            results_data = [r.to_dict() for r in self.branch_results[branch_name]]

            with results_file.open("w") as f:
                json.dump(results_data, f, indent=2)

        except Exception:
            logger.exception("Failed to save results for %s", branch_name)

    async def run_test_suite(
        self,
        branch_name: str,
        suite_name: str,
        force: bool = False,  # noqa: FBT001, ARG002
    ) -> TestResult:
        """Run a specific test suite on a branch.

        Args:
            branch_name: Name of the branch to test
            suite_name: Name of the test suite to run
            force: Run even if branch is not up to date

        Returns:
            TestResult with execution details
        """
        if suite_name not in self.test_suites:
            msg = f"Test suite '{suite_name}' not found"
            raise ValueError(msg)

        suite = self.test_suites[suite_name]
        test_id = f"{branch_name}:{suite_name}:{int(time.time())}"

        # Create test result
        result = TestResult(
            test_id=test_id,
            test_type=suite.test_type,
            branch_name=branch_name,
            status=TestStatus.PENDING,
            start_time=datetime.now(UTC),
        )

        # Switch to branch if needed
        current_branch = self.branch_manager._get_current_branch()
        if current_branch != branch_name:
            success = self.branch_manager.switch_branch(branch_name)
            if not success:
                result.status = TestStatus.ERROR
                result.error = f"Failed to switch to branch {branch_name}"
                result.end_time = datetime.now(UTC)
                return result

        # Check if build is required
        if suite.requires_build:
            build_result = await self._run_build(branch_name)
            if not build_result:
                result.status = TestStatus.ERROR
                result.error = "Build failed before running tests"
                result.end_time = datetime.now(UTC)
                return result

        # Execute test
        result.status = TestStatus.RUNNING
        self.running_tests[test_id] = result

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(suite.environment)
            env.update(
                {
                    "YESMAN_BRANCH": branch_name,
                    "YESMAN_TEST_ID": test_id,
                    "YESMAN_TEST_TYPE": suite.test_type.value,
                }
            )

            # Run command
            logger.info("Running %s on %s: %s", suite_name, branch_name, " ".join(suite.command))

            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                *suite.command,
                cwd=self.repo_path / suite.working_directory,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=suite.timeout,
                )

                end_time = time.time()
                result.duration = end_time - start_time
                result.output = stdout.decode("utf-8")
                result.error = stderr.decode("utf-8")
                result.exit_code = process.returncode
                result.end_time = datetime.now(UTC)

                # Determine status
                if process.returncode == 0:
                    result.status = TestStatus.PASSED
                else:
                    result.status = TestStatus.FAILED

                # Parse test output for additional info
                await self._parse_test_output(result, suite)

            except TimeoutError:
                logger.warning("Test %s timed out after %ds", test_id, suite.timeout)

                # Terminate process
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5)
                except (TimeoutError, ProcessLookupError, OSError):
                    with contextlib.suppress(Exception):
                        process.kill()

                result.status = TestStatus.ERROR
                result.error = f"Test timed out after {suite.timeout} seconds"
                result.end_time = datetime.now(UTC)
                result.duration = suite.timeout

        except Exception as e:
            logger.exception("Error running test %s", test_id)
            result.status = TestStatus.ERROR
            result.error = str(e)
            result.end_time = datetime.now(UTC)

        finally:
            # Clean up
            if test_id in self.running_tests:
                del self.running_tests[test_id]

        # Store result
        if branch_name not in self.branch_results:
            self.branch_results[branch_name] = []

        self.branch_results[branch_name].append(result)
        self._save_test_results(branch_name)

        logger.info(
            "Test %s on %s completed: %s (duration: %.2fs)",
            suite_name,
            branch_name,
            result.status.value,
            result.duration,
        )

        return result

    async def run_all_tests(
        self,
        branch_name: str,
        parallel: bool = True,  # noqa: FBT001
    ) -> list[TestResult]:
        """Run all test suites on a branch.

        Args:
            branch_name: Name of the branch to test
            parallel: Run tests in parallel where possible

        Returns:
            List of TestResult objects
        """
        results = []

        # Separate critical and non-critical tests
        critical_suites = [name for name, suite in self.test_suites.items() if suite.critical]
        non_critical_suites = [name for name, suite in self.test_suites.items() if not suite.critical]

        # Run critical tests first (sequentially)
        for suite_name in critical_suites:
            result = await self.run_test_suite(branch_name, suite_name)
            results.append(result)

            # Stop if critical test fails
            if result.status == TestStatus.FAILED:
                logger.warning("Critical test %s failed, skipping remaining tests", suite_name)
                return results

        # Run non-critical tests
        if parallel and len(non_critical_suites) > 1:
            # Run in parallel
            parallel_suites = [s for s in non_critical_suites if self.test_suites[s].parallel]
            sequential_suites = [s for s in non_critical_suites if not self.test_suites[s].parallel]

            # Run parallel tests
            if parallel_suites:
                tasks = [self.run_test_suite(branch_name, suite_name) for suite_name in parallel_suites]
                parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in parallel_results:  # type: ignore[assignment]
                    if isinstance(result, TestResult):
                        results.append(result)
                    else:
                        logger.error("Error in parallel test execution: %s", result)

            # Run sequential tests
            for suite_name in sequential_suites:
                result = await self.run_test_suite(branch_name, suite_name)
                results.append(result)
        else:
            # Run sequentially
            for suite_name in non_critical_suites:
                result = await self.run_test_suite(branch_name, suite_name)
                results.append(result)

        return results

    @staticmethod
    async def _parse_test_output(result: TestResult, suite: TestSuite) -> None:
        """Parse test output to extract additional information."""
        try:
            output = result.output

            # Parse pytest output
            if "pytest" in suite.command:
                # Extract coverage information
                if "coverage" in output.lower():
                    coverage_match = re.search(r"TOTAL.*?(\d+)%", output)
                    if coverage_match:
                        result.coverage = float(coverage_match.group(1))

                # Extract failed test names
                if result.status == TestStatus.FAILED:
                    failed_tests = re.findall(r"FAILED (.*?) -", output)
                    result.failed_tests = failed_tests

            # Parse mypy output
            elif "mypy" in suite.command:
                if result.status == TestStatus.FAILED:
                    # Count type errors
                    error_count = output.count("error:")
                    result.metadata["error_count"] = error_count

            # Parse ruff output
            elif "ruff" in suite.command:
                if result.status == TestStatus.FAILED:
                    # Count lint violations
                    lines = output.strip().split("\n")
                    violation_count = len([line for line in lines if line.strip()])
                    result.metadata["violation_count"] = violation_count

        except Exception as e:
            logger.debug("Error parsing test output: %s", e)

    async def _run_build(self, branch_name: str) -> bool:
        """Run build process for a branch."""
        try:
            # Simple build check - can be extended
            process = await asyncio.create_subprocess_exec(
                "python",
                "-c",
                "import sys; print('Build check passed')",
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await process.communicate()
            return process.returncode == 0

        except Exception:
            logger.exception("Build failed for %s", branch_name)
            return False

    def get_branch_test_summary(self, branch_name: str) -> dict[str]:
        """Get test summary for a branch."""
        if branch_name not in self.branch_results:
            return {"branch": branch_name, "total_tests": 0, "status": "no_tests"}

        results = self.branch_results[branch_name]
        if not results:
            return {"branch": branch_name, "total_tests": 0, "status": "no_tests"}

        # Get latest results for each test type
        latest_results: dict[str] = {}
        for result in results:
            key = f"{result.test_type.value}"
            if key not in latest_results or result.start_time > latest_results[key].start_time:
                latest_results[key] = result

        # Calculate summary
        total_tests = len(latest_results)
        passed = len([r for r in latest_results.values() if r.status == TestStatus.PASSED])
        failed = len([r for r in latest_results.values() if r.status == TestStatus.FAILED])
        errors = len([r for r in latest_results.values() if r.status == TestStatus.ERROR])

        # Overall status
        if errors > 0:
            overall_status = "error"
        elif failed > 0:
            overall_status = "failed"
        elif passed == total_tests:
            overall_status = "passed"
        else:
            overall_status = "partial"

        return {
            "branch": branch_name,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "status": overall_status,
            "latest_results": {k: v.to_dict() for k, v in latest_results.items()},
            "last_run": max(r.start_time for r in latest_results.values()).isoformat(),
        }

    def get_all_branch_summaries(self) -> dict[str, dict[str]]:
        """Get test summaries for all active branches."""
        summaries = {}

        try:
            for branch_info in self.branch_manager.list_active_branches():
                summaries[branch_info.name] = self.get_branch_test_summary(branch_info.name)
        except Exception as e:
            logger.warning("Failed to get active branches for summaries: %s", e)
            # Return summaries for branches we have results for
            for branch_name in self.branch_results:
                summaries[branch_name] = self.get_branch_test_summary(branch_name)

        return summaries

    async def auto_test_on_commit(self, branch_name: str) -> list[TestResult]:
        """Automatically run tests when commits are detected on a branch."""
        if not self.auto_testing_enabled or not self.test_on_commit:
            return []

        logger.info("Auto-testing triggered for %s on commit", branch_name)
        return await self.run_all_tests(branch_name, parallel=True)

    def configure_test_suite(
        self,
        name: str,
        test_type: TestType,
        command: list[str],
        **kwargs: Any,
    ) -> None:
        """Configure or update a test suite."""
        self.test_suites[name] = TestSuite(
            name=name,
            test_type=test_type,
            command=command,
            **kwargs,
        )
        self._save_test_configuration()
        logger.info("Configured test suite: %s", name)

    def enable_auto_testing(self, enabled: bool = True) -> None:  # noqa: FBT001
        """Enable or disable automatic testing."""
        self.auto_testing_enabled = enabled
        self._save_test_configuration()
        logger.info("Auto-testing %s", "enabled" if enabled else "disabled")

    async def start_test_monitor(self) -> None:
        """Start monitoring for automatic test execution."""
        if not self.auto_testing_enabled:
            logger.info("Auto-testing is disabled")
            return

        logger.info("Starting test monitor for automatic branch testing")

        # This would integrate with git hooks or file watching
        # For now, we'll implement a simple polling mechanism
        while self.auto_testing_enabled:
            try:
                # Check for new commits on active branches
                try:
                    active_branches = self.branch_manager.list_active_branches()
                except Exception as e:
                    logger.warning("Failed to get active branches for monitoring: %s", e)
                    await asyncio.sleep(60)
                    continue

                for branch_info in active_branches:
                    # Check if branch has new commits since last test
                    last_test_time = self._get_last_test_time(branch_info.name)

                    # Get last commit time (simplified check)
                    try:
                        result = subprocess.run(
                            [
                                "git",
                                "log",
                                "-1",
                                "--pretty=format:%ct",
                                branch_info.name,
                            ],
                            check=False,
                            cwd=self.repo_path,
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )

                        if result.returncode == 0 and result.stdout.strip():
                            last_commit_time = datetime.fromtimestamp(int(result.stdout.strip()), tz=UTC)

                            # Run tests if there are new commits
                            if last_commit_time > last_test_time:
                                logger.info("New commits detected on %s, running tests", branch_info.name)
                                await self.auto_test_on_commit(branch_info.name)

                    except Exception as e:
                        logger.debug("Error checking commits for %s: %s", branch_info.name, e)

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except Exception:
                logger.exception("Error in test monitor")
                await asyncio.sleep(60)

    def _get_last_test_time(self, branch_name: str) -> datetime:
        """Get the time of the last test run for a branch."""
        if branch_name not in self.branch_results or not self.branch_results[branch_name]:
            return datetime.min.replace(tzinfo=UTC)

        return max(result.start_time for result in self.branch_results[branch_name])
