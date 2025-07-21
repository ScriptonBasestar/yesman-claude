#!/usr/bin/env python3

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


with open("api/routers/controllers.py", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if len(line.rstrip()) > 88:
        print(f"Line {i}: {len(line.rstrip())} chars - {line.rstrip()[:100]}...")
