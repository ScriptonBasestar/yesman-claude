#!/usr/bin/env python3
"""실시간 Controller 로그 뷰어 - 디버깅용"""

import argparse
import time
from pathlib import Path

from libs.core.claude_manager import ClaudeManager
from libs.core.session_manager import SessionManager


def print_header():
    """헤더 출력"""
    print("=" * 80)
    print("🚀 YESMAN CONTROLLER REAL-TIME LOG VIEWER")
    print("=" * 80)
    print()


def get_controller_status(claude_manager, session_name):
    """컨트롤러 상태 확인"""
    try:
        controller = claude_manager.get_controller(session_name)
        if not controller:
            return "❌ Controller not found"

        status = "🟢 ACTIVE" if controller.is_running else "⚪ READY"
        auto_next = "✅ ON" if controller.is_auto_next_enabled else "❌ OFF"
        model = controller.selected_model
        waiting = "⏳ YES" if controller.is_waiting_for_input() else "✅ NO"

        return f"{status} | Auto-Next: {auto_next} | Model: {model} | Waiting: {waiting}"
    except Exception as e:
        return f"❌ Error: {e}"


def monitor_logs(session_name, follow=True):
    """로그 실시간 모니터링"""
    log_path = Path("~/tmp/logs/yesman/").expanduser()
    controller_log = log_path / f"claude_manager_{session_name}.log"

    print(f"📁 Log file: {controller_log}")
    print(f"📊 Monitoring session: {session_name}")
    print()

    # 컨트롤러 상태 확인
    claude_manager = ClaudeManager()
    session_manager = SessionManager()

    if not follow:
        # 한 번만 상태 체크
        print("🔍 Current Controller Status:")
        print("-" * 50)
        status = get_controller_status(claude_manager, session_name)
        print(f"Status: {status}")
        print()

        # 최근 로그 출력
        if controller_log.exists():
            print("📋 Recent Log Entries (last 20 lines):")
            print("-" * 50)
            with open(controller_log) as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line.rstrip())
        else:
            print("⚠️  Log file not found. Controller may not have been started yet.")
        return

    # 실시간 모니터링
    print("🔄 Starting real-time monitoring... (Press Ctrl+C to stop)")
    print("=" * 80)

    last_position = 0
    status_check_interval = 5  # 5초마다 상태 체크
    last_status_check = 0

    try:
        while True:
            current_time = time.time()

            # 주기적으로 컨트롤러 상태 출력
            if current_time - last_status_check >= status_check_interval:
                print()
                print(f"⏰ [{time.strftime('%H:%M:%S')}] Controller Status Check:")
                status = get_controller_status(claude_manager, session_name)
                print(f"   {status}")
                print("-" * 80)
                last_status_check = current_time

            # 로그 파일 체크
            if controller_log.exists():
                current_size = controller_log.stat().st_size

                if current_size > last_position:
                    with open(controller_log) as f:
                        f.seek(last_position)
                        new_content = f.read()

                        for line in new_content.splitlines():
                            if line.strip():
                                # 로그 라인 색상화
                                timestamp = time.strftime("%H:%M:%S")
                                if "ERROR" in line:
                                    print(f"🔴 [{timestamp}] {line}")
                                elif "WARNING" in line:
                                    print(f"🟡 [{timestamp}] {line}")
                                elif "Auto-respond" in line:
                                    print(f"🤖 [{timestamp}] {line}")
                                elif "Prompt detected" in line:
                                    print(f"⏳ [{timestamp}] {line}")
                                elif "Starting monitoring" in line:
                                    print(f"🚀 [{timestamp}] {line}")
                                elif "Stopping" in line or "stopped" in line:
                                    print(f"⏹️  [{timestamp}] {line}")
                                else:
                                    print(f"ℹ️  [{timestamp}] {line}")

                    last_position = current_size
            else:
                # 로그 파일이 없으면 주기적으로 알림
                if current_time - last_status_check >= status_check_interval:
                    print(f"⚠️  [{time.strftime('%H:%M:%S')}] Log file not found: {controller_log}")

            time.sleep(0.5)  # 0.5초마다 체크

    except KeyboardInterrupt:
        print()
        print("👋 Monitoring stopped by user")


def list_sessions():
    """사용 가능한 세션 목록"""
    try:
        session_manager = SessionManager()
        sessions = session_manager.get_all_sessions()

        print("📊 Available Sessions:")
        print("-" * 50)

        if not sessions:
            print("❌ No sessions found. Run './yesman.py setup' first.")
            return

        for session in sessions:
            status_icon = "🟢" if session.status == "running" else "🔴"
            print(f"{status_icon} {session.session_name} ({session.project_name}) - {session.status}")

        print()
        print("💡 Usage: python debug_controller.py <session_name>")

    except Exception as e:
        print(f"❌ Error listing sessions: {e}")


def main():
    parser = argparse.ArgumentParser(description="Yesman Controller Real-time Log Viewer")
    parser.add_argument("session_name", nargs="?", help="Session name to monitor")
    parser.add_argument("--list", "-l", action="store_true", help="List available sessions")
    parser.add_argument("--once", "-o", action="store_true", help="Check status once and show recent logs")

    args = parser.parse_args()

    print_header()

    if args.list:
        list_sessions()
        return

    if not args.session_name:
        print("❌ Please provide a session name or use --list to see available sessions")
        print()
        list_sessions()
        return

    monitor_logs(args.session_name, follow=not args.once)


if __name__ == "__main__":
    main()
