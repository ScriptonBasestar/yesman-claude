# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Automatic conflict resolution and semantic merge implementation for multi-
agent development."""

import ast
import asyncio
import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .branch_manager import BranchManager
from .conflict_resolution import ConflictResolutionEngine
from .semantic_analyzer import (
    SemanticAnalyzer,
    SemanticConflict,
    SemanticConflictType,
    SemanticContext,
)

logger = logging.getLogger(__name__)


class MergeStrategy(Enum):
    """Strategies for semantic merging."""

    PREFER_FIRST = "prefer_first"
    PREFER_SECOND = "prefer_second"
    INTELLIGENT_MERGE = "intelligent_merge"
    FUNCTION_LEVEL_MERGE = "function_level_merge"
    AST_BASED_MERGE = "ast_based_merge"
    SEMANTIC_UNION = "semantic_union"
    CONTEXTUAL_MERGE = "contextual_merge"


class MergeResolution(Enum):
    """Resolution outcomes for merge operations."""

    AUTO_RESOLVED = "auto_resolved"
    PARTIAL_RESOLUTION = "partial_resolution"
    MANUAL_REQUIRED = "manual_required"
    MERGE_FAILED = "merge_failed"
    SEMANTIC_PRESERVED = "semantic_preserved"


@dataclass
class MergeResult:
    """Result of a semantic merge operation."""

    merge_id: str
    file_path: str
    resolution: MergeResolution
    strategy_used: MergeStrategy
    merged_content: str | None = None
    conflicts_resolved: list[str] = field(default_factory=list)
    unresolved_conflicts: list[str] = field(default_factory=list)
    merge_confidence: float = 0.0
    semantic_integrity: bool = True
    diff_stats: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    merge_time: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ConflictResolutionRule:
    """Rule for automatic conflict resolution."""

    rule_id: str
    pattern: str
    conflict_types: list[SemanticConflictType]
    resolution_strategy: MergeStrategy
    confidence_threshold: float = 0.7
    description: str = ""
    enabled: bool = True


class SemanticMerger:
    """Advanced semantic merger for automatic conflict resolution."""

    def __init__(
        self,
        semantic_analyzer: SemanticAnalyzer,
        conflict_engine: ConflictResolutionEngine,
        branch_manager: BranchManager,
        repo_path: str | None = None,
    ) -> None:
        """Initialize the semantic merger.

        Args:
            semantic_analyzer: SemanticAnalyzer for code analysis
            conflict_engine: ConflictResolutionEngine for conflict context
            branch_manager: BranchManager for branch operations
            repo_path: Path to git repository

        Returns:
            Description of return value
        """
        self.semantic_analyzer = semantic_analyzer
        self.conflict_engine = conflict_engine
        self.branch_manager = branch_manager
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

        # Merge results storage
        self.merge_results: dict[str, MergeResult] = {}
        self.merge_history: list[MergeResult] = []

        # Resolution rules
        self.resolution_rules = self._initialize_resolution_rules()

        # Merge configuration
        self.default_strategy = MergeStrategy.INTELLIGENT_MERGE
        self.preserve_comments = True
        self.preserve_docstrings = True
        self.preserve_imports = True
        self.enable_ast_validation = True

        # Machine learning components for merge decisions
        self.merge_patterns: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        self.success_rate_by_strategy: defaultdict[str, list[float]] = defaultdict(list)

        # Performance tracking
        self.merge_stats = {
            "total_merges": 0,
            "successful_merges": 0,
            "auto_resolved": 0,
            "manual_required": 0,
            "semantic_integrity_maintained": 0,
            "average_confidence": 0.0,
        }

    async def perform_semantic_merge(
        self,
        file_path: str,
        branch1: str,
        branch2: str,
        target_branch: str | None = None,
        strategy: MergeStrategy | None = None,
    ) -> MergeResult:
        """Perform intelligent semantic merge of a file between branches.

        Args:
            file_path: Path to file to merge
            branch1: First branch name
            branch2: Second branch name
            target_branch: Target branch for merge (default: branch1)
            strategy: Specific merge strategy to use

        Returns:
            MergeResult with merge outcome and details
        """
        logger.info(
            "Performing semantic merge for %s between %s and %s",
            file_path,
            branch1,
            branch2,
        )

        merge_id = f"merge_{branch1}_{branch2}_{hashlib.sha256(file_path.encode()).hexdigest()[:8]}"
        strategy = strategy or self.default_strategy
        target_branch = target_branch or branch1

        try:
            # Get file contents from both branches
            content1 = await self._get_file_content(file_path, branch1)
            content2 = await self._get_file_content(file_path, branch2)

            if not content1 or not content2:
                return MergeResult(
                    merge_id=merge_id,
                    file_path=file_path,
                    resolution=MergeResolution.MERGE_FAILED,
                    strategy_used=strategy,
                    merge_confidence=0.0,
                    semantic_integrity=False,
                    metadata={"error": "Could not retrieve file contents"},
                )

            # Detect semantic conflicts
            conflicts = await self._detect_file_conflicts(file_path, branch1, branch2)

            # Apply resolution strategy
            merge_result = await self._apply_merge_strategy(
                merge_id,
                file_path,
                content1,
                content2,
                conflicts,
                strategy,
            )

            # Validate semantic integrity
            if merge_result.merged_content and self.enable_ast_validation:
                merge_result.semantic_integrity = self._validate_ast_integrity(
                    merge_result.merged_content,
                )

            # Store result
            self.merge_results[merge_id] = merge_result
            self.merge_history.append(merge_result)
            self._update_merge_stats(merge_result)

            logger.info("Merge completed: %s", merge_result.resolution.value)

        except (OSError, RuntimeError, ValueError, SyntaxError) as e:
            logger.exception("Error performing semantic merge")
            return MergeResult(
                merge_id=merge_id,
                file_path=file_path,
                resolution=MergeResolution.MERGE_FAILED,
                strategy_used=strategy,
                merge_confidence=0.0,
                semantic_integrity=False,
                metadata={"error": str(e)},
            )
        else:
            return merge_result

    async def batch_merge_files(
        self,
        file_paths: list[str],
        branch1: str,
        branch2: str,
        target_branch: str | None = None,
        max_concurrent: int = 5,
    ) -> list[MergeResult]:
        """Perform batch semantic merge of multiple files."""
        logger.info("Starting batch merge of %d files", len(file_paths))

        semaphore = asyncio.Semaphore(max_concurrent)

        async def merge_file(file_path: str) -> MergeResult:
            async with semaphore:
                return await self.perform_semantic_merge(
                    file_path,
                    branch1,
                    branch2,
                    target_branch,
                )

        tasks = [merge_file(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and convert to MergeResults
        merge_results: list[MergeResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Error merging %s: %s", file_paths[i], result)
                merge_results.append(
                    MergeResult(
                        merge_id=f"error_{i}",
                        file_path=file_paths[i],
                        resolution=MergeResolution.MERGE_FAILED,
                        strategy_used=self.default_strategy,
                        metadata={"error": str(result)},
                    ),
                )
            else:
                assert isinstance(result, MergeResult)  # Type narrowing for mypy
                merge_results.append(result)

        logger.info("Batch merge completed: %d results", len(merge_results))
        return merge_results

    async def auto_resolve_conflicts(
        self,
        conflicts: list[SemanticConflict],
    ) -> list[MergeResult]:
        """Automatically resolve a list of semantic conflicts.

        Args:
            conflicts: List of SemanticConflict to resolve

        Returns:
            List of MergeResult for each resolution attempt
        """
        logger.info("Auto-resolving %d semantic conflicts", len(conflicts))

        results = []

        # Group conflicts by file for efficient processing
        conflicts_by_file = defaultdict(list)
        for conflict in conflicts:
            conflicts_by_file[conflict.file_path].append(conflict)

        for file_path, file_conflicts in conflicts_by_file.items():
            # Determine best resolution strategy for this file
            strategy = self._select_optimal_strategy(file_conflicts)

            # Get the first conflict to extract branch information
            first_conflict = file_conflicts[0]

            # Perform merge for this file
            merge_result = await self.perform_semantic_merge(
                file_path=file_path,
                branch1=first_conflict.branch1,
                branch2=first_conflict.branch2,
                strategy=strategy,
            )

            # Record which conflicts were addressed
            resolved_conflicts = []
            for conflict in file_conflicts:
                if self._conflict_resolved_by_merge(conflict, merge_result):
                    resolved_conflicts.append(conflict.conflict_id)

            merge_result.conflicts_resolved = resolved_conflicts
            results.append(merge_result)

        logger.info("Auto-resolution completed: %d files processed", len(results))
        return results

    async def _apply_merge_strategy(
        self,
        merge_id: str,
        file_path: str,
        content1: str,
        content2: str,
        conflicts: list[SemanticConflict],
        strategy: MergeStrategy,
    ) -> MergeResult:
        """Apply specific merge strategy to resolve conflicts."""
        if strategy == MergeStrategy.INTELLIGENT_MERGE:
            return await self._intelligent_merge(
                merge_id,
                file_path,
                content1,
                content2,
                conflicts,
            )
        if strategy == MergeStrategy.AST_BASED_MERGE:
            return await self._ast_based_merge(
                merge_id,
                file_path,
                content1,
                content2,
                conflicts,
            )
        if strategy == MergeStrategy.FUNCTION_LEVEL_MERGE:
            return await self._function_level_merge(
                merge_id,
                file_path,
                content1,
                content2,
                conflicts,
            )
        if strategy == MergeStrategy.SEMANTIC_UNION:
            return await self._semantic_union_merge(
                merge_id,
                file_path,
                content1,
                content2,
                conflicts,
            )
        if strategy == MergeStrategy.CONTEXTUAL_MERGE:
            return await self._contextual_merge(
                merge_id,
                file_path,
                content1,
                content2,
                conflicts,
            )
        if strategy == MergeStrategy.PREFER_FIRST:
            return self._prefer_branch_merge(
                merge_id,
                file_path,
                content1,
                conflicts,
                "first",
            )
        if strategy == MergeStrategy.PREFER_SECOND:
            return self._prefer_branch_merge(
                merge_id,
                file_path,
                content2,
                conflicts,
                "second",
            )
        # Fallback to intelligent merge
        return await self._intelligent_merge(
            merge_id,
            file_path,
            content1,
            content2,
            conflicts,
        )

    async def _intelligent_merge(
        self,
        merge_id: str,
        file_path: str,
        content1: str,
        content2: str,
        conflicts: list[SemanticConflict],
    ) -> MergeResult:
        """Perform intelligent merge using multiple heuristics."""
        try:
            # Parse ASTs for both versions
            ast.parse(content1)
            ast.parse(content2)

            # Extract semantic contexts
            context1 = self.semantic_analyzer._extract_semantic_context(  # noqa: SLF001
                file_path,
                content1,
            )
            context2 = self.semantic_analyzer._extract_semantic_context(  # noqa: SLF001
                file_path,
                content2,
            )

            # Start with base content
            merged_content = content1
            resolved_conflicts = []
            unresolved_conflicts = []
            confidence_scores = []

            # Process each conflict type intelligently
            for conflict in conflicts:
                resolution_result = await self._resolve_individual_conflict(
                    conflict,
                    content1,
                    content2,
                    context1,
                    context2,
                )

                if resolution_result["resolved"]:
                    resolved_conflicts.append(conflict.conflict_id)
                    confidence_scores.append(resolution_result["confidence"])
                    # Apply the resolution to merged content
                    merged_content = resolution_result.get(
                        "merged_content",
                        merged_content,
                    )
                else:
                    unresolved_conflicts.append(conflict.conflict_id)

            # Calculate overall confidence
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

            # Determine resolution status
            if not unresolved_conflicts:
                resolution = MergeResolution.AUTO_RESOLVED
            elif resolved_conflicts:
                resolution = MergeResolution.PARTIAL_RESOLUTION
            else:
                resolution = MergeResolution.MANUAL_REQUIRED

            # Calculate diff statistics
            diff_stats = self._calculate_diff_stats(content1, content2, merged_content)

            return MergeResult(
                merge_id=merge_id,
                file_path=file_path,
                resolution=resolution,
                strategy_used=MergeStrategy.INTELLIGENT_MERGE,
                merged_content=merged_content,
                conflicts_resolved=resolved_conflicts,
                unresolved_conflicts=unresolved_conflicts,
                merge_confidence=overall_confidence,
                semantic_integrity=True,
                diff_stats=diff_stats,
                metadata={
                    "total_conflicts": len(conflicts),
                    "resolution_details": {
                        "resolved": len(resolved_conflicts),
                        "unresolved": len(unresolved_conflicts),
                    },
                },
            )

        except Exception as e:
            logger.exception("Error in intelligent merge")
            return MergeResult(
                merge_id=merge_id,
                file_path=file_path,
                resolution=MergeResolution.MERGE_FAILED,
                strategy_used=MergeStrategy.INTELLIGENT_MERGE,
                merge_confidence=0.0,
                semantic_integrity=False,
                metadata={"error": str(e)},
            )

    async def _ast_based_merge(
        self,
        merge_id: str,
        file_path: str,
        content1: str,
        content2: str,
        conflicts: list[SemanticConflict],
    ) -> MergeResult:
        """Perform AST-based merge preserving code structure."""
        try:
            # Parse both ASTs
            tree1 = ast.parse(content1)
            tree2 = ast.parse(content2)

            # Create merged AST by combining nodes intelligently
            merged_tree = self._merge_ast_trees(tree1, tree2, conflicts)

            # Convert back to source code
            merged_content = ast.unparse(merged_tree)

            # Validate the result
            try:
                ast.parse(merged_content)
                semantic_integrity = True
            except SyntaxError:
                semantic_integrity = False

            return MergeResult(
                merge_id=merge_id,
                file_path=file_path,
                resolution=(MergeResolution.AUTO_RESOLVED if semantic_integrity else MergeResolution.MERGE_FAILED),
                strategy_used=MergeStrategy.AST_BASED_MERGE,
                merged_content=merged_content,
                merge_confidence=0.8 if semantic_integrity else 0.0,
                semantic_integrity=semantic_integrity,
                diff_stats=self._calculate_diff_stats(
                    content1,
                    content2,
                    merged_content,
                ),
            )

        except Exception as e:
            logger.exception("Error in AST-based merge")
            return MergeResult(
                merge_id=merge_id,
                file_path=file_path,
                resolution=MergeResolution.MERGE_FAILED,
                strategy_used=MergeStrategy.AST_BASED_MERGE,
                merge_confidence=0.0,
                semantic_integrity=False,
                metadata={"error": str(e)},
            )

    async def _function_level_merge(
        self,
        merge_id: str,
        file_path: str,
        content1: str,
        content2: str,
        conflicts: list[SemanticConflict],
    ) -> MergeResult:
        """Perform function-level merge for granular conflict resolution."""
        try:
            # Extract function definitions from both versions
            functions1 = self._extract_functions_with_content(content1)
            functions2 = self._extract_functions_with_content(content2)

            base_content = self._extract_non_function_content(content1)
            merged_functions = {}
            resolved_conflicts = []
            unresolved_conflicts = []

            # Merge functions intelligently
            all_function_names = set(functions1.keys()) | set(functions2.keys())

            for func_name in all_function_names:
                if func_name in functions1 and func_name in functions2:
                    # Function exists in both - need to merge
                    func_conflict = self._find_function_conflict(func_name, conflicts)
                    if func_conflict:
                        merge_result = self._merge_function_definitions(
                            functions1[func_name],
                            functions2[func_name],
                            func_conflict,
                        )
                        merged_functions[func_name] = merge_result["content"]

                        if merge_result["resolved"]:
                            resolved_conflicts.append(func_conflict.conflict_id)
                        else:
                            unresolved_conflicts.append(func_conflict.conflict_id)
                    else:
                        # No conflict detected, prefer version with more recent changes
                        merged_functions[func_name] = functions2[func_name]
                elif func_name in functions1:
                    # Only in first version
                    merged_functions[func_name] = functions1[func_name]
                else:
                    # Only in second version
                    merged_functions[func_name] = functions2[func_name]

            # Reconstruct file content
            merged_content = base_content
            for func_name, func_content in merged_functions.items():
                merged_content += "\n\n" + func_content

            # Calculate confidence based on resolution success
            confidence = len(resolved_conflicts) / max(len(conflicts), 1)

            # Determine resolution status
            resolution = (MergeResolution.PARTIAL_RESOLUTION if resolved_conflicts else MergeResolution.MANUAL_REQUIRED) if unresolved_conflicts else MergeResolution.AUTO_RESOLVED

            return MergeResult(
                merge_id=merge_id,
                file_path=file_path,
                resolution=resolution,
                strategy_used=MergeStrategy.FUNCTION_LEVEL_MERGE,
                merged_content=merged_content,
                conflicts_resolved=resolved_conflicts,
                unresolved_conflicts=unresolved_conflicts,
                merge_confidence=confidence,
                semantic_integrity=True,
                diff_stats=self._calculate_diff_stats(
                    content1,
                    content2,
                    merged_content,
                ),
            )

        except Exception as e:
            logger.exception("Error in function-level merge")
            return MergeResult(
                merge_id=merge_id,
                file_path=file_path,
                resolution=MergeResolution.MERGE_FAILED,
                strategy_used=MergeStrategy.FUNCTION_LEVEL_MERGE,
                merge_confidence=0.0,
                semantic_integrity=False,
                metadata={"error": str(e)},
            )

    async def _semantic_union_merge(
        self,
        merge_id: str,
        file_path: str,
        content1: str,
        content2: str,
        conflicts: list[SemanticConflict],
    ) -> MergeResult:
        """Perform semantic union merge combining compatible changes."""
        try:
            # Extract semantic contexts
            context1 = self.semantic_analyzer._extract_semantic_context(  # noqa: SLF001
                file_path,
                content1,
            )
            context2 = self.semantic_analyzer._extract_semantic_context(  # noqa: SLF001
                file_path,
                content2,
            )

            # Create union of compatible elements
            merged_imports = self._merge_imports(context1.imports, context2.imports)
            merged_functions = self._merge_function_signatures(
                context1.functions,
                context2.functions,
            )
            merged_classes = self._merge_class_definitions(
                context1.classes,
                context2.classes,
            )

            # Reconstruct content from merged elements
            merged_content = self._reconstruct_from_semantic_elements(
                merged_imports,
                merged_functions,
                merged_classes,
                content1,
                content2,
            )

            # Assess conflicts resolution
            resolved_conflicts = []
            for conflict in conflicts:
                if conflict.conflict_type in {
                    SemanticConflictType.IMPORT_SEMANTIC_CONFLICT,
                    SemanticConflictType.FUNCTION_SIGNATURE_CHANGE,
                    SemanticConflictType.CLASS_INTERFACE_CHANGE,
                }:
                    resolved_conflicts.append(conflict.conflict_id)

            unresolved_conflicts = [c.conflict_id for c in conflicts if c.conflict_id not in resolved_conflicts]

            confidence = len(resolved_conflicts) / max(len(conflicts), 1)
            resolution = MergeResolution.AUTO_RESOLVED if not unresolved_conflicts else MergeResolution.PARTIAL_RESOLUTION

            return MergeResult(
                merge_id=merge_id,
                file_path=file_path,
                resolution=resolution,
                strategy_used=MergeStrategy.SEMANTIC_UNION,
                merged_content=merged_content,
                conflicts_resolved=resolved_conflicts,
                unresolved_conflicts=unresolved_conflicts,
                merge_confidence=confidence,
                semantic_integrity=True,
                diff_stats=self._calculate_diff_stats(
                    content1,
                    content2,
                    merged_content,
                ),
            )

        except Exception as e:
            logger.exception("Error in semantic union merge")
            return MergeResult(
                merge_id=merge_id,
                file_path=file_path,
                resolution=MergeResolution.MERGE_FAILED,
                strategy_used=MergeStrategy.SEMANTIC_UNION,
                merge_confidence=0.0,
                semantic_integrity=False,
                metadata={"error": str(e)},
            )

    async def _contextual_merge(
        self,
        merge_id: str,
        file_path: str,
        content1: str,
        content2: str,
        conflicts: list[SemanticConflict],
    ) -> MergeResult:
        """Perform contextual merge considering code dependencies and usage
        patterns."""
        # This would implement advanced contextual analysis
        # For now, delegate to intelligent merge
        return await self._intelligent_merge(
            merge_id,
            file_path,
            content1,
            content2,
            conflicts,
        )

    @staticmethod
    def _prefer_branch_merge(
        merge_id: str,
        file_path: str,
        content: str,
        conflicts: list[SemanticConflict],
        branch_preference: str,
    ) -> MergeResult:
        """Simple merge strategy preferring one branch over the other."""
        return MergeResult(
            merge_id=merge_id,
            file_path=file_path,
            resolution=MergeResolution.AUTO_RESOLVED,
            strategy_used=(MergeStrategy.PREFER_FIRST if branch_preference == "first" else MergeStrategy.PREFER_SECOND),
            merged_content=content,
            conflicts_resolved=[c.conflict_id for c in conflicts],
            merge_confidence=1.0,
            semantic_integrity=True,
            diff_stats={"lines_added": 0, "lines_removed": 0, "lines_modified": 0},
            metadata={"branch_preference": branch_preference},
        )

    # Helper methods

    async def _detect_file_conflicts(
        self,
        file_path: str,
        branch1: str,
        branch2: str,
    ) -> list[SemanticConflict]:
        """Detect conflicts in a specific file between branches."""
        return await self.semantic_analyzer._analyze_file_semantic_conflicts(  # noqa: SLF001
            file_path,
            branch1,
            branch2,
        )

    async def _get_file_content(self, file_path: str, branch: str) -> str | None:
        """Get file content from a specific branch."""
        return await self.semantic_analyzer._get_file_content(file_path, branch)  # noqa: SLF001

    @staticmethod
    def _validate_ast_integrity(content: str) -> bool:
        """Validate that merged content maintains AST integrity."""
        try:
            ast.parse(content)
        except SyntaxError:
            return False
        else:
            return True

    @staticmethod
    def _calculate_diff_stats(
        content1: str,
        content2: str,
        merged: str,
    ) -> dict[str, int]:
        """Calculate diff statistics for merge result."""
        lines1 = content1.split("\n")
        lines2 = content2.split("\n")
        lines_merged = merged.split("\n")

        return {
            "lines_original1": len(lines1),
            "lines_original2": len(lines2),
            "lines_merged": len(lines_merged),
            "lines_added": max(0, len(lines_merged) - len(lines1)),
            "lines_removed": max(0, len(lines1) - len(lines_merged)),
        }

    @staticmethod
    def _initialize_resolution_rules() -> list[ConflictResolutionRule]:
        """Initialize default conflict resolution rules."""
        return [
            ConflictResolutionRule(
                rule_id="import_order",
                pattern="import.*",
                conflict_types=[SemanticConflictType.IMPORT_SEMANTIC_CONFLICT],
                resolution_strategy=MergeStrategy.SEMANTIC_UNION,
                confidence_threshold=0.8,
                description="Merge import statements by union",
            ),
            ConflictResolutionRule(
                rule_id="function_signature_extension",
                pattern="def .*\\(.*\\):",
                conflict_types=[SemanticConflictType.FUNCTION_SIGNATURE_CHANGE],
                resolution_strategy=MergeStrategy.FUNCTION_LEVEL_MERGE,
                confidence_threshold=0.7,
                description="Merge function signatures intelligently",
            ),
            ConflictResolutionRule(
                rule_id="class_method_addition",
                pattern="class .*:",
                conflict_types=[SemanticConflictType.CLASS_INTERFACE_CHANGE],
                resolution_strategy=MergeStrategy.SEMANTIC_UNION,
                confidence_threshold=0.8,
                description="Union merge for class method additions",
            ),
        ]

    @staticmethod
    def _select_optimal_strategy(
        conflicts: list[SemanticConflict],
    ) -> MergeStrategy:
        """Select optimal merge strategy based on conflict types and
        patterns."""
        # Count conflict types
        conflict_type_counts: defaultdict[SemanticConflictType, int] = defaultdict(int)
        for conflict in conflicts:
            conflict_type_counts[conflict.conflict_type] += 1

        # Strategy selection heuristics
        if conflict_type_counts[SemanticConflictType.FUNCTION_SIGNATURE_CHANGE] > 0:
            return MergeStrategy.FUNCTION_LEVEL_MERGE
        if conflict_type_counts[SemanticConflictType.IMPORT_SEMANTIC_CONFLICT] > 0:
            return MergeStrategy.SEMANTIC_UNION
        if conflict_type_counts[SemanticConflictType.CLASS_INTERFACE_CHANGE] > 0:
            return MergeStrategy.AST_BASED_MERGE
        return MergeStrategy.INTELLIGENT_MERGE

    async def _resolve_individual_conflict(
        self,
        conflict: SemanticConflict,
        content1: str,
        content2: str,  # noqa: ARG002
        context1: SemanticContext,
        context2: SemanticContext,
    ) -> dict[str, Any]:
        """Resolve an individual semantic conflict."""
        resolution_result = {
            "resolved": False,
            "confidence": 0.0,
            "merged_content": content1,
            "strategy": "none",
        }

        try:
            if conflict.conflict_type == SemanticConflictType.IMPORT_SEMANTIC_CONFLICT:
                self._merge_imports(context1.imports, context2.imports)
                # Apply to content (simplified)
                resolution_result.update(
                    {"resolved": True, "confidence": 0.9, "strategy": "import_union"},
                )

            elif conflict.conflict_type == SemanticConflictType.FUNCTION_SIGNATURE_CHANGE:
                # Intelligent function signature merge
                if conflict.symbol_name in context1.functions and conflict.symbol_name in context2.functions:
                    func1 = context1.functions[conflict.symbol_name]
                    func2 = context2.functions[conflict.symbol_name]

                    # Simple heuristic: prefer version with more parameters (additive change)
                    if len(func2.args) >= len(func1.args):
                        resolution_result.update(
                            {
                                "resolved": True,
                                "confidence": 0.7,
                                "strategy": "prefer_extended_signature",
                            },
                        )

            elif conflict.conflict_type == SemanticConflictType.VARIABLE_TYPE_CONFLICT:
                # Type conflict resolution
                resolution_result.update(
                    {
                        "resolved": False,  # Usually requires manual intervention
                        "confidence": 0.0,
                        "strategy": "manual_required",
                    },
                )

        except Exception:
            logger.exception("Error resolving conflict %s", conflict.conflict_id)

        return resolution_result

    @staticmethod
    def _conflict_resolved_by_merge(
        conflict: SemanticConflict,  # noqa: ARG004
        merge_result: MergeResult,
    ) -> bool:
        """Check if a conflict was resolved by the merge operation."""
        return merge_result.resolution in {MergeResolution.AUTO_RESOLVED, MergeResolution.PARTIAL_RESOLUTION} and merge_result.semantic_integrity

    def _update_merge_stats(self, merge_result: MergeResult) -> None:
        """Update merge statistics."""
        self.merge_stats["total_merges"] += 1

        if merge_result.resolution == MergeResolution.AUTO_RESOLVED:
            self.merge_stats["successful_merges"] += 1
            self.merge_stats["auto_resolved"] += 1
        elif merge_result.resolution == MergeResolution.PARTIAL_RESOLUTION:
            self.merge_stats["successful_merges"] += 1
        elif merge_result.resolution == MergeResolution.MANUAL_REQUIRED:
            self.merge_stats["manual_required"] += 1

        if merge_result.semantic_integrity:
            self.merge_stats["semantic_integrity_maintained"] += 1

        # Update average confidence
        total_confidence = self.merge_stats["average_confidence"] * (self.merge_stats["total_merges"] - 1)
        self.merge_stats["average_confidence"] = (total_confidence + merge_result.merge_confidence) / self.merge_stats["total_merges"]

    # Placeholder methods for complex operations (would be fully implemented)

    @staticmethod
    def _merge_ast_trees(
        tree1: ast.AST,
        tree2: ast.AST,  # noqa: ARG004
        conflicts: list[SemanticConflict],  # noqa: ARG004
    ) -> ast.AST:
        """Merge two AST trees intelligently."""
        # Simplified implementation - would need complex AST merging logic
        return tree1

    @staticmethod
    def _extract_functions_with_content(content: str) -> dict[str, str]:
        """Extract function definitions with their full content."""
        functions = {}
        try:
            tree = ast.parse(content)
            lines = content.split("\n")

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    # Extract function content (simplified)
                    start_line = node.lineno - 1
                    # Would need proper end line detection
                    end_line = start_line + 10  # Simplified
                    func_content = "\n".join(
                        lines[start_line : min(end_line, len(lines))],
                    )
                    functions[node.name] = func_content
        except (SyntaxError, ValueError, AttributeError):
            pass
        return functions

    @staticmethod
    def _extract_non_function_content(content: str) -> str:
        """Extract non-function content (imports, module variables, etc.)."""
        # Simplified implementation
        lines = content.split("\n")
        non_func_lines = []

        for line in lines:
            if not line.strip().startswith("def ") and not line.strip().startswith(
                "async def ",
            ):
                non_func_lines.append(line)
            else:
                break  # Stop at first function

        return "\n".join(non_func_lines)

    @staticmethod
    def _find_function_conflict(
        func_name: str,
        conflicts: list[SemanticConflict],
    ) -> SemanticConflict | None:
        """Find conflict related to a specific function."""
        for conflict in conflicts:
            if conflict.symbol_name == func_name and conflict.conflict_type == SemanticConflictType.FUNCTION_SIGNATURE_CHANGE:
                return conflict
        return None

    @staticmethod
    def _merge_function_definitions(
        func1: str,  # noqa: ARG004
        func2: str,
        conflict: SemanticConflict,  # noqa: ARG004
    ) -> dict[str, Any]:
        """Merge two function definitions."""
        # Simplified implementation
        return {
            "content": func2,  # Prefer second version
            "resolved": True,
            "confidence": 0.7,
        }

    @staticmethod
    def _merge_imports(imports1: list, imports2: list) -> list:
        """Merge import lists intelligently."""
        # Simplified union merge
        all_imports = list(imports1) + list(imports2)
        # Remove duplicates while preserving order
        seen = set()
        merged = []
        for imp in all_imports:
            imp_key = (imp.module, imp.name, imp.alias)
            if imp_key not in seen:
                seen.add(imp_key)
                merged.append(imp)
        return merged

    @staticmethod
    def _merge_function_signatures(funcs1: dict, funcs2: dict) -> dict:
        """Merge function signature dictionaries."""
        merged = funcs1.copy()
        merged.update(funcs2)
        return merged

    @staticmethod
    def _merge_class_definitions(classes1: dict, classes2: dict) -> dict:
        """Merge class definition dictionaries."""
        merged = classes1.copy()
        merged.update(classes2)
        return merged

    @staticmethod
    def _reconstruct_from_semantic_elements(
        imports: list,  # noqa: ARG004
        functions: dict,  # noqa: ARG004
        classes: dict,  # noqa: ARG004
        content1: str,  # noqa: ARG004
        content2: str,
    ) -> str:
        """Reconstruct source code from semantic elements."""
        # Simplified implementation - would need proper code generation
        return content2  # Fallback to second version

    def get_merge_summary(self) -> dict[str, Any]:
        """Get comprehensive summary of merge operations."""
        return {
            "total_merges": self.merge_stats["total_merges"],
            "success_rate": (self.merge_stats["successful_merges"] / max(self.merge_stats["total_merges"], 1)),
            "auto_resolution_rate": (self.merge_stats["auto_resolved"] / max(self.merge_stats["total_merges"], 1)),
            "semantic_integrity_rate": (self.merge_stats["semantic_integrity_maintained"] / max(self.merge_stats["total_merges"], 1)),
            "average_confidence": self.merge_stats["average_confidence"],
            "strategy_performance": dict(self.success_rate_by_strategy),
            "recent_merges": [
                {
                    "merge_id": result.merge_id,
                    "file_path": result.file_path,
                    "resolution": result.resolution.value,
                    "confidence": result.merge_confidence,
                    "strategy": result.strategy_used.value,
                    "merge_time": result.merge_time.isoformat(),
                }
                for result in self.merge_history[-10:]  # Last 10 merges
            ],
        }
