"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Claude monitoring and auto-response system."""

import asyncio
import logging
import threading
import time

from libs.ai.adaptive_response import AdaptiveConfig, AdaptiveResponse
from libs.automation.automation_manager import AutomationManager
from libs.dashboard.health_calculator import HealthCalculator
from libs.logging.async_logger import AsyncLogger, AsyncLoggerConfig, LogLevel

from .content_collector import ClaudeContentCollector
from .prompt_detector import ClaudePromptDetector, PromptInfo, PromptType


class ClaudeMonitor:
    """Handles Claude monitoring and auto-response logic."""

    def __init__(self, session_manager: object, process_controller: object, status_manager: object) -> None:
        self.session_manager = session_manager
        self.process_controller = process_controller
        self.status_manager = status_manager
        self.session_name = session_manager.session_name

        # Monitoring state
        self.is_running = False
        self._monitor_thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

        # Auto-response settings
        self.is_auto_next_enabled = True
        self.yn_mode = "Auto"
        self.yn_response = "y"
        self.mode12 = "Auto"
        self.mode12_response = "1"
        self.mode123 = "Auto"
        self.mode123_response = "1"

        # Prompt detection
        self.prompt_detector = ClaudePromptDetector()
        self.content_collector = ClaudeContentCollector(session_manager.session_name)
        self.current_prompt: PromptInfo | None = None
        self.waiting_for_input = False

        # AI-powered adaptive response system
        self.adaptive_response = AdaptiveResponse(
            config=AdaptiveConfig(
                min_confidence_threshold=0.7,
                learning_enabled=True,
                auto_response_enabled=True,
                response_delay_ms=1500,  # Slightly longer delay for more natural interaction
            ),
        )

        # Context-aware automation system
        self.automation_manager = AutomationManager(
            project_path=None,  # Will use current working directory
        )

        # Project health monitoring system
        self.health_calculator = HealthCalculator(
            project_path=None,  # Will use current working directory
        )

        # High-performance async logging system
        self.async_logger: AsyncLogger | None = None

        self.logger = logging.getLogger(f"yesman.claude_monitor.{self.session_name}")

    def set_auto_next(self, enabled: bool) -> None:  # noqa: FBT001
        """Enable or disable auto-next responses."""
        self.is_auto_next_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self.status_manager.update_status(f"[cyan]Auto next {status}[/]")

    def set_mode_yn(self, mode: str, response: str) -> None:
        """Set manual override for Y/N prompts."""
        self.yn_mode = mode
        self.yn_response = response

    def set_mode_12(self, mode: str, response: str) -> None:
        """Set manual override for 1/2 prompts."""
        self.mode12 = mode
        self.mode12_response = response

    def set_mode_123(self, mode: str, response: str) -> None:
        """Set manual override for 1/2/3 prompts."""
        self.mode123 = mode
        self.mode123_response = response

    def start_monitoring(self) -> bool:
        """Start the monitoring loop."""
        if not self.session_manager.get_claude_pane():
            self.status_manager.update_status("[red]Cannot start: No Claude pane in session[/]")
            return False

        if self.is_running:
            self.status_manager.update_status("[yellow]Monitor already running[/]")
            return False

        try:
            self.is_running = True
            self.status_manager.update_status(f"[green]Starting claude monitor for {self.session_name}[/]")

            # Start monitoring in a separate thread with its own event loop
            self._monitor_thread = threading.Thread(target=self._run_monitor_loop, daemon=True)
            self._monitor_thread.start()

            return True

        except Exception as e:
            self.is_running = False
            self.status_manager.update_status(f"[red]Failed to start claude monitor: {e}[/]")
            self.logger.error("Failed to start claude monitor: {e}", exc_info=True)
            return False

    def stop_monitoring(self) -> bool:
        """Stop the monitoring loop."""
        if not self.is_running:
            self.status_manager.update_status("[yellow]Claude monitor not running[/]")
            return False

        self.is_running = False

        # Stop the event loop if it's running
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)

        self.status_manager.update_status(f"[red]Stopped claude monitor for {self.session_name}[/]")
        return True

    def _run_monitor_loop(self) -> None:
        """Run the monitor loop in its own thread with event loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._monitor_loop())
        except Exception:
            self.logger.error("Monitor loop error: {e}", exc_info=True)
        finally:
            self._loop.close()
            self.is_running = False

    async def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in background."""
        if not self.session_manager.get_claude_pane():
            self.logger.error("Cannot start monitoring: no Claude pane for {self.session_name}")
            self.is_running = False
            return

        self.logger.info("Starting monitoring loop for {self.session_name}")
        last_content = ""

        try:
            while self.is_running:
                await asyncio.sleep(1)  # Check every second

                try:
                    content = self.session_manager.capture_pane_content()

                    # Check if Claude is still running
                    if not self.process_controller.is_claude_running():
                        if self.is_auto_next_enabled:
                            self.status_manager.update_activity("🔄 Auto-restarting Claude...")
                            self.process_controller.restart_claude_pane()
                            continue
                        self.status_manager.update_status("[yellow]Claude not running. Auto-restart disabled.[/]")
                        continue

                    # Check for prompts and auto-respond if enabled
                    prompt_info = self._check_for_prompt(content)

                    if prompt_info:
                        # Try adaptive AI-powered response first if auto_next is enabled
                        if self.is_auto_next_enabled:
                            context = f"session:{self.session_name}, type:{prompt_info.type.value}"
                            (
                                should_respond,
                                ai_response,
                                confidence,
                            ) = await self.adaptive_response.should_auto_respond(
                                prompt_info.question,
                                context,
                                self.session_name,
                            )

                            if should_respond:
                                # Send AI-predicted response
                                success = await self.adaptive_response.send_adaptive_response(
                                    prompt_info.question,
                                    ai_response,
                                    confidence,
                                    context,
                                    self.session_name,
                                )

                                if success:
                                    self.process_controller.send_input(ai_response)
                                    self.status_manager.update_activity(f"🤖 AI auto-responded: '{ai_response}' (confidence: {confidence:.2f})")
                                    self.status_manager.record_response(prompt_info.type.value, ai_response, content)
                                    self.adaptive_response.confirm_response_success(
                                        prompt_info.question,
                                        ai_response,
                                        context,
                                        self.session_name,
                                        True,
                                    )
                                    self._clear_prompt_state()
                                    continue

                            # Fall back to legacy pattern-based auto-response if AI didn't handle it
                            if self._auto_respond_to_selection(prompt_info):
                                response = self._get_legacy_response(prompt_info)
                                self.status_manager.update_activity(f"✅ Legacy auto-responded: '{response}' to {prompt_info.type.value}")
                                self.status_manager.record_response(prompt_info.type.value, response, content)
                                # Learn from legacy response for future AI improvements
                                self.adaptive_response.learn_from_manual_response(
                                    prompt_info.question,
                                    response,
                                    context,
                                    self.session_name,
                                )
                                self._clear_prompt_state()
                                continue

                        # If auto-response didn't handle it, show waiting status
                        self.status_manager.update_activity(f"⏳ Waiting for input: {prompt_info.type.value}")
                        self.logger.debug("Prompt detected: {prompt_info.type.value} - {prompt_info.question}")
                    elif self.waiting_for_input:
                        self.status_manager.update_activity("⏳ Waiting for user input...")
                    else:
                        # Clear prompt state if no longer waiting
                        self._clear_prompt_state()

                    # Periodically update AI patterns
                    await self.adaptive_response.update_patterns()

                    # Analyze content for automation contexts
                    if content != last_content and len(content.strip()) > 0:
                        automation_contexts = self.automation_manager.analyze_content_for_context(content, self.session_name)
                        for auto_context in automation_contexts:
                            self.logger.info("Automation context detected: {auto_context.context_type.value} (confidence: {auto_context.confidence:.2f})")

                    # Check for Claude idle automation opportunities
                    if hasattr(self.status_manager, "last_activity_time"):
                        idle_context = self.automation_manager.analyze_claude_idle(
                            self.status_manager.last_activity_time,
                            idle_threshold=60,
                        )
                        if idle_context:
                            self.logger.debug("Claude idle context: {idle_context.confidence:.2f}")

                    # Collect content for pattern analysis
                    if content != last_content and len(content.strip()) > 0:
                        try:
                            # Convert PromptInfo to dict for collection compatibility
                            prompt_dict = None
                            if prompt_info:
                                prompt_dict = {
                                    "type": prompt_info.type.value,
                                    "question": prompt_info.question,
                                    "options": prompt_info.options,
                                    "confidence": prompt_info.confidence,
                                }
                            self.content_collector.collect_interaction(content, prompt_dict, None)
                        except Exception:
                            self.logger.exception("Failed to collect content: {e}")

                    # Update activity if content changed
                    if content != last_content:
                        self.status_manager.update_activity("📝 Content updated")
                        last_content = content

                except Exception:
                    self.logger.exception("Error in monitoring loop: {e}")
                    await asyncio.sleep(5)  # Wait longer on errors

        except asyncio.CancelledError:
            self.logger.info("Monitoring loop cancelled")
        except Exception:
            self.logger.exception("Monitoring loop error: {e}")
        finally:
            self.is_running = False
            self.status_manager.update_status("[red]Claude monitor stopped[/]")

    def _check_for_prompt(self, content: str) -> PromptInfo | None:
        """Check if content contains a prompt waiting for input."""
        prompt_info = self.prompt_detector.detect_prompt(content)

        if prompt_info:
            self.current_prompt = prompt_info
            self.waiting_for_input = True
            self.logger.info("Prompt detected: {prompt_info.type.value} - {prompt_info.question}")
        else:
            # Check if we're still waiting for input based on content patterns
            self.waiting_for_input = self.prompt_detector.is_waiting_for_input(content)

        return prompt_info

    def _clear_prompt_state(self) -> None:
        """Clear the current prompt state."""
        self.current_prompt = None
        self.waiting_for_input = False

    def _auto_respond_to_selection(self, prompt_info: PromptInfo) -> bool:
        """Auto-respond to selection prompts based on patterns and manual overrides."""
        if not self.is_auto_next_enabled:
            self.logger.debug("Auto-response disabled, skipping")
            return False

        self.logger.info("Attempting auto-response for prompt type: {prompt_info.type.value}")

        try:
            if prompt_info.type == PromptType.NUMBERED_SELECTION:
                return self._handle_numbered_selection(prompt_info)
            if prompt_info.type == PromptType.BINARY_CHOICE:
                return self._handle_binary_choice(prompt_info)
            if prompt_info.type == PromptType.CONFIRMATION:
                return self._handle_binary_selection(prompt_info)
            if prompt_info.type == PromptType.LOGIN_REDIRECT:
                return self._handle_login_redirect(prompt_info)

        except Exception:
            self.logger.exception("Error in auto_respond_to_selection: {e}")

        return False

    def _handle_numbered_selection(self, prompt_info: PromptInfo) -> bool:
        """Handle numbered selection prompts (1, 2, 3 options)."""
        opts_count = prompt_info.metadata.get("option_count", len(prompt_info.options))

        # Check manual overrides
        if opts_count == 2 and self.mode12 == "Manual":
            response = self.mode12_response
        elif opts_count >= 3 and self.mode123 == "Manual":
            response = self.mode123_response
        else:
            # Use pattern-based response or fallback
            response = getattr(prompt_info, "recommended_response", None) or "1"

        self.process_controller.send_input(response)
        self.status_manager.record_response(prompt_info.type.value, response, prompt_info.question)
        self.logger.info("Auto-responding to numbered selection with: {response}")
        return True

    def _handle_binary_choice(self, prompt_info: PromptInfo) -> bool:
        """Handle binary choice prompts (y/n)."""
        # Check manual override
        if self.yn_mode == "Manual":
            response = self.yn_response.lower() if isinstance(self.yn_response, str) else str(self.yn_response)
        else:
            # Use pattern-based response or fallback
            response = getattr(prompt_info, "recommended_response", None) or "y"

        self.process_controller.send_input(response)
        self.status_manager.record_response(prompt_info.type.value, response, prompt_info.question)
        self.logger.info("Auto-responding to binary choice with: {response}")
        return True

    def _handle_binary_selection(self, prompt_info: PromptInfo) -> bool:
        """Handle binary selection prompts ([1] [2])."""
        # Check manual override
        if self.mode12 == "Manual":
            response = self.mode12_response
        else:
            # Use pattern-based response or fallback
            response = getattr(prompt_info, "recommended_response", None) or "1"

        self.process_controller.send_input(response)
        self.status_manager.record_response(prompt_info.type.value, response, prompt_info.question)
        self.logger.info("Auto-responding to binary selection with: {response}")
        return True

    def _handle_login_redirect(self, prompt_info: PromptInfo) -> bool:
        """Handle login redirect prompts."""
        question = prompt_info.question.lower()

        if "continue" in question or "press enter" in question:
            response = ""  # Just press Enter
            self.process_controller.send_input(response)
            self.status_manager.record_response(prompt_info.type.value, "Enter", prompt_info.question)
            self.logger.info("Auto-responding to login redirect with Enter")
            return True

        return False

    # Public interface methods
    def is_waiting_for_input(self) -> bool:
        """Check if Claude is currently waiting for user input."""
        return self.waiting_for_input

    def get_current_prompt(self) -> PromptInfo | None:
        """Get the current prompt information."""
        return self.current_prompt

    def get_collection_stats(self) -> dict:
        """Get content collection statistics."""
        return self.content_collector.get_collection_stats()

    def cleanup_old_collections(self, days_to_keep: int = 7) -> int:
        """Clean up old collection files."""
        return self.content_collector.cleanup_old_files(days_to_keep)

    def _get_legacy_response(self, prompt_info: PromptInfo) -> str:
        """Get response that would be used by legacy auto-response system."""
        try:
            if prompt_info.type == PromptType.NUMBERED_SELECTION:
                opts_count = prompt_info.metadata.get("option_count", len(prompt_info.options))
                if opts_count == 2 and self.mode12 == "Manual":
                    return self.mode12_response
                if opts_count >= 3 and self.mode123 == "Manual":
                    return self.mode123_response
                return getattr(prompt_info, "recommended_response", None) or "1"

            if prompt_info.type == PromptType.BINARY_CHOICE:
                if self.yn_mode == "Manual":
                    return self.yn_response.lower() if isinstance(self.yn_response, str) else str(self.yn_response)
                return getattr(prompt_info, "recommended_response", None) or "y"

            if prompt_info.type == PromptType.CONFIRMATION:
                if self.mode12 == "Manual":
                    return self.mode12_response
                return getattr(prompt_info, "recommended_response", None) or "1"

            if prompt_info.type == PromptType.LOGIN_REDIRECT:
                question = prompt_info.question.lower()
                if "continue" in question or "press enter" in question:
                    return ""  # Just press Enter

        except Exception:
            self.logger.exception("Error getting legacy response: {e}")

        return "1"  # Safe fallback

    # Adaptive response management methods
    def get_adaptive_statistics(self) -> dict:
        """Get statistics from the adaptive response system."""
        return self.adaptive_response.get_learning_statistics()

    def set_adaptive_confidence_threshold(self, threshold: float) -> None:
        """Adjust the confidence threshold for adaptive responses."""
        self.adaptive_response.adjust_confidence_threshold(threshold)

    def enable_adaptive_response(self, enabled: bool = True) -> None:  # noqa: FBT001
        """Enable or disable adaptive response functionality."""
        self.adaptive_response.enable_auto_response(enabled)

    def enable_adaptive_learning(self, enabled: bool = True) -> None:  # noqa: FBT001
        """Enable or disable adaptive learning functionality."""
        self.adaptive_response.enable_learning(enabled)

    def export_adaptive_data(self, output_path: str) -> bool:
        """Export adaptive learning data for analysis."""
        from pathlib import Path

        return self.adaptive_response.export_learning_data(Path(output_path))

    def learn_from_user_input(self, prompt_text: str, user_response: str, context: str = "") -> None:
        """Learn from manual user input for future improvements."""
        self.adaptive_response.learn_from_manual_response(
            prompt_text,
            user_response,
            context,
            self.session_name,
        )

    # Context-aware automation methods
    async def start_automation_monitoring(self, monitor_interval: int = 10) -> bool:
        """Start context-aware automation monitoring."""
        return await self.automation_manager.start_monitoring(monitor_interval)

    async def stop_automation_monitoring(self) -> bool:
        """Stop context-aware automation monitoring."""
        return await self.automation_manager.stop_monitoring()

    def get_automation_status(self) -> dict:
        """Get automation system status."""
        return self.automation_manager.get_automation_status()

    def register_automation_workflow(self, workflow: object) -> None:
        """Register a custom automation workflow."""
        self.automation_manager.register_custom_workflow(workflow)

    async def test_automation(self, context_type_name: str) -> dict:
        """Test automation with simulated context."""
        from libs.automation.context_detector import ContextType

        try:
            context_type = ContextType(context_type_name)
            return await self.automation_manager.test_automation_chain(context_type)
        except ValueError:
            return {"error": f"Invalid context type: {context_type_name}"}

    def get_automation_execution_history(self, limit: int = 10) -> list:
        """Get recent automation execution history."""
        return self.automation_manager.get_execution_history(limit)

    def save_automation_config(self) -> None:
        """Save automation configuration."""
        self.automation_manager.save_automation_config()

    def load_automation_config(self) -> None:
        """Load automation configuration."""
        self.automation_manager.load_automation_config()

    # Project health monitoring methods
    async def calculate_project_health(self, force_refresh: bool = False) -> dict:  # noqa: FBT001
        """Calculate comprehensive project health."""
        health = await self.health_calculator.calculate_health(force_refresh)
        return health.to_dict()

    def get_health_summary(self) -> dict:
        """Get a quick health summary."""
        # This would be cached from last calculation
        try:
            # For now, return a default summary - in real implementation this would use cached data
            return {
                "overall": {"score": 75, "level": "good", "emoji": "🟡"},
                "categories": {},
                "metrics_count": 0,
                "last_assessment": time.time(),
                "project_path": str(self.health_calculator.project_path),
            }
        except Exception as e:
            self.logger.exception("Error getting health summary: {e}")
            return {"error": str(e)}

    # Asynchronous logging methods
    async def _start_async_logging(self) -> None:
        """Start the async logging system."""
        if self.async_logger:
            return

        config = AsyncLoggerConfig(
            name=f"yesman.claude_monitor.{self.session_name}",
            level=LogLevel.INFO,
            max_queue_size=5000,
            batch_size=25,
            flush_interval=3.0,
            enable_console=False,  # Use standard logger for console
            enable_file=True,
            enable_batch_processor=True,
        )

        self.async_logger = AsyncLogger(config)
        await self.async_logger.start()
        self.logger.info("Async logging system started")

    async def _stop_async_logging(self) -> None:
        """Stop the async logging system."""
        if self.async_logger:
            await self.async_logger.stop()
            self.async_logger = None
            self.logger.info("Async logging system stopped")

    def _async_log(self, level: LogLevel, message: str, **kwargs) -> None:
        """Log message to async logger (safe for sync contexts)."""
        if self.async_logger:
            self.async_logger.log(level, message, **kwargs)
        else:
            # Fallback to standard logger
            self.logger.log(level.level_value, message)

    async def start_async_monitoring(self) -> bool:
        """Start monitoring with async logging enabled."""
        try:
            await self._start_async_logging()
            result = self.start_monitoring()
            if result:
                self._async_log(
                    LogLevel.INFO,
                    "Claude monitor started with async logging",
                    session=self.session_name,
                )
            return result
        except Exception:
            self.logger.exception("Failed to start async monitoring: {e}")
            return False

    async def stop_async_monitoring(self) -> bool:
        """Stop monitoring and async logging."""
        try:
            result = self.stop_monitoring()
            await self._stop_async_logging()
            return result
        except Exception:
            self.logger.exception("Failed to stop async monitoring: {e}")
            return False

    def get_async_logging_stats(self) -> dict:
        """Get async logging statistics."""
        if self.async_logger:
            return self.async_logger.get_statistics()
        return {"error": "Async logging not enabled"}

    async def flush_async_logs(self) -> None:
        """Force flush all pending async logs."""
        if self.async_logger:
            await self.async_logger.flush()

    @staticmethod
    def _detect_trust_prompt( content: str) -> bool:
        """Detect trust prompt in content (legacy compatibility method)."""
        # Check if content contains trust-related prompts
        trust_keywords = ["trust", "certificate", "security", "authenticate", "verify"]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in trust_keywords)

    @staticmethod
    def _auto_trust_if_needed() -> bool:
        """Auto-respond to trust prompts if detected (legacy compatibility method)."""
        # For safety, this method returns False by default
        # Individual implementations should override based on security requirements
        return False
