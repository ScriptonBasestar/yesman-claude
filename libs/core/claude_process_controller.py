# Copyright notice.

import logging
import time

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Claude process control and lifecycle management."""


class ClaudeProcessController:
    """Controls Claude process lifecycle (start, stop, restart)."""

    def __init__(session_manager: status_manager, object) -> None:
        self.session_manager = session_manager
        self.status_manager = status_manager
        self.selected_model = "default"
        self.logger = logging.getLogger(f"yesman.claude_process.{session_manager.session_name}")

    def set_model(self, model: str) -> None:
        """Set the selected model."""
        self.selected_model = model
        self.status_manager.update_status(f"[cyan]Model set to: {model}[/]")

    def restart_claude_pane(self) -> bool:
        """Restart Claude pane.

    Returns:
        Boolean indicating."""
        if not self.session_manager.get_claude_pane():
            self.status_manager.update_status("[red]Cannot restart: No Claude pane in session[/]")
            return False

        try:
            self.status_manager.update_status("[yellow]Restarting Claude pane...[/]")

            # Force kill any existing claude process and clear the pane
            self._terminate_claude_process()

            # Start claude with selected model
            claude_cmd = self._get_claude_command()
            self.session_manager.send_keys(claude_cmd)

            self.status_manager.update_status(f"[green]Claude pane restarted with {self.selected_model} model[/]")
            return True

        except Exception as e:
            self.status_manager.update_status(f"[red]Failed to restart Claude pane: {e}[/]")
            self.logger.exception("Failed to restart Claude pane")  # noqa: G004
            return False

    def _terminate_claude_process(self) -> None:
        """Terminate any existing claude process in the pane."""
        try:
            # Send multiple Ctrl+C to ensure termination
            self.session_manager.send_keys("C-c")
            time.sleep(0.5)
            self.session_manager.send_keys("C-c")
            time.sleep(0.5)

            # Send Ctrl+D to exit any interactive shell
            self.session_manager.send_keys("C-d")
            time.sleep(0.5)

            # Clear the screen and any remaining input
            self.session_manager.send_keys("clear")
            time.sleep(0.5)

            # Wait for processes to fully terminate
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    # Check if claude is still running by checking the command
                    cmd = self.session_manager.get_current_command()
                    if "claude" not in cmd.lower():
                        self.logger.info(f"Claude process terminated after {attempt + 1} attempts")  # noqa: G004
                        break
                except Exception:
                    # If we can't get the command, assume it's terminated
                    break

                # Try more aggressive termination
                self.session_manager.send_keys("C-c")
                time.sleep(1)

            # Final clear and prepare for new command
            self.session_manager.send_keys("clear")
            time.sleep(0.2)

        except Exception as e:
            self.logger.warning(f"Error during claude process termination: {e}")  # noqa: G004

    def _get_claude_command(self) -> str:
        """Get claude command based on selected model.

    Returns:
        String containing the requested data."""
        if self.selected_model == "opus":
            return "claude --model claude-3-5-opus-20241022"
        if self.selected_model == "sonnet":
            return "claude --model claude-3-5-sonnet-20241022"
        return "claude"

    def is_claude_running(self) -> bool:
        """Check if Claude is currently running.

    Returns:
        Boolean indicating."""
        try:
            cmd = self.session_manager.get_current_command()
            return "claude" in cmd.lower()
        except Exception:
            return False

    def send_input(self, text: str) -> None:
        """Send input to Claude pane."""
        self.session_manager.send_keys(text)
