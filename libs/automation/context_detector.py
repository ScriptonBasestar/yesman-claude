"""Context detection system for workflow automation."""

import logging
import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of workflow contexts that can be detected."""

    GIT_COMMIT = "git_commit"
    TEST_FAILURE = "test_failure"
    BUILD_FAILURE = "build_failure"
    DEPENDENCY_UPDATE = "dependency_update"
    FILE_CHANGE = "file_change"
    CLAUDE_IDLE = "claude_idle"
    ERROR_DETECTED = "error_detected"
    DEPLOYMENT_READY = "deployment_ready"
    CODE_REVIEW = "code_review"
    UNKNOWN = "unknown"


@dataclass
class ContextInfo:
    """Information about detected context."""

    context_type: ContextType
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any]
    timestamp: float
    project_path: Optional[str] = None
    session_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "context_type": self.context_type.value,
            "confidence": self.confidence,
            "details": self.details,
            "timestamp": self.timestamp,
            "project_path": self.project_path,
            "session_name": self.session_name,
        }


class ContextDetector:
    """Detects workflow contexts from various sources."""

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.logger = logging.getLogger("yesman.context_detector")

        # Context detection patterns
        self.patterns = {
            ContextType.GIT_COMMIT: [
                r"committed.*files? changed",
                r"git commit.*successful",
                r"\[.*\] .*commit.*",
                r"Changes committed successfully",
            ],
            ContextType.TEST_FAILURE: [
                r"test.*failed",
                r"assertion.*error",
                r"FAILED.*test",
                r"pytest.*failed",
                r"jest.*failed",
                r"Error.*test",
                r"\d+ failed.*\d+ passed",
            ],
            ContextType.BUILD_FAILURE: [
                r"build.*failed",
                r"compilation.*error",
                r"npm.*error",
                r"yarn.*error",
                r"webpack.*error",
                r"tsc.*error",
                r"cargo.*error",
            ],
            ContextType.DEPENDENCY_UPDATE: [
                r"package.*updated",
                r"npm.*install",
                r"yarn.*install",
                r"pip.*install",
                r"requirements.*updated",
                r"cargo.*update",
            ],
            ContextType.ERROR_DETECTED: [
                r"error:|ERROR:",
                r"exception.*occurred",
                r"traceback.*most recent",
                r"fatal.*error",
                r"segmentation.*fault",
            ],
            ContextType.CODE_REVIEW: [
                r"review.*requested",
                r"pull.*request",
                r"merge.*request",
                r"code.*review",
                r"pr.*created",
            ],
        }

        self._last_git_hash = None
        self._last_file_mtimes: Dict[str, float] = {}

    def detect_context_from_content(self, content: str, session_name: str = None) -> List[ContextInfo]:
        """Detect context from content (e.g., tmux pane output)."""
        detected_contexts = []

        for context_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    confidence = self._calculate_confidence(context_type, content, match)

                    if confidence > 0.6:  # Minimum confidence threshold
                        context_info = ContextInfo(
                            context_type=context_type,
                            confidence=confidence,
                            details={
                                "matched_pattern": pattern,
                                "matched_text": match.group(),
                                "content_snippet": content[max(0, match.start() - 50) : match.end() + 50],
                            },
                            timestamp=time.time(),
                            project_path=str(self.project_path),
                            session_name=session_name,
                        )
                        detected_contexts.append(context_info)

        return detected_contexts

    def detect_git_context(self) -> Optional[ContextInfo]:
        """Detect git-related context changes."""
        try:
            # Check current git status
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=False,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                current_hash = result.stdout.strip()

                if self._last_git_hash and current_hash != self._last_git_hash:
                    # New commit detected
                    commit_info = self._get_commit_info(current_hash)
                    self._last_git_hash = current_hash

                    return ContextInfo(
                        context_type=ContextType.GIT_COMMIT,
                        confidence=0.95,
                        details={
                            "commit_hash": current_hash,
                            "commit_message": commit_info.get("message", ""),
                            "files_changed": commit_info.get("files_changed", []),
                        },
                        timestamp=time.time(),
                        project_path=str(self.project_path),
                    )

                self._last_git_hash = current_hash

        except Exception as e:
            self.logger.debug(f"Git context detection failed: {e}")

        return None

    def detect_file_changes(self, watched_patterns: List[str] = None) -> List[ContextInfo]:
        """Detect file system changes."""
        if not watched_patterns:
            watched_patterns = ["*.py", "*.js", "*.ts", "*.md", "package.json", "requirements.txt"]

        detected_changes = []

        for pattern in watched_patterns:
            try:
                for file_path in self.project_path.glob(f"**/{pattern}"):
                    if file_path.is_file():
                        current_mtime = file_path.stat().st_mtime
                        file_key = str(file_path)

                        if file_key in self._last_file_mtimes and current_mtime > self._last_file_mtimes[file_key]:
                            # File was modified
                            detected_changes.append(
                                ContextInfo(
                                    context_type=ContextType.FILE_CHANGE,
                                    confidence=0.8,
                                    details={
                                        "file_path": file_key,
                                        "file_type": file_path.suffix,
                                        "modification_time": current_mtime,
                                    },
                                    timestamp=time.time(),
                                    project_path=str(self.project_path),
                                )
                            )

                        self._last_file_mtimes[file_key] = current_mtime

            except Exception as e:
                self.logger.debug(f"File change detection failed for {pattern}: {e}")

        return detected_changes

    def detect_claude_idle_context(self, last_activity_time: float, idle_threshold: int = 30) -> Optional[ContextInfo]:
        """Detect when Claude has been idle for a while."""
        current_time = time.time()
        idle_duration = current_time - last_activity_time

        if idle_duration > idle_threshold:
            return ContextInfo(
                context_type=ContextType.CLAUDE_IDLE,
                confidence=min(1.0, idle_duration / (idle_threshold * 2)),
                details={
                    "idle_duration": idle_duration,
                    "last_activity": last_activity_time,
                },
                timestamp=current_time,
                project_path=str(self.project_path),
            )

        return None

    def detect_deployment_ready_context(self) -> Optional[ContextInfo]:
        """Detect when project is ready for deployment."""
        try:
            # Check if tests are passing
            test_result = self._run_quick_test_check()

            # Check if build is successful
            build_result = self._run_quick_build_check()

            # Check git status
            git_clean = self._is_git_clean()

            if test_result and build_result and git_clean:
                return ContextInfo(
                    context_type=ContextType.DEPLOYMENT_READY,
                    confidence=0.9,
                    details={
                        "tests_passing": test_result,
                        "build_successful": build_result,
                        "git_clean": git_clean,
                    },
                    timestamp=time.time(),
                    project_path=str(self.project_path),
                )

        except Exception as e:
            self.logger.debug(f"Deployment readiness check failed: {e}")

        return None

    def _calculate_confidence(self, context_type: ContextType, content: str, match: re.Match) -> float:
        """Calculate confidence score for a detected context."""
        base_confidence = 0.7

        # Boost confidence based on context specificity
        if context_type == ContextType.TEST_FAILURE:
            if "failed" in match.group().lower() and any(test_word in content.lower() for test_word in ["test", "spec", "jest", "pytest"]):
                base_confidence += 0.2

        elif context_type == ContextType.GIT_COMMIT:
            if "commit" in match.group().lower() and "success" in content.lower():
                base_confidence += 0.2

        elif context_type == ContextType.BUILD_FAILURE and "error" in match.group().lower() and any(build_word in content.lower() for build_word in ["build", "compile", "webpack", "tsc"]):
            base_confidence += 0.2

        # Reduce confidence if match is very short or unclear
        if len(match.group()) < 10:
            base_confidence -= 0.1

        return min(1.0, max(0.0, base_confidence))

    def _get_commit_info(self, commit_hash: str) -> Dict[str, Any]:
        """Get detailed information about a commit."""
        try:
            # Get commit message
            msg_result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%s", commit_hash],
                check=False,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Get changed files
            files_result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                check=False,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            return {
                "message": msg_result.stdout.strip() if msg_result.returncode == 0 else "",
                "files_changed": files_result.stdout.strip().split("\n") if files_result.returncode == 0 else [],
            }

        except Exception as e:
            self.logger.debug(f"Failed to get commit info: {e}")
            return {}

    def _run_quick_test_check(self) -> bool:
        """Run a quick test to see if tests are generally passing."""
        test_commands = [
            ["npm", "test", "--", "--passWithNoTests"],
            ["pytest", "--tb=no", "-q"],
            ["python", "-m", "pytest", "--tb=no", "-q"],
            ["cargo", "test", "--quiet"],
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    check=False,
                    cwd=self.project_path,
                    capture_output=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return False

    def _run_quick_build_check(self) -> bool:
        """Run a quick build check."""
        build_commands = [
            ["npm", "run", "build"],
            ["yarn", "build"],
            ["python", "setup.py", "check"],
            ["cargo", "check"],
        ]

        for cmd in build_commands:
            try:
                result = subprocess.run(
                    cmd,
                    check=False,
                    cwd=self.project_path,
                    capture_output=True,
                    timeout=60,
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return False

    def _is_git_clean(self) -> bool:
        """Check if git working directory is clean."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                check=False,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and not result.stdout.strip()
        except Exception:
            return False

    def get_current_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current project context."""
        summary = {
            "project_path": str(self.project_path),
            "timestamp": time.time(),
            "contexts": [],
        }

        # Check various context types
        git_context = self.detect_git_context()
        if git_context:
            summary["contexts"].append(git_context.to_dict())

        file_changes = self.detect_file_changes()
        for change in file_changes[-5:]:  # Last 5 changes
            summary["contexts"].append(change.to_dict())

        deployment_context = self.detect_deployment_ready_context()
        if deployment_context:
            summary["contexts"].append(deployment_context.to_dict())

        return summary
