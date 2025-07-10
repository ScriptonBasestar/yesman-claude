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
from libs.multi_agent.branch_manager import BranchManager


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


# Register the command group
def register_commands(cli):
    """Register multi-agent commands with the main CLI"""
    cli.add_command(multi_agent_cli)
