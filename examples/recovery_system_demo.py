#!/usr/bin/env python3
"""Demo script showing rollback and error recovery capabilities"""

import asyncio
import tempfile
from pathlib import Path

from libs.multi_agent.agent_pool import AgentPool


async def demo_recovery_system():
    """Demonstrate recovery and rollback functionality"""

    print("🔄 Recovery and Rollback System Demo")
    print("=" * 50)

    # Create temporary work directory
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)

        print(f"📁 Working directory: {work_dir}")

        # 1. Create and configure agent pool with recovery
        print("\n1️⃣ Creating Agent Pool with Recovery System...")
        agent_pool = AgentPool(max_agents=3, work_dir=str(work_dir))

        # Enable recovery system
        agent_pool.enable_recovery_system(work_dir=str(work_dir / "recovery"))
        print("   ✅ Recovery system enabled")

        # 2. Show recovery configuration
        print("\n2️⃣ Recovery System Configuration...")
        recovery_status = agent_pool.get_recovery_status()

        print(f"   🔧 Recovery enabled: {recovery_status['recovery_enabled']}")
        print(f"   📊 Active operations: {recovery_status['active_operations']}")

        # Show default recovery strategies
        strategies = agent_pool.recovery_engine.recovery_strategies
        print(f"   📋 Configured recovery strategies: {len(strategies)}")
        for name in strategies:
            print(f"      • {name}")

        # 3. Demonstrate snapshot creation
        print("\n3️⃣ Creating Operation Snapshots...")

        # Create some test files to backup
        test_file = work_dir / "test_config.txt"
        test_file.write_text("original configuration")

        # Create snapshot before operation
        snapshot_id = await agent_pool.create_operation_snapshot(
            operation_type="file_modification",
            description="Modifying test configuration file",
            files_to_backup=[str(test_file)],
            context={"operation": "config_update", "version": "1.0"},
        )

        print(f"   📸 Created snapshot: {snapshot_id}")
        print(f"   💾 Backed up file: {test_file.name}")

        # Modify the file (simulate an operation)
        test_file.write_text("modified configuration - this might break things!")
        print("   ✏️ Modified file content")

        # 4. List available snapshots
        print("\n4️⃣ Available Recovery Snapshots...")
        snapshots = agent_pool.list_recovery_snapshots()

        for i, snapshot in enumerate(snapshots, 1):
            print(f"   {i}. {snapshot['snapshot_id']}")
            print(f"      Description: {snapshot['description']}")
            print(f"      Type: {snapshot['operation_type']}")
            print(f"      Timestamp: {snapshot['timestamp']}")
            print(f"      Files backed up: {snapshot['file_count']}")

        # 5. Demonstrate rollback
        print("\n5️⃣ Testing Rollback Functionality...")
        print(f"   📄 Current file content: '{test_file.read_text()}'")

        # Rollback to snapshot
        print(f"   🔄 Rolling back to snapshot {snapshot_id}...")
        rollback_success = await agent_pool.rollback_to_snapshot(snapshot_id)

        if rollback_success:
            print("   ✅ Rollback successful!")
            print(f"   📄 Restored file content: '{test_file.read_text()}'")
        else:
            print("   ❌ Rollback failed!")

        # 6. Demonstrate execute_with_recovery
        print("\n6️⃣ Execute Operation with Automatic Recovery...")

        # Create a failing operation that will be retried
        failure_count = 0

        async def unreliable_operation():
            nonlocal failure_count
            failure_count += 1
            if failure_count < 3:  # Fail first 2 times
                print(f"   💥 Operation failed (attempt {failure_count})")
                raise Exception(f"Simulated failure #{failure_count}")
            print(f"   ✅ Operation succeeded on attempt {failure_count}")
            return f"success after {failure_count} attempts"

        success, result = await agent_pool.execute_with_recovery(
            operation_func=unreliable_operation,
            operation_type="task_execution",
            description="Unreliable operation with auto-retry",
            max_retries=3,
        )

        print(f"   📊 Final result: Success={success}, Result='{result}'")

        # 7. Show recovery metrics
        print("\n7️⃣ Recovery System Metrics...")
        metrics = recovery_status["metrics"]

        print(f"   📈 Total operations: {metrics['total_operations']}")
        print(f"   ❌ Failed operations: {metrics['failed_operations']}")
        print(f"   🔧 Successful recoveries: {metrics['successful_recoveries']}")
        print(f"   🔄 Rollbacks performed: {metrics['rollbacks_performed']}")
        print(f"   💾 Disk usage: {metrics['disk_usage_mb']:.2f} MB")

        # 8. Demonstrate custom recovery strategy
        print("\n8️⃣ Custom Recovery Strategy...")

        # Register a custom recovery strategy
        from libs.multi_agent.recovery_engine import RecoveryAction

        agent_pool.recovery_engine.register_recovery_strategy(
            name="demo_custom_error",
            error_pattern=r"demo.*error",
            max_retries=2,
            retry_delay=0.5,
            recovery_actions=[RecoveryAction.RETRY, RecoveryAction.SKIP],
        )

        print("   🔧 Registered custom recovery strategy for 'demo.*error' pattern")
        print("   ⚙️ Strategy: 2 retries with 0.5s delay, then skip operation")

        # 9. Show operation types and capabilities
        print("\n9️⃣ Recovery System Capabilities...")
        print("   🎯 Supported Operation Types:")
        print("      • Task execution with automatic retry and agent reset")
        print("      • Branch operations with git state restoration")
        print("      • File modifications with backup and restore")
        print("      • Agent assignments with state rollback")
        print("      • System configuration with snapshot recovery")
        print("      • Test execution with failure isolation")

        print("\n   🛡️ Recovery Actions:")
        print("      • RETRY: Automatic retry with exponential backoff")
        print("      • ROLLBACK: Full state restoration from snapshot")
        print("      • RESET_AGENT: Reset agent to clean state")
        print("      • RESTORE_STATE: Partial state restoration")
        print("      • SKIP: Skip failed operation and continue")
        print("      • ESCALATE: Alert system administrators")

        print("\n   📊 Monitoring Features:")
        print("      • Real-time failure tracking and metrics")
        print("      • Automatic snapshot cleanup (age and count limits)")
        print("      • Operation history and audit trail")
        print("      • Disk usage monitoring and optimization")
        print("      • Configurable recovery strategies per error type")

        # 10. Advanced usage examples
        print("\n🔟 Advanced Usage Examples...")
        print("   💡 To use in practice:")
        print("   1. Enable recovery: agent_pool.enable_recovery_system()")
        print("   2. Create snapshots: await agent_pool.create_operation_snapshot()")
        print("   3. Execute with protection: await agent_pool.execute_with_recovery()")
        print("   4. Manual rollback: await agent_pool.rollback_to_snapshot(snapshot_id)")
        print("   5. Monitor status: agent_pool.get_recovery_status()")

        print("\n   🚀 Integration points:")
        print("      • Automatic task failure recovery")
        print("      • Branch operation rollback on conflicts")
        print("      • File system transaction protection")
        print("      • Multi-agent coordination error handling")
        print("      • Test execution isolation and cleanup")

        print("\n✅ Recovery System Demo completed successfully!")
        print("\n🔒 Your multi-agent operations are now protected with:")
        print("   • Automatic snapshots before critical operations")
        print("   • Intelligent error detection and recovery")
        print("   • File system transaction safety")
        print("   • Agent state consistency protection")
        print("   • Operation audit trail and metrics")


if __name__ == "__main__":
    asyncio.run(demo_recovery_system())
