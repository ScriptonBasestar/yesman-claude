# Copyright notice.

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

from .response_analyzer import ResponseAnalyzer

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Adaptive response system that integrates learning with auto-response."""


logger = logging.getLogger(__name__)


@dataclass
class AdaptiveConfig:
    """Configuration for adaptive response behavior."""

    min_confidence_threshold: float = 0.6
    learning_enabled: bool = True
    auto_response_enabled: bool = True
    response_delay_ms: int = 1000  # Delay before sending response
    pattern_update_interval: int = 3600  # Update patterns every hour
    max_response_history: int = 1000


class AdaptiveResponse:
    """Adaptive response system that learns from user patterns."""

    def __init__(self, config: AdaptiveConfig | None = None, data_dir: Path | None = None) -> None:
        self.config = config or AdaptiveConfig()
        self.analyzer = ResponseAnalyzer(data_dir)

        self._response_queue: list[tuple[str, str, str, str]] = []
        self._learning_cache: dict[str, object] = {}
        self._last_pattern_update = time.time()

        logger.info("Adaptive response system initialized")

    async def should_auto_respond(self, prompt_text: str, context: str = "", project_name: str | None = None) -> tuple[bool, str, float]:
        """Determine if we should auto-respond to a prompt and what the
        response should be."""
        if not self.config.auto_response_enabled:
            return False, "", 0.0

        # Get prediction from analyzer
        predicted_response, confidence = self.analyzer.predict_response(
            prompt_text,
            context,
            project_name,
        )

        # Check if confidence meets threshold
        should_respond = confidence >= self.config.min_confidence_threshold

        logger.debug("Auto-response decision: {should_respond} (confidence: {confidence:.2f}, threshold: {self.config.min_confidence_threshold:.2f})")

        if should_respond:
            logger.info("Auto-responding with: '{predicted_response}' (confidence: {confidence:.2f})")

        return should_respond, predicted_response, confidence

    async def send_adaptive_response(
        self,
        prompt_text: str,
        response: str,
        confidence: float,  # noqa: ARG002
        context: str = "",
        project_name: str | None = None,
    ) -> bool:
        """Send an adaptive response with appropriate delay and logging."""
        try:
            # Add delay to simulate human response time
            if self.config.response_delay_ms > 0:
                await asyncio.sleep(self.config.response_delay_ms / 1000.0)

            # Queue response for learning (will be confirmed later)
            self._response_queue.append((prompt_text, response, context, project_name))

            # Log the response attempt
            logger.info("Sent adaptive response: '{response}' for prompt type: {self.analyzer._classify_prompt_type(prompt_text)}")

            return True

        except Exception:
            logger.exception("Failed to send adaptive response: {e}")
            return False

    def confirm_response_success(
        self,
        prompt_text: str,
        response: str,
        context: str = "",
        project_name: str | None = None,
        success: bool = True,  # noqa: FBT001
    ) -> None:
        """Confirm whether a response was successful and record it for
        learning."""
        if not self.config.learning_enabled:
            return

        try:
            # Record the response for learning
            if success:
                self.analyzer.record_response(prompt_text, response, context, project_name)
                logger.debug("Recorded successful response: {response}")
            else:
                # For failed responses, we might want to adjust confidence
                logger.warning("Response failed: {response} for prompt: {prompt_text}")

        except Exception:
            logger.exception("Failed to record response: {e}")

    def learn_from_manual_response(
        self,
        prompt_text: str,
        user_response: str,
        context: str = "",
        project_name: str | None = None,
    ) -> None:
        """Learn from a manual user response that was not auto-generated."""
        if not self.config.learning_enabled:
            return

        try:
            # Record manual response for learning
            self.analyzer.record_response(prompt_text, user_response, context, project_name)
            logger.debug("Learned from manual response: {user_response}")

        except Exception:
            logger.exception("Failed to learn from manual response: {e}")

    async def update_patterns(self) -> None:
        """Periodically update and optimize response patterns."""
        current_time = time.time()

        if (current_time - self._last_pattern_update) < self.config.pattern_update_interval:
            return

        try:
            logger.info("Updating response patterns...")

            # Cleanup old data to keep learning fresh
            removed_count = self.analyzer.cleanup_old_data(days_to_keep=30)
            if isinstance(removed_count, int) and removed_count > 0:
                logger.info("Cleaned up {removed_count} old response records")

            # Get statistics
            stats = self.analyzer.get_statistics()
            logger.info("Pattern statistics: {stats}")

            # Update cache with new patterns
            self._learning_cache.update(
                {
                    "last_update": current_time,
                    "stats": stats,
                }
            )

            self._last_pattern_update = current_time
            logger.info("Pattern update completed")

        except Exception:
            logger.exception("Failed to update patterns: {e}")

    def get_learning_statistics(self) -> dict[str, object]:
        """Get comprehensive learning statistics.

        Returns:
        Dict containing the requested data.
        """
        try:
            base_stats = self.analyzer.get_statistics()

            # Add adaptive-specific statistics
            adaptive_stats = {
                "adaptive_config": {
                    "auto_response_enabled": self.config.auto_response_enabled,
                    "learning_enabled": self.config.learning_enabled,
                    "min_confidence_threshold": self.config.min_confidence_threshold,
                    "response_delay_ms": self.config.response_delay_ms,
                },
                "runtime_info": {
                    "response_queue_size": len(self._response_queue),
                    "last_pattern_update": self._last_pattern_update,
                    "cache_size": len(self._learning_cache),
                },
            }

            return {**base_stats, **adaptive_stats}

        except Exception:
            logger.exception("Failed to get learning statistics: {e}")
            return {}

    def get_prompt_suggestions(self, partial_prompt: str, limit: int = 5) -> list[str]:
        """Get suggestions for similar prompts based on learning history.

        Returns:
        List of the requested data.
        """
        try:
            # Simple implementation - find prompts that contain similar keywords
            suggestions = []
            keywords = partial_prompt.lower().split()

            for record in self.analyzer.response_history[-100:]:  # Last 100 records
                prompt_lower = record.prompt_text.lower()

                # Check if any keywords match
                if any(keyword in prompt_lower for keyword in keywords) and record.prompt_text not in suggestions:
                    suggestions.append(record.prompt_text)

                if len(suggestions) >= limit:
                    break

            return suggestions

        except Exception:
            logger.exception("Failed to get prompt suggestions: {e}")
            return []

    def export_learning_data(self, output_path: Path) -> bool:
        """Export learning data for analysis or backup.

        Returns:
        Boolean indicating.
        """
        try:
            export_data = {
                "config": {
                    "min_confidence_threshold": self.config.min_confidence_threshold,
                    "learning_enabled": self.config.learning_enabled,
                    "auto_response_enabled": self.config.auto_response_enabled,
                },
                "statistics": self.get_learning_statistics(),
                "export_timestamp": time.time(),
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            logger.info("Learning data exported to: {output_path}")
            return True

        except Exception:
            logger.exception("Failed to export learning data: {e}")
            return False

    def adjust_confidence_threshold(self, new_threshold: float) -> None:
        """Dynamically adjust the confidence threshold for auto-responses."""
        if 0.0 <= new_threshold <= 1.0:
            self.config.min_confidence_threshold = new_threshold
            logger.info("Confidence threshold adjusted: {old_threshold:.2f} -> {new_threshold:.2f}")
        else:
            logger.warning("Invalid confidence threshold: {new_threshold}. Must be between 0.0 and 1.0")

    def enable_auto_response(self, enabled: bool = True) -> None:  # noqa: FBT001
        """Enable or disable auto-response functionality."""
        self.config.auto_response_enabled = enabled
        logger.info("Auto-response {'enabled' if enabled else 'disabled'}")

    def enable_learning(self, enabled: bool = True) -> None:  # noqa: FBT001
        """Enable or disable learning functionality."""
        self.config.learning_enabled = enabled
        logger.info("Learning {'enabled' if enabled else 'disabled'}")
