"""Context-aware automation and workflow management commands"""

import click
import time
import asyncio
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

from libs.automation.automation_manager import AutomationManager
from libs.automation.context_detector import ContextType
from libs.automation.workflow_engine import WorkflowChain


@click.group()
def automate():
    """Context-aware automation and workflow management"""
    pass


@automate.command()
@click.option('--project-path', '-p', default=".", help='Project directory path')
def status(project_path):
    """Show automation system status"""
    console = Console()
    
    try:
        project_path = Path(project_path).resolve()
        automation_manager = AutomationManager(project_path)
        
        # Get current status
        stats = automation_manager.get_statistics()
        
        # Create status overview
        overview = Panel(
            f"Project: {project_path.name}\\n"
            f"Monitoring: {'✅ Active' if automation_manager.is_monitoring else '❌ Inactive'}\\n"
            f"Uptime: {_format_duration(time.time() - stats['start_time'])}\\n"
            f"Contexts Detected: {stats['contexts_detected']}\\n"
            f"Workflows Triggered: {stats['workflows_triggered']}\\n"
            f"Workflows Completed: {stats['workflows_completed']}",
            title="🤖 Automation Status",
            border_style="blue"
        )
        console.print(overview)
        
        # Show available context types
        context_table = Table(title="📊 Context Detection Capabilities", show_header=True)
        context_table.add_column("Context Type", style="cyan")
        context_table.add_column("Description", style="white")
        context_table.add_column("Triggers", style="yellow")
        
        context_info = {
            ContextType.GIT_COMMIT: ("Git Commit", "Detects new commits", "commit hooks, git log"),
            ContextType.TEST_FAILURE: ("Test Failure", "Detects failing tests", "test output, CI status"),
            ContextType.BUILD_EVENT: ("Build Event", "Detects build starts/completion", "build scripts, CI"),
            ContextType.DEPENDENCY_UPDATE: ("Dependencies", "Detects dependency changes", "package files"),
            ContextType.ERROR_OCCURRENCE: ("Error", "Detects runtime errors", "log analysis"),
            ContextType.PERFORMANCE_ISSUE: ("Performance", "Detects performance issues", "metrics, profiling"),
            ContextType.DEPLOYMENT: ("Deployment", "Detects deployment events", "deploy scripts"),
            ContextType.CODE_REVIEW: ("Code Review", "Detects review requests", "PR/MR events")
        }
        
        for context_type, (name, desc, triggers) in context_info.items():
            context_table.add_row(name, desc, triggers)
        
        console.print(context_table)
        
        # Show workflow chains
        chains = automation_manager.workflow_engine.get_available_chains()
        if chains:
            console.print("\\n🔗 Available Workflow Chains:")
            for chain_name in chains:
                console.print(f"  • {chain_name}")
        else:
            console.print("\\n📝 No workflow chains configured")
            
    except Exception as e:
        console.print(f"[red]Error getting automation status: {e}[/]")


@automate.command()
@click.option('--project-path', '-p', default=".", help='Project directory path')
@click.option('--interval', '-i', default=10, type=int, help='Detection interval in seconds')
def monitor(project_path, interval):
    """Start context monitoring and automation"""
    console = Console()
    
    try:
        project_path = Path(project_path).resolve()
        automation_manager = AutomationManager(project_path)
        
        console.print(f"🚀 Starting automation monitoring for {project_path.name}")
        console.print(f"Detection interval: {interval} seconds")
        console.print("Press Ctrl+C to stop monitoring")
        console.print("=" * 60)
        
        # Add callback for events
        def on_context_detected(context_info):
            console.print(f"[yellow]🔍 Context detected: {context_info.context_type.value}[/]")
            console.print(f"   Details: {context_info.description}")
        
        def on_workflow_triggered(workflow_name, context):
            console.print(f"[cyan]⚡ Workflow triggered: {workflow_name}[/]")
            console.print(f"   Context: {context.context_type.value}")
        
        def on_workflow_completed(workflow_name, success, results):
            status = "✅ Success" if success else "❌ Failed"
            console.print(f"[green]{status}: {workflow_name}[/]")
            if results:
                console.print(f"   Results: {results}")
        
        automation_manager.add_callback('context_detected', on_context_detected)
        automation_manager.add_callback('workflow_triggered', on_workflow_triggered)
        automation_manager.add_callback('workflow_completed', on_workflow_completed)
        
        # Start monitoring
        async def run_monitoring():
            await automation_manager.start_monitoring(detection_interval=interval)
        
        asyncio.run(run_monitoring())
        
    except KeyboardInterrupt:
        console.print("\\n[yellow]Automation monitoring stopped[/]")
    except Exception as e:
        console.print(f"[red]Error during monitoring: {e}[/]")


@automate.command()
@click.option('--project-path', '-p', default=".", help='Project directory path')
@click.option('--context-type', '-c', required=True, 
              type=click.Choice([ct.value for ct in ContextType]),
              help='Context type to simulate')
@click.option('--description', '-d', default="Manual trigger", help='Context description')
def trigger(project_path, context_type, description):
    """Manually trigger automation for a specific context"""
    console = Console()
    
    try:
        project_path = Path(project_path).resolve()
        automation_manager = AutomationManager(project_path)
        
        # Convert string to enum
        context_enum = ContextType(context_type)
        
        console.print(f"🎯 Manually triggering automation for context: {context_type}")
        console.print(f"Description: {description}")
        
        # Simulate context detection
        async def trigger_automation():
            result = await automation_manager.trigger_automation_for_context(
                context_enum, {"description": description, "manual": True}
            )
            return result
        
        result = asyncio.run(trigger_automation())
        
        if result:
            console.print(f"✅ Automation triggered successfully")
            console.print(f"Workflows executed: {len(result)}")
            for workflow_name, success in result.items():
                status = "✅" if success else "❌"
                console.print(f"  {status} {workflow_name}")
        else:
            console.print("⚠️ No workflows triggered for this context")
            
    except Exception as e:
        console.print(f"[red]Error triggering automation: {e}[/]")


@automate.command()
@click.argument('workflow_name')
@click.option('--project-path', '-p', default=".", help='Project directory path')
def execute(workflow_name, project_path):
    """Execute a specific workflow chain"""
    console = Console()
    
    try:
        project_path = Path(project_path).resolve()
        automation_manager = AutomationManager(project_path)
        
        console.print(f"⚡ Executing workflow: {workflow_name}")
        
        async def run_workflow():
            success, results = await automation_manager.workflow_engine.execute_chain(
                workflow_name, {}
            )
            return success, results
        
        success, results = asyncio.run(run_workflow())
        
        if success:
            console.print(f"✅ Workflow '{workflow_name}' completed successfully")
        else:
            console.print(f"❌ Workflow '{workflow_name}' failed")
        
        if results:
            console.print("Results:")
            for step, result in results.items():
                console.print(f"  {step}: {result}")
                
    except Exception as e:
        console.print(f"[red]Error executing workflow: {e}[/]")


@automate.command()
@click.option('--project-path', '-p', default=".", help='Project directory path')
def detect(project_path):
    """Run context detection once and show results"""
    console = Console()
    
    try:
        project_path = Path(project_path).resolve()
        automation_manager = AutomationManager(project_path)
        
        console.print(f"🔍 Running context detection for {project_path.name}...")
        
        async def run_detection():
            contexts = await automation_manager.context_detector.detect_all_contexts()
            return contexts
        
        contexts = asyncio.run(run_detection())
        
        if not contexts:
            console.print("ℹ️ No contexts detected")
            return
        
        # Display detected contexts
        table = Table(title="🎯 Detected Contexts", show_header=True)
        table.add_column("Type", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Confidence", style="green", justify="center")
        table.add_column("Data", style="yellow")
        
        for context in contexts:
            data_summary = str(context.metadata)[:50] + "..." if len(str(context.metadata)) > 50 else str(context.metadata)
            table.add_row(
                context.context_type.value,
                context.description,
                f"{context.confidence:.1%}",
                data_summary
            )
        
        console.print(table)
        
        # Show potential workflows
        console.print("\\n🔗 Potential Workflows:")
        for context in contexts:
            workflows = automation_manager.workflow_engine.get_workflows_for_context(context.context_type)
            if workflows:
                console.print(f"  {context.context_type.value}: {', '.join(workflows)}")
            else:
                console.print(f"  {context.context_type.value}: No workflows configured")
                
    except Exception as e:
        console.print(f"[red]Error during context detection: {e}[/]")


@automate.command()
@click.option('--project-path', '-p', default=".", help='Project directory path')
@click.option('--output', '-o', help='Output file for workflow configuration')
def config(project_path, output):
    """Generate workflow configuration template"""
    console = Console()
    
    try:
        # Generate sample workflow configuration
        sample_config = {
            "workflows": {
                "git-commit-workflow": {
                    "triggers": ["git_commit"],
                    "steps": [
                        {
                            "name": "run_tests",
                            "command": "npm test",
                            "on_failure": "notify"
                        },
                        {
                            "name": "check_build", 
                            "command": "npm run build",
                            "depends_on": ["run_tests"]
                        },
                        {
                            "name": "deploy_if_green",
                            "command": "npm run deploy",
                            "depends_on": ["run_tests", "check_build"],
                            "condition": "all_success"
                        }
                    ]
                },
                "test-failure-workflow": {
                    "triggers": ["test_failure"],
                    "steps": [
                        {
                            "name": "analyze_failure",
                            "command": "npm run test:analyze"
                        },
                        {
                            "name": "notify_team",
                            "command": "slack-notify 'Tests failing'"
                        }
                    ]
                },
                "dependency-update-workflow": {
                    "triggers": ["dependency_update"],
                    "steps": [
                        {
                            "name": "backup_lockfile",
                            "command": "cp package-lock.json package-lock.json.bak"
                        },
                        {
                            "name": "run_tests",
                            "command": "npm test"
                        },
                        {
                            "name": "rollback_if_fail",
                            "command": "mv package-lock.json.bak package-lock.json",
                            "condition": "previous_failed"
                        }
                    ]
                }
            }
        }
        
        import json
        config_json = json.dumps(sample_config, indent=2)
        
        if output:
            output_path = Path(output)
            output_path.write_text(config_json)
            console.print(f"✅ Workflow configuration written to: {output_path}")
        else:
            console.print("📝 Sample Workflow Configuration:")
            console.print(config_json)
            
    except Exception as e:
        console.print(f"[red]Error generating configuration: {e}[/]")


def _format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m {int(seconds%60)}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


if __name__ == "__main__":
    automate()