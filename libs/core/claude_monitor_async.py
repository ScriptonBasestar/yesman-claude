#!/usr/bin/env python3

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Async-first Claude monitoring system integrated with AsyncEventBus.

This module provides a high-performance, event-driven Claude monitoring system
that replaces the thread-based approach with native async operations. It integrates
seamlessly with the AsyncEventBus for decoupled, reactive system communication.

Key Improvements:
- Native async operation without separate threads
- Event-driven architecture integration
- Non-blocking I/O operations
- Performance monitoring and metrics
- Graceful error handling and recovery
"""

import asyncio
import logging
import time
from typing import Any, cast

from libs.ai.adaptive_response import AdaptiveConfig, AdaptiveResponse
from libs.automation.automation_manager import AutomationManager
from libs.dashboard.health_calculator import HealthCalculator
from libs.logging.async_logger import AsyncLogger, AsyncLoggerConfig, LogLevel

from .async_event_bus import AsyncEventBus, Event, EventPriority, EventType, get_event_bus
from .content_collector import ClaudeContentCollector
from .prompt_detector import ClaudePromptDetector, PromptInfo, PromptType


class AsyncClaudeMonitor:
    """High-performance async Claude monitoring system.

    This class provides event-driven Claude monitoring with non-blocking operations,
    integrated performance metrics, and seamless AsyncEventBus communication.
    """

    def __init__(
        self,
        session_manager: object,
        process_controller: object,
        status_manager: object,
        event_bus: AsyncEventBus | None = None,
    ) -> None:
        """Initialize the AsyncClaudeMonitor.

        Args:
            session_manager: Session management interface
            process_controller: Process control interface
            status_manager: Status management interface
            event_bus: Optional event bus instance (uses global if None)
        """
        self.session_manager = session_manager
        self.process_controller = process_controller
        self.status_manager = status_manager
        self.session_name = getattr(session_manager, "session_name", "unknown")

        # Event-driven architecture
        self.event_bus = event_bus or get_event_bus()

        # Monitoring state
        self.is_running = False
        self._monitor_task: asyncio.Task | None = None
        self._cleanup_task: asyncio.Task | None = None

        # Performance monitoring
        self._loop_count = 0
        self._start_time = 0.0
        self._last_performance_report = 0.0
        self._performance_interval = 60.0  # Report performance every 60 seconds

        # Auto-response settings (backward compatibility)
        self.is_auto_next_enabled = True
        self.yn_mode = "Auto"
        self.yn_response = "y"
        self.mode12 = "Auto"
        self.mode12_response = "1"
        self.mode123 = "Auto"
        self.mode123_response = "1"

        # Prompt detection and content analysis
        self.prompt_detector = ClaudePromptDetector()
        self.content_collector = ClaudeContentCollector(self.session_name)
        self.current_prompt: PromptInfo | None = None
        self.waiting_for_input = False
        self._last_content = ""

        # AI-powered adaptive response system
        self.adaptive_response = AdaptiveResponse(
            config=AdaptiveConfig(
                min_confidence_threshold=0.7,
                learning_enabled=True,
                auto_response_enabled=True,
                response_delay_ms=1500,
            ),
        )

        # Context-aware automation system
        self.automation_manager = AutomationManager(project_path=None)

        # Project health monitoring system
        self.health_calculator = HealthCalculator(project_path=None)

        # High-performance async logging system
        self.async_logger: AsyncLogger | None = None

        # Logger setup
        self.logger = logging.getLogger(f"yesman.async_claude_monitor.{self.session_name}")

        # Event subscriptions
        self._setup_event_subscriptions()

    def _setup_event_subscriptions(self) -> None:
        """Set up event bus subscriptions for system events."""
        self.event_bus.subscribe(EventType.SYSTEM_SHUTDOWN, self._handle_system_shutdown)

    async def _handle_system_shutdown(self, event: Event) -> None:
        """Handle system shutdown events gracefully."""
        self.logger.info("Received system shutdown event, stopping monitor")
        await self.stop_monitoring_async()

    # Core monitoring methods
    async def start_monitoring_async(self) -> bool:
        """Start the async monitoring loop.

        Returns:
            True if monitoring started successfully, False otherwise
        """
        if not cast("Any", self.session_manager).get_claude_pane():
            await self._publish_status_event("error", "Cannot start: No Claude pane in session")
            return False

        if self.is_running:
            await self._publish_status_event("warning", "Monitor already running")
            return False

        try:
            self.is_running = True
            self._start_time = time.time()
            self._loop_count = 0

            await self._start_async_logging()

            # Start the main monitoring task
            self._monitor_task = asyncio.create_task(self._monitor_loop_async())

            # Start cleanup task for maintenance
            self._cleanup_task = asyncio.create_task(self._maintenance_loop())

            await self._publish_status_event("success", f"Started async Claude monitor for {self.session_name}")

            # Publish monitoring started event
            await self.event_bus.publish(
                Event(
                    type=EventType.SESSION_STARTED,
                    data={"session_name": self.session_name, "monitor_type": "async_claude_monitor", "auto_next_enabled": self.is_auto_next_enabled},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.HIGH,
                )
            )

            return True

        except Exception as e:
            self.is_running = False
            await self._publish_status_event("error", f"Failed to start Claude monitor: {e}")
            self.logger.error("Failed to start Claude monitor: %s", e, exc_info=True)
            return False

    async def stop_monitoring_async(self) -> bool:
        """Stop the async monitoring loop gracefully.

        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        if not self.is_running:
            await self._publish_status_event("warning", "Claude monitor not running")
            return False

        self.logger.info("Stopping async Claude monitor...")
        self.is_running = False

        # Cancel monitoring tasks
        tasks_to_cancel = []
        if self._monitor_task and not self._monitor_task.done():
            tasks_to_cancel.append(self._monitor_task)
        if self._cleanup_task and not self._cleanup_task.done():
            tasks_to_cancel.append(self._cleanup_task)

        if tasks_to_cancel:
            # Cancel tasks gracefully
            for task in tasks_to_cancel:
                task.cancel()

            # Wait for cancellation with timeout
            try:
                await asyncio.wait_for(asyncio.gather(*tasks_to_cancel, return_exceptions=True), timeout=5.0)
            except TimeoutError:
                self.logger.warning("Monitor tasks cancellation timed out")

        # Stop async logging
        await self._stop_async_logging()

        # Publish monitoring stopped event
        await self.event_bus.publish(
            Event(
                type=EventType.SESSION_STOPPED,
                data={"session_name": self.session_name, "monitor_type": "async_claude_monitor", "uptime_seconds": time.time() - self._start_time, "total_loops": self._loop_count},
                timestamp=time.time(),
                source="async_claude_monitor",
                correlation_id=self.session_name,
                priority=EventPriority.HIGH,
            )
        )

        await self._publish_status_event("info", f"Stopped async Claude monitor for {self.session_name}")
        return True

    async def _monitor_loop_async(self) -> None:
        """Main async monitoring loop - non-blocking and event-driven.

        This is the core performance-critical method that replaces the
        thread-based monitoring with pure async operations.
        """
        if not cast("Any", self.session_manager).get_claude_pane():
            self.logger.error("Cannot start monitoring: no Claude pane for %s", self.session_name)
            self.is_running = False
            return

        self.logger.info("Starting async monitoring loop for %s", self.session_name)

        try:
            while self.is_running:
                loop_start = time.perf_counter()

                try:
                    # Async content capture (non-blocking)
                    content = await self._capture_pane_content_async()

                    # Check Claude process status asynchronously
                    claude_running = await self._check_claude_status_async()

                    if not claude_running:
                        await self._handle_claude_not_running()
                        continue

                    # Process content for prompts and automation
                    await self._process_content_async(content)

                    # Update performance metrics
                    self._loop_count += 1

                    # Report performance metrics periodically
                    if time.time() - self._last_performance_report > self._performance_interval:
                        await self._report_performance_metrics()
                        self._last_performance_report = time.time()

                except asyncio.CancelledError:
                    self.logger.info("Monitor loop cancelled")
                    break
                except Exception as e:
                    self.logger.error("Error in monitoring loop: %s", e, exc_info=True)

                    # Publish error event
                    await self.event_bus.publish(
                        Event(
                            type=EventType.CLAUDE_ERROR,
                            data={"session_name": self.session_name, "error": str(e), "error_type": type(e).__name__},
                            timestamp=time.time(),
                            source="async_claude_monitor",
                            correlation_id=self.session_name,
                            priority=EventPriority.HIGH,
                        )
                    )

                    # Wait longer on errors to prevent tight error loops
                    await asyncio.sleep(5.0)
                    continue

                # Optimal sleep duration - non-blocking
                loop_duration = time.perf_counter() - loop_start
                optimal_sleep = max(0.1, 1.0 - loop_duration)  # Aim for ~1 second intervals
                await asyncio.sleep(optimal_sleep)

        except asyncio.CancelledError:
            self.logger.info("Async monitoring loop cancelled")
        except Exception as e:
            self.logger.error("Critical error in monitoring loop: %s", e, exc_info=True)
        finally:
            self.is_running = False
            self.logger.info("Async monitoring loop stopped")

    async def _capture_pane_content_async(self) -> str:
        """Capture pane content asynchronously.

        Returns:
            Current pane content as string
        """
        try:
            # Run the potentially blocking pane capture in a thread pool
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, cast("Any", self.session_manager).capture_pane_content)
            return cast(str, content)
        except Exception as e:
            self.logger.exception("Error capturing pane content")
            return ""

    async def _check_claude_status_async(self) -> bool:
        """Check Claude process status asynchronously.

        Returns:
            True if Claude is running, False otherwise
        """
        try:
            # Run potentially blocking process check in thread pool
            loop = asyncio.get_event_loop()
            is_running = await loop.run_in_executor(None, cast("Any", self.process_controller).is_claude_running)
            return cast(bool, is_running)
        except Exception as e:
            self.logger.exception("Error checking Claude status")
            return False

    async def _handle_claude_not_running(self) -> None:
        """Handle the case when Claude is not running."""
        if self.is_auto_next_enabled:
            self.logger.info("Claude not running, attempting auto-restart")

            await self._publish_activity_event("🔄 Auto-restarting Claude...")

            try:
                # Run restart in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, cast("Any", self.process_controller).restart_claude_pane)

                # Publish restart event
                await self.event_bus.publish(
                    Event(
                        type=EventType.CLAUDE_STATUS_CHANGED,
                        data={"session_name": self.session_name, "status": "restarted", "auto_restart": True},
                        timestamp=time.time(),
                        source="async_claude_monitor",
                        correlation_id=self.session_name,
                        priority=EventPriority.HIGH,
                    )
                )

            except Exception as e:
                self.logger.exception("Failed to restart Claude")
                await self.event_bus.publish(
                    Event(
                        type=EventType.CLAUDE_ERROR,
                        data={"session_name": self.session_name, "error": f"Restart failed: {e}", "auto_restart_failed": True},
                        timestamp=time.time(),
                        source="async_claude_monitor",
                        correlation_id=self.session_name,
                        priority=EventPriority.CRITICAL,
                    )
                )
        else:
            await self._publish_status_event("warning", "Claude not running. Auto-restart disabled.")

    async def _process_content_async(self, content: str) -> None:
        """Process pane content for prompts and automation opportunities.

        Args:
            content: Current pane content
        """
        # Check for prompts
        prompt_info = await self._check_for_prompt_async(content)

        if prompt_info:
            await self._handle_prompt_async(prompt_info, content)
        elif self.waiting_for_input:
            await self._publish_activity_event("⏳ Waiting for user input...")
        else:
            # Clear prompt state if no longer waiting
            self._clear_prompt_state()

        # Update AI patterns periodically
        await self.adaptive_response.update_patterns()

        # Analyze content for automation contexts (only if content changed)
        if content != self._last_content and len(content.strip()) > 0:
            await self._analyze_automation_context(content)
            await self._collect_content_interaction(content, prompt_info)
            await self._publish_activity_event("📝 Content updated")
            self._last_content = content

    async def _check_for_prompt_async(self, content: str) -> PromptInfo | None:
        """Check for prompts in content asynchronously.

        Args:
            content: Content to analyze

        Returns:
            PromptInfo if prompt detected, None otherwise
        """
        try:
            # Run prompt detection in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            prompt_info = await loop.run_in_executor(None, self.prompt_detector.detect_prompt, content)

            if prompt_info:
                self.current_prompt = prompt_info
                self.waiting_for_input = True
                self.logger.info("Prompt detected: %s - %s", prompt_info.type.value, prompt_info.question)

                # Publish prompt detection event
                await self.event_bus.publish(
                    Event(
                        type=EventType.CLAUDE_PROMPT_SENT,
                        data={
                            "session_name": self.session_name,
                            "prompt_type": prompt_info.type.value,
                            "question": prompt_info.question,
                            "options": prompt_info.options,
                            "confidence": prompt_info.confidence,
                        },
                        timestamp=time.time(),
                        source="async_claude_monitor",
                        correlation_id=self.session_name,
                        priority=EventPriority.NORMAL,
                    )
                )
            else:
                # Check if still waiting based on content patterns
                self.waiting_for_input = await loop.run_in_executor(None, self.prompt_detector.is_waiting_for_input, content)

            return cast(PromptInfo | None, prompt_info)

        except Exception as e:
            self.logger.exception("Error checking for prompts")
            return None

    async def _handle_prompt_async(self, prompt_info: PromptInfo, content: str) -> None:
        """Handle detected prompts with AI-powered and fallback responses.

        Args:
            prompt_info: Detected prompt information
            content: Current content context
        """
        if not self.is_auto_next_enabled:
            await self._publish_activity_event(f"⏳ Waiting for input: {prompt_info.type.value}")
            return

        try:
            # Try AI-powered adaptive response first
            context = f"session:{self.session_name}, type:{prompt_info.type.value}"

            should_respond, ai_response, confidence = await self.adaptive_response.should_auto_respond(
                prompt_info.question,
                context,
                self.session_name,
            )

            if should_respond:
                success = await self._send_ai_response(prompt_info, ai_response, confidence, context)
                if success:
                    return

            # Fallback to pattern-based response
            if await self._auto_respond_to_selection_async(prompt_info):
                response = self._get_legacy_response(prompt_info)
                await self._send_legacy_response(prompt_info, response, context)
                return

            # No auto-response available
            await self._publish_activity_event(f"⏳ Waiting for input: {prompt_info.type.value}")

        except Exception as e:
            self.logger.exception("Error handling prompt")
            await self._publish_activity_event(f"❌ Error handling prompt: {e}")

    async def _send_ai_response(self, prompt_info: PromptInfo, response: str, confidence: float, context: str) -> bool:
        """Send AI-generated response and handle the result."""
        try:
            success = await self.adaptive_response.send_adaptive_response(
                prompt_info.question,
                response,
                confidence,
                context,
                self.session_name,
            )

            if success:
                # Send response to Claude
                await self._send_input_async(response)

                await self._publish_activity_event(f"🤖 AI auto-responded: '{response}' (confidence: {confidence:.2f})")
                await self._record_response_async(prompt_info.type.value, response, prompt_info.question)

                # Confirm success to adaptive system
                self.adaptive_response.confirm_response_success(
                    prompt_info.question,
                    response,
                    context,
                    self.session_name,
                    True,
                )

                # Publish successful response event
                await self.event_bus.publish(
                    Event(
                        type=EventType.CLAUDE_RESPONSE,
                        data={"session_name": self.session_name, "response": response, "response_type": "ai_adaptive", "confidence": confidence, "prompt_type": prompt_info.type.value},
                        timestamp=time.time(),
                        source="async_claude_monitor",
                        correlation_id=self.session_name,
                        priority=EventPriority.NORMAL,
                    )
                )

                self._clear_prompt_state()
                return True

        except Exception as e:
            self.logger.exception("Error sending AI response")

        return False

    async def _send_legacy_response(self, prompt_info: PromptInfo, response: str, context: str) -> None:
        """Send pattern-based legacy response."""
        try:
            await self._send_input_async(response)

            await self._publish_activity_event(f"✅ Legacy auto-responded: '{response}' to {prompt_info.type.value}")
            await self._record_response_async(prompt_info.type.value, response, prompt_info.question)

            # Learn from legacy response for future AI improvements
            self.adaptive_response.learn_from_manual_response(
                prompt_info.question,
                response,
                context,
                self.session_name,
            )

            # Publish legacy response event
            await self.event_bus.publish(
                Event(
                    type=EventType.CLAUDE_RESPONSE,
                    data={"session_name": self.session_name, "response": response, "response_type": "legacy_pattern", "prompt_type": prompt_info.type.value},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.NORMAL,
                )
            )

            self._clear_prompt_state()

        except Exception as e:
            self.logger.exception("Error sending legacy response")

    async def _send_input_async(self, input_text: str) -> None:
        """Send input to Claude process asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cast("Any", self.process_controller).send_input, input_text)
        except Exception as e:
            self.logger.exception("Error sending input")
            raise

    async def _record_response_async(self, prompt_type: str, response: str, question: str) -> None:
        """Record response asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cast("Any", self.status_manager).record_response, prompt_type, response, question)
        except Exception as e:
            self.logger.exception("Error recording response")

    async def _auto_respond_to_selection_async(self, prompt_info: PromptInfo) -> bool:
        """Check if we should auto-respond to selection prompts."""
        if not self.is_auto_next_enabled:
            return False

        try:
            # Run response logic in thread pool
            loop = asyncio.get_event_loop()
            should_respond = await loop.run_in_executor(None, self._should_auto_respond, prompt_info)
            return cast(bool, should_respond)
        except Exception as e:
            self.logger.exception("Error checking auto-response")
            return False

    def _should_auto_respond(self, prompt_info: PromptInfo) -> bool:
        """Determine if we should auto-respond (runs in thread pool)."""
        try:
            return prompt_info.type in {
                PromptType.NUMBERED_SELECTION,
                PromptType.BINARY_CHOICE,
                PromptType.CONFIRMATION,
                PromptType.LOGIN_REDIRECT,
            }
        except Exception:
            return False

    async def _analyze_automation_context(self, content: str) -> None:
        """Analyze content for automation contexts."""
        try:
            loop = asyncio.get_event_loop()
            automation_contexts = await loop.run_in_executor(None, self.automation_manager.analyze_content_for_context, content, self.session_name)

            for auto_context in automation_contexts:
                if hasattr(auto_context, "context_type") and hasattr(auto_context, "confidence"):
                    self.logger.info(
                        "Automation context detected: %s (confidence: %.2f)",
                        auto_context.context_type.value,
                        auto_context.confidence,
                    )

                    # Publish automation context event
                    await self.event_bus.publish(
                        Event(
                            type=EventType.CUSTOM,
                            data={
                                "event_subtype": "automation_context_detected",
                                "session_name": self.session_name,
                                "context_type": auto_context.context_type.value,
                                "confidence": auto_context.confidence,
                            },
                            timestamp=time.time(),
                            source="async_claude_monitor",
                            correlation_id=self.session_name,
                            priority=EventPriority.LOW,
                        )
                    )

        except Exception as e:
            self.logger.exception("Error analyzing automation context")

    async def _collect_content_interaction(self, content: str, prompt_info: PromptInfo | None) -> None:
        """Collect content interaction for pattern analysis."""
        try:
            # Convert PromptInfo to dict for compatibility
            prompt_dict = None
            if prompt_info:
                prompt_dict = {
                    "type": prompt_info.type.value,
                    "question": prompt_info.question,
                    "options": prompt_info.options,
                    "confidence": prompt_info.confidence,
                }

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.content_collector.collect_interaction, content, prompt_dict, None)
        except Exception as e:
            self.logger.exception("Error collecting content interaction")

    async def _maintenance_loop(self) -> None:
        """Background maintenance loop for cleanup and optimization."""
        maintenance_interval = 300.0  # 5 minutes

        try:
            while self.is_running:
                await asyncio.sleep(maintenance_interval)

                if not self.is_running:
                    break

                try:
                    # Cleanup old collections
                    loop = asyncio.get_event_loop()
                    cleaned_count = await loop.run_in_executor(
                        None,
                        self.content_collector.cleanup_old_files,
                        7,  # Keep 7 days
                    )

                    if cleaned_count > 0:
                        self.logger.info("Cleaned up %d old collection files", cleaned_count)

                    # Check Claude idle automation
                    if hasattr(self.status_manager, "last_activity_time"):
                        idle_context = await loop.run_in_executor(
                            None,
                            self.automation_manager.analyze_claude_idle,
                            cast("Any", self.status_manager).last_activity_time,
                            60,  # 60 second idle threshold
                        )

                        if idle_context and hasattr(idle_context, "confidence"):
                            self.logger.debug("Claude idle context: %.2f", idle_context.confidence)

                except Exception as e:
                    self.logger.exception("Error in maintenance loop")

        except asyncio.CancelledError:
            self.logger.info("Maintenance loop cancelled")

    async def _report_performance_metrics(self) -> None:
        """Report performance metrics to the event bus."""
        try:
            uptime = time.time() - self._start_time
            loops_per_second = self._loop_count / uptime if uptime > 0 else 0

            metrics = {
                "session_name": self.session_name,
                "uptime_seconds": uptime,
                "total_loops": self._loop_count,
                "loops_per_second": loops_per_second,
                "is_running": self.is_running,
                "auto_next_enabled": self.is_auto_next_enabled,
                "waiting_for_input": self.waiting_for_input,
                "current_prompt_type": self.current_prompt.type.value if self.current_prompt else None,
            }

            await self.event_bus.publish(
                Event(
                    type=EventType.PERFORMANCE_METRICS,
                    data={"component": "async_claude_monitor", "metrics": metrics},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.LOW,
                )
            )

            self.logger.debug("Performance: %.2f loops/sec, %d total loops", loops_per_second, self._loop_count)

        except Exception as e:
            self.logger.exception("Error reporting performance metrics")

    # Event publishing helpers
    async def _publish_status_event(self, status_type: str, message: str) -> None:
        """Publish status update event."""
        try:
            await self.event_bus.publish(
                Event(
                    type=EventType.DASHBOARD_UPDATE,
                    data={"update_type": "status", "status_type": status_type, "message": message, "session_name": self.session_name},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.NORMAL,
                )
            )

            # Also update status manager for backward compatibility
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cast("Any", self.status_manager).update_status, f"[{status_type}]{message}[/]")
        except Exception as e:
            self.logger.exception("Error publishing status event")

    async def _publish_activity_event(self, message: str) -> None:
        """Publish activity update event."""
        try:
            await self.event_bus.publish(
                Event(
                    type=EventType.DASHBOARD_UPDATE,
                    data={"update_type": "activity", "message": message, "session_name": self.session_name},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.LOW,
                )
            )

            # Also update status manager for backward compatibility
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cast("Any", self.status_manager).update_activity, message)
        except Exception as e:
            self.logger.exception("Error publishing activity event")

    # Utility methods (maintaining backward compatibility)
    def _clear_prompt_state(self) -> None:
        """Clear the current prompt state."""
        self.current_prompt = None
        self.waiting_for_input = False

    def _get_legacy_response(self, prompt_info: PromptInfo) -> str:
        """Get response that would be used by legacy auto-response system."""
        try:
            if prompt_info.type == PromptType.NUMBERED_SELECTION:
                opts_count = cast("dict[str, Any]", prompt_info.metadata).get("option_count", len(prompt_info.options))
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

        except Exception as e:
            self.logger.exception("Error getting legacy response")

        return "1"  # Safe fallback

    # Async logging methods
    async def _start_async_logging(self) -> None:
        """Start the async logging system."""
        if self.async_logger:
            return

        try:
            config = AsyncLoggerConfig(
                name=f"yesman.async_claude_monitor.{self.session_name}",
                level=LogLevel.INFO,
                max_queue_size=5000,
                batch_size=25,
                flush_interval=3.0,
                enable_console=False,
                enable_file=True,
                enable_batch_processor=True,
            )

            self.async_logger = AsyncLogger(config)
            await self.async_logger.start()
            self.logger.info("Async logging system started")
        except Exception as e:
            self.logger.exception("Failed to start async logging")

    async def _stop_async_logging(self) -> None:
        """Stop the async logging system."""
        if self.async_logger:
            try:
                await self.async_logger.stop()
                self.async_logger = None
                self.logger.info("Async logging system stopped")
            except Exception as e:
                self.logger.exception("Error stopping async logging")

    # Public interface methods (backward compatibility)
    def set_auto_next(self, enabled: bool) -> None:
        """Enable or disable auto-next responses."""
        self.is_auto_next_enabled = enabled
        status = "enabled" if enabled else "disabled"
        cast("Any", self.status_manager).update_status(f"[cyan]Auto next {status}[/]")

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

    def is_waiting_for_input(self) -> bool:
        """Check if Claude is currently waiting for user input."""
        return self.waiting_for_input

    def get_current_prompt(self) -> PromptInfo | None:
        """Get the current prompt information."""
        return self.current_prompt

    def get_collection_stats(self) -> dict[str, Any]:
        """Get content collection statistics."""
        return cast("dict[str, Any]", self.content_collector.get_collection_stats())

    # Legacy compatibility methods (delegate to original ClaudeMonitor for non-async operations)
    def start_monitoring(self) -> bool:
        """Legacy sync method - creates async task."""
        if self.is_running:
            return True

        # Create async task to run the monitoring
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a task
                asyncio.create_task(self.start_monitoring_async())
                return True
            else:
                # If not in async context, run until complete
                return loop.run_until_complete(self.start_monitoring_async())
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self.start_monitoring_async())

    def stop_monitoring(self) -> bool:
        """Legacy sync method - stops async monitoring."""
        if not self.is_running:
            return True

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a task
                asyncio.create_task(self.stop_monitoring_async())
                return True
            else:
                # If not in async context, run until complete
                return loop.run_until_complete(self.stop_monitoring_async())
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self.stop_monitoring_async())


# Factory function for creating monitors based on async capability
def create_claude_monitor(
    session_manager: object,
    process_controller: object,
    status_manager: object,
    prefer_async: bool = True,
    event_bus: AsyncEventBus | None = None,
) -> Any:
    """Factory function to create appropriate Claude monitor.

    Args:
        session_manager: Session management interface
        process_controller: Process control interface
        status_manager: Status management interface
        prefer_async: Whether to prefer async implementation
        event_bus: Optional event bus instance

    Returns:
        AsyncClaudeMonitor if prefer_async=True, else legacy ClaudeMonitor
    """
    if prefer_async:
        return AsyncClaudeMonitor(session_manager=session_manager, process_controller=process_controller, status_manager=status_manager, event_bus=event_bus)
    else:
        # Import and return legacy monitor for backward compatibility
        from .claude_monitor import ClaudeMonitor

        return ClaudeMonitor(session_manager=session_manager, process_controller=process_controller, status_manager=status_manager)
