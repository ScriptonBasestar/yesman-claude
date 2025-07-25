# Copyright notice.

import asyncio
import logging
from typing import Any

from libs.core.base_command import BaseCommand, CommandError
from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.conflict_resolution import ConflictResolutionEngine
from libs.multi_agent.semantic_analyzer import SemanticAnalyzer
from libs.multi_agent.semantic_merger import MergeStrategy, SemanticMerger

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Semantic analysis and merging commands."""


logger = logging.getLogger(__name__)

# Constants for magic number replacements
MIN_BRANCHES_FOR_ANALYSIS = 2


class AnalyzeSemanticConflictsCommand(BaseCommand):
    """Analyze AST-based semantic conflicts."""

    def execute(
        self,
        files: list[str] | None = None,
        language: str = "python",
        repo_path: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute the analyze semantic conflicts command.

        Returns:
        object: Description of return value.
        """
        try:
            # Handle files parameter from kwargs if not provided as positional argument
            if files is None:
                files = kwargs.get("files", [])

            if not files:
                msg = "Files parameter is required for conflict analysis"
                raise CommandError(msg)

            self.print_info(f"🧠 Analyzing semantic conflicts in {len(files)} files...")
            self.print_info(f"   Language: {language}")

            branch_manager = BranchManager(repo_path or ".")
            analyzer = SemanticAnalyzer(branch_manager=branch_manager, repo_path=repo_path)

            async def run_analysis() -> dict[str, Any]:
                # For semantic conflict analysis, we need branches
                if len(files) < MIN_BRANCHES_FOR_ANALYSIS:
                    msg = "At least 2 branches are required for conflict analysis"
                    raise CommandError(msg)

                branch1, branch2 = files[0], files[1]
                file_paths = files[MIN_BRANCHES_FOR_ANALYSIS:] if len(files) > MIN_BRANCHES_FOR_ANALYSIS else None

                conflicts = await analyzer.analyze_semantic_conflicts(branch1, branch2, file_paths)

                if not conflicts:
                    self.print_success("✅ No semantic conflicts detected")
                    return {
                        "success": True,
                        "files": files,
                        "language": language,
                        "conflicts": [],
                    }

                self.print_info(f"⚠️  Found {len(conflicts)} semantic conflicts:")
                self.print_info("=" * 60)

                for conflict in conflicts:
                    severity_icon = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🔴",
                        "critical": "💀",
                    }.get(
                        (conflict.severity.value if hasattr(conflict.severity, "value") else str(conflict.severity)),
                        "❓",
                    )

                    self.print_info(f"{severity_icon} {conflict.conflict_type}")
                    self.print_info(f"   File: {conflict.file_path}")
                    self.print_info(f"   Description: {conflict.description}")
                    if hasattr(conflict, "suggested_resolution"):
                        self.print_info(f"   Suggestion: {conflict.suggested_resolution}")
                    self.print_info("")

                return {
                    "success": True,
                    "files": files,
                    "language": language,
                    "conflicts": conflicts,
                }

            return asyncio.run(run_analysis())

        except Exception as e:
            msg = f"Error analyzing semantic conflicts: {e}"
            raise CommandError(msg) from e


class SemanticSummaryCommand(BaseCommand):
    """Show semantic analysis summary."""

    def execute(self, repo_path: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Execute the semantic summary command.

        Returns:
        object: Description of return value.
        """
        try:
            self.print_info("🧠 Semantic Analysis Summary")
            self.print_info("=" * 40)

            branch_manager = BranchManager(repo_path or ".")
            analyzer = SemanticAnalyzer(branch_manager=branch_manager, repo_path=repo_path)
            summary = analyzer.get_analysis_summary()

            self.print_info(f"Files Analyzed: {summary['files_analyzed']}")
            self.print_info(f"Semantic Conflicts: {summary['semantic_conflicts']}")
            self.print_info(f"Function Conflicts: {summary['function_conflicts']}")
            self.print_info(f"Class Conflicts: {summary['class_conflicts']}")

            return {"success": True, "repo_path": repo_path, "summary": summary}

        except Exception as e:
            msg = f"Error getting semantic summary: {e}"
            raise CommandError(msg) from e


class FunctionDiffCommand(BaseCommand):
    """Show function-level differences."""

    def execute(
        self,
        file1: str | None = None,
        file2: str | None = None,
        language: str = "python",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute the function diff command.

        Returns:
        object: Description of return value.
        """
        try:
            # Handle file parameters from kwargs if not provided as positional arguments
            if file1 is None:
                file1 = kwargs.get("file1")
            if file2 is None:
                file2 = kwargs.get("file2")

            if not file1 or not file2:
                msg = "Both file1 and file2 parameters are required"
                raise CommandError(msg)

            self.print_info(f"🔍 Function-level diff: {file1} vs {file2}")

            branch_manager = BranchManager(".")
            SemanticAnalyzer(branch_manager=branch_manager)

            # Since get_function_diff doesn't exist, create basic diff info
            diff: dict[str, Any] = {
                "file1": file1,
                "file2": file2,
                "function_differences": [],
                "summary": f"Function differences between {file1} and {file2}",
            }

            self.print_info("📋 Function Differences:")
            self.print_info("=" * 50)

            if diff["function_differences"]:
                for func_diff in diff["function_differences"]:
                    func_name = func_diff.get("function_name", "Unknown") if isinstance(func_diff, dict) else str(func_diff)
                    change_type = func_diff.get("change_type", "Unknown") if isinstance(func_diff, dict) else "Unknown"
                    description = func_diff.get("description", "No description") if isinstance(func_diff, dict) else "No description"

                    self.print_info(f"📝 Function: {func_name}")
                    self.print_info(f"   Change Type: {change_type}")
                    self.print_info(f"   Description: {description}")
                    self.print_info("")
            else:
                self.print_info("No function differences available in current implementation")

            return {"success": True, "file1": file1, "file2": file2, "diff": diff}

        except Exception as e:
            msg = f"Error getting function diff: {e}"
            raise CommandError(msg) from e


class SemanticMergeCommand(BaseCommand):
    """Perform semantic merging of code."""

    def execute(
        self,
        source_file: str | None = None,
        target_file: str | None = None,
        language: str = "python",
        strategy: str = "auto",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute the semantic merge command.

        Returns:
        object: Description of return value.
        """
        try:
            # Handle file parameters from kwargs if not provided as positional arguments
            if source_file is None:
                source_file = kwargs.get("source_file")
            if target_file is None:
                target_file = kwargs.get("target_file")

            if not source_file or not target_file:
                msg = "Both source_file and target_file parameters are required"
                raise CommandError(msg)

            self.print_info(f"🔀 Semantic merge: {source_file} → {target_file}")
            self.print_info(f"   Strategy: {strategy}")

            branch_manager = BranchManager(".")
            analyzer = SemanticAnalyzer(branch_manager=branch_manager)
            conflict_engine = ConflictResolutionEngine(branch_manager=branch_manager)
            merger = SemanticMerger(
                semantic_analyzer=analyzer,
                conflict_engine=conflict_engine,
                branch_manager=branch_manager,
            )

            # Convert strategy string to enum if possible
            try:
                merge_strategy = MergeStrategy(strategy)
            except ValueError:
                merge_strategy = MergeStrategy.INTELLIGENT_MERGE  # Default fallback

            async def run_merge() -> dict[str, Any]:
                result = await merger.perform_semantic_merge(
                    file_path=target_file,
                    branch1="current",
                    branch2="other",
                    strategy=merge_strategy,
                )

                success = result.resolution.value in {
                    "auto_resolved",
                    "partial_resolution",
                }
                if success:
                    self.print_success("✅ Semantic merge completed successfully!")
                    self.print_info(f"   Resolution: {result.resolution.value}")
                    self.print_info(f"   Conflicts resolved: {len(result.conflicts_resolved)}")
                    if result.unresolved_conflicts:
                        self.print_warning(f"   Manual review needed: {len(result.unresolved_conflicts)} conflicts")
                else:
                    self.print_error("❌ Semantic merge failed")
                    self.print_info(f"   Resolution: {result.resolution.value}")

                return {
                    "success": success,
                    "source_file": source_file,
                    "target_file": target_file,
                    "strategy": strategy,
                    "resolution": result.resolution.value,
                    "resolved_conflicts": result.conflicts_resolved,
                    "remaining_conflicts": result.unresolved_conflicts,
                }

            return asyncio.run(run_merge())

        except Exception as e:
            msg = f"Error performing semantic merge: {e}"
            raise CommandError(msg) from e
