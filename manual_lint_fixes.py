#!/usr/bin/env python3
"""Manual lint fixes for common issues"""

import re
from pathlib import Path


def fix_import_order(file_path):
    """Fix basic import ordering issues"""
    with open(file_path) as f:
        content = f.read()

    lines = content.split("\n")

    # Find imports section
    import_start = None
    import_end = None

    for i, line in enumerate(lines):
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            if import_start is None:
                import_start = i
            import_end = i
        elif import_start is not None and line.strip() == "":
            continue
        elif import_start is not None and not line.strip().startswith('"""') and not line.strip().startswith("#"):
            break

    if import_start is None:
        return False

    # Extract imports
    imports = []
    for i in range(import_start, import_end + 1):
        line = lines[i]
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            imports.append(line)

    # Sort imports (basic sorting)
    stdlib_imports = []
    third_party_imports = []
    local_imports = []

    for imp in imports:
        if imp.strip().startswith("from libs.") or imp.strip().startswith("from commands.") or imp.strip().startswith("from api."):
            local_imports.append(imp)
        elif any(pkg in imp for pkg in ["click", "rich", "fastapi", "uvicorn", "pydantic", "typer"]):
            third_party_imports.append(imp)
        else:
            stdlib_imports.append(imp)

    # Sort each group
    stdlib_imports.sort()
    third_party_imports.sort()
    local_imports.sort()

    # Reconstruct import section
    new_imports = []
    if stdlib_imports:
        new_imports.extend(stdlib_imports)
        new_imports.append("")
    if third_party_imports:
        new_imports.extend(third_party_imports)
        new_imports.append("")
    if local_imports:
        new_imports.extend(local_imports)

    # Replace imports in content
    new_lines = lines[:import_start] + new_imports + lines[import_end + 1 :]

    new_content = "\n".join(new_lines)

    if new_content != content:
        with open(file_path, "w") as f:
            f.write(new_content)
        return True

    return False


def fix_long_lines(file_path):
    """Fix some common long line issues"""
    with open(file_path) as f:
        content = f.read()

    lines = content.split("\n")
    modified = False

    for i, line in enumerate(lines):
        if len(line) > 120:  # Using 120 as a reasonable limit
            # Try to fix long import lines
            if "from " in line and "import " in line and line.count(",") > 2 and not line.strip().endswith("("):
                # Extract the import parts
                match = re.match(r"(\s*from\s+[^\s]+\s+import\s+)", line)
                if match:
                    prefix = match.group(1)
                    imports_part = line[len(prefix) :].strip()

                    # Split imports
                    imports = [imp.strip() for imp in imports_part.split(",")]

                    # Create multi-line import
                    new_lines = [prefix + "("]
                    for imp in imports:
                        new_lines.append(f"    {imp},")
                    new_lines.append(")")

                    lines[i : i + 1] = new_lines
                    modified = True
                    break

    if modified:
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
        return True

    return False


def main():
    """Main function"""
    project_root = Path("/Users/archmagece/myopen/scripton/yesman-claude")

    # Find Python files
    python_files = []
    for directory in ["libs", "commands", "api", "tests"]:
        if (project_root / directory).exists():
            python_files.extend((project_root / directory).rglob("*.py"))

    print(f"Found {len(python_files)} Python files")

    import_fixes = 0
    line_fixes = 0

    for file_path in python_files:
        if "migrations" in str(file_path) or "node_modules" in str(file_path):
            continue

        try:
            if fix_import_order(file_path):
                import_fixes += 1
                print(f"Fixed imports in: {file_path}")

            if fix_long_lines(file_path):
                line_fixes += 1
                print(f"Fixed long lines in: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print("\nCompleted manual fixes:")
    print(f"Import fixes: {import_fixes}")
    print(f"Long line fixes: {line_fixes}")

    print("\nNow you should run these commands manually:")
    print("1. uv run ruff check libs commands api tests --select I --fix")
    print("2. uv run ruff format libs commands api tests")
    print("3. uv run ruff check libs commands api tests")


if __name__ == "__main__":
    main()
