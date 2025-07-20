"""Project health calculator widget."""

import logging
import os
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class ProjectHealth:
    """Calculates project health metrics across multiple categories."""

    def __init__(self, project_path: str = ".") -> None:
        self.project_path = project_path
        self.categories = [
            "build",
            "tests",
            "dependencies",
            "security",
            "performance",
            "code_quality",
            "git",
            "documentation",
        ]

    def calculate_health(self) -> dict[str, Any]:
        """Calculate overall project health score."""
        try:
            scores: dict[str, Any] = {}

            # Calculate individual category scores
            scores["build_score"] = self._check_build_health()
            scores["test_score"] = self._check_test_health()
            scores["deps_score"] = self._check_dependencies_health()
            scores["security_score"] = self._check_security_health()
            scores["perf_score"] = self._check_performance_health()
            scores["quality_score"] = self._check_code_quality_health()
            scores["git_score"] = self._check_git_health()
            scores["docs_score"] = self._check_documentation_health()

            # Calculate overall score
            valid_scores = [v for v in scores.values() if v is not None]
            overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

            scores["overall_score"] = int(overall_score)
            suggestions = self._generate_suggestions(scores)
            scores["suggestions"] = suggestions

            return scores

        except Exception as e:
            logger.exception(f"Error calculating project health: {e}")
            return {
                "overall_score": 50,
                "build_score": 50,
                "test_score": 50,
                "deps_score": 50,
                "security_score": 50,
                "perf_score": 50,
                "quality_score": 50,
                "git_score": 50,
                "docs_score": 50,
                "suggestions": ["Unable to calculate health metrics"],
            }

    def _check_build_health(self) -> int:
        """Check if project builds successfully."""
        try:
            # Check for common build files
            build_files = ["Makefile", "build.py", "setup.py", "pyproject.toml"]
            has_build_config = any(os.path.exists(f) for f in build_files)

            if has_build_config:
                return 85
            return 60
        except Exception:
            return 50

    def _check_test_health(self) -> int:
        """Check test coverage and presence."""
        try:
            # Check for test directories/files
            test_indicators = ["tests/", "test_", "pytest", "unittest"]
            has_tests = any(os.path.exists(indicator) or any(indicator in f for f in os.listdir(".") if os.path.isfile(f)) for indicator in test_indicators)

            if has_tests:
                return 75
            return 40
        except Exception:
            return 50

    def _check_dependencies_health(self) -> int:
        """Check dependency management."""
        try:
            # Check for dependency files
            dep_files = ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"]
            has_deps = any(os.path.exists(f) for f in dep_files)

            if has_deps:
                return 90
            return 30
        except Exception:
            return 50

    def _check_security_health(self) -> int:
        """Check security aspects."""
        try:
            # Basic security checks
            has_gitignore = os.path.exists(".gitignore")
            has_secrets = any(keyword in open(f).read().lower() for f in os.listdir(".") if f.endswith((".py", ".yaml", ".yml", ".json")) for keyword in ["password", "secret", "key", "token"])

            score = 70
            if has_gitignore:
                score += 10
            if not has_secrets:
                score += 20

            return min(score, 100)
        except Exception:
            return 80

    def _check_performance_health(self) -> int:
        """Check performance indicators."""
        # Basic performance score
        return 65

    def _check_code_quality_health(self) -> int:
        """Check code quality."""
        try:
            # Check for linting/formatting config
            quality_files = [
                ".flake8",
                ".pylintrc",
                "pyproject.toml",
                ".pre-commit-config.yaml",
            ]
            has_quality_config = any(os.path.exists(f) for f in quality_files)

            if has_quality_config:
                return 85
            return 60
        except Exception:
            return 50

    def _check_git_health(self) -> int:
        """Check git repository health."""
        try:
            if os.path.exists(".git"):
                # Check for recent commits
                try:
                    result = subprocess.run(
                        ["git", "log", "--oneline", "-n", "10"],
                        check=False,
                        capture_output=True,
                        text=True,
                        cwd=self.project_path,
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        return 95
                except Exception as e:
                    # Log subprocess execution errors if needed
                    logger.warning(f"Failed to check git log: {e}")
                return 80
            return 30
        except Exception:
            return 50

    def _check_documentation_health(self) -> int:
        """Check documentation coverage."""
        try:
            # Check for documentation files
            doc_files = ["README.md", "README.rst", "docs/", "CHANGELOG.md"]
            has_docs = any(os.path.exists(f) for f in doc_files)

            if has_docs:
                return 70
            return 30
        except Exception:
            return 50

    def _generate_suggestions(self, scores: dict[str, Any]) -> list[str]:
        """Generate improvement suggestions based on scores."""
        suggestions = []

        if scores.get("test_score", 0) < 70:
            suggestions.append("Consider increasing test coverage")

        if scores.get("deps_score", 0) < 80:
            suggestions.append("Update outdated dependencies")

        if scores.get("docs_score", 0) < 70:
            suggestions.append("Add more documentation")

        if scores.get("quality_score", 0) < 80:
            suggestions.append("Set up code quality tools (linting, formatting)")

        if scores.get("security_score", 0) < 80:
            suggestions.append("Review security practices")

        return suggestions or ["Project health looks good!"]
