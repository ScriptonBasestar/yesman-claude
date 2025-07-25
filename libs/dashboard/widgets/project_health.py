# Copyright notice.

import logging
import os
import subprocess  # noqa: S404
from typing import Any

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Project health calculator widget."""


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

    def calculate_health(self) -> dict[str, object]:
        """Calculate overall project health score.

        Returns:
        object: Description of return value.
        """
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
            valid_scores = [v for v in scores.values() if v is not None and isinstance(v, (int, float))]
            overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

            scores["overall_score"] = int(overall_score)
            suggestions = self._generate_suggestions(scores)
            scores["suggestions"] = suggestions

        except (OSError, PermissionError, ValueError, TypeError):
            logger.exception("Error calculating project health")  # noqa: G004
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
        else:
            return scores

    @staticmethod
    def _check_build_health() -> int:
        """Check if project builds successfully.

        Returns:
        int: Description of return value.
        """
        try:
            # Check for common build files
            build_files = ["Makefile", "build.py", "setup.py", "pyproject.toml"]
            has_build_config = any(os.path.exists(f) for f in build_files)

        except (OSError, FileNotFoundError):
            return 50
        else:
            if has_build_config:
                return 85
            return 60

    @staticmethod
    def _check_test_health() -> int:
        """Check test coverage and presence.

        Returns:
        int: Description of return value.
        """
        try:
            # Check for test directories/files
            test_indicators = ["tests/", "test_", "pytest", "unittest"]
            has_tests = any(os.path.exists(indicator) or any(indicator in f for f in os.listdir(".") if os.path.isfile(f)) for indicator in test_indicators)

        except (OSError, FileNotFoundError):
            return 50
        else:
            if has_tests:
                return 75
            return 40

    @staticmethod
    def _check_dependencies_health() -> int:
        """Check dependency management.

        Returns:
        int: Description of return value.
        """
        try:
            # Check for dependency files
            dep_files = ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"]
            has_deps = any(os.path.exists(f) for f in dep_files)

        except (OSError, FileNotFoundError):
            return 50
        else:
            if has_deps:
                return 90
            return 30

    @staticmethod
    def _check_security_health() -> int:
        """Check security aspects.

        Returns:
        int: Description of return value.
        """
        try:
            # Basic security checks
            has_gitignore = os.path.exists(".gitignore")
            has_secrets = any(
                keyword in open(f, encoding="utf-8").read().lower() for f in os.listdir(".") if f.endswith((".py", ".yaml", ".yml", ".json")) for keyword in ["password", "secret", "key", "token"]
            )

            score = 70
            if has_gitignore:
                score += 10
            if not has_secrets:
                score += 20

            return min(score, 100)
        except (OSError, FileNotFoundError):
            return 80

    @staticmethod
    def _check_performance_health() -> int:
        """Check performance indicators.

        Returns:
        int: Description of return value.
        """
        # Basic performance score
        return 65

    @staticmethod
    def _check_code_quality_health() -> int:
        """Check code quality.

        Returns:
        int: Description of return value.
        """
        try:
            # Check for linting/formatting config
            quality_files = [
                ".flake8",
                ".pylintrc",
                "pyproject.toml",
                ".pre-commit-config.yaml",
            ]
            has_quality_config = any(os.path.exists(f) for f in quality_files)

        except (OSError, FileNotFoundError):
            return 50
        else:
            if has_quality_config:
                return 85
            return 60

    def _check_git_health(self) -> int:
        """Check git repository health.

        Returns:
        int: Description of return value.
        """
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
                except (subprocess.CalledProcessError, OSError, FileNotFoundError) as e:
                    # Log subprocess execution errors if needed
                    logger.warning(f"Failed to check git log: {e}")  # noqa: G004
                return 80

        except (OSError, subprocess.CalledProcessError):
            return 50
        else:
            return 30

    @staticmethod
    def _check_documentation_health() -> int:
        """Check documentation coverage.

        Returns:
        int: Description of return value.
        """
        try:
            # Check for documentation files
            doc_files = ["README.md", "README.rst", "docs/", "CHANGELOG.md"]
            has_docs = any(os.path.exists(f) for f in doc_files)

        except (OSError, FileNotFoundError):
            return 50
        else:
            if has_docs:
                return 70
            return 30

    @staticmethod
    def _generate_suggestions(scores: dict[str, object]) -> list[str]:
        """Generate improvement suggestions based on scores.

        Returns:
        object: Description of return value.
        """
        suggestions = []

        test_score = scores.get("test_score", 0)
        if isinstance(test_score, (int, float)) and test_score < 70:
            suggestions.append("Consider increasing test coverage")

        deps_score = scores.get("deps_score", 0)
        if isinstance(deps_score, (int, float)) and deps_score < 80:
            suggestions.append("Update outdated dependencies")

        docs_score = scores.get("docs_score", 0)
        if isinstance(docs_score, (int, float)) and docs_score < 70:
            suggestions.append("Add more documentation")

        quality_score = scores.get("quality_score", 0)
        if isinstance(quality_score, (int, float)) and quality_score < 80:
            suggestions.append("Set up code quality tools (linting, formatting)")

        security_score = scores.get("security_score", 0)
        if isinstance(security_score, (int, float)) and security_score < 80:
            suggestions.append("Review security practices")

        return suggestions or ["Project health looks good!"]
