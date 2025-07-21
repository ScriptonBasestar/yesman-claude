#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Demo: Mock Centralization Benefits.

Shows the difference between old duplicated mock patterns and new centralized approach
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.fixtures.mock_factories import ManagerMockFactory


def demo_old_vs_new_patterns():
    """Demonstrate the difference between old and new mock patterns."""
    print("🔧 Mock Centralization Demo")
    print("=" * 50)

    # === OLD PATTERN (Duplicated across 10+ test files) ===
    print("\n❌ OLD PATTERN - Duplicated Mock Setup:")
    print("```python")
    print("@patch('commands.setup.SessionManager')")
    print("def test_setup_session(self, mock_session_manager):")
    print("    # This pattern repeated 20+ times across files")
    print("    mock_manager_instance = MagicMock()")
    print("    mock_manager_instance.create_session.return_value = True")
    print("    mock_manager_instance.get_sessions.return_value = [")
    print("        {'session_name': 'test', 'status': 'active'}")
    print("    ]")
    print("    mock_session_manager.return_value = mock_manager_instance")
    print("    # ... test code ...")
    print("```")
    print("Issues: Duplicated 20+ times, inconsistent behavior, hard to maintain")

    # === NEW PATTERN (Centralized) ===
    print("\n✅ NEW PATTERN - Centralized Mock Factory:")
    print("```python")
    print("from tests.fixtures.mock_factories import ManagerMockFactory")
    print("")
    print("@patch('commands.setup.SessionManager')")
    print("def test_setup_session(self, mock_session_manager):")
    print("    # One line replaces 10+ lines of setup")
    print("    mock_manager_instance = ManagerMockFactory.create_session_manager_mock()")
    print("    mock_session_manager.return_value = mock_manager_instance")
    print("    # ... test code ...")
    print("```")
    print("Benefits: Consistent behavior, easy to maintain, customizable")

    # === EVEN BETTER - Using Context Factory ===
    print("\n🚀 BEST PATTERN - Context Factory:")
    print("```python")
    print("from tests.fixtures.mock_factories import PatchContextFactory")
    print("")
    print("def test_setup_session():")
    print("    with PatchContextFactory.patch_session_manager() as mock_manager:")
    print("        # Mock automatically configured and patched")
    print("        # ... test code ...")
    print("```")
    print("Benefits: Zero boilerplate, automatic cleanup, type safety")

    # === FIXTURE PATTERN ===
    print("\n⭐ FIXTURE PATTERN - pytest Integration:")
    print("```python")
    print("def test_with_session_manager(mock_session_manager):")
    print("    # Uses centralized fixture from conftest.py")
    print("    assert mock_session_manager.create_session.return_value is True")
    print("    # ... test code ...")
    print("```")
    print("Benefits: Automatic injection, shared across tests, easy to override")


def demo_customization_options():
    """Show how to customize the centralized mocks."""
    print("\n\n🎛️ Customization Examples")
    print("=" * 50)

    # Custom session data
    print("\n1️⃣ Custom Session Data:")
    custom_sessions = [
        {"session_name": "django-dev", "status": "active"},
        {"session_name": "api-server", "status": "stopped"},
    ]

    mock_manager = ManagerMockFactory.create_session_manager_mock(
        sessions=custom_sessions,
        create_session_result=False,  # Simulate failure
    )

    print(f"   Sessions: {mock_manager.get_sessions.return_value}")
    print(f"   Create result: {mock_manager.create_session.return_value}")

    # Custom controller behavior
    print("\n2️⃣ Custom Controller Behavior:")
    mock_controller = MagicMock()
    mock_controller.session_name = "custom-session"
    mock_controller.status = "error"

    mock_claude = ManagerMockFactory.create_claude_manager_mock(
        controller_count=3,
        get_controller_result=mock_controller,
        controllers_status={
            "session1": "running",
            "session2": "error",
            "session3": "stopped",
        },
    )

    print(f"   Controller count: {mock_claude.get_controller_count.return_value}")
    print(f"   Controller status: {mock_claude.get_controller.return_value.status}")
    print(f"   All statuses: {mock_claude.get_all_status.return_value}")

    # Error simulation
    print("\n3️⃣ Error Simulation:")

    def raise_validation_error(session_name):
        if "invalid" in session_name:
            raise ValueError(f"Invalid session name: {session_name}")

    mock_manager = ManagerMockFactory.create_session_manager_mock(
        validate_session_name_side_effect=raise_validation_error,
    )

    try:
        mock_manager.validate_session_name("invalid-session")
    except ValueError as e:
        print(f"   Validation error: {e}")

    print("   Valid session: OK")
    mock_manager.validate_session_name("valid-session")


def demo_migration_example():
    """Show a real migration example."""
    print("\n\n📦 Migration Example")
    print("=" * 50)

    print("Before migration (duplicated across multiple files):")
    print("=" * 30)
    old_test_code = """
@patch('api.routes.sessions.SessionManager')
def test_get_sessions_list(self, mock_session_manager):
    # 15 lines of repetitive setup
    mock_manager_instance = MagicMock()
    mock_session_data = {
        "session_name": "test-session",
        "status": "active",
        "windows": [{"name": "main", "panes": 2}]
    }
    mock_manager_instance.get_sessions.return_value = [mock_session_data]
    mock_manager_instance.create_session.return_value = True
    mock_manager_instance.session_exists.return_value = True
    mock_session_manager.return_value = mock_manager_instance

    # Actual test (2 lines)
    response = client.get("/api/sessions")
    assert response.status_code == 200
"""

    print(old_test_code)

    print("\nAfter migration (using centralized factory):")
    print("=" * 30)
    new_test_code = """
def test_get_sessions_list(mock_session_manager):
    # 0 lines of setup - fixture handles everything!

    # Actual test (2 lines)
    response = client.get("/api/sessions")
    assert response.status_code == 200
"""

    print(new_test_code)

    print("Migration benefits:")
    print("✅ Reduced from 17 lines to 4 lines (75% reduction)")
    print("✅ Zero boilerplate setup code")
    print("✅ Consistent mock behavior across all tests")
    print("✅ Easy to modify behavior globally")
    print("✅ Type safety and IDE support")


def demo_priority_targets():
    """Show the highest impact migration targets."""
    print("\n\n🎯 Priority Migration Targets")
    print("=" * 50)

    targets = [
        ("SessionManager", 20, "10 files", "HIGH"),
        ("ClaudeManager", 9, "7 files", "HIGH"),
        ("subprocess.run", 15, "8 files", "MEDIUM"),
        ("TmuxManager", 6, "4 files", "MEDIUM"),
        ("libtmux.Server", 4, "4 files", "LOW"),
    ]

    print("Priority | Mock Object    | Uses | Files | Impact")
    print("---------|----------------|------|-------|--------")
    for obj, uses, files, priority in targets:
        print(f"{priority:8} | {obj:14} | {uses:4} | {files:5} | {'🔥' if priority == 'HIGH' else '🔸' if priority == 'MEDIUM' else '🔹'}")

    print("\nRecommended migration order:")
    print("1. SessionManager - Highest impact (20 duplications)")
    print("2. ClaudeManager - High impact (9 duplications)")
    print("3. subprocess.run - Medium impact (widespread usage)")
    print("4. TmuxManager - Medium impact (4 files)")
    print("5. libtmux.Server - Lower impact (specialized usage)")


if __name__ == "__main__":
    demo_old_vs_new_patterns()
    demo_customization_options()
    demo_migration_example()
    demo_priority_targets()

    print("\n\n🎉 Mock Centralization Demo Complete!")
    print("\nNext steps:")
    print("1. Migrate SessionManager tests (highest impact)")
    print("2. Migrate ClaudeManager tests")
    print("3. Update test documentation")
    print("4. Add lint rules to prevent future duplication")
