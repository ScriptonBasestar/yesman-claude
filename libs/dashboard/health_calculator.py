# Copyright notice.

import json
import logging
import subprocess  # noqa: S404
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, cast

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Project health score calculation system."""


logger = logging.getLogger(__name__)


class HealthCategory(Enum):
    """Categories for health assessment."""

    BUILD = "build"
    TESTS = "tests"
    DEPENDENCIES = "dependencies"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    GIT = "git"
    DOCUMENTATION = "documentation"


class HealthLevel(Enum):
    """Health levels with scores."""

    EXCELLENT = (90, 100, "excellent", "🟢")
    GOOD = (70, 89, "good", "🟡")
    WARNING = (50, 69, "warning", "🟠")
    CRITICAL = (0, 49, "critical", "🔴")
    UNKNOWN = (-1, -1, "unknown", "⚪")

    def __init__(self, min_score: int, max_score: int, label: str, emoji: str) -> None:
        self.min_score = min_score
        self.max_score = max_score
        self.label = label
        self.emoji = emoji

    @classmethod
    def from_score(cls, score: int) -> "HealthLevel":
        """Get health level from numeric score.

        Returns:
        'Healthlevel' object.
        """
        if score < 0:
            return cls.UNKNOWN
        for level in [cls.EXCELLENT, cls.GOOD, cls.WARNING, cls.CRITICAL]:
            if level.min_score <= score <= level.max_score:
                return level
        return cls.UNKNOWN


@dataclass
class HealthMetric:
    """Individual health metric."""

    category: HealthCategory
    name: str
    score: int
    max_score: int = 100
    description: str = ""
    details: dict[str, object] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)

    @property
    def health_level(self) -> HealthLevel:
        """Get health level for this metric.

        Returns:
        Dict containing health status information.
        """
        percentage = (self.score / self.max_score) * 100 if self.max_score > 0 else 0
        return HealthLevel.from_score(int(percentage))

    @property
    def percentage(self) -> float:
        """Get percentage score.

        Returns:
        Float representing.
        """
        return (self.score / self.max_score) * 100 if self.max_score > 0 else 0

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary.

        Returns:
        Dict containing.
        """
        return {
            "category": self.category.value,
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage,
            "health_level": self.health_level.label,
            "emoji": self.health_level.emoji,
            "description": self.description,
            "details": self.details,
            "last_updated": self.last_updated,
        }


@dataclass
class ProjectHealth:
    """Overall project health assessment."""

    project_path: str
    overall_score: int
    metrics: list[HealthMetric]
    last_assessment: float = field(default_factory=time.time)

    @property
    def overall_health_level(self) -> HealthLevel:
        """Get overall health level.

        Returns:
        Dict containing health status information.
        """
        return HealthLevel.from_score(self.overall_score)

    @property
    def category_scores(self) -> dict[str, float]:
        """Get average scores by category.

        Returns:
        Dict containing.
        """
        category_metrics: dict[str, list[float]] = {}
        for metric in self.metrics:
            category = metric.category.value
            if category not in category_metrics:
                category_metrics[category] = []
            category_metrics[category].append(metric.percentage)

        return {category: sum(scores) / len(scores) if scores else 0 for category, scores in category_metrics.items()}

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary.

        Returns:
        Dict containing.
        """
        return {
            "project_path": self.project_path,
            "overall_score": self.overall_score,
            "overall_health_level": self.overall_health_level.label,
            "overall_emoji": self.overall_health_level.emoji,
            "category_scores": self.category_scores,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "last_assessment": self.last_assessment,
            "total_metrics": len(self.metrics),
        }


class HealthCalculator:
    """Calculates project health scores based on various metrics."""

    def __init__(self, project_path: Path | None = None) -> None:
        self.project_path = project_path or Path.cwd()
        self.logger = logging.getLogger("yesman.health_calculator")

        # Cache for expensive operations
        self._cache: dict[str, object] = {}
        self._cache_ttl = 300  # 5 minutes

    async def calculate_health(self, force_refresh: bool = False) -> ProjectHealth:  # noqa: FBT001
        """Calculate comprehensive project health."""
        cache_key = f"health_{self.project_path}"

        if not force_refresh and cache_key in self._cache:
            cached_data = self._cache[cache_key]
            cached_data_dict = cast(dict[str, Any], cached_data)
            if time.time() - cast(float, cached_data_dict["timestamp"]) < self._cache_ttl:
                return ProjectHealth(**cast(dict[str, Any], cached_data_dict["health"]))

        self.logger.info("Calculating health for project: %s", self.project_path)

        metrics = []

        # Build health
        build_metrics = await self._assess_build_health()
        metrics.extend(build_metrics)

        # Test health
        test_metrics = await self._assess_test_health()
        metrics.extend(test_metrics)

        # Dependencies health
        dependency_metrics = await self._assess_dependency_health()
        metrics.extend(dependency_metrics)

        # Performance health
        performance_metrics = await self._assess_performance_health()
        metrics.extend(performance_metrics)

        # Security health
        security_metrics = await self._assess_security_health()
        metrics.extend(security_metrics)

        # Code quality health
        quality_metrics = await self._assess_code_quality_health()
        metrics.extend(quality_metrics)

        # Git health
        git_metrics = await self._assess_git_health()
        metrics.extend(git_metrics)

        # Documentation health
        doc_metrics = await self._assess_documentation_health()
        metrics.extend(doc_metrics)

        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)

        health = ProjectHealth(
            project_path=str(self.project_path),
            overall_score=overall_score,
            metrics=metrics,
        )

        # Cache result
        self._cache[cache_key] = {
            "health": {
                "project_path": health.project_path,
                "overall_score": health.overall_score,
                "metrics": health.metrics,
                "last_assessment": health.last_assessment,
            },
            "timestamp": time.time(),
        }

        return health

    async def _assess_build_health(self) -> list[HealthMetric]:
        """Assess build system health."""
        metrics = []

        try:
            # Check for build configuration files
            build_files = [
                ("package.json", "npm/yarn build"),
                ("Cargo.toml", "cargo build"),
                ("setup.py", "python setup"),
                ("Makefile", "make build"),
                ("build.gradle", "gradle build"),
                ("pom.xml", "maven build"),
            ]

            build_config_score = 0
            found_configs = []

            for config_file, build_system in build_files:
                if (self.project_path / config_file).exists():
                    build_config_score += 20
                    found_configs.append(build_system)

            build_config_score = min(100, build_config_score)

            metrics.append(
                HealthMetric(
                    category=HealthCategory.BUILD,
                    name="Build Configuration",
                    score=build_config_score,
                    description="Build system configuration files present",
                    details={"found_configs": found_configs},
                )
            )

            # Try to run build command
            build_success_score = await self._test_build_command()

            metrics.append(
                HealthMetric(
                    category=HealthCategory.BUILD,
                    name="Build Success",
                    score=build_success_score,
                    description="Can project build successfully",
                )
            )

        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as e:
            self.logger.debug("Build health assessment error: %s", e)

        return metrics

    async def _assess_test_health(self) -> list[HealthMetric]:
        """Assess test suite health."""
        metrics = []

        try:
            # Check for test files
            test_patterns = [
                "**/*test*.py",
                "**/*test*.js",
                "**/*test*.ts",
                "**/test_*.py",
                "**/tests/**/*.py",
                "**/*.spec.js",
                "**/*.spec.ts",
                "**/src/**/__tests__/**/*",
            ]

            test_files = []
            for pattern in test_patterns:
                test_files.extend(list(self.project_path.glob(pattern)))

            test_coverage_score = min(100, len(test_files) * 10)  # 10 points per test file, max 100

            metrics.append(
                HealthMetric(
                    category=HealthCategory.TESTS,
                    name="Test Coverage",
                    score=test_coverage_score,
                    description=f"Number of test files found: {len(test_files)}",
                    details={"test_file_count": len(test_files)},
                )
            )

            # Try to run tests
            test_success_score = await self._test_test_command()

            metrics.append(
                HealthMetric(
                    category=HealthCategory.TESTS,
                    name="Test Success",
                    score=test_success_score,
                    description="Can tests run successfully",
                )
            )

        except (OSError, subprocess.SubprocessError, ValueError) as e:
            self.logger.debug("Test health assessment error: %s", e)

        return metrics

    async def _assess_dependency_health(self) -> list[HealthMetric]:
        """Assess dependency health."""
        metrics = []

        try:
            # Check for dependency files and potential issues
            dependency_files = [
                ("package.json", self._check_npm_dependencies),
                ("requirements.txt", self._check_python_dependencies),
                ("Cargo.toml", self._check_rust_dependencies),
                ("go.mod", self._check_go_dependencies),
            ]

            total_deps = 0
            outdated_deps = 0

            for dep_file, check_func in dependency_files:
                dep_path = self.project_path / dep_file
                if dep_path.exists():
                    deps, outdated = await check_func(dep_path)
                    total_deps += deps
                    outdated_deps += outdated

            # Calculate dependency health score
            if total_deps > 0:
                outdated_ratio = outdated_deps / total_deps
                dependency_score = max(0, 100 - int(outdated_ratio * 100))
            else:
                dependency_score = 80  # Default score if no dependencies found

            metrics.append(
                HealthMetric(
                    category=HealthCategory.DEPENDENCIES,
                    name="Dependency Freshness",
                    score=dependency_score,
                    description=f"Dependency status: {total_deps} total, {outdated_deps} potentially outdated",
                    details={
                        "total_dependencies": total_deps,
                        "outdated_dependencies": outdated_deps,
                    },
                )
            )

        except (OSError, json.JSONDecodeError, ValueError) as e:
            self.logger.debug("Dependency health assessment error: %s", e)

        return metrics

    async def _assess_performance_health(self) -> list[HealthMetric]:
        """Assess performance-related health."""
        metrics = []

        try:
            # Check project size and structure
            file_count = len(list(self.project_path.rglob("*")))
            size_score = max(0, 100 - max(0, (file_count - 1000) // 100))  # Penalty for large projects

            metrics.append(
                HealthMetric(
                    category=HealthCategory.PERFORMANCE,
                    name="Project Size",
                    score=size_score,
                    description=f"Project file count: {file_count}",
                    details={"file_count": file_count},
                )
            )

            # Check for performance-related configuration
            perf_configs = [
                ".eslintrc",
                "tsconfig.json",
                "webpack.config.js",
                "rollup.config.js",
                "vite.config.js",
                "babel.config.js",
            ]

            perf_config_score = 0
            found_perf_configs = []

            for config in perf_configs:
                if (self.project_path / config).exists():
                    perf_config_score += 15
                    found_perf_configs.append(config)

            perf_config_score = min(100, perf_config_score)

            metrics.append(
                HealthMetric(
                    category=HealthCategory.PERFORMANCE,
                    name="Performance Tooling",
                    score=perf_config_score,
                    description="Performance-related configuration files",
                    details={"found_configs": found_perf_configs},
                )
            )

        except (OSError, ValueError) as e:
            self.logger.debug("Performance health assessment error: %s", e)

        return metrics

    async def _assess_security_health(self) -> list[HealthMetric]:
        """Assess security-related health."""
        metrics = []

        try:
            # Check for security-related files
            security_files = [
                ".gitignore",
                ".env.example",
                "SECURITY.md",
                ".github/dependabot.yml",
                ".snyk",
            ]

            security_score = 0
            found_security_files = []

            for sec_file in security_files:
                if (self.project_path / sec_file).exists():
                    security_score += 20
                    found_security_files.append(sec_file)

            # Check .gitignore content for common sensitive patterns
            gitignore_path = self.project_path / ".gitignore"
            if gitignore_path.exists():
                gitignore_content = gitignore_path.read_text()
                sensitive_patterns = [
                    ".env",
                    "*.key",
                    "*.pem",
                    "secrets",
                    "credentials",
                ]
                protected_patterns = sum(1 for pattern in sensitive_patterns if pattern in gitignore_content)
                security_score += protected_patterns * 4  # 4 points per protected pattern

            security_score = min(100, security_score)

            metrics.append(
                HealthMetric(
                    category=HealthCategory.SECURITY,
                    name="Security Configuration",
                    score=security_score,
                    description="Security-related files and configurations",
                    details={"found_files": found_security_files},
                )
            )

        except (OSError, UnicodeDecodeError) as e:
            self.logger.debug("Security health assessment error: %s", e)

        return metrics

    async def _assess_code_quality_health(self) -> list[HealthMetric]:
        """Assess code quality health."""
        metrics = []

        try:
            # Check for code quality tools
            quality_files = [
                (".eslintrc.json", "ESLint"),
                (".eslintrc.js", "ESLint"),
                ("pylint.rc", "Pylint"),
                (".flake8", "Flake8"),
                ("mypy.ini", "MyPy"),
                (".prettierrc", "Prettier"),
                ("rustfmt.toml", "RustFmt"),
            ]

            quality_score = 0
            found_tools = []

            for config_file, tool_name in quality_files:
                if (self.project_path / config_file).exists():
                    quality_score += 15
                    found_tools.append(tool_name)

            quality_score = min(100, quality_score)

            metrics.append(
                HealthMetric(
                    category=HealthCategory.CODE_QUALITY,
                    name="Code Quality Tools",
                    score=quality_score,
                    description="Code quality and linting tools configured",
                    details={"found_tools": found_tools},
                )
            )

            # Check for documentation in code
            doc_score = await self._assess_code_documentation()

            metrics.append(
                HealthMetric(
                    category=HealthCategory.CODE_QUALITY,
                    name="Code Documentation",
                    score=doc_score,
                    description="Documentation coverage in source code",
                )
            )

        except (OSError, ValueError) as e:
            self.logger.debug("Code quality health assessment error: %s", e)

        return metrics

    async def _assess_git_health(self) -> list[HealthMetric]:
        """Assess Git repository health."""
        metrics = []

        try:
            if not (self.project_path / ".git").exists():
                metrics.append(
                    HealthMetric(
                        category=HealthCategory.GIT,
                        name="Git Repository",
                        score=0,
                        description="No Git repository found",
                    )
                )
                return metrics

            # Check git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                check=False,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                uncommitted_files = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
                git_status_score = max(0, 100 - (uncommitted_files * 10))  # Penalty for uncommitted files

                metrics.append(
                    HealthMetric(
                        category=HealthCategory.GIT,
                        name="Git Status",
                        score=git_status_score,
                        description=f"Uncommitted files: {uncommitted_files}",
                        details={"uncommitted_files": uncommitted_files},
                    )
                )

            # Check recent commit activity
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                check=False,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                recent_commits = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
                commit_activity_score = min(100, recent_commits * 10)

                metrics.append(
                    HealthMetric(
                        category=HealthCategory.GIT,
                        name="Recent Activity",
                        score=commit_activity_score,
                        description=f"Recent commits: {recent_commits}",
                        details={"recent_commits": recent_commits},
                    )
                )

        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            self.logger.debug("Git health assessment error: %s", e)

        return metrics

    async def _assess_documentation_health(self) -> list[HealthMetric]:
        """Assess documentation health."""
        metrics = []

        try:
            # Check for documentation files
            doc_files = [
                "README.md",
                "README.rst",
                "README.txt",
                "CHANGELOG.md",
                "CONTRIBUTING.md",
                "LICENSE",
                "docs/README.md",
                "INSTALL.md",
            ]

            doc_score = 0
            found_docs = []

            for doc_file in doc_files:
                doc_path = self.project_path / doc_file
                if doc_path.exists():
                    # Give more points for longer documentation
                    try:
                        content_length = len(doc_path.read_text())
                        if content_length > 500:  # Substantial documentation
                            doc_score += 20
                        elif content_length > 100:  # Basic documentation
                            doc_score += 10
                        else:  # Minimal documentation
                            doc_score += 5
                        found_docs.append(doc_file)
                    except (OSError, UnicodeDecodeError):
                        doc_score += 5
                        found_docs.append(doc_file)

            doc_score = min(100, doc_score)

            metrics.append(
                HealthMetric(
                    category=HealthCategory.DOCUMENTATION,
                    name="Documentation Files",
                    score=doc_score,
                    description=f"Documentation files found: {len(found_docs)}",
                    details={"found_docs": found_docs},
                )
            )

        except (OSError, UnicodeDecodeError) as e:
            self.logger.debug("Documentation health assessment error: %s", e)

        return metrics

    @staticmethod
    def _calculate_overall_score(metrics: list[HealthMetric]) -> int:
        """Calculate overall project health score.

        Returns:
        Integer representing.
        """
        if not metrics:
            return 0

        # Weight categories differently
        category_weights = {
            HealthCategory.BUILD: 20,
            HealthCategory.TESTS: 20,
            HealthCategory.DEPENDENCIES: 15,
            HealthCategory.SECURITY: 15,
            HealthCategory.CODE_QUALITY: 15,
            HealthCategory.GIT: 10,
            HealthCategory.PERFORMANCE: 10,
            HealthCategory.DOCUMENTATION: 5,
        }

        weighted_sum = 0.0
        total_weight = 0

        for metric in metrics:
            weight = category_weights.get(metric.category, 5)
            weighted_sum += float(metric.percentage * weight)
            total_weight += weight

        return int(weighted_sum / total_weight) if total_weight > 0 else 0

    async def _test_build_command(self) -> int:
        """Test if build command works."""
        build_commands = [
            ["npm", "run", "build"],
            ["yarn", "build"],
            ["cargo", "check"],
            ["python", "setup.py", "check"],
            ["make", "check"],
        ]

        for cmd in build_commands:
            try:
                result = subprocess.run(
                    cmd,
                    check=False,
                    cwd=self.project_path,
                    capture_output=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return 100
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return 30  # Default score if no build command works

    async def _test_test_command(self) -> int:
        """Test if test command works."""
        test_commands = [
            ["npm", "test"],
            ["yarn", "test"],
            ["pytest", "--tb=no", "-q"],
            ["python", "-m", "pytest", "--tb=no", "-q"],
            ["cargo", "test", "--quiet"],
            ["go", "test", "./..."],
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    check=False,
                    cwd=self.project_path,
                    capture_output=True,
                    timeout=60,
                )
                if result.returncode == 0:
                    return 100
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return 40  # Default score if no test command works

    @staticmethod
    async def _check_npm_dependencies(package_json_path: Path) -> tuple[int, int]:
        """Check npm dependencies for outdated packages."""
        try:
            with open(package_json_path, encoding="utf-8") as f:
                package_data = json.load(f)

            deps = package_data.get("dependencies", {})
            dev_deps = package_data.get("devDependencies", {})
            total_deps = len(deps) + len(dev_deps)

            # Simple heuristic: assume 10% might be outdated
            outdated_deps = max(1, total_deps // 10)

            return total_deps, outdated_deps

        except (OSError, json.JSONDecodeError, KeyError):
            return 0, 0

    @staticmethod
    async def _check_python_dependencies(requirements_path: Path) -> tuple[int, int]:
        """Check Python dependencies."""
        try:
            content = requirements_path.read_text()
            lines = [line.strip() for line in content.split("\n") if line.strip() and not line.startswith("#")]
            total_deps = len(lines)

            # Simple heuristic: assume 15% might be outdated
            outdated_deps = max(1, total_deps // 7)

            return total_deps, outdated_deps

        except (OSError, UnicodeDecodeError):
            return 0, 0

    @staticmethod
    async def _check_rust_dependencies(cargo_toml_path: Path) -> tuple[int, int]:
        """Check Rust/Cargo dependencies."""
        try:
            with open(cargo_toml_path, "rb") as f:
                content = tomllib.load(f)
            deps = content.get("dependencies", {})
            dev_deps = content.get("dev-dependencies", {})
            return (
                len(deps) + len(dev_deps),
                0,
            )  # Assuming no easy way to check outdated
        except (ImportError, OSError, ValueError, KeyError):
            return 0, 0

    @staticmethod
    def _get_dependencies_from_toml(content: str) -> tuple[list[str], list[str]]:
        """Extract dependencies from Cargo.toml content.

        Returns:
        List of the requested data.
        """
        dependencies = []
        dev_dependencies = []
        in_deps_section = False
        in_dev_deps_section = False

        for raw_line in content.split("\n"):
            line = raw_line.strip()
            if line == "[dependencies]":
                in_deps_section = True
                in_dev_deps_section = False
                continue
            if line == "[dev-dependencies]":
                in_dev_deps_section = True
                in_deps_section = False
                continue
            if line.startswith("["):
                in_deps_section = False
                in_dev_deps_section = False
                continue

            if in_deps_section and "=" in line:
                dependencies.append(line.split("=")[0].strip())
            elif in_dev_deps_section and "=" in line:
                dev_dependencies.append(line.split("=")[0].strip())

        return dependencies, dev_dependencies

    @staticmethod
    async def _check_go_dependencies(go_mod_path: Path) -> tuple[int, int]:
        """Check Go dependencies."""
        try:
            content = go_mod_path.read_text()
            lines = [line.strip() for line in content.split("\n") if line.strip() and line.startswith("\t")]
            deps_count = len(lines)

            outdated_deps = max(1, deps_count // 10)

            return deps_count, outdated_deps

        except (OSError, UnicodeDecodeError):
            return 0, 0

    async def _assess_code_documentation(self) -> int:
        """Assess code documentation coverage."""
        try:
            # Look for common source files
            source_patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.rs", "**/*.go"]

            total_files = 0
            documented_files = 0

            for pattern in source_patterns:
                for file_path in self.project_path.glob(pattern):
                    if file_path.is_file() and "node_modules" not in str(file_path):
                        total_files += 1
                        try:
                            content = file_path.read_text()
                            # Simple heuristic: look for docstrings/comments
                            if (
                                '"""' in content
                                or "'''" in content  # Python docstrings
                                or "/**" in content  # JS/TS JSDoc
                                or "///" in content  # Rust doc comments
                                or "// " in content
                            ):  # General comments
                                documented_files += 1
                        except (OSError, UnicodeDecodeError) as e:
                            self.logger.warning("Could not parse file %s: %s", file_path, e)
                            continue

            if total_files > 0:
                doc_ratio = documented_files / total_files
                return int(doc_ratio * 100)
            return 80  # Default if no source files found

        except (OSError, ValueError):
            return 50  # Default on error

    @staticmethod
    def get_health_summary(health: ProjectHealth) -> dict[str, object]:
        """Get a summary of project health.

        Returns:
        Dict containing health status information.
        """
        return {
            "overall": {
                "score": health.overall_score,
                "level": health.overall_health_level.label,
                "emoji": health.overall_health_level.emoji,
            },
            "categories": health.category_scores,
            "metrics_count": len(health.metrics),
            "last_assessment": health.last_assessment,
            "project_path": health.project_path,
        }
