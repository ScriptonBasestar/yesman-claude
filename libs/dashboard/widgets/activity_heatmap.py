# Copyright notice.

import logging
import re
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from libs.yesman_config import YesmanConfig

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


logger = logging.getLogger(__name__)


class ActivityHeatmapGenerator:
    def __init__(self, config: YesmanConfig) -> None:
        self.config = config

    def collect_session_activity(
        self, session_name: str, days: int = 7
    ) -> dict[str, int]:
        """Tmux 세션의 활동 로그 수집 및 분석.

        Returns:
        object: Description of return value.
        """
        start_time_collect = datetime.now(UTC)
        try:
            log_path_str = self.config.get("log_path", "~/.scripton/yesman/logs/")
            safe_session_name = "".join(
                c for c in session_name if c.isalnum() or c in {"-", "_"}
            ).rstrip()
            log_file = Path(str(log_path_str)).expanduser() / f"{safe_session_name}.log"

            if not log_file.exists():
                log_file = Path(str(log_path_str)).expanduser() / "yesman.log"
                if not log_file.exists():
                    logger.warning(
                        f"Log file not found for session {session_name}. Returning empty activity."
                    )  # noqa: G004
                    return {}

            activity_counts: defaultdict[str, int] = defaultdict(int)

            now = datetime.now(UTC)
            start_time_filter = now - timedelta(days=days)

            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    match = re.match(r"\[(.*?)\]", line)
                    if match:
                        timestamp_str = match.group(1).split(",")[0]
                        try:
                            log_time = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S"
                            )
                            if log_time > start_time_filter:
                                hour_timestamp = log_time.strftime("%Y-%m-%dT%H:00:00")
                                activity_counts[hour_timestamp] += 1
                        except ValueError:
                            continue
            logger.info(
                f"Collected activity for {session_name} in {(datetime.now(UTC) - start_time_collect).total_seconds():.4f} seconds."
            )  # noqa: G004
            return activity_counts
        except Exception:
            logger.exception(
                "Error collecting session activity for {session_name}"
            )  # noqa: G004
            return {}

    def generate_heatmap_data(
        self, sessions: list[str], days: int = 7
    ) -> dict[str, Any]:
        """24x7 그리드 형태의 히트맵 데이터 생성.

        Returns:
        object: Description of return value.
        """
        start_time_generate = datetime.now(UTC)
        heatmap_data: defaultdict[int, defaultdict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for session_name in sessions:
            activity = self.collect_session_activity(session_name, days)
            for timestamp, count in activity.items():
                # Assuming timestamp is in ISO format 'YYYY-MM-DDTHH:00:00'
                day_of_week = datetime.fromisoformat(
                    timestamp
                ).weekday()  # Monday is 0 and Sunday is 6
                hour = datetime.fromisoformat(timestamp).hour
                heatmap_data[day_of_week][hour] += count
        logger.info(
            f"Generated heatmap data for sessions {sessions} in {(datetime.now(UTC) - start_time_generate).total_seconds():.4f} seconds."
        )  # noqa: G004
        return {
            "heatmap": heatmap_data,
            "sessions": sessions,
            "days": days,
        }
