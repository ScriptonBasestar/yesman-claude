"""Project health score calculation system."""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re

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
    
    def __init__(self, min_score: int, max_score: int, label: str, emoji: str):
        self.min_score = min_score
        self.max_score = max_score
        self.label = label
        self.emoji = emoji
        
    @classmethod
    def from_score(cls, score: int) -> 'HealthLevel':
        """Get health level from numeric score."""
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
    details: Dict[str, Any] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)
    
    @property
    def health_level(self) -> HealthLevel:
        """Get health level for this metric."""
        percentage = (self.score / self.max_score) * 100 if self.max_score > 0 else 0
        return HealthLevel.from_score(int(percentage))
        
    @property
    def percentage(self) -> float:
        """Get percentage score."""
        return (self.score / self.max_score) * 100 if self.max_score > 0 else 0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'category': self.category.value,
            'name': self.name,
            'score': self.score,
            'max_score': self.max_score,
            'percentage': self.percentage,
            'health_level': self.health_level.label,
            'emoji': self.health_level.emoji,
            'description': self.description,
            'details': self.details,
            'last_updated': self.last_updated
        }


@dataclass
class ProjectHealth:
    """Overall project health assessment."""
    project_path: str
    overall_score: int
    metrics: List[HealthMetric]
    last_assessment: float = field(default_factory=time.time)
    
    @property
    def overall_health_level(self) -> HealthLevel:
        """Get overall health level."""
        return HealthLevel.from_score(self.overall_score)
        
    @property
    def category_scores(self) -> Dict[str, float]:
        """Get average scores by category."""
        category_metrics = {}
        for metric in self.metrics:
            category = metric.category.value
            if category not in category_metrics:
                category_metrics[category] = []
            category_metrics[category].append(metric.percentage)
            
        return {
            category: sum(scores) / len(scores) if scores else 0
            for category, scores in category_metrics.items()
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'project_path': self.project_path,
            'overall_score': self.overall_score,
            'overall_health_level': self.overall_health_level.label,
            'overall_emoji': self.overall_health_level.emoji,
            'category_scores': self.category_scores,
            'metrics': [metric.to_dict() for metric in self.metrics],
            'last_assessment': self.last_assessment,
            'total_metrics': len(self.metrics)
        }


class HealthCalculator:
    """Calculates project health scores based on various metrics."""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.logger = logging.getLogger("yesman.health_calculator")
        
        # Cache for expensive operations
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
        
    async def calculate_health(self, force_refresh: bool = False) -> ProjectHealth:
        """Calculate comprehensive project health."""
        cache_key = f"health_{self.project_path}"
        
        if not force_refresh and cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if time.time() - cached_data['timestamp'] < self._cache_ttl:
                return ProjectHealth(**cached_data['health'])
                
        self.logger.info(f"Calculating health for project: {self.project_path}")
        
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
            metrics=metrics
        )
        
        # Cache result
        self._cache[cache_key] = {
            'health': {
                'project_path': health.project_path,
                'overall_score': health.overall_score,
                'metrics': health.metrics,
                'last_assessment': health.last_assessment
            },
            'timestamp': time.time()
        }
        
        return health
        
    async def _assess_build_health(self) -> List[HealthMetric]:
        """Assess build system health."""
        metrics = []
        
        try:
            # Check for build configuration files
            build_files = [
                ('package.json', 'npm/yarn build'),
                ('Cargo.toml', 'cargo build'),
                ('setup.py', 'python setup'),
                ('Makefile', 'make build'),
                ('build.gradle', 'gradle build'),
                ('pom.xml', 'maven build')
            ]
            
            build_config_score = 0
            found_configs = []
            
            for config_file, build_system in build_files:
                if (self.project_path / config_file).exists():
                    build_config_score += 20
                    found_configs.append(build_system)
                    
            build_config_score = min(100, build_config_score)
            
            metrics.append(HealthMetric(
                category=HealthCategory.BUILD,
                name="Build Configuration",
                score=build_config_score,
                description=f"Build system configuration files present",
                details={'found_configs': found_configs}
            ))
            
            # Try to run build command
            build_success_score = await self._test_build_command()
            
            metrics.append(HealthMetric(
                category=HealthCategory.BUILD,
                name="Build Success",
                score=build_success_score,
                description="Can project build successfully"
            ))
            
        except Exception as e:
            self.logger.debug(f"Build health assessment error: {e}")
            
        return metrics
        
    async def _assess_test_health(self) -> List[HealthMetric]:
        """Assess test suite health."""
        metrics = []
        
        try:
            # Check for test files
            test_patterns = [
                "**/*test*.py", "**/*test*.js", "**/*test*.ts",
                "**/test_*.py", "**/tests/**/*.py",
                "**/*.spec.js", "**/*.spec.ts",
                "**/src/**/__tests__/**/*"
            ]
            
            test_files = []
            for pattern in test_patterns:
                test_files.extend(list(self.project_path.glob(pattern)))
                
            test_coverage_score = min(100, len(test_files) * 10)  # 10 points per test file, max 100
            
            metrics.append(HealthMetric(
                category=HealthCategory.TESTS,
                name="Test Coverage",
                score=test_coverage_score,
                description=f"Number of test files found: {len(test_files)}",
                details={'test_file_count': len(test_files)}
            ))
            
            # Try to run tests
            test_success_score = await self._test_test_command()
            
            metrics.append(HealthMetric(
                category=HealthCategory.TESTS,
                name="Test Success",
                score=test_success_score,
                description="Can tests run successfully"
            ))
            
        except Exception as e:
            self.logger.debug(f"Test health assessment error: {e}")
            
        return metrics
        
    async def _assess_dependency_health(self) -> List[HealthMetric]:
        """Assess dependency health."""
        metrics = []
        
        try:
            # Check for dependency files and potential issues
            dependency_files = [
                ('package.json', self._check_npm_dependencies),
                ('requirements.txt', self._check_python_dependencies),
                ('Cargo.toml', self._check_rust_dependencies),
                ('go.mod', self._check_go_dependencies)
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
                
            metrics.append(HealthMetric(
                category=HealthCategory.DEPENDENCIES,
                name="Dependency Freshness",
                score=dependency_score,
                description=f"Dependency status: {total_deps} total, {outdated_deps} potentially outdated",
                details={'total_dependencies': total_deps, 'outdated_dependencies': outdated_deps}
            ))
            
        except Exception as e:
            self.logger.debug(f"Dependency health assessment error: {e}")
            
        return metrics
        
    async def _assess_performance_health(self) -> List[HealthMetric]:
        """Assess performance-related health."""
        metrics = []
        
        try:
            # Check project size and structure
            file_count = len(list(self.project_path.rglob('*')))
            size_score = max(0, 100 - max(0, (file_count - 1000) // 100))  # Penalty for large projects
            
            metrics.append(HealthMetric(
                category=HealthCategory.PERFORMANCE,
                name="Project Size",
                score=size_score,
                description=f"Project file count: {file_count}",
                details={'file_count': file_count}
            ))
            
            # Check for performance-related configuration
            perf_configs = [
                '.eslintrc', 'tsconfig.json', 'webpack.config.js',
                'rollup.config.js', 'vite.config.js', 'babel.config.js'
            ]
            
            perf_config_score = 0
            found_perf_configs = []
            
            for config in perf_configs:
                if (self.project_path / config).exists():
                    perf_config_score += 15
                    found_perf_configs.append(config)
                    
            perf_config_score = min(100, perf_config_score)
            
            metrics.append(HealthMetric(
                category=HealthCategory.PERFORMANCE,
                name="Performance Tooling",
                score=perf_config_score,
                description="Performance-related configuration files",
                details={'found_configs': found_perf_configs}
            ))
            
        except Exception as e:
            self.logger.debug(f"Performance health assessment error: {e}")
            
        return metrics
        
    async def _assess_security_health(self) -> List[HealthMetric]:
        """Assess security-related health."""
        metrics = []
        
        try:
            # Check for security-related files
            security_files = [
                '.gitignore', '.env.example', 'SECURITY.md',
                '.github/dependabot.yml', '.snyk'
            ]
            
            security_score = 0
            found_security_files = []
            
            for sec_file in security_files:
                if (self.project_path / sec_file).exists():
                    security_score += 20
                    found_security_files.append(sec_file)
                    
            # Check .gitignore content for common sensitive patterns
            gitignore_path = self.project_path / '.gitignore'
            if gitignore_path.exists():
                gitignore_content = gitignore_path.read_text()
                sensitive_patterns = ['.env', '*.key', '*.pem', 'secrets', 'credentials']
                protected_patterns = sum(1 for pattern in sensitive_patterns if pattern in gitignore_content)
                security_score += protected_patterns * 4  # 4 points per protected pattern
                
            security_score = min(100, security_score)
            
            metrics.append(HealthMetric(
                category=HealthCategory.SECURITY,
                name="Security Configuration",
                score=security_score,
                description="Security-related files and configurations",
                details={'found_files': found_security_files}
            ))
            
        except Exception as e:
            self.logger.debug(f"Security health assessment error: {e}")
            
        return metrics
        
    async def _assess_code_quality_health(self) -> List[HealthMetric]:
        """Assess code quality health."""
        metrics = []
        
        try:
            # Check for code quality tools
            quality_files = [
                ('.eslintrc.json', 'ESLint'),
                ('.eslintrc.js', 'ESLint'),
                ('pylint.rc', 'Pylint'),
                ('.flake8', 'Flake8'),
                ('mypy.ini', 'MyPy'),
                ('.prettierrc', 'Prettier'),
                ('rustfmt.toml', 'RustFmt')
            ]
            
            quality_score = 0
            found_tools = []
            
            for config_file, tool_name in quality_files:
                if (self.project_path / config_file).exists():
                    quality_score += 15
                    found_tools.append(tool_name)
                    
            quality_score = min(100, quality_score)
            
            metrics.append(HealthMetric(
                category=HealthCategory.CODE_QUALITY,
                name="Code Quality Tools",
                score=quality_score,
                description="Code quality and linting tools configured",
                details={'found_tools': found_tools}
            ))
            
            # Check for documentation in code
            doc_score = await self._assess_code_documentation()
            
            metrics.append(HealthMetric(
                category=HealthCategory.CODE_QUALITY,
                name="Code Documentation",
                score=doc_score,
                description="Documentation coverage in source code"
            ))
            
        except Exception as e:
            self.logger.debug(f"Code quality health assessment error: {e}")
            
        return metrics
        
    async def _assess_git_health(self) -> List[HealthMetric]:
        """Assess Git repository health."""
        metrics = []
        
        try:
            if not (self.project_path / '.git').exists():
                metrics.append(HealthMetric(
                    category=HealthCategory.GIT,
                    name="Git Repository",
                    score=0,
                    description="No Git repository found"
                ))
                return metrics
                
            # Check git status
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                uncommitted_files = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                git_status_score = max(0, 100 - (uncommitted_files * 10))  # Penalty for uncommitted files
                
                metrics.append(HealthMetric(
                    category=HealthCategory.GIT,
                    name="Git Status",
                    score=git_status_score,
                    description=f"Uncommitted files: {uncommitted_files}",
                    details={'uncommitted_files': uncommitted_files}
                ))
            
            # Check recent commit activity
            result = subprocess.run(
                ['git', 'log', '--oneline', '-10'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                recent_commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                commit_activity_score = min(100, recent_commits * 10)
                
                metrics.append(HealthMetric(
                    category=HealthCategory.GIT,
                    name="Recent Activity",
                    score=commit_activity_score,
                    description=f"Recent commits: {recent_commits}",
                    details={'recent_commits': recent_commits}
                ))
                
        except Exception as e:
            self.logger.debug(f"Git health assessment error: {e}")
            
        return metrics
        
    async def _assess_documentation_health(self) -> List[HealthMetric]:
        """Assess documentation health."""
        metrics = []
        
        try:
            # Check for documentation files
            doc_files = [
                'README.md', 'README.rst', 'README.txt',
                'CHANGELOG.md', 'CONTRIBUTING.md', 'LICENSE',
                'docs/README.md', 'INSTALL.md'
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
                    except Exception:
                        doc_score += 5
                        found_docs.append(doc_file)
                        
            doc_score = min(100, doc_score)
            
            metrics.append(HealthMetric(
                category=HealthCategory.DOCUMENTATION,
                name="Documentation Files",
                score=doc_score,
                description=f"Documentation files found: {len(found_docs)}",
                details={'found_docs': found_docs}
            ))
            
        except Exception as e:
            self.logger.debug(f"Documentation health assessment error: {e}")
            
        return metrics
        
    def _calculate_overall_score(self, metrics: List[HealthMetric]) -> int:
        """Calculate overall project health score."""
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
            HealthCategory.DOCUMENTATION: 5
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for metric in metrics:
            weight = category_weights.get(metric.category, 5)
            weighted_sum += metric.percentage * weight
            total_weight += weight
            
        return int(weighted_sum / total_weight) if total_weight > 0 else 0
        
    async def _test_build_command(self) -> int:
        """Test if build command works."""
        build_commands = [
            ['npm', 'run', 'build'],
            ['yarn', 'build'],
            ['cargo', 'check'],
            ['python', 'setup.py', 'check'],
            ['make', 'check']
        ]
        
        for cmd in build_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_path,
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return 100
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
                
        return 30  # Default score if no build command works
        
    async def _test_test_command(self) -> int:
        """Test if test command works."""
        test_commands = [
            ['npm', 'test'],
            ['yarn', 'test'],
            ['pytest', '--tb=no', '-q'],
            ['python', '-m', 'pytest', '--tb=no', '-q'],
            ['cargo', 'test', '--quiet'],
            ['go', 'test', './...']
        ]
        
        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_path,
                    capture_output=True,
                    timeout=60
                )
                if result.returncode == 0:
                    return 100
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
                
        return 40  # Default score if no test command works
        
    async def _check_npm_dependencies(self, package_json_path: Path) -> Tuple[int, int]:
        """Check npm dependencies for outdated packages."""
        try:
            with open(package_json_path) as f:
                package_data = json.load(f)
                
            deps = package_data.get('dependencies', {})
            dev_deps = package_data.get('devDependencies', {})
            total_deps = len(deps) + len(dev_deps)
            
            # Simple heuristic: assume 10% might be outdated
            outdated_deps = max(1, total_deps // 10)
            
            return total_deps, outdated_deps
            
        except Exception:
            return 0, 0
            
    async def _check_python_dependencies(self, requirements_path: Path) -> Tuple[int, int]:
        """Check Python dependencies."""
        try:
            content = requirements_path.read_text()
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            total_deps = len(lines)
            
            # Simple heuristic: assume 15% might be outdated
            outdated_deps = max(1, total_deps // 7)
            
            return total_deps, outdated_deps
            
        except Exception:
            return 0, 0
            
    async def _check_rust_dependencies(self, cargo_toml_path: Path) -> Tuple[int, int]:
        """Check Rust dependencies."""
        try:
            content = cargo_toml_path.read_text()
            # Simple parsing for [dependencies] section
            in_deps_section = False
            deps_count = 0
            
            for line in content.split('\n'):
                line = line.strip()
                if line == '[dependencies]':
                    in_deps_section = True
                elif line.startswith('[') and line != '[dependencies]':
                    in_deps_section = False
                elif in_deps_section and '=' in line and not line.startswith('#'):
                    deps_count += 1
                    
            outdated_deps = max(1, deps_count // 8)
            
            return deps_count, outdated_deps
            
        except Exception:
            return 0, 0
            
    async def _check_go_dependencies(self, go_mod_path: Path) -> Tuple[int, int]:
        """Check Go dependencies."""
        try:
            content = go_mod_path.read_text()
            lines = [line.strip() for line in content.split('\n') if line.strip() and line.startswith('\t')]
            deps_count = len(lines)
            
            outdated_deps = max(1, deps_count // 10)
            
            return deps_count, outdated_deps
            
        except Exception:
            return 0, 0
            
    async def _assess_code_documentation(self) -> int:
        """Assess code documentation coverage."""
        try:
            # Look for common source files
            source_patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.rs', '**/*.go']
            
            total_files = 0
            documented_files = 0
            
            for pattern in source_patterns:
                for file_path in self.project_path.glob(pattern):
                    if file_path.is_file() and 'node_modules' not in str(file_path):
                        total_files += 1
                        try:
                            content = file_path.read_text()
                            # Simple heuristic: look for docstrings/comments
                            if ('"""' in content or "'''" in content or  # Python docstrings
                                '/**' in content or  # JS/TS JSDoc
                                '///' in content or  # Rust doc comments
                                '// ' in content):   # General comments
                                documented_files += 1
                        except Exception:
                            continue
                            
            if total_files > 0:
                doc_ratio = documented_files / total_files
                return int(doc_ratio * 100)
            else:
                return 80  # Default if no source files found
                
        except Exception:
            return 50  # Default on error
            
    def get_health_summary(self, health: ProjectHealth) -> Dict[str, Any]:
        """Get a summary of project health."""
        return {
            'overall': {
                'score': health.overall_score,
                'level': health.overall_health_level.label,
                'emoji': health.overall_health_level.emoji
            },
            'categories': health.category_scores,
            'metrics_count': len(health.metrics),
            'last_assessment': health.last_assessment,
            'project_path': health.project_path
        }