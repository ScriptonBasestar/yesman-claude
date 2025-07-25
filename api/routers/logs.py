# Copyright notice.

import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, cast

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from libs.core.services import get_config

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


logger = logging.getLogger(__name__)


class LogEntry(BaseModel):
    level: str
    timestamp: str
    source: str
    message: str
    raw: str


router = APIRouter()


@router.get("/sessions/{session_name}/logs", response_model=list[str])
def get_session_logs(session_name: str, limit: int = 100) -> object:
    """특정 세션의 최근 로그를 조회합니다.

    Returns:
        object: Description of return value.
    """
    try:
        config = get_config()
        log_path_str = cast(str, config.get("log_path", "~/.scripton/yesman/logs/"))
        # 세션 이름에 유효하지 않은 문자가 있을 수 있으므로 정제합니다.
        safe_session_name = "".join(c for c in session_name if c.isalnum() or c in {"-", "_"}).rstrip()
        log_file = Path(log_path_str).expanduser() / f"{safe_session_name}.log"

        if not log_file.exists():
            # 컨트롤러 로그가 없을 경우, 메인 로그를 대신 반환해볼 수 있습니다.
            log_file = Path(log_path_str).expanduser() / "yesman.log"
            if not log_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Log file for session '{session_name}' not found.",
                )

        with open(log_file, encoding="utf-8") as f:
            # 큰 로그 파일을 효율적으로 읽기 위해 마지막 N줄만 읽는 것이 좋지만,
            # 여기서는 간단하게 모든 줄을 읽고 마지막 부분만 반환합니다.
            lines = f.readlines()
            return lines[-limit:]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {e!s}")


def parse_log_line(line: str) -> LogEntry | None:
    """Parse a log line into a structured LogEntry.

    Returns:
        Logentry | None object.
    """
    line = line.strip()
    if not line:
        return None

    # Try to parse structured log format: [timestamp] [level] [source] message
    log_pattern = r"^\[([^\]]+)\]\s*\[([^\]]+)\]\s*\[([^\]]+)\]\s*(.+)$"
    match = re.match(log_pattern, line)

    if match:
        timestamp_str, level, source, message = match.groups()
        return LogEntry(
            level=level.lower(),
            timestamp=timestamp_str,
            source=source,
            message=message,
            raw=line,
        )

    # Try simplified format: [timestamp] [level] message
    simple_pattern = r"^\[([^\]]+)\]\s*\[([^\]]+)\]\s*(.+)$"
    match = re.match(simple_pattern, line)

    if match:
        timestamp_str, level, message = match.groups()
        return LogEntry(
            level=level.lower(),
            timestamp=timestamp_str,
            source="yesman",
            message=message,
            raw=line,
        )

    # Fallback: treat as unstructured log
    return LogEntry(
        level="info",
        timestamp=datetime.now(UTC).isoformat(),
        source="unknown",
        message=line,
        raw=line,
    )


@router.get("/logs", response_model=list[LogEntry])
def get_logs(
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    level: Annotated[str | None, Query()] = None,
    source: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> list[LogEntry]:
    """Get parsed log entries with optional filtering.

    Returns:
        object: Description of return value.
    """
    try:
        config = get_config()
        log_path_str = cast(str, config.get("log_path", "~/.scripton/yesman/logs/"))
        log_files = [
            Path(log_path_str).expanduser() / "yesman.log",
            Path(log_path_str).expanduser() / "claude_manager.log",
            Path(log_path_str).expanduser() / "dashboard.log",
        ]

        all_logs = []

        for log_file in log_files:
            if log_file.exists():
                try:
                    with open(log_file, encoding="utf-8") as f:
                        lines = f.readlines()
                        for line in lines[-limit:]:  # Take last N lines from each file
                            log_entry = parse_log_line(line)
                            if log_entry:
                                all_logs.append(log_entry)
                except Exception as e:
                    logger.warning(f"Failed to parse log file {log_file}: {e}")  # noqa: G004
                    continue

        # Sort by timestamp (newest first)
        all_logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply filters
        filtered_logs = all_logs

        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level.lower()]

        if source:
            filtered_logs = [log for log in filtered_logs if log.source == source]

        if search:
            search_lower = search.lower()
            filtered_logs = [log for log in filtered_logs if search_lower in log.message.lower()]

        return filtered_logs[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {e!s}")


@router.get("/logs/sources")
def get_log_sources() -> object:
    """Get available log sources.

    Returns:
        object: Description of return value.
    """
    try:
        config = get_config()
        log_path_str = cast(str, config.get("log_path", "~/.scripton/yesman/logs/"))
        log_files = [
            Path(log_path_str).expanduser() / "yesman.log",
            Path(log_path_str).expanduser() / "claude_manager.log",
            Path(log_path_str).expanduser() / "dashboard.log",
        ]

        sources = set()

        for log_file in log_files:
            if log_file.exists():
                try:
                    with open(log_file, encoding="utf-8") as f:
                        # Sample first 50 lines to get sources
                        for i, line in enumerate(f):
                            if i >= 50:
                                break
                            log_entry = parse_log_line(line)
                            if log_entry:
                                sources.add(log_entry.source)
                except Exception as e:
                    logger.warning(f"Failed to parse log file {log_file}: {e}")  # noqa: G004
                    continue

        return {"sources": sorted(sources)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log sources: {e!s}")


@router.post("/logs/test")
def add_test_log(level: str = "info", source: str = "test", message: str = "Test log message") -> object:
    """Add a test log entry (for development/testing).

    Returns:
        object: Description of return value.
    """
    # This is a simple test endpoint that could write to a test log file
    # or in a real implementation, emit through the logging system

    test_log_entry = LogEntry(
        level=level.lower(),
        timestamp=datetime.now(UTC).isoformat(),
        source=source,
        message=message,
        raw=f"[{datetime.now(UTC).isoformat()}] [{level.upper()}] [{source}] {message}",
    )

    return {"status": "success", "log_entry": test_log_entry}
