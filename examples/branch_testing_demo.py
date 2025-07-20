#!/usr/bin/env python3
"""Demo script showing branch testing integration capabilities."""

import asyncio
import tempfile
from pathlib import Path

from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.branch_test_manager import BranchTestManager, TestType


async def demo_branch_testing():
    """Demonstrate branch testing functionality."""
    print("🧪 Branch Testing Integration Demo")
    print("=" * 50)

    # Create temporary work directory
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)

        print(f"📁 Working directory: {work_dir}")

        # 1. Create and configure agent pool
        print("\n1️⃣ Creating Agent Pool...")
        agent_pool = AgentPool(max_agents=3, work_dir=str(work_dir))

        # Enable branch testing (without real git repo for demo)
        print("   🔧 Enabling branch testing...")

        # Create a mock branch test manager for demo
        btm = BranchTestManager(repo_path=str(work_dir), results_dir=str(work_dir / "test_results"))

        # Configure some demo test suites
        print("   📋 Configuring test suites...")
        btm.configure_test_suite(
            name="unit_tests",
            test_type=TestType.UNIT,
            command=["python", "-c", "print('✅ Unit tests passed!'); exit(0)"],
            timeout=30,
            critical=True,
        )

        btm.configure_test_suite(
            name="lint_check",
            test_type=TestType.LINT,
            command=["python", "-c", "print('✅ Lint check passed!'); exit(0)"],
            timeout=15,
            critical=False,
        )

        btm.configure_test_suite(
            name="type_check",
            test_type=TestType.TYPE_CHECK,
            command=["python", "-c", "print('✅ Type check passed!'); exit(0)"],
            timeout=20,
            critical=False,
        )

        # Attach to agent pool
        agent_pool.branch_test_manager = btm
        agent_pool._test_integration_enabled = True

        print(f"   ✅ Configured {len(btm.test_suites)} test suites")

        # 2. Create test tasks for a branch
        print("\n2️⃣ Creating Test Tasks...")
        branch_name = "feature/awesome-feature"

        # Create individual test task
        unit_test_task = agent_pool.create_test_task(
            branch_name=branch_name,
            test_suite_name="unit_tests",
            priority=8,
        )

        print(f"   📝 Created task: {unit_test_task.title}")
        print(f"      Priority: {unit_test_task.priority}")
        print(f"      Command: {' '.join(unit_test_task.command[:2])}...")

        # 3. Demonstrate auto test creation
        print("\n3️⃣ Auto-Creating Test Tasks for Branch...")
        task_ids = await agent_pool.auto_test_branch(branch_name)

        print(f"   🚀 Created {len(task_ids)} automated test tasks")
        for task_id in task_ids:
            task = agent_pool.tasks[task_id]
            print(f"      - {task.title} (Priority: {task.priority})")

        # 4. Show task queue status
        print("\n4️⃣ Task Queue Status...")
        print(f"   📊 Total tasks in queue: {len(agent_pool.tasks)}")

        # Group by priority
        high_priority = [t for t in agent_pool.tasks.values() if t.priority >= 8]
        medium_priority = [t for t in agent_pool.tasks.values() if 5 <= t.priority < 8]
        low_priority = [t for t in agent_pool.tasks.values() if t.priority < 5]

        print(f"      High priority (8-10): {len(high_priority)} tasks")
        print(f"      Medium priority (5-7): {len(medium_priority)} tasks")
        print(f"      Low priority (1-4): {len(low_priority)} tasks")

        # 5. Demonstrate test configuration
        print("\n5️⃣ Test Configuration...")
        print("   📋 Available Test Suites:")

        for name, suite in btm.test_suites.items():
            critical_marker = "🔴" if suite.critical else "🟡"
            print(f"      {critical_marker} {name} ({suite.test_type.value})")
            print(f"         Command: {' '.join(suite.command[:3])}...")
            print(f"         Timeout: {suite.timeout}s")
            print(f"         Critical: {suite.critical}")

        # 6. Show integration capabilities
        print("\n6️⃣ Integration Capabilities...")
        print("   🔗 Branch testing integrates with:")
        print("      • Multi-agent task scheduling")
        print("      • Intelligent workload distribution")
        print("      • Priority-based test execution")
        print("      • Automatic test result collection")
        print("      • Branch-specific test history")
        print("      • Failure handling and retries")

        # 7. Configuration examples
        print("\n7️⃣ Configuration Examples...")
        print("   ⚙️ Auto-testing settings:")
        print(f"      Auto-testing enabled: {btm.auto_testing_enabled}")
        print(f"      Test on commit: {btm.test_on_commit}")
        print(f"      Test on push: {btm.test_on_push}")
        print(f"      Parallel test limit: {btm.parallel_test_limit}")

        print("\n8️⃣ Usage Scenarios...")
        print("   📈 This system enables:")
        print("      • Automatic testing when new commits are detected")
        print("      • Parallel test execution across multiple agents")
        print("      • Branch-specific test result tracking")
        print("      • Integration with CI/CD workflows")
        print("      • Intelligent test prioritization")
        print("      • Failure isolation and reporting")

        print("\n✅ Demo completed successfully!")
        print("\n💡 To use in practice:")
        print("   1. Enable branch testing: agent_pool.enable_branch_testing()")
        print("   2. Configure test suites with btm.configure_test_suite()")
        print("   3. Create test tasks: agent_pool.auto_test_branch(branch_name)")
        print("   4. Start agent pool: await agent_pool.start()")


if __name__ == "__main__":
    asyncio.run(demo_branch_testing())
