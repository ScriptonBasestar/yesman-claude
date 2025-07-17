#!/usr/bin/env python3

with open("api/routers/controllers.py") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if len(line.rstrip()) > 88:
        print(f"Line {i}: {len(line.rstrip())} chars - {line.rstrip()[:100]}...")
