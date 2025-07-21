#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

import os

# Remove the conflicting file
conflicting_file = "/Users/archmagece/myopen/scripton/yesman-claude/commands/multi_agent.py"
if os.path.exists(conflicting_file):
    os.remove(conflicting_file)
    print(f"Removed {conflicting_file}")
else:
    print(f"File {conflicting_file} not found")
