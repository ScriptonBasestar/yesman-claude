import subprocess  # noqa: S404

from fastapi import APIRouter, HTTPException

from libs.core.session_manager import SessionManager

from ..shared import claude_manager

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Controller management API endpoints."""


router = APIRouter()
# Using shared ClaudeManager instance to ensure consistency across all API endpoints
cm = claude_manager


@router.get("/sessions/{session_name}/controller/status", response_model=str)
def get_controller_status(session_name: str) -> str | None:
    """지정된 세션의 컨트롤러 상태를 조회합니다 ('running' 또는 'stopped').

    Returns:
        Dict containing status information.
    """
    try:
        controller = cm.get_controller(session_name)
    except (AttributeError, KeyError, RuntimeError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get controller status: {e!s}",
        )
    else:
        return "running" if controller.is_running else "stopped"


@router.post("/sessions/{session_name}/controller/start", status_code=204)
def start_controller(session_name: str) -> None:  # noqa: PLR1702
    """지정된 세션의 컨트롤러를 시작합니다."""
    try:
        controller = cm.get_controller(session_name)

        # First check if session exists

        session_manager = SessionManager()
        sessions = session_manager.get_all_sessions()

        session_exists = any(s.session_name == session_name and s.status == "running" for s in sessions)

        if not session_exists:
            raise HTTPException(
                status_code=400,
                detail=(f"❌ Session '{session_name}' is not running. Please start the session first using 'yesman up' or the dashboard."),
            )

        # Check if controller is already running
        if controller.is_running:
            raise HTTPException(
                status_code=400,
                detail=(f"✅ Controller for session '{session_name}' is already running."),
            )

        # Check if Claude pane exists before attempting to start
        if not controller.claude_pane:
            # Get detailed session information for debugging
            pane_info = []
            window_count = 0
            total_panes = 0

            try:
                if controller.session_manager.session:
                    for window in controller.session_manager.session.list_windows():
                        window_count += 1
                        panes_in_window = window.list_panes()
                        total_panes += len(panes_in_window)

                        for pane in panes_in_window:
                            try:
                                cmd = pane.cmd(
                                    "display-message",
                                    "-p",
                                    "#{pane_current_command}",
                                ).stdout[0]
                                pane_info.append(
                                    f"Window '{window.name}' Pane {pane.index}: {cmd}",
                                )
                            except (OSError, subprocess.CalledProcessError, RuntimeError) as e:
                                pane_info.append(
                                    f"Window '{window.name}' Pane {pane.index}: <command unknown> (error: {e!s})",
                                )
                else:
                    pane_info.append("❌ Could not access session information")
            except (AttributeError, RuntimeError, OSError) as e:
                pane_info.append(f"❌ Error accessing session: {e!s}")

            detail_msg = (
                f"❌ No Claude Code pane found in session '{session_name}'. "
                f"Make sure Claude Code (claude) is running in one of the panes.\n\n"
                f"📊 Session Info:\n"
                f"• Windows: {window_count}\n"
                f"• Total Panes: {total_panes}\n\n"
                f"🔍 Current Panes:\n"
            )

            if pane_info:
                detail_msg += "\n".join(f"  • {info}" for info in pane_info)
            else:
                detail_msg += "  • No panes found"

            detail_msg += f"\n\n💡 To fix this:\n1. Open session: tmux attach -t {session_name}\n2. Start Claude Code in a pane: claude\n3. Try starting the controller again"

            raise HTTPException(status_code=500, detail=detail_msg)

        # Try to start the controller with detailed error handling
        try:
            success = controller.start()

            if not success:
                # Get more specific error from the controller
                error_details = []

                # Check session manager state
                if not controller.session_manager.initialize_session():
                    error_details.append("❌ Session manager failed to initialize")

                # Check if monitoring can start
                if hasattr(controller, "monitor"):
                    try:
                        monitor_status = controller.monitor.is_running
                        error_details.append(f"📊 Monitor running: {monitor_status}")
                    except (AttributeError, RuntimeError) as e:
                        error_details.append(f"❌ Monitor error: {e!s}")

                detail_msg = f"❌ Controller failed to start for session '{session_name}'. The system encountered an internal error.\n\n🔍 Diagnostic Information:\n"

                if error_details:
                    detail_msg += "\n".join(f"  • {info}" for info in error_details)
                else:
                    detail_msg += "  • No specific error information available"

                detail_msg += (
                    f"\n\n💡 Troubleshooting Steps:\n"
                    f"1. Check if Claude Code is responsive in the session\n"
                    f"2. Restart the session: yesman down {session_name} && "
                    f"yesman up {session_name}\n"
                    f"3. Check logs: yesman logs {session_name}\n"
                    f"4. Try restarting the API server"
                )

                raise HTTPException(status_code=500, detail=detail_msg)

        except (RuntimeError, OSError, subprocess.CalledProcessError, AttributeError) as start_error:
            # Detailed error information for start failures
            detail_msg = (
                f"❌ Controller start failed for session '{session_name}': "
                f"{start_error!s}\n\n"
                f"🔍 Error Type: {type(start_error).__name__}\n"
                f"📊 Session Status: {'Running' if session_exists else 'Not Running'}\n"
                f"🔧 Claude Pane: {'Found' if controller.claude_pane else 'Not Found'}\n\n"
                f"💡 Common Solutions:\n"
                f"1. Ensure Claude Code is running: tmux attach -t {session_name}\n"
                f"2. Check if claude command is available in the pane\n"
                f"3. Try restarting the session\n"
                f"4. Check system logs for more details"
            )

            raise HTTPException(status_code=500, detail=detail_msg)

        return

    except HTTPException:
        raise
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError, TypeError) as e:
        # Catch-all for unexpected errors
        detail_msg = (
            f"❌ Unexpected error starting controller for session '{session_name}': "
            f"{e!s}\n\n"
            f"🔍 Error Type: {type(e).__name__}\n"
            f"📍 This is likely a system-level issue.\n\n"
            f"💡 Please try:\n"
            f"1. Restart the API server\n"
            f"2. Check system logs\n"
            f"3. Verify tmux is running properly\n"
            f"4. Report this error if it persists"
        )

        raise HTTPException(
            status_code=500,
            detail=detail_msg,
        )


@router.post("/sessions/{session_name}/controller/stop", status_code=204)
def stop_controller(session_name: str) -> None:
    """지정된 세션의 컨트롤러를 중지합니다."""
    try:
        controller = cm.get_controller(session_name)

        # 이미 중지되어 있는 경우도 성공으로 처리
        if not controller.is_running:
            return

        success = controller.stop()
        if not success:
            # 컨트롤러가 이미 중지되어 있을 수 있으므로 상태 확인
            if not controller.is_running:
                return  # 이미 중지됨 - 성공으로 처리

            detail_msg = (
                f"❌ Controller failed to stop gracefully for session "
                f"'{session_name}'.\n\n"
                f"🔍 The controller may be in an inconsistent state.\n\n"
                f"💡 Troubleshooting Steps:\n"
                f"1. Try stopping again in a few seconds\n"
                f"2. Check if the tmux session still exists\n"
                f"3. Force restart the session if necessary\n"
                f"4. Restart the API server if the issue persists"
            )

            raise HTTPException(
                status_code=500,
                detail=detail_msg,
            )
        return
    except HTTPException:
        raise
    except (RuntimeError, OSError, AttributeError, KeyError) as e:
        detail_msg = (
            f"❌ Failed to stop controller for session '{session_name}': {e!s}\n\n"
            f"🔍 Error Type: {type(e).__name__}\n\n"
            f"💡 This might be caused by:\n"
            f"1. Session no longer exists\n"
            f"2. Controller is already stopped\n"
            f"3. System-level issue\n\n"
            f"🔧 Usually this error can be ignored if the session is being torn down."
        )

        raise HTTPException(
            status_code=500,
            detail=detail_msg,
        )


@router.post("/sessions/{session_name}/controller/restart", status_code=204)
def restart_claude_pane(session_name: str) -> None:
    """Claude가 실행 중인 pane을 재시작합니다."""
    try:
        controller = cm.get_controller(session_name)

        # Check if Claude pane exists
        if not controller.claude_pane:
            detail_msg = (
                f"❌ Cannot restart Claude pane for session '{session_name}' - "
                f"no Claude pane found.\n\n"
                f"🔍 Make sure Claude Code is running in the session.\n\n"
                f"💡 To fix this:\n"
                f"1. Open session: tmux attach -t {session_name}\n"
                f"2. Start Claude Code in a pane: claude\n"
                f"3. Try the restart again"
            )

            raise HTTPException(
                status_code=400,
                detail=detail_msg,
            )

        success = controller.restart_claude_pane()
        if not success:
            detail_msg = (
                f"❌ Failed to restart Claude pane for session '{session_name}'.\n\n"
                f"🔍 The pane restart operation failed.\n\n"
                f"💡 Troubleshooting Steps:\n"
                f"1. Check if Claude Code is responsive in the session\n"
                f"2. Manually restart Claude Code: tmux attach -t {session_name}\n"
                f"3. Try stopping and starting the controller instead\n"
                f"4. Check session logs for more details"
            )

            raise HTTPException(
                status_code=500,
                detail=detail_msg,
            )
        return
    except HTTPException:
        raise
    except (RuntimeError, OSError, subprocess.CalledProcessError, AttributeError) as e:
        detail_msg = (
            f"❌ Failed to restart Claude pane for session '{session_name}': "
            f"{e!s}\n\n"
            f"🔍 Error Type: {type(e).__name__}\n\n"
            f"💡 This might be caused by:\n"
            f"1. Session no longer exists\n"
            f"2. Claude pane is not responsive\n"
            f"3. System-level tmux issue\n\n"
            f"🔧 Try manually restarting the session if this persists."
        )

        raise HTTPException(
            status_code=500,
            detail=detail_msg,
        )


@router.post("/controllers/start-all", status_code=200)
def start_all_controllers() -> object:
    """모든 활성 세션의 컨트롤러를 시작합니다.

    Returns:
        Object object.
    """
    try:
        session_manager = SessionManager()
        sessions = session_manager.get_all_sessions()

        # 실행 중인 세션들만 필터링
        running_sessions = [s for s in sessions if s.status == "running"]

        if not running_sessions:
            return {
                "message": "No running sessions found to start controllers.",
                "started": 0,
                "errors": [],
            }

        started_count = 0
        errors = []

        for session in running_sessions:
            try:
                controller = cm.get_controller(session.session_name)
                if not controller.is_running:
                    success = controller.start()
                    if success:
                        started_count += 1
                    else:
                        errors.append(f"Failed to start controller for session '{session.session_name}'")
                else:
                    # 이미 실행 중인 경우도 성공으로 카운트
                    started_count += 1
            except (RuntimeError, OSError, AttributeError) as e:
                errors.append(f"Error starting controller for session '{session.session_name}': {e!s}")

        if errors and started_count == 0:
            # 모든 요청이 실패한 경우
            raise HTTPException(
                status_code=500,
                detail=(f"Failed to start any controllers. Errors: {'; '.join(errors)}"),
            )

        return {
            "message": (f"Started {started_count} controller(s) out of {len(running_sessions)} session(s)."),
            "started": started_count,
            "total_sessions": len(running_sessions),
            "errors": errors,
        }

    except HTTPException:
        raise
    except (ImportError, AttributeError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to start all controllers: {e!s}")


@router.post("/controllers/stop-all", status_code=200)
def stop_all_controllers() -> object:
    """모든 활성 세션의 컨트롤러를 중지합니다.

    Returns:
        Object object.
    """
    try:
        session_manager = SessionManager()
        sessions = session_manager.get_all_sessions()

        # 실행 중인 세션들만 필터링
        running_sessions = [s for s in sessions if s.status == "running"]

        if not running_sessions:
            return {
                "message": "No running sessions found to stop controllers.",
                "stopped": 0,
                "errors": [],
            }

        stopped_count = 0
        errors = []

        for session in running_sessions:
            try:
                controller = cm.get_controller(session.session_name)
                if controller.is_running:
                    success = controller.stop()
                    if success:
                        stopped_count += 1
                    # 중지 실패 후 상태 재확인
                    elif not controller.is_running:
                        stopped_count += 1  # 실제로는 중지됨
                    else:
                        errors.append(f"Failed to stop controller for session '{session.session_name}'")
                else:
                    # 이미 중지된 경우도 성공으로 카운트
                    stopped_count += 1
            except (RuntimeError, OSError, AttributeError) as e:
                errors.append(f"Error stopping controller for session '{session.session_name}': {e!s}")

        if errors and stopped_count == 0:
            # 모든 요청이 실패한 경우
            raise HTTPException(
                status_code=500,
                detail=(f"Failed to stop any controllers. Errors: {'; '.join(errors)}"),
            )

        return {
            "message": (f"Stopped {stopped_count} controller(s) out of {len(running_sessions)} session(s)."),
            "stopped": stopped_count,
            "total_sessions": len(running_sessions),
            "errors": errors,
        }

    except HTTPException:
        raise
    except (ImportError, AttributeError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop all controllers: {e!s}")
