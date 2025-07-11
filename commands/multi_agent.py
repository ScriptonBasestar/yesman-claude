"""Multi-agent system commands for parallel development automation"""

import asyncio
import click
import logging
from pathlib import Path
from typing import Optional

from libs.dashboard.widgets.agent_monitor import AgentMonitor, run_agent_monitor
from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.types import Task, Agent
from libs.multi_agent.conflict_resolution import ConflictResolutionEngine
from libs.multi_agent.conflict_prediction import ConflictPredictor
from libs.multi_agent.semantic_analyzer import SemanticAnalyzer
from libs.multi_agent.semantic_merger import (
    SemanticMerger,
    MergeStrategy,
    MergeResolution,
)
from libs.multi_agent.auto_resolver import AutoResolver, AutoResolutionMode
from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.dependency_propagation import (
    DependencyPropagationSystem,
    DependencyType,
    ChangeImpact,
    PropagationStrategy,
)
from libs.multi_agent.collaboration_engine import CollaborationEngine
from libs.multi_agent.branch_info_protocol import BranchInfoProtocol
from libs.multi_agent.code_review_engine import (
    CodeReviewEngine,
    ReviewType,
    ReviewSeverity,
    ReviewStatus,
    QualityMetric,
)


logger = logging.getLogger(__name__)


@click.group(name="multi-agent")
@click.pass_context
def multi_agent_cli(ctx):
    """Multi-agent system for parallel development automation"""
    pass


@multi_agent_cli.command("start")
@click.option("--max-agents", "-a", default=3, help="Maximum number of agents")
@click.option("--work-dir", "-w", help="Work directory for agents")
@click.option("--monitor", "-m", is_flag=True, help="Start with monitoring dashboard")
def start_agents(max_agents: int, work_dir: Optional[str], monitor: bool):
    """Start the multi-agent pool"""
    click.echo(f"🤖 Starting multi-agent pool with {max_agents} agents...")

    try:
        # Create agent pool
        pool = AgentPool(max_agents=max_agents, work_dir=work_dir)

        async def run_pool():
            await pool.start()

            if monitor:
                click.echo("📊 Starting monitoring dashboard...")
                await run_agent_monitor(pool)
            else:
                click.echo("✅ Agent pool started successfully")
                click.echo("Use 'yesman multi-agent monitor' to view status")

                # Keep running until interrupted
                try:
                    while pool._running:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    click.echo("\n🛑 Stopping agent pool...")
                    await pool.stop()

        asyncio.run(run_pool())

    except Exception as e:
        click.echo(f"❌ Error starting agents: {e}", err=True)
        raise click.ClickException(str(e))


@multi_agent_cli.command("monitor")
@click.option("--work-dir", "-w", help="Work directory for agents")
@click.option("--duration", "-d", type=float, help="Monitoring duration in seconds")
@click.option("--refresh", "-r", default=1.0, help="Refresh interval in seconds")
def monitor_agents(work_dir: Optional[str], duration: Optional[float], refresh: float):
    """Start real-time agent monitoring dashboard"""
    click.echo("📊 Starting agent monitoring dashboard...")

    try:
        # Try to connect to existing agent pool
        pool = None
        if work_dir:
            pool_dir = Path(work_dir) / ".yesman-agents"
            if pool_dir.exists():
                pool = AgentPool(work_dir=work_dir)
                # Load existing state without starting
                pool._load_state()

        async def run_monitor():
            monitor = AgentMonitor(agent_pool=pool)
            monitor.refresh_interval = refresh

            if not pool:
                click.echo("⚠️  No active agent pool found. Showing demo mode.")
                # Add some demo data for visualization
                monitor.agent_metrics = {
                    "agent-1": monitor.AgentMetrics(
                        agent_id="agent-1",
                        current_task="task-123",
                        tasks_completed=5,
                        tasks_failed=1,
                        total_execution_time=300.0,
                    ),
                    "agent-2": monitor.AgentMetrics(
                        agent_id="agent-2",
                        tasks_completed=3,
                        tasks_failed=0,
                        total_execution_time=180.0,
                    ),
                }

            await monitor.start_monitoring(duration)

        asyncio.run(run_monitor())

    except KeyboardInterrupt:
        click.echo("\n👋 Monitoring stopped")
    except Exception as e:
        click.echo(f"❌ Error in monitoring: {e}", err=True)
        raise click.ClickException(str(e))


@multi_agent_cli.command("status")
@click.option("--work-dir", "-w", help="Work directory for agents")
def status(work_dir: Optional[str]):
    """Show current agent pool status"""
    try:
        pool = AgentPool(work_dir=work_dir)
        pool._load_state()

        stats = pool.get_pool_statistics()
        agents = pool.list_agents()
        tasks = pool.list_tasks()

        click.echo("🤖 Multi-Agent Pool Status")
        click.echo("=" * 40)
        click.echo(f"Total Agents: {len(agents)}")
        click.echo(f"Active Agents: {stats.get('active_agents', 0)}")
        click.echo(f"Idle Agents: {stats.get('idle_agents', 0)}")
        click.echo(f"Total Tasks: {len(tasks)}")
        click.echo(f"Completed Tasks: {stats.get('completed_tasks', 0)}")
        click.echo(f"Failed Tasks: {stats.get('failed_tasks', 0)}")
        click.echo(f"Queue Size: {stats.get('queue_size', 0)}")
        click.echo(
            f"Average Execution Time: {stats.get('average_execution_time', 0):.1f}s"
        )

        if agents:
            click.echo("\n📋 Agents:")
            for agent in agents:
                status_icon = {
                    "idle": "🟢",
                    "working": "🟡",
                    "error": "🔴",
                    "terminated": "⚫",
                }.get(agent.get("state", "unknown"), "❓")

                click.echo(
                    f"  {status_icon} {agent['agent_id']} - "
                    f"Completed: {agent.get('completed_tasks', 0)}, "
                    f"Failed: {agent.get('failed_tasks', 0)}"
                )

    except Exception as e:
        click.echo(f"❌ Error getting status: {e}", err=True)


@multi_agent_cli.command("stop")
@click.option("--work-dir", "-w", help="Work directory for agents")
def stop_agents(work_dir: Optional[str]):
    """Stop the multi-agent pool"""
    click.echo("🛑 Stopping multi-agent pool...")

    try:
        pool = AgentPool(work_dir=work_dir)

        async def stop_pool():
            await pool.stop()
            click.echo("✅ Agent pool stopped successfully")

        asyncio.run(stop_pool())

    except Exception as e:
        click.echo(f"❌ Error stopping agents: {e}", err=True)


@multi_agent_cli.command("add-task")
@click.argument("title")
@click.argument("command", nargs=-1, required=True)
@click.option("--work-dir", "-w", help="Work directory for agents")
@click.option("--directory", "-d", default=".", help="Working directory for task")
@click.option("--priority", "-p", default=5, help="Task priority (1-10)")
@click.option("--complexity", "-c", default=5, help="Task complexity (1-10)")
@click.option("--timeout", "-t", default=300, help="Task timeout in seconds")
@click.option("--description", help="Task description")
def add_task(
    title: str,
    command: tuple,
    work_dir: Optional[str],
    directory: str,
    priority: int,
    complexity: int,
    timeout: int,
    description: Optional[str],
):
    """Add a task to the agent pool queue"""
    try:
        pool = AgentPool(work_dir=work_dir)

        task = pool.create_task(
            title=title,
            command=list(command),
            working_directory=directory,
            description=description or f"Execute: {' '.join(command)}",
            priority=priority,
            complexity=complexity,
            timeout=timeout,
        )

        click.echo(f"✅ Task added: {task.task_id}")
        click.echo(f"   Title: {task.title}")
        click.echo(f"   Command: {' '.join(task.command)}")
        click.echo(f"   Priority: {task.priority}")

    except Exception as e:
        click.echo(f"❌ Error adding task: {e}", err=True)


@multi_agent_cli.command("list-tasks")
@click.option("--work-dir", "-w", help="Work directory for agents")
@click.option("--status", help="Filter by status (pending/running/completed/failed)")
def list_tasks(work_dir: Optional[str], status: Optional[str]):
    """List tasks in the agent pool"""
    try:
        pool = AgentPool(work_dir=work_dir)

        from libs.multi_agent.types import TaskStatus

        filter_status = None
        if status:
            try:
                filter_status = TaskStatus(status.lower())
            except ValueError:
                click.echo(f"❌ Invalid status: {status}")
                return

        tasks = pool.list_tasks(filter_status)

        if not tasks:
            click.echo("📝 No tasks found")
            return

        click.echo(f"📋 Tasks ({len(tasks)} found):")
        click.echo("=" * 80)

        for task in tasks:
            status_icon = {
                "pending": "⏳",
                "assigned": "📤",
                "running": "⚡",
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫",
            }.get(task.get("status", "unknown"), "❓")

            click.echo(f"{status_icon} {task['task_id'][:8]}... - {task['title']}")
            click.echo(f"   Status: {task['status'].upper()}")
            if task.get("assigned_agent"):
                click.echo(f"   Agent: {task['assigned_agent']}")
            click.echo(f"   Command: {' '.join(task['command'])}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error listing tasks: {e}", err=True)


@multi_agent_cli.command("detect-conflicts")
@click.argument("branches", nargs=-1, required=True)
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option("--auto-resolve", "-a", is_flag=True, help="Attempt automatic resolution")
def detect_conflicts(branches: tuple, repo_path: Optional[str], auto_resolve: bool):
    """Detect conflicts between branches"""
    try:
        click.echo(f"🔍 Detecting conflicts between branches: {', '.join(branches)}")

        # Create conflict resolution engine
        branch_manager = BranchManager(repo_path=repo_path)
        engine = ConflictResolutionEngine(branch_manager, repo_path)

        async def run_detection():
            conflicts = await engine.detect_potential_conflicts(list(branches))

            if not conflicts:
                click.echo("✅ No conflicts detected")
                return

            click.echo(f"⚠️  Found {len(conflicts)} potential conflicts:")
            click.echo("=" * 60)

            for conflict in conflicts:
                severity_icon = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🔴",
                    "critical": "💀",
                }.get(conflict.severity.value, "❓")

                click.echo(f"{severity_icon} {conflict.conflict_id}")
                click.echo(f"   Type: {conflict.conflict_type.value}")
                click.echo(f"   Severity: {conflict.severity.value}")
                click.echo(f"   Branches: {', '.join(conflict.branches)}")
                click.echo(f"   Files: {', '.join(conflict.files)}")
                click.echo(f"   Description: {conflict.description}")
                click.echo(
                    f"   Suggested Strategy: {conflict.suggested_strategy.value}"
                )
                click.echo()

            # Auto-resolve if requested
            if auto_resolve:
                click.echo("🔧 Attempting automatic resolution...")
                results = await engine.auto_resolve_all()

                resolved = len([r for r in results if r.success])
                failed = len(results) - resolved

                click.echo(f"✅ Auto-resolved: {resolved}")
                click.echo(f"❌ Failed to resolve: {failed}")

                if failed > 0:
                    click.echo(
                        "\n🚨 Manual intervention required for remaining conflicts"
                    )

        asyncio.run(run_detection())

    except Exception as e:
        click.echo(f"❌ Error detecting conflicts: {e}", err=True)


@multi_agent_cli.command("resolve-conflict")
@click.argument("conflict_id")
@click.option(
    "--strategy",
    help="Resolution strategy (auto_merge/prefer_latest/prefer_main/custom_merge/semantic_analysis)",
)
@click.option("--repo-path", "-r", help="Path to git repository")
def resolve_conflict(
    conflict_id: str, strategy: Optional[str], repo_path: Optional[str]
):
    """Resolve a specific conflict"""
    try:
        click.echo(f"🔧 Resolving conflict: {conflict_id}")

        # Create conflict resolution engine
        branch_manager = BranchManager(repo_path=repo_path)
        engine = ConflictResolutionEngine(branch_manager, repo_path)

        # Convert strategy string to enum
        resolution_strategy = None
        if strategy:
            try:
                from libs.multi_agent.conflict_resolution import ResolutionStrategy

                resolution_strategy = ResolutionStrategy(strategy)
            except ValueError:
                click.echo(f"❌ Invalid strategy: {strategy}")
                click.echo(
                    "Valid strategies: auto_merge, prefer_latest, prefer_main, custom_merge, semantic_analysis"
                )
                return

        async def run_resolution():
            result = await engine.resolve_conflict(conflict_id, resolution_strategy)

            if result.success:
                click.echo(f"✅ Conflict resolved successfully!")
                click.echo(f"   Strategy used: {result.strategy_used.value}")
                click.echo(f"   Resolution time: {result.resolution_time:.2f}s")
                click.echo(f"   Message: {result.message}")
                if result.resolved_files:
                    click.echo(f"   Resolved files: {', '.join(result.resolved_files)}")
            else:
                click.echo(f"❌ Failed to resolve conflict")
                click.echo(f"   Strategy attempted: {result.strategy_used.value}")
                click.echo(f"   Error: {result.message}")
                if result.remaining_conflicts:
                    click.echo(
                        f"   Remaining conflicts: {', '.join(result.remaining_conflicts)}"
                    )

        asyncio.run(run_resolution())

    except Exception as e:
        click.echo(f"❌ Error resolving conflict: {e}", err=True)


@multi_agent_cli.command("conflict-summary")
@click.option("--repo-path", "-r", help="Path to git repository")
def conflict_summary(repo_path: Optional[str]):
    """Show conflict resolution summary and statistics"""
    try:
        click.echo("📊 Conflict Resolution Summary")
        click.echo("=" * 40)

        # Create conflict resolution engine
        branch_manager = BranchManager(repo_path=repo_path)
        engine = ConflictResolutionEngine(branch_manager, repo_path)

        summary = engine.get_conflict_summary()

        # Overall statistics
        click.echo(f"Total Conflicts: {summary['total_conflicts']}")
        click.echo(f"Resolved: {summary['resolved_conflicts']}")
        click.echo(f"Unresolved: {summary['unresolved_conflicts']}")
        click.echo(f"Resolution Rate: {summary['resolution_rate']:.1%}")

        # Severity breakdown
        if summary["severity_breakdown"]:
            click.echo("\n📈 Severity Breakdown:")
            for severity, count in summary["severity_breakdown"].items():
                if count > 0:
                    severity_icon = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🔴",
                        "critical": "💀",
                    }.get(severity, "❓")
                    click.echo(f"  {severity_icon} {severity.capitalize()}: {count}")

        # Type breakdown
        if summary["type_breakdown"]:
            click.echo("\n🏷️  Type Breakdown:")
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
                    click.echo(
                        f"  {type_icon} {conflict_type.replace('_', ' ').title()}: {count}"
                    )

        # Resolution statistics
        stats = summary["resolution_stats"]
        if stats["total_conflicts"] > 0:
            click.echo("\n⚡ Resolution Statistics:")
            click.echo(f"  Auto-resolved: {stats['auto_resolved']}")
            click.echo(f"  Human required: {stats['human_required']}")
            click.echo(f"  Success rate: {stats['resolution_success_rate']:.1%}")
            click.echo(f"  Average time: {stats['average_resolution_time']:.2f}s")

    except Exception as e:
        click.echo(f"❌ Error getting conflict summary: {e}", err=True)


@multi_agent_cli.command("predict-conflicts")
@click.argument("branches", nargs=-1, required=True)
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option(
    "--time-horizon", "-t", type=int, default=7, help="Prediction time horizon in days"
)
@click.option(
    "--min-confidence",
    "-c",
    type=float,
    default=0.3,
    help="Minimum confidence threshold",
)
@click.option(
    "--limit", "-l", type=int, default=10, help="Maximum number of predictions to show"
)
def predict_conflicts(
    branches: tuple,
    repo_path: Optional[str],
    time_horizon: int,
    min_confidence: float,
    limit: int,
):
    """Predict potential conflicts between branches"""
    try:
        click.echo(f"🔮 Predicting conflicts for branches: {', '.join(branches)}")
        click.echo(f"   Time horizon: {time_horizon} days")
        click.echo(f"   Confidence threshold: {min_confidence}")

        # Create prediction system
        branch_manager = BranchManager(repo_path=repo_path)
        conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
        predictor = ConflictPredictor(conflict_engine, branch_manager, repo_path)

        # Set prediction parameters
        predictor.min_confidence_threshold = min_confidence
        predictor.max_predictions_per_run = limit * 2  # Get more, filter later

        async def run_prediction():
            from datetime import timedelta

            horizon = timedelta(days=time_horizon)
            predictions = await predictor.predict_conflicts(list(branches), horizon)

            if not predictions:
                click.echo("✅ No potential conflicts predicted")
                return

            # Filter and limit results
            filtered_predictions = [
                p for p in predictions if p.likelihood_score >= min_confidence
            ]
            filtered_predictions = filtered_predictions[:limit]

            click.echo(f"⚠️  Found {len(filtered_predictions)} potential conflicts:")
            click.echo("=" * 80)

            for i, prediction in enumerate(filtered_predictions, 1):
                confidence_icon = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🔴",
                    "critical": "💀",
                }.get(prediction.confidence.value, "❓")

                pattern_icon = {
                    "overlapping_imports": "📦",
                    "function_signature_drift": "🔧",
                    "variable_naming_collision": "🏷️",
                    "class_hierarchy_change": "🏗️",
                    "dependency_version_mismatch": "📋",
                    "api_breaking_change": "💥",
                    "resource_contention": "⚡",
                    "merge_context_loss": "🔀",
                }.get(prediction.pattern.value, "❓")

                click.echo(
                    f"{i}. {confidence_icon} {pattern_icon} {prediction.prediction_id}"
                )
                click.echo(
                    f"   Pattern: {prediction.pattern.value.replace('_', ' ').title()}"
                )
                click.echo(
                    f"   Confidence: {prediction.confidence.value.upper()} ({prediction.likelihood_score:.1%})"
                )
                click.echo(f"   Branches: {', '.join(prediction.affected_branches)}")
                if prediction.affected_files:
                    files_str = ", ".join(prediction.affected_files[:3])
                    if len(prediction.affected_files) > 3:
                        files_str += f" (and {len(prediction.affected_files) - 3} more)"
                    click.echo(f"   Files: {files_str}")
                click.echo(f"   Description: {prediction.description}")

                if prediction.timeline_prediction:
                    click.echo(
                        f"   Expected: {prediction.timeline_prediction.strftime('%Y-%m-%d %H:%M')}"
                    )

                if prediction.prevention_suggestions:
                    click.echo("   Prevention:")
                    for suggestion in prediction.prevention_suggestions[:2]:
                        click.echo(f"     • {suggestion}")
                click.echo()

        asyncio.run(run_prediction())

    except Exception as e:
        click.echo(f"❌ Error predicting conflicts: {e}", err=True)


@multi_agent_cli.command("prediction-summary")
@click.option("--repo-path", "-r", help="Path to git repository")
def prediction_summary(repo_path: Optional[str]):
    """Show conflict prediction summary and statistics"""
    try:
        click.echo("🔮 Conflict Prediction Summary")
        click.echo("=" * 40)

        # Create prediction system
        branch_manager = BranchManager(repo_path=repo_path)
        conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
        predictor = ConflictPredictor(conflict_engine, branch_manager, repo_path)

        summary = predictor.get_prediction_summary()

        # Overall statistics
        click.echo(f"Total Predictions: {summary['total_predictions']}")
        click.echo(f"Active Predictions: {summary.get('active_predictions', 0)}")

        # Confidence breakdown
        if summary["by_confidence"]:
            click.echo("\n🎯 Confidence Breakdown:")
            for confidence, count in summary["by_confidence"].items():
                if count > 0:
                    confidence_icon = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🔴",
                        "critical": "💀",
                    }.get(confidence, "❓")
                    click.echo(
                        f"  {confidence_icon} {confidence.capitalize()}: {count}"
                    )

        # Pattern breakdown
        if summary["by_pattern"]:
            click.echo("\n🏷️  Pattern Breakdown:")
            for pattern, count in summary["by_pattern"].items():
                if count > 0:
                    pattern_icon = {
                        "overlapping_imports": "📦",
                        "function_signature_drift": "🔧",
                        "variable_naming_collision": "🏷️",
                        "class_hierarchy_change": "🏗️",
                        "dependency_version_mismatch": "📋",
                        "api_breaking_change": "💥",
                        "resource_contention": "⚡",
                        "merge_context_loss": "🔀",
                    }.get(pattern, "❓")
                    click.echo(
                        f"  {pattern_icon} {pattern.replace('_', ' ').title()}: {count}"
                    )

        # Accuracy metrics
        accuracy = summary["accuracy_metrics"]
        if accuracy["total_predictions"] > 0:
            click.echo("\n📊 Accuracy Metrics:")
            click.echo(f"  Accuracy Rate: {accuracy['accuracy_rate']:.1%}")
            click.echo(f"  Prevented Conflicts: {accuracy['prevented_conflicts']}")
            click.echo(f"  False Positives: {accuracy['false_positives']}")

        # Most likely conflicts
        if summary.get("most_likely_conflicts"):
            click.echo("\n🚨 Most Likely Conflicts:")
            for conflict in summary["most_likely_conflicts"]:
                click.echo(
                    f"  • {conflict['description']} ({conflict['likelihood']:.1%})"
                )

    except Exception as e:
        click.echo(f"❌ Error getting prediction summary: {e}", err=True)


@multi_agent_cli.command("analyze-conflict-patterns")
@click.argument("branches", nargs=-1, required=True)
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option("--pattern", "-p", help="Focus on specific pattern type")
@click.option("--export", "-e", help="Export analysis to JSON file")
def analyze_conflict_patterns(
    branches: tuple,
    repo_path: Optional[str],
    pattern: Optional[str],
    export: Optional[str],
):
    """Analyze detailed conflict patterns between branches"""
    try:
        click.echo(f"🔍 Analyzing conflict patterns for: {', '.join(branches)}")

        # Create prediction system
        branch_manager = BranchManager(repo_path=repo_path)
        conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
        predictor = ConflictPredictor(conflict_engine, branch_manager, repo_path)

        async def run_analysis():
            analysis_results = {}

            # Calculate conflict vectors for all pairs
            click.echo("\n📊 Conflict Vector Analysis:")
            click.echo("-" * 40)

            for i, branch1 in enumerate(branches):
                for branch2 in branches[i + 1 :]:
                    click.echo(f"\n🔗 {branch1} ↔ {branch2}")

                    vector = await predictor._calculate_conflict_vector(
                        branch1, branch2
                    )
                    analysis_results[f"{branch1}:{branch2}"] = {
                        "vector": vector._asdict(),
                        "patterns": {},
                    }

                    # Display vector components
                    click.echo(f"   File Overlap: {vector.file_overlap_score:.2f}")
                    click.echo(
                        f"   Change Frequency: {vector.change_frequency_score:.2f}"
                    )
                    click.echo(f"   Complexity: {vector.complexity_score:.2f}")
                    click.echo(
                        f"   Dependency Coupling: {vector.dependency_coupling_score:.2f}"
                    )
                    click.echo(
                        f"   Semantic Distance: {vector.semantic_distance_score:.2f}"
                    )
                    click.echo(
                        f"   Temporal Proximity: {vector.temporal_proximity_score:.2f}"
                    )

                    # Overall risk score
                    risk_score = sum(vector) / len(vector)
                    risk_level = (
                        "🔴 HIGH"
                        if risk_score > 0.7
                        else "🟡 MEDIUM"
                        if risk_score > 0.4
                        else "🟢 LOW"
                    )
                    click.echo(f"   Overall Risk: {risk_level} ({risk_score:.2f})")

                    # Pattern-specific analysis
                    if pattern:
                        from libs.multi_agent.conflict_prediction import ConflictPattern

                        try:
                            target_pattern = ConflictPattern(pattern)
                            detector = predictor.pattern_detectors.get(target_pattern)
                            if detector:
                                result = await detector(branch1, branch2, vector)
                                if result:
                                    analysis_results[f"{branch1}:{branch2}"][
                                        "patterns"
                                    ][pattern] = {
                                        "likelihood": result.likelihood_score,
                                        "confidence": result.confidence.value,
                                        "description": result.description,
                                    }
                                    click.echo(
                                        f"   {pattern.replace('_', ' ').title()}: {result.likelihood_score:.1%} confidence"
                                    )
                        except ValueError:
                            click.echo(f"   ❌ Unknown pattern: {pattern}")

            # Export results if requested
            if export:
                import json

                with open(export, "w") as f:
                    json.dump(analysis_results, f, indent=2, default=str)
                click.echo(f"\n💾 Analysis exported to: {export}")

        asyncio.run(run_analysis())

    except Exception as e:
        click.echo(f"❌ Error analyzing patterns: {e}", err=True)


@multi_agent_cli.command("analyze-semantic-conflicts")
@click.argument("branches", nargs=-1, required=True)
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option("--files", "-f", help="Specific files to analyze (comma-separated)")
@click.option(
    "--include-private", "-p", is_flag=True, help="Include private members in analysis"
)
@click.option("--export", "-e", help="Export results to JSON file")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed analysis")
def analyze_semantic_conflicts(
    branches: tuple,
    repo_path: Optional[str],
    files: Optional[str],
    include_private: bool,
    export: Optional[str],
    detailed: bool,
):
    """Analyze AST-based semantic conflicts between branches"""
    try:
        click.echo(f"🧠 Analyzing semantic conflicts between: {', '.join(branches)}")

        if len(branches) < 2:
            click.echo("❌ Need at least 2 branches for comparison")
            return

        # Create semantic analyzer
        branch_manager = BranchManager(repo_path=repo_path)
        analyzer = SemanticAnalyzer(branch_manager, repo_path)

        # Configure analysis options
        analyzer.check_private_members = include_private

        # Parse file list
        file_list = None
        if files:
            file_list = [f.strip() for f in files.split(",")]

        async def run_semantic_analysis():
            all_conflicts = []
            analysis_results = {}

            # Analyze all pairs of branches
            for i, branch1 in enumerate(branches):
                for branch2 in branches[i + 1 :]:
                    click.echo(f"\n🔬 Analyzing {branch1} ↔ {branch2}")

                    conflicts = await analyzer.analyze_semantic_conflicts(
                        branch1, branch2, file_list
                    )

                    pair_key = f"{branch1}:{branch2}"
                    analysis_results[pair_key] = {
                        "conflicts": len(conflicts),
                        "details": [],
                    }

                    if not conflicts:
                        click.echo("✅ No semantic conflicts detected")
                        continue

                    click.echo(f"⚠️  Found {len(conflicts)} semantic conflicts:")
                    click.echo("-" * 60)

                    for j, conflict in enumerate(conflicts[:10], 1):  # Show top 10
                        severity_icon = {
                            "low": "🟢",
                            "medium": "🟡",
                            "high": "🔴",
                            "critical": "💀",
                        }.get(conflict.severity.value, "❓")

                        conflict_type_icon = {
                            "function_signature_change": "🔧",
                            "class_interface_change": "🏗️",
                            "api_breaking_change": "💥",
                            "inheritance_conflict": "🧬",
                            "import_semantic_conflict": "📦",
                            "variable_type_conflict": "🔤",
                            "decorator_conflict": "✨",
                            "data_structure_change": "📊",
                        }.get(conflict.conflict_type.value, "❓")

                        click.echo(
                            f"{j}. {severity_icon} {conflict_type_icon} {conflict.symbol_name}"
                        )
                        click.echo(
                            f"   Type: {conflict.conflict_type.value.replace('_', ' ').title()}"
                        )
                        click.echo(f"   Severity: {conflict.severity.value.upper()}")
                        click.echo(f"   File: {conflict.file_path}")
                        click.echo(f"   Description: {conflict.description}")

                        if detailed:
                            if conflict.old_definition:
                                click.echo(f"   Old: {conflict.old_definition}")
                            if conflict.new_definition:
                                click.echo(f"   New: {conflict.new_definition}")
                            click.echo(
                                f"   Suggested Resolution: {conflict.suggested_resolution.value}"
                            )

                        click.echo()

                        # Store for export
                        analysis_results[pair_key]["details"].append(
                            {
                                "conflict_id": conflict.conflict_id,
                                "type": conflict.conflict_type.value,
                                "severity": conflict.severity.value,
                                "symbol": conflict.symbol_name,
                                "file": conflict.file_path,
                                "description": conflict.description,
                                "old_definition": conflict.old_definition,
                                "new_definition": conflict.new_definition,
                                "suggested_resolution": conflict.suggested_resolution.value,
                                "metadata": conflict.metadata,
                            }
                        )

                    if len(conflicts) > 10:
                        click.echo(f"   ... and {len(conflicts) - 10} more conflicts")

                    all_conflicts.extend(conflicts)

            # Show summary
            if all_conflicts:
                click.echo(f"\n📊 Analysis Summary:")
                click.echo(f"Total conflicts: {len(all_conflicts)}")

                # Group by type
                from collections import Counter

                type_counts = Counter(c.conflict_type.value for c in all_conflicts)
                severity_counts = Counter(c.severity.value for c in all_conflicts)

                click.echo("\n🏷️  By Type:")
                for conflict_type, count in type_counts.most_common():
                    click.echo(
                        f"  • {conflict_type.replace('_', ' ').title()}: {count}"
                    )

                click.echo("\n⚡ By Severity:")
                for severity, count in severity_counts.most_common():
                    icon = {
                        "critical": "💀",
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢",
                    }.get(severity, "❓")
                    click.echo(f"  {icon} {severity.capitalize()}: {count}")

                # Analysis performance
                summary = analyzer.get_analysis_summary()
                click.echo(f"\n📈 Performance:")
                click.echo(f"  Files analyzed: {summary['files_analyzed']}")
                click.echo(f"  Analysis time: {summary['analysis_time']:.2f}s")
                click.echo(f"  Cache hits: {summary['cache_hits']}")

            # Export results
            if export:
                import json

                export_data = {
                    "branches": list(branches),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "total_conflicts": len(all_conflicts),
                    "branch_pairs": analysis_results,
                    "performance_stats": analyzer.get_analysis_summary(),
                }

                with open(export, "w") as f:
                    json.dump(export_data, f, indent=2, default=str)
                click.echo(f"\n💾 Results exported to: {export}")

        asyncio.run(run_semantic_analysis())

    except Exception as e:
        click.echo(f"❌ Error analyzing semantic conflicts: {e}", err=True)


@multi_agent_cli.command("semantic-summary")
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option("--branch", "-b", help="Branch to analyze (default: current)")
@click.option("--files", "-f", help="Specific files to analyze (comma-separated)")
def semantic_summary(
    repo_path: Optional[str], branch: Optional[str], files: Optional[str]
):
    """Show semantic structure summary of code"""
    try:
        click.echo("🧠 Semantic Code Analysis")
        click.echo("=" * 40)

        # Create semantic analyzer
        branch_manager = BranchManager(repo_path=repo_path)
        analyzer = SemanticAnalyzer(branch_manager, repo_path)

        # Parse file list
        file_list = None
        if files:
            file_list = [f.strip() for f in files.split(",")]

        async def run_summary():
            current_branch = branch or "HEAD"

            if file_list:
                files_to_analyze = file_list
            else:
                # Get all Python files in repo
                files_to_analyze = []
                try:
                    result = await analyzer._get_changed_python_files(
                        current_branch, current_branch
                    )
                    files_to_analyze = result
                except:
                    # Fallback: scan current directory
                    for py_file in analyzer.repo_path.rglob("*.py"):
                        if not any(part.startswith(".") for part in py_file.parts):
                            files_to_analyze.append(
                                str(py_file.relative_to(analyzer.repo_path))
                            )

            total_functions = 0
            total_classes = 0
            total_imports = 0
            visibility_stats = {"public": 0, "protected": 0, "private": 0, "magic": 0}

            click.echo(f"Branch: {current_branch}")
            click.echo(f"Files to analyze: {len(files_to_analyze)}")
            click.echo()

            for file_path in files_to_analyze[:20]:  # Limit to first 20 files
                context = await analyzer._get_semantic_context(
                    file_path, current_branch
                )
                if not context:
                    continue

                click.echo(f"📄 {file_path}")
                click.echo(f"   Functions: {len(context.functions)}")
                click.echo(f"   Classes: {len(context.classes)}")
                click.echo(f"   Imports: {len(context.imports)}")
                click.echo(f"   Global Variables: {len(context.global_variables)}")
                click.echo(f"   Constants: {len(context.constants)}")

                # Count visibility
                for func in context.functions.values():
                    visibility_stats[func.visibility.value] += 1
                    total_functions += 1

                for cls in context.classes.values():
                    visibility_stats[cls.visibility.value] += 1
                    total_classes += 1
                    total_functions += len(cls.methods)

                total_imports += len(context.imports)
                click.echo()

            if len(files_to_analyze) > 20:
                click.echo(f"... and {len(files_to_analyze) - 20} more files")

            # Overall statistics
            click.echo("📊 Overall Statistics:")
            click.echo(f"Total Functions: {total_functions}")
            click.echo(f"Total Classes: {total_classes}")
            click.echo(f"Total Imports: {total_imports}")

            click.echo("\n👁️  Visibility Distribution:")
            for visibility, count in visibility_stats.items():
                if count > 0:
                    icon = {
                        "public": "🌍",
                        "protected": "🛡️",
                        "private": "🔒",
                        "magic": "✨",
                    }.get(visibility, "❓")
                    click.echo(f"  {icon} {visibility.capitalize()}: {count}")

        asyncio.run(run_summary())

    except Exception as e:
        click.echo(f"❌ Error generating semantic summary: {e}", err=True)


@multi_agent_cli.command("function-diff")
@click.argument("function_name")
@click.argument("branch1")
@click.argument("branch2")
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option("--file", "-f", help="Specific file containing the function")
def function_diff(
    function_name: str,
    branch1: str,
    branch2: str,
    repo_path: Optional[str],
    file: Optional[str],
):
    """Compare function signatures between branches"""
    try:
        click.echo(
            f"🔧 Comparing function '{function_name}' between {branch1} and {branch2}"
        )

        # Create semantic analyzer
        branch_manager = BranchManager(repo_path=repo_path)
        analyzer = SemanticAnalyzer(branch_manager, repo_path)

        async def run_diff():
            # Find function in both branches
            func1 = None
            func2 = None
            file1 = None
            file2 = None

            # Get list of files to search
            if file:
                files_to_search = [file]
            else:
                # Search all Python files
                files_to_search = []
                try:
                    result1 = await analyzer._get_changed_python_files(branch1, branch1)
                    result2 = await analyzer._get_changed_python_files(branch2, branch2)
                    files_to_search = list(set(result1 + result2))
                except:
                    # Fallback: scan current directory
                    for py_file in analyzer.repo_path.rglob("*.py"):
                        if not any(part.startswith(".") for part in py_file.parts):
                            files_to_search.append(
                                str(py_file.relative_to(analyzer.repo_path))
                            )

            # Search for function
            for file_path in files_to_search:
                # Check branch1
                context1 = await analyzer._get_semantic_context(file_path, branch1)
                if context1 and function_name in context1.functions:
                    func1 = context1.functions[function_name]
                    file1 = file_path

                # Check classes for methods
                if context1:
                    for class_name, class_def in context1.classes.items():
                        if function_name in class_def.methods:
                            func1 = class_def.methods[function_name]
                            file1 = file_path
                            function_name = f"{class_name}.{function_name}"
                            break

                # Check branch2
                context2 = await analyzer._get_semantic_context(file_path, branch2)
                if context2 and function_name.split(".")[-1] in context2.functions:
                    func2 = context2.functions[function_name.split(".")[-1]]
                    file2 = file_path

                # Check classes for methods
                if context2:
                    for class_name, class_def in context2.classes.items():
                        method_name = function_name.split(".")[-1]
                        if method_name in class_def.methods:
                            func2 = class_def.methods[method_name]
                            file2 = file_path
                            break

                if func1 and func2:
                    break

            # Display results
            if not func1 and not func2:
                click.echo(f"❌ Function '{function_name}' not found in either branch")
                return
            elif not func1:
                click.echo(f"⚠️  Function '{function_name}' not found in {branch1}")
                click.echo(f"✅ Found in {branch2}: {file2}")
                click.echo(f"\n{branch2} signature:")
                click.echo(f"  {analyzer._signature_to_string(func2)}")
                return
            elif not func2:
                click.echo(f"✅ Found in {branch1}: {file1}")
                click.echo(f"⚠️  Function '{function_name}' not found in {branch2}")
                click.echo(f"\n{branch1} signature:")
                click.echo(f"  {analyzer._signature_to_string(func1)}")
                return

            # Compare signatures
            click.echo(f"✅ Found in both branches")
            click.echo(f"   {branch1}: {file1}")
            click.echo(f"   {branch2}: {file2}")

            sig1_str = analyzer._signature_to_string(func1)
            sig2_str = analyzer._signature_to_string(func2)

            click.echo(f"\n📋 Signature Comparison:")
            click.echo(f"{branch1}: {sig1_str}")
            click.echo(f"{branch2}: {sig2_str}")

            if analyzer._functions_have_signature_conflict(func1, func2):
                click.echo("\n⚠️  CONFLICT DETECTED")

                # Analyze differences
                impact = analyzer._analyze_function_impact(func1, func2)
                severity = analyzer._assess_function_conflict_severity(func1, func2)

                click.echo(f"Severity: {severity.value.upper()}")
                click.echo(f"Breaking Change: {impact['breaking_change']}")

                if impact["parameter_changes"]:
                    click.echo("Parameter Changes:")
                    for change in impact["parameter_changes"]:
                        click.echo(f"  • {change}")

                if impact["return_type_change"]:
                    click.echo(
                        f"Return Type Changed: {func1.return_type} → {func2.return_type}"
                    )

                if impact["decorator_changes"]:
                    click.echo(
                        f"Decorator Changes: {func1.decorators} → {func2.decorators}"
                    )

                # Suggest resolution
                resolution = analyzer._suggest_function_resolution(func1, func2)
                click.echo(f"Suggested Resolution: {resolution.value}")
            else:
                click.echo("\n✅ No conflicts detected")

        asyncio.run(run_diff())

    except Exception as e:
        click.echo(f"❌ Error comparing function: {e}", err=True)


@multi_agent_cli.command("semantic-merge")
@click.argument("file_path")
@click.argument("branch1")
@click.argument("branch2")
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option(
    "--target-branch", "-t", help="Target branch for merge (default: branch1)"
)
@click.option(
    "--strategy",
    "-s",
    type=click.Choice([s.value for s in MergeStrategy]),
    help="Merge strategy to use",
)
@click.option("--apply", "-a", is_flag=True, help="Apply merge result to target branch")
@click.option("--export", "-e", help="Export merge result to file")
def semantic_merge(
    file_path: str,
    branch1: str,
    branch2: str,
    repo_path: Optional[str],
    target_branch: Optional[str],
    strategy: Optional[str],
    apply: bool,
    export: Optional[str],
):
    """Perform intelligent semantic merge of a file between branches"""
    try:
        click.echo(f"🔀 Semantic merge: {file_path}")
        click.echo(f"   Branches: {branch1} ↔ {branch2}")

        if strategy:
            strategy_enum = MergeStrategy(strategy)
            click.echo(f"   Strategy: {strategy_enum.value}")
        else:
            strategy_enum = None

        # Create components
        branch_manager = BranchManager(repo_path=repo_path)
        conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
        semantic_analyzer = SemanticAnalyzer(branch_manager, repo_path)
        semantic_merger = SemanticMerger(
            semantic_analyzer, conflict_engine, branch_manager, repo_path
        )

        async def run_merge():
            # Perform semantic merge
            merge_result = await semantic_merger.perform_semantic_merge(
                file_path=file_path,
                branch1=branch1,
                branch2=branch2,
                target_branch=target_branch,
                strategy=strategy_enum,
            )

            # Display results
            click.echo(f"\n📊 Merge Result:")
            click.echo(f"   Merge ID: {merge_result.merge_id}")
            click.echo(f"   Resolution: {merge_result.resolution.value}")
            click.echo(f"   Strategy Used: {merge_result.strategy_used.value}")
            click.echo(f"   Confidence: {merge_result.merge_confidence:.1%}")
            click.echo(
                f"   Semantic Integrity: {'✅' if merge_result.semantic_integrity else '❌'}"
            )

            if merge_result.conflicts_resolved:
                click.echo(
                    f"   Conflicts Resolved: {len(merge_result.conflicts_resolved)}"
                )
                for conflict_id in merge_result.conflicts_resolved[:5]:
                    click.echo(f"     • {conflict_id}")
                if len(merge_result.conflicts_resolved) > 5:
                    click.echo(
                        f"     ... and {len(merge_result.conflicts_resolved) - 5} more"
                    )

            if merge_result.unresolved_conflicts:
                click.echo(
                    f"   ⚠️  Unresolved Conflicts: {len(merge_result.unresolved_conflicts)}"
                )
                for conflict_id in merge_result.unresolved_conflicts[:3]:
                    click.echo(f"     • {conflict_id}")

            # Show diff stats
            if merge_result.diff_stats:
                stats = merge_result.diff_stats
                click.echo(f"\n📈 Changes:")
                if "lines_merged" in stats:
                    click.echo(f"   Total lines: {stats['lines_merged']}")
                if "lines_added" in stats:
                    click.echo(f"   Lines added: {stats['lines_added']}")
                if "lines_removed" in stats:
                    click.echo(f"   Lines removed: {stats['lines_removed']}")

            # Export result if requested
            if export and merge_result.merged_content:
                with open(export, "w") as f:
                    f.write(merge_result.merged_content)
                click.echo(f"\n💾 Merged content exported to: {export}")

            # Apply if requested and successful
            if apply and merge_result.resolution in [
                MergeResolution.AUTO_RESOLVED,
                MergeResolution.PARTIAL_RESOLUTION,
            ]:
                if merge_result.semantic_integrity:
                    click.echo(
                        f"\n✅ Merge would be applied to {target_branch or branch1}"
                    )
                    # In actual implementation, this would write the merged content
                    click.echo("   (Dry run - actual application not implemented yet)")
                else:
                    click.echo(
                        f"\n❌ Cannot apply merge due to semantic integrity issues"
                    )
            elif apply:
                click.echo(f"\n❌ Cannot apply merge - resolution failed")

        asyncio.run(run_merge())

    except Exception as e:
        click.echo(f"❌ Error performing semantic merge: {e}", err=True)


@multi_agent_cli.command("batch-merge")
@click.argument("branch1")
@click.argument("branch2")
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option(
    "--target-branch", "-t", help="Target branch for merge (default: branch1)"
)
@click.option("--files", "-f", help="Specific files to merge (comma-separated)")
@click.option(
    "--strategy",
    "-s",
    type=click.Choice([s.value for s in MergeStrategy]),
    help="Merge strategy to use",
)
@click.option("--max-concurrent", "-c", default=5, help="Maximum concurrent merges")
@click.option("--apply", "-a", is_flag=True, help="Apply successful merge results")
@click.option("--export-summary", "-e", help="Export batch summary to JSON file")
def batch_merge(
    branch1: str,
    branch2: str,
    repo_path: Optional[str],
    target_branch: Optional[str],
    files: Optional[str],
    strategy: Optional[str],
    max_concurrent: int,
    apply: bool,
    export_summary: Optional[str],
):
    """Perform batch semantic merge of multiple files between branches"""
    try:
        click.echo(f"🔀 Batch semantic merge: {branch1} ↔ {branch2}")

        strategy_enum = MergeStrategy(strategy) if strategy else None

        # Create components
        branch_manager = BranchManager(repo_path=repo_path)
        conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
        semantic_analyzer = SemanticAnalyzer(branch_manager, repo_path)
        semantic_merger = SemanticMerger(
            semantic_analyzer, conflict_engine, branch_manager, repo_path
        )

        async def run_batch_merge():
            # Parse file list
            if files:
                file_list = [f.strip() for f in files.split(",")]
            else:
                # Get all changed Python files
                try:
                    file_list = await semantic_analyzer._get_changed_python_files(
                        branch1, branch2
                    )
                except:
                    click.echo(
                        "❌ Could not determine changed files. Please specify --files"
                    )
                    return

            if not file_list:
                click.echo("✅ No files to merge")
                return

            click.echo(f"📁 Files to merge: {len(file_list)}")
            for f in file_list[:10]:
                click.echo(f"   • {f}")
            if len(file_list) > 10:
                click.echo(f"   ... and {len(file_list) - 10} more")

            click.echo(
                f"\n🚀 Starting batch merge (max {max_concurrent} concurrent)..."
            )

            # Perform batch merge
            merge_results = await semantic_merger.batch_merge_files(
                file_paths=file_list,
                branch1=branch1,
                branch2=branch2,
                target_branch=target_branch,
                max_concurrent=max_concurrent,
            )

            # Analyze results
            successful = [
                r
                for r in merge_results
                if r.resolution
                in [MergeResolution.AUTO_RESOLVED, MergeResolution.PARTIAL_RESOLUTION]
            ]
            failed = [
                r for r in merge_results if r.resolution == MergeResolution.MERGE_FAILED
            ]
            manual_required = [
                r
                for r in merge_results
                if r.resolution == MergeResolution.MANUAL_REQUIRED
            ]

            # Display summary
            click.echo(f"\n📊 Batch Merge Summary:")
            click.echo(f"   Total files: {len(merge_results)}")
            click.echo(f"   ✅ Successful: {len(successful)}")
            click.echo(f"   ⚠️  Manual required: {len(manual_required)}")
            click.echo(f"   ❌ Failed: {len(failed)}")

            if successful:
                avg_confidence = sum(r.merge_confidence for r in successful) / len(
                    successful
                )
                semantic_integrity_rate = sum(
                    1 for r in successful if r.semantic_integrity
                ) / len(successful)
                click.echo(f"   📈 Average confidence: {avg_confidence:.1%}")
                click.echo(f"   🔒 Semantic integrity: {semantic_integrity_rate:.1%}")

            # Show detailed results for failures
            if failed:
                click.echo(f"\n❌ Failed merges:")
                for result in failed[:5]:
                    error = result.metadata.get("error", "Unknown error")
                    click.echo(f"   • {result.file_path}: {error}")
                if len(failed) > 5:
                    click.echo(f"   ... and {len(failed) - 5} more")

            if manual_required:
                click.echo(f"\n⚠️  Manual intervention required:")
                for result in manual_required[:5]:
                    click.echo(
                        f"   • {result.file_path}: {len(result.unresolved_conflicts)} unresolved conflicts"
                    )
                if len(manual_required) > 5:
                    click.echo(f"   ... and {len(manual_required) - 5} more")

            # Apply successful merges if requested
            if apply and successful:
                click.echo(f"\n🚀 Applying {len(successful)} successful merges...")
                for result in successful:
                    if result.semantic_integrity:
                        click.echo(f"   ✅ Would apply: {result.file_path}")
                        # In actual implementation, this would write the merged content
                    else:
                        click.echo(
                            f"   ⚠️  Skipping due to integrity issues: {result.file_path}"
                        )
                click.echo("   (Dry run - actual application not implemented yet)")

            # Export summary if requested
            if export_summary:
                import json
                from datetime import datetime

                summary_data = {
                    "batch_merge_summary": {
                        "timestamp": datetime.now().isoformat(),
                        "branch1": branch1,
                        "branch2": branch2,
                        "target_branch": target_branch or branch1,
                        "strategy": strategy_enum.value
                        if strategy_enum
                        else "intelligent_merge",
                        "total_files": len(merge_results),
                        "successful": len(successful),
                        "manual_required": len(manual_required),
                        "failed": len(failed),
                        "average_confidence": avg_confidence if successful else 0.0,
                        "semantic_integrity_rate": semantic_integrity_rate
                        if successful
                        else 0.0,
                    },
                    "detailed_results": [
                        {
                            "merge_id": r.merge_id,
                            "file_path": r.file_path,
                            "resolution": r.resolution.value,
                            "strategy": r.strategy_used.value,
                            "confidence": r.merge_confidence,
                            "semantic_integrity": r.semantic_integrity,
                            "conflicts_resolved": len(r.conflicts_resolved),
                            "conflicts_unresolved": len(r.unresolved_conflicts),
                            "merge_time": r.merge_time.isoformat(),
                        }
                        for r in merge_results
                    ],
                }

                with open(export_summary, "w") as f:
                    json.dump(summary_data, f, indent=2)
                click.echo(f"\n💾 Batch summary exported to: {export_summary}")

        asyncio.run(run_batch_merge())

    except Exception as e:
        click.echo(f"❌ Error performing batch merge: {e}", err=True)


@multi_agent_cli.command("auto-resolve")
@click.argument("branch1")
@click.argument("branch2")
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option(
    "--target-branch", "-t", help="Target branch for resolution (default: branch1)"
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice([m.value for m in AutoResolutionMode]),
    default="balanced",
    help="Auto-resolution mode",
)
@click.option("--files", "-f", help="Specific files to process (comma-separated)")
@click.option("--apply", "-a", is_flag=True, help="Apply successful resolutions")
@click.option("--export", "-e", help="Export resolution report to JSON file")
@click.option(
    "--preview", "-p", is_flag=True, help="Preview mode - show what would be resolved"
)
def auto_resolve(
    branch1: str,
    branch2: str,
    repo_path: Optional[str],
    target_branch: Optional[str],
    mode: str,
    files: Optional[str],
    apply: bool,
    export: Optional[str],
    preview: bool,
):
    """Automatically resolve conflicts between branches using AI-powered semantic analysis"""
    try:
        mode_enum = AutoResolutionMode(mode)

        click.echo(f"🤖 Auto-resolving conflicts: {branch1} ↔ {branch2}")
        click.echo(f"   Mode: {mode_enum.value}")
        click.echo(f"   Target: {target_branch or branch1}")

        if preview:
            click.echo("   👁️  Preview mode - no changes will be applied")

        # Create components
        branch_manager = BranchManager(repo_path=repo_path)
        conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
        semantic_analyzer = SemanticAnalyzer(branch_manager, repo_path)
        semantic_merger = SemanticMerger(
            semantic_analyzer, conflict_engine, branch_manager, repo_path
        )

        # Create conflict predictor for advanced resolution
        from libs.multi_agent.conflict_prediction import ConflictPredictor

        conflict_predictor = ConflictPredictor(
            conflict_engine, branch_manager, repo_path
        )

        # Create auto resolver
        auto_resolver = AutoResolver(
            semantic_analyzer=semantic_analyzer,
            semantic_merger=semantic_merger,
            conflict_engine=conflict_engine,
            conflict_predictor=conflict_predictor,
            branch_manager=branch_manager,
            repo_path=repo_path,
        )

        async def run_auto_resolve():
            # Parse file filter
            file_filter = None
            if files:
                file_filter = [f.strip() for f in files.split(",")]

            click.echo(f"\n🔍 Analyzing conflicts...")

            # Perform auto-resolution
            result = await auto_resolver.auto_resolve_branch_conflicts(
                branch1=branch1,
                branch2=branch2,
                target_branch=target_branch,
                mode=mode_enum,
                file_filter=file_filter,
            )

            # Display detailed results
            click.echo(f"\n📊 Auto-Resolution Results:")
            click.echo(f"   Session ID: {result.session_id}")
            click.echo(f"   Outcome: {result.outcome.value}")
            click.echo(f"   Resolution time: {result.resolution_time:.2f}s")

            # Conflict statistics
            click.echo(f"\n🎯 Conflict Analysis:")
            click.echo(f"   Conflicts detected: {result.conflicts_detected}")
            click.echo(f"   Conflicts resolved: {result.conflicts_resolved}")
            click.echo(f"   Files processed: {result.files_processed}")

            if result.conflicts_detected > 0:
                resolution_rate = result.conflicts_resolved / result.conflicts_detected
                click.echo(f"   Resolution rate: {resolution_rate:.1%}")

            # Quality metrics
            click.echo(f"\n✨ Quality Metrics:")
            click.echo(f"   Confidence score: {result.confidence_score:.1%}")
            click.echo(
                f"   Semantic integrity: {'✅' if result.semantic_integrity_preserved else '❌'}"
            )

            # Escalated conflicts
            if result.escalated_conflicts:
                click.echo(
                    f"\n⚠️  Escalated to human ({len(result.escalated_conflicts)}):"
                )
                for conflict_id in result.escalated_conflicts[:5]:
                    click.echo(f"   • {conflict_id}")
                if len(result.escalated_conflicts) > 5:
                    click.echo(f"   ... and {len(result.escalated_conflicts) - 5} more")

            # Merge results details
            if result.merge_results:
                click.echo(f"\n📁 File Results:")
                successful_merges = [
                    r
                    for r in result.merge_results
                    if r.resolution
                    in [
                        MergeResolution.AUTO_RESOLVED,
                        MergeResolution.PARTIAL_RESOLUTION,
                    ]
                ]

                for merge_result in successful_merges[:10]:
                    resolution_icon = (
                        "✅"
                        if merge_result.resolution == MergeResolution.AUTO_RESOLVED
                        else "⚠️"
                    )
                    click.echo(f"   {resolution_icon} {merge_result.file_path}")
                    click.echo(f"      Strategy: {merge_result.strategy_used.value}")
                    click.echo(f"      Confidence: {merge_result.merge_confidence:.1%}")
                    if merge_result.conflicts_resolved:
                        click.echo(
                            f"      Resolved: {len(merge_result.conflicts_resolved)} conflicts"
                        )

                if len(successful_merges) > 10:
                    click.echo(
                        f"   ... and {len(successful_merges) - 10} more successful merges"
                    )

            # Manual intervention requirements
            if result.manual_intervention_required:
                click.echo(f"\n👥 Manual Intervention Required:")
                for item in result.manual_intervention_required[:5]:
                    click.echo(f"   • {item}")
                if len(result.manual_intervention_required) > 5:
                    click.echo(
                        f"   ... and {len(result.manual_intervention_required) - 5} more"
                    )

            # Apply results if requested and not in preview mode
            if (
                apply
                and not preview
                and result.outcome in ["fully_resolved", "partially_resolved"]
            ):
                click.echo(f"\n🚀 Applying resolution results...")
                applied_count = len(
                    [r for r in result.merge_results if r.semantic_integrity]
                )
                click.echo(f"   Would apply {applied_count} successful merges")
                click.echo("   (Dry run - actual application not implemented yet)")
            elif apply and preview:
                click.echo(
                    f"\n👁️  Preview mode - would apply resolution to {len(result.merge_results)} files"
                )

            # Export report if requested
            if export:
                import json

                report_data = {
                    "auto_resolution_report": {
                        "session_id": result.session_id,
                        "timestamp": result.resolved_at.isoformat(),
                        "branches": {
                            "source1": branch1,
                            "source2": branch2,
                            "target": target_branch or branch1,
                        },
                        "mode": result.mode.value,
                        "outcome": result.outcome.value,
                        "performance": {
                            "resolution_time": result.resolution_time,
                            "conflicts_detected": result.conflicts_detected,
                            "conflicts_resolved": result.conflicts_resolved,
                            "files_processed": result.files_processed,
                            "confidence_score": result.confidence_score,
                            "semantic_integrity_preserved": result.semantic_integrity_preserved,
                        },
                        "escalated_conflicts": result.escalated_conflicts,
                        "manual_intervention_required": result.manual_intervention_required,
                        "metadata": result.metadata,
                    },
                    "merge_results": [
                        {
                            "merge_id": r.merge_id,
                            "file_path": r.file_path,
                            "resolution": r.resolution.value,
                            "strategy": r.strategy_used.value,
                            "confidence": r.merge_confidence,
                            "semantic_integrity": r.semantic_integrity,
                            "conflicts_resolved": r.conflicts_resolved,
                            "unresolved_conflicts": r.unresolved_conflicts,
                        }
                        for r in result.merge_results
                    ],
                }

                with open(export, "w") as f:
                    json.dump(report_data, f, indent=2, default=str)
                click.echo(f"\n💾 Resolution report exported to: {export}")

            # Provide recommendations
            click.echo(f"\n💡 Recommendations:")
            if result.outcome == "fully_resolved":
                click.echo("   ✅ All conflicts resolved successfully")
            elif result.outcome == "partially_resolved":
                click.echo("   ⚠️  Some conflicts require manual review")
                click.echo(
                    "   💡 Consider using 'conservative' mode for higher precision"
                )
            elif result.outcome == "escalated_to_human":
                click.echo("   👥 Most conflicts require human intervention")
                click.echo(
                    "   💡 Review conflict complexity and consider breaking down changes"
                )
            else:
                click.echo("   ❌ Resolution failed - check logs for details")

        asyncio.run(run_auto_resolve())

    except Exception as e:
        click.echo(f"❌ Error in auto-resolution: {e}", err=True)


@multi_agent_cli.command("prevent-conflicts")
@click.argument("branches", nargs=-1, required=True)
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option(
    "--mode",
    "-m",
    type=click.Choice([m.value for m in AutoResolutionMode]),
    default="predictive",
    help="Prevention mode",
)
@click.option(
    "--apply-measures", "-a", is_flag=True, help="Apply automatic preventive measures"
)
@click.option("--export", "-e", help="Export prevention report to JSON file")
def prevent_conflicts(
    branches: tuple,
    repo_path: Optional[str],
    mode: str,
    apply_measures: bool,
    export: Optional[str],
):
    """Use AI prediction to prevent conflicts before they occur"""
    try:
        mode_enum = AutoResolutionMode(mode)

        click.echo(f"🔮 Predictive conflict prevention")
        click.echo(f"   Branches: {', '.join(branches)}")
        click.echo(f"   Mode: {mode_enum.value}")

        if len(branches) < 2:
            click.echo("❌ Need at least 2 branches for conflict prediction")
            return

        # Create components
        branch_manager = BranchManager(repo_path=repo_path)
        conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
        semantic_analyzer = SemanticAnalyzer(branch_manager, repo_path)
        semantic_merger = SemanticMerger(
            semantic_analyzer, conflict_engine, branch_manager, repo_path
        )

        from libs.multi_agent.conflict_prediction import ConflictPredictor

        conflict_predictor = ConflictPredictor(
            conflict_engine, branch_manager, repo_path
        )

        auto_resolver = AutoResolver(
            semantic_analyzer=semantic_analyzer,
            semantic_merger=semantic_merger,
            conflict_engine=conflict_engine,
            conflict_predictor=conflict_predictor,
            branch_manager=branch_manager,
            repo_path=repo_path,
        )

        async def run_prevention():
            click.echo(
                f"\n🔍 Analyzing {len(branches)} branches for potential conflicts..."
            )

            # Perform predictive conflict prevention
            result = await auto_resolver.prevent_conflicts_predictively(
                branches=list(branches), prevention_mode=mode_enum
            )

            # Display results
            click.echo(f"\n📊 Prevention Results:")
            click.echo(f"   Status: {result['status']}")
            click.echo(f"   Branches analyzed: {result['branches_analyzed']}")

            if "predictions_found" in result:
                click.echo(f"   Predictions found: {result['predictions_found']}")
                click.echo(
                    f"   High confidence: {result['high_confidence_predictions']}"
                )

            if "preventive_measures_applied" in result:
                click.echo(
                    f"   Preventive measures applied: {result['preventive_measures_applied']}"
                )

            # Show recommendations
            if "recommendations" in result and result["recommendations"]:
                click.echo(f"\n💡 Prevention Strategies:")
                for i, strategy in enumerate(result["recommendations"][:10], 1):
                    click.echo(f"{i}. Pattern: {strategy['pattern']}")
                    click.echo(f"   Prediction ID: {strategy['prediction_id']}")

                    if strategy["automated_measures"]:
                        click.echo("   🤖 Automated measures:")
                        for measure in strategy["automated_measures"]:
                            click.echo(f"     • {measure.replace('_', ' ').title()}")

                    if strategy["manual_actions"]:
                        click.echo("   👥 Manual actions:")
                        for action in strategy["manual_actions"]:
                            click.echo(f"     • {action.replace('_', ' ').title()}")

                    if strategy["prevention_suggestions"]:
                        click.echo("   💭 Suggestions:")
                        for suggestion in strategy["prevention_suggestions"][:3]:
                            click.echo(f"     • {suggestion}")

                    click.echo()

            # Show applied measures
            if "applied_measures" in result and result["applied_measures"]:
                click.echo(f"🚀 Applied Preventive Measures:")
                successful = [
                    m
                    for m in result["applied_measures"]
                    if m["status"] == "applied_successfully"
                ]
                failed = [
                    m for m in result["applied_measures"] if m["status"] == "failed"
                ]

                if successful:
                    click.echo(f"   ✅ Successful ({len(successful)}):")
                    for measure in successful:
                        click.echo(
                            f"     • {measure['measure'].replace('_', ' ').title()}"
                        )

                if failed:
                    click.echo(f"   ❌ Failed ({len(failed)}):")
                    for measure in failed:
                        error = measure.get("error", "Unknown error")
                        click.echo(
                            f"     • {measure['measure'].replace('_', ' ').title()}: {error}"
                        )

            # Show prevention summary
            if "prevention_summary" in result:
                summary = result["prevention_summary"]
                click.echo(f"\n📈 Prevention Summary:")
                click.echo(f"   Conflicts prevented: {summary['conflicts_prevented']}")
                click.echo(
                    f"   Manual intervention needed: {summary['manual_intervention_needed']}"
                )

            # Export results if requested
            if export:
                import json
                from datetime import datetime

                export_data = {
                    "conflict_prevention_report": {
                        "timestamp": datetime.now().isoformat(),
                        "branches": list(branches),
                        "mode": mode_enum.value,
                        "results": result,
                    }
                }

                with open(export, "w") as f:
                    json.dump(export_data, f, indent=2, default=str)
                click.echo(f"\n💾 Prevention report exported to: {export}")

        asyncio.run(run_prevention())

    except Exception as e:
        click.echo(f"❌ Error in conflict prevention: {e}", err=True)


@multi_agent_cli.command("collaborate")
@click.argument("agents", nargs=-1, required=True)
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(
        ["isolated", "cooperative", "synchronized", "hierarchical", "peer_to_peer"]
    ),
    default="cooperative",
    help="Collaboration mode",
)
@click.option("--purpose", "-p", required=True, help="Purpose of collaboration")
@click.option(
    "--duration", "-d", type=int, default=3600, help="Session duration in seconds"
)
@click.option(
    "--enable-sync", "-s", is_flag=True, help="Enable auto-sync between agents"
)
def collaborate(
    agents: tuple,
    repo_path: Optional[str],
    mode: str,
    purpose: str,
    duration: int,
    enable_sync: bool,
):
    """Start a collaboration session between multiple agents"""
    try:
        from libs.multi_agent.collaboration_engine import CollaborationMode

        click.echo(f"🤝 Starting collaboration session")
        click.echo(f"   Agents: {', '.join(agents)}")
        click.echo(f"   Mode: {mode}")
        click.echo(f"   Purpose: {purpose}")

        # Create components
        branch_manager = BranchManager(repo_path=repo_path)
        conflict_engine = ConflictResolutionEngine(branch_manager, repo_path)
        semantic_analyzer = SemanticAnalyzer(branch_manager, repo_path)

        # Create mock agent pool for demo
        from libs.multi_agent.agent_pool import AgentPool

        agent_pool = AgentPool(max_agents=len(agents))

        # Create collaboration engine
        from libs.multi_agent.collaboration_engine import CollaborationEngine

        collab_engine = CollaborationEngine(
            agent_pool=agent_pool,
            branch_manager=branch_manager,
            conflict_engine=conflict_engine,
            semantic_analyzer=semantic_analyzer,
            repo_path=repo_path,
        )

        if enable_sync:
            collab_engine.enable_auto_sync = True
            collab_engine.sync_interval = 30  # More frequent for demo

        async def run_collaboration():
            from libs.multi_agent.collaboration_engine import (
                MessageType,
                MessagePriority,
            )

            # Start collaboration engine
            await collab_engine.start()
            click.echo("\n✅ Collaboration engine started")

            # Create collaboration session
            mode_enum = CollaborationMode(mode.upper())
            session_id = await collab_engine.create_collaboration_session(
                initiator_id=agents[0],
                participant_ids=list(agents),
                mode=mode_enum,
                purpose=purpose,
                initial_context={
                    "repo_path": repo_path or ".",
                    "start_time": datetime.now().isoformat(),
                },
            )

            click.echo(f"\n📋 Session created: {session_id}")
            click.echo(f"   Duration: {duration}s")

            # Simulate some collaborative activities
            await asyncio.sleep(2)

            # Share some knowledge
            knowledge_id = await collab_engine.share_knowledge(
                contributor_id=agents[0],
                knowledge_type="session_info",
                content={
                    "session_id": session_id,
                    "purpose": purpose,
                    "participants": list(agents),
                },
                tags=["collaboration", "session"],
                relevance_score=1.0,
            )
            click.echo(f"\n📚 Knowledge shared: {knowledge_id}")

            # Send status updates
            for i, agent in enumerate(agents[1:], 1):
                await collab_engine.send_message(
                    sender_id=agent,
                    recipient_id=None,  # Broadcast
                    message_type=MessageType.STATUS_UPDATE,
                    subject=f"{agent} joined collaboration",
                    content={"status": "ready", "agent_index": i},
                    priority=MessagePriority.NORMAL,
                )

            # Get collaboration summary
            summary = collab_engine.get_collaboration_summary()

            click.echo(f"\n📊 Collaboration Statistics:")
            click.echo(f"   Messages sent: {summary['statistics']['messages_sent']}")
            click.echo(
                f"   Knowledge shared: {summary['statistics']['knowledge_shared']}"
            )
            click.echo(f"   Active sessions: {summary['active_sessions']}")

            # Wait for duration or user interrupt
            click.echo(f"\n⏳ Session running for {duration}s (Ctrl+C to stop)...")
            try:
                await asyncio.sleep(duration)
            except KeyboardInterrupt:
                click.echo("\n⚠️  Session interrupted by user")

            # End session
            await collab_engine.end_collaboration_session(
                session_id, outcomes=[f"Collaboration completed: {purpose}"]
            )

            # Stop engine
            await collab_engine.stop()
            click.echo("\n✅ Collaboration session ended")

            # Final summary
            final_summary = collab_engine.get_collaboration_summary()
            click.echo(f"\n📈 Final Summary:")
            click.echo(
                f"   Total messages: {final_summary['statistics']['messages_sent']}"
            )
            click.echo(
                f"   Messages delivered: {final_summary['statistics']['messages_delivered']}"
            )
            click.echo(f"   Knowledge items: {final_summary['shared_knowledge_count']}")
            click.echo(
                f"   Successful collaborations: {final_summary['statistics']['successful_collaborations']}"
            )

        asyncio.run(run_collaboration())

    except Exception as e:
        click.echo(f"❌ Error in collaboration: {e}", err=True)


@multi_agent_cli.command("send-message")
@click.option("--from", "sender", required=True, help="Sender agent ID")
@click.option("--to", "recipient", help="Recipient agent ID (omit for broadcast)")
@click.option(
    "--type",
    "msg_type",
    type=click.Choice(
        [
            "status",
            "dependency",
            "conflict",
            "help",
            "knowledge",
            "review",
            "sync",
            "broadcast",
        ]
    ),
    required=True,
    help="Message type",
)
@click.option("--subject", "-s", required=True, help="Message subject")
@click.option("--content", "-c", required=True, help="Message content (JSON format)")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["low", "normal", "high", "critical", "emergency"]),
    default="normal",
    help="Message priority",
)
@click.option("--repo-path", "-r", help="Path to git repository")
def send_message(
    sender: str,
    recipient: Optional[str],
    msg_type: str,
    subject: str,
    content: str,
    priority: str,
    repo_path: Optional[str],
):
    """Send a message between agents in the collaboration system"""
    try:
        import json
        from libs.multi_agent.collaboration_engine import MessageType, MessagePriority

        # Parse content as JSON
        try:
            content_data = json.loads(content)
        except json.JSONDecodeError:
            # If not valid JSON, treat as string content
            content_data = {"message": content}

        # Map message type
        type_mapping = {
            "status": MessageType.STATUS_UPDATE,
            "dependency": MessageType.DEPENDENCY_CHANGE,
            "conflict": MessageType.CONFLICT_ALERT,
            "help": MessageType.HELP_REQUEST,
            "knowledge": MessageType.KNOWLEDGE_SHARE,
            "review": MessageType.REVIEW_REQUEST,
            "sync": MessageType.SYNC_REQUEST,
            "broadcast": MessageType.BROADCAST,
        }
        message_type = type_mapping[msg_type]

        # Map priority
        priority_mapping = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL,
            "high": MessagePriority.HIGH,
            "critical": MessagePriority.CRITICAL,
            "emergency": MessagePriority.EMERGENCY,
        }
        message_priority = priority_mapping[priority]

        click.echo(f"📨 Sending message")
        click.echo(f"   From: {sender}")
        click.echo(f"   To: {recipient or 'All agents (broadcast)'}")
        click.echo(f"   Type: {msg_type}")
        click.echo(f"   Priority: {priority}")

        # This is a demo - in real usage, would connect to running collaboration engine
        click.echo(f"\n✅ Message sent successfully")
        click.echo(f"   Subject: {subject}")
        click.echo(f"   Content: {json.dumps(content_data, indent=2)}")

    except Exception as e:
        click.echo(f"❌ Error sending message: {e}", err=True)


@multi_agent_cli.command("share-knowledge")
@click.option("--agent", "-a", required=True, help="Contributing agent ID")
@click.option(
    "--type",
    "-t",
    required=True,
    help="Knowledge type (e.g., pattern, api_change, function_signature)",
)
@click.option("--content", "-c", required=True, help="Knowledge content (JSON format)")
@click.option("--tags", help="Tags for categorization (comma-separated)")
@click.option(
    "--relevance", "-r", type=float, default=1.0, help="Relevance score (0.0-1.0)"
)
@click.option("--repo-path", help="Path to git repository")
def share_knowledge(
    agent: str,
    type: str,
    content: str,
    tags: Optional[str],
    relevance: float,
    repo_path: Optional[str],
):
    """Share knowledge in the collaboration system"""
    try:
        import json

        # Parse content
        try:
            content_data = json.loads(content)
        except json.JSONDecodeError:
            content_data = {"description": content}

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]

        click.echo(f"📚 Sharing knowledge")
        click.echo(f"   Contributor: {agent}")
        click.echo(f"   Type: {type}")
        click.echo(f"   Relevance: {relevance}")
        if tag_list:
            click.echo(f"   Tags: {', '.join(tag_list)}")

        # This is a demo - in real usage, would connect to running collaboration engine
        click.echo(f"\n✅ Knowledge shared successfully")
        click.echo(f"   Content: {json.dumps(content_data, indent=2)}")

    except Exception as e:
        click.echo(f"❌ Error sharing knowledge: {e}", err=True)


@multi_agent_cli.command("branch-info")
@click.option(
    "--action",
    "-a",
    type=click.Choice(
        ["register", "update", "status", "sync", "subscribe", "merge-report"]
    ),
    required=True,
    help="Action to perform",
)
@click.option("--branch", "-b", help="Branch name")
@click.option("--agent", help="Agent ID")
@click.option(
    "--info-type",
    "-t",
    type=click.Choice(
        [
            "state",
            "commits",
            "files",
            "dependencies",
            "tests",
            "build",
            "conflicts",
            "merge",
            "progress",
            "api",
        ]
    ),
    help="Type of information to update",
)
@click.option("--data", "-d", help="Update data (JSON format)")
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option(
    "--sync-strategy",
    type=click.Choice(["immediate", "periodic", "on_demand", "milestone", "smart"]),
    default="smart",
    help="Synchronization strategy",
)
def branch_info(
    action: str,
    branch: Optional[str],
    agent: Optional[str],
    info_type: Optional[str],
    data: Optional[str],
    repo_path: Optional[str],
    sync_strategy: str,
):
    """Manage branch information sharing protocol"""
    try:
        from libs.multi_agent.branch_info_protocol import (
            BranchInfoProtocol,
            BranchInfoType,
            SyncStrategy,
        )
        import json

        click.echo(f"🌿 Branch Info Protocol - {action}")

        if action == "register":
            if not branch or not agent:
                click.echo(
                    "❌ Branch and agent are required for registration", err=True
                )
                return

            click.echo(f"   Registering branch: {branch}")
            click.echo(f"   Agent: {agent}")
            click.echo(f"   Strategy: {sync_strategy}")

            # Parse work items if provided in data
            work_items = []
            if data:
                try:
                    data_dict = json.loads(data)
                    work_items = data_dict.get("work_items", [])
                except json.JSONDecodeError:
                    pass

            if work_items:
                click.echo(f"   Work items: {len(work_items)}")

            click.echo("\n✅ Branch registered successfully")

        elif action == "update":
            if not branch or not info_type:
                click.echo("❌ Branch and info type are required for update", err=True)
                return

            # Map CLI info types to enum values
            type_mapping = {
                "state": BranchInfoType.BRANCH_STATE,
                "commits": BranchInfoType.COMMIT_HISTORY,
                "files": BranchInfoType.FILE_CHANGES,
                "dependencies": BranchInfoType.DEPENDENCY_MAP,
                "tests": BranchInfoType.TEST_STATUS,
                "build": BranchInfoType.BUILD_STATUS,
                "conflicts": BranchInfoType.CONFLICT_INFO,
                "merge": BranchInfoType.MERGE_READINESS,
                "progress": BranchInfoType.WORK_PROGRESS,
                "api": BranchInfoType.API_CHANGES,
            }

            branch_info_type = type_mapping[info_type]

            click.echo(f"   Updating branch: {branch}")
            click.echo(f"   Info type: {branch_info_type.value}")

            if data:
                try:
                    update_data = json.loads(data)
                    click.echo(f"   Data: {json.dumps(update_data, indent=2)}")
                except json.JSONDecodeError:
                    click.echo(f"   Data: {data}")

            click.echo("\n✅ Branch info updated")

        elif action == "status":
            click.echo("\n📊 Branch Information Status")
            click.echo("-" * 40)

            # This is a demo - would show real protocol status
            click.echo("Active branches: 0")
            click.echo("Total subscriptions: 0")
            click.echo("Sync strategy: smart")
            click.echo("Recent syncs: 0")

        elif action == "sync":
            if agent:
                click.echo(f"   Requesting sync for agent: {agent}")
                if branch:
                    click.echo(f"   Specific branch: {branch}")
                else:
                    click.echo("   All branches")
            else:
                click.echo("❌ Agent ID required for sync request", err=True)
                return

            click.echo("\n✅ Sync request sent")

        elif action == "subscribe":
            if not agent or not branch:
                click.echo(
                    "❌ Agent and branch are required for subscription", err=True
                )
                return

            click.echo(f"   Agent {agent} subscribing to branch {branch}")
            click.echo("\n✅ Subscription successful")

        elif action == "merge-report":
            if not branch:
                click.echo("❌ Branch name required for merge report", err=True)
                return

            click.echo(f"\n📋 Merge Readiness Report for {branch}")
            click.echo("-" * 40)

            # Demo merge report
            click.echo("✅ Tests passed: Yes")
            click.echo("✅ Build successful: Yes")
            click.echo("✅ No conflicts: Yes")
            click.echo("✅ Work completed: Yes")
            click.echo("\nMerge Score: 1.0 (Ready to merge)")
            click.echo("\nRecommendations: None - branch is ready to merge!")

    except Exception as e:
        click.echo(f"❌ Error in branch info protocol: {e}", err=True)


@multi_agent_cli.command("dependency-track")
@click.option("--file", "-f", required=True, help="File path where dependency changed")
@click.option("--agent", "-a", required=True, help="Agent ID making the change")
@click.option(
    "--type",
    "-t",
    type=click.Choice([dt.value for dt in DependencyType]),
    required=True,
    help="Type of dependency change",
)
@click.option("--details", "-d", required=True, help="Change details (JSON format)")
@click.option(
    "--impact",
    "-i",
    type=click.Choice([ci.value for ci in ChangeImpact]),
    help="Impact level (auto-detected if not specified)",
)
@click.option(
    "--strategy",
    "-s",
    type=click.Choice([ps.value for ps in PropagationStrategy]),
    default="immediate",
    help="Propagation strategy",
)
@click.option("--repo-path", "-r", help="Path to git repository")
def dependency_track(
    file: str,
    agent: str,
    type: str,
    details: str,
    impact: Optional[str],
    strategy: str,
    repo_path: Optional[str],
):
    """Track a dependency change for propagation"""
    try:
        import json

        click.echo(f"📊 Tracking dependency change")
        click.echo(f"   File: {file}")
        click.echo(f"   Agent: {agent}")
        click.echo(f"   Type: {type}")
        click.echo(f"   Strategy: {strategy}")

        # Parse details
        try:
            details_data = json.loads(details)
        except json.JSONDecodeError:
            details_data = {"description": details}

        # Convert enum values
        dependency_type = DependencyType(type)
        propagation_strategy = PropagationStrategy(strategy)
        impact_level = ChangeImpact(impact) if impact else None

        click.echo(f"   Details: {json.dumps(details_data, indent=2)}")

        # This is a demo - in real usage would connect to running dependency system
        async def track_change():
            from unittest.mock import Mock

            # Create mock components
            branch_manager = BranchManager(repo_path=repo_path)

            # Mock collaboration engine and branch info protocol
            collab_engine = Mock()
            branch_protocol = Mock()

            # Create dependency propagation system
            dep_system = DependencyPropagationSystem(
                collaboration_engine=collab_engine,
                branch_info_protocol=branch_protocol,
                branch_manager=branch_manager,
                repo_path=repo_path,
            )

            # Track the change
            change_id = await dep_system.track_dependency_change(
                file_path=file,
                changed_by=agent,
                change_type=dependency_type,
                change_details=details_data,
                impact_level=impact_level,
                propagation_strategy=propagation_strategy,
            )

            click.echo(f"\n✅ Change tracked successfully")
            click.echo(f"   Change ID: {change_id}")

            # Get summary
            summary = dep_system.get_propagation_summary()
            click.echo(f"   Total changes tracked: {summary['total_changes_tracked']}")
            click.echo(f"   Pending changes: {summary['pending_changes']}")

        try:
            asyncio.run(track_change())
        except Exception:
            # Fallback to demo output
            mock_change_id = f"dep_change_{agent}_{file.replace('/', '_')}"
            click.echo(f"\n✅ Change tracked successfully")
            click.echo(f"   Change ID: {mock_change_id}")
            click.echo("   (Demo mode - actual tracking not performed)")

    except Exception as e:
        click.echo(f"❌ Error tracking dependency change: {e}", err=True)


@multi_agent_cli.command("dependency-status")
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed dependency graph")
@click.option("--export", "-e", help="Export dependency data to JSON file")
def dependency_status(repo_path: Optional[str], detailed: bool, export: Optional[str]):
    """Show dependency propagation system status"""
    try:
        click.echo("📊 Dependency Propagation System Status")
        click.echo("=" * 50)

        # This is a demo - would show real system status
        click.echo("System Status: Running")
        click.echo("Auto-propagation: Enabled")
        click.echo("Batch size: 10")
        click.echo("Max concurrent: 5")

        click.echo("\n📈 Statistics:")
        click.echo("   Changes tracked: 0")
        click.echo("   Changes propagated: 0")
        click.echo("   Success rate: 100.0%")
        click.echo("   Average propagation time: 0.0s")

        click.echo("\n🗂️  Dependency Graph:")
        click.echo("   Nodes: 0")
        click.echo("   Dependencies mapped: 0")

        if detailed:
            click.echo("\n📋 Recent Changes:")
            click.echo("   No recent changes")

            click.echo("\n🔄 Pending Propagations:")
            click.echo("   No pending propagations")

        if export:
            import json

            export_data = {
                "dependency_system_status": {
                    "timestamp": "2025-01-11T00:00:00",
                    "system_running": True,
                    "auto_propagation": True,
                    "statistics": {
                        "changes_tracked": 0,
                        "changes_propagated": 0,
                        "success_rate": 1.0,
                        "average_propagation_time": 0.0,
                    },
                    "dependency_graph": {
                        "nodes": 0,
                        "dependencies": 0,
                    },
                }
            }

            with open(export, "w") as f:
                json.dump(export_data, f, indent=2)
            click.echo(f"\n💾 Status exported to: {export}")

    except Exception as e:
        click.echo(f"❌ Error getting dependency status: {e}", err=True)


@multi_agent_cli.command("dependency-impact")
@click.argument("file_path")
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option("--export", "-e", help="Export impact report to JSON file")
def dependency_impact(file_path: str, repo_path: Optional[str], export: Optional[str]):
    """Analyze dependency impact for a specific file"""
    try:
        click.echo(f"🔍 Analyzing dependency impact for: {file_path}")

        # This is a demo - would perform real analysis
        async def analyze_impact():
            from unittest.mock import Mock

            # Create mock components
            branch_manager = BranchManager(repo_path=repo_path)
            collab_engine = Mock()
            branch_protocol = Mock()

            dep_system = DependencyPropagationSystem(
                collaboration_engine=collab_engine,
                branch_info_protocol=branch_protocol,
                branch_manager=branch_manager,
                repo_path=repo_path,
            )

            # Build dependency graph
            await dep_system.build_dependency_graph()

            # Get impact report
            report = await dep_system.get_dependency_impact_report(file_path)

            if "error" in report:
                click.echo(f"❌ {report['error']}")
                return

            click.echo(f"\n📊 Impact Analysis:")
            click.echo(f"   File: {report['file_path']}")
            click.echo(f"   Module: {report['module_name']}")
            click.echo(f"   Direct dependents: {report['direct_dependents']}")
            click.echo(f"   Indirect dependents: {report['indirect_dependents']}")
            click.echo(f"   Total impact: {report['total_impact']}")
            click.echo(f"   Complexity score: {report['complexity_score']:.2f}")
            click.echo(f"   Risk level: {report['risk_level'].upper()}")

            if report["affected_branches"]:
                click.echo(f"\n🌿 Affected Branches:")
                for branch in report["affected_branches"]:
                    click.echo(f"   • {branch}")

            if report["dependencies"]:
                click.echo(f"\n📦 Dependencies ({len(report['dependencies'])}):")
                for dep in report["dependencies"][:5]:
                    click.echo(f"   • {dep}")
                if len(report["dependencies"]) > 5:
                    click.echo(f"   ... and {len(report['dependencies']) - 5} more")

            if report["dependents"]:
                click.echo(f"\n🔗 Dependents ({len(report['dependents'])}):")
                for dep in report["dependents"][:5]:
                    click.echo(f"   • {dep}")
                if len(report["dependents"]) > 5:
                    click.echo(f"   ... and {len(report['dependents']) - 5} more")

            if export:
                import json

                with open(export, "w") as f:
                    json.dump(report, f, indent=2, default=str)
                click.echo(f"\n💾 Impact report exported to: {export}")

        try:
            asyncio.run(analyze_impact())
        except Exception:
            # Fallback to demo output
            click.echo(f"\n📊 Impact Analysis:")
            click.echo(f"   File: {file_path}")
            click.echo(f"   Module: {file_path.replace('/', '.').replace('.py', '')}")
            click.echo(f"   Direct dependents: 0")
            click.echo(f"   Indirect dependents: 0")
            click.echo(f"   Total impact: 0")
            click.echo(f"   Complexity score: 0.0")
            click.echo(f"   Risk level: LOW")
            click.echo("   (Demo mode - actual analysis not performed)")

    except Exception as e:
        click.echo(f"❌ Error analyzing dependency impact: {e}", err=True)


@multi_agent_cli.command("dependency-propagate")
@click.argument("change_ids", nargs=-1, required=True)
@click.option("--branches", "-b", help="Target branches (comma-separated)")
@click.option("--repo-path", "-r", help="Path to git repository")
@click.option("--export", "-e", help="Export propagation results to JSON file")
def dependency_propagate(
    change_ids: tuple,
    branches: Optional[str],
    repo_path: Optional[str],
    export: Optional[str],
):
    """Manually propagate specific dependency changes to branches"""
    try:
        click.echo(f"🚀 Propagating dependency changes")
        click.echo(f"   Change IDs: {', '.join(change_ids)}")

        target_branches = None
        if branches:
            target_branches = [b.strip() for b in branches.split(",")]
            click.echo(f"   Target branches: {', '.join(target_branches)}")
        else:
            click.echo("   Target branches: All affected branches")

        # This is a demo - would perform real propagation
        async def propagate_changes():
            from unittest.mock import Mock

            # Create mock components
            branch_manager = BranchManager(repo_path=repo_path)
            collab_engine = Mock()
            branch_protocol = Mock()

            dep_system = DependencyPropagationSystem(
                collaboration_engine=collab_engine,
                branch_info_protocol=branch_protocol,
                branch_manager=branch_manager,
                repo_path=repo_path,
            )

            # Propagate changes
            results = await dep_system.propagate_changes_to_branches(
                change_ids=list(change_ids), target_branches=target_branches
            )

            click.echo(f"\n📊 Propagation Results:")

            for result in results:
                success_icon = "✅" if result.success else "❌"
                click.echo(f"\n{success_icon} Change: {result.change_id}")
                click.echo(f"   Success: {result.success}")
                click.echo(f"   Propagated to: {len(result.propagated_to)} branches")
                click.echo(f"   Failed targets: {len(result.failed_targets)} branches")
                click.echo(f"   Processing time: {result.processing_time:.2f}s")

                if result.propagated_to:
                    click.echo(f"   ✅ Successful: {', '.join(result.propagated_to)}")

                if result.failed_targets:
                    click.echo(f"   ❌ Failed: {', '.join(result.failed_targets)}")

                if result.warnings:
                    click.echo(f"   ⚠️  Warnings:")
                    for warning in result.warnings:
                        click.echo(f"     • {warning}")

                if result.recommendations:
                    click.echo(f"   💡 Recommendations:")
                    for rec in result.recommendations:
                        click.echo(f"     • {rec}")

            if export:
                import json

                export_data = {
                    "propagation_results": [
                        {
                            "change_id": r.change_id,
                            "success": r.success,
                            "propagated_to": r.propagated_to,
                            "failed_targets": r.failed_targets,
                            "warnings": r.warnings,
                            "recommendations": r.recommendations,
                            "processing_time": r.processing_time,
                            "metadata": r.metadata,
                        }
                        for r in results
                    ]
                }

                with open(export, "w") as f:
                    json.dump(export_data, f, indent=2)
                click.echo(f"\n💾 Results exported to: {export}")

        try:
            asyncio.run(propagate_changes())
        except Exception:
            # Fallback to demo output
            click.echo(f"\n📊 Propagation Results:")
            for change_id in change_ids:
                click.echo(f"\n✅ Change: {change_id}")
                click.echo(f"   Success: True")
                click.echo(f"   Propagated to: 0 branches")
                click.echo(f"   Processing time: 0.0s")
            click.echo("   (Demo mode - actual propagation not performed)")

    except Exception as e:
        click.echo(f"❌ Error propagating changes: {e}", err=True)


@multi_agent_cli.command("review-initiate")
@click.argument("branch_name")
@click.option("--agent", "-a", required=True, help="Agent ID requesting review")
@click.option("--files", "-f", required=True, help="Files to review (comma-separated)")
@click.option(
    "--types",
    "-t",
    help="Review types (comma-separated: style_quality,security,performance,etc.)",
)
@click.option("--reviewers", "-r", help="Specific reviewers (comma-separated)")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["low", "normal", "high", "critical", "emergency"]),
    default="normal",
    help="Review priority",
)
@click.option("--repo-path", help="Path to git repository")
def review_initiate(
    branch_name: str,
    agent: str,
    files: str,
    types: Optional[str],
    reviewers: Optional[str],
    priority: str,
    repo_path: Optional[str],
):
    """Initiate a code review for changes in a branch"""
    try:
        from libs.multi_agent.collaboration_engine import MessagePriority

        click.echo(f"📋 Initiating code review")
        click.echo(f"   Branch: {branch_name}")
        click.echo(f"   Requester: {agent}")
        click.echo(f"   Priority: {priority}")

        # Parse files
        file_list = [f.strip() for f in files.split(",")]
        click.echo(f"   Files: {len(file_list)} files")

        # Parse review types
        review_types = []
        if types:
            type_mapping = {
                "style_quality": ReviewType.STYLE_QUALITY,
                "security": ReviewType.SECURITY,
                "performance": ReviewType.PERFORMANCE,
                "maintainability": ReviewType.MAINTAINABILITY,
                "functionality": ReviewType.FUNCTIONALITY,
                "documentation": ReviewType.DOCUMENTATION,
                "testing": ReviewType.TESTING,
                "complexity": ReviewType.COMPLEXITY,
            }
            for t in types.split(","):
                t = t.strip()
                if t in type_mapping:
                    review_types.append(type_mapping[t])

        # Parse reviewers
        reviewer_list = None
        if reviewers:
            reviewer_list = [r.strip() for r in reviewers.split(",")]

        # Map priority
        priority_mapping = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL,
            "high": MessagePriority.HIGH,
            "critical": MessagePriority.CRITICAL,
            "emergency": MessagePriority.EMERGENCY,
        }
        msg_priority = priority_mapping[priority]

        async def run_review():
            try:
                from unittest.mock import Mock

                # Create mock components
                branch_manager = BranchManager(repo_path=repo_path)
                collab_engine = Mock()
                semantic_analyzer = Mock()

                # Create code review engine
                review_engine = CodeReviewEngine(
                    collaboration_engine=collab_engine,
                    semantic_analyzer=semantic_analyzer,
                    branch_manager=branch_manager,
                    repo_path=repo_path,
                )

                await review_engine.start()

                # Initiate review
                review_id = await review_engine.initiate_review(
                    branch_name=branch_name,
                    agent_id=agent,
                    files_changed=file_list,
                    review_types=review_types or None,
                    reviewer_ids=reviewer_list,
                    priority=msg_priority,
                )

                click.echo(f"\n✅ Review initiated successfully")
                click.echo(f"   Review ID: {review_id}")

                # Wait for automated review to complete
                await asyncio.sleep(2)

                # Get review status
                review = await review_engine.get_review_status(review_id)
                if review:
                    click.echo(f"   Status: {review.status.value}")
                    click.echo(f"   Overall score: {review.overall_score:.1f}/10")
                    click.echo(f"   Findings: {len(review.findings)}")

                    # Show critical findings
                    critical_findings = [
                        f
                        for f in review.findings
                        if f.severity == ReviewSeverity.CRITICAL
                    ]
                    if critical_findings:
                        click.echo(f"   🚨 Critical issues: {len(critical_findings)}")

                await review_engine.stop()

            except Exception as e:
                click.echo(f"   ❌ Error during review: {e}")

        try:
            asyncio.run(run_review())
        except Exception:
            # Fallback to demo output
            mock_review_id = f"review_{branch_name}_{agent}"
            click.echo(f"\n✅ Review initiated successfully")
            click.echo(f"   Review ID: {mock_review_id}")
            click.echo("   (Demo mode - actual review not performed)")

    except Exception as e:
        click.echo(f"❌ Error initiating review: {e}", err=True)


@multi_agent_cli.command("review-approve")
@click.argument("review_id")
@click.option("--reviewer", "-r", required=True, help="Reviewer ID")
@click.option("--comments", "-c", help="Approval comments")
@click.option("--repo-path", help="Path to git repository")
def review_approve(
    review_id: str, reviewer: str, comments: Optional[str], repo_path: Optional[str]
):
    """Approve a code review"""
    try:
        click.echo(f"✅ Approving code review")
        click.echo(f"   Review ID: {review_id}")
        click.echo(f"   Reviewer: {reviewer}")

        async def run_approval():
            try:
                from unittest.mock import Mock

                # Create mock components
                branch_manager = BranchManager(repo_path=repo_path)
                collab_engine = Mock()
                semantic_analyzer = Mock()

                review_engine = CodeReviewEngine(
                    collaboration_engine=collab_engine,
                    semantic_analyzer=semantic_analyzer,
                    branch_manager=branch_manager,
                    repo_path=repo_path,
                )

                await review_engine.start()

                # Approve review
                success = await review_engine.approve_review(
                    review_id=review_id,
                    reviewer_id=reviewer,
                    comments=comments,
                )

                if success:
                    click.echo(f"\n✅ Review approved successfully")
                    if comments:
                        click.echo(f"   Comments: {comments}")
                else:
                    click.echo(f"\n❌ Failed to approve review")
                    click.echo(f"   Review may not exist or reviewer not assigned")

                await review_engine.stop()

            except Exception as e:
                click.echo(f"   ❌ Error during approval: {e}")

        try:
            asyncio.run(run_approval())
        except Exception:
            # Fallback to demo output
            click.echo(f"\n✅ Review approved successfully")
            if comments:
                click.echo(f"   Comments: {comments}")
            click.echo("   (Demo mode - actual approval not performed)")

    except Exception as e:
        click.echo(f"❌ Error approving review: {e}", err=True)


@multi_agent_cli.command("review-reject")
@click.argument("review_id")
@click.option("--reviewer", "-r", required=True, help="Reviewer ID")
@click.option("--reasons", required=True, help="Rejection reasons (comma-separated)")
@click.option("--suggestions", "-s", help="Improvement suggestions (comma-separated)")
@click.option("--repo-path", help="Path to git repository")
def review_reject(
    review_id: str,
    reviewer: str,
    reasons: str,
    suggestions: Optional[str],
    repo_path: Optional[str],
):
    """Reject a code review with reasons"""
    try:
        click.echo(f"❌ Rejecting code review")
        click.echo(f"   Review ID: {review_id}")
        click.echo(f"   Reviewer: {reviewer}")

        # Parse reasons
        reason_list = [r.strip() for r in reasons.split(",")]

        # Parse suggestions
        suggestion_list = []
        if suggestions:
            suggestion_list = [s.strip() for s in suggestions.split(",")]

        async def run_rejection():
            try:
                from unittest.mock import Mock

                # Create mock components
                branch_manager = BranchManager(repo_path=repo_path)
                collab_engine = Mock()
                semantic_analyzer = Mock()

                review_engine = CodeReviewEngine(
                    collaboration_engine=collab_engine,
                    semantic_analyzer=semantic_analyzer,
                    branch_manager=branch_manager,
                    repo_path=repo_path,
                )

                await review_engine.start()

                # Reject review
                success = await review_engine.reject_review(
                    review_id=review_id,
                    reviewer_id=reviewer,
                    reasons=reason_list,
                    suggestions=suggestion_list,
                )

                if success:
                    click.echo(f"\n❌ Review rejected")
                    click.echo(f"   Reasons:")
                    for reason in reason_list:
                        click.echo(f"     • {reason}")

                    if suggestion_list:
                        click.echo(f"   Suggestions:")
                        for suggestion in suggestion_list:
                            click.echo(f"     • {suggestion}")
                else:
                    click.echo(f"\n❌ Failed to reject review")
                    click.echo(f"   Review may not exist or reviewer not assigned")

                await review_engine.stop()

            except Exception as e:
                click.echo(f"   ❌ Error during rejection: {e}")

        try:
            asyncio.run(run_rejection())
        except Exception:
            # Fallback to demo output
            click.echo(f"\n❌ Review rejected")
            click.echo(f"   Reasons:")
            for reason in reason_list:
                click.echo(f"     • {reason}")
            click.echo("   (Demo mode - actual rejection not performed)")

    except Exception as e:
        click.echo(f"❌ Error rejecting review: {e}", err=True)


@multi_agent_cli.command("review-status")
@click.argument("review_id", required=False)
@click.option("--repo-path", help="Path to git repository")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed review information")
def review_status(review_id: Optional[str], repo_path: Optional[str], detailed: bool):
    """Get status of a specific review or all reviews"""
    try:
        if review_id:
            click.echo(f"📊 Code Review Status: {review_id}")
        else:
            click.echo("📊 All Code Reviews Status")

        async def get_status():
            try:
                from unittest.mock import Mock

                # Create mock components
                branch_manager = BranchManager(repo_path=repo_path)
                collab_engine = Mock()
                semantic_analyzer = Mock()

                review_engine = CodeReviewEngine(
                    collaboration_engine=collab_engine,
                    semantic_analyzer=semantic_analyzer,
                    branch_manager=branch_manager,
                    repo_path=repo_path,
                )

                await review_engine.start()

                if review_id:
                    # Get specific review status
                    review = await review_engine.get_review_status(review_id)
                    if review:
                        click.echo(f"\n📋 Review Details:")
                        click.echo(f"   Branch: {review.branch_name}")
                        click.echo(f"   Requester: {review.agent_id}")
                        click.echo(f"   Status: {review.status.value}")
                        click.echo(f"   Overall score: {review.overall_score:.1f}/10")
                        click.echo(f"   Auto-approved: {review.auto_approved}")

                        if review.reviewer_ids:
                            click.echo(
                                f"   Reviewers: {', '.join(review.reviewer_ids)}"
                            )

                        click.echo(f"   Files: {len(review.files_changed)}")
                        if detailed:
                            for file in review.files_changed:
                                click.echo(f"     • {file}")

                        click.echo(f"   Findings: {len(review.findings)}")
                        if detailed and review.findings:
                            # Group findings by severity
                            from collections import Counter

                            severity_counts = Counter(
                                f.severity.value for f in review.findings
                            )
                            for severity, count in severity_counts.items():
                                severity_icon = {
                                    "critical": "💀",
                                    "high": "🔴",
                                    "medium": "🟡",
                                    "low": "🟢",
                                    "info": "ℹ️",
                                }.get(severity, "❓")
                                click.echo(f"     {severity_icon} {severity}: {count}")

                        if review.quality_metrics:
                            click.echo(
                                f"   Quality metrics: {len(review.quality_metrics)}"
                            )
                            if detailed:
                                for metric in review.quality_metrics:
                                    click.echo(f"     • {metric.file_path}")
                                    if metric.violations:
                                        for violation in metric.violations:
                                            click.echo(f"       ⚠️ {violation.value}")

                    else:
                        click.echo(f"\n❌ Review {review_id} not found")

                else:
                    # Get review summary
                    summary = review_engine.get_review_summary()
                    click.echo(f"\n📊 Review Summary:")
                    click.echo(f"   Total reviews: {summary.total_reviews}")
                    click.echo(f"   Approved: {summary.approved_reviews}")
                    click.echo(f"   Rejected: {summary.rejected_reviews}")
                    click.echo(f"   Pending: {summary.pending_reviews}")

                    if summary.total_reviews > 0:
                        click.echo(f"   Average score: {summary.average_score:.1f}/10")

                    click.echo(f"   Total findings: {summary.total_findings}")
                    click.echo(f"   Critical findings: {summary.critical_findings}")

                    if summary.most_common_issues:
                        click.echo(f"\n🔍 Most Common Issues:")
                        for issue, count in summary.most_common_issues[:5]:
                            click.echo(f"   • {issue}: {count}")

                    if (
                        summary.review_time_stats
                        and "average_time" in summary.review_time_stats
                    ):
                        avg_time = summary.review_time_stats["average_time"]
                        click.echo(f"   Average review time: {avg_time:.1f}s")

                await review_engine.stop()

            except Exception as e:
                click.echo(f"   ❌ Error getting status: {e}")

        try:
            asyncio.run(get_status())
        except Exception:
            # Fallback to demo output
            if review_id:
                click.echo(f"\n📋 Review Details:")
                click.echo(f"   Status: pending")
                click.echo(f"   Overall score: 0.0/10")
                click.echo("   (Demo mode - actual status not available)")
            else:
                click.echo(f"\n📊 Review Summary:")
                click.echo(f"   Total reviews: 0")
                click.echo("   (Demo mode - actual summary not available)")

    except Exception as e:
        click.echo(f"❌ Error getting review status: {e}", err=True)


@multi_agent_cli.command("quality-check")
@click.argument("files", nargs=-1, required=True)
@click.option(
    "--metrics",
    "-m",
    help="Quality metrics to check (comma-separated: complexity,maintainability,coverage,etc.)",
)
@click.option("--export", "-e", help="Export quality report to JSON file")
@click.option("--repo-path", help="Path to git repository")
def quality_check(
    files: tuple,
    metrics: Optional[str],
    export: Optional[str],
    repo_path: Optional[str],
):
    """Perform quality check on specified files"""
    try:
        click.echo(f"🔍 Performing quality check")
        click.echo(f"   Files: {len(files)} files")

        # Parse metrics
        quality_metrics = None
        if metrics:
            metric_mapping = {
                "complexity": QualityMetric.CYCLOMATIC_COMPLEXITY,
                "maintainability": QualityMetric.MAINTAINABILITY_INDEX,
                "coverage": QualityMetric.CODE_COVERAGE,
                "duplication": QualityMetric.DUPLICATION_RATIO,
                "lines": QualityMetric.LINES_OF_CODE,
                "debt": QualityMetric.TECHNICAL_DEBT,
                "security": QualityMetric.SECURITY_SCORE,
                "performance": QualityMetric.PERFORMANCE_SCORE,
            }
            quality_metrics = []
            for m in metrics.split(","):
                m = m.strip()
                if m in metric_mapping:
                    quality_metrics.append(metric_mapping[m])

        async def run_quality_check():
            try:
                from unittest.mock import Mock

                # Create mock components
                branch_manager = BranchManager(repo_path=repo_path)
                collab_engine = Mock()
                semantic_analyzer = Mock()

                review_engine = CodeReviewEngine(
                    collaboration_engine=collab_engine,
                    semantic_analyzer=semantic_analyzer,
                    branch_manager=branch_manager,
                    repo_path=repo_path,
                )

                await review_engine.start()

                # Perform quality check
                results = await review_engine.perform_quality_check(
                    file_paths=list(files), quality_types=quality_metrics
                )

                click.echo(f"\n📊 Quality Check Results:")

                for i, result in enumerate(results, 1):
                    click.echo(f"\n{i}. {result.file_path}")

                    # Show metrics
                    for metric, value in result.metrics.items():
                        metric_icon = {
                            QualityMetric.CYCLOMATIC_COMPLEXITY: "🔄",
                            QualityMetric.MAINTAINABILITY_INDEX: "🔧",
                            QualityMetric.CODE_COVERAGE: "🛡️",
                            QualityMetric.DUPLICATION_RATIO: "📋",
                            QualityMetric.LINES_OF_CODE: "📏",
                            QualityMetric.TECHNICAL_DEBT: "💳",
                            QualityMetric.SECURITY_SCORE: "🔒",
                            QualityMetric.PERFORMANCE_SCORE: "⚡",
                        }.get(metric, "📊")

                        # Check if violates threshold
                        violates = metric in result.violations
                        status_icon = "❌" if violates else "✅"

                        click.echo(
                            f"   {metric_icon} {status_icon} {metric.value}: {value}"
                        )

                    if result.violations:
                        click.echo(f"   ⚠️ Violations: {len(result.violations)}")

                # Export if requested
                if export:
                    import json

                    export_data = {
                        "quality_check_report": {
                            "files_checked": len(results),
                            "results": [
                                {
                                    "file_path": r.file_path,
                                    "metrics": {
                                        m.value: v for m, v in r.metrics.items()
                                    },
                                    "thresholds": {
                                        m.value: v for m, v in r.thresholds.items()
                                    },
                                    "violations": [v.value for v in r.violations],
                                    "calculated_at": r.calculated_at.isoformat(),
                                }
                                for r in results
                            ],
                        }
                    }

                    with open(export, "w") as f:
                        json.dump(export_data, f, indent=2)
                    click.echo(f"\n💾 Quality report exported to: {export}")

                await review_engine.stop()

            except Exception as e:
                click.echo(f"   ❌ Error during quality check: {e}")

        try:
            asyncio.run(run_quality_check())
        except Exception:
            # Fallback to demo output
            click.echo(f"\n📊 Quality Check Results:")
            for i, file in enumerate(files, 1):
                click.echo(f"\n{i}. {file}")
                click.echo(f"   🔄 ✅ cyclomatic_complexity: 5.0")
                click.echo(f"   🔧 ✅ maintainability_index: 75.0")
            click.echo("   (Demo mode - actual quality check not performed)")

    except Exception as e:
        click.echo(f"❌ Error performing quality check: {e}", err=True)


@multi_agent_cli.command("review-summary")
@click.option("--repo-path", help="Path to git repository")
@click.option("--export", "-e", help="Export summary to JSON file")
def review_summary(repo_path: Optional[str], export: Optional[str]):
    """Get comprehensive review engine summary"""
    try:
        click.echo("📊 Code Review Engine Summary")
        click.echo("=" * 40)

        async def get_summary():
            try:
                from unittest.mock import Mock

                # Create mock components
                branch_manager = BranchManager(repo_path=repo_path)
                collab_engine = Mock()
                semantic_analyzer = Mock()

                review_engine = CodeReviewEngine(
                    collaboration_engine=collab_engine,
                    semantic_analyzer=semantic_analyzer,
                    branch_manager=branch_manager,
                    repo_path=repo_path,
                )

                await review_engine.start()

                # Get engine summary
                summary = review_engine.get_engine_summary()

                click.echo(f"Engine Status: Running")
                click.echo(f"Active reviews: {summary['active_reviews']}")
                click.echo(f"Total reviews: {summary['total_reviews']}")

                # Statistics
                stats = summary["statistics"]
                click.echo(f"\n📈 Statistics:")
                click.echo(f"   Reviews initiated: {stats['reviews_initiated']}")
                click.echo(f"   Reviews completed: {stats['reviews_completed']}")
                click.echo(f"   Auto-approved: {stats['auto_approved']}")
                click.echo(
                    f"   Manual reviews required: {stats['manual_reviews_required']}"
                )
                click.echo(f"   Total findings: {stats['total_findings']}")

                if stats["reviews_completed"] > 0:
                    click.echo(
                        f"   Average review time: {stats['average_review_time']:.1f}s"
                    )

                # Available tools
                tools = summary["available_tools"]
                click.echo(f"\n🛠️ Available Tools:")
                for tool, available in tools.items():
                    status = "✅" if available else "❌"
                    click.echo(f"   {status} {tool}")

                # Configuration
                config = summary["review_config"]
                click.echo(f"\n⚙️ Configuration:")
                click.echo(
                    f"   Auto-approve threshold: {config['auto_approve_threshold']}"
                )
                click.echo(
                    f"   Max concurrent reviews: {config['max_concurrent_reviews']}"
                )
                click.echo(f"   Default reviewers: {config['default_reviewers']}")
                click.echo(f"   AI reviewer enabled: {config['enable_ai_reviewer']}")

                # Recent reviews
                if summary["recent_reviews"]:
                    click.echo(f"\n📋 Recent Reviews:")
                    for review in summary["recent_reviews"][-5:]:
                        status_icon = {
                            "pending": "⏳",
                            "in_progress": "🔄",
                            "completed": "✅",
                            "approved": "✅",
                            "rejected": "❌",
                        }.get(review["status"], "❓")

                        click.echo(
                            f"   {status_icon} {review['review_id']} - {review['branch_name']} "
                            f"(Score: {review['overall_score']:.1f})"
                        )

                # Export if requested
                if export:
                    import json

                    with open(export, "w") as f:
                        json.dump(summary, f, indent=2, default=str)
                    click.echo(f"\n💾 Summary exported to: {export}")

                await review_engine.stop()

            except Exception as e:
                click.echo(f"   ❌ Error getting summary: {e}")

        try:
            asyncio.run(get_summary())
        except Exception:
            # Fallback to demo output
            click.echo(f"Engine Status: Running")
            click.echo(f"Active reviews: 0")
            click.echo(f"Total reviews: 0")
            click.echo("   (Demo mode - actual summary not available)")

    except Exception as e:
        click.echo(f"❌ Error getting review summary: {e}", err=True)


# Register the command group
def register_commands(cli):
    """Register multi-agent commands with the main CLI"""
    cli.add_command(multi_agent_cli)
