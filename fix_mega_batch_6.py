#!/usr/bin/env python3
"""
MEGA BATCH 6: Fix E402 + DOC201 + PLR6301 errors in one comprehensive run.
Total target: 3,473+ errors across all Python files.
"""
import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a command and report results."""
    print(f"\n🔧 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"⏱️ Execution time: {end_time - start_time:.2f} seconds")
    
    if result.returncode == 0:
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(result.stdout)
        return True
    else:
        print(f"❌ {description} failed")
        if result.stderr.strip():
            print(f"Error: {result.stderr}")
        if result.stdout.strip():
            print(f"Output: {result.stdout}")
        return False

def count_errors() -> dict:
    """Count current errors by type."""
    result = subprocess.run(
        ['ruff', 'check', '--select=E402,DOC201,PLR6301'],
        capture_output=True, text=True
    )
    
    # Count by parsing text output
    counts = {}
    if result.stdout:
        for line in result.stdout.split('\n'):
            if ':' in line and any(code in line for code in ['E402', 'DOC201', 'PLR6301']):
                for code in ['E402', 'DOC201', 'PLR6301']:
                    if code in line:
                        counts[code] = counts.get(code, 0) + 1
                        break
    
    return counts

def main():
    """Main batch processing function."""
    print("🚀 MEGA BATCH 6: E402 + DOC201 + PLR6301 Auto-Fix")
    print("=" * 60)
    
    # Count initial errors
    print("📊 Counting initial errors...")
    initial_counts = count_errors()
    total_initial = sum(initial_counts.values())
    
    print(f"Initial error counts:")
    for code, count in sorted(initial_counts.items()):
        print(f"  {code}: {count:,} errors")
    print(f"  Total: {total_initial:,} errors")
    
    if total_initial == 0:
        print("✅ No errors to fix!")
        return
    
    success_count = 0
    
    # Step 1: Fix E402 - Import ordering (highest priority)
    print(f"\n{'='*60}")
    print("STEP 1: Fixing E402 - Import not at top of file")
    print(f"{'='*60}")
    
    if run_command([sys.executable, 'fix_e402_imports.py'], "Fixing import ordering (E402)"):
        success_count += 1
    
    # Step 2: Fix PLR6301 - Static methods (medium priority)  
    print(f"\n{'='*60}")
    print("STEP 2: Fixing PLR6301 - Method could be static")
    print(f"{'='*60}")
    
    if run_command([sys.executable, 'fix_plr6301_staticmethod.py'], "Converting to static methods (PLR6301)"):
        success_count += 1
    
    # Step 3: Fix DOC201 - Return documentation (lowest priority)
    print(f"\n{'='*60}")
    print("STEP 3: Fixing DOC201 - Return not documented")
    print(f"{'='*60}")
    
    if run_command([sys.executable, 'fix_doc201_returns.py'], "Adding return documentation (DOC201)"):
        success_count += 1
    
    # Final verification
    print(f"\n{'='*60}")
    print("FINAL VERIFICATION")
    print(f"{'='*60}")
    
    print("📊 Counting remaining errors...")
    final_counts = count_errors()
    total_final = sum(final_counts.values())
    
    print(f"Final error counts:")
    for code, count in sorted(final_counts.items()):
        initial = initial_counts.get(code, 0)
        fixed = initial - count
        print(f"  {code}: {count:,} errors (fixed {fixed:,})")
    print(f"  Total: {total_final:,} errors")
    
    total_fixed = total_initial - total_final
    fix_rate = (total_fixed / total_initial * 100) if total_initial > 0 else 0
    
    print(f"\n🎯 MEGA BATCH 6 RESULTS:")
    print(f"  Initial errors: {total_initial:,}")
    print(f"  Fixed errors: {total_fixed:,}")
    print(f"  Remaining errors: {total_final:,}")
    print(f"  Success rate: {fix_rate:.1f}%")
    print(f"  Steps completed: {success_count}/3")
    
    if total_fixed > 0:
        print(f"\n✅ Successfully processed MEGA BATCH 6!")
        print(f"🔥 Fixed {total_fixed:,} errors across E402, DOC201, and PLR6301!")
    else:
        print(f"\n⚠️ No errors were fixed in this batch.")
    
    # Cleanup temp files
    temp_files = ['fix_e402_imports.py', 'fix_doc201_returns.py', 'fix_plr6301_staticmethod.py']
    for temp_file in temp_files:
        if Path(temp_file).exists():
            Path(temp_file).unlink()
    
    return total_fixed > 0

if __name__ == '__main__':
    main()