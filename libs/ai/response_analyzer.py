"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Response pattern analysis and learning engine."""

import json
import logging
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ResponseRecord:
    """A record of a user response to a prompt."""

    timestamp: float
    prompt_text: str
    prompt_type: str  # 'numbered_selection', 'yes_no', 'confirmation', etc.
    user_response: str
    context: str  # Additional context about the situation
    project_name: str | None = None
    confidence_score: float = 1.0  # How confident we are in this response


@dataclass
class PromptPattern:
    """A learned pattern for a specific type of prompt."""

    pattern_id: str
    prompt_type: str
    regex_pattern: str
    confidence_threshold: float
    common_responses: dict[str, int]  # response -> frequency
    context_factors: dict[str, float]  # context -> weight
    last_updated: float


class ResponseAnalyzer:
    """Analyzes user response patterns and learns optimal responses."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or Path.home() / ".scripton" / "yesman" / "ai_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.responses_file = self.data_dir / "response_history.json"
        self.patterns_file = self.data_dir / "learned_patterns.json"

        self.response_history: list[ResponseRecord] = []
        self.learned_patterns: dict[str, PromptPattern] = {}

        self._load_data()

    def _load_data(self) -> None:
        """Load existing response history and patterns."""
        try:
            if self.responses_file.exists():
                with open(self.responses_file) as f:
                    data = json.load(f)
                    self.response_history = [ResponseRecord(**record) for record in data]
                logger.info("Loaded %d response records", len(self.response_history))

            if self.patterns_file.exists():
                with open(self.patterns_file) as f:
                    data = json.load(f)
                    self.learned_patterns = {pid: PromptPattern(**pattern) for pid, pattern in data.items()}
                logger.info("Loaded %d learned patterns", len(self.learned_patterns))

        except Exception:
            logger.exception("Error loading AI data")

    def _save_data(self) -> None:
        """Save response history and patterns to disk."""
        try:
            # Save response history
            with open(self.responses_file, "w") as f:
                json.dump([asdict(record) for record in self.response_history], f, indent=2)

            # Save patterns
            with open(self.patterns_file, "w") as f:
                json.dump(
                    {pid: asdict(pattern) for pid, pattern in self.learned_patterns.items()},
                    f,
                    indent=2,
                )

        except Exception:
            logger.exception("Error saving AI data")

    def record_response(
        self,
        prompt_text: str,
        user_response: str,
        context: str = "",
        project_name: str | None = None,
    ) -> None:
        """Record a user response for learning."""
        prompt_type = self._classify_prompt_type(prompt_text)

        record = ResponseRecord(
            timestamp=time.time(),
            prompt_text=prompt_text,
            prompt_type=prompt_type,
            user_response=user_response,
            context=context,
            project_name=project_name,
        )

        self.response_history.append(record)

        # Update patterns
        self._update_patterns(record)

        # Save periodically
        if len(self.response_history) % 10 == 0:
            self._save_data()

        logger.debug("Recorded response: %s -> %s", prompt_type, user_response)

    @staticmethod
    def _classify_prompt_type( prompt_text: str) -> str:
        """Classify the type of prompt based on its content."""
        text = prompt_text.lower().strip()

        # Common prompt patterns
        if re.search(r"\b(yes|no)\b.*\?", text):
            return "yes_no"
        if re.search(r"\b[1-9]\d*\)", text) or re.search(r"select.*[1-9]", text):
            return "numbered_selection"
        if "overwrite" in text or "replace" in text:
            return "overwrite_confirmation"
        if "continue" in text or "proceed" in text:
            return "proceed_confirmation"
        if "trust" in text and "code" in text:
            return "trust_confirmation"
        if re.search(r"choose|select|pick", text):
            return "choice_selection"
        return "unknown"

    def _update_patterns(self, record: ResponseRecord) -> None:
        """Update learned patterns based on new response record."""
        pattern_id = f"{record.prompt_type}_{record.project_name or 'global'}"

        if pattern_id not in self.learned_patterns:
            # Create new pattern
            self.learned_patterns[pattern_id] = PromptPattern(
                pattern_id=pattern_id,
                prompt_type=record.prompt_type,
                regex_pattern=self._generate_regex_pattern(record.prompt_text),
                confidence_threshold=0.7,
                common_responses={},
                context_factors={},
                last_updated=time.time(),
            )

        pattern = self.learned_patterns[pattern_id]

        # Update response frequencies
        if record.user_response not in pattern.common_responses:
            pattern.common_responses[record.user_response] = 0
        pattern.common_responses[record.user_response] += 1

        # Update context factors
        if record.context:
            context_key = self._extract_context_key(record.context)
            if context_key not in pattern.context_factors:
                pattern.context_factors[context_key] = 0.5
            # Adjust factor based on response success (simplified)
            pattern.context_factors[context_key] = min(1.0, pattern.context_factors[context_key] + 0.1)

        pattern.last_updated = time.time()

    @staticmethod
    def _generate_regex_pattern(prompt_text: str) -> str:
        """Generate a regex pattern to match similar prompts."""
        # Simplified pattern generation - replace specific words with wildcards
        pattern = re.escape(prompt_text.lower())

        # Replace numbers with number patterns
        pattern = re.sub(r"\\d+", r"\\d+", pattern)

        # Replace file names/paths with wildcards
        return re.sub(r"[a-zA-Z0-9_\-\.]+\.(py|js|ts|md|txt)", r"[\\w\-\.]+", pattern)

    @staticmethod
    def _extract_context_key(context: str) -> str:
        """Extract a key from context for pattern matching."""
        # Simplified context extraction
        context = context.lower()

        if "error" in context:
            return "error_context"
        if "test" in context:
            return "test_context"
        if "build" in context:
            return "build_context"
        if "deploy" in context:
            return "deploy_context"
        return "general_context"

    def predict_response(self, prompt_text: str, context: str = "", project_name: str | None = None) -> tuple[str, float]:
        """Predict the best response for a given prompt."""
        prompt_type = self._classify_prompt_type(prompt_text)
        pattern_id = f"{prompt_type}_{project_name or 'global'}"

        # Try project-specific pattern first
        if pattern_id in self.learned_patterns:
            pattern = self.learned_patterns[pattern_id]
        else:
            # Fall back to global pattern
            global_pattern_id = f"{prompt_type}_global"
            if global_pattern_id in self.learned_patterns:
                pattern = self.learned_patterns[global_pattern_id]
            else:
                # No learned pattern, use defaults
                return self._get_default_response(prompt_type)

        # Calculate confidence based on pattern matching and context
        confidence = self._calculate_confidence(pattern, prompt_text, context)

        if confidence < pattern.confidence_threshold:
            return self._get_default_response(prompt_type)

        # Get most common response
        if pattern.common_responses:
            best_response = max(pattern.common_responses.items(), key=lambda x: x[1])[0]
            return best_response, confidence
        return self._get_default_response(prompt_type)

    def _calculate_confidence(self, pattern: PromptPattern, prompt_text: str, context: str) -> float:
        """Calculate confidence score for a prediction."""
        base_confidence = 0.5

        # Pattern matching confidence
        try:
            if re.search(pattern.regex_pattern, prompt_text.lower()):
                base_confidence += 0.3
        except re.error:
            pass

        # Context confidence
        if context:
            context_key = self._extract_context_key(context)
            if context_key in pattern.context_factors:
                base_confidence += pattern.context_factors[context_key] * 0.2

        # Response frequency confidence
        total_responses = sum(pattern.common_responses.values())
        if total_responses > 5:  # Enough data
            base_confidence += 0.2

        return min(1.0, base_confidence)

    @staticmethod
    def _get_default_response(prompt_type: str) -> tuple[str, float]:
        """Get default response for a prompt type."""
        defaults = {
            "yes_no": ("yes", 0.3),
            "numbered_selection": ("1", 0.3),
            "overwrite_confirmation": ("yes", 0.4),
            "proceed_confirmation": ("yes", 0.4),
            "trust_confirmation": ("yes", 0.5),
            "choice_selection": ("1", 0.3),
            "unknown": ("", 0.1),
        }

        return defaults.get(prompt_type, ("", 0.1))

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about learned patterns and responses."""
        total_responses = len(self.response_history)

        # Response type distribution
        type_counts = Counter(record.prompt_type for record in self.response_history)

        # Project distribution
        project_counts = Counter(record.project_name or "global" for record in self.response_history)

        # Recent activity (last 7 days)
        week_ago = time.time() - (7 * 24 * 3600)
        recent_responses = [r for r in self.response_history if r.timestamp > week_ago]

        return {
            "total_responses": total_responses,
            "total_patterns": len(self.learned_patterns),
            "response_types": dict(type_counts),
            "project_distribution": dict(project_counts),
            "recent_activity": len(recent_responses),
            "data_directory": str(self.data_dir),
        }

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove old response records to keep data fresh."""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)

        old_count = len(self.response_history)
        self.response_history = [record for record in self.response_history if record.timestamp > cutoff_time]

        removed = old_count - len(self.response_history)
        if removed > 0:
            logger.info("Cleaned up %d old response records", removed)
            self._save_data()

        return removed
