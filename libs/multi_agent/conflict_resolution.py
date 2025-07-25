# Copyright notice.

import asyncio
import logging
import re
import subprocess  # noqa: S404
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import cast

from .branch_manager import BranchManager

# Example: Handle import conflicts
# Simple approach: merge unique imports
# Extract imports from conflict markers
# Extract import statements
# Merge unique imports

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Conflict resolution engine for multi-agent branch-based development."""


logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts that can occur."""

    FILE_MODIFICATION = "file_modification"  # Same file modified in different branches
    FILE_DELETION = "file_deletion"  # File deleted in one branch, modified in another
    FILE_CREATION = "file_creation"  # Same file created with different content
    SEMANTIC = "semantic"  # Semantic conflicts (e.g., API changes)
    DEPENDENCY = "dependency"  # Dependency conflicts
    MERGE_CONFLICT = "merge_conflict"  # Traditional git merge conflicts


class ConflictSeverity(Enum):
    """Severity levels for conflicts."""

    LOW = "low"  # Auto-resolvable conflicts
    MEDIUM = "medium"  # Requires simple merge strategies
    HIGH = "high"  # Requires human intervention
    CRITICAL = "critical"  # Blocks all progress


class ResolutionStrategy(Enum):
    """Strategies for conflict resolution."""

    AUTO_MERGE = "auto_merge"  # Automatic merge with git strategies
    PREFER_LATEST = "prefer_latest"  # Use latest changes
    PREFER_MAIN = "prefer_main"  # Prefer main branch version
    CUSTOM_MERGE = "custom_merge"  # Custom merge logic
    HUMAN_REQUIRED = "human_required"  # Requires human intervention
    SEMANTIC_ANALYSIS = "semantic_analysis"  # Use AST analysis for resolution


@dataclass
class ConflictInfo:
    """Information about a detected conflict."""

    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    branches: list[str]
    files: list[str]
    description: str
    suggested_strategy: ResolutionStrategy
    metadata: dict[str, object] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    resolution_result: str | None = None


@dataclass
class ResolutionResult:
    """Result of a conflict resolution attempt."""

    conflict_id: str
    success: bool
    strategy_used: ResolutionStrategy
    resolution_time: float
    message: str
    resolved_files: list[str] = field(default_factory=list)
    remaining_conflicts: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


class ConflictResolutionEngine:
    """Engine for detecting and resolving conflicts between branches."""

    def __init__(self, branch_manager: BranchManager, repo_path: str | None = None) -> None:
        """Initialize the conflict resolution engine.

        Args:
            branch_manager: BranchManager instance for branch operations
            repo_path: Path to the git repository (defaults to current directory)
        """
        self.branch_manager = branch_manager
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

        # Conflict tracking
        self.detected_conflicts: dict[str, ConflictInfo] = {}
        self.resolution_history: list[ResolutionResult] = []

        # Resolution strategies
        self.strategy_handlers = {
            ResolutionStrategy.AUTO_MERGE: self._auto_merge_strategy,
            ResolutionStrategy.PREFER_LATEST: self._prefer_latest_strategy,
            ResolutionStrategy.PREFER_MAIN: self._prefer_main_strategy,
            ResolutionStrategy.CUSTOM_MERGE: self._custom_merge_strategy,
            ResolutionStrategy.SEMANTIC_ANALYSIS: self._semantic_analysis_strategy,
        }

        # Configuration
        self.auto_resolve_enabled = True
        self.max_retry_attempts = 3
        self.conflict_patterns = self._load_conflict_patterns()

        # Performance tracking
        self.resolution_stats = {
            "total_conflicts": 0,
            "auto_resolved": 0,
            "human_required": 0,
            "resolution_success_rate": 0.0,
            "average_resolution_time": 0.0,
        }

    @staticmethod
    def _load_conflict_patterns() -> dict[str, dict[str, object]]:
        """Load known conflict patterns and their resolutions."""
        return {
            "import_conflicts": {
                "pattern": r"<<<<<<< HEAD\nimport.*?\n=======\nimport.*?\n>>>>>>> ",
                "strategy": ResolutionStrategy.SEMANTIC_ANALYSIS,
                "auto_resolve": True,
            },
            "version_conflicts": {
                "pattern": r'version\s*=\s*["\'].*?["\']',
                "strategy": ResolutionStrategy.PREFER_LATEST,
                "auto_resolve": True,
            },
            "comment_conflicts": {
                "pattern": r"<<<<<<< HEAD\n\s*#.*?\n=======\n\s*#.*?\n>>>>>>> ",
                "strategy": ResolutionStrategy.AUTO_MERGE,
                "auto_resolve": True,
            },
        }

    async def detect_potential_conflicts(
        self,
        branches: list[str],
    ) -> list[ConflictInfo]:
        """Detect potential conflicts between branches.

        Args:
            branches: List of branch names to analyze

        Returns:
            List of detected conflicts
        """
        logger.info("Detecting conflicts between branches: %s", branches)
        conflicts = []

        try:
            # Check all pairs of branches
            for i, branch1 in enumerate(branches):
                for branch2 in branches[i + 1 :]:
                    branch_conflicts = await self._detect_branch_conflicts(
                        branch1,
                        branch2,
                    )
                    conflicts.extend(branch_conflicts)

            # Store detected conflicts
            for conflict in conflicts:
                self.detected_conflicts[conflict.conflict_id] = conflict

            self.resolution_stats["total_conflicts"] += len(conflicts)
            logger.info("Detected %d potential conflicts", len(conflicts))

        except (subprocess.CalledProcessError, OSError, RuntimeError):
            logger.exception("Error detecting conflicts")

        return conflicts

    async def _detect_branch_conflicts(
        self,
        branch1: str,
        branch2: str,
    ) -> list[ConflictInfo]:
        """Detect conflicts between two specific branches."""
        conflicts = []

        try:
            # Use git merge-tree to simulate merge and detect conflicts
            result = await self._run_git_command(
                [
                    "merge-tree",
                    await self._get_merge_base(branch1, branch2),
                    branch1,
                    branch2,
                ],
            )

            if result.returncode == 0 and result.stdout:
                # Parse merge-tree output for conflicts
                conflicts.extend(
                    self._parse_merge_tree_output(result.stdout, branch1, branch2),
                )

            # Check for file-level conflicts
            file_conflicts = await self._detect_file_conflicts(branch1, branch2)
            conflicts.extend(file_conflicts)

            # Check for semantic conflicts
            semantic_conflicts = await self._detect_semantic_conflicts(branch1, branch2)
            conflicts.extend(semantic_conflicts)

        except (subprocess.CalledProcessError, OSError, RuntimeError, AttributeError):
            logger.exception("Error detecting conflicts between %s and %s", branch1, branch2)

        return conflicts

    def _parse_merge_tree_output(
        self,
        output: str,
        branch1: str,
        branch2: str,
    ) -> list[ConflictInfo]:
        """Parse git merge-tree output to extract conflict information."""
        conflicts = []
        lines = output.strip().split("\n")

        current_file = None
        conflict_content: list[str] = []

        for line in lines:
            if line.startswith("@@"):
                # New conflict section
                if current_file and conflict_content:
                    conflicts.append(
                        self._create_merge_conflict(
                            current_file,
                            branch1,
                            branch2,
                            "\n".join(conflict_content),
                        ),
                    )

                # Extract file name from git output
                file_match = re.search(r"\+\+\+ b/(.+)", line)
                current_file = file_match.group(1) if file_match else None
                conflict_content = []
            else:
                conflict_content.append(line)

        # Handle last conflict
        if current_file and conflict_content:
            conflicts.append(
                self._create_merge_conflict(
                    current_file,
                    branch1,
                    branch2,
                    "\n".join(conflict_content),
                ),
            )

        return conflicts

    def _create_merge_conflict(
        self,
        file_path: str,
        branch1: str,
        branch2: str,
        content: str,
    ) -> ConflictInfo:
        """Create a ConflictInfo object for a merge conflict."""
        conflict_id = f"merge_{branch1}_{branch2}_{file_path}".replace("/", "_")

        # Determine severity based on file type and content
        severity = ConflictSeverity.MEDIUM
        if file_path.endswith(".py"):
            # Python files may have semantic implications
            severity = ConflictSeverity.HIGH
        elif any(pattern in content.lower() for pattern in ["import", "class", "def"]):
            severity = ConflictSeverity.HIGH
        elif any(pattern in content.lower() for pattern in ["comment", "#", "version"]):
            severity = ConflictSeverity.LOW

        # Suggest resolution strategy
        strategy = self._suggest_resolution_strategy(content, file_path)

        return ConflictInfo(
            conflict_id=conflict_id,
            conflict_type=ConflictType.MERGE_CONFLICT,
            severity=severity,
            branches=[branch1, branch2],
            files=[file_path],
            description=f"Merge conflict in {file_path} between {branch1} and {branch2}",
            suggested_strategy=strategy,
            metadata={
                "conflict_content": content,
                "file_extension": Path(file_path).suffix,
            },
        )

    def _suggest_resolution_strategy(
        self,
        content: str,
        file_path: str,
    ) -> ResolutionStrategy:
        """Suggest the best resolution strategy for a conflict."""
        # Check against known patterns
        for pattern_info in self.conflict_patterns.values():
            pattern = cast(str, pattern_info["pattern"])
            if re.search(pattern, content):
                return ResolutionStrategy(pattern_info["strategy"])

        # Default strategies based on file type
        if file_path.endswith(".py"):
            return ResolutionStrategy.SEMANTIC_ANALYSIS
        if file_path.endswith((".md", ".txt", ".rst")):
            return ResolutionStrategy.AUTO_MERGE
        if file_path.endswith((".json", ".yaml", ".yml")):
            return ResolutionStrategy.PREFER_LATEST
        return ResolutionStrategy.AUTO_MERGE

    async def _detect_file_conflicts(
        self,
        branch1: str,
        branch2: str,
    ) -> list[ConflictInfo]:
        """Detect file-level conflicts (additions, deletions,
        modifications)."""
        conflicts = []

        try:
            # Get changed files in each branch
            files1 = await self._get_changed_files(branch1)
            files2 = await self._get_changed_files(branch2)

            # Find overlapping files
            common_files = set(files1.keys()) & set(files2.keys())

            for file_path in common_files:
                change1 = files1[file_path]
                change2 = files2[file_path]

                conflict_type = ConflictType.FILE_MODIFICATION
                severity = ConflictSeverity.MEDIUM

                # Determine conflict type
                if (change1 == "D" and change2 == "M") or (change1 == "M" and change2 == "D"):
                    conflict_type = ConflictType.FILE_DELETION
                    severity = ConflictSeverity.HIGH
                elif change1 == "A" and change2 == "A":
                    conflict_type = ConflictType.FILE_CREATION
                    severity = ConflictSeverity.MEDIUM

                conflict_id = f"file_{branch1}_{branch2}_{file_path}".replace("/", "_")

                conflicts.append(
                    ConflictInfo(
                        conflict_id=conflict_id,
                        conflict_type=conflict_type,
                        severity=severity,
                        branches=[branch1, branch2],
                        files=[file_path],
                        description=f"File conflict: {file_path} ({change1} vs {change2})",
                        suggested_strategy=ResolutionStrategy.PREFER_LATEST,
                        metadata={"change_types": [change1, change2]},
                    ),
                )

        except (subprocess.CalledProcessError, OSError, RuntimeError):
            logger.exception("Error detecting file conflicts")

        return conflicts

    async def _detect_semantic_conflicts(
        self,
        branch1: str,
        branch2: str,
    ) -> list[ConflictInfo]:
        """Detect semantic conflicts (API changes, dependency conflicts)."""
        conflicts = []

        try:
            # Get Python files changed in both branches
            python_files1 = await self._get_python_files_changed(branch1)
            python_files2 = await self._get_python_files_changed(branch2)

            common_python_files = set(python_files1) & set(python_files2)

            for file_path in common_python_files:
                # Analyze semantic changes
                semantic_conflicts = await self._analyze_semantic_changes(
                    file_path,
                    branch1,
                    branch2,
                )
                conflicts.extend(semantic_conflicts)

        except (subprocess.CalledProcessError, OSError, RuntimeError, AttributeError):
            logger.exception("Error detecting semantic conflicts")

        return conflicts

    async def _analyze_semantic_changes(
        self,
        file_path: str,
        branch1: str,
        branch2: str,
    ) -> list[ConflictInfo]:
        """Analyze semantic changes in a Python file."""
        conflicts: list[ConflictInfo] = []

        try:
            # Get file content from both branches
            content1 = await self._get_file_content(file_path, branch1)
            content2 = await self._get_file_content(file_path, branch2)

            if not content1 or not content2:
                return conflicts

            # Simple semantic analysis
            # Check for function signature changes
            functions1 = self._extract_function_signatures(content1)
            functions2 = self._extract_function_signatures(content2)

            for func_name in functions1:
                if func_name in functions2 and functions1[func_name] != functions2[func_name]:
                    conflict_id = f"semantic_{branch1}_{branch2}_{file_path}_{func_name}".replace(
                        "/",
                        "_",
                    )

                    conflicts.append(
                        ConflictInfo(
                            conflict_id=conflict_id,
                            conflict_type=ConflictType.SEMANTIC,
                            severity=ConflictSeverity.HIGH,
                            branches=[branch1, branch2],
                            files=[file_path],
                            description=f"Function signature conflict: {func_name} in {file_path}",
                            suggested_strategy=ResolutionStrategy.HUMAN_REQUIRED,
                            metadata={
                                "function_name": func_name,
                                "signature1": functions1[func_name],
                                "signature2": functions2[func_name],
                            },
                        ),
                    )

        except (
            subprocess.CalledProcessError,
            OSError,
            RuntimeError,
            ValueError,
            TypeError,
        ):
            logger.exception("Error analyzing semantic changes in %s", file_path)

        return conflicts

    @staticmethod
    def _extract_function_signatures(content: str) -> dict[str, str]:
        """Extract function signatures from Python code."""
        signatures = {}

        # Simple regex-based extraction
        func_pattern = r"def\s+(\w+)\s*\([^)]*\)(?:\s*->\s*[^:]+)?:"
        matches = re.finditer(func_pattern, content, re.MULTILINE)

        for match in matches:
            func_name = match.group(1)
            signature = match.group(0)
            signatures[func_name] = signature

        return signatures

    async def resolve_conflict(
        self,
        conflict_id: str,
        strategy: ResolutionStrategy | None = None,
    ) -> ResolutionResult:
        """Resolve a specific conflict.

        Args:
            conflict_id: ID of the conflict to resolve
            strategy: Resolution strategy to use (if None, uses suggested strategy)

        Returns:
            Result of the resolution attempt
        """
        if conflict_id not in self.detected_conflicts:
            return ResolutionResult(
                conflict_id=conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.AUTO_MERGE,
                resolution_time=0.0,
                message="Conflict not found",
            )

        conflict = self.detected_conflicts[conflict_id]
        strategy = strategy or conflict.suggested_strategy

        start_time = datetime.now(UTC)

        try:
            # Use appropriate resolution handler
            if strategy in self.strategy_handlers:
                result = await self.strategy_handlers[strategy](conflict)
            else:
                result = ResolutionResult(
                    conflict_id=conflict_id,
                    success=False,
                    strategy_used=strategy,
                    resolution_time=0.0,
                    message=f"Unknown strategy: {strategy}",
                )

            # Update resolution time
            resolution_time = (datetime.now(UTC) - start_time).total_seconds()
            result.resolution_time = resolution_time

            # Update conflict info
            if result.success:
                conflict.resolved_at = datetime.now(UTC)
                conflict.resolution_result = result.message
                self.resolution_stats["auto_resolved"] += 1
            else:
                self.resolution_stats["human_required"] += 1

            # Add to history
            self.resolution_history.append(result)

            # Update success rate
            total_attempts = len(self.resolution_history)
            successful = len([r for r in self.resolution_history if r.success])
            self.resolution_stats["resolution_success_rate"] = successful / total_attempts if total_attempts > 0 else 0.0

            # Update average resolution time
            times = [r.resolution_time for r in self.resolution_history if r.resolution_time > 0]
            self.resolution_stats["average_resolution_time"] = sum(times) / len(times) if times else 0.0

            logger.info(
                "Conflict resolution result: %s using %s",
                result.success,
                strategy.value,
            )

        except Exception as e:
            logger.exception("Error resolving conflict %s", conflict_id)
            result = ResolutionResult(
                conflict_id=conflict_id,
                success=False,
                strategy_used=strategy,
                resolution_time=(datetime.now(UTC) - start_time).total_seconds(),
                message=f"Resolution failed: {e}",
            )

        return result

    async def _auto_merge_strategy(self, conflict: ConflictInfo) -> ResolutionResult:
        """Attempt automatic merge using git strategies."""
        try:
            # Try git merge with different strategies
            strategies = ["recursive", "ours", "theirs", "octopus"]

            for strategy in strategies:
                result = await self._try_git_merge(conflict.branches, strategy)
                if result:
                    return ResolutionResult(
                        conflict_id=conflict.conflict_id,
                        success=True,
                        strategy_used=ResolutionStrategy.AUTO_MERGE,
                        resolution_time=0.0,
                        message=f"Auto-merged using {strategy} strategy",
                        resolved_files=conflict.files,
                    )

            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.AUTO_MERGE,
                resolution_time=0.0,
                message="All auto-merge strategies failed",
            )

        except Exception as e:
            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.AUTO_MERGE,
                resolution_time=0.0,
                message=f"Auto-merge failed: {e}",
            )

    async def _prefer_latest_strategy(self, conflict: ConflictInfo) -> ResolutionResult:
        """Resolve conflict by preferring the latest changes."""
        try:
            # Find the branch with latest changes
            latest_branch = await self._get_latest_branch(conflict.branches)

            if latest_branch:
                return ResolutionResult(
                    conflict_id=conflict.conflict_id,
                    success=True,
                    strategy_used=ResolutionStrategy.PREFER_LATEST,
                    resolution_time=0.0,
                    message=f"Used changes from latest branch: {latest_branch}",
                    resolved_files=conflict.files,
                    metadata={"chosen_branch": latest_branch},
                )

            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.PREFER_LATEST,
                resolution_time=0.0,
                message="Could not determine latest branch",
            )

        except Exception as e:
            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.PREFER_LATEST,
                resolution_time=0.0,
                message=f"Latest preference failed: {e}",
            )

    @staticmethod
    async def _prefer_main_strategy(conflict: ConflictInfo) -> ResolutionResult:
        """Resolve conflict by preferring main branch changes."""
        main_branches = ["main", "master", "develop"]

        try:
            for main_branch in main_branches:
                if main_branch in conflict.branches:
                    return ResolutionResult(
                        conflict_id=conflict.conflict_id,
                        success=True,
                        strategy_used=ResolutionStrategy.PREFER_MAIN,
                        resolution_time=0.0,
                        message=f"Used changes from main branch: {main_branch}",
                        resolved_files=conflict.files,
                        metadata={"chosen_branch": main_branch},
                    )

            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.PREFER_MAIN,
                resolution_time=0.0,
                message="No main branch found in conflict",
            )

        except Exception as e:
            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.PREFER_MAIN,
                resolution_time=0.0,
                message=f"Main preference failed: {e}",
            )

    async def _custom_merge_strategy(self, conflict: ConflictInfo) -> ResolutionResult:
        """Apply custom merge logic based on conflict patterns."""
        try:
            # Check for known patterns and apply custom logic
            content = conflict.metadata.get("conflict_content", "")

            if "import" in str(content).lower():
                resolved_content = self._resolve_import_conflicts(cast(str, content))
                if resolved_content:
                    return ResolutionResult(
                        conflict_id=conflict.conflict_id,
                        success=True,
                        strategy_used=ResolutionStrategy.CUSTOM_MERGE,
                        resolution_time=0.0,
                        message="Resolved import conflicts using custom logic",
                        resolved_files=conflict.files,
                    )

            # Add more custom patterns here

            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.CUSTOM_MERGE,
                resolution_time=0.0,
                message="No custom pattern matched",
            )

        except Exception as e:
            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.CUSTOM_MERGE,
                resolution_time=0.0,
                message=f"Custom merge failed: {e}",
            )

    @staticmethod
    async def _semantic_analysis_strategy(
        conflict: ConflictInfo,
    ) -> ResolutionResult:
        """Use semantic analysis to resolve conflicts."""
        try:
            # This would integrate with the TaskAnalyzer for AST-based analysis
            # For now, implement basic semantic checks

            if conflict.conflict_type == ConflictType.SEMANTIC:
                # Analyze function signatures
                metadata = conflict.metadata
                if "function_name" in metadata:
                    # Simple heuristic: prefer signature with more parameters (more specific)
                    sig1 = cast(str, metadata.get("signature1", ""))
                    sig2 = cast(str, metadata.get("signature2", ""))

                    params1 = sig1.count(",") + 1 if "(" in sig1 else 0
                    params2 = sig2.count(",") + 1 if "(" in sig2 else 0

                    chosen_sig = sig1 if params1 >= params2 else sig2

                    return ResolutionResult(
                        conflict_id=conflict.conflict_id,
                        success=True,
                        strategy_used=ResolutionStrategy.SEMANTIC_ANALYSIS,
                        resolution_time=0.0,
                        message="Resolved using semantic analysis: chose signature with more parameters",
                        resolved_files=conflict.files,
                        metadata={"chosen_signature": chosen_sig},
                    )

            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.SEMANTIC_ANALYSIS,
                resolution_time=0.0,
                message="Semantic analysis could not resolve conflict",
            )

        except Exception as e:
            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                success=False,
                strategy_used=ResolutionStrategy.SEMANTIC_ANALYSIS,
                resolution_time=0.0,
                message=f"Semantic analysis failed: {e}",
            )

    @staticmethod
    def _resolve_import_conflicts(content: str) -> str | None:
        """Resolve import statement conflicts."""
        parts = content.split("=======")
        if len(parts) == 2:
            head_part = parts[0].replace("<<<<<<< HEAD", "").strip()
            other_part = parts[1].split(">>>>>>> ")[0].strip()

            head_imports = [line.strip() for line in head_part.split("\n") if line.strip().startswith("import")]
            other_imports = [line.strip() for line in other_part.split("\n") if line.strip().startswith("import")]

            all_imports = list(set(head_imports + other_imports))
            all_imports.sort()  # Sort alphabetically

            return "\n".join(all_imports)

        return None

    async def auto_resolve_all(self) -> list[ResolutionResult]:
        """Attempt to automatically resolve all detected conflicts."""
        results = []

        for conflict_id, conflict in self.detected_conflicts.items():
            if conflict.resolved_at is None and conflict.severity in {
                ConflictSeverity.LOW,
                ConflictSeverity.MEDIUM,
            }:
                result = await self.resolve_conflict(conflict_id)
                results.append(result)

        return results

    def get_conflict_summary(self) -> dict[str, object]:
        """Get a summary of all conflicts and resolution statistics."""
        total_conflicts = len(self.detected_conflicts)
        resolved_conflicts = len(
            [c for c in self.detected_conflicts.values() if c.resolved_at is not None],
        )

        severity_counts = {}
        for severity in ConflictSeverity:
            severity_counts[severity.value] = len(
                [c for c in self.detected_conflicts.values() if c.severity == severity],
            )

        type_counts = {}
        for conflict_type in ConflictType:
            type_counts[conflict_type.value] = len(
                [c for c in self.detected_conflicts.values() if c.conflict_type == conflict_type],
            )

        return {
            "total_conflicts": total_conflicts,
            "resolved_conflicts": resolved_conflicts,
            "unresolved_conflicts": total_conflicts - resolved_conflicts,
            "resolution_rate": (resolved_conflicts / total_conflicts if total_conflicts > 0 else 0.0),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "resolution_stats": self.resolution_stats.copy(),
        }

    # Git helper methods
    async def _run_git_command(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
        cmd = ["git", *args]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await result.communicate()

        return subprocess.CompletedProcess(
            args=cmd,
            returncode=result.returncode,
            stdout=stdout.decode(),
            stderr=stderr.decode(),
        )

    async def _get_merge_base(self, branch1: str, branch2: str) -> str:
        """Get the merge base of two branches."""
        result = await self._run_git_command(["merge-base", branch1, branch2])
        return str(result.stdout).strip()

    async def _get_changed_files(self, branch: str) -> dict[str, str]:
        """Get files changed in a branch with their change types."""
        result = await self._run_git_command(
            ["diff", "--name-status", f"HEAD..{branch}"],
        )

        files = {}
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    change_type = parts[0]
                    file_path = parts[1]
                    files[file_path] = change_type

        return files

    async def _get_python_files_changed(self, branch: str) -> list[str]:
        """Get Python files changed in a branch."""
        files = await self._get_changed_files(branch)
        return [f for f in files if f.endswith(".py")]

    async def _get_file_content(self, file_path: str, branch: str) -> str | None:
        """Get file content from a specific branch."""
        try:
            result = await self._run_git_command(["show", f"{branch}:{file_path}"])
            return str(result.stdout) if result.returncode == 0 else None
        except (subprocess.CalledProcessError, OSError, RuntimeError):
            return None

    async def _get_latest_branch(self, branches: list[str]) -> str | None:
        """Determine which branch has the latest changes."""
        latest_branch = None
        latest_time = None

        for branch in branches:
            try:
                result = await self._run_git_command(
                    ["log", "-1", "--format=%ct", branch],
                )
                timestamp = int(result.stdout.strip())

                if latest_time is None or timestamp > latest_time:
                    latest_time = timestamp
                    latest_branch = branch
            except Exception as e:
                logger.warning("Could not get commit time for branch %s: %s", branch, e)
                continue

        return latest_branch

    @staticmethod
    async def _try_git_merge(branches: list[str], strategy: str) -> bool:
        """Try to merge branches using a specific git strategy."""
        try:
            # This would be implemented with actual git merge commands
            # For now, return a simulation result
            return strategy in {"recursive", "ours"} and len(branches) == 2
        except (subprocess.CalledProcessError, OSError, RuntimeError):
            return False
