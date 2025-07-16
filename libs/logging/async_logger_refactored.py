"""Asynchronous logger with queue-based processing for high performance - Refactored version."""

import asyncio
import logging
import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from libs.core.mixins import StatisticsProviderMixin

from .batch_processor import BatchProcessor


class LogLevel(Enum):
    """Enhanced log levels with priorities."""

    TRACE = (5, "TRACE")
    DEBUG = (10, "DEBUG")
    INFO = (20, "INFO")
    WARNING = (30, "WARNING")
    ERROR = (40, "ERROR")
    CRITICAL = (50, "CRITICAL")

    def __init__(self, value: int, name: str):
        """Initialize LogLevel enum members."""
        self.level_value = value
        self.level_name = name


@dataclass
class LogEntry:
    """Structured log entry."""

    level: LogLevel
    message: str
    timestamp: float = field(default_factory=time.time)
    logger_name: str = ""
    module: str = ""
    function: str = ""
    line_number: int = 0
    thread_id: int = field(default_factory=lambda: threading.get_ident())
    process_id: int = field(default_factory=lambda: os.getpid())
    extra_data: dict[str, Any] = field(default_factory=dict)
    exception_info: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert log entry to dictionary for serialization."""
        return {
            "level": self.level.level_name,
            "level_value": self.level.level_value,
            "message": self.message,
            "timestamp": self.timestamp,
            "logger_name": self.logger_name,
            "module": self.module,
            "function": self.function,
            "line_number": self.line_number,
            "thread_id": self.thread_id,
            "process_id": self.process_id,
            "extra_data": self.extra_data,
            "exception_info": self.exception_info,
        }


class AsyncLogger(StatisticsProviderMixin):
    """High-performance asynchronous logger with batch processing."""

    def __init__(
        self,
        name: str = "async_logger",
        min_level: LogLevel = LogLevel.INFO,
        enable_batch_processing: bool = True,
        batch_size: int = 100,
        batch_timeout: float = 5.0,
        output_dir: Path | None = None,
        max_queue_size: int = 10000,
        thread_pool_size: int = 2,
    ):
        """
        Initialize async logger.

        Args:
            name: Logger name
            min_level: Minimum log level to process
            enable_batch_processing: Whether to enable batch processing
            batch_size: Number of entries per batch
            batch_timeout: Maximum time before flushing a batch
            output_dir: Directory for batch processor output
            max_queue_size: Maximum number of queued log entries
            thread_pool_size: Number of threads for I/O operations
        """
        self.name = name
        self.min_level = min_level
        self.enable_batch_processing = enable_batch_processing

        # Async queue for log entries
        self.log_queue: asyncio.Queue[LogEntry | None] = asyncio.Queue(maxsize=max_queue_size)

        # Batch processor
        self.batch_processor: BatchProcessor | None = None
        if enable_batch_processing:
            self.batch_processor = BatchProcessor(
                max_batch_size=batch_size,
                max_batch_time=batch_timeout,
                output_dir=output_dir,
            )

        # Thread pool for I/O operations
        self.thread_pool = ThreadPoolExecutor(max_workers=thread_pool_size)

        # Processing task
        self._processing_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

        # Standard logger for fallback
        self.fallback_logger = logging.getLogger(name)

        # Statistics
        self.stats = {
            "start_time": time.time(),
            "entries_logged": 0,
            "entries_processed": 0,
            "entries_dropped": 0,
            "errors": 0,
            "queue_full_count": 0,
            "current_queue_size": 0,
            "peak_queue_size": 0,
            "processing_time_ms": 0.0,
        }

        # Lock for thread-safe operations
        self._stats_lock = threading.Lock()

    def get_statistics(self) -> dict[str, Any]:
        """Get logger statistics - implements StatisticsProviderMixin interface."""
        batch_stats = {}
        if self.batch_processor:
            batch_stats = self.batch_processor.get_statistics()

        with self._stats_lock:
            uptime = time.time() - self.stats["start_time"]
            processing_rate = self.stats["entries_processed"] / uptime if uptime > 0 else 0

            return {
                **self.stats,
                "uptime_seconds": uptime,
                "processing_rate": processing_rate,
                "min_level": self.min_level.level_name,
                "batch_processing_enabled": self.enable_batch_processing,
                "batch_processor_stats": batch_stats,
                "thread_pool_size": self.thread_pool._max_workers,
                "is_running": self._processing_task is not None and not self._processing_task.done(),
            }

    async def start(self):
        """Start the async logger."""
        if self._processing_task and not self._processing_task.done():
            return

        self._stop_event.clear()

        # Start batch processor if enabled
        if self.batch_processor:
            await self.batch_processor.start()

        # Start processing task
        self._processing_task = asyncio.create_task(self._processing_loop())

        # Log startup
        await self.info(f"AsyncLogger '{self.name}' started")

    async def stop(self):
        """Stop the async logger gracefully."""
        if not self._processing_task:
            return

        # Signal stop
        self._stop_event.set()

        # Put sentinel value to unblock queue
        try:
            await asyncio.wait_for(self.log_queue.put(None), timeout=1.0)
        except TimeoutError:
            pass

        # Wait for processing to complete
        try:
            await asyncio.wait_for(self._processing_task, timeout=10.0)
        except TimeoutError:
            self._processing_task.cancel()

        # Stop batch processor
        if self.batch_processor:
            await self.batch_processor.stop()

        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)

        # Log shutdown
        self.fallback_logger.info(f"AsyncLogger '{self.name}' stopped")

    async def _processing_loop(self):
        """Main processing loop for log entries."""
        try:
            while not self._stop_event.is_set():
                try:
                    # Get entry from queue with timeout
                    entry = await asyncio.wait_for(self.log_queue.get(), timeout=1.0)

                    if entry is None:  # Sentinel value
                        break

                    # Process the entry
                    await self._process_entry(entry)

                    # Update statistics
                    with self._stats_lock:
                        self.stats["entries_processed"] += 1
                        self.stats["current_queue_size"] = self.log_queue.qsize()

                except TimeoutError:
                    continue
                except Exception as e:
                    self.fallback_logger.error(f"Error processing log entry: {e}")
                    with self._stats_lock:
                        self.stats["errors"] += 1

        except Exception as e:
            self.fallback_logger.error(f"Fatal error in processing loop: {e}")

    async def _process_entry(self, entry: LogEntry):
        """Process a single log entry."""
        start_time = time.time()

        try:
            # Convert to dict for processing
            entry_dict = entry.to_dict()

            # Send to batch processor if enabled
            if self.batch_processor:
                self.batch_processor.add_entry(entry_dict)

            # Also log to standard logger
            self._log_to_standard(entry)

            # Update processing time
            processing_time = (time.time() - start_time) * 1000
            with self._stats_lock:
                self.stats["processing_time_ms"] += processing_time

        except Exception as e:
            self.fallback_logger.error(f"Error processing entry: {e}")
            with self._stats_lock:
                self.stats["errors"] += 1

    def _log_to_standard(self, entry: LogEntry):
        """Log entry to standard Python logger."""
        # Format message with context
        formatted_message = f"[{entry.module}:{entry.function}:{entry.line_number}] {entry.message}"

        # Add extra data if present
        if entry.extra_data:
            formatted_message += f" | Extra: {entry.extra_data}"

        # Log at appropriate level
        log_func = getattr(self.fallback_logger, entry.level.level_name.lower(), None)
        if log_func:
            if entry.exception_info:
                log_func(formatted_message + f"\n{entry.exception_info}")
            else:
                log_func(formatted_message)

    async def _log(
        self,
        level: LogLevel,
        message: str,
        exc_info: Exception | None = None,
        **kwargs,
    ):
        """Internal method to queue a log entry."""
        if level.level_value < self.min_level.level_value:
            return

        # Get caller info
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            module = os.path.basename(caller_frame.f_code.co_filename)
            function = caller_frame.f_code.co_name
            line_number = caller_frame.f_lineno
        else:
            module = function = "unknown"
            line_number = 0

        # Create log entry
        entry = LogEntry(
            level=level,
            message=message,
            logger_name=self.name,
            module=module,
            function=function,
            line_number=line_number,
            extra_data=kwargs,
            exception_info=traceback.format_exc() if exc_info else None,
        )

        # Try to queue the entry
        try:
            self.log_queue.put_nowait(entry)
            with self._stats_lock:
                self.stats["entries_logged"] += 1
                current_size = self.log_queue.qsize()
                self.stats["current_queue_size"] = current_size
                self.stats["peak_queue_size"] = max(self.stats["peak_queue_size"], current_size)
        except asyncio.QueueFull:
            # Queue is full, drop the entry
            with self._stats_lock:
                self.stats["entries_dropped"] += 1
                self.stats["queue_full_count"] += 1

            # Fallback to standard logger
            self.fallback_logger.warning(f"Log queue full, dropping entry: {message}")

    # Convenience methods for different log levels
    async def trace(self, message: str, **kwargs):
        """Log a trace message."""
        await self._log(LogLevel.TRACE, message, **kwargs)

    async def debug(self, message: str, **kwargs):
        """Log a debug message."""
        await self._log(LogLevel.DEBUG, message, **kwargs)

    async def info(self, message: str, **kwargs):
        """Log an info message."""
        await self._log(LogLevel.INFO, message, **kwargs)

    async def warning(self, message: str, **kwargs):
        """Log a warning message."""
        await self._log(LogLevel.WARNING, message, **kwargs)

    async def error(self, message: str, exc_info: Exception | None = None, **kwargs):
        """Log an error message."""
        await self._log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)

    async def critical(self, message: str, exc_info: Exception | None = None, **kwargs):
        """Log a critical message."""
        await self._log(LogLevel.CRITICAL, message, exc_info=exc_info, **kwargs)

    def set_min_level(self, level: LogLevel):
        """Set minimum log level."""
        self.min_level = level

    async def flush(self):
        """Flush any pending log entries."""
        # Wait for queue to empty
        while not self.log_queue.empty():
            await asyncio.sleep(0.1)

        # Flush batch processor if enabled
        if self.batch_processor:
            await self.batch_processor.wait_for_pending()

    async def cleanup_old_logs(self, days_to_keep: int = 7):
        """Clean up old log files if batch processing is enabled."""
        if self.batch_processor:
            return await self.batch_processor.cleanup_old_files(days_to_keep)
        return 0
