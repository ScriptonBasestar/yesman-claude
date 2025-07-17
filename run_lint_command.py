#!/usr/bin/env python3
"""Run make lint command and capture output"""
import subprocess
import sys
import os

# Change to project directory
os.chdir("/Users/archmagece/myopen/scripton/yesman-claude")

def run_make_lint():
    """Run make lint and capture all output"""
    try:
        # Run make lint command
        result = subprocess.run(
            ["make", "lint"], 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        # Write output to file
        with open("lint-output.txt", "w") as f:
            f.write("=== MAKE LINT OUTPUT ===\n")
            f.write(f"Exit code: {result.returncode}\n\n")
            
            if result.stdout:
                f.write("=== STDOUT ===\n")
                f.write(result.stdout)
                f.write("\n\n")
            
            if result.stderr:
                f.write("=== STDERR ===\n")
                f.write(result.stderr)
                f.write("\n\n")
        
        # Also print to console
        print(f"Exit code: {result.returncode}")
        print("\n=== STDOUT ===")
        print(result.stdout)
        if result.stderr:
            print("\n=== STDERR ===")
            print(result.stderr)
        
        print(f"\nOutput saved to lint-output.txt")
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Command timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"Error running make lint: {e}")
        return False

if __name__ == "__main__":
    run_make_lint()