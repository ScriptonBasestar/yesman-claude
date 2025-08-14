#!/usr/bin/env python3

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Simple test application for yesman-claude integration testing."""


def main() -> None:
    """Simple test application main function."""
    # Basic test functionality - minimal implementation is sufficient
    name = input("Enter your name: ")

    # Basic file operations for testing
    try:
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(f"User name: {name}\n")
    except Exception:
        print("Failed to write output file")


if __name__ == "__main__":
    main()
