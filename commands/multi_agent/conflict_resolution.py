"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Conflict detection and resolution commands."""

import asyncio
import logging

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from libs.core.base_command import BaseCommand, CommandError
from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.conflict_resolution import ConflictResolutionEngine

logger = logging.getLogger(__name__)


class DetectConflictsCommand(BaseCommand):
    """Detect conflicts between branches."""

    def execute(self, **kwargs) -> dict:
        """Execute the command."""
        # Extract parameters from kwargs

        branches = kwargs["branches"]

        repo_path = kwargs.get("repo_path")

        auto_resolve = kwargs.get("auto_resolve", False)
        """Execute the detect conflicts command."""
        try:
            # Create progress indicator for conflict detection
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold yellow]{task.description}"),
                TimeElapsedColumn(),
                transient=True,
            ) as progress:
                detection_task = progress.add_task(
                    f"🔍 Detecting conflicts between branches: {', '.join(branches)}",
                    total=None,
                )

                # Create conflict resolution engine
                branch_manager = BranchManager(repo_path=repo_path)
                engine = ConflictResolutionEngine(branch_manager, repo_path)

                async def run_detection():
                    conflicts = await engine.detect_potential_conflicts(branches)
                    progress.update(detection_task, description="✅ Conflict detection completed")

                    if not conflicts:
                        self.print_success("✅ No conflicts detected")
                        return {
                            "success": True,
                            "branches": branches,
                            "repo_path": repo_path,
                            "conflicts": [],
                            "auto_resolve_results": None,
                        }

                    self.print_info(f"⚠️  Found {len(conflicts)} potential conflicts:")
                    self.print_info("=" * 60)

                    for conflict in conflicts:
                        severity_icon = {
                            "low": "🟢",
                            "medium": "🟡",
                            "high": "🔴",
                            "critical": "💀",
                        }.get(conflict.severity.value, "❓")

                        self.print_info(f"{severity_icon} {conflict.conflict_id}")
                        self.print_info(f"   Type: {conflict.conflict_type.value}")
                        self.print_info(f"   Severity: {conflict.severity.value}")
                        self.print_info(f"   Branches: {', '.join(conflict.branches)}")
                        self.print_info(f"   Files: {', '.join(conflict.files)}")
                        self.print_info(f"   Description: {conflict.description}")
                        self.print_info(f"   Suggested Strategy: {conflict.suggested_strategy.value}")
                        self.print_info("")

                    auto_resolve_results = None
                    # Auto-resolve if requested
                    if auto_resolve:
                        self.print_info("🔧 Attempting automatic resolution...")
                        results = await engine.auto_resolve_all()
                        resolved = len([r for r in results if r.success])
                        failed = len(results) - resolved

                        self.print_success(f"✅ Auto-resolved: {resolved}")
                        if failed > 0:
                            self.print_error(f"❌ Failed to resolve: {failed}")
                            self.print_warning("🚨 Manual intervention required for remaining conflicts")

                        auto_resolve_results = {
                            "resolved": resolved,
                            "failed": failed,
                            "results": results,
                        }

                    return {
                        "success": True,
                        "branches": branches,
                        "repo_path": repo_path,
                        "conflicts": conflicts,
                        "auto_resolve_results": auto_resolve_results,
                    }

                return asyncio.run(run_detection())

        except Exception as e:
            msg = f"Error detecting conflicts: {e}"
            raise CommandError(msg) from e


class ResolveConflictCommand(BaseCommand):
    """Resolve a specific conflict."""

    def execute(self, **kwargs) -> dict:
        """Execute the command."""
        # Extract parameters from kwargs

        conflict_id = kwargs["conflict_id"]

        strategy = kwargs.get("strategy")

        repo_path = kwargs.get("repo_path")
        """Execute the resolve conflict command."""
        try:
            self.print_info(f"🔧 Resolving conflict: {conflict_id}")

            # Create conflict resolution engine
            branch_manager = BranchManager(repo_path=repo_path)
            engine = ConflictResolutionEngine(branch_manager, repo_path)

            # Convert strategy string to enum
            resolution_strategy = None
            if strategy:
                try:
                    from libs.multi_agent.conflict_resolution import ResolutionStrategy

                    resolution_strategy = ResolutionStrategy(strategy)
                except ValueError as e:
                    msg = f"Invalid strategy: {strategy}"
                    raise CommandError(
                        msg,
                        recovery_hint="Valid strategies: auto_merge, prefer_latest, prefer_main, custom_merge, semantic_analysis",
                    ) from e

            async def run_resolution():
                result = await engine.resolve_conflict(conflict_id, resolution_strategy)

                if result.success:
                    self.print_success("✅ Conflict resolved successfully!")
                    self.print_info(f"   Strategy used: {result.strategy_used.value}")
                    self.print_info(f"   Resolution time: {result.resolution_time:.2f}s")
                    self.print_info(f"   Message: {result.message}")
                    if result.resolved_files:
                        self.print_info(f"   Resolved files: {', '.join(result.resolved_files)}")
                else:
                    self.print_error("❌ Failed to resolve conflict")
                    self.print_info(f"   Strategy attempted: {result.strategy_used.value}")
                    self.print_info(f"   Error: {result.message}")
                    if result.remaining_conflicts:
                        self.print_info(f"   Remaining conflicts: {', '.join(result.remaining_conflicts)}")

                return {
                    "success": result.success,
                    "conflict_id": conflict_id,
                    "strategy": strategy,
                    "repo_path": repo_path,
                    "strategy_used": result.strategy_used.value if result.strategy_used else None,
                    "resolution_time": result.resolution_time,
                    "message": result.message,
                    "resolved_files": result.resolved_files,
                    "remaining_conflicts": result.remaining_conflicts,
                }

            return asyncio.run(run_resolution())

        except Exception as e:
            msg = f"Error resolving conflict: {e}"
            raise CommandError(msg) from e


class ConflictSummaryCommand(BaseCommand):
    """Show conflict resolution summary and statistics."""

    def execute(self, **kwargs) -> dict:
        """Execute the command."""
        # Extract parameters from kwargs

        repo_path = kwargs.get("repo_path")
        """Execute the conflict summary command."""
        try:
            self.print_info("📊 Conflict Resolution Summary")
            self.print_info("=" * 40)

            # Create conflict resolution engine
            branch_manager = BranchManager(repo_path=repo_path)
            engine = ConflictResolutionEngine(branch_manager, repo_path)

            summary = engine.get_conflict_summary()

            # Overall statistics
            self.print_info(f"Total Conflicts: {summary['total_conflicts']}")
            self.print_info(f"Resolved: {summary['resolved_conflicts']}")
            self.print_info(f"Unresolved: {summary['unresolved_conflicts']}")
            self.print_info(f"Resolution Rate: {summary['resolution_rate']:.1%}")

            # Severity breakdown
            if summary["severity_breakdown"]:
                self.print_info("\n📈 Severity Breakdown:")
                for severity, count in summary["severity_breakdown"].items():
                    if count > 0:
                        severity_icon = {
                            "low": "🟢",
                            "medium": "🟡",
                            "high": "🔴",
                            "critical": "💀",
                        }.get(severity, "❓")
                        self.print_info(f"  {severity_icon} {severity.capitalize()}: {count}")

            # Type breakdown
            if summary["type_breakdown"]:
                self.print_info("\n🏷️  Type Breakdown:")
                for conflict_type, count in summary["type_breakdown"].items():
                    if count > 0:
                        type_icon = {
                            "file_modification": "📝",
                            "file_deletion": "🗑️",
                            "file_creation": "📄",
                            "semantic": "🧠",
                            "dependency": "🔗",
                            "merge_conflict": "⚡",
                        }.get(conflict_type, "❓")
                        self.print_info(f"  {type_icon} {conflict_type.replace('_', ' ').title()}: {count}")

            # Resolution statistics
            stats = summary["resolution_stats"]
            if stats["total_conflicts"] > 0:
                self.print_info("\n⚡ Resolution Statistics:")
                self.print_info(f"  Auto-resolved: {stats['auto_resolved']}")
                self.print_info(f"  Human required: {stats['human_required']}")
                self.print_info(f"  Success rate: {stats['resolution_success_rate']:.1%}")
                self.print_info(f"  Average time: {stats['average_resolution_time']:.2f}s")

            return {"success": True, "repo_path": repo_path, "summary": summary}

        except Exception as e:
            msg = f"Error getting conflict summary: {e}"
            raise CommandError(msg) from e
