#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

import os
import stat

# Make the validation script executable
script_path = "scripts/validate-lint-config.py"
current_permissions = os.stat(script_path).st_mode
new_permissions = current_permissions | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
os.chmod(script_path, new_permissions)

print(f"Made {script_path} executable")
print(f"Previous permissions: {oct(current_permissions)}")
print(f"New permissions: {oct(new_permissions)}")
