# Copyright notice.

import gzip
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from libs.core.base_batch_processor import BaseBatchProcessor

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Batch log processor for optimized I/O operations - Refactored version."""


@dataclass
class LogBatch:
    """A batch of log entries to be processed together."""

    entries: list[dict[str, object]]
    timestamp: float
    batch_id: str
    size_bytes: int = 0

    def __post_init__(self) -> object:
        """Calculate size after initialization.

        Returns:
        object: Description of return value.
        """
        if not self.size_bytes:
            self.size_bytes = sum(len(str(entry)) for entry in self.entries)


class BatchProcessor(BaseBatchProcessor[dict[str, object], LogBatch]):
    """Processes log entries in batches for optimized I/O."""

    def __init__(
        self,
        max_batch_size: int = 100,
        max_batch_time: float = 5.0,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        compression_enabled: bool = True,  # noqa: FBT001
        output_dir: Path | None = None,
    ) -> None:
        """Initialize the batch processor.

        Args:
            max_batch_size: Maximum number of log entries per batch
            max_batch_time: Maximum time before flushing a batch
            max_file_size: Maximum size of a single log file
            compression_enabled: Whether to enable gzip compression
            output_dir: Directory to write log files

        Returns:
        None: Description of return value.
        """
        # Initialize base class
        super().__init__(
            batch_size=max_batch_size,
            flush_interval=max_batch_time,
        )

        # Additional configuration
        self.max_file_size = max_file_size
        self.compression_enabled = compression_enabled
        self.output_dir = output_dir or Path.home() / ".scripton" / "yesman" / "logs"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # File management
        self.batch_counter = 0
        self.current_file_size = 0
        self.current_log_file: Path | None = None

        # Extended statistics
        self.extended_stats = {
            "bytes_written": 0,
            "compression_ratio": 1.0,
            "files_created": 0,
        }

        self.logger = logging.getLogger("yesman.batch_processor")

    def create_batch(self, items: list[dict[str, object]]) -> LogBatch:
        """Create a LogBatch from log entries.

        Returns:
        LogBatch: Description of return value.
        """
        # Add timestamp if not present
        for entry in items:
            if "timestamp" not in entry:
                entry["timestamp"] = time.time()

        batch = LogBatch(
            entries=items,
            timestamp=time.time(),
            batch_id=f"batch_{self.batch_counter:06d}",
        )

        self.batch_counter += 1
        return batch

    async def process_batch(self, batch: LogBatch) -> None:
        """Process a batch by writing to log file."""
        await self._write_batch(batch)

        # Update extended statistics
        if self.compression_enabled:
            # Calculate compression ratio from last write
            if hasattr(self, "_last_compression_ratio"):
                total_batches = self._stats.total_batches
                self.extended_stats["compression_ratio"] = (self.extended_stats["compression_ratio"] * (total_batches - 1) + self._last_compression_ratio) / total_batches

    async def _write_batch(self, batch: LogBatch) -> None:
        """Write a batch to storage."""
        # Check if we need a new log file
        if not self.current_log_file or self.current_file_size >= self.max_file_size:
            await self._rotate_log_file()

        # Prepare batch data
        batch_data = {
            "batch_id": batch.batch_id,
            "timestamp": batch.timestamp,
            "entry_count": len(batch.entries),
            "entries": batch.entries,
        }

        # Serialize to JSON
        json_data = json.dumps(batch_data, default=str, separators=(",", ":"))
        raw_size = len(json_data.encode("utf-8"))

        # Write to file (with optional compression)
        if self.compression_enabled and self.current_log_file.suffix == ".gz":
            compressed_data = gzip.compress(json_data.encode("utf-8"))

            # Write compressed data
            with open(self.current_log_file, "ab") as f:
                f.write(compressed_data)

            written_size = len(compressed_data)

            # Store compression ratio for statistics
            self._last_compression_ratio = written_size / raw_size if raw_size > 0 else 1.0
        else:
            # Write uncompressed with newline
            json_data += "\n"

            # Append to file
            with open(self.current_log_file, "a", encoding="utf-8") as f:
                f.write(json_data)

            written_size = len(json_data.encode("utf-8"))

        self.current_file_size += written_size
        self.extended_stats["bytes_written"] += written_size

        self.logger.debug(f"Wrote batch {batch.batch_id}: {len(batch.entries)} entries, {written_size} bytes")  # noqa: G004

    async def _rotate_log_file(self) -> None:
        """Rotate to a new log file."""
        timestamp = int(time.time())
        file_extension = ".jsonl.gz" if self.compression_enabled else ".jsonl"

        self.current_log_file = self.output_dir / f"yesman_logs_{timestamp}{file_extension}"
        self.current_file_size = 0
        self.extended_stats["files_created"] += 1

        self.logger.info(f"Rotated to new log file: {self.current_log_file}")  # noqa: G004

    def add_entry(self, entry: dict[str, object]) -> None:
        """Add a log entry to the processing queue."""
        self.add(entry)

    def get_statistics(self) -> dict[str, object]:
        """Get processing statistics.

        Returns:
        object: Description of return value.
        """
        # Get base statistics
        base_stats = super().get_statistics()

        # Add extended statistics
        return {
            **base_stats,
            **self.extended_stats,
            "current_file_size": self.current_file_size,
            "max_file_size": self.max_file_size,
            "compression_enabled": self.compression_enabled,
            "output_directory": str(self.output_dir),
            "entries_per_second": (base_stats["total_items"] / max(time.time() - self._stats.last_batch_time.timestamp(), 1) if self._stats.last_batch_time else 0),
        }

    async def cleanup_old_files(self, days_to_keep: int = 7) -> int:
        """Clean up old log files."""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        removed_count = 0

        try:
            for log_file in self.output_dir.glob("yesman_logs_*.jsonl*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    removed_count += 1

            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old log files")  # noqa: G004

        except Exception as e:
            self.logger.exception("Error cleaning up old log files")  # noqa: G004

        return removed_count

    async def read_batch_file(self, file_path: Path) -> list[LogBatch]:
        """Read and parse a batch log file."""
        batches = []

        try:
            if file_path.suffix == ".gz":
                # Read compressed file
                compressed_data = file_path.read_bytes()
                json_data = gzip.decompress(compressed_data).decode("utf-8")
            else:
                # Read uncompressed file
                json_data = file_path.read_text(encoding="utf-8")

            # Parse JSON lines
            for line in json_data.strip().split("\n"):
                if line.strip():
                    batch_data = json.loads(line)
                    batch = LogBatch(
                        entries=batch_data["entries"],
                        timestamp=batch_data["timestamp"],
                        batch_id=batch_data["batch_id"],
                    )
                    batches.append(batch)

        except Exception as e:
            self.logger.exception("Error reading batch file {file_path}")  # noqa: G004

        return batches

    def get_recent_entries(self, limit: int = 100) -> list[dict[str, object]]:
        """Get recent log entries from memory (pending entries).

        Returns:
        object: Description of return value.
        """
        with self._lock:
            recent = list(self._pending_items)
            return recent[-limit:] if len(recent) > limit else recent
