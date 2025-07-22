#!/usr/bin/env python3
"""
Manual fixer for remaining ANN003 errors that the main script missed.
"""

import subprocess
from pathlib import Path
import re


def fix_remaining_ann003():
    """Fix remaining ANN003 errors manually."""

    # Get remaining errors
    result = subprocess.run(["ruff", "check", "--select", "ANN003", "--exclude", ".backups", "."], capture_output=True, text=True)

    if result.returncode == 0:
        print("No ANN003 errors found!")
        return

    # Parse errors
    lines = result.stderr.split("\n")
    errors = []

    for line in lines:
        if "ANN003" in line and ".py:" in line:
            # Extract file path and line number
            match = re.match(r"^(.+\.py):(\d+):", line)
            if match:
                file_path = Path(match.group(1))
                line_num = int(match.group(2))
                errors.append((file_path, line_num))

    print(f"Found {len(errors)} remaining ANN003 errors")

    # Process each error
    for file_path, line_num in errors:
        print(f"\nProcessing {file_path}:{line_num}")

        try:
            content = file_path.read_text(encoding="utf-8")
            lines_list = content.split("\n")

            if line_num <= len(lines_list):
                original_line = lines_list[line_num - 1]

                # Check if already has type annotation
                if "**kwargs: Any" in original_line or "**kwargs: Dict" in original_line:
                    print(f"  Already has type annotation: {original_line.strip()}")
                    continue

                # Fix different patterns
                fixed_line = original_line

                # Pattern 1: **kwargs,  # comment
                if re.search(r"\*\*kwargs,\s*#", original_line):
                    fixed_line = re.sub(r"(\*\*kwargs),", r"\1: Any,", original_line)

                # Pattern 2: **kwargs) -> return_type:
                elif re.search(r"\*\*kwargs\)\s*->", original_line):
                    fixed_line = re.sub(r"(\*\*kwargs)\)", r"\1: Any)", original_line)

                # Pattern 3: **kwargs without type
                elif "**kwargs" in original_line and ": Any" not in original_line:
                    fixed_line = re.sub(r"(\*\*kwargs)(?!\s*:)", r"\1: Any", original_line)

                if fixed_line != original_line:
                    lines_list[line_num - 1] = fixed_line
                    print(f"  Fixed: {original_line.strip()} -> {fixed_line.strip()}")

                    # Update file
                    content = "\n".join(lines_list)

                    # Add Any import if needed
                    if "from typing import Any" not in content and "import typing" not in content:
                        # Find best place to add import
                        insert_pos = 0
                        lines_list = content.split("\n")

                        for i, line in enumerate(lines_list):
                            stripped = line.strip()
                            if stripped.startswith("from typing import"):
                                # Add Any to existing typing import
                                if "Any" not in line:
                                    lines_list[i] = line.replace("import ", "import Any, ")
                                    print(f"  Added Any to existing typing import")
                                break
                            elif stripped.startswith("import ") or stripped.startswith("from ") and "import" in stripped:
                                insert_pos = i + 1
                            elif stripped and not stripped.startswith("#") and "import" not in stripped:
                                break
                        else:
                            # No existing typing import found, add new one
                            lines_list.insert(insert_pos, "from typing import Any")
                            print(f"  Added 'from typing import Any' at line {insert_pos + 1}")

                        content = "\n".join(lines_list)

                    # Write back
                    file_path.write_text(content, encoding="utf-8")

                    # Verify fix
                    verify_result = subprocess.run(["ruff", "check", "--select", "ANN003", str(file_path)], capture_output=True, text=True)

                    if verify_result.returncode == 0:
                        print(f"  ✅ Fixed successfully")
                    else:
                        print(f"  ❌ Still has errors after fix")
                else:
                    print(f"  No changes needed: {original_line.strip()}")

        except Exception as e:
            print(f"  Error processing {file_path}: {e}")


if __name__ == "__main__":
    fix_remaining_ann003()
