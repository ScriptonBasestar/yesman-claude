#!/usr/bin/env python3
"""
Simple test application for yesman-claude integration testing
"""


def main():
    """Main function that needs some improvements"""
    # TODO: Add logging functionality
    print("Hello, World!")

    # TODO: Add user input validation
    name = input("Enter your name: ")
    print(f"Hello, {name}!")

    # TODO: Add error handling for file operations
    try:
        with open("output.txt", "w") as f:
            f.write(f"User name: {name}\n")
    except Exception as e:
        print(f"Error writing file: {e}")


if __name__ == "__main__":
    main()
