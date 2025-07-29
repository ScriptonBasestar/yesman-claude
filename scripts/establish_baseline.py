#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""
Performance baseline establishment runner for Yesman-Claude project.

This script establishes performance baselines and integrates with the quality gates system
to provide continuous performance monitoring and regression detection.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add the project root to sys.path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.performance_baseline import get_performance_monitor
from scripts.quality_gates_checker import QualityGatesChecker


async def establish_baseline(duration: int = 60, run_quality_gates: bool = True) -> None:
    """
    Establish a new performance baseline.

    Args:
        duration: Baseline monitoring duration in seconds
        run_quality_gates: Whether to run quality gates during baseline
    """
    print("🎯 Establishing Yesman-Claude Performance Baseline")
    print(f"⏱️  Duration: {duration} seconds")
    print("=" * 60)

    # Get performance monitor
    perf_monitor = get_performance_monitor()

    try:
        # Establish baseline with monitoring
        print("📊 Starting baseline establishment...")

        # Optionally run quality gates during baseline to measure their performance
        quality_task = None
        if run_quality_gates:
            print("🛡️ Running quality gates during baseline...")
            quality_task = asyncio.create_task(run_quality_gates_baseline())

        # Establish the baseline
        baseline = await perf_monitor.establish_baseline(duration)

        # Wait for quality gates to complete if running
        if quality_task:
            await quality_task

        print("\n✅ Baseline established successfully!")
        print(f"📁 Baseline saved to: {perf_monitor.data_dir}")

        # Generate and display summary report
        report = perf_monitor.generate_performance_report(compare_to_baseline=False)
        print_baseline_summary(report)

        # Save detailed report
        report_file = perf_monitor.data_dir / "baseline_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📄 Detailed report saved to: {report_file}")

    except Exception as e:
        print(f"❌ Failed to establish baseline: {e}")
        sys.exit(1)


async def run_quality_gates_baseline() -> None:
    """Run quality gates during baseline establishment to measure their performance."""
    try:
        checker = QualityGatesChecker()

        # Run essential gates (lighter load)
        print("  🔍 Running essential quality gates...")
        essential_results = await checker.run_essential_gates()

        # Wait a bit
        await asyncio.sleep(10)

        # Run comprehensive gates
        print("  🔍 Running comprehensive quality gates...")
        comprehensive_results = await checker.run_comprehensive_gates()

        print("  ✅ Quality gates completed during baseline")

    except Exception as e:
        print(f"  ⚠️ Quality gates failed during baseline: {e}")


def print_baseline_summary(report: dict) -> None:
    """Print a human-readable baseline summary."""
    print("\n📈 Baseline Summary")
    print("=" * 40)

    # System summary
    system = report.get("system_summary", {})
    if "error" not in system:
        print("🖥️  System Performance:")
        print(f"   CPU Average: {system.get('cpu_percent', {}).get('average', 0):.1f}%")
        print(f"   Memory Average: {system.get('memory_percent', {}).get('average', 0):.1f}%")
        print(f"   Samples Collected: {system.get('samples_count', 0)}")

    # Monitoring summary
    monitoring = report.get("monitoring_summary", {})
    if "error" not in monitoring:
        print("🔍 Claude Monitoring:")
        print(f"   Average Loops/sec: {monitoring.get('loops_per_second', {}).get('average', 0):.2f}")
        print(f"   Average Loop Duration: {monitoring.get('loop_duration_ms', {}).get('average', 0):.1f}ms")
        print(f"   Total Loops: {monitoring.get('total_loops', 0)}")
        print(f"   Monitor Types: {', '.join(monitoring.get('monitor_types', []))}")

    # Event bus summary
    event_bus = report.get("event_bus_summary", {})
    if "info" not in event_bus and "error" not in event_bus:
        print("🚌 Event Bus Performance:")
        throughput = event_bus.get("throughput", {})
        print(f"   Events/sec: {throughput.get('events_per_second', 0):.1f}")
        print(f"   Success Rate: {throughput.get('success_rate', 0):.1f}%")

    # Quality gates summary
    quality = report.get("quality_gates_summary", {})
    if "info" not in quality and "error" not in quality:
        print("🛡️ Quality Gates Performance:")
        print(f"   Average Execution: {quality.get('execution_time_ms', {}).get('average', 0):.0f}ms")
        results = quality.get("results_distribution", {})
        print(f"   Results: {results.get('pass', 0)} pass, {results.get('fail', 0)} fail, {results.get('warning', 0)} warning")

    print(f"\n⏱️  Report Duration: {report.get('monitoring_duration_seconds', 0):.1f} seconds")


async def compare_with_baseline() -> None:
    """Compare current performance with established baseline."""
    print("📊 Comparing current performance with baseline...")

    perf_monitor = get_performance_monitor()

    # Load existing baseline
    baseline = await perf_monitor.load_baseline()
    if not baseline:
        print("❌ No baseline found. Run with --establish first.")
        sys.exit(1)

    # Start monitoring for comparison
    await perf_monitor.start_monitoring()

    # Monitor for 30 seconds for comparison
    print("⏱️  Monitoring current performance for 30 seconds...")
    await asyncio.sleep(30)

    await perf_monitor.stop_monitoring()

    # Generate comparison report
    report = perf_monitor.generate_performance_report(compare_to_baseline=True)

    print("\n📈 Performance Comparison")
    print("=" * 40)

    comparison = report.get("baseline_comparison", {})
    if "error" not in comparison:
        print(f"🔄 Baseline Version: {comparison.get('baseline_version', 'unknown')}")
        print(f"📅 Baseline Date: {comparison.get('baseline_timestamp', 'unknown')}")
        print(f"🎯 Overall Assessment: {comparison.get('overall_assessment', 'pending')}")
    else:
        print(f"❌ Comparison failed: {comparison.get('error', 'unknown')}")


def main():
    """Main entry point for baseline establishment."""
    parser = argparse.ArgumentParser(description="Establish performance baseline for Yesman-Claude")

    parser.add_argument("--establish", action="store_true", help="Establish a new performance baseline")
    parser.add_argument("--compare", action="store_true", help="Compare current performance with baseline")
    parser.add_argument("--duration", type=int, default=60, help="Baseline monitoring duration in seconds (default: 60)")
    parser.add_argument("--no-quality-gates", action="store_true", help="Skip running quality gates during baseline")

    args = parser.parse_args()

    if not args.establish and not args.compare:
        print("❓ Please specify --establish or --compare")
        parser.print_help()
        sys.exit(1)

    try:
        if args.establish:
            asyncio.run(establish_baseline(duration=args.duration, run_quality_gates=not args.no_quality_gates))
        elif args.compare:
            asyncio.run(compare_with_baseline())

    except KeyboardInterrupt:
        print("\n⛔ Baseline establishment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
