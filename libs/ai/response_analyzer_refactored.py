# Copyright notice.

import json
import logging
import math
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from libs.core.mixins import StatisticsProviderMixin

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Response pattern analysis and learning engine - Refactored version."""


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


class ResponseAnalyzer(StatisticsProviderMixin):
    """Analyzes user response patterns and learns optimal responses."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or Path.home() / ".scripton" / "yesman" / "ai_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.responses_file = self.data_dir / "response_history.json"
        self.patterns_file = self.data_dir / "learned_patterns.json"

        # Load existing data
        self.response_history: list[ResponseRecord] = self._load_responses()
        self.learned_patterns: dict[str, PromptPattern] = self._load_patterns()

        # Analysis cache
        self._pattern_cache: dict[str, tuple[str, float, float]] = (
            {}
        )  # prompt -> (response, confidence, timestamp)
        self._cache_expiry = 3600  # 1 hour

        # Statistics tracking
        self._stats = {
            "total_responses": 0,
            "patterns_learned": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "predictions_made": 0,
            "prediction_accuracy": 0.0,
        }

    def get_statistics(self) -> dict[str, object]:
        """Get statistics about learned patterns and responses - implements StatisticsProviderMixin interface.

        Returns:
        Dict containing the requested data.
        """
        total_responses = len(self.response_history)

        # Response type distribution
        type_counts = Counter(record.prompt_type for record in self.response_history)

        # Project distribution
        project_counts = Counter(
            record.project_name or "global" for record in self.response_history
        )

        # Recent activity (last 7 days)
        recent_cutoff = time.time() - (7 * 24 * 3600)
        recent_responses = [
            r for r in self.response_history if r.timestamp > recent_cutoff
        ]

        # Cache statistics
        cache_size = len(self._pattern_cache)
        valid_cache_entries = sum(
            1
            for _, (_, _, timestamp) in self._pattern_cache.items()
            if time.time() - timestamp < self._cache_expiry
        )

        return {
            "total_responses": total_responses,
            "unique_patterns": len(self.learned_patterns),
            "response_types": dict(type_counts),
            "project_distribution": dict(project_counts),
            "recent_responses_7d": len(recent_responses),
            "cache_size": cache_size,
            "valid_cache_entries": valid_cache_entries,
            "cache_hit_rate": (
                self._stats["cache_hits"]
                / (self._stats["cache_hits"] + self._stats["cache_misses"])
                * 100
                if (self._stats["cache_hits"] + self._stats["cache_misses"]) > 0
                else 0.0
            ),
            **self._stats,
        }

    def _load_responses(self) -> list[ResponseRecord]:
        """Load response history from file.

        Returns:
        List of.
        """
        if not self.responses_file.exists():
            return []

        try:
            with open(self.responses_file, encoding="utf-8") as f:
                data = json.load(f)
                return [ResponseRecord(**item) for item in data]
        except Exception:
            logger.exception("Failed to load response history")  # noqa: G004
            return []

    def _load_patterns(self) -> dict[str, PromptPattern]:
        """Load learned patterns from file.

        Returns:
        Dict containing.
        """
        if not self.patterns_file.exists():
            return {}

        try:
            with open(self.patterns_file, encoding="utf-8") as f:
                data = json.load(f)
                return {k: PromptPattern(**v) for k, v in data.items()}
        except Exception:
            logger.exception("Failed to load patterns")  # noqa: G004
            return {}

    def save_data(self) -> None:
        """Save responses and patterns to disk."""
        try:
            # Save response history
            with open(self.responses_file, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in self.response_history], f, indent=2)

            # Save learned patterns
            with open(self.patterns_file, "w", encoding="utf-8") as f:
                json.dump(
                    {k: asdict(v) for k, v in self.learned_patterns.items()},
                    f,
                    indent=2,
                )

        except Exception:
            logger.exception("Failed to save data")  # noqa: G004

    def record_response(
        self,
        prompt_text: str,
        user_response: str,
        prompt_type: str,
        context: str = "",
        project_name: str | None = None,
    ) -> None:
        """Record a user response for learning."""
        record = ResponseRecord(
            timestamp=time.time(),
            prompt_text=prompt_text,
            prompt_type=prompt_type,
            user_response=user_response,
            context=context,
            project_name=project_name,
        )

        self.response_history.append(record)
        self._stats["total_responses"] += 1

        # Learn from this response
        self._learn_from_response(record)

        # Save periodically (every 10 responses)
        if len(self.response_history) % 10 == 0:
            self.save_data()

    def _learn_from_response(self, record: ResponseRecord) -> None:
        """Learn patterns from a response record."""
        pattern_id = f"{record.prompt_type}_{hash(record.prompt_text) % 10000}"

        if pattern_id in self.learned_patterns:
            # Update existing pattern
            pattern = self.learned_patterns[pattern_id]
            pattern.common_responses[record.user_response] = (
                pattern.common_responses.get(record.user_response, 0) + 1
            )
            pattern.last_updated = time.time()
        else:
            # Create new pattern
            pattern = PromptPattern(
                pattern_id=pattern_id,
                prompt_type=record.prompt_type,
                regex_pattern=self._generate_regex_pattern(record.prompt_text),
                confidence_threshold=0.7,
                common_responses={record.user_response: 1},
                context_factors={},
                last_updated=time.time(),
            )
            self.learned_patterns[pattern_id] = pattern
            self._stats["patterns_learned"] += 1

    @staticmethod
    def _generate_regex_pattern(prompt_text: str) -> str:
        """Generate a regex pattern from prompt text.

        Returns:
        String containing.
        """
        # Escape special regex characters
        escaped = re.escape(prompt_text)

        # Replace common variable parts with regex patterns
        patterns = [
            (r"\\\d+", r"\\d+"),  # Numbers
            (r"'[^']*'", r"'[^']*'"),  # Quoted strings
            (r'"[^"]*"', r'"[^"]*"'),  # Double quoted strings
            (r"\b[A-Z][a-z]+\b", r"\\b[A-Z][a-z]+\\b"),  # Capitalized words (names)
        ]

        result = escaped
        for old, new in patterns:
            result = re.sub(old, new, result)

        return result

    def predict_response(
        self,
        prompt_text: str,
        prompt_type: str,
        context: str = "",  # noqa: ARG002
        project_name: str | None = None,
    ) -> tuple[str | None, float]:
        """Predict the likely user response based on learned patterns.

        Returns:
        Tuple[Str | None, Float] object.
        """
        # Check cache first
        cache_key = f"{prompt_type}:{prompt_text}:{project_name}"
        if cache_key in self._pattern_cache:
            cached_data = self._pattern_cache[cache_key]
            if len(cached_data) == 3:
                response, confidence, timestamp = cached_data
                if time.time() - timestamp < self._cache_expiry:
                    self._stats["cache_hits"] += 1
                    return response, confidence
        else:
            self._stats["cache_misses"] += 1

        # Find matching patterns
        best_match = None
        best_confidence = 0.0

        for pattern in self.learned_patterns.values():
            if pattern.prompt_type != prompt_type:
                continue

            # Check if prompt matches pattern
            if re.match(pattern.regex_pattern, prompt_text):
                # Calculate confidence based on response frequency
                total_responses = sum(pattern.common_responses.values())
                if total_responses > 0:
                    most_common = max(
                        pattern.common_responses.items(), key=lambda x: x[1]
                    )
                    confidence = most_common[1] / total_responses

                    # Adjust confidence based on recency
                    age_factor = max(
                        0.5,
                        1.0 - (time.time() - pattern.last_updated) / (30 * 24 * 3600),
                    )
                    confidence *= age_factor

                    if confidence > best_confidence:
                        best_match = most_common[0]
                        best_confidence = confidence

        # Cache the result
        if best_match:
            # Store as tuple[str, float, float] in cache but return only tuple[str, float]
            self._pattern_cache[cache_key] = (best_match, best_confidence, time.time())
            self._stats["predictions_made"] += 1

        return best_match, best_confidence

    @staticmethod
    def get_default_response(prompt_type: str) -> tuple[str, float]:
        """Get default response for a prompt type when no pattern matches.

        Returns:
        Tuple[Str, Float] object the requested data.
        """
        defaults = {
            "yes_no": ("y", 0.8),
            "numbered_selection": ("1", 0.6),
            "confirmation": ("yes", 0.7),
            "continue": ("", 0.9),  # Just press enter
            "file_path": ("", 0.1),  # Don't guess file paths
        }

        return defaults.get(prompt_type, ("", 0.1))

    def analyze_response_patterns(
        self, project_name: str | None = None
    ) -> dict[str, object]:
        """Analyze response patterns for insights.

        Returns:
        Dict containing.
        """
        # Filter by project if specified
        records = self.response_history
        if project_name:
            records = [r for r in records if r.project_name == project_name]

        if not records:
            return {"error": "No records found"}

        # Analyze patterns
        type_responses: dict[str, Counter[str]] = {}
        for record in records:
            if record.prompt_type not in type_responses:
                type_responses[record.prompt_type] = Counter()
            type_responses[record.prompt_type][record.user_response] += 1

        # Calculate insights
        insights = {}
        for prompt_type, responses in type_responses.items():
            total = sum(responses.values())
            most_common = responses.most_common(3)

            insights[prompt_type] = {
                "total_responses": total,
                "most_common": [
                    (resp, count / total * 100) for resp, count in most_common
                ],
                "unique_responses": len(responses),
                "entropy": self._calculate_entropy(responses),
            }

        return cast(dict[str, object], insights)

    @staticmethod
    def _calculate_entropy(counter: Counter) -> float:
        """Calculate Shannon entropy for response distribution.

        Returns:
        Float representing.
        """
        total = sum(counter.values())
        if total == 0:
            return 0.0

        entropy = 0.0
        for count in counter.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        return entropy

    def cleanup_old_data(self, days_to_keep: int = 90) -> object:
        """Remove old response records.

        Returns:
        Object object.
        """
        cutoff = time.time() - (days_to_keep * 24 * 3600)
        original_count = len(self.response_history)

        self.response_history = [
            r for r in self.response_history if r.timestamp > cutoff
        ]

        removed = original_count - len(self.response_history)
        if removed > 0:
            logger.info(f"Cleaned up {removed} old response records")  # noqa: G004
            self.save_data()

        return removed
