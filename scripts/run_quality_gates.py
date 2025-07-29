#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""
Simple runner for quality gates checker.

This script provides a convenient way to run quality gates with
commonly used configurations and output formats.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.quality_gates_checker import QualityGatesChecker


async def run_basic_quality_gates():
    """Run basic quality gates check."""
    print("🛡️ Running Yesman-Claude Quality Gates...")

    # Initialize checker with default configuration
    checker = QualityGatesChecker()

    # Run all quality gates
    results = await checker.run_all_gates()

    # Generate and display report
    report = checker.generate_report(results, format="markdown")
    print(report)

    # Save report to file
    report_path = project_root / "QUALITY_GATES_REPORT.md"
    report_path.write_text(report)
    print(f"\n📄 Full report saved to: {report_path}")

    # Return results for further processing if needed
    return results


async def run_essential_quality_gates():
    """Run essential quality gates for fast pre-commit checks."""
    print("🛡️ Running Essential Quality Gates (fast)...")

    # Initialize checker with default configuration
    checker = QualityGatesChecker()

    # Run essential quality gates only
    results = await checker.run_essential_gates()

    # Generate brief report
    print(f"📊 Result: {results.overall_result.value.upper()}")
    print(f"⏱️  Execution time: {results.execution_time:.2f}s")
    print(f"🔍 Checks: {results.total_checks}, Failures: {results.blocking_failures}")

    if results.blocking_failures > 0:
        print("\n❌ Blocking failures:")
        for result in results.checks:
            if result.result.value == "fail":
                print(f"  - {result.name}: {result.message}")

    return results


async def run_comprehensive_quality_gates():
    """Run comprehensive quality gates for pre-push validation."""
    print("🛡️ Running Comprehensive Quality Gates...")

    # Initialize checker with default configuration
    checker = QualityGatesChecker()

    # Run comprehensive quality gates
    results = await checker.run_comprehensive_gates()

    # Generate and display full report
    report = checker.generate_report(results, format="markdown")

    # Save detailed report
    report_path = project_root / "QUALITY_GATES_COMPREHENSIVE.md"
    report_path.write_text(report)

    # Print summary
    print(f"📊 Overall Result: {results.overall_result.value.upper()}")
    print(f"📈 Overall Score: {results.summary['overall_score']:.1f}/100")
    print(f"⏱️  Execution time: {results.execution_time:.2f}s")
    print(f"📄 Full report saved to: {report_path}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Yesman-Claude Quality Gates")
    parser.add_argument("--fast", action="store_true", help="Run essential gates only (fast)")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive gates (thorough)")

    args = parser.parse_args()

    try:
        if args.fast:
            results = asyncio.run(run_essential_quality_gates())
        elif args.comprehensive:
            results = asyncio.run(run_comprehensive_quality_gates())
        else:
            results = asyncio.run(run_basic_quality_gates())

        # Exit with appropriate code
        if results.overall_result.value == "fail":
            print(f"\n❌ Quality gates failed - {results.blocking_failures} blocking failures")
            sys.exit(1)
        elif results.overall_result.value == "warning":
            print(f"\n⚠️ Quality gates passed with warnings - {results.warning_failures} warning failures")
            sys.exit(0)
        else:
            print("\n✅ All quality gates passed!")
            sys.exit(0)

    except Exception as e:
        print(f"\n💥 Error running quality gates: {e}")
        sys.exit(1)
