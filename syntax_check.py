#!/usr/bin/env python3
"""Basic syntax check for key files"""
import ast
import sys
from pathlib import Path

def check_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def main():
    """Check syntax of key files"""
    base_path = Path("/Users/archmagece/myopen/scripton/yesman-claude")
    
    files_to_check = [
        "api/routers/controllers.py",
        "api/background_tasks.py",
        "api/middleware/error_handler.py",
        "commands/multi_agent.py",
        "commands/multi_agent_main.py"
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        full_path = base_path / file_path
        if full_path.exists():
            is_valid, error = check_syntax(full_path)
            if is_valid:
                print(f"✅ {file_path}: Syntax OK")
            else:
                print(f"❌ {file_path}: {error}")
                all_good = False
        else:
            print(f"⚠️  {file_path}: File not found")
    
    print(f"\n{'✅ All files have valid syntax!' if all_good else '❌ Some files have syntax errors!'}")
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)