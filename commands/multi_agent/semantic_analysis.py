"""Semantic analysis and merging commands."""

import asyncio
import logging

from libs.core.base_command import BaseCommand, CommandError
from libs.multi_agent.semantic_analyzer import SemanticAnalyzer
from libs.multi_agent.semantic_merger import SemanticMerger

logger = logging.getLogger(__name__)


class AnalyzeSemanticConflictsCommand(BaseCommand):
    """Analyze AST-based semantic conflicts."""

    def execute(
        self,
        files: list[str],
        language: str = "python",
        repo_path: str | None = None,
        **kwargs,
    ) -> dict:
        """Execute the analyze semantic conflicts command."""
        try:
            self.print_info(f"🧠 Analyzing semantic conflicts in {len(files)} files...")
            self.print_info(f"   Language: {language}")

            analyzer = SemanticAnalyzer(language=language, repo_path=repo_path)

            async def run_analysis():
                conflicts = await analyzer.analyze_semantic_conflicts(files)

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
                    }.get(conflict.severity, "❓")

                    self.print_info(f"{severity_icon} {conflict.conflict_type}")
                    self.print_info(f"   File: {conflict.file_path}")
                    self.print_info(f"   Lines: {conflict.line_start}-{conflict.line_end}")
                    self.print_info(f"   Description: {conflict.description}")
                    self.print_info(f"   Suggestion: {conflict.suggestion}")
                    self.print_info("")

                return {
                    "success": True,
                    "files": files,
                    "language": language,
                    "conflicts": conflicts,
                }

            return asyncio.run(run_analysis())

        except Exception as e:
            raise CommandError(f"Error analyzing semantic conflicts: {e}") from e


class SemanticSummaryCommand(BaseCommand):
    """Show semantic analysis summary."""

    def execute(self, repo_path: str | None = None, **kwargs) -> dict:
        """Execute the semantic summary command."""
        try:
            self.print_info("🧠 Semantic Analysis Summary")
            self.print_info("=" * 40)

            analyzer = SemanticAnalyzer(repo_path=repo_path)
            summary = analyzer.get_analysis_summary()

            self.print_info(f"Files Analyzed: {summary['files_analyzed']}")
            self.print_info(f"Semantic Conflicts: {summary['semantic_conflicts']}")
            self.print_info(f"Function Conflicts: {summary['function_conflicts']}")
            self.print_info(f"Class Conflicts: {summary['class_conflicts']}")

            return {"success": True, "repo_path": repo_path, "summary": summary}

        except Exception as e:
            raise CommandError(f"Error getting semantic summary: {e}") from e


class FunctionDiffCommand(BaseCommand):
    """Show function-level differences."""

    def execute(self, file1: str, file2: str, language: str = "python", **kwargs) -> dict:
        """Execute the function diff command."""
        try:
            self.print_info(f"🔍 Function-level diff: {file1} vs {file2}")

            analyzer = SemanticAnalyzer(language=language)
            diff = analyzer.get_function_diff(file1, file2)

            self.print_info("📋 Function Differences:")
            self.print_info("=" * 50)

            for func_diff in diff.function_differences:
                self.print_info(f"📝 Function: {func_diff.function_name}")
                self.print_info(f"   Change Type: {func_diff.change_type}")
                self.print_info(f"   Description: {func_diff.description}")
                self.print_info("")

            return {"success": True, "file1": file1, "file2": file2, "diff": diff}

        except Exception as e:
            raise CommandError(f"Error getting function diff: {e}") from e


class SemanticMergeCommand(BaseCommand):
    """Perform semantic merging of code."""

    def execute(
        self,
        source_file: str,
        target_file: str,
        language: str = "python",
        strategy: str = "auto",
        **kwargs,
    ) -> dict:
        """Execute the semantic merge command."""
        try:
            self.print_info(f"🔀 Semantic merge: {source_file} → {target_file}")
            self.print_info(f"   Strategy: {strategy}")

            merger = SemanticMerger(language=language)

            # Convert strategy string to enum
            from libs.multi_agent.semantic_merger import MergeStrategy

            merge_strategy = MergeStrategy(strategy)

            async def run_merge():
                result = await merger.merge_files(source_file, target_file, merge_strategy)

                if result.success:
                    self.print_success("✅ Semantic merge completed successfully!")
                    self.print_info(f"   Merged functions: {len(result.merged_functions)}")
                    self.print_info(f"   Conflicts resolved: {len(result.resolved_conflicts)}")
                    if result.remaining_conflicts:
                        self.print_warning(f"   Manual review needed: {len(result.remaining_conflicts)} conflicts")
                else:
                    self.print_error("❌ Semantic merge failed")
                    self.print_info(f"   Error: {result.error_message}")

                return {
                    "success": result.success,
                    "source_file": source_file,
                    "target_file": target_file,
                    "strategy": strategy,
                    "merged_functions": result.merged_functions,
                    "resolved_conflicts": result.resolved_conflicts,
                    "remaining_conflicts": result.remaining_conflicts,
                    "error_message": result.error_message,
                }

            return asyncio.run(run_merge())

        except Exception as e:
            raise CommandError(f"Error performing semantic merge: {e}") from e
