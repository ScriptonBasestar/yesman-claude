#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Demo script for multi-agent system metrics verification."""

import asyncio
import tempfile
from pathlib import Path

from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.metrics_verifier import (
    MetricsVerifier,
)


async def demo_metrics_verification():
    """Demonstrate comprehensive metrics verification system."""
    print("🎯 Multi-Agent System Metrics Verification Demo")
    print("=" * 60)

    # Create temporary work directory
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)

        print(f"📁 Working directory: {work_dir}")

        # 1. Initialize agent pool and metrics verifier
        print("\n1️⃣ Initializing Multi-Agent System...")
        agent_pool = AgentPool(max_agents=3, work_dir=str(work_dir / "agents"))
        verifier = MetricsVerifier(work_dir=str(work_dir / "metrics"))

        print(f"   🤖 Agent pool: {agent_pool.max_agents} max agents")
        print(f"   📊 Metrics directory: {verifier.work_dir}")

        # 2. Show success criteria
        print("\n2️⃣ Success Criteria Requirements...")
        criteria = verifier.success_criteria
        print(f"   🚀 Speed improvement: {criteria.min_speed_improvement}x - {criteria.max_speed_improvement}x")
        print(f"   🔧 Conflict resolution: ≥{criteria.min_conflict_resolution_rate:.0%}")
        print(f"   🌿 Merge success rate: ≥{criteria.min_merge_success_rate:.0%}")
        print(f"   📈 Quality maintenance: ≥{criteria.min_quality_maintenance:+.1f}")

        # 3. Get benchmark tasks
        print("\n3️⃣ Benchmark Task Configuration...")
        benchmark_tasks = verifier.get_benchmark_tasks()
        print(f"   📋 Total benchmark tasks: {len(benchmark_tasks)}")
        for i, task in enumerate(benchmark_tasks, 1):
            print(f"      {i}. {task['title']}: {task['description']}")

        # 4. Run single-agent baseline
        print("\n4️⃣ Single-Agent Performance Baseline...")
        print("   ⏱️ Running single-agent benchmark (this may take a moment)...")

        single_time = await verifier.measure_single_agent_performance(
            agent_pool=agent_pool,
            benchmark_tasks=benchmark_tasks,
            iterations=2,  # Reduced for demo
        )

        print(f"   ✅ Single-agent baseline: {single_time:.2f} seconds")

        # 5. Run multi-agent performance test
        print("\n5️⃣ Multi-Agent Performance Measurement...")
        print("   ⏱️ Running multi-agent benchmark...")

        multi_time = await verifier.measure_multi_agent_performance(
            agent_pool=agent_pool,
            benchmark_tasks=benchmark_tasks,
            iterations=2,  # Reduced for demo
        )

        print(f"   ✅ Multi-agent performance: {multi_time:.2f} seconds")
        print(f"   📈 Speed improvement: {verifier.current_metrics.speed_improvement_ratio:.2f}x")

        # 6. Simulate real-world metrics
        print("\n6️⃣ Simulating Real-World Operation Metrics...")

        # Conflict resolution simulation
        print("   🔧 Simulating conflict resolution scenarios...")
        conflicts_scenarios = [
            (10, 9),  # 90% success rate
            (15, 12),  # 80% success rate
            (8, 7),  # 87.5% success rate
        ]

        for total, resolved in conflicts_scenarios:
            verifier.track_conflict_resolution(total, resolved)
            print(f"      Resolved {resolved}/{total} conflicts")

        final_conflicts = verifier.current_metrics
        print(f"   📊 Overall conflict resolution: {final_conflicts.conflict_resolution_rate:.1%}")

        # Branch merge simulation
        print("   🌿 Simulating branch merge operations...")
        merge_scenarios = [
            (20, 20),  # 100% success
            (15, 15),  # 100% success
            (10, 10),  # 100% success
            (5, 4),  # 80% success (one failure)
        ]

        for total, successful in merge_scenarios:
            verifier.track_merge_success(total, successful)
            print(f"      Merged {successful}/{total} branches successfully")

        final_merges = verifier.current_metrics
        print(f"   📊 Overall merge success: {final_merges.merge_success_rate:.1%}")

        # Code quality simulation
        print("   📈 Simulating code quality assessment...")
        quality_scenarios = [
            (8.2, 8.4),  # +0.2 improvement
            (7.8, 8.1),  # +0.3 improvement
            (8.5, 8.6),  # +0.1 improvement
        ]

        for initial, final in quality_scenarios:
            verifier.track_code_quality(initial, final)
            print(f"      Quality: {initial} -> {final} (change: {final - initial:+.1f})")

        final_quality = verifier.current_metrics
        print(f"   📊 Overall quality improvement: {final_quality.quality_improvement:+.2f}")

        # 7. Verify success criteria
        print("\n7️⃣ Success Criteria Verification...")
        verification_results = verifier.verify_success_criteria()
        compliance = verification_results["compliance"]

        print("   🎯 Verification Results:")
        print(f"      Speed improvement: {'✅ PASS' if compliance['speed_improvement'] else '❌ FAIL'}")
        print(f"      Conflict resolution: {'✅ PASS' if compliance['conflict_resolution'] else '❌ FAIL'}")
        print(f"      Merge success: {'✅ PASS' if compliance['merge_success'] else '❌ FAIL'}")
        print(f"      Quality maintenance: {'✅ PASS' if compliance['quality_maintenance'] else '❌ FAIL'}")
        print(f"      Overall success: {'✅ PASS' if compliance['overall_success'] else '❌ FAIL'}")

        # 8. Generate detailed report
        print("\n8️⃣ Detailed Performance Report...")
        report = verifier.generate_performance_report()
        print("\n" + "─" * 60)
        print(report)
        print("─" * 60)

        # 9. Show verification files
        print("\n9️⃣ Generated Verification Files...")
        metrics_files = list(verifier.work_dir.glob("*.json"))
        for file_path in sorted(metrics_files):
            print(f"   📄 {file_path.name}: {file_path.stat().st_size} bytes")

        # 10. Success summary
        print("\n🔟 Verification Summary...")
        overall_success = verification_results["overall_success"]

        if overall_success:
            print("   🎉 SUCCESS: Multi-agent system meets all success criteria!")
            print("   ✅ The system achieves the required performance targets:")
            print(f"      • {verifier.current_metrics.speed_improvement_ratio:.1f}x speed improvement (target: 2-3x)")
            print(f"      • {final_conflicts.conflict_resolution_rate:.0%} conflict resolution rate (target: ≥80%)")
            print(f"      • {final_merges.merge_success_rate:.0%} merge success rate (target: ≥99%)")
            print(f"      • {final_quality.quality_improvement:+.1f} quality improvement (target: ≥0)")
        else:
            print("   ⚠️  WARNING: System does not meet all success criteria")
            print("   📋 Areas needing improvement:")

            if not compliance["speed_improvement"]:
                print(f"      • Speed improvement: {verifier.current_metrics.speed_improvement_ratio:.1f}x (needs 2-3x)")
            if not compliance["conflict_resolution"]:
                print(f"      • Conflict resolution: {final_conflicts.conflict_resolution_rate:.0%} (needs ≥80%)")
            if not compliance["merge_success"]:
                print(f"      • Merge success: {final_merges.merge_success_rate:.0%} (needs ≥99%)")
            if not compliance["quality_maintenance"]:
                print(f"      • Quality change: {final_quality.quality_improvement:+.1f} (needs ≥0)")

        # 11. Integration recommendations
        print("\n1️⃣1️⃣ Integration Recommendations...")
        print("   🔧 To use metrics verification in production:")
        print("   1. Initialize MetricsVerifier in your agent pool setup")
        print("   2. Call verifier.track_*() methods during operations")
        print("   3. Run verifier.verify_success_criteria() periodically")
        print("   4. Use verifier.generate_performance_report() for monitoring")
        print("   5. Store metrics data for historical analysis")

        print("   📊 Automatic integration points:")
        print("      • AgentPool task completion callbacks")
        print("      • BranchManager conflict resolution events")
        print("      • Merge operation success/failure tracking")
        print("      • Code quality assessment tools")

        print("\n✅ Metrics Verification Demo completed successfully!")
        print(f"\n💾 All verification data saved to: {verifier.work_dir}")

        return verification_results


if __name__ == "__main__":
    asyncio.run(demo_metrics_verification())
