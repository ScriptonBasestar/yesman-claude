#!/usr/bin/env python3

# Copyright notice.

import os
import shutil

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Fix the module naming conflict by removing the wrapper file."""


base_path = "/Users/archmagece/myopen/scripton/yesman-claude"

# Remove the conflicting multi_agent.py file
conflict_file = os.path.join(base_path, "commands", "multi_agent.py")
if os.path.exists(conflict_file):
    # Create backup first
    backup_file = os.path.join(base_path, "commands", "multi_agent_wrapper_backup.py")
    shutil.copy2(conflict_file, backup_file)
    print(f"Backed up {conflict_file} to {backup_file}")

    # Remove the original
    os.remove(conflict_file)
    print(f"Removed conflicting file: {conflict_file}")
else:
    print(f"File not found: {conflict_file}")

print("Module conflict resolved. The multi_agent package can now be imported without issues.")
