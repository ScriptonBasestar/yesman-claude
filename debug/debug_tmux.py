#!/usr/bin/env python3
"""Debug tmux command issues"""

import libtmux


def main():
    print("🔍 Debugging tmux command detection...")

    server = libtmux.Server()
    session = server.find_where({"session_name": "proxynd"})

    if not session:
        print("❌ Session 'proxynd' not found")
        return

    print(f"✅ Found session: {session}")

    for window in session.list_windows():
        print(f"📋 Window: {window.name} (index: {window.index})")

        for pane in window.list_panes():
            print(f"  🔹 Pane {pane.index}:")

            try:
                # Test 1: Try the current method
                cmd_result = pane.cmd("display-message", "-p", "#{pane_current_command}")
                print(f"    cmd result: {cmd_result}")
                print(f"    stdout: {cmd_result.stdout}")
                if cmd_result.stdout:
                    cmd = cmd_result.stdout[0]
                    print(f"    command: '{cmd}'")
                    print(f"    'claude' in cmd.lower(): {'claude' in cmd.lower()}")

            except Exception as e:
                print(f"    ❌ Error getting command: {e}")
                print(f"    Error type: {type(e)}")

            try:
                # Test 2: Try alternative method
                cmd_alt = pane.display_message("#{pane_current_command}")
                print(f"    alternative method: '{cmd_alt}'")

            except Exception as e:
                print(f"    ❌ Error with alternative: {e}")

            try:
                # Test 3: Capture content
                content_result = pane.cmd("capture-pane", "-p")
                content = "\n".join(content_result.stdout) if content_result.stdout else ""
                print(f"    content length: {len(content)}")
                print(f"    content preview: {repr(content[:100])}")

            except Exception as e:
                print(f"    ❌ Error capturing content: {e}")


if __name__ == "__main__":
    main()
